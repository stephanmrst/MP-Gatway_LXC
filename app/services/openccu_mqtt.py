"""Dedicated CCU-Jack MQTT discovery runtime.

The service intentionally stays independent from the gateway's regular MQTT
bridge. It only subscribes to the configured CCU-Jack topic prefix and keeps a
small in-memory discovery cache for the OpenCCU Explorer.
"""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from datetime import datetime
from typing import Any, Callable

from app.services.openccu_rest import OpenCcuRestCache

try:
    import paho.mqtt.client as mqtt
except Exception:  # pragma: no cover - startup remains possible without paho
    mqtt = None


class OpenCcuMqttRuntime:
    MAX_ENTRIES = 2000

    def __init__(self, config_loader: Callable[[], dict[str, Any]], logger=None, on_value=None, metadata=None):
        self._config_loader = config_loader
        self._logger = logger
        self.on_value = on_value
        self._lock = threading.RLock()
        self._client = None
        self.metadata = metadata or OpenCcuRestCache(config_loader, logger)
        self._entries: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._last_dispatched: dict[str, tuple[Any, str, float]] = {}
        self._generation = 0
        self._status = {
            "enabled": False,
            "connected": False,
            "state": "stopped",
            "message": "Integration ist deaktiviert",
            "host": "",
            "port": 1883,
            "topic": "",
            "last_connect": "",
            "last_message": "",
            "received": 0,
            "unique_topics": 0,
        }

    def _log(self, level: str, text: str, *args):
        logger = self._logger
        if logger is not None:
            getattr(logger, level, logger.info)(text, *args)

    def _cfg(self) -> dict[str, Any]:
        return dict((self._config_loader() or {}).get("openccu", {}) or {})

    @staticmethod
    def _subscription(value: Any) -> str:
        topic = str(value or "").strip() or "device/status/#"
        if "+" not in topic and "#" not in topic:
            topic = topic.rstrip("/") + "/#"
        return topic

    def start(self):
        self.reload()
        self.metadata.ensure_fresh()

    def stop(self):
        with self._lock:
            self._generation += 1
            client = self._client
            self._client = None
            self._status.update(connected=False, state="stopped")
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass
            try:
                client.loop_stop()
            except Exception:
                pass

    def reload(self):
        self.stop()
        cfg = self._cfg()
        enabled = bool(cfg.get("enabled"))
        host = str(cfg.get("mqtt_host") or cfg.get("host") or "").strip()
        try:
            port = int(cfg.get("mqtt_port", 1883))
        except (TypeError, ValueError):
            port = 1883
        topic = self._subscription(cfg.get("topic_prefix"))
        with self._lock:
            self._status.update(
                enabled=enabled,
                connected=False,
                host=host,
                port=port,
                topic=topic,
                state="disabled" if not enabled else "connecting",
                message="Integration ist deaktiviert" if not enabled else "Verbindung wird aufgebaut",
            )
            self._generation += 1
            generation = self._generation
        if not enabled:
            return
        if not host:
            with self._lock:
                self._status.update(state="error", message="MQTT Host fehlt")
            return
        if mqtt is None:
            with self._lock:
                self._status.update(state="error", message="paho-mqtt ist nicht installiert")
            return

        try:
            try:
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=f"mp-gateway-openccu-{int(time.time())}")
            except (AttributeError, TypeError):
                client = mqtt.Client(client_id=f"mp-gateway-openccu-{int(time.time())}")
            user = str(cfg.get("mqtt_user") or "").strip()
            if user:
                client.username_pw_set(user, str(cfg.get("mqtt_password") or ""))
            if cfg.get("mqtt_tls"):
                client.tls_set()
            client.reconnect_delay_set(min_delay=1, max_delay=60)
            client.on_connect = lambda c, u, f, rc, *extra: self._on_connect(generation, c, rc)
            client.on_disconnect = lambda c, u, rc, *extra: self._on_disconnect(generation, rc)
            client.on_message = lambda c, u, msg: self._on_message(generation, msg)
            with self._lock:
                if generation != self._generation:
                    return
                self._client = client
            client.connect_async(host, port, keepalive=45)
            client.loop_start()
            self._log("info", "OpenCCU MQTT runtime starting host=%s port=%s topic=%s", host, port, topic)
        except Exception as exc:
            with self._lock:
                self._status.update(state="error", message=f"Verbindungsstart fehlgeschlagen: {exc}")
            self._log("exception", "OpenCCU MQTT startup failed")

    def _on_connect(self, generation: int, client, rc):
        if generation != self._generation:
            return
        code = int(getattr(rc, "value", rc) or 0)
        if code != 0:
            with self._lock:
                self._status.update(connected=False, state="error", message=f"MQTT-Verbindung abgelehnt (Code {code})")
            return
        topic = self._status.get("topic") or "device/status/#"
        result, _mid = client.subscribe(topic, qos=0)
        if int(result) != 0:
            with self._lock:
                self._status.update(connected=False, state="error", message=f"Subscribe fehlgeschlagen (Code {result})")
            return
        now = datetime.now().isoformat(timespec="seconds")
        self.metadata.ensure_fresh()
        with self._lock:
            self._status.update(connected=True, state="connected", message="Verbunden und abonniert", last_connect=now)
        self._log("info", "OpenCCU MQTT connected and subscribed topic=%s", topic)

    def _on_disconnect(self, generation: int, rc):
        if generation != self._generation:
            return
        code = int(getattr(rc, "value", rc) or 0)
        with self._lock:
            enabled = bool(self._status.get("enabled"))
            self._status.update(
                connected=False,
                state="reconnecting" if enabled else "stopped",
                message="Verbindung verloren – automatischer Reconnect läuft" if enabled else "Gestoppt",
            )
        if code:
            self._log("warning", "OpenCCU MQTT disconnected rc=%s; reconnect active", code)

    @staticmethod
    def _decode_payload(raw: bytes) -> tuple[str, Any, str, dict[str, Any]]:
        """Decode a CCU-Jack payload and expose its actual datapoint value.

        CCU-Jack commonly publishes envelopes such as
        ``{"s": 0, "ts": 1234567890, "v": false}``.  The Explorer and
        every downstream consumer need the value from ``v`` rather than the
        complete JSON envelope.  The original envelope remains available as
        metadata for diagnostics.
        """
        text = raw.decode("utf-8", errors="replace")
        metadata: dict[str, Any] = {}
        try:
            decoded = json.loads(text)
            if isinstance(decoded, dict) and "v" in decoded:
                value = decoded.get("v")
                metadata = {
                    "ccu_status": decoded.get("s"),
                    "ccu_timestamp": decoded.get("ts"),
                    "ccu_payload": decoded,
                }
            else:
                value = decoded
            if isinstance(value, bool):
                value_type = "bool"
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                value_type = "number"
            elif isinstance(value, (dict, list)):
                value_type = "json"
            elif value is None:
                value_type = "null"
            else:
                value_type = "string"
            return text, value, value_type, metadata
        except Exception:
            lowered = text.strip().lower()
            if lowered in {"true", "false"}:
                return text, lowered == "true", "bool", metadata
            try:
                if "." in text or "e" in lowered:
                    return text, float(text), "number", metadata
                return text, int(text), "number", metadata
            except Exception:
                return text, text, "string", metadata

    def _on_message(self, generation: int, msg):
        if generation != self._generation:
            return
        now = datetime.now().isoformat(timespec="seconds")
        raw_text, value, value_type, payload_meta = self._decode_payload(bytes(msg.payload or b""))
        topic = str(msg.topic or "")
        entry = {
            "topic": topic,
            "value": value,
            "raw": raw_text,
            "value_type": value_type,
            "qos": int(getattr(msg, "qos", 0) or 0),
            "retain": bool(getattr(msg, "retain", False)),
            "updated_at": now,
            "count": 1,
            **payload_meta,
        }
        with self._lock:
            old = self._entries.pop(topic, None)
            if old:
                entry["count"] = int(old.get("count", 0)) + 1
                entry["first_seen"] = old.get("first_seen") or now
            else:
                entry["first_seen"] = now
            self._entries[topic] = entry
            while len(self._entries) > self.MAX_ENTRIES:
                self._entries.popitem(last=False)
            self._status["last_message"] = now
            self._status["received"] = int(self._status.get("received", 0)) + 1
            self._status["unique_topics"] = len(self._entries)
        if callable(self.on_value):
            # CCU-Jack can deliver the same state telegram twice within a few
            # milliseconds.  Explorer accounting may keep both receptions, but
            # the object runtime must route one CCU event only once.  Use the
            # original CCU timestamp plus the unchanged raw payload as event
            # identity; real follow-up changes therefore remain untouched.
            ccu_timestamp = payload_meta.get("ccu_timestamp")
            dispatch_now = time.monotonic()
            duplicate_event = False
            if ccu_timestamp is not None:
                with self._lock:
                    previous = self._last_dispatched.get(topic)
                    signature = (ccu_timestamp, raw_text, dispatch_now)
                    if previous is not None:
                        previous_ts, previous_raw, previous_at = previous
                        duplicate_event = (
                            previous_ts == ccu_timestamp
                            and previous_raw == raw_text
                            and dispatch_now - previous_at <= 2.0
                        )
                    if not duplicate_event:
                        self._last_dispatched[topic] = signature
            if duplicate_event:
                self._log(
                    "debug",
                    "OpenCCU duplicate event skipped topic=%s ccu_timestamp=%s",
                    topic, ccu_timestamp,
                )
                return
            try:
                self.on_value(topic, value, now)
            except Exception:
                self._log("exception", "OpenCCU live value dispatch failed topic=%s", topic)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            entries = [dict(item) for item in reversed(self._entries.values())]
            status = dict(self._status)
        self.metadata.ensure_fresh()
        devices = self.metadata.snapshot_catalog()
        by_device = {str(item.get("address") or "").upper(): item for item in devices}
        by_channel = {}
        for device in devices:
            for channel in device.get("channels", []):
                by_channel[str(channel.get("address") or "").upper()] = channel

        live_by_device = {}
        for entry in entries:
            parts = [part for part in str(entry.get("topic") or "").split("/") if part]
            try:
                idx = parts.index("status")
            except ValueError:
                continue
            if len(parts) < idx + 4:
                continue
            serial = parts[idx + 1]
            channel_no = parts[idx + 2]
            datapoint = "/".join(parts[idx + 3:])
            channel_address = f"{serial}:{channel_no}"
            entry["serial"] = serial
            entry["channel"] = channel_no
            entry["channel_address"] = channel_address
            entry["datapoint"] = datapoint
            channel_meta = by_channel.get(channel_address.upper(), {})
            entry["channel_name"] = channel_meta.get("name") or channel_address
            entry["device_name"] = by_device.get(serial.upper(), {}).get("name") or serial
            live_by_device.setdefault(serial.upper(), []).append(entry)

        for device in devices:
            live = live_by_device.get(str(device.get("address") or "").upper(), [])
            device["live_datapoints"] = live
            online_dp = next((e for e in live if str(e.get("datapoint") or "").upper() in {"ONLINE", "UNREACH"}), None)
            if online_dp and str(online_dp.get("datapoint") or "").upper() == "UNREACH":
                device["online"] = not bool(online_dp.get("value"))
            elif online_dp:
                device["online"] = bool(online_dp.get("value"))
            else:
                device["online"] = bool(live)
            device["last_update"] = max((str(e.get("updated_at") or "") for e in live), default="")

        return {"status": status, "metadata_status": self.metadata.snapshot_status(), "devices": devices, "entries": entries}

    def clear(self):
        with self._lock:
            self._entries.clear()
            self._status.update(unique_topics=0, received=0, last_message="")
