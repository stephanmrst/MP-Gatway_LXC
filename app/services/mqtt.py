"""MQTT runtime helpers with per-broker reconnect handling."""

from __future__ import annotations

import logging
import queue
import threading
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from types import SimpleNamespace

LOGGER = logging.getLogger(__name__)

mqtt_monitor_values: dict[str, dict[str, Any]] = {}
mqtt_clients: dict[str, object] = {}
mqtt_client: object = None

_BROKER_STATES: dict[str, dict[str, Any]] = {}
_BROKER_LOCK = threading.RLock()
_HEALTHCHECK_THREAD: threading.Thread | None = None
_HEALTHCHECK_STOP = threading.Event()
_RECONNECT_BACKOFFS = (5, 10, 30, 60, 120)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _age_seconds(timestamp: str) -> float | None:
    if not timestamp:
        return None
    try:
        dt = datetime.fromisoformat(timestamp)
    except Exception:
        return None
    try:
        return max(0.0, (datetime.now(timezone.utc).astimezone() - dt).total_seconds())
    except Exception:
        return None


def _safe_int(value: Any, default: int = 1883) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _normalize_name(value: Any, default: str = "Broker") -> str:
    name = str(value or "").strip()
    return name or default


def _client_id(name: str, host: str, port: int, is_main: bool) -> str:
    prefix = "mpgw-main" if is_main else "mpgw-ext"
    return f"{prefix}-{name}-{host}-{port}-{uuid4().hex[:10]}"


def _state_key(broker: dict[str, Any]) -> str:
    return _normalize_name(broker.get("name"), "Broker")


def _default_subscriptions(_: dict[str, Any]) -> list[str]:
    return ["#"]


def _normalize_queue_mode(value: Any, broker_name: str = "") -> str:
    text = str(value or "").strip().lower().replace("_", "-")
    if text in {"normal", "latest-per-topic"}:
        return text
    if "victron" in str(broker_name or "").lower():
        return "latest-per-topic"
    return "latest-per-topic"


def _safe_queue_size(value: Any, default: int = 500) -> int:
    try:
        size = int(value)
        return max(1, min(size, 5000))
    except Exception:
        return default


def _make_broker_state(broker: dict[str, Any], subscriptions: list[str] | None = None) -> dict[str, Any]:
    name = _normalize_name(broker.get("name"), "Broker")
    host = str(broker.get("host", "") or "").strip()
    port = _safe_int(broker.get("port", 1883))
    state = {
        "name": name,
        "host": host,
        "port": port,
        "user": str(broker.get("user", "") or "").strip(),
        "password": str(broker.get("password", "") or ""),
        "enabled": bool(broker.get("enabled", True)),
        "is_main": bool(broker.get("is_main", False)),
        "client_id": _client_id(name, host, port, bool(broker.get("is_main", False))),
        "client": None,
        "connected": False,
        "connecting": False,
        "reconnect_running": False,
        "reconnect_attempts": 0,
        "last_connect": "",
        "last_disconnect": "",
        "last_message_time": "",
        "last_message_value": "",
        "last_error": "",
        "connect_rc": None,
        "disconnect_rc": None,
        "subscription_count": 0,
        "queue_mode": _normalize_queue_mode(broker.get("queue_mode", ""), name),
        "max_queue_size": _safe_queue_size(broker.get("max_queue_size", 500)),
        "received_messages": 0,
        "processed_messages": 0,
        "dropped_messages": 0,
        "dropped_since_log": 0,
        "last_queue_full_log": 0.0,
        "last_processed_time": "",
        "pending_by_topic": {},
        "pending_topics": set(),
        "queue_lock": threading.RLock(),
        "subscriptions": list(subscriptions or _default_subscriptions(broker)),
        "message_queue": queue.Queue(maxsize=_safe_queue_size(broker.get("max_queue_size", 500))),
        "worker_thread": None,
        "healthcheck_thread": None,
        "reconnect_timer": None,
        "stop_event": threading.Event(),
        "suppress_disconnect_reconnect": False,
        "last_healthcheck": "",
        "connect_started_at": "",
        "worker_alive": False,
    }
    state["subscription_count"] = len(state["subscriptions"])
    return state


