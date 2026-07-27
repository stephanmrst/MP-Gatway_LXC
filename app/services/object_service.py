"""Central object service for MP-Gateway V33."""

import json
import logging
import os
import re
import threading
import time
import traceback
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    from app.services.object_adapter_engine import ADAPTER_TYPES, deserialize_adapter
    from app.models.object_model import (
        GatewayObject,
        new_object_id,
        normalize_source_type,
        normalize_target_type,
        object_name_from_address,
        utc_now_iso,
    )
except ModuleNotFoundError:
    from services.object_adapter_engine import ADAPTER_TYPES, deserialize_adapter
    from models.object_model import (
        GatewayObject,
        new_object_id,
        normalize_source_type,
        normalize_target_type,
        object_name_from_address,
        utc_now_iso,
    )


LOGGER = logging.getLogger(__name__)
APP_ROOT = Path(os.environ.get("MQTT2LOX_APP_ROOT", Path.cwd()))
CONFIG_DIR = Path(os.environ.get("MQTT2LOX_CONFIG_DIR", APP_ROOT / "config"))
OBJECTS_FILE = CONFIG_DIR / "objects.json"
OBJECTS_FILE_LOCK = threading.RLock()
OBJECTS_CACHE_LOCK = threading.RLock()
OBJECTS_CACHE: list["GatewayObject"] = []
OBJECTS_CACHE_MTIME = 0.0
OBJECT_ENDPOINT_INDEX_LOCK = threading.RLock()
OBJECT_ENDPOINT_INDEX: dict[str, list["GatewayObject"]] = {}
OBJECT_ENDPOINT_INDEX_MTIME = 0.0
OBJECT_ROUTE_CACHE_LOCK = threading.RLock()
OBJECT_ROUTE_CACHE: dict[str, list[dict[str, Any]]] = {}
OBJECT_ROUTE_CACHE_MTIME = 0.0
OBJECT_ROUTE_EXPORT_CACHE_LOCK = threading.RLock()
OBJECT_ROUTE_EXPORT_CACHE: dict[str, Any] = {}
OBJECT_ROUTE_EXPORT_CACHE_MTIME = 0.0
LIVE_ROUTE_DISPATCHER = None
LIVE_ROUTE_DISPATCHER_LOCK = threading.RLock()
CORE_FIELDS = {
    "id",
    "name",
    "datatype",
    "unit",
    "enabled",
    "created_at",
    "updated_at",
}
META_FIELDS = {"room", "category", "notes", "icon", "scaling", "legacy_ids", "origin_source", "source", "openccu_topic", "openccu_device", "openccu_channel", "openccu_datapoint"}
LEGACY_FIELDS = {
    "source_type",
    "source_address",
    "target_type",
    "target_address",
    "influx_enabled",
    "type",
    "mqtt_topic",
    "mqtt_json_key",
    "knx_ga",
    "loxone_topic",
    "udp_topic",
    "influx_topic",
    "protocols",
}
SUPPORTED_ROUTE_PAIRS = {
    ("mqtt", "loxone"),
    ("mqtt", "knx"),
    ("mqtt", "udp"),
    ("mqtt", "influx"),
    ("loxone", "mqtt"),
    ("loxone", "knx"),
    ("loxone", "udp"),
    ("loxone", "influx"),
    ("knx", "mqtt"),
    ("knx", "loxone"),
    ("knx", "udp"),
    ("knx", "influx"),
    ("udp", "mqtt"),
    ("udp", "knx"),
    ("udp", "influx"),
}
ROUTE_SOURCE_PRIORITY = ("loxone", "mqtt", "udp")
INTERNAL_OBJECT_ID_RE = re.compile(r"(?:obj_[0-9a-f]{32}|[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", re.IGNORECASE)
OBJECT_LIVE_CACHE: dict[str, dict[str, Any]] = {}
KNX_DPT_LABELS = {
    "1.001": "Switch / Bool",
    "5.001": "Percent 0-100%",
    "5.010": "Counter pulses",
    "7.001": "Unsigned 2 byte",
    "8.001": "Signed 2 byte",
    "9.001": "Temperature °C",
    "9.004": "Illuminance lux",
    "9.005": "Wind speed m/s",
    "9.006": "Pressure Pa",
    "9.007": "Humidity %",
    "12.001": "Unsigned 4 byte",
    "13.001": "Signed 4 byte",
    "14.056": "Power W",
    "14.019": "Current A",
    "14.027": "Voltage V",
    "16.001": "Text",
}


def is_internal_object_id(value: Any) -> bool:
    return bool(INTERNAL_OBJECT_ID_RE.fullmatch(str(value or "").strip()))


def _new_unique_object_id(existing_ids: set[str] | None = None) -> str:
    existing_ids = {str(value or "").strip() for value in (existing_ids or set())}
    object_id = new_object_id()
    while object_id in existing_ids:
        object_id = new_object_id()
    return object_id


def _legacy_ids_from_data(data: dict[str, Any], previous_id: str = "") -> list[str]:
    values = []
    raw = data.get("legacy_ids", [])
    if isinstance(raw, str):
        values.extend(part.strip() for part in raw.split(","))
    elif isinstance(raw, list):
        values.extend(str(part or "").strip() for part in raw)
    for key in ("key", "uuid"):
        values.append(str(data.get(key, "") or "").strip())
    if previous_id:
        values.append(str(previous_id or "").strip())
    result = []
    for value in values:
        if value and value not in result and not is_internal_object_id(value):
            result.append(value)
    return result


def _identity_values(item: GatewayObject) -> set[str]:
    values = {str(item.id or "").strip(), str(item.uuid or "").strip(), str(item.key or "").strip()}
    raw = item.meta.get("legacy_ids", [])
    if isinstance(raw, str):
        values.update(part.strip() for part in raw.split(","))
    elif isinstance(raw, list):
        values.update(str(part or "").strip() for part in raw)
    return {value for value in values if value}


