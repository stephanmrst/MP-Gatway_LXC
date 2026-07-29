"""OpenCCU XML-API device and channel cache.

Device and channel names are loaded exclusively from
/config/xmlapi/devicelist.cgi. CCU-Jack MQTT remains responsible only for live
values.
"""
from __future__ import annotations

import base64
import ssl
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Callable


class OpenCcuRestCache:
    REFRESH_SECONDS = 600

    def __init__(self, config_loader: Callable[[], dict[str, Any]], logger=None):
        self._config_loader = config_loader
        self._logger = logger
        self._lock = threading.RLock()
        self._devices: dict[str, dict[str, Any]] = {}
        self._channels: dict[str, dict[str, Any]] = {}
        self._refreshing = False
        self._status = {
            "state": "idle",
            "message": "Geräteliste noch nicht geladen",
            "device_count": 0,
            "channel_count": 0,
            "last_refresh": "",
            "last_error": "",
            "source": "XML-API",
        }

    def _cfg(self):
        return dict((self._config_loader() or {}).get("openccu", {}) or {})

    def _log(self, level, text, *args):
        if self._logger is not None:
            getattr(self._logger, level, self._logger.info)(text, *args)

    def snapshot_status(self):
        with self._lock:
            return dict(self._status)

    def snapshot_catalog(self):
        with self._lock:
            devices = []
            for device in self._devices.values():
                item = dict(device)
                item["channels"] = [dict(channel) for channel in device.get("channels", [])]
                devices.append(item)
        devices.sort(key=lambda item: (str(item.get("name") or "").lower(), str(item.get("address") or "")))
        return devices

    def ensure_fresh(self):
        with self._lock:
            last = self._status.get("last_refresh_epoch", 0) or 0
            needed = not self._devices or time.time() - last >= self.REFRESH_SECONDS
        if needed:
            self.refresh_async()

    def refresh_async(self):
        with self._lock:
            if self._refreshing:
                return False
            self._refreshing = True
            self._status.update(
                state="loading",
                message="Geräte werden über die XML-API geladen",
                last_error="",
                source="XML-API",
            )
        threading.Thread(target=self._refresh_worker, name="openccu-xmlapi-cache", daemon=True).start()
        return True

    def _refresh_worker(self):
        try:
            devices, channels = self._fetch_xmlapi_devices()
            now = datetime.now().isoformat(timespec="seconds")
            with self._lock:
                self._devices = devices
                self._channels = channels
                self._status.update(
                    state="ready",
                    message=f"{len(devices)} Geräte geladen",
                    device_count=len(devices),
                    channel_count=len(channels),
                    last_refresh=now,
                    last_refresh_epoch=time.time(),
                    last_error="",
                    source="XML-API",
                )
            self._log("info", "OpenCCU XML-API cache loaded: %s devices, %s channels", len(devices), len(channels))
        except Exception as exc:
            with self._lock:
                self._status.update(
                    state="error",
                    message="Geräte konnten nicht geladen werden",
                    last_error=str(exc),
                    source="XML-API",
                )
            self._log("warning", "OpenCCU XML-API cache failed: %s", exc)
        finally:
            with self._lock:
                self._refreshing = False

    def _fetch_xmlapi_devices(self):
        cfg = self._cfg()
        host = str(cfg.get("host") or "").strip()
        if not host:
            raise ValueError("OpenCCU Host fehlt")
        scheme = "https" if cfg.get("https") else "http"
        port = int(cfg.get("http_port", 443 if scheme == "https" else 80))
        url = f"{scheme}://{host}:{port}/config/xmlapi/devicelist.cgi"
        headers = {"Accept": "application/xml,text/xml,*/*", "User-Agent": "MP-Gateway/34.6.9"}
        user = str(cfg.get("api_user") or "")
        if user:
            token = base64.b64encode(f"{user}:{cfg.get('api_password') or ''}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        request = urllib.request.Request(url, headers=headers)
        context = ssl._create_unverified_context() if scheme == "https" else None
        with urllib.request.urlopen(request, timeout=25, context=context) as response:
            raw = response.read()
        root = ET.fromstring(raw)

        devices: dict[str, dict[str, Any]] = {}
        channels: dict[str, dict[str, Any]] = {}
        for dev in root.findall(".//device"):
            address = str(dev.attrib.get("address") or "").strip()
            if not address:
                continue
            device = {
                "ise_id": str(dev.attrib.get("ise_id") or ""),
                "name": str(dev.attrib.get("name") or address).strip() or address,
                "address": address,
                "device_type": str(dev.attrib.get("device_type") or dev.attrib.get("type") or "").strip(),
                "interface": str(dev.attrib.get("interface") or "").strip(),
                "channels": [],
            }
            for ch in dev.findall("./channel"):
                ch_address = str(ch.attrib.get("address") or "").strip()
                if not ch_address:
                    continue
                channel_no = ch_address.split(":", 1)[1] if ":" in ch_address else str(ch.attrib.get("index") or "")
                channel = {
                    "ise_id": str(ch.attrib.get("ise_id") or ""),
                    "name": str(ch.attrib.get("name") or ch_address).strip() or ch_address,
                    "address": ch_address,
                    "channel": channel_no,
                    "type": str(ch.attrib.get("type") or "").strip(),
                    "direction": str(ch.attrib.get("direction") or "").strip(),
                    "parent_device": str(ch.attrib.get("parent_device") or device["ise_id"]),
                    "device_address": address,
                }
                device["channels"].append(channel)
                channels[ch_address.upper()] = channel
            device["channels"].sort(key=lambda item: (int(item["channel"]) if str(item["channel"]).isdigit() else 9999, item["name"].lower()))
            devices[address.upper()] = device
        if not devices:
            raise ValueError("XML-API lieferte keine Geräte. XML-API-Add-on und Firewall-Einstellungen prüfen")
        return devices, channels