def _get_state(name: str) -> dict[str, Any] | None:
    with _BROKER_LOCK:
        return _BROKER_STATES.get(name)


def _set_client(name: str, client: object) -> None:
    global mqtt_client
    with _BROKER_LOCK:
        state = _BROKER_STATES.get(name)
        if not state:
            return
        state["client"] = client
        mqtt_clients[name] = client
        if state.get("is_main"):
            mqtt_client = client


def _set_status(name: str, **updates: Any) -> None:
    with _BROKER_LOCK:
        state = _BROKER_STATES.get(name)
        if not state:
            return
        state.update(updates)


def _log(add_log_entry, message: str) -> None:
    if callable(add_log_entry):
        try:
            add_log_entry(message)
        except Exception:
            LOGGER.exception("MQTT log callback failed")
    else:
        LOGGER.info(message)


def _resubscribe_client(state: dict[str, Any], client: object, add_log_entry) -> None:
    subs = list(state.get("subscriptions") or ["#"])
    ok_topics: list[str] = []
    for topic in subs:
        try:
            result = client.subscribe(topic)
            rc = result[0] if isinstance(result, tuple) else result
            if rc in (0, None):
                ok_topics.append(topic)
            else:
                _log(add_log_entry, f"MQTT Broker {state['name']} subscribe rc={rc} topic={topic}")
        except Exception as exc:
            _log(add_log_entry, f"MQTT Broker {state['name']} subscribe Fehler topic={topic}: {exc}")
    state["subscription_count"] = len(ok_topics) or len(subs)
    _log(
        add_log_entry,
        f"MQTT Broker {state['name']} reconnect OK resubscribed topics: {', '.join(ok_topics or subs)}",
    )


def _broker_worker(state: dict[str, Any], handler, add_log_entry) -> None:
    state["worker_alive"] = True
    while not state["stop_event"].is_set():
        try:
            item = state["message_queue"].get(timeout=0.5)
        except queue.Empty:
            continue
        if item is None:
            continue
        try:
            if state["stop_event"].is_set():
                continue
            if state.get("queue_mode") == "latest-per-topic":
                topic = item
                with state["queue_lock"]:
                    entry = state["pending_by_topic"].pop(topic, None)
                    state["pending_topics"].discard(topic)
            else:
                entry = item
            if not entry:
                continue
            handler(entry["client"], entry["userdata"], entry["msg"])
            state["processed_messages"] = int(state.get("processed_messages", 0)) + 1
            state["last_processed_time"] = _now_iso()
        except Exception as exc:
            state["last_error"] = str(exc)
            _log(add_log_entry, f"MQTT Broker {state['name']} worker Fehler: {exc}")
        finally:
            try:
                state["message_queue"].task_done()
            except Exception:
                pass
    state["worker_alive"] = False


def _rate_limited_queue_log(state: dict[str, Any], add_log_entry, message: str) -> None:
    now = time.time()
    last = float(state.get("last_queue_full_log", 0.0) or 0.0)
    if now - last < 10:
        return
    state["last_queue_full_log"] = now
    state["dropped_since_log"] = 0
    _log(add_log_entry, message)