def _now_live_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _migrate_raw_object_ids(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    existing_ids = {str(item.get("id", "") or "").strip() for item in items if is_internal_object_id(item.get("id", ""))}
    changed = False
    migrated = []
    for item in items:
        current = dict(item)
        current_id = str(current.get("id", "") or "").strip()
        if not is_internal_object_id(current_id):
            previous_id = current_id or str(current.get("uuid", "") or current.get("key", "") or "").strip()
            new_id = _new_unique_object_id(existing_ids)
            existing_ids.add(new_id)
            current["id"] = new_id
            legacy_ids = _legacy_ids_from_data(current, previous_id)
            if legacy_ids:
                current["legacy_ids"] = legacy_ids
            current.pop("key", None)
            changed = True
            LOGGER.info("Objekt-ID migriert old_id=%s new_id=%s", previous_id, new_id)
        migrated.append(current)
    return migrated, changed


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on", "ja"}


def _ensure_file() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _objects_file_mtime() -> float:
    try:
        return float(OBJECTS_FILE.stat().st_mtime)
    except OSError:
        return 0.0


def _invalidate_object_caches() -> None:
    global OBJECTS_CACHE_MTIME, OBJECT_ENDPOINT_INDEX_MTIME, OBJECT_ROUTE_CACHE_MTIME, OBJECT_ROUTE_EXPORT_CACHE_MTIME
    with OBJECTS_CACHE_LOCK:
        OBJECTS_CACHE.clear()
        OBJECTS_CACHE_MTIME = 0.0
    with OBJECT_ENDPOINT_INDEX_LOCK:
        OBJECT_ENDPOINT_INDEX.clear()
        OBJECT_ENDPOINT_INDEX_MTIME = 0.0
    with OBJECT_ROUTE_CACHE_LOCK:
        OBJECT_ROUTE_CACHE.clear()
        OBJECT_ROUTE_CACHE_MTIME = 0.0
    with OBJECT_ROUTE_EXPORT_CACHE_LOCK:
        OBJECT_ROUTE_EXPORT_CACHE.clear()
        OBJECT_ROUTE_EXPORT_CACHE_MTIME = 0.0
LIVE_ROUTE_DISPATCHER = None
LIVE_ROUTE_DISPATCHER_LOCK = threading.RLock()


def _rebuild_object_endpoint_index() -> dict[str, list["GatewayObject"]]:
    global OBJECT_ENDPOINT_INDEX_MTIME
    index = _build_object_endpoint_index()
    with OBJECT_ENDPOINT_INDEX_LOCK:
        OBJECT_ENDPOINT_INDEX.clear()
        OBJECT_ENDPOINT_INDEX.update(index)
        OBJECT_ENDPOINT_INDEX_MTIME = _objects_file_mtime()
        return OBJECT_ENDPOINT_INDEX


def _read_raw() -> list[dict[str, Any]]:
    _ensure_file()
    if not OBJECTS_FILE.exists():
        return []
    try:
        with OBJECTS_FILE.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.exception("objects.json konnte nicht gelesen werden: %s", exc)
        return []
    items = raw.get("objects", raw) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        LOGGER.warning("objects.json enthaelt keine Liste")
        return []
    clean_items = [item for item in items if isinstance(item, dict)]
    migrated_items, migrated = _migrate_raw_object_ids(clean_items)
    if migrated:
        _write_raw(migrated_items)
    return migrated_items


def _objects_tmp_path() -> Path:
    return OBJECTS_FILE.with_name(f"{OBJECTS_FILE.name}.{uuid4().hex}.tmp")


def _replace_with_retry(tmp_path: Path) -> None:
    attempts = 8
    delay_seconds = 0.12
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            os.replace(tmp_path, OBJECTS_FILE)
            return
        except OSError as exc:
            last_exc = exc
            winerror = getattr(exc, "winerror", None)
            if not isinstance(exc, PermissionError) and winerror not in {5, 32}:
                raise
            if attempt >= attempts:
                break
            time.sleep(delay_seconds)
            delay_seconds = min(delay_seconds + 0.08, 0.3)
    if last_exc is not None:
        raise last_exc


def _write_raw(items: list[dict[str, Any]]) -> None:
    with OBJECTS_FILE_LOCK:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = _objects_tmp_path()
        try:
            with tmp_path.open("w", encoding="utf-8") as handle:
                json.dump(items, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            _replace_with_retry(tmp_path)
            _invalidate_object_caches()
        except OSError as exc:
            LOGGER.exception("objects.json konnte nicht geschrieben werden: %s", exc)
            raise
        finally:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass


def _source_from_legacy(data: dict[str, Any]) -> tuple[str, str]:
    source_address = str(data.get("source_address", "") or "").strip()
    if source_address:
        return normalize_source_type(data.get("source_type", "mqtt")), source_address
    for source_type, key in (
        ("mqtt", "mqtt_topic"),
        ("knx", "knx_ga"),
        ("loxone", "loxone_topic"),
        ("udp", "udp_topic"),
    ):
        value = str(data.get(key, "") or "").strip()
        if value:
            return source_type, value
    return normalize_source_type(data.get("source_type", "mqtt")), str(data.get("source_address", "") or "").strip()


def _serialize_adapter_payload(protocol: str, payload: dict[str, Any], datatype: str) -> dict[str, Any]:
    payload = dict(payload or {})
    payload["protocol"] = protocol
    payload["enabled"] = _as_bool(payload.get("enabled", True), True)
    payload["direction"] = str(payload.get("direction", "both") or "both")
    payload["datatype"] = str(payload.get("datatype", payload.get("value_type", datatype)) or datatype or "auto")
    return deserialize_adapter(payload).serialize()


def _add_adapter(adapters: dict[str, dict[str, Any]], protocol: str, payload: dict[str, Any], datatype: str) -> None:
    protocol = str(protocol or "").strip().lower()
    if protocol not in ADAPTER_TYPES:
        return
    current = dict(adapters.get(protocol, {}))
    current.update({key: value for key, value in dict(payload or {}).items() if value is not None})
    adapters[protocol] = _serialize_adapter_payload(protocol, current, datatype)


def _apply_udp_default_topic(item: GatewayObject, create_missing: bool = False) -> None:
    adapters = {}
    for adapter in item.adapters:
        protocol = str(getattr(adapter, "protocol", "") or "").strip().lower()
        if protocol:
            adapters[protocol] = adapter
    udp_adapter = adapters.get("udp")
    if udp_adapter is not None and (
        str(getattr(udp_adapter, "udp_topic", "") or "").strip()
        or str(getattr(udp_adapter, "target_topic", "") or "").strip()
    ):
        return
    default_topic = f"{str(item.name or '').strip()}/value" if str(item.name or "").strip() else ""
    if not default_topic:
        return
    target_fields_present = bool(
        udp_adapter is not None
        and (
            str(getattr(udp_adapter, "target_enabled", "") or "").strip()
            or str(getattr(udp_adapter, "target_host", "") or "").strip()
            or str(getattr(udp_adapter, "target_ip", "") or "").strip()
            or str(getattr(udp_adapter, "target_port", "") or "").strip()
        )
    )
    if not target_fields_present and udp_adapter is not None and any(
        str(getattr(udp_adapter, field, "") or "").strip()
        for field in ("source_enabled", "listen_port", "source_topic", "source_json_path", "source_host", "source_port")
    ):
        return
    if udp_adapter is None:
        if not create_missing:
            return
        udp_adapter = ADAPTER_TYPES["udp"](
            enabled=False,
            direction="out",
            datatype=item.datatype or "auto",
            target_enabled=False,
        )
    # A default topic is useful as a suggestion, but it must never activate
    # UDP sending on a freshly created object. Preserve an explicitly saved
    # target_enabled value on existing adapters.
    udp_adapter.udp_topic = default_topic
    udp_adapter.target_payload_mode = str(getattr(udp_adapter, "target_payload_mode", "") or "topic_value") or "topic_value"
    udp_adapter.payload_mode = udp_adapter.target_payload_mode
    if not str(getattr(udp_adapter, "target_host", "") or "").strip() and str(getattr(udp_adapter, "target_ip", "") or "").strip():
        udp_adapter.target_host = str(getattr(udp_adapter, "target_ip", "") or "").strip()
    if not str(getattr(udp_adapter, "target_ip", "") or "").strip() and str(getattr(udp_adapter, "target_host", "") or "").strip():
        udp_adapter.target_ip = str(getattr(udp_adapter, "target_host", "") or "").strip()
    if not str(getattr(udp_adapter, "format", "") or "").strip():
        udp_adapter.format = ""
    adapters["udp"] = udp_adapter
    item.adapters = [adapters[protocol] for protocol in ("mqtt", "udp", "knx", "loxone", "influx") if protocol in adapters]


def _default_influx_measurement(name: str) -> str:
    value = re.sub(r"\s+", "_", str(name or "").strip())
    value = re.sub(r"[^0-9A-Za-z_().-]+", "_", value).strip("_")
    return value or "object_value"


def _default_influx_topic(name: str) -> str:
    value = str(name or "").strip()
    return f"{value}/value" if value else "object/value"


def _apply_influx_defaults(item: GatewayObject, create_missing: bool = False) -> None:
    adapters = {}
    for adapter in item.adapters:
        protocol = str(getattr(adapter, "protocol", "") or "").strip().lower()
        if protocol:
            adapters[protocol] = adapter
    influx_adapter = adapters.get("influx")
    if influx_adapter is None:
        if not create_missing:
            return
        influx_adapter = ADAPTER_TYPES["influx"](enabled=False, direction="out", datatype=item.datatype or "auto")
    if not str(getattr(influx_adapter, "measurement", "") or "").strip():
        influx_adapter.measurement = _default_influx_measurement(item.name)
    if not str(getattr(influx_adapter, "field", "") or "").strip():
        influx_adapter.field = "value"
    if not str(getattr(influx_adapter, "topic", "") or "").strip():
        influx_adapter.topic = _default_influx_topic(item.name)
    adapters["influx"] = influx_adapter
    item.adapters = [adapters[protocol] for protocol in ("mqtt", "udp", "knx", "loxone", "influx") if protocol in adapters]


def _normalize_adapters(data: dict[str, Any], datatype: str, existing: GatewayObject | None = None) -> dict[str, dict[str, Any]]:
    adapters: dict[str, dict[str, Any]] = {}
    if existing:
        for adapter in existing.adapters:
            if isinstance(adapter, dict):
                protocol = str(adapter.get("protocol", "") or "").strip().lower()
                payload = adapter
            else:
                protocol = str(getattr(adapter, "protocol", "") or "").strip().lower()
                payload = adapter.serialize() if hasattr(adapter, "serialize") else {}
            _add_adapter(adapters, protocol, payload, datatype)

    raw_adapters = data.get("adapters")
    if isinstance(raw_adapters, dict):
        for protocol, payload in raw_adapters.items():
            payload = payload if isinstance(payload, dict) else {}
            _add_adapter(adapters, protocol, payload, datatype)
    elif isinstance(raw_adapters, list):
        for payload in raw_adapters:
            if not isinstance(payload, dict):
                continue
            _add_adapter(adapters, payload.get("protocol", ""), payload, datatype)

    raw_protocols = data.get("protocols")
    if isinstance(raw_protocols, dict):
        for protocol, payload in raw_protocols.items():
            if isinstance(payload, dict):
                _add_adapter(adapters, protocol, payload, datatype)

    for protocol in ADAPTER_TYPES:
        payload = data.get(protocol)
        if isinstance(payload, dict):
            _add_adapter(adapters, protocol, payload, datatype)

    source_type, source_address = _source_from_legacy(data)
    if source_address and source_type in ADAPTER_TYPES and source_type not in adapters:
        _add_adapter(adapters, source_type, _legacy_adapter_payload(source_type, source_address, datatype, "in"), datatype)

    target_type = normalize_target_type(data.get("target_type", ""))
    target_address = str(data.get("target_address", "") or "").strip()
    if target_address and target_type in ADAPTER_TYPES and target_type not in adapters:
        _add_adapter(adapters, target_type, _legacy_adapter_payload(target_type, target_address, datatype, "out"), datatype)

    influx_topic = str(data.get("influx_topic", "") or "").strip()
    if (influx_topic or _as_bool(data.get("influx_enabled", False), False)) and "influx" not in adapters:
        _add_adapter(adapters, "influx", {"enabled": True, "direction": "out", "measurement": influx_topic, "datatype": datatype}, datatype)

    return adapters


def _legacy_adapter_payload(protocol: str, address: str, datatype: str, direction: str) -> dict[str, Any]:
    payload: dict[str, Any] = {"enabled": True, "direction": direction, "datatype": datatype}
    if protocol == "mqtt":
        payload["topic"] = address
    elif protocol == "knx":
        payload["group_address"] = address
    elif protocol == "loxone":
        payload["uuid"] = address
        payload["io_address"] = address
    elif protocol == "udp":
        if direction == "in":
            payload["source_enabled"] = True
            payload["listen_port"] = address
            payload["source_topic"] = address
            payload["source_payload_mode"] = "value"
        else:
            payload["target_enabled"] = True
            payload["udp_topic"] = address
            payload["target_host"] = ""
            payload["target_port"] = ""
            payload["target_payload_mode"] = "topic_value"
            payload["payload_mode"] = "topic_value"
    elif protocol == "influx":
        payload["measurement"] = address
    return payload


def _object_from_dict(data: dict[str, Any]) -> GatewayObject:
    source_type, source_address = _source_from_legacy(data)
    now = utc_now_iso()
    object_id = str(data.get("id", "") or "").strip()
    if not is_internal_object_id(object_id):
        object_id = new_object_id()
    name = str(data.get("name", "") or "").strip() or object_name_from_address(source_address)
    datatype = str(data.get("datatype", data.get("type", "auto")) or "auto").strip() or "auto"
    meta = {key: data.get(key, "") for key in META_FIELDS if key in data}
    meta["adapters"] = _normalize_adapters(data, datatype)
    # 34.7.3 migration: older OpenCCU objects stored the CCU-Jack input
    # inside the normal MQTT adapter. Move that input endpoint into dedicated
    # OpenCCU metadata so MQTT remains free as a real output adapter.
    semantic_source = str(meta.get("source") or meta.get("origin_source") or "").strip().lower()
    if semantic_source == "openccu":
        adapters = dict(meta.get("adapters") or {})
        legacy_mqtt = adapters.get("mqtt")
        stored_openccu_topic = str(meta.get("openccu_topic") or "").strip()
        mqtt_topic = str(legacy_mqtt.get("topic") or "").strip() if isinstance(legacy_mqtt, dict) else ""
        # Only remove the historic CCU-Jack source adapter.  A separately
        # configured MQTT target must survive deserialization, even when its
        # direction is "both" (the UI default).
        if isinstance(legacy_mqtt, dict) and stored_openccu_topic and mqtt_topic == stored_openccu_topic:
            adapters.pop("mqtt", None)
            meta["adapters"] = adapters
    return GatewayObject(
        id=object_id,
        name=name,
        datatype=datatype,
        unit=str(data.get("unit", "") or "").strip(),
        enabled=_as_bool(data.get("enabled", True), True),
        created_at=str(data.get("created_at", "") or now),
        updated_at=str(data.get("updated_at", "") or now),
        meta=meta,
    )


def _object_to_dict(item: GatewayObject) -> dict[str, Any]:
    return item.to_dict()


def _payload_from_data(data: dict[str, Any], existing: GatewayObject | None = None) -> GatewayObject:
    now = utc_now_iso()
    source_type, source_address = _source_from_legacy(data)
    name = str(data.get("name", existing.name if existing else "") or "").strip() or object_name_from_address(source_address)
    datatype = str(data.get("datatype", data.get("type", existing.datatype if existing else "auto")) or "auto").strip() or "auto"
    meta = dict(existing.meta) if existing else {}
    if not existing:
        legacy_ids = _legacy_ids_from_data(data, str(data.get("id", "") or "").strip())
        if legacy_ids:
            meta["legacy_ids"] = legacy_ids
    protocol_keys = tuple(ADAPTER_TYPES.keys())
    if any(key in data for key in ("adapters", "protocols", "source_type", "source_address", "target_type", "target_address", "mqtt_topic", "knx_ga", "loxone_topic", "udp_topic", "influx_topic", *protocol_keys)):
        meta["adapters"] = _normalize_adapters(data, datatype, existing)
    for key in META_FIELDS:
        if key in data:
            meta[key] = data.get(key, "")
    semantic_source = str(meta.get("source") or meta.get("origin_source") or "").strip().lower()
    if semantic_source == "openccu":
        adapters = dict(meta.get("adapters") or {})
        legacy_mqtt = adapters.get("mqtt")
        stored_openccu_topic = str(meta.get("openccu_topic") or "").strip()
        mqtt_topic = str(legacy_mqtt.get("topic") or "").strip() if isinstance(legacy_mqtt, dict) else ""
        # Migrate only when the MQTT adapter really is the old CCU-Jack input
        # endpoint.  Do not mistake a new MQTT target for the OpenCCU source.
        if isinstance(legacy_mqtt, dict) and stored_openccu_topic and mqtt_topic == stored_openccu_topic:
            adapters.pop("mqtt", None)
            meta["adapters"] = adapters
    return GatewayObject(
        id=existing.id if existing else (str(data.get("id", "") or "").strip() if is_internal_object_id(data.get("id", "")) else new_object_id()),
        name=name,
        datatype=datatype,
        unit=str(data.get("unit", existing.unit if existing else "") or "").strip(),
        enabled=_as_bool(data.get("enabled", existing.enabled if existing else True), True),
        created_at=str(data.get("created_at", existing.created_at if existing else "") or now),
        updated_at=now,
        meta=meta,
    )


def list_objects() -> list[GatewayObject]:
    global OBJECTS_CACHE_MTIME
    mtime = _objects_file_mtime()
    with OBJECTS_CACHE_LOCK:
        if OBJECTS_CACHE and OBJECTS_CACHE_MTIME == mtime:
            return list(OBJECTS_CACHE)
    objects = []
    for item in _read_raw():
        try:
            objects.append(_object_from_dict(item))
        except Exception as exc:
            LOGGER.exception("Objekt konnte nicht geladen werden: %s", exc)
    with OBJECTS_CACHE_LOCK:
        current_mtime = _objects_file_mtime()
        if OBJECTS_CACHE and OBJECTS_CACHE_MTIME == current_mtime:
            return list(OBJECTS_CACHE)
        OBJECTS_CACHE[:] = objects
        OBJECTS_CACHE_MTIME = current_mtime
        return list(OBJECTS_CACHE)


def _clone_route_export_result(routes: dict[str, list[dict[str, Any]] | dict[str, dict[str, Any]]]) -> dict[str, Any]:
    cloned: dict[str, Any] = {}
    for key, value in (routes or {}).items():
        if isinstance(value, list):
            cloned[key] = [dict(item) if isinstance(item, dict) else deepcopy(item) for item in value]
        elif isinstance(value, dict):
            cloned[key] = {sub_key: dict(sub_value) if isinstance(sub_value, dict) else deepcopy(sub_value) for sub_key, sub_value in value.items()}
        else:
            cloned[key] = deepcopy(value)
    return cloned


def _endpoint_index_key(protocol: str, value: Any) -> str:
    protocol = str(protocol or "").strip().lower()
    value = _normalize_match_value(value)
    if not protocol or not value:
        return ""
    return f"{protocol}:{value}"


def _json_path_lookup(data: Any, key_path: str) -> Any:
    current = data
    path = str(key_path or "").strip().replace(".", "/")
    if not path:
        return current
    segments = [segment for segment in path.split("/") if segment]
    for segment in segments:
        while segment:
            if isinstance(current, dict):
                match = re.match(r"^([^\[\]]+)(.*)$", segment)
                if not match:
                    return None
                key = match.group(1)
                remainder = match.group(2) or ""
                if key not in current:
                    return None
                current = current[key]
                segment = remainder
                continue
            if isinstance(current, list):
                match = re.match(r"^\[(\d+)\](.*)$", segment)
                if not match:
                    if segment.isdigit():
                        index = int(segment)
                        if 0 <= index < len(current):
                            current = current[index]
                            segment = ""
                            continue
                    return None
                index = int(match.group(1))
                remainder = match.group(2) or ""
                if 0 <= index < len(current):
                    current = current[index]
                    segment = remainder
                    continue
                return None
            return None
    return current


def _collect_object_endpoint_keys(item: GatewayObject) -> list[str]:
    keys: list[str] = []
    for protocol, adapter in _adapter_map(item).items():
        if not _is_enabled_adapter(adapter):
            continue
        if protocol == "loxone":
            uuid_value = _normalize_uuid_value(_loxone_source_uuid(adapter))
            io_value = _normalize_match_value(_loxone_source_io(adapter))
            name_value = _normalize_match_value(_loxone_source_name(adapter) or getattr(item, "name", ""))
            visu_name_value = _normalize_match_value(_loxone_source_name(adapter))
            if uuid_value:
                keys.append(_endpoint_index_key("loxone_uuid", uuid_value))
            if io_value:
                keys.append(_endpoint_index_key("loxone_io", io_value))
            if name_value:
                keys.append(_endpoint_index_key("loxone_name", name_value))
            if visu_name_value:
                keys.append(_endpoint_index_key("loxone_name", visu_name_value))
        elif protocol == "mqtt":
            topic = _normalize_match_value(_adapter_value(adapter, "topic"))
            if topic:
                keys.append(_endpoint_index_key("mqtt_topic", topic))
            json_key = _normalize_match_value(_adapter_value(adapter, "json_key"))
            if topic and json_key:
                keys.append(_endpoint_index_key("mqtt_json_key", f"{topic}/{json_key}"))
        elif protocol == "knx":
            ga = _normalize_knx_group_address_value(_adapter_value(adapter, "group_address"))
            if ga:
                keys.append(_endpoint_index_key("knx_ga", ga))
        elif protocol == "udp":
            source_topic = _normalize_match_value(_adapter_value(adapter, "source_topic") or _adapter_value(adapter, "udp_topic") or _adapter_value(adapter, "format"))
            source_json_path = _normalize_match_value(_adapter_value(adapter, "source_json_path"))
            listen_port = _normalize_match_value(_adapter_value(adapter, "listen_port"))
            source_host = _normalize_match_value(_adapter_value(adapter, "source_host"))
            source_port = _normalize_match_value(_adapter_value(adapter, "source_port"))
            target_topic = _normalize_match_value(_adapter_value(adapter, "udp_topic") or _adapter_value(adapter, "target_topic") or _adapter_value(adapter, "format"))
            if source_topic:
                keys.append(_endpoint_index_key("udp_source_topic", source_topic))
                keys.append(_endpoint_index_key("udp_topic", source_topic))
            if source_json_path:
                keys.append(_endpoint_index_key("udp_source_json_path", source_json_path))
            if listen_port:
                keys.append(_endpoint_index_key("udp_listen_port", listen_port))
            if source_host:
                keys.append(_endpoint_index_key("udp_source_host", source_host))
            if source_port:
                keys.append(_endpoint_index_key("udp_source_port", source_port))
            if target_topic:
                keys.append(_endpoint_index_key("udp_topic", target_topic))
    meta = dict(getattr(item, "meta", {}) or {})
    if str(meta.get("source") or meta.get("origin_source") or "").strip().lower() == "openccu":
        openccu_topic = _normalize_match_value(meta.get("openccu_topic"))
        if openccu_topic:
            keys.append(_endpoint_index_key("openccu_topic", openccu_topic))
    return [key for key in keys if key]


def _build_object_endpoint_index() -> dict[str, list[GatewayObject]]:
    index: dict[str, list[GatewayObject]] = {}
    for item in list_objects():
        for key in _collect_object_endpoint_keys(item):
            index.setdefault(key, []).append(item)
    return index


def _get_object_endpoint_index() -> dict[str, list[GatewayObject]]:
    global OBJECT_ENDPOINT_INDEX_MTIME
    with OBJECT_ENDPOINT_INDEX_LOCK:
        mtime = _objects_file_mtime()
        if OBJECT_ENDPOINT_INDEX and OBJECT_ENDPOINT_INDEX_MTIME == mtime:
            return OBJECT_ENDPOINT_INDEX
    return _rebuild_object_endpoint_index()


def lookup_knx_dpt(group_address: Any) -> str:
    """Return the configured object DPT for a KNX group address from the endpoint cache."""
    ga = _normalize_knx_group_address_value(group_address)
    if not ga:
        return ""
    index = _get_object_endpoint_index()
    candidates = index.get(_endpoint_index_key("knx_ga", ga), [])
    for item in sorted(candidates, key=lambda obj: str(getattr(obj, "id", "") or "")):
        adapter = _adapter_map(item).get("knx")
        if not adapter or not _is_enabled_adapter(adapter):
            continue
        if _normalize_knx_group_address_value(_adapter_value(adapter, "group_address")) != ga:
            continue
        dpt = _normalize_knx_dpt(_adapter_value(adapter, "dpt"))
        if dpt:
            return dpt
    return ""


def lookup_knx_dpt_details(group_address: Any) -> dict[str, Any]:
    """Return KNX object lookup details for focused runtime tracing."""
    ga = _normalize_knx_group_address_value(group_address)
    details: dict[str, Any] = {"group_address": ga, "dpt": "", "object": None, "candidates": 0}
    if not ga:
        return details
    index = _get_object_endpoint_index()
    candidates = index.get(_endpoint_index_key("knx_ga", ga), [])
    details["candidates"] = len(candidates)
    for item in sorted(candidates, key=lambda obj: str(getattr(obj, "id", "") or "")):
        adapter = _adapter_map(item).get("knx")
        if not adapter or not _is_enabled_adapter(adapter):
            continue
        if _normalize_knx_group_address_value(_adapter_value(adapter, "group_address")) != ga:
            continue
        dpt = _normalize_knx_dpt(_adapter_value(adapter, "dpt"))
        details["dpt"] = dpt
        details["object"] = {
            "id": str(getattr(item, "id", "") or ""),
            "name": str(getattr(item, "name", "") or ""),
            "datatype": str(getattr(item, "datatype", "") or ""),
            "knx": {
                "group_address": _adapter_value(adapter, "group_address"),
                "dpt": _adapter_value(adapter, "dpt"),
                "enabled": _is_enabled_adapter(adapter),
            },
        }
        return details
    return details


def build_object(data: dict[str, Any]) -> GatewayObject:
    return _payload_from_data(dict(data or {}))


def get_object(object_id: str) -> GatewayObject | None:
    needle = str(object_id or "").strip()
    if not needle:
        return None
    for item in list_objects():
        if needle in _identity_values(item):
            return item
    return None


def create_object(data: dict[str, Any]) -> GatewayObject:
    with OBJECTS_FILE_LOCK:
        objects = [_object_from_dict(item) for item in _read_raw()]
        item = _payload_from_data(dict(data or {}))
        _apply_udp_default_topic(item, create_missing=True)
        _apply_influx_defaults(item, create_missing=True)
        existing_ids = {obj.id for obj in objects}
        while item.id in existing_ids:
            item.id = _new_unique_object_id(existing_ids)
        objects.append(item)
        _write_raw([_object_to_dict(obj) for obj in objects])
        clear_object_runtime_state()
    _rebuild_object_endpoint_index()
    return item


def update_object(object_id: str, data: dict[str, Any]) -> GatewayObject | None:
    with OBJECTS_FILE_LOCK:
        objects = [_object_from_dict(item) for item in _read_raw()]
        for index, current in enumerate(objects):
            if str(object_id or "").strip() in _identity_values(current):
                payload = dict(data or {})
                payload["id"] = current.id
                objects[index] = _payload_from_data(payload, current)
                _apply_udp_default_topic(objects[index], create_missing=False)
                _apply_influx_defaults(objects[index], create_missing=False)
                _write_raw([_object_to_dict(obj) for obj in objects])
                clear_object_runtime_state()
                updated = objects[index]
                break
        else:
            return None
    _rebuild_object_endpoint_index()
    return updated


def delete_object(object_id: str) -> bool:
    with OBJECTS_FILE_LOCK:
        needle = str(object_id or "").strip()
        if not needle:
            return False

        objects = [_object_from_dict(item) for item in _read_raw()]
        remaining: list[GatewayObject] = []
        deleted_cache_ids: list[str] = []
        deleted = False
        for item in objects:
            if needle in _identity_values(item):
                deleted = True
                deleted_cache_ids.append(item.id)
                raw_legacy_ids = item.meta.get("legacy_ids", [])
                if isinstance(raw_legacy_ids, str):
                    deleted_cache_ids.extend(part.strip() for part in raw_legacy_ids.split(",") if part.strip())
                elif isinstance(raw_legacy_ids, list):
                    deleted_cache_ids.extend(str(value or "").strip() for value in raw_legacy_ids if str(value or "").strip())
                continue
            remaining.append(item)

        if not deleted:
            return False

        _write_raw([_object_to_dict(obj) for obj in remaining])
        clear_object_live_statuses(*deleted_cache_ids)
        clear_object_runtime_state()
    _rebuild_object_endpoint_index()
    return True


def clear_object_live_status(object_id: str) -> None:
    object_id = str(object_id or "").strip()
    if object_id:
        OBJECT_LIVE_CACHE.pop(object_id, None)


def clear_object_live_statuses(*object_ids: str) -> bool:
    cleared = False
    for object_id in object_ids:
        object_id = str(object_id or "").strip()
        if not object_id:
            continue
        if OBJECT_LIVE_CACHE.pop(object_id, None) is not None:
            cleared = True
    return cleared


def clear_object_runtime_state() -> bool:
    cleared = bool(OBJECT_LIVE_CACHE)
    OBJECT_LIVE_CACHE.clear()
    return cleared


def toggle_object(object_id: str, enabled: bool) -> GatewayObject | None:
    return update_object(object_id, {"enabled": bool(enabled)})


def serialize_object(item: GatewayObject) -> dict[str, Any]:
    payload = _object_to_dict(item)
    route_report = get_object_route_report(item)
    display_source = str(route_report.get("current_source") or "").strip().lower()
    live = dict(get_object_live_status(item.id) or _live_empty(item))
    payload["live"] = live
    payload["live_value"] = live.get("live_value")
    payload["last_value"] = live.get("last_value")
    payload["last_source"] = live.get("last_source")
    payload["source_protocol"] = live.get("source_protocol")
    payload["input_protocol"] = live.get("input_protocol")
    payload["last_target"] = live.get("last_target")
    payload["target_protocol"] = live.get("target_protocol")
    payload["output_protocol"] = live.get("output_protocol")
    payload["last_update"] = live.get("last_update")
    payload["display_source"] = display_source or "unbekannt"
    payload["route_source"] = display_source or "unbekannt"
    payload["route_sources"] = sorted({
        str(route.get("source") or "").strip().lower()
        for route in (route_report.get("main_routes") or [])
        if isinstance(route, dict) and str(route.get("source") or "").strip()
    })
    payload["route_targets"] = sorted({
        str(route.get("target") or "").strip().lower()
        for route in (route_report.get("main_routes") or [])
        if isinstance(route, dict) and str(route.get("target") or "").strip()
    })
    payload["route_status"] = route_report.get("status") or get_object_route_status(item)
    payload["route_report"] = route_report
    return payload


def _live_empty(item: GatewayObject | None, object_id: str = "") -> dict[str, Any]:
    resolved_id = str(getattr(item, "id", "") or object_id or "").strip()
    return {
        "object_id": resolved_id,
        "live_value": None,
        "value": None,
        "last_value": None,
        "unit": str(getattr(item, "unit", "") or ""),
        "source": "unbekannt",
        "adapter": "unbekannt",
        "original_source": "unbekannt",
        "source_protocol": "unbekannt",
        "last_source": "unbekannt",
        "current_source": "unbekannt",
        "input_protocol": "unbekannt",
        "last_target": "",
        "target_protocol": "",
        "output_protocol": "",
        "source_address": "",
        "recognized_endpoint": "",
        "endpoint": "",
        "timestamp": "",
        "updated_at": "",
        "last_update": "",
        "targets": [],
        "last_target_adapter": "",
        "last_target_adapters": [],
        "status": "unbekannt",
        "live_status": "unbekannt",
    }


def _live_targets(item: GatewayObject, source: str) -> list[str]:
    source = str(source or "").strip().lower()
    targets = []
    for protocol, adapter in _adapter_map(item).items():
        if protocol == source:
            continue
        if _is_enabled_adapter(adapter):
            targets.append(protocol)
    return sorted(set(targets))


def _configured_input_source(item: GatewayObject) -> tuple[str | None, Any | None, dict[str, Any]]:
    adapters = _adapter_map(item)
    candidates: list[tuple[int, int, str, Any]] = []
    protocol_order = {"loxone": 0, "udp": 1, "mqtt": 2, "knx": 3}

    for protocol in ("loxone", "udp", "mqtt", "knx"):
        adapter = adapters.get(protocol)
        if adapter is None or not _is_complete_endpoint(protocol, adapter):
            continue
        if protocol == "loxone" and not _loxone_source_route_active(adapter):
            continue
        if protocol == "udp" and not _udp_source_route_active(adapter):
            continue

        direction = str(getattr(adapter, "direction", "both") or "both").strip().lower()
        if direction not in {"in", "both"}:
            continue
        if protocol == "mqtt" and not _adapter_value(adapter, "topic"):
            continue
        if protocol == "knx" and not _adapter_value(adapter, "group_address"):
            continue

        # Ein expliziter Eingang (direction=in) ist die tatsächliche Quelle.
        # Ein Adapter mit direction=both kann zugleich nur Ziel/Rückkanal sein
        # und darf deshalb einen eindeutigen Eingang nicht überstimmen.
        priority = 0 if direction == "in" else 1
        candidates.append((priority, protocol_order[protocol], protocol, adapter))

    if not candidates:
        return None, None, adapters
    _, _, protocol, adapter = min(candidates, key=lambda entry: (entry[0], entry[1]))
    return protocol, adapter, adapters


def _live_unit(item: GatewayObject, source: str = "") -> str:
    unit = str(getattr(item, "unit", "") or "").strip()
    if unit:
        return unit
    adapter = _adapter_map(item).get(str(source or "").strip().lower())
    return _adapter_value(adapter, "unit") if adapter else ""


def _object_matches_live_source(item: GatewayObject, source: str, **endpoint: Any) -> bool:
    source = str(source or "").strip().lower()
    adapters = _adapter_map(item)
    if source == "openccu":
        topic = _normalize_match_value(endpoint.get("topic"))
        meta = dict(getattr(item, "meta", {}) or {})
        return bool(topic and _normalize_match_value(meta.get("openccu_topic")) == topic)
    adapter = adapters.get(source)
    if not adapter:
        return False
    if source == "mqtt":
        topic = _normalize_match_value(endpoint.get("topic"))
        json_key = _normalize_match_value(endpoint.get("json_key") or endpoint.get("mqtt_json_key"))
        adapter_topic = _normalize_match_value(_adapter_value(adapter, "topic"))
        adapter_json_key = _normalize_match_value(_adapter_value(adapter, "json_key"))
        incoming_broker = _normalize_match_value(endpoint.get("broker") or endpoint.get("source_broker") or "Hauptbroker")
        adapter_broker = _normalize_match_value(_adapter_value(adapter, "source_broker") or "Hauptbroker")
        if incoming_broker != adapter_broker:
            return False
        if topic and adapter_topic == topic:
            if json_key:
                return bool(adapter_json_key and adapter_json_key == json_key)
            return True
        return False
    if source == "loxone":
        uuid_value = _normalize_uuid_value(endpoint.get("loxone_uuid") or endpoint.get("uuid") or endpoint.get("source_uuid"))
        io_value = _normalize_match_value(endpoint.get("loxone_io") or endpoint.get("source_io") or endpoint.get("io_address") or endpoint.get("name") or endpoint.get("source_name"))
        adapter_uuid = _normalize_uuid_value(_adapter_value(adapter, "uuid"))
        adapter_io = _normalize_match_value(_loxone_source_io(adapter))
        adapter_source_uuid = _normalize_uuid_value(_adapter_value(adapter, "source_uuid"))
        adapter_source_name = _normalize_match_value(_adapter_value(adapter, "source_name"))
        return bool(
            (uuid_value and adapter_uuid and uuid_value == adapter_uuid)
            or (uuid_value and adapter_source_uuid and uuid_value == adapter_source_uuid)
            or (io_value and adapter_io and io_value == adapter_io)
            or (io_value and adapter_source_name and io_value == adapter_source_name)
        )
    if source == "knx":
        ga = _normalize_knx_group_address_value(endpoint.get("group_address") or endpoint.get("ga"))
        return bool(ga and _normalize_knx_group_address_value(_adapter_value(adapter, "group_address")) == ga)
    if source == "udp":
        topic = _normalize_match_value(endpoint.get("source_topic") or endpoint.get("udp_topic") or endpoint.get("topic") or endpoint.get("format"))
        json_path = _normalize_match_value(endpoint.get("source_json_path") or endpoint.get("json_key") or endpoint.get("path"))
        sender_host = _normalize_match_value(endpoint.get("udp_source_host") or endpoint.get("source_host"))
        sender_port = _normalize_match_value(endpoint.get("udp_source_port") or endpoint.get("source_port"))
        listen_port = _normalize_match_value(endpoint.get("udp_listen_port") or endpoint.get("listen_port"))
        adapter_topic = _normalize_match_value(_udp_source_topic(adapter))
        adapter_json_path = _normalize_match_value(_udp_source_json_path(adapter))
        adapter_source_host = _normalize_match_value(_adapter_value(adapter, "source_host"))
        adapter_source_port = _normalize_match_value(_adapter_value(adapter, "source_port"))
        adapter_listen_port = _normalize_match_value(_adapter_value(adapter, "listen_port"))
        topic_match = bool(topic and adapter_topic and adapter_topic == topic)
        json_path_match = bool(json_path and adapter_json_path and adapter_json_path == json_path)
        host_ok = bool(not adapter_source_host or (sender_host and sender_host == adapter_source_host))
        sender_port_ok = bool(not adapter_source_port or (sender_port and sender_port == adapter_source_port))
        listen_port_ok = bool(not adapter_listen_port or (listen_port and listen_port == adapter_listen_port))
        if adapter_topic or adapter_json_path:
            return bool((topic_match or json_path_match) and host_ok and sender_port_ok and listen_port_ok)
        return bool(
            host_ok
            and sender_port_ok
            and (
                (listen_port and adapter_listen_port and listen_port == adapter_listen_port)
                or (sender_host and adapter_source_host and sender_host == adapter_source_host)
                or (sender_port and adapter_source_port and sender_port == adapter_source_port)
            )
        )
    return False


def _live_lookup_candidates(source: str, **endpoint: Any) -> list[tuple[str, str, str]]:
    source = str(source or "").strip().lower()
    if source == "openccu":
        topic = _normalize_match_value(endpoint.get("topic") or endpoint.get("source_topic"))
        return [("openccu_topic", topic, "openccu.topic")]
    if source == "loxone":
        uuid_value = _normalize_uuid_value(endpoint.get("loxone_uuid") or endpoint.get("uuid") or endpoint.get("source_uuid"))
        io_value = _normalize_match_value(endpoint.get("loxone_io") or endpoint.get("source_io") or endpoint.get("io_address") or endpoint.get("io") or endpoint.get("name") or endpoint.get("source_name"))
        name_value = _normalize_match_value(endpoint.get("name") or endpoint.get("visu_name") or endpoint.get("source_name"))
        return [
            ("loxone_uuid", uuid_value, "loxone.uuid"),
            ("loxone_io", io_value, "loxone.io_address"),
            ("loxone_name", name_value, "object.name"),
        ]
    if source == "mqtt":
        topic = _normalize_match_value(endpoint.get("topic"))
        json_key = _normalize_match_value(endpoint.get("json_key") or endpoint.get("mqtt_json_key"))
        candidates = [("mqtt_topic", topic, "mqtt.topic")]
        if topic and json_key:
            candidates.append(("mqtt_json_key", f"{topic}/{json_key}", "mqtt.topic/json_key"))
        return candidates
    if source == "knx":
        ga = _normalize_knx_group_address_value(endpoint.get("group_address") or endpoint.get("ga"))
        return [("knx_ga", ga, "knx.group_address")]
    if source == "udp":
        udp_topic = _normalize_match_value(endpoint.get("source_topic") or endpoint.get("udp_topic") or endpoint.get("topic") or endpoint.get("format"))
        source_json_path = _normalize_match_value(endpoint.get("source_json_path") or endpoint.get("json_key") or endpoint.get("path"))
        udp_source_host = _normalize_match_value(endpoint.get("udp_source_host") or endpoint.get("source_host"))
        udp_source_port = _normalize_match_value(endpoint.get("udp_source_port") or endpoint.get("source_port"))
        udp_listen_port = _normalize_match_value(endpoint.get("udp_listen_port") or endpoint.get("listen_port"))
        candidates = [("udp_source_topic", udp_topic, "udp.source_topic")]
        if udp_topic:
            candidates.append(("udp_topic", udp_topic, "udp.topic"))
        if source_json_path:
            candidates.append(("udp_source_json_path", source_json_path, "udp.source_json_path"))
        if udp_source_host:
            candidates.append(("udp_source_host", udp_source_host, "udp.source_host"))
        if udp_source_port:
            candidates.append(("udp_source_port", udp_source_port, "udp.source_port"))
        if udp_listen_port:
            candidates.append(("udp_listen_port", udp_listen_port, "udp.listen_port"))
        return candidates
    return [
        ("loxone_uuid", _normalize_uuid_value(endpoint.get("loxone_uuid") or endpoint.get("uuid") or endpoint.get("source_uuid")), "loxone.uuid"),
        ("loxone_io", _normalize_match_value(endpoint.get("loxone_io") or endpoint.get("io_address") or endpoint.get("io") or endpoint.get("name") or endpoint.get("source_name")), "loxone.io_address"),
        ("mqtt_topic", _normalize_match_value(endpoint.get("topic")), "mqtt.topic"),
        ("mqtt_json_key", _normalize_match_value(endpoint.get("topic") and endpoint.get("json_key") and f"{endpoint.get('topic')}/{endpoint.get('json_key')}"), "mqtt.topic/json_key"),
        ("knx_ga", _normalize_knx_group_address_value(endpoint.get("group_address") or endpoint.get("ga")), "knx.group_address"),
        ("udp_source_topic", _normalize_match_value(endpoint.get("source_topic") or endpoint.get("udp_topic") or endpoint.get("topic") or endpoint.get("format")), "udp.source_topic"),
        ("udp_source_json_path", _normalize_match_value(endpoint.get("source_json_path") or endpoint.get("json_key") or endpoint.get("path")), "udp.source_json_path"),
    ]


def _live_debug_snapshot(item: GatewayObject) -> dict[str, Any]:
    adapters = _adapter_map(item)
    loxone = adapters.get("loxone")
    mqtt = adapters.get("mqtt")
    knx = adapters.get("knx")
    udp = adapters.get("udp")
    return {
        "object_id": item.id,
        "name": item.name,
        "loxone": {
            "uuid": _adapter_value(loxone, "uuid") if loxone else "",
            "io_address": _adapter_value(loxone, "io_address") if loxone else "",
            "name": _loxone_source_name(loxone) if loxone else "",
            "source_uuid": _loxone_source_uuid(loxone) if loxone else "",
            "target_uuid": _loxone_target_uuid(loxone) if loxone else "",
            "target_name": _loxone_target_name(loxone) if loxone else "",
            "target_room": _loxone_target_room(loxone) if loxone else "",
            "target_category": _loxone_target_category(loxone) if loxone else "",
            "target_type": _loxone_target_type(loxone) if loxone else "",
        },
        "mqtt": {
            "topic": _adapter_value(mqtt, "topic") if mqtt else "",
            "json_key": _adapter_value(mqtt, "json_key") if mqtt else "",
        },
        "knx": {
            "group_address": _adapter_value(knx, "group_address") if knx else "",
        },
        "udp": {
            "address": _endpoint_address("udp", udp) if udp else "",
            "format": _adapter_value(udp, "format") if udp else "",
            "source_topic": _udp_source_topic(udp) if udp else "",
            "source_json_path": _udp_source_json_path(udp) if udp else "",
            "source_host": _adapter_value(udp, "source_host") if udp else "",
            "source_port": _adapter_value(udp, "source_port") if udp else "",
            "listen_port": _adapter_value(udp, "listen_port") if udp else "",
            "target_topic": _udp_target_topic(udp) if udp else "",
            "target_host": _adapter_value(udp, "target_host") if udp else "",
            "target_ip": _adapter_value(udp, "target_ip") if udp else "",
            "target_port": _adapter_value(udp, "target_port") if udp else "",
        },
    }


def set_live_route_dispatcher(dispatcher) -> None:
    """Register the runtime router called after a live value was stored.

    The object service stays protocol-neutral; the core runtime supplies the
    actual target dispatcher.
    """
    global LIVE_ROUTE_DISPATCHER
    with LIVE_ROUTE_DISPATCHER_LOCK:
        LIVE_ROUTE_DISPATCHER = dispatcher


def _dispatch_recorded_live_values(updates, source, value, endpoint) -> None:
    if not updates or not bool(endpoint.get("route_after_record", False)):
        return
    with LIVE_ROUTE_DISPATCHER_LOCK:
        dispatcher = LIVE_ROUTE_DISPATCHER
    if not callable(dispatcher):
        LOGGER.warning("Live routing requested but runtime dispatcher is not registered")
        return
    source = str(endpoint.get("original_source") or source or "").strip().lower()
    if source in {"mqtt", "openccu"}:
        source_ref = str(endpoint.get("topic") or "").strip()
    elif source == "knx":
        source_ref = str(endpoint.get("group_address") or endpoint.get("ga") or "").strip()
    elif source == "udp":
        source_ref = str(endpoint.get("source_topic") or endpoint.get("udp_topic") or endpoint.get("topic") or "").strip()
    elif source == "loxone":
        source_ref = str(endpoint.get("loxone_io") or endpoint.get("io_address") or endpoint.get("name") or "").strip()
    else:
        source_ref = str(endpoint.get("topic") or endpoint.get("source_ref") or "").strip()
    metadata = dict(endpoint)
    metadata.pop("route_after_record", None)
    metadata.setdefault("use_event_value", False)
    trace_id = f"live-{time.time_ns()}-{threading.get_ident()}"
    metadata["routing_trace_id"] = trace_id
    object_ids = [
        str((entry or {}).get("object_id") or ((entry or {}).get("object") or {}).get("id") or "").strip()
        for entry in (updates or [])
    ]
    object_ids = [item for item in object_ids if item]
    stack_text = " | ".join(
        line.strip().replace("\n", " ")
        for line in traceback.format_stack(limit=10)[:-1]
    )
    LOGGER.warning(
        "ROUTING REQUEST trace=%s objects=%s source=%s ref=%s value=%r thread=%s stack=%s",
        trace_id, object_ids, source, source_ref, value, threading.get_ident(), stack_text,
    )
    try:
        dispatcher(updates, source, source_ref, value, metadata=metadata)
    except Exception:
        LOGGER.exception("Routing after record_live_value failed source=%s ref=%s", source, source_ref)


def record_live_value(source: str, value: Any, timestamp: str = "", **endpoint: Any) -> list[dict[str, Any]]:
    """Record a runtime-only live value for all objects matching the source endpoint."""
    incoming_source = str(source or "").strip().lower() or "unbekannt"
    original_source = str(endpoint.get("original_source") or incoming_source or "").strip().lower() or "unbekannt"
    target_adapter = str(endpoint.get("target_adapter") or "").strip().lower()
    ignored_echo = bool(endpoint.get("ignored_echo", False))
    timestamp = str(timestamp or "").strip() or _now_live_iso()
    updates = []
    index = _get_object_endpoint_index()
    lookup_candidates = _live_lookup_candidates(incoming_source, **endpoint)
    matched_items: list[tuple[GatewayObject, str, str]] = []
    seen_ids = set()
    for key, raw_value, endpoint_name in lookup_candidates:
        key = _endpoint_index_key(key, raw_value)
        if not key:
            continue
        for item in index.get(key, []):
            if item.id in seen_ids:
                continue
            if not _object_matches_live_source(item, incoming_source, **endpoint):
                continue
            seen_ids.add(item.id)
            matched_items.append((item, raw_value, endpoint_name))
    for item, source_address, recognized_endpoint in matched_items:
        previous = OBJECT_LIVE_CACHE.get(item.id) or {}
        stored_source = original_source
        skip_update = False
        item_value = value
        item_source_address = source_address
        item_recognized_endpoint = recognized_endpoint
        adapters = _adapter_map(item)
        mqtt_adapter = adapters.get("mqtt")
        mqtt_json_key = _normalize_match_value(_adapter_value(mqtt_adapter, "json_key")) if mqtt_adapter else ""
        item_meta = dict(getattr(item, "meta", {}) or {})
        semantic_source = str(item_meta.get("source") or item_meta.get("origin_source") or "").strip().lower()
        # CCU-Jack liefert Statuswerte als {s, ts, v}. Bei OpenCCU-Objekten ist
        # 'v' der eigentliche Livewert; ältere Objekte besitzen noch keinen
        # json_key und werden deshalb hier rückwärtskompatibel entpackt.
        if incoming_source in {"mqtt", "openccu"} and semantic_source == "openccu" and not mqtt_json_key:
            mqtt_payload = value
            if isinstance(mqtt_payload, str):
                try:
                    mqtt_payload = json.loads(mqtt_payload)
                except Exception:
                    pass
            if isinstance(mqtt_payload, dict) and "v" in mqtt_payload:
                item_value = mqtt_payload.get("v")
                item_recognized_endpoint = f"{recognized_endpoint} / v"
        if incoming_source == "mqtt" and mqtt_json_key:
            mqtt_payload = value
            if isinstance(mqtt_payload, str):
                try:
                    mqtt_payload = json.loads(mqtt_payload)
                except Exception:
                    pass
            extracted = _json_path_lookup(mqtt_payload, mqtt_json_key)
            if extracted is None:
                LOGGER.info(
                    "MQTT json key not matched object_id=%s topic=%s json_key=%s value=%s",
                    item.id,
                    source_address,
                    mqtt_json_key,
                    value,
                )
                continue
            item_value = extracted
            item_source_address = f"{source_address}/{mqtt_json_key}" if source_address else mqtt_json_key
            item_recognized_endpoint = f"{recognized_endpoint} / {mqtt_json_key}"
        udp_adapter = adapters.get("udp")
        udp_source_json_path = _normalize_match_value(_udp_source_json_path(udp_adapter)) if udp_adapter else ""
        udp_source_mode = _normalize_match_value(_udp_source_payload_mode(udp_adapter)) if udp_adapter else ""
        if incoming_source == "udp" and udp_source_mode == "json" and udp_source_json_path:
            udp_payload = endpoint.get("json_data")
            if udp_payload is None:
                udp_payload = endpoint.get("payload_raw")
            if udp_payload is None:
                udp_payload = value
            if isinstance(udp_payload, str):
                try:
                    udp_payload = json.loads(udp_payload)
                except Exception:
                    try:
                        udp_payload = json.loads(udp_payload.strip())
                    except Exception:
                        pass
            extracted = _json_path_lookup(udp_payload, udp_source_json_path)
            if extracted is None:
                LOGGER.warning(
                    "JSON path not found object_id=%s source_json_path=%s value=%s payload_type=%s",
                    item.id,
                    udp_source_json_path,
                    value,
                    type(udp_payload).__name__,
                )
                continue
            item_value = extracted
            item_source_address = f"{source_address}/{udp_source_json_path}" if source_address else udp_source_json_path
            item_recognized_endpoint = f"{recognized_endpoint} / {udp_source_json_path}"
        previous_source = str(previous.get("source_protocol") or previous.get("last_source") or previous.get("original_source") or previous.get("source") or "").lower()
        if (
            incoming_source == "mqtt"
            and previous_source
            and previous_source != "mqtt"
            and str(previous.get("value")) == str(item_value)
            and "mqtt" in (previous.get("targets") or _live_targets(item, previous_source))
        ):
            stored_source = previous_source
            ignored_echo = True
            skip_update = True

        if skip_update:
            LOGGER.info(
                "Live source preserved object_id=%s incoming_source=%s stored_source=%s target_adapter=%s value=%s ignored_echo=%s",
                item.id,
                incoming_source,
                stored_source,
                target_adapter or "mqtt",
                item_value,
                str(bool(ignored_echo)).lower(),
            )
            updates.append(dict(previous))
            continue

        payload = update_object_live_value(
            item.id,
            item_value,
            source=stored_source,
            endpoint=item_recognized_endpoint,
            source_address=item_source_address,
            timestamp=timestamp,
            status="aktiv",
            target_adapter=target_adapter,
            targets=_live_targets(item, stored_source),
            unit=_live_unit(item, stored_source),
        )
        LOGGER.info(
            "Live value stored object_id=%s incoming_source=%s stored_source=%s target_adapter=%s value=%s ignored_echo=%s",
            item.id,
            incoming_source,
            stored_source,
            target_adapter,
            item_value,
            str(bool(ignored_echo)).lower(),
        )
        updates.append(dict(payload))
    if incoming_source == "loxone" and not matched_items:
        all_objects = list(list_objects())
        LOGGER.info(
            "Live value not matched source=%s value=%s loxone_uuid=%s loxone_io=%s name=%s mqtt_topic=%s knx_ga=%s udp_address=%s object_id=%s objects=%s object_fields=%s",
            incoming_source,
            value,
            endpoint.get("loxone_uuid") or endpoint.get("uuid") or "",
            endpoint.get("loxone_io") or endpoint.get("io_address") or "",
            endpoint.get("name") or endpoint.get("visu_name") or "",
            endpoint.get("topic") or "",
            endpoint.get("group_address") or endpoint.get("ga") or "",
            endpoint.get("udp_topic") or endpoint.get("topic") or endpoint.get("format") or "",
            endpoint.get("object_id") or "",
            len({item.id for bucket in index.values() for item in bucket}),
            [_live_debug_snapshot(item) for item in all_objects[:10]],
        )
    _dispatch_recorded_live_values(updates, original_source, value, endpoint)
    return updates


def update_object_live_value(
    object_id: str,
    value: Any,
    source: str = "",
    endpoint: str = "",
    source_address: str = "",
    timestamp: str = "",
    status: str = "aktiv",
    target_adapter: str = "",
    targets: list[str] | None = None,
    unit: str = "",
) -> dict[str, Any]:
    """Set the central runtime-only object live state for one object."""
    object_id = str(object_id or "").strip()
    if not object_id:
        return {}
    source = str(source or "unbekannt").strip().lower() or "unbekannt"
    target_adapter = str(target_adapter or "").strip().lower()
    timestamp = str(timestamp or "").strip() or _now_live_iso()
    current = dict(OBJECT_LIVE_CACHE.get(object_id) or {})
    item = get_object(object_id)
    unit = str(unit or current.get("unit") or (getattr(item, "unit", "") if item else "") or "").strip()
    live_status = str(status or "aktiv").strip() or "aktiv"
    last_target_adapters = list(current.get("last_target_adapters") or [])
    if target_adapter and target_adapter not in last_target_adapters:
        last_target_adapters.append(target_adapter)
    elif target_adapter and not last_target_adapters:
        last_target_adapters = [target_adapter]
    display_source = source.upper() if source and source != "unbekannt" else "unbekannt"
    payload = {
        "object_id": object_id,
        "live_value": value,
        "value": value,
        "last_value": value,
        "unit": unit,
        "source": display_source,
        "adapter": display_source,
        "original_source": source,
        "source_protocol": source,
        "last_source": source,
        "current_source": source,
        "input_protocol": source,
        "last_target": target_adapter,
        "target_protocol": target_adapter,
        "output_protocol": target_adapter,
        "source_address": str(source_address or current.get("source_address") or "").strip(),
        "recognized_endpoint": str(endpoint or current.get("recognized_endpoint") or "").strip(),
        "endpoint": str(endpoint or current.get("endpoint") or current.get("recognized_endpoint") or "").strip(),
        "timestamp": timestamp,
        "updated_at": timestamp,
        "last_update": timestamp,
        "targets": list(targets if targets is not None else current.get("targets") or []),
        "last_target_adapter": target_adapter,
        "last_target_adapters": last_target_adapters,
        "status": live_status,
        "live_status": live_status,
    }
    OBJECT_LIVE_CACHE[object_id] = payload
    return dict(payload)


def record_live_target(object_id: str, target_adapter: str, value: Any = None, original_source: str = "loxone") -> None:
    object_id = str(object_id or "").strip()
    target_adapter = str(target_adapter or "").strip().lower()
    if not object_id or not target_adapter:
        return
    current = OBJECT_LIVE_CACHE.get(object_id)
    if not current:
        return
    targets = list(current.get("last_target_adapters") or [])
    if target_adapter not in targets:
        targets.append(target_adapter)
    current["last_target_adapter"] = target_adapter
    current["last_target_adapters"] = targets
    current["last_target"] = target_adapter
    current["target_protocol"] = target_adapter
    current["output_protocol"] = target_adapter
    current["live_value"] = current.get("value") if value is None else value
    current["last_value"] = current.get("value") if value is None else value
    current["value"] = current.get("value") if value is None else value
    current["last_update"] = current.get("last_update") or _now_live_iso()
    OBJECT_LIVE_CACHE[object_id] = current
    LOGGER.info(
        "Live target recorded object_id=%s incoming_source=%s stored_source=%s target_adapter=%s value=%s ignored_echo=%s",
        object_id,
        original_source,
        current.get("source_protocol") or current.get("last_source") or current.get("source") or "unbekannt",
        target_adapter,
        current.get("value") if value is None else value,
        "false",
    )


def get_object_live_status(object_id: str) -> dict[str, Any] | None:
    item = get_object(object_id)
    if item is None:
        return None
    return dict(_resolved_live_status(item))


def list_object_live_status() -> list[dict[str, Any]]:
    result = []
    for item in list_objects():
        result.append(dict(_resolved_live_status(item)))
    return result


def _resolved_live_status(item: GatewayObject) -> dict[str, Any]:
    live = dict(_live_empty(item))
    live.update(dict(OBJECT_LIVE_CACHE.get(item.id) or {}))

    # Fachliche Objektquelle und technischer Transport sind zwei getrennte Dinge.
    # Bei OpenCCU bleibt die Quelle deshalb OpenCCU, auch wenn der Live-Wert über
    # den MQTT-Adapter empfangen wurde.
    meta = dict(getattr(item, "meta", {}) or {})
    semantic_source = str(meta.get("source") or meta.get("origin_source") or "").strip().lower()
    transport_source = str(
        live.get("source_protocol")
        or live.get("last_source")
        or live.get("current_source")
        or live.get("original_source")
        or live.get("adapter")
        or ""
    ).strip().lower()
    configured_source, configured_adapter, _ = _configured_input_source(item)
    display_source = semantic_source or configured_source or transport_source or "unbekannt"

    if configured_adapter is not None and not str(live.get("source_address") or "").strip():
        live["source_address"] = _endpoint_address(configured_source or transport_source, configured_adapter)
    live["recognized_endpoint"] = live.get("recognized_endpoint") or live.get("source_address") or ""
    technical_source = transport_source or configured_source or "unbekannt"
    live["transport_adapter"] = technical_source
    live["adapter"] = technical_source
    # Technische Live-/Routingfelder bleiben beim echten Eingangsadapter.
    # Nur display_source beschreibt die fachliche Herkunft.
    live["input_protocol"] = technical_source
    live["source_protocol"] = technical_source
    live["last_source"] = technical_source
    live["current_source"] = technical_source
    live["source"] = technical_source
    live["original_source"] = technical_source
    live.setdefault("last_target", str(live.get("last_target") or ""))
    live.setdefault("target_protocol", str(live.get("target_protocol") or ""))
    live.setdefault("output_protocol", str(live.get("output_protocol") or ""))
    route_report = get_object_route_report(item)
    route_source = str(route_report.get("current_source") or "").strip().lower()
    live["route_source"] = route_source or ""
    # Karten, Filter und Explorer zeigen ausschließlich die fachliche Objektquelle.
    # Der technische Empfangsweg steht separat in transport_adapter/adapter.
    live["display_source"] = display_source or route_source or "unbekannt"
    live["route_sources"] = sorted({
        str(route.get("source") or "").strip().lower()
        for route in (route_report.get("main_routes") or [])
        if isinstance(route, dict) and str(route.get("source") or "").strip()
    })
    live["route_targets"] = sorted({
        str(route.get("target") or "").strip().lower()
        for route in (route_report.get("main_routes") or [])
        if isinstance(route, dict) and str(route.get("target") or "").strip()
    })
    return live


def get_udp_source_listen_ports() -> list[str]:
    ports: list[str] = []
    for item in list_objects():
        for adapter in _adapter_map(item).values():
            if str(getattr(adapter, "protocol", "") or "").strip().lower() != "udp":
                continue
            if not _udp_source_enabled(adapter):
                continue
            listen_port = _normalize_match_value(_adapter_value(adapter, "listen_port"))
            if listen_port and listen_port not in ports:
                ports.append(listen_port)
    if not ports:
        try:
            from app.services.config import load_config as _load_config
        except ModuleNotFoundError:
            from services.config import load_config as _load_config
        try:
            cfg = _load_config() or {}
            legacy_port = str((cfg.get("udp_input") or {}).get("port", "") or "").strip()
            if legacy_port and legacy_port not in ports:
                ports.append(legacy_port)
        except Exception:
            pass
    return ports


def _adapter_map(item: GatewayObject) -> dict[str, Any]:
    adapters = {}
    for adapter in item.adapters:
        if isinstance(adapter, dict):
            adapter = deserialize_adapter(adapter)
        protocol = str(getattr(adapter, "protocol", "") or "").strip().lower()
        if protocol:
            adapters[protocol] = adapter
    return adapters


def _adapter_value(adapter: Any, name: str) -> str:
    return str(getattr(adapter, name, "") or "").strip()


def _loxone_source_uuid(adapter: Any) -> str:
    return _adapter_value(adapter, "source_uuid") or _adapter_value(adapter, "uuid")


def _loxone_source_io(adapter: Any) -> str:
    return _adapter_value(adapter, "source_io") or _adapter_value(adapter, "io_address")


def _loxone_source_name(adapter: Any) -> str:
    return _adapter_value(adapter, "source_name") or _adapter_value(adapter, "visu_name")


def _loxone_source_room(adapter: Any) -> str:
    return _adapter_value(adapter, "source_room") or _adapter_value(adapter, "room")


def _loxone_source_category(adapter: Any) -> str:
    return _adapter_value(adapter, "source_category") or _adapter_value(adapter, "control_type") or _adapter_value(adapter, "type")


def _loxone_target_uuid(adapter: Any) -> str:
    return _adapter_value(adapter, "target_uuid") or _loxone_source_uuid(adapter)


def _loxone_target_uuid_explicit(adapter: Any) -> str:
    return _adapter_value(adapter, "target_uuid")


def _loxone_target_name(adapter: Any) -> str:
    return _adapter_value(adapter, "target_name") or _loxone_source_name(adapter) or _adapter_value(adapter, "name")


def _loxone_target_room(adapter: Any) -> str:
    return _adapter_value(adapter, "target_room") or _adapter_value(adapter, "room")


def _loxone_target_category(adapter: Any) -> str:
    return _adapter_value(adapter, "target_category") or _adapter_value(adapter, "control_type") or _adapter_value(adapter, "type")


def _loxone_target_type(adapter: Any) -> str:
    return _adapter_value(adapter, "target_type") or _loxone_target_category(adapter)


def _loxone_target_enabled(adapter: Any) -> bool:
    value = getattr(adapter, "target_enabled", None)
    if value is None:
        value = getattr(adapter, "active", None)
    if value is None and _loxone_target_uuid_explicit(adapter):
        value = True
    return bool(value)


def _loxone_source_enabled(adapter: Any) -> bool:
    value = getattr(adapter, "source_enabled", None)
    if value is None:
        value = getattr(adapter, "enabled", None)
    if value is None and (_loxone_source_uuid(adapter) or _loxone_source_io(adapter) or _loxone_source_name(adapter)):
        value = True
    return bool(value and (_loxone_source_uuid(adapter) or _loxone_source_io(adapter) or _loxone_source_name(adapter)))


def _loxone_source_route_active(adapter: Any) -> bool:
    return bool(_loxone_source_enabled(adapter) and (_loxone_source_uuid(adapter) or _loxone_source_io(adapter) or _loxone_source_name(adapter)))


def _loxone_gateway_configured() -> bool:
    config_path = CONFIG_DIR / "config.json"
    try:
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                cfg = json.load(handle) or {}
            return bool(str((cfg.get("loxone") or {}).get("host", "")).strip())
    except Exception:
        LOGGER.exception("Loxone-Gateway-Check ueber config.json fehlgeschlagen")
    try:
        try:
            from app.services.config import load_config as _load_config
        except ModuleNotFoundError:
            from services.config import load_config as _load_config
        cfg = _load_config() or {}
        return bool(str((cfg.get("loxone") or {}).get("host", "")).strip())
    except Exception:
        return False


def _loxone_target_route_active(adapter: Any) -> bool:
    return bool(_loxone_target_enabled(adapter) and _loxone_target_uuid_explicit(adapter) and _loxone_gateway_configured())


def _udp_source_topic(adapter: Any) -> str:
    return _adapter_value(adapter, "source_topic") or _adapter_value(adapter, "udp_topic") or _adapter_value(adapter, "format")


def _udp_source_json_path(adapter: Any) -> str:
    return _adapter_value(adapter, "source_json_path")


def _udp_source_payload_mode(adapter: Any) -> str:
    return _adapter_value(adapter, "source_payload_mode") or _adapter_value(adapter, "payload_mode") or "value"


def _udp_target_topic(adapter: Any) -> str:
    return _adapter_value(adapter, "udp_topic") or _adapter_value(adapter, "target_topic") or _adapter_value(adapter, "format")


def _udp_target_payload_mode(adapter: Any) -> str:
    return _adapter_value(adapter, "target_payload_mode") or _adapter_value(adapter, "payload_mode") or "topic_value"


def _udp_source_enabled(adapter: Any) -> bool:
    value = getattr(adapter, "source_enabled", None)
    if value is None:
        value = getattr(adapter, "enabled", None)
    if value is None and (_adapter_value(adapter, "listen_port") or _udp_source_topic(adapter) or _udp_source_json_path(adapter)):
        value = True
    return bool(value and (_adapter_value(adapter, "listen_port") or _udp_source_topic(adapter) or _udp_source_json_path(adapter)))


def _udp_target_enabled(adapter: Any) -> bool:
    value = getattr(adapter, "target_enabled", None)
    if value is None:
        value = getattr(adapter, "enabled", None)
    if value is None and (_adapter_value(adapter, "target_host") or _adapter_value(adapter, "target_ip") or _adapter_value(adapter, "target_port") or _udp_target_topic(adapter)):
        value = True
    return bool(value and (_adapter_value(adapter, "target_host") or _adapter_value(adapter, "target_ip") or _adapter_value(adapter, "target_port") or _udp_target_topic(adapter)))


def _udp_source_route_active(adapter: Any) -> bool:
    return bool(_udp_source_enabled(adapter) and _adapter_value(adapter, "listen_port"))


def _udp_target_route_active(adapter: Any) -> bool:
    return bool(_udp_target_enabled(adapter) and (_adapter_value(adapter, "target_port") or _adapter_value(adapter, "target_host") or _adapter_value(adapter, "target_ip")))


def _loxone_display_label(adapter: Any, role: str = "source") -> str:
    role = str(role or "").strip().lower()
    if role == "target":
        parts = [
            _loxone_target_name(adapter),
            _loxone_target_room(adapter),
            _loxone_target_category(adapter),
        ]
        fallback = _loxone_target_uuid(adapter) or _loxone_source_io(adapter)
    else:
        parts = [
            _loxone_source_name(adapter) or _loxone_source_io(adapter),
            _loxone_source_room(adapter),
            _loxone_source_category(adapter),
        ]
        fallback = _loxone_source_uuid(adapter) or _loxone_source_io(adapter)
    parts = [part for part in parts if part]
    return " · ".join(parts) if parts else fallback


def _udp_display_label(adapter: Any, role: str = "source") -> str:
    role = str(role or "").strip().lower()
    if role == "target":
        topic = _udp_target_topic(adapter)
        host = _adapter_value(adapter, "target_host") or _adapter_value(adapter, "target_ip")
        port = _adapter_value(adapter, "target_port")
        parts = [part for part in (topic, f"{host}:{port}" if host and port else "", f"port {port}" if port and not (host and port) else "") if part]
        return " · ".join(parts) if parts else (topic or host or port)
    topic = _udp_source_topic(adapter)
    listen_port = _adapter_value(adapter, "listen_port")
    sender = " @ ".join([part for part in (_adapter_value(adapter, "source_host"), _adapter_value(adapter, "source_port")) if part])
    parts = [part for part in (topic, f"listen {listen_port}" if listen_port else "", sender) if part]
    return " · ".join(parts) if parts else (topic or listen_port or sender)


def _normalize_match_value(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_knx_group_address_value(value: Any) -> str:
    text = str(value or "").strip().replace(" ", "")
    if not text:
        return ""
    if "/" not in text:
        return text.lower()
    parts = [part for part in text.split("/") if part != ""]
    if len(parts) != 3:
        return text.lower()
    try:
        return "/".join(str(int(part)) for part in parts)
    except Exception:
        return text.lower()


def _normalize_uuid_value(value: Any) -> str:
    return _normalize_match_value(value).replace("-", "")


def _knx_gateway_enabled() -> bool:
    config_path = CONFIG_DIR / "knx_config.json"
    try:
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                cfg = json.load(handle) or {}
            return bool(cfg.get("enabled", False))
    except Exception:
        LOGGER.exception("KNX-Gateway-Check ueber knx_config.json fehlgeschlagen")
    try:
        try:
            from app.services.config import load_knx_config as _load_knx_config
        except ModuleNotFoundError:
            from services.config import load_knx_config as _load_knx_config
        enabled = bool(_load_knx_config().get("enabled", False))
    except Exception:
        enabled = False
    return enabled


def _normalize_knx_dpt(value: Any) -> str:
    dpt = _normalize_match_value(value)
    if not dpt:
        return ""
    dpt = dpt.replace("dpt", "").replace("dpt_", "").replace("_", ".")
    if dpt.isdigit() and len(dpt) == 4:
        return f"{dpt[:2]}.{dpt[2:]}"
    if dpt.isdigit() and len(dpt) == 5:
        return f"{dpt[:2]}.{dpt[2:]}"
    if "." in dpt:
        parts = [part for part in dpt.split(".") if part]
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
    return dpt


def _default_knx_dpt_for_object(item: Any) -> str:
    datatype = _normalize_match_value(getattr(item, "datatype", "") or "")
    unit = _normalize_match_value(getattr(item, "unit", "") or "")
    combined = f"{datatype} {unit}".strip()
    if any(token in combined for token in ("bool", "switch", "on/off", "an/aus")):
        return "1.001"
    if "%" in combined or "percent" in combined:
        return "5.001"
    if "°c" in combined or "temp" in combined or "temperature" in combined:
        return "9.001"
    if "w" == unit or "power" in combined or "leistung" in combined:
        return "14.056"
    if "a" == unit or "current" in combined or "strom" in combined:
        return "14.019"
    if "v" == unit or "voltage" in combined or "spannung" in combined:
        return "14.027"
    if "text" in combined or "string" in combined:
        return "16.001"
    return "9.001"


def _knx_dpt_label(dpt: Any) -> str:
    dpt_value = _normalize_knx_dpt(dpt)
    return KNX_DPT_LABELS.get(dpt_value, "")


def _endpoint_address(protocol: str, adapter: Any) -> str:
    if protocol == "mqtt":
        topic = _adapter_value(adapter, "topic")
        json_key = _adapter_value(adapter, "json_key")
        if topic and json_key:
            return f"{topic} / {json_key}"
        return topic
    if protocol == "loxone":
        return _loxone_display_label(adapter, "source")
    if protocol == "knx":
        group_address = _adapter_value(adapter, "group_address")
        dpt = _normalize_knx_dpt(_adapter_value(adapter, "dpt"))
        if not group_address:
            return ""
        label = _knx_dpt_label(dpt)
        if dpt and label:
            return f"{group_address} · DPT {dpt} {label}"
        if dpt:
            return f"{group_address} · DPT {dpt}"
        return group_address
    if protocol == "udp":
        source_label = _udp_display_label(adapter, "source")
        target_label = _udp_display_label(adapter, "target")
        if _udp_source_route_active(adapter) and not _udp_target_route_active(adapter):
            return source_label
        if _udp_target_route_active(adapter) and not _udp_source_route_active(adapter):
            return target_label
        return source_label or target_label
    if protocol == "influx":
        measurement = _adapter_value(adapter, "measurement")
        field = _adapter_value(adapter, "field") or "value"
        topic = _adapter_value(adapter, "topic")
        parts = [part for part in (measurement, field, topic) if part]
        return " / ".join(parts)
    return ""


def _endpoint_missing_fields(protocol: str, adapter: Any) -> list[str]:
    required = {
        "mqtt": (("topic", "Topic"),),
        "loxone": (),
        "knx": (("group_address", "Gruppenadresse"), ("dpt", "DPT")),
        "udp": (("target_ip", "Ziel-IP"), ("target_port", "Ziel-Port")),
        "influx": (("measurement", "Measurement"),),
    }.get(protocol, ())
    if protocol == "loxone":
        return [] if (_loxone_source_uuid(adapter) or _loxone_source_io(adapter) or _loxone_source_name(adapter) or _loxone_target_uuid_explicit(adapter)) else ["UUID oder IO-Adresse"]
    if protocol == "udp":
        missing = []
        if _udp_source_enabled(adapter):
            if not _adapter_value(adapter, "listen_port"):
                missing.append("Listen-Port")
        if _udp_target_enabled(adapter):
            if not (_adapter_value(adapter, "target_host") or _adapter_value(adapter, "target_ip")):
                missing.append("Ziel-IP")
            if not _adapter_value(adapter, "target_port"):
                missing.append("Ziel-Port")
        if missing:
            return missing
        if _udp_source_enabled(adapter) or _udp_target_enabled(adapter):
            return []
        return ["UDP-Quelle oder UDP-Ziel"]
    return [label for field, label in required if not _adapter_value(adapter, field)]


def _is_enabled_adapter(adapter: Any) -> bool:
    return bool(getattr(adapter, "enabled", False))


def _is_complete_endpoint(protocol: str, adapter: Any) -> bool:
    if protocol == "knx" and not _knx_gateway_enabled():
        return False
    if protocol == "loxone":
        has_endpoint = bool(_loxone_source_uuid(adapter) or _loxone_source_io(adapter) or _loxone_source_name(adapter) or _loxone_target_uuid_explicit(adapter))
        has_source = _loxone_source_route_active(adapter)
        has_target = _loxone_target_route_active(adapter)
        return bool(has_endpoint and (has_source or has_target))
    if protocol == "udp":
        return _is_enabled_adapter(adapter) and (bool(_udp_source_route_active(adapter)) or bool(_udp_target_route_active(adapter)))
    return _is_enabled_adapter(adapter) and not _endpoint_missing_fields(protocol, adapter)


def _adapter_config_errors(protocol: str, adapter: Any) -> list[str]:
    errors = []
    if protocol not in ADAPTER_TYPES:
        errors.append(f"Unbekanntes Protokoll: {protocol}")
    direction = str(getattr(adapter, "direction", "both") or "both").strip().lower()
    if direction not in {"in", "out", "both"}:
        errors.append(f"{protocol.upper()}: ungueltige Richtung {direction}")
    datatype = str(getattr(adapter, "datatype", "auto") or "auto").strip()
    if not datatype:
        errors.append(f"{protocol.upper()}: Datentyp fehlt")
    if protocol == "knx":
        if not _adapter_value(adapter, "group_address"):
            errors.append("KNX: Gruppenadresse fehlt")
        if not _normalize_knx_dpt(_adapter_value(adapter, "dpt")):
            errors.append("KNX: DPT fehlt")
    return errors


def _can_source(adapter: Any) -> bool:
    protocol = str(getattr(adapter, "protocol", "") or "").strip().lower()
    direction = str(getattr(adapter, "direction", "both") or "both").strip().lower()
    if protocol == "udp":
        return bool(_udp_source_route_active(adapter) or direction in {"in", "both"} and _udp_source_enabled(adapter))
    return protocol != "influx" and direction in {"in", "both"}


def _can_target(adapter: Any) -> bool:
    protocol = str(getattr(adapter, "protocol", "") or "").strip().lower()
    if protocol == "knx" and not _knx_gateway_enabled():
        return False
    if protocol == "loxone":
        return _loxone_target_route_active(adapter)
    if protocol == "udp":
        return bool(_udp_target_route_active(adapter) or (str(getattr(adapter, "direction", "both") or "both").strip().lower() in {"out", "both"} and _udp_target_enabled(adapter)))
    direction = str(getattr(adapter, "direction", "both") or "both").strip().lower()
    return direction in {"out", "both"}


def _primary_route_source(item: GatewayObject) -> tuple[str | None, Any | None, dict[str, Any]]:
    adapters = {
        protocol: adapter
        for protocol, adapter in _adapter_map(item).items()
        if _is_complete_endpoint(protocol, adapter)
    }
    for protocol in ROUTE_SOURCE_PRIORITY:
        adapter = adapters.get(protocol)
        if adapter is not None and _can_source(adapter):
            if protocol == "loxone" and not _loxone_source_enabled(adapter):
                continue
            return protocol, adapter, adapters
    return None, None, adapters


def get_object_route_status(item: GatewayObject) -> str:
    if not item.enabled:
        return "deaktiviert"
    adapters = _adapter_map(item)
    meta = dict(getattr(item, "meta", {}) or {})
    if str(meta.get("source") or meta.get("origin_source") or "").strip().lower() == "openccu":
        for protocol, adapter in adapters.items():
            if not _is_enabled_adapter(adapter) or not _can_target(adapter):
                continue
            if _is_complete_endpoint(protocol, adapter):
                return "aktiv"
    errors = []
    source_protocols = set()
    target_protocols = set()
    for protocol, adapter in adapters.items():
        if not _is_enabled_adapter(adapter):
            continue
        errors.extend(_adapter_config_errors(protocol, adapter))
        if _is_complete_endpoint(protocol, adapter):
            if protocol == "loxone":
                if _loxone_source_enabled(adapter):
                    source_protocols.add(protocol)
            elif _can_source(adapter):
                source_protocols.add(protocol)
            if _can_target(adapter):
                target_protocols.add(protocol)
    if errors:
        return "fehler"
    for source_protocol in source_protocols:
        for target_protocol in target_protocols:
            if source_protocol == target_protocol:
                continue
            if (source_protocol, target_protocol) in SUPPORTED_ROUTE_PAIRS:
                return "aktiv"
    return "nicht konfiguriert"


def _route_source_for_report(item: GatewayObject) -> tuple[str | None, Any | None, dict[str, Any]]:
    configured_source, configured_adapter, configured_adapters = _configured_input_source(item)
    if configured_source is not None and configured_adapter is not None:
        return configured_source, configured_adapter, configured_adapters
    adapters = _adapter_map(item)
    return None, None, adapters


def route_object_value(object_id: str, original_source: str, source_ref: str, value: Any, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    item = get_object(object_id)
    metadata = dict(metadata or {})
    if item is None:
        return {
            "object_id": str(object_id or "").strip(),
            "item": None,
            "original_source": str(original_source or "").strip().lower(),
            "source_ref": str(source_ref or "").strip(),
            "value": value,
            "metadata": metadata,
            "route_report": None,
            "routes": [],
        }
    source = str(original_source or "").strip().lower()
    source_kwargs: dict[str, Any] = {}
    if source == "mqtt":
        source_kwargs["topic"] = metadata.get("topic") or source_ref
        source_kwargs["broker"] = metadata.get("broker") or metadata.get("source_broker") or "Hauptbroker"
        source_kwargs["source_broker"] = source_kwargs["broker"]
        if metadata.get("json_key"):
            source_kwargs["json_key"] = metadata.get("json_key")
    elif source == "loxone":
        source_kwargs["loxone_uuid"] = metadata.get("loxone_uuid", "")
        source_kwargs["loxone_io"] = metadata.get("loxone_io") or source_ref
        source_kwargs["name"] = metadata.get("name") or source_ref
    elif source == "udp":
        source_kwargs["udp_topic"] = metadata.get("udp_topic") or metadata.get("source_topic") or source_ref
        source_kwargs["source_topic"] = metadata.get("source_topic") or metadata.get("udp_topic") or source_ref
        source_kwargs["source_json_path"] = metadata.get("source_json_path") or metadata.get("json_key") or ""
        source_kwargs["udp_source_host"] = metadata.get("udp_source_host") or metadata.get("source_host") or ""
        source_kwargs["udp_source_port"] = metadata.get("udp_source_port") or metadata.get("source_port") or ""
        source_kwargs["udp_listen_port"] = metadata.get("udp_listen_port") or metadata.get("listen_port") or ""
    elif source == "knx":
        source_kwargs["group_address"] = metadata.get("group_address") or source_ref
    else:
        source_kwargs["topic"] = metadata.get("topic") or source_ref
        source_kwargs["udp_topic"] = metadata.get("udp_topic") or source_ref
        source_kwargs["group_address"] = metadata.get("group_address") or source_ref
        source_kwargs["loxone_uuid"] = metadata.get("loxone_uuid", "")
        source_kwargs["loxone_io"] = metadata.get("loxone_io", "")
        source_kwargs["name"] = metadata.get("name", "")
    return {
        "object_id": item.id,
        "item": item,
        "original_source": source,
        "source_ref": str(source_ref or "").strip(),
        "value": value,
        "metadata": metadata,
        "source_kwargs": source_kwargs,
        "route_report": get_object_route_report(item),
        "routes": build_generated_route_entries(item, source),
    }


def build_generated_route_entries(item: GatewayObject, source_protocol: str | None = None) -> list[dict[str, str]]:
    meta = dict(getattr(item, "meta", {}) or {})
    semantic_source = str(meta.get("source") or meta.get("origin_source") or "").strip().lower()
    if semantic_source == "openccu" and str(source_protocol or "").strip().lower() in {"", "openccu"}:
        entries = []
        source_address = str(meta.get("openccu_topic") or "").strip()
        for target, target_adapter in _adapter_map(item).items():
            if not _is_enabled_adapter(target_adapter) or not _can_target(target_adapter):
                continue
            if not _is_complete_endpoint(target, target_adapter):
                continue
            target_address = (
                _loxone_display_label(target_adapter, "target") if target == "loxone"
                else _udp_display_label(target_adapter, "target") if target == "udp"
                else _endpoint_address(target, target_adapter)
            )
            entries.append({
                "source": "OPENCCU",
                "target": target.upper(),
                "source_address": source_address,
                "target_address": target_address,
                "direction": f"OPENCCU -> {target.upper()}",
                "status": "aktiv",
            })
        return entries
    if source_protocol:
        source_protocol = str(source_protocol or "").strip().lower() or None
    source_protocol, source_adapter, adapters = _route_source_for_report(item) if source_protocol is None else (
        source_protocol,
        _adapter_map(item).get(source_protocol),
        _adapter_map(item),
    )
    if source_protocol is None or source_adapter is None:
        return []
    entries = []
    for target, target_adapter in adapters.items():
        # MQTT may legitimately route to MQTT when source and destination use
        # different broker/topic endpoints. Exact self-routes are blocked at runtime.
        if (target == source_protocol and target != "mqtt") or not _can_target(target_adapter):
            continue
        if not _is_complete_endpoint(target, target_adapter):
            continue
        if (source_protocol, target) not in SUPPORTED_ROUTE_PAIRS and not (source_protocol == "mqtt" and target == "mqtt"):
            continue
        source_address = _loxone_display_label(source_adapter, "source") if source_protocol == "loxone" else (_udp_display_label(source_adapter, "source") if source_protocol == "udp" else _endpoint_address(source_protocol, source_adapter))
        target_address = _loxone_display_label(target_adapter, "target") if target == "loxone" else (_udp_display_label(target_adapter, "target") if target == "udp" else _endpoint_address(target, target_adapter))
        entries.append(
            {
                "source": source_protocol.upper(),
                "target": target.upper(),
                "source_address": source_address,
                "target_address": target_address,
                "direction": f"{source_protocol.upper()} -> {target.upper()}",
                "status": "aktiv",
            }
        )
    return entries


def build_return_route_entries(item: GatewayObject, source_protocol: str | None = None) -> list[dict[str, str]]:
    if source_protocol:
        source_protocol = str(source_protocol or "").strip().lower() or None
    source_protocol, source_adapter, adapters = _route_source_for_report(item) if source_protocol is None else (
        source_protocol,
        _adapter_map(item).get(source_protocol),
        _adapter_map(item),
    )
    if source_protocol is None or source_adapter is None or not _can_target(source_adapter):
        return []
    entries = []
    for candidate_protocol in ("mqtt", "loxone", "udp", "knx"):
        if candidate_protocol == source_protocol:
            continue
        candidate_adapter = adapters.get(candidate_protocol)
        if candidate_adapter is None or not _can_source(candidate_adapter):
            continue
        if not _is_complete_endpoint(candidate_protocol, candidate_adapter):
            continue
        if (candidate_protocol, source_protocol) not in SUPPORTED_ROUTE_PAIRS:
            continue
        entries.append(
            {
                "source": candidate_protocol.upper(),
                "target": source_protocol.upper(),
                "source_address": _loxone_display_label(candidate_adapter, "source") if candidate_protocol == "loxone" else (_udp_display_label(candidate_adapter, "source") if candidate_protocol == "udp" else _endpoint_address(candidate_protocol, candidate_adapter)),
                "target_address": _loxone_display_label(source_adapter, "target") if source_protocol == "loxone" else (_udp_display_label(source_adapter, "target") if source_protocol == "udp" else _endpoint_address(source_protocol, source_adapter)),
                "direction": f"{candidate_protocol.upper()} -> {source_protocol.upper()}",
                "status": "konfiguriert",
            }
        )
    return entries


def get_object_route_report(item: GatewayObject) -> dict[str, Any]:
    adapters = _adapter_map(item)
    missing = []
    errors = []
    for protocol in ("mqtt", "loxone", "udp", "knx", "influx"):
        adapter = adapters.get(protocol)
        if protocol == "knx" and not _knx_gateway_enabled():
            missing.append("KNX deaktiviert")
            continue
        if protocol == "loxone":
            target_uuid = _loxone_target_uuid_explicit(adapter) if adapter is not None else ""
            if adapter is not None and _loxone_target_enabled(adapter) and (not target_uuid or not _loxone_gateway_configured()):
                missing.append("LOXONE nicht konfiguriert")
                continue
        if not adapter or not _is_enabled_adapter(adapter):
            missing.append(f"{protocol.upper()} inaktiv")
            continue
        errors.extend(_adapter_config_errors(protocol, adapter))
        fields = _endpoint_missing_fields(protocol, adapter)
        if fields:
            missing.append(f"{protocol.upper()}: " + ", ".join(fields))

    complete_count = sum(
        1 for protocol, adapter in adapters.items()
        if _is_complete_endpoint(protocol, adapter)
    )
    if complete_count >= 2:
        missing = [entry for entry in missing if not entry.endswith("inaktiv")]
    source_protocol, source_adapter, _ = _route_source_for_report(item)
    meta = dict(getattr(item, "meta", {}) or {})
    semantic_source = str(meta.get("source") or meta.get("origin_source") or "").strip().lower()
    report_source = "openccu" if semantic_source == "openccu" else source_protocol
    main_routes = build_generated_route_entries(item, report_source)
    return_routes = build_return_route_entries(item, report_source)
    return {
        "status": get_object_route_status(item),
        "current_source": report_source.upper() if report_source else "",
        "current_source_address": _endpoint_address(source_protocol, source_adapter) if source_protocol and source_adapter else "",
        "main_routes": main_routes,
        "return_routes": return_routes,
        "routes": main_routes,
        "missing_endpoints": missing,
        "errors": errors,
    }


def _route_lookup_key(kind: str, value: Any) -> str:
    value = _normalize_match_value(value)
    if not value:
        return ""
    return f"{kind}:{value}"


def _build_loxone_to_mqtt_route_index() -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for item in list_objects():
        if get_object_route_status(item) != "aktiv":
            continue
        adapters = _adapter_map(item)
        loxone_adapter = adapters.get("loxone")
        mqtt_adapter = adapters.get("mqtt")
        if not loxone_adapter or not mqtt_adapter:
            continue
        if not _is_complete_endpoint("loxone", loxone_adapter) or not _is_complete_endpoint("mqtt", mqtt_adapter):
            continue
        if not _can_source(loxone_adapter) or not _can_target(mqtt_adapter):
            continue
        route = {
            "object_id": item.id,
            "object_name": item.name,
            "mqtt_topic": _adapter_value(mqtt_adapter, "topic"),
            "retain": bool(getattr(mqtt_adapter, "retain", False)),
            "loxone_uuid": _loxone_source_uuid(loxone_adapter),
            "loxone_io": _adapter_value(loxone_adapter, "io_address"),
        }
        for key in (
            _route_lookup_key("uuid", route["loxone_uuid"]),
            _route_lookup_key("io", route["loxone_io"]),
            _route_lookup_key("name", _loxone_source_name(loxone_adapter) or item.name),
            _route_lookup_key("name", item.name),
        ):
            if not key:
                continue
            index.setdefault(key, []).append(route)
    return index


def _get_loxone_to_mqtt_route_index() -> dict[str, list[dict[str, Any]]]:
    global OBJECT_ROUTE_CACHE_MTIME
    with OBJECT_ROUTE_CACHE_LOCK:
        mtime = _objects_file_mtime()
        if OBJECT_ROUTE_CACHE and OBJECT_ROUTE_CACHE_MTIME == mtime:
            return OBJECT_ROUTE_CACHE
        OBJECT_ROUTE_CACHE.clear()
        OBJECT_ROUTE_CACHE.update(_build_loxone_to_mqtt_route_index())
        OBJECT_ROUTE_CACHE_MTIME = _objects_file_mtime()
        return OBJECT_ROUTE_CACHE


def _route_base(item: GatewayObject, source_topic: str) -> dict[str, Any]:
    return {
        "enabled": True,
        "source_topic": source_topic,
        "mapping_alias": item.name,
        "group": "Objektmanager V33",
        "set_name": item.name or item.id,
        "__object_route": True,
        "__object_id": item.id,
    }


def build_routes_from_objects(log_func=None) -> dict[str, list[dict[str, Any]] | dict[str, dict[str, Any]]]:
    global OBJECT_ROUTE_EXPORT_CACHE_MTIME
    with OBJECT_ROUTE_EXPORT_CACHE_LOCK:
        mtime = _objects_file_mtime()
        if log_func is None and OBJECT_ROUTE_EXPORT_CACHE and OBJECT_ROUTE_EXPORT_CACHE_MTIME == mtime:
            return _clone_route_export_result(OBJECT_ROUTE_EXPORT_CACHE)

    objects = list_objects()
    routes: dict[str, Any] = {
        "mqtt2lox": [],
        "mqtt2udp": [],
        "mqtt2knx": [],
        "loxone2mqtt": [],
        "loxone2knx": [],
        "knx2mqtt": [],
        "udp2mqtt": [],
        "udp2knx": [],
        "knx2lox": [],
        "topic_config": {},
    }
    active = 0
    skipped = 0
    errors: list[str] = []

    for item in objects:
        name = item.name or item.id
        try:
            if get_object_route_status(item) != "aktiv":
                skipped += 1
                continue

            adapters = _adapter_map(item)
            for entry in build_generated_route_entries(item):
                source = entry["source"].lower()
                target = entry["target"].lower()
                source_adapter = adapters[source]
                target_adapter = adapters[target]
                base = _route_base(item, entry["source_address"])
                if source == "mqtt" and target == "loxone":
                    routes["mqtt2lox"].append({"enabled": True, "loxone_uuid": _loxone_target_uuid(target_adapter) or _loxone_source_uuid(target_adapter), "loxone_io": _loxone_target_uuid(target_adapter) or _adapter_value(target_adapter, "io_address"), "group": "Objektmanager V33", "set_name": item.name or item.id, "mapping_alias": item.name, "__object_route": True, "__object_id": item.id})
                    active += 1
                elif source == "loxone" and target == "mqtt":
                    routes["loxone2mqtt"] = routes.get("loxone2mqtt", [])
                    routes["loxone2mqtt"].append({"enabled": True, "loxone_uuid": _loxone_source_uuid(source_adapter), "loxone_io": _adapter_value(source_adapter, "io_address"), "mqtt_topic": _adapter_value(target_adapter, "topic"), "retain": bool(getattr(target_adapter, "retain", False)), "group": "Objektmanager V33", "set_name": item.name or item.id, "mapping_alias": item.name, "__object_route": True, "__object_id": item.id})
                    active += 1
                elif source == "loxone" and target == "knx":
                    routes["loxone2knx"].append({"enabled": True, "loxone_uuid": _loxone_source_uuid(source_adapter), "loxone_io": _adapter_value(source_adapter, "io_address"), "group_address": _adapter_value(target_adapter, "group_address"), "dpt": _adapter_value(target_adapter, "dpt"), "group": "Objektmanager V33", "set_name": item.name or item.id, "mapping_alias": item.name, "__object_route": True, "__object_id": item.id})
                    active += 1
                elif source == "mqtt" and target == "knx":
                    route = dict(base)
                    route.update({"group_address": _adapter_value(target_adapter, "group_address"), "dpt": _adapter_value(target_adapter, "dpt"), "payload_mode": "raw", "json_key": "", "invert": False, "test_value": "1"})
                    routes["mqtt2knx"].append(route)
                    active += 1
                elif source == "mqtt" and target == "udp":
                    continue
                elif source == "mqtt" and target == "influx":
                    continue
                elif source == "knx" and target == "mqtt":
                    routes["knx2mqtt"].append({"enabled": True, "group_address": _adapter_value(source_adapter, "group_address"), "mqtt_topic": _adapter_value(target_adapter, "topic"), "dpt": _adapter_value(source_adapter, "dpt"), "retain": bool(getattr(target_adapter, "retain", True)), "invert": False, "group": "Objektmanager V33", "set_name": item.name or item.id, "mapping_alias": item.name, "__object_route": True, "__object_id": item.id})
                    active += 1
                elif source == "knx" and target == "loxone":
                    routes["knx2lox"].append({"enabled": True, "group_address": _adapter_value(source_adapter, "group_address"), "loxone_io": _loxone_target_uuid(target_adapter) or _adapter_value(target_adapter, "io_address"), "dpt": _adapter_value(source_adapter, "dpt"), "invert": False, "group": "Objektmanager V33", "set_name": item.name or item.id, "mapping_alias": item.name, "__object_route": True, "__object_id": item.id})
                    active += 1
                elif source == "knx" and target == "influx":
                    continue
                elif source == "udp" and target == "mqtt":
                    continue
                elif source == "udp" and target == "knx":
                    routes["udp2knx"].append({"enabled": True, "source_topic": _adapter_value(source_adapter, "format"), "group_address": _adapter_value(target_adapter, "group_address"), "dpt": _adapter_value(target_adapter, "dpt"), "invert": False, "test_value": "1", "group": "Objektmanager V33", "set_name": item.name or item.id, "mapping_alias": item.name, "__object_route": True, "__object_id": item.id})
                    active += 1
                elif source == "udp" and target == "influx":
                    continue
                elif source == "loxone" and target == "influx":
                    continue
        except Exception as exc:
            skipped += 1
            errors.append(f"{name}/{item.id}: {exc}")

    if log_func:
        log_func(f"Objektrouten: gesamt={len(objects)}, aktiv={active}, übersprungen={skipped}")
        for message in errors:
            log_func(f"Objektroute Fehler {message}")

    with OBJECT_ROUTE_EXPORT_CACHE_LOCK:
        OBJECT_ROUTE_EXPORT_CACHE.clear()
        OBJECT_ROUTE_EXPORT_CACHE.update(_clone_route_export_result(routes))
        OBJECT_ROUTE_EXPORT_CACHE_MTIME = _objects_file_mtime()

    return routes


def find_loxone_to_mqtt_route(loxone_uuid: str = "", loxone_io: str = "", state_name: str = "") -> dict[str, Any] | None:
    """Return the active object route that permits publishing a Loxone state to MQTT."""
    route_index = _get_loxone_to_mqtt_route_index()
    candidates = [
        _route_lookup_key("uuid", loxone_uuid),
        _route_lookup_key("io", loxone_io),
        _route_lookup_key("name", state_name),
    ]
    seen_keys = set()
    for key in candidates:
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        routes = route_index.get(key) or []
        if routes:
            return dict(routes[0])
    return None