def _enqueue_broker_message(state: dict[str, Any], entry: dict[str, Any], add_log_entry) -> None:
    mode = state.get("queue_mode", "latest-per-topic")
    topic = str(entry.get("topic", "") or "").strip()
    if not topic:
        return
    state["received_messages"] = int(state.get("received_messages", 0)) + 1
    if mode == "latest-per-topic":
        with state["queue_lock"]:
            state["pending_by_topic"][topic] = entry
            if topic in state["pending_topics"]:
                return
            state["pending_topics"].add(topic)
            if state["message_queue"].qsize() >= state.get("max_queue_size", 500):
                dropped_topic = None
                try:
                    dropped_topic = state["message_queue"].get_nowait()
                    state["message_queue"].task_done()
                except queue.Empty:
                    dropped_topic = None
                if dropped_topic is not None:
                    state["pending_topics"].discard(dropped_topic)
                    state["pending_by_topic"].pop(dropped_topic, None)
                    state["dropped_messages"] = int(state.get("dropped_messages", 0)) + 1
                    state["dropped_since_log"] = int(state.get("dropped_since_log", 0)) + 1
            try:
                state["message_queue"].put_nowait(topic)
            except queue.Full:
                state["pending_topics"].discard(topic)
                state["pending_by_topic"].pop(topic, None)
                state["dropped_messages"] = int(state.get("dropped_messages", 0)) + 1
                state["dropped_since_log"] = int(state.get("dropped_since_log", 0)) + 1
                _rate_limited_queue_log(
                    state,
                    add_log_entry,
                    f"MQTT Broker {state['name']} message queue voll: {state.get('dropped_since_log', 0)} Nachrichten verworfen",
                )
                return
        return

    try:
        if state["message_queue"].full():
            try:
                state["message_queue"].get_nowait()
                state["message_queue"].task_done()
                state["dropped_messages"] = int(state.get("dropped_messages", 0)) + 1
                state["dropped_since_log"] = int(state.get("dropped_since_log", 0)) + 1
            except queue.Empty:
                pass
        state["message_queue"].put_nowait(entry)
    except queue.Full:
        state["dropped_messages"] = int(state.get("dropped_messages", 0)) + 1
        state["dropped_since_log"] = int(state.get("dropped_since_log", 0)) + 1
    if int(state.get("dropped_since_log", 0)) > 0:
        _rate_limited_queue_log(
            state,
            add_log_entry,
            f"MQTT Broker {state['name']} message queue voll: {state.get('dropped_since_log', 0)} Nachrichten verworfen",
        )


def _schedule_reconnect(name: str, mqtt_lib, handler, add_log_entry) -> None:
    state = _get_state(name)
    if not state or state["stop_event"].is_set():
        return

    with _BROKER_LOCK:
        if state.get("reconnect_running") or state.get("reconnect_timer"):
            return
        attempt = int(state.get("reconnect_attempts", 0)) + 1
        delay = _RECONNECT_BACKOFFS[min(attempt - 1, len(_RECONNECT_BACKOFFS) - 1)]
        state["reconnect_running"] = True
        state["reconnect_attempts"] = attempt
        state["last_error"] = state.get("last_error", "")

    def _runner():
        success = _reconnect_broker(name, mqtt_lib, handler, add_log_entry)
        with _BROKER_LOCK:
            state = _BROKER_STATES.get(name)
            if state:
                state["reconnect_running"] = False
                state["reconnect_timer"] = None
        if not success:
            _schedule_reconnect(name, mqtt_lib, handler, add_log_entry)

    timer = threading.Timer(delay, _runner)
    timer.daemon = True
    with _BROKER_LOCK:
        state = _BROKER_STATES.get(name)
        if not state:
            return
        state["reconnect_timer"] = timer
    _log(add_log_entry, f"MQTT Broker {name} reconnect in {delay}s attempt={attempt}")
    timer.start()


def _disconnect_client_safely(state: dict[str, Any]) -> None:
    client = state.get("client")
    if client is None:
        return
    state["suppress_disconnect_reconnect"] = True
    try:
        try:
            client.loop_stop()
        except Exception:
            pass
        try:
            client.disconnect()
        except Exception:
            pass
    finally:
        state["suppress_disconnect_reconnect"] = False


def _create_client(mqtt_lib, state: dict[str, Any], handler, add_log_entry):
    userdata = {"broker": state["name"], "broker_key": state["name"]}
    client = mqtt_lib.Client(client_id=state["client_id"], userdata=userdata)
    if state.get("user"):
        try:
            client.username_pw_set(state["user"], state.get("password", ""))
        except Exception as exc:
            state["last_error"] = str(exc)
            _log(add_log_entry, f"MQTT Broker {state['name']} username_pw_set Fehler: {exc}")

    def on_connect(client_obj, userdata, flags, rc, properties=None):
        state["connected"] = rc == 0
        state["connecting"] = False
        state["connect_rc"] = rc
        state["last_connect"] = _now_iso()
        state["connect_started_at"] = ""
        state["last_error"] = "" if rc == 0 else f"connect rc={rc}"
        if rc == 0:
            state["reconnect_attempts"] = 0
            _log(
                add_log_entry,
                f"MQTT Broker {state['name']} connected host={state['host']} port={state['port']} client_id={state['client_id']} rc={rc}",
            )
            _resubscribe_client(state, client_obj, add_log_entry)
        else:
            _log(
                add_log_entry,
                f"MQTT Broker {state['name']} connect fehlgeschlagen host={state['host']} port={state['port']} rc={rc}",
            )

    def on_disconnect(client_obj, userdata, rc, properties=None):
        state["connected"] = False
        state["connecting"] = False
        state["disconnect_rc"] = rc
        state["last_disconnect"] = _now_iso()
        state["connect_started_at"] = ""
        if rc != 0:
            state["last_error"] = f"disconnect rc={rc}"
        _log(
            add_log_entry,
            f"MQTT Broker {state['name']} disconnected host={state['host']} port={state['port']} rc={rc}",
        )
        if state["stop_event"].is_set() or state.get("suppress_disconnect_reconnect"):
            return
        _schedule_reconnect(state["name"], mqtt_lib, handler, add_log_entry)

    def on_message(client_obj, userdata, msg):
        if state["stop_event"].is_set():
            return
        payload = msg.payload.decode("utf-8", errors="ignore").strip()
        state["last_message_time"] = _now_iso()
        state["last_message_value"] = payload
        try:
            fake_msg = SimpleNamespace(
                topic=msg.topic,
                payload=msg.payload,
                qos=getattr(msg, "qos", 0),
                retain=bool(getattr(msg, "retain", False)),
            )
            entry = {
                "client": client_obj,
                "userdata": userdata,
                "msg": fake_msg,
                "topic": msg.topic,
                "payload": payload,
            }
            _enqueue_broker_message(state, entry, add_log_entry)
        except Exception as exc:
            state["last_error"] = str(exc)
            _log(add_log_entry, f"MQTT Broker {state['name']} on_message Fehler: {exc}")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    return client


def _connect_broker(state: dict[str, Any], mqtt_lib, handler, add_log_entry) -> object | None:
    if state["stop_event"].is_set():
        return None
    client = _create_client(mqtt_lib, state, handler, add_log_entry)
    try:
        state["connecting"] = True
        state["connect_started_at"] = _now_iso()
        _log(
            add_log_entry,
            f"MQTT Broker {state['name']} connect start host={state['host']} port={state['port']} client_id={state['client_id']}",
        )
        client.connect(state["host"], int(state["port"]), 60)
        client.loop_start()
        _set_client(state["name"], client)
        state["last_error"] = ""
        return client
    except Exception as exc:
        state["connecting"] = False
        state["connected"] = False
        state["connect_started_at"] = ""
        state["last_error"] = str(exc)
        _log(
            add_log_entry,
            f"MQTT Broker {state['name']} connect Fehler host={state['host']} port={state['port']}: {exc}",
        )
        try:
            client.loop_stop()
        except Exception:
            pass
        try:
            client.disconnect()
        except Exception:
            pass
        return None


def _reconnect_broker(name: str, mqtt_lib, handler, add_log_entry) -> bool:
    state = _get_state(name)
    if not state or state["stop_event"].is_set():
        return False
    old_client = state.get("client")
    if old_client is not None:
        _disconnect_client_safely(state)
    with _BROKER_LOCK:
        state = _BROKER_STATES.get(name)
        if not state or state["stop_event"].is_set():
            return False
        state["client"] = None
        mqtt_clients[name] = None
    client = _connect_broker(state, mqtt_lib, handler, add_log_entry)
    return client is not None


def _healthcheck_loop(mqtt_lib, handler, add_log_entry) -> None:
    while not _HEALTHCHECK_STOP.wait(45):
        with _BROKER_LOCK:
            states = list(_BROKER_STATES.values())
        for state in states:
            if state["stop_event"].is_set():
                continue
            state["last_healthcheck"] = _now_iso()
            client = state.get("client")
            connected = bool(client and getattr(client, "is_connected", lambda: False)())
            thread_alive = bool(getattr(client, "_thread", None) and getattr(client._thread, "is_alive", lambda: False)())
            if connected:
                state["connected"] = True
                continue
            if state.get("connecting"):
                age = _age_seconds(str(state.get("connect_started_at", "")))
                if age is not None and age < 120:
                    continue
                _log(add_log_entry, f"MQTT Broker {state['name']} connect timeout after {int(age or 0)}s")
                _disconnect_client_safely(state)
                with _BROKER_LOCK:
                    if state["name"] in _BROKER_STATES:
                        _BROKER_STATES[state["name"]]["connecting"] = False
                        _BROKER_STATES[state["name"]]["connect_started_at"] = ""
            if client is None or not thread_alive:
                state["last_error"] = state.get("last_error", "") or "client_hung_or_disconnected"
            if not state.get("reconnect_running"):
                _schedule_reconnect(state["name"], mqtt_lib, handler, add_log_entry)


def _start_worker_and_healthcheck(mqtt_lib, handler, add_log_entry) -> None:
    global _HEALTHCHECK_THREAD
    with _BROKER_LOCK:
        if _HEALTHCHECK_THREAD and _HEALTHCHECK_THREAD.is_alive():
            return
        _HEALTHCHECK_STOP.clear()
        _HEALTHCHECK_THREAD = threading.Thread(
            target=_healthcheck_loop,
            args=(mqtt_lib, handler, add_log_entry),
            daemon=True,
            name="mqtt-healthcheck",
        )
        _HEALTHCHECK_THREAD.start()


def _start_worker(state: dict[str, Any], handler, add_log_entry) -> None:
    if state.get("worker_thread") and state["worker_thread"].is_alive():
        return
    thread = threading.Thread(
        target=_broker_worker,
        args=(state, handler, add_log_entry),
        daemon=True,
        name=f"mqtt-worker-{state['name']}",
    )
    state["worker_thread"] = thread
    thread.start()


def _broker_descriptor(broker: dict[str, Any], internal_main: bool = False) -> dict[str, Any]:
    desc = {
        "name": _normalize_name(broker.get("name"), "Hauptbroker" if broker.get("is_main") else "Broker"),
        "host": str(broker.get("host", "") or "").strip(),
        "port": _safe_int(broker.get("port", 1883)),
        "user": str(broker.get("user", "") or "").strip(),
        "password": str(broker.get("password", "") or ""),
        "enabled": bool(broker.get("enabled", True)),
        "is_main": bool(broker.get("is_main", False)),
    }
    if internal_main:
        desc["name"] = "Internen Broker"
    return desc


def get_effective_mqtt_config(config, load_internal_broker_config):
    mqtt_cfg = dict((config or {}).get("mqtt", {}) or {})
    mqtt_cfg.setdefault("host", "127.0.0.1")
    mqtt_cfg.setdefault("port", 1883)
    mqtt_cfg.setdefault("user", "")
    mqtt_cfg.setdefault("password", "")
    mqtt_cfg.setdefault("prefix", "loxone")

    try:
        internal = load_internal_broker_config() if callable(load_internal_broker_config) else {}
    except Exception:
        internal = {}

    if isinstance(internal, dict) and internal.get("enabled") and internal.get("use_as_main"):
        mqtt_cfg = {
            "host": str(internal.get("connect_host") or internal.get("host") or mqtt_cfg.get("host") or "127.0.0.1"),
            "port": _safe_int(internal.get("port", mqtt_cfg.get("port", 1883))),
            "user": str(internal.get("user", "") or "").strip(),
            "password": str(internal.get("password", "") or ""),
            "prefix": mqtt_cfg.get("prefix", "loxone") or "loxone",
            "use_internal_broker": True,
            "internal_broker_host": str(internal.get("host", "") or "").strip(),
        }
    return mqtt_cfg


def build_broker_list(config, load_mqtt_brokers, load_internal_broker_config):
    brokers: list[dict[str, Any]] = []
    effective = get_effective_mqtt_config(config, load_internal_broker_config)
    try:
        internal = load_internal_broker_config() if callable(load_internal_broker_config) else {}
    except Exception:
        internal = {}
    if isinstance(internal, dict) and internal.get("enabled") and internal.get("use_as_main"):
        brokers.append(
            _broker_descriptor(
                {
                    "name": "Hauptbroker",
                    "host": effective.get("host", ""),
                    "port": effective.get("port", 1883),
                    "user": effective.get("user", ""),
                    "password": effective.get("password", ""),
                    "enabled": True,
                    "is_main": True,
                },
                internal_main=True,
            )
        )
    else:
        brokers.append(
            _broker_descriptor(
                {
                    "name": "Hauptbroker",
                    "host": effective.get("host", ""),
                    "port": effective.get("port", 1883),
                    "user": effective.get("user", ""),
                    "password": effective.get("password", ""),
                    "enabled": True,
                    "is_main": True,
                }
            )
        )

    for broker in list(load_mqtt_brokers() or []):
        if not isinstance(broker, dict) or not broker.get("enabled", True):
            continue
        brokers.append(_broker_descriptor(broker))
    return brokers


def record_mqtt_message(broker_name: str, topic: str, payload: Any):
    entry = {
        "broker": str(broker_name or "").strip() or "unbekannt",
        "topic": str(topic or "").strip(),
        "payload": payload,
        "value": payload,
        "timestamp": _now_iso(),
    }
    with _BROKER_LOCK:
        mqtt_monitor_values[f"{entry['broker']}::{entry['topic']}"] = dict(entry)
        state = _BROKER_STATES.get(entry["broker"])
        if state:
            state["last_message_time"] = entry["timestamp"]
            state["last_message_value"] = payload
    return entry


def get_broker_statuses():
    with _BROKER_LOCK:
        states = list(_BROKER_STATES.values())
    statuses = []
    for state in states:
        client = state.get("client")
        connected = bool(state.get("connected") or (client and getattr(client, "is_connected", lambda: False)()))
        statuses.append(
            {
                "name": state.get("name", ""),
                "host": state.get("host", ""),
                "port": state.get("port", 1883),
                "is_main": bool(state.get("is_main", False)),
                "client_id": state.get("client_id", ""),
                "connected": connected,
                "status": "verbunden" if connected else ("verbindet" if state.get("connecting") else "getrennt"),
                "last_connect": state.get("last_connect", ""),
                "last_disconnect": state.get("last_disconnect", ""),
                "last_message_time": state.get("last_message_time", ""),
                "last_processed_time": state.get("last_processed_time", ""),
                "last_error": state.get("last_error", ""),
                "reconnect_running": bool(state.get("reconnect_running", False)),
                "reconnect_attempts": int(state.get("reconnect_attempts", 0)),
                "subscription_count": int(state.get("subscription_count", 0)),
                "queue_mode": state.get("queue_mode", "latest-per-topic"),
                "queue_size": int(state.get("message_queue").qsize() if state.get("message_queue") else 0),
                "max_queue_size": int(state.get("max_queue_size", 500)),
                "dropped_messages": int(state.get("dropped_messages", 0)),
                "processed_messages": int(state.get("processed_messages", 0)),
                "worker_alive": bool(state.get("worker_alive", False)),
            }
        )
    return statuses


def get_broker_status(name: str):
    for status in get_broker_statuses():
        if status.get("name") == name:
            return status
    return {}


def stop_clients(add_log_entry=None):
    global mqtt_client, _HEALTHCHECK_THREAD
    with _BROKER_LOCK:
        states = list(_BROKER_STATES.values())
    for state in states:
        state["stop_event"].set()
        state["connecting"] = False
        state["connected"] = False
        state["reconnect_running"] = False
        timer = state.get("reconnect_timer")
        if timer is not None:
            try:
                timer.cancel()
            except Exception:
                pass
        client = state.get("client")
        if client is not None:
            try:
                client.loop_stop()
            except Exception:
                pass
            try:
                client.disconnect()
            except Exception:
                pass
        state["worker_alive"] = False
        state["last_error"] = state.get("last_error", "")
        queue_lock = state.get("queue_lock")
        try:
            if queue_lock:
                with queue_lock:
                    state.get("pending_by_topic", {}).clear()
                    state.get("pending_topics", set()).clear()
            else:
                state.get("pending_by_topic", {}).clear()
                state.get("pending_topics", set()).clear()
        except Exception:
            pass
        worker = state.get("worker_thread")
        if worker and worker.is_alive():
            try:
                worker.join(timeout=1.0)
            except Exception:
                pass
    _HEALTHCHECK_STOP.set()
    if _HEALTHCHECK_THREAD and _HEALTHCHECK_THREAD.is_alive():
        try:
            _HEALTHCHECK_THREAD.join(timeout=2.0)
        except Exception:
            pass
    with _BROKER_LOCK:
        _BROKER_STATES.clear()
        mqtt_clients.clear()
        mqtt_client = None
        mqtt_monitor_values.clear()
        _HEALTHCHECK_THREAD = None
    if callable(add_log_entry):
        try:
            add_log_entry("MQTT Clients gestoppt")
        except Exception:
            pass


def connect_brokers(config, mqtt_lib, load_mqtt_brokers, load_internal_broker_config, message_handler, add_log_entry):
    global mqtt_client
    stop_clients(add_log_entry=None)
    brokers = build_broker_list(config, load_mqtt_brokers, load_internal_broker_config)
    if not brokers:
        return None, mqtt_clients

    with _BROKER_LOCK:
        _BROKER_STATES.clear()
        mqtt_clients.clear()
        mqtt_client = None

    main_client = None
    for broker in brokers:
        state = _make_broker_state(broker)
        with _BROKER_LOCK:
            _BROKER_STATES[state["name"]] = state
            mqtt_clients[state["name"]] = None
        _start_worker(state, message_handler, add_log_entry)
        client = _connect_broker(state, mqtt_lib, message_handler, add_log_entry)
        if state.get("is_main"):
            main_client = client

    _start_worker_and_healthcheck(mqtt_lib, message_handler, add_log_entry)
    with _BROKER_LOCK:
        mqtt_client = main_client
        if main_client is not None:
            mqtt_clients["Hauptbroker"] = main_client
    return mqtt_client, mqtt_clients


def publish(topic, payload, retain=False, broker_name="Hauptbroker"):
    with _BROKER_LOCK:
        client = mqtt_client if broker_name == "Hauptbroker" else mqtt_clients.get(broker_name)
    if not client:
        return False
    try:
        client.publish(topic, payload, retain=bool(retain))
        return True
    except Exception:
        LOGGER.exception("MQTT publish failed")
        return False


def test_connection(mqtt_lib, host, port, user="", password="", timeout=5):
    client = mqtt_lib.Client(client_id=f"mpgw-test-{uuid4().hex[:12]}")
    if user:
        client.username_pw_set(user, password)
    try:
        client.connect(str(host), int(port), int(timeout))
        client.loop_start()
        time.sleep(0.5)
        client.loop_stop()
        client.disconnect()
    except Exception:
        try:
            client.loop_stop()
        except Exception:
            pass
        try:
            client.disconnect()
        except Exception:
            pass
        raise
