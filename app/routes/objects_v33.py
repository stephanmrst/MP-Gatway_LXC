"""Object Manager V33 routes."""

import inspect
import re
import threading

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

try:
    from app.models.object_model import GatewayObject
    from app.services.object_adapter_engine import (
        ADAPTER_TYPES,
        adapter_from_form,
        adapter_template_name,
        deserialize_adapter,
    )
    from app.services import object_service
    from app.services.object_routing_preview import build_object_routing_preview
except ModuleNotFoundError:
    from models.object_model import GatewayObject
    from services.object_adapter_engine import (
        ADAPTER_TYPES,
        adapter_from_form,
        adapter_template_name,
        deserialize_adapter,
    )
    from services import object_service
    from services.object_routing_preview import build_object_routing_preview


bp = Blueprint("objects_v33", __name__, template_folder="../../templates")
_EXPLORER_CREATE_LOCK = threading.Lock()
SOURCE_FILTER_TYPES = {"mqtt", "loxone", "udp", "knx", "openccu"}


def _wants_ajax_response() -> bool:
    return request.headers.get("X-Requested-With", "").lower() == "xmlhttprequest"


def _slugify(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("-_")
    return text or "object"


def _looks_like_uuid(value: str) -> bool:
    text = str(value or "").strip()
    return bool(re.fullmatch(r"(?:[0-9a-fA-F]{32}|[0-9a-fA-F-]{36})", text))


def _request_first(*names: str) -> str:
    for name in names:
        value = _clean_prefill(request.args.get(name, ""))
        if value:
            return value
    return ""


def _request_bool(*names: str, default: bool = False) -> bool:
    for name in names:
        if name in request.form:
            value = request.form.get(name)
            return str(value or "").strip().lower() not in {"", "0", "false", "off", "no", "nein"}
        if name in request.args:
            value = request.args.get(name, "")
            if value != "":
                return str(value or "").strip().lower() not in {"", "0", "false", "off", "no", "nein"}
    return bool(default)


def _datatype_from_request() -> str:
    datatype = _request_first("datatype", "value_type", "type")
    if datatype and datatype.lower() != "auto":
        return datatype
    value = _request_first("value", "last_value")
    if not value:
        return datatype or "auto"
    lowered = value.lower()
    if lowered in {"true", "false", "on", "off", "yes", "no", "ja", "nein"}:
        return "bool"
    try:
        float(value.replace(",", "."))
        return "number"
    except ValueError:
        return "text"


def _new_object_key(name: str) -> str:
    base = _slugify(name)
    existing = {item.key for item in object_service.list_objects()}
    if base not in existing:
        return base
    index = 2
    while f"{base}_{index}" in existing:
        index += 1
    return f"{base}_{index}"


def _adapter_protocols(object_def):
    protocols = []
    for adapter in object_def.adapters:
        if isinstance(adapter, dict):
            adapter = deserialize_adapter(adapter)
        protocol = str(getattr(adapter, "protocol", "") or "").strip().lower()
        if not protocol:
            continue
        if protocol == "loxone":
            has_source = bool(
                str(getattr(adapter, "source_uuid", "") or "").strip()
                or str(getattr(adapter, "source_io", "") or getattr(adapter, "io_address", "") or "").strip()
                or str(getattr(adapter, "source_name", "") or getattr(adapter, "visu_name", "") or "").strip()
            )
            has_target = bool(
                bool(getattr(adapter, "target_enabled", False))
                and str(getattr(adapter, "target_uuid", "") or "").strip()
            )
            if has_source or has_target:
                protocols.append(protocol)
            continue
        if getattr(adapter, "enabled", False):
            protocols.append(protocol)
    return sorted(set(protocol for protocol in protocols if protocol))


def _route_status(object_def):
    return object_service.get_object_route_status(object_def)


def _current_source_label(object_def):
    try:
        meta = dict(getattr(object_def, "meta", {}) or {})
        if str(meta.get("source") or meta.get("origin_source") or "").strip().lower() == "openccu":
            return "OpenCCU"
        live = object_service.get_object_live_status(getattr(object_def, "id", "")) or {}
        live_source = str(
            live.get("source_protocol")
            or live.get("last_source")
            or live.get("current_source")
            or live.get("original_source")
            or ""
        ).strip().lower()
        if not live_source or live_source == "unbekannt":
            report = object_service.get_object_route_report(object_def) or {}
            live_source = str(report.get("current_source") or "").strip().lower()
        if not live_source:
            live_source = str(getattr(object_def, "source_protocol", "") or getattr(object_def, "input_protocol", "") or "").strip().lower()
    except Exception:
        return "unbekannt"
    if not live_source or live_source == "unbekannt":
        return "unbekannt"
    return {
        "loxone": "Loxone",
        "mqtt": "MQTT",
        "udp": "UDP",
        "knx": "KNX",
        "influx": "Influx",
    }.get(live_source, "unbekannt")


def _current_source_address(object_def):
    try:
        report = object_service.get_object_route_report(object_def) or {}
        live_source = str(report.get("current_source") or "").strip().lower()
        live_address = str(report.get("current_source_address") or "").strip()
        if live_address:
            return live_address
    except Exception:
        return ""
    if not live_source or live_source == "unbekannt":
        return ""
    return ""


def _object_filter_source(object_def) -> str:
    try:
        meta = dict(getattr(object_def, "meta", {}) or {})
        if str(meta.get("source") or meta.get("origin_source") or "").strip().lower() == "openccu":
            return "openccu"
        report = object_service.get_object_route_report(object_def) or {}
        source = str(report.get("current_source") or "").strip().lower()
        if source in ADAPTER_TYPES and source != "influx":
            return source
    except Exception:
        pass
    adapters = _adapter_map(object_def)
    for protocol in ("mqtt", "loxone", "udp", "knx"):
        adapter = adapters.get(protocol)
        if adapter is None:
            continue
        direction = str(getattr(adapter, "direction", "both") or "both").strip().lower()
        if direction not in {"in", "both"}:
            continue
        if protocol == "mqtt" and str(getattr(adapter, "topic", "") or "").strip():
            return protocol
        if protocol == "knx" and str(getattr(adapter, "group_address", "") or "").strip():
            return protocol
        if protocol == "udp" and (
            str(getattr(adapter, "source_topic", "") or "").strip()
            or str(getattr(adapter, "source_json_path", "") or "").strip()
            or str(getattr(adapter, "listen_port", "") or "").strip()
        ):
            return protocol
        if protocol == "loxone" and (
            str(getattr(adapter, "source_uuid", "") or getattr(adapter, "uuid", "") or "").strip()
            or str(getattr(adapter, "source_io", "") or getattr(adapter, "io_address", "") or "").strip()
            or str(getattr(adapter, "source_name", "") or getattr(adapter, "visu_name", "") or "").strip()
        ):
            return protocol
    return "unbekannt"


def _selected_source_type(object_def) -> str:
    try:
        report = object_service.get_object_route_report(object_def) or {}
        live_source = str(report.get("current_source") or "").strip().lower()
        if not live_source:
            live = object_service.get_object_live_status(getattr(object_def, "id", "")) or {}
            live_source = str(
                live.get("display_source")
                or live.get("input_protocol")
                or live.get("source_protocol")
                or live.get("last_source")
                or live.get("current_source")
                or live.get("source")
                or live.get("original_source")
                or ""
            ).strip().lower()
        if live_source in ADAPTER_TYPES:
            return live_source
        source = str(report.get("current_source") or "").strip().lower()
        if source in ADAPTER_TYPES:
            return source
    except Exception:
        pass
    return "unbekannt"


def _blank_object_draft(source_type: str = "mqtt") -> GatewayObject:
    adapters = {}
    for protocol in ("mqtt", "udp", "knx", "loxone", "influx"):
        adapters[protocol] = ADAPTER_TYPES[protocol](enabled=False)
    draft = GatewayObject(
        id="",
        name="",
        datatype="auto",
        unit="",
        enabled=True,
        meta={"adapters": adapters},
    )
    setattr(draft, "_selected_source_type", str(source_type or "mqtt").strip().lower() or "mqtt")
    return draft


def _reload_object_routes():
    core = current_app.extensions.get("app_core")
    if core and hasattr(core, "reload_object_routes_async"):
        core.reload_object_routes_async("objects_v33")
    elif core and hasattr(core, "reload_object_routes"):
        core.reload_object_routes("objects_v33")


def _safe_reload_object_routes(context: str = "") -> bool:
    try:
        _reload_object_routes()
        return True
    except Exception as exc:
        current_app.logger.exception("Objektrouten konnten nicht neu geladen werden: %s", exc)
        core = current_app.extensions.get("app_core")
        if core and hasattr(core, "add_log_entry"):
            try:
                core.add_log_entry(f"Object Routes Reload Fehler context={context or ''} error={exc}")
            except Exception:
                pass
        return False


def _log_explorer_import(source: str, uuid: str, name: str, object_id: str, action: str, error: str = ""):
    message = (
        "Object Explorer Import "
        f"source={source or ''} uuid={uuid or ''} name={name or ''} "
        f"object_id={object_id or ''} action={action or ''}"
    )
    if error:
        message += f" error={error}"
    try:
        current_app.logger.info(message)
    except Exception:
        pass
    core = current_app.extensions.get("app_core")
    if core and hasattr(core, "add_log_entry"):
        try:
            core.add_log_entry(message)
        except Exception:
            pass


def _log_explorer_debug(stage: str, **data):
    safe_data = {}
    for key, value in data.items():
        try:
            safe_data[key] = value if isinstance(value, (str, int, float, bool, type(None), dict, list, tuple)) else str(value)
        except Exception:
            safe_data[key] = "<unserializable>"
    message = f"Object Explorer Debug stage={stage} data={safe_data}"
    try:
        current_app.logger.info(message)
    except Exception:
        pass
    core = current_app.extensions.get("app_core")
    if core and hasattr(core, "add_log_entry"):
        try:
            core.add_log_entry(message)
        except Exception:
            pass


def _log_object_delete(object_id: str, found: bool, deleted: bool, redirect_target: str, error: str = ""):
    message = (
        "Object Delete "
        f"object_id={object_id or ''} found={str(bool(found)).lower()} "
        f"deleted={str(bool(deleted)).lower()} redirect={redirect_target or ''}"
    )
    if error:
        message += f" error={error}"
    try:
        current_app.logger.info(message)
    except Exception:
        pass
    core = current_app.extensions.get("app_core")
    if core and hasattr(core, "add_log_entry"):
        try:
            core.add_log_entry(message)
        except Exception:
            pass


def _filtered_objects(query: str, active_filter: str = "all"):
    objects = object_service.list_objects()
    needle = str(query or "").strip().lower()
    active_filter = str(active_filter or "all").strip().lower()
    filtered = [
        item
        for item in objects
        if not needle
        or needle in " ".join(
            [item.id, item.uuid, item.key, item.name, item.category, item.type, item.unit, item.room]
        ).lower()
    ]
    if active_filter in SOURCE_FILTER_TYPES:
        return [item for item in filtered if _object_filter_source(item) == active_filter]
    return filtered


def _adapter_map(object_def):
    adapters = {}
    for adapter in object_def.adapters:
        if isinstance(adapter, dict):
            adapter = deserialize_adapter(adapter)
        protocol = str(getattr(adapter, "protocol", "") or "").strip().lower()
        if protocol:
            adapters[protocol] = adapter
    return adapters


def _loxone_target_options():
    core = current_app.extensions.get("app_core")
    if core is None:
        return []
    try:
        config = core.load_config()
        mapping = core.load_mapping(config) or {}
    except Exception as exc:
        current_app.logger.exception("Loxone Zieloptionen konnten nicht geladen werden: %s", exc)
        return []

    rooms = {}
    raw_rooms = mapping.get("rooms", {}) if isinstance(mapping, dict) else {}
    if isinstance(raw_rooms, dict):
        for room_uuid, room in raw_rooms.items():
            if isinstance(room, dict):
                rooms[str(room_uuid)] = str(room.get("name", "") or "").strip()

    options_by_uuid = {}

    def walk_controls(controls):
        if not isinstance(controls, dict):
            return
        for control_uuid, control in controls.items():
            if not isinstance(control, dict):
                continue
            control_name = str(control.get("name", "") or control_uuid).strip()
            control_type = str(control.get("type", "") or control.get("cat", "") or "").strip()
            room_id = str(control.get("room", "") or control.get("roomUuid", "") or "").strip()
            room_name = rooms.get(room_id, room_id)
            details = control.get("details", {}) if isinstance(control.get("details"), dict) else {}
            unit = str(details.get("unit", "") or control.get("unit", "") or "").strip()
            states = control.get("states", {}) if isinstance(control.get("states"), dict) else {}
            if states:
                for state_name, state_uuid in states.items():
                    uuid_value = str(state_uuid or "").strip()
                    if not uuid_value:
                        continue
                    options_by_uuid.setdefault(
                        uuid_value,
                        {
                            "uuid": uuid_value,
                            "name": f"{control_name}/{state_name}" if state_name else control_name,
                            "room": room_name,
                            "category": control_type,
                            "type": control_type,
                            "control_uuid": str(control_uuid),
                            "control_name": control_name,
                            "state_name": str(state_name),
                            "unit": unit,
                        },
                    )
            else:
                uuid_value = str(control_uuid or "").strip()
                if uuid_value:
                    options_by_uuid.setdefault(
                        uuid_value,
                        {
                            "uuid": uuid_value,
                            "name": control_name,
                            "room": room_name,
                            "category": control_type,
                            "type": control_type,
                            "control_uuid": uuid_value,
                            "control_name": control_name,
                            "state_name": "",
                            "unit": unit,
                        },
                    )
            walk_controls(control.get("subControls", {}))

    walk_controls(mapping.get("controls", {}) if isinstance(mapping, dict) else {})
    return sorted(
        options_by_uuid.values(),
        key=lambda item: (
            str(item.get("name", "")).casefold(),
            str(item.get("room", "")).casefold(),
            str(item.get("category", "")).casefold(),
        ),
    )


def _normalize_external_uuid(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "")


def _find_object_by_loxone_uuid(loxone_uuid: str):
    return _find_object_by_loxone_endpoint(loxone_uuid=loxone_uuid)


def _find_object_by_loxone_endpoint(loxone_uuid: str = "", io_address: str = ""):
    """Find an existing object by the current persisted Loxone adapter endpoint.

    Wichtig: Nur config/objects.json ist Quelle der Wahrheit. Es wird kein
    Runtime-/Live-/Legacy-Cache verwendet. UUID und IO-Adresse werden getrennt
    verglichen, damit ein geloeschter Datenpunkt sofort wieder angelegt werden
    kann und ein bestehender Datenpunkt sauber geoeffnet wird.
    """
    uuid_needle = _normalize_external_uuid(loxone_uuid)
    io_needle = str(io_address or "").strip().lower()
    if not uuid_needle and not io_needle:
        return None
    for item in object_service.list_objects():
        adapter = _adapter_map(item).get("loxone")
        if adapter is None:
            continue
        adapter_uuid = _normalize_external_uuid(getattr(adapter, "uuid", ""))
        adapter_io = str(
            getattr(adapter, "source_io", "")
            or getattr(adapter, "io_address", "")
            or ""
        ).strip().lower()
        if uuid_needle and adapter_uuid and adapter_uuid == uuid_needle:
            return item
        if io_needle and adapter_io and adapter_io == io_needle:
            return item
    return None


def _ensure_known_adapters(object_def):
    adapters = _adapter_map(object_def)
    result = []
    for protocol in ("mqtt", "udp", "knx", "loxone", "influx"):
        adapter = adapters.get(protocol)
        if adapter is None:
            adapter = ADAPTER_TYPES[protocol](enabled=False)
        if protocol == "knx" and not str(getattr(adapter, "dpt", "") or "").strip():
            adapter.dpt = object_service._default_knx_dpt_for_object(object_def)
        if protocol == "influx":
            if not str(getattr(adapter, "measurement", "") or "").strip():
                adapter.measurement = object_service._default_influx_measurement(getattr(object_def, "name", "") or "")
            if not str(getattr(adapter, "field", "") or "").strip():
                adapter.field = "value"
            if not str(getattr(adapter, "topic", "") or "").strip():
                adapter.topic = object_service._default_influx_topic(getattr(object_def, "name", "") or "")
        result.append(adapter)
    return result


def _adapter_for_core_fields(protocol, address, datatype="auto", enabled=True, direction="both", json_key=""):
    adapter_cls = ADAPTER_TYPES[protocol]
    kwargs = {"enabled": enabled, "direction": direction, "datatype": datatype}
    if protocol == "mqtt":
        kwargs["topic"] = address
        kwargs["json_key"] = json_key
    elif protocol == "knx":
        kwargs["group_address"] = address
    elif protocol == "loxone":
        kwargs["uuid"] = address
        kwargs["io_address"] = address
    elif protocol == "udp":
        kwargs["format"] = address
        kwargs["udp_topic"] = address
    elif protocol == "influx":
        kwargs["measurement"] = address
        kwargs["field"] = "value"
        kwargs["topic"] = address
    return adapter_cls(**kwargs)


def _object_from_prefill():
    explorer = _clean_prefill(request.args.get("explorer", "")).lower()
    source_type = _clean_prefill(request.args.get("source_type") or request.args.get("source") or explorer or "mqtt").lower()
    source_address = _request_first("source_address", "source_topic", "topic", "group_address", "knx_ga", "loxone_io", "io_address", "name", "value")
    json_key = _request_first("mqtt_json_key", "json_key")
    name = request.args.get("name", "").strip()
    if not name:
        try:
            from app.models.object_model import object_name_from_address
        except ModuleNotFoundError:
            from models.object_model import object_name_from_address
        name = object_name_from_address(source_address)

    payload = {
        "id": "",
        "name": name,
        "datatype": _datatype_from_request(),
        "category": request.args.get("category", ""),
        "room": request.args.get("room", ""),
        "unit": request.args.get("unit", ""),
        "notes": request.args.get("description", request.args.get("notes", "")),
        "enabled": True,
    }

    # Wichtig: Explorer-Importe dürfen niemals technische Daten in Allgemein legen.
    # Loxone-Explorer befüllt ausschließlich den Loxone-Endpunkt, MQTT-Explorer ausschließlich MQTT.
    if explorer == "loxone" or source_type == "loxone":
        adapter = _loxone_adapter_from_request(_datatype_from_request())
        if adapter.uuid or adapter.io_address:
            payload["loxone"] = adapter.serialize()
    elif explorer in {"mqtt", "openccu"} or source_type in {"mqtt", "openccu"}:
        topic = _request_first("topic", "source_address", "source_topic")
        if topic:
            if explorer == "openccu" or source_type == "openccu":
                payload["source"] = "openccu"
                payload["origin_source"] = "openccu"
                payload["openccu_topic"] = topic
                payload["openccu_device"] = _clean_prefill(request.args.get("openccu_device", ""))
                payload["openccu_channel"] = _clean_prefill(request.args.get("openccu_channel", ""))
                payload["openccu_datapoint"] = _clean_prefill(request.args.get("openccu_datapoint", ""))
                if not payload["category"]:
                    payload["category"] = "OpenCCU"
            else:
                payload["mqtt"] = _adapter_for_core_fields("mqtt", topic, _datatype_from_request(), True, "both", json_key=json_key).serialize()
    elif explorer == "udp" or source_type == "udp":
        adapter = _udp_adapter_from_request(datatype)
        if str(getattr(adapter, "udp_topic", "") or "").strip() or str(getattr(adapter, "listen_port", "") or "").strip() or str(getattr(adapter, "source_host", "") or "").strip():
            payload["udp"] = adapter.serialize()
            if not payload["category"]:
                payload["category"] = "UDP"
            if not payload["unit"]:
                payload["unit"] = _clean_prefill(request.args.get("unit", ""))
    elif explorer == "knx" or source_type == "knx":
        adapter = _knx_adapter_from_request(_datatype_from_request())
        if adapter.group_address:
            payload["knx"] = adapter.serialize()
            if not payload["category"]:
                payload["category"] = "KNX"
    elif source_type in ADAPTER_TYPES and source_address:
        payload[source_type] = _adapter_for_core_fields(source_type, source_address, _datatype_from_request(), True, "both").serialize()
    return payload


def _clean_prefill(value: str) -> str:
    return str(value or "").strip()


def _loxone_adapter_from_request(datatype: str):
    source_uuid = _request_first("source_uuid", "loxone_uuid", "state_uuid", "uuid", "control_uuid")
    source_io = _request_first("source_io", "loxone_io", "io_address", "source_address", "path", "topic", "name")
    source_name = _request_first("source_name", "visu_name", "display_name", "label")
    source_room = _request_first("source_room", "room")
    source_category = _request_first("source_category", "control_type", "cat", "category", "type")
    target_uuid = _request_first("target_uuid")
    return ADAPTER_TYPES["loxone"](
        enabled=True,
        direction="both",
        datatype=datatype or "auto",
        uuid=source_uuid,
        io_address=source_io,
        control_type=source_category,
        visu_name=source_name,
        room=source_room,
        unit=_request_first("unit"),
        source_uuid=source_uuid,
        source_io=source_io,
        source_name=source_name,
        source_room=source_room,
        source_category=source_category,
        source_enabled=_request_bool("source_enabled", default=bool(source_uuid or source_io or source_name)),
        target_uuid=target_uuid,
        target_name=_request_first("target_name"),
        target_room=_request_first("target_room"),
        target_category=_request_first("target_category"),
        target_type=_request_first("target_type"),
        target_enabled=_request_bool("target_enabled", "active", default=bool(target_uuid)),
    )


def _udp_adapter_from_request(datatype: str):
    source_host = _request_first("udp_source_host", "source_host", "udp_host", "sender_host")
    source_port = _request_first("udp_source_port", "source_port", "udp_sender_port", "sender_port")
    listen_port = _request_first("udp_listen_port", "listen_port", "udp_port", "port")
    source_topic = _request_first("source_topic", "udp_source_topic", "topic", "udp_path", "path", "name")
    source_json_path = _request_first("source_json_path", "udp_source_json_path", "json_key")
    source_payload_mode = _request_first("source_payload_mode", "udp_source_payload_mode") or "value"
    source_enabled = _request_bool("source_enabled", default=False)
    target_enabled = _request_bool("target_enabled", default=False)
    target_host = _request_first("target_host", "udp_target_host", "target_ip", "udp_target_ip")
    target_port = _request_first("target_port", "udp_target_port")
    target_topic = _request_first("udp_topic", "target_topic", "topic", "udp_path", "path", "name")
    target_payload_mode = _request_first("target_payload_mode", "udp_target_payload_mode", "payload_mode") or "topic_value"
    return ADAPTER_TYPES["udp"](
        enabled=True,
        direction="both" if source_enabled and target_enabled else ("in" if source_enabled else "out"),
        datatype=datatype or "auto",
        source_enabled=source_enabled,
        source_host=source_host,
        source_port=source_port,
        listen_port=listen_port,
        source_payload_mode=source_payload_mode,
        source_topic=source_topic,
        source_json_path=source_json_path,
        target_enabled=target_enabled,
        target_host=target_host,
        target_ip=target_host,
        target_port=target_port,
        udp_topic=target_topic,
        target_payload_mode=target_payload_mode,
        payload_mode=target_payload_mode,
        format="",
    )


def _knx_adapter_from_request(datatype: str):
    group_address = _request_first("group_address", "knx_ga", "source_address", "topic", "value")
    dpt = _request_first("dpt", "knx_dpt", "detected_dpt", "configured_dpt")
    return ADAPTER_TYPES["knx"](
        enabled=True,
        direction="in",
        datatype=datatype or "auto",
        group_address=group_address,
        dpt=dpt,
    )


def _find_openccu_object(topic: str = "", name: str = ""):
    topic = _clean_prefill(topic)
    name = _clean_prefill(name).casefold()
    for item in object_service.list_objects():
        meta = dict(getattr(item, "meta", {}) or {})
        semantic_source = str(meta.get("source") or meta.get("origin_source") or "").strip().lower()
        if semantic_source != "openccu":
            continue
        stored_topic = _clean_prefill(meta.get("openccu_topic", ""))
        if topic and stored_topic and stored_topic == topic:
            return item
        if name and str(getattr(item, "name", "") or "").strip().casefold() == name:
            return item
    return None


def _openccu_live_value_from_request():
    raw = _clean_prefill(request.args.get("value", request.args.get("last_value", "")))
    if raw == "":
        return None
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return float(raw) if any(ch in lowered for ch in (".", "e")) else int(raw)
    except (TypeError, ValueError):
        return raw


def _object_payload_from_explorer() -> dict:
    explorer = _clean_prefill(request.args.get("explorer", "")).lower()
    source_type = _clean_prefill(request.args.get("source_type") or request.args.get("source") or explorer or "").lower()
    if not explorer:
        explorer = source_type or "mqtt"
    mode = _clean_prefill(request.args.get("mode", request.args.get("payload_mode", request.args.get("source_payload_mode", "")))).lower()

    display_name = _clean_prefill(request.args.get("name", request.args.get("display_name", "")))
    fallback_name = (
        _clean_prefill(request.args.get("visu_name", ""))
        or _clean_prefill(request.args.get("loxone_io", ""))
        or _clean_prefill(request.args.get("topic", request.args.get("source_address", "")))
        or _clean_prefill(request.args.get("group_address", request.args.get("knx_ga", "")))
        or _clean_prefill(request.args.get("mqtt_json_key", request.args.get("json_key", "")))
    )
    name = display_name or fallback_name or "Neues Objekt"
    datatype = _datatype_from_request()
    json_key = _request_first("mqtt_json_key", "json_key")
    payload = {
        "id": "",
        "name": name,
        "datatype": datatype,
        "category": _clean_prefill(request.args.get("category", "")),
        "room": _clean_prefill(request.args.get("room", "")),
        "unit": _clean_prefill(request.args.get("unit", "")),
        "notes": _clean_prefill(request.args.get("description", request.args.get("notes", ""))),
        "enabled": True,
    }

    if explorer == "loxone" or source_type == "loxone":
        adapter = _loxone_adapter_from_request(datatype)
        payload["loxone"] = adapter.serialize()
        if not payload["room"]:
            payload["room"] = adapter.room
        if not payload["unit"]:
            payload["unit"] = adapter.unit
        if not payload["category"]:
            payload["category"] = "Loxone"
    elif explorer in {"mqtt", "openccu"} or source_type in {"mqtt", "openccu"}:
        topic = _request_first("topic", "source_address", "source_topic")
        if topic:
            if explorer == "openccu" or source_type == "openccu":
                payload["source"] = "openccu"
                payload["origin_source"] = "openccu"
                payload["openccu_topic"] = topic
                payload["openccu_device"] = _clean_prefill(request.args.get("openccu_device", ""))
                payload["openccu_channel"] = _clean_prefill(request.args.get("openccu_channel", ""))
                payload["openccu_datapoint"] = _clean_prefill(request.args.get("openccu_datapoint", ""))
                if not payload["category"]:
                    payload["category"] = "OpenCCU"
            else:
                payload["mqtt"] = _adapter_for_core_fields("mqtt", topic, datatype, True, "both", json_key=json_key).serialize()
                if not payload["category"]:
                    payload["category"] = "MQTT"
    elif explorer == "udp" or source_type == "udp":
        adapter = _udp_adapter_from_request(datatype)
        if mode != "json":
            if hasattr(adapter, "source_json_path"):
                adapter.source_json_path = ""
        if (
            str(getattr(adapter, "source_topic", "") or "").strip()
            or str(getattr(adapter, "source_json_path", "") or "").strip()
            or str(getattr(adapter, "listen_port", "") or "").strip()
            or str(getattr(adapter, "target_host", "") or "").strip()
            or str(getattr(adapter, "target_port", "") or "").strip()
            or str(getattr(adapter, "udp_topic", "") or "").strip()
        ):
            payload["udp"] = adapter.serialize()
            payload["source_type"] = "udp"
            payload["source_address"] = (
                str(getattr(adapter, "source_topic", "") or "").strip()
                or str(getattr(adapter, "listen_port", "") or "").strip()
                or str(getattr(adapter, "source_json_path", "") or "").strip()
            )
            if not payload["category"]:
                payload["category"] = "UDP"
            if not payload["unit"]:
                payload["unit"] = _clean_prefill(request.args.get("unit", ""))
    elif explorer == "knx" or source_type == "knx":
        adapter = _knx_adapter_from_request(datatype)
        if str(getattr(adapter, "group_address", "") or "").strip():
            payload["knx"] = adapter.serialize()
            payload["source_type"] = "knx"
            payload["source_address"] = adapter.group_address
            if not payload["category"]:
                payload["category"] = "KNX"
    elif explorer == "influx" or source_type == "influx":
        measurement = _clean_prefill(request.args.get("measurement", ""))
        field = _clean_prefill(request.args.get("field", "")) or "value"
        influx_topic = _clean_prefill(request.args.get("topic", ""))
        if measurement:
            adapter_cls = ADAPTER_TYPES["influx"]
            payload["influx"] = adapter_cls(
                enabled=True,
                direction="out",
                datatype=datatype,
                measurement=measurement,
                field=field,
                topic=influx_topic,
            ).serialize()
            if not payload["category"]:
                payload["category"] = "Influx"

    return payload


def _log_create_object_failed(reason: str, selected_uuid: str = "", selected_name: str = "", selected_io: str = "", explorer: str = "", source: str = ""):
    current_app.logger.error("CREATE OBJECT FAILED")
    current_app.logger.error(f"request.args={request.args}")
    current_app.logger.error(f"request.form={request.form}")
    current_app.logger.error(f"json={request.get_json(silent=True)}")
    current_app.logger.error(f"selected_uuid={selected_uuid or ''}")
    current_app.logger.error(f"selected_name={selected_name or ''}")
    current_app.logger.error(f"selected_io_address={selected_io or ''}")
    current_app.logger.error(f"explorer={explorer or ''}")
    current_app.logger.error(f"source={source or ''}")
    current_app.logger.error(f"reason={reason}")


def _objects_index_redirect(object_id: str = "", tab: str = "general", notice: str = ""):
    redirect_args = {}
    if object_id:
        redirect_args["selected"] = object_id
    redirect_args["tab"] = tab or "general"
    embed_ts = _clean_prefill(request.args.get("_embed_ts", ""))
    if embed_ts:
        redirect_args["_embed_ts"] = embed_ts
    if notice:
        redirect_args["notice"] = notice
    return redirect(url_for("objects_v33.objects_v33_index", **redirect_args))


def _mqtt_broker_choices():
    choices = ["Hauptbroker"]
    core = current_app.extensions.get("app_core")
    try:
        brokers = core.load_mqtt_brokers() if core and hasattr(core, "load_mqtt_brokers") else []
    except Exception:
        brokers = []
    for broker in brokers or []:
        if not isinstance(broker, dict) or not broker.get("enabled", True):
            continue
        name = str(broker.get("name") or "").strip()
        if name and name not in choices:
            choices.append(name)
    return choices


def _detail_context(selected, selected_tab: str = "general", notice: str = "", errors=None, is_new: bool | None = None):
    selected_source_type = _selected_source_type(selected) if selected else "unbekannt"
    if selected is not None and hasattr(selected, "_selected_source_type"):
        selected_source_type = str(getattr(selected, "_selected_source_type", "unbekannt") or "unbekannt").strip().lower() or "unbekannt"
    return {
        "selected": selected,
        "selected_adapters": _ensure_known_adapters(selected) if selected else [],
        "selected_preview": build_object_routing_preview(selected) if selected else [],
        "selected_route_report": object_service.get_object_route_report(selected) if selected else None,
        "loxone_target_options": _loxone_target_options(),
        "mqtt_broker_choices": _mqtt_broker_choices(),
        "adapter_template_name": adapter_template_name,
        "selected_tab": selected_tab or "general",
        "notice": notice or "",
        "errors": errors or [],
        "is_new": bool(is_new) if is_new is not None else not bool(selected),
        "adapter_protocols": _adapter_protocols,
        "route_status": _route_status,
        "current_source_label": _current_source_label,
        "current_source_address": _current_source_address,
        "selected_source_type": selected_source_type,
    }


@bp.route("/objects_v33")
def objects_v33_index():
    query = request.args.get("q", "")
    active_filter = request.args.get("filter", "all")
    objects = _filtered_objects(query, active_filter)
    selected_id = request.args.get("selected", "").strip()
    if selected_id in {"_none", "none", "null"}:
        selected = None
    else:
        selected = object_service.get_object(selected_id) if selected_id else (objects[0] if objects else None)
    return render_template(
        "objects_v33/list.html",
        objects=objects,
        visible_count=len(objects),
        query=query,
        active_filter=active_filter,
        **_detail_context(selected, request.args.get("tab", "general"), request.args.get("notice", "")),
    )


@bp.route("/objects_v33/new")
def objects_v33_new():
    # /new ist nur für manuelles +Neu. Alte Explorer-Links mit Parametern werden
    # hier abgefangen und direkt in eine echte Speicherung umgeleitet.
    explorer_keys = {"explorer", "source_type", "source", "source_address", "source_topic", "topic", "loxone_uuid", "loxone_io"}
    if any(key in request.args for key in explorer_keys):
        return redirect(url_for("objects_v33.objects_v33_create_from_explorer", **request.args.to_dict(flat=True)))

    objects = _filtered_objects("", "all")
    source_type = _clean_prefill(request.args.get("source_type") or request.args.get("source") or "mqtt").lower()
    return render_template(
        "objects_v33/list.html",
        objects=objects,
        visible_count=len(objects),
        query="",
        active_filter="all",
        **_detail_context(_blank_object_draft(source_type), "general", request.args.get("notice", ""), errors=[], is_new=True),
    )


@bp.route("/objects_v33/panel/<object_uuid>")
def objects_v33_panel(object_uuid):
    object_uuid = _clean_prefill(object_uuid)
    selected_tab = request.args.get("tab", "general")
    notice = request.args.get("notice", "")
    if object_uuid in {"", "_none", "none", "null"}:
        selected = None
    else:
        selected = object_service.get_object(object_uuid)
    return render_template("objects_v33/_detail.html", **_detail_context(selected, selected_tab, notice))


@bp.route("/objects_v33/create_from_explorer")
def objects_v33_create_from_explorer():
    explorer = _clean_prefill(request.args.get("explorer", "")).lower()
    source_type = _clean_prefill(request.args.get("source_type") or request.args.get("source") or explorer or "").lower()
    loxone_uuid = _request_first("loxone_uuid", "state_uuid", "uuid", "control_uuid")
    selected_io = _request_first("loxone_io", "io_address", "source_address", "path")
    topic = _request_first("topic", "source_topic")
    objects_before_ids = [item.id for item in object_service.list_objects()]
    source = explorer or source_type
    if source not in ADAPTER_TYPES:
        if loxone_uuid or selected_io:
            source = "loxone"
        elif topic:
            source = "mqtt"
        else:
            source = "mqtt"
    tab = "loxone" if source == "loxone" else (_clean_prefill(request.args.get("tab", source or "general")) or "general")
    display_name = _clean_prefill(request.args.get("name", request.args.get("visu_name", ""))) or "Neues Objekt"
    if source == "loxone" and not selected_io:
        selected_io = _request_first("topic", "name")
    request_args = request.args.to_dict(flat=True)
    _log_explorer_debug(
        "request",
        route="objects_v33_create_from_explorer",
        url=request.url,
        path=request.path,
        referrer=request.referrer or "",
        embedded_hint="_embed_ts" in request.args,
        args=request_args,
        form=request.form.to_dict(flat=True),
        json=request.get_json(silent=True),
        selected_uuid=loxone_uuid,
        selected_name=display_name,
        selected_topic=_clean_prefill(request.args.get("topic", "")),
        selected_io=selected_io,
        objects_before_ids=objects_before_ids,
    )

    try:
        with _EXPLORER_CREATE_LOCK:
            if source == "loxone" and not (loxone_uuid or selected_io):
                create_phase = "validate_minimum_loxone_payload"
                reason = "missing required loxone uuid/io_address"
                _log_create_object_failed(reason, loxone_uuid, display_name, selected_io, explorer, source)
                notice = "Objekt konnte nicht erstellt werden. Bitte Auswahl pruefen und erneut versuchen."
                _log_explorer_debug(
                    "notice",
                    generator="objects_v33_create_from_explorer",
                    location=f"{__file__}:{inspect.currentframe().f_lineno if inspect.currentframe() else 'unknown'}",
                    url=request.url,
                    args=request_args,
                    object_id="",
                    error="",
                    reason=reason,
                    notice=notice,
                )
                return _objects_index_redirect("", tab, notice)

            create_phase = "find_existing_by_loxone_uuid"
            if source == "loxone":
                existing = _find_object_by_loxone_endpoint(loxone_uuid, selected_io)
            elif source == "openccu":
                existing = _find_openccu_object(topic, display_name)
            else:
                existing = None
            duplicate_found = existing is not None
            duplicate_object_id = existing.id if existing is not None else ""
            current_app.logger.info(
                "CREATE REQUEST source=%s uuid=%s io=%s objects_before_ids=%s duplicate_found=%s duplicate_object_id=%s action=%s",
                source or "",
                loxone_uuid or "",
                selected_io or "",
                ",".join(objects_before_ids),
                str(bool(duplicate_found)).lower(),
                duplicate_object_id or "",
                "opened" if duplicate_found else "pending",
            )
            if existing is not None:
                if source == "openccu" and topic:
                    repair_payload = existing.to_dict()
                    repair_payload.update({
                        "source": "openccu",
                        "origin_source": "openccu",
                        "openccu_topic": topic,
                        "openccu_device": _clean_prefill(request.args.get("openccu_device", "")),
                        "openccu_channel": _clean_prefill(request.args.get("openccu_channel", "")),
                        "openccu_datapoint": _clean_prefill(request.args.get("openccu_datapoint", "")),
                    })
                    existing = object_service.update_object(existing.id, repair_payload) or existing
                    live_value = _openccu_live_value_from_request()
                    if live_value is not None:
                        object_service.update_object_live_value(
                            existing.id,
                            live_value,
                            source="openccu",
                            endpoint="openccu.topic",
                            source_address=topic,
                            status="aktiv",
                        )
                _log_explorer_debug("existing", args=request_args, object_id=existing.id, payload={})
                _log_explorer_import(source, loxone_uuid, existing.name or display_name, existing.id, "existing")
                current_app.logger.info(
                    "CREATE RESULT source=%s uuid=%s object_id=%s action=opened",
                    source or "",
                    loxone_uuid or "",
                    existing.id or "",
                )
                return _objects_index_redirect(existing.id, tab)

            create_phase = "build_payload_from_explorer"
            payload = _object_payload_from_explorer()
            _log_explorer_debug("payload", args=request_args, payload=payload)
            create_phase = "create_object"
            object_def = object_service.create_object(payload)
            if source == "openccu" and topic:
                live_value = _openccu_live_value_from_request()
                if live_value is not None:
                    object_service.update_object_live_value(
                        object_def.id,
                        live_value,
                        source="openccu",
                        endpoint="openccu.topic",
                        source_address=topic,
                        status="aktiv",
                    )
            create_phase = "reload_object_routes"
            if not _safe_reload_object_routes("create_from_explorer"):
                current_app.logger.error(
                    "Object Explorer Import route reload failed object_id=%s source=%s uuid=%s",
                    object_def.id,
                    source,
                    loxone_uuid,
                )
            objects_after_ids = [item.id for item in object_service.list_objects()]
            _log_explorer_debug("created", args=request_args, object_id=object_def.id, payload=payload)
            _log_explorer_import(source, loxone_uuid, object_def.name or display_name, object_def.id, "created")
            current_app.logger.info(
                "CREATE RESULT source=%s uuid=%s object_id=%s action=created objects_after_ids=%s",
                source or "",
                loxone_uuid or "",
                object_def.id or "",
                ",".join(objects_after_ids),
            )
            return _objects_index_redirect(object_def.id, tab)
    except Exception as exc:
        current_app.logger.exception("Explorer-Import fehlgeschlagen")
        fallback = None
        try:
            fallback = _find_object_by_loxone_endpoint(loxone_uuid, selected_io) if source == "loxone" else None
        except Exception:
            current_app.logger.exception("Explorer-Import Fallback-Suche fehlgeschlagen")
        object_id = fallback.id if fallback is not None else ""
        _log_explorer_import(source, loxone_uuid, display_name, object_id, "error", str(exc))
        frame = inspect.currentframe()
        notice_location = f"{__file__}:{(frame.f_lineno + 1) if frame else 'unknown'}"
        reason = f"exception during {locals().get('create_phase', 'unknown')}: {type(exc).__name__}: {exc}"
        _log_create_object_failed(reason, loxone_uuid, display_name, selected_io, explorer, source)
        notice = "Objekt konnte nicht erstellt werden. Bitte Auswahl pruefen und erneut versuchen."
        _log_explorer_debug(
            "notice",
            generator="objects_v33_create_from_explorer",
            location=notice_location,
            url=request.url,
            args=request_args,
            object_id=object_id,
            error=str(exc),
            reason=reason,
            notice=notice,
        )
        current_app.logger.info(
            "CREATE RESULT source=%s uuid=%s object_id=%s action=error",
            source or "",
            loxone_uuid or "",
            object_id or "",
        )
        return _objects_index_redirect(object_id, tab, notice)


@bp.route("/objects_v33/edit/<object_uuid>")
def objects_v33_edit(object_uuid):
    object_def = object_service.get_object(object_uuid)
    if object_def is None:
        return redirect(url_for("objects_v33.objects_v33_index"))
    return redirect(url_for("objects_v33.objects_v33_index", selected=object_def.id))


@bp.route("/objects_v33/save", methods=["POST"])
def objects_v33_save():
    object_uuid = request.form.get("uuid", "").strip()
    source_type = request.form.get("source_type", "").strip().lower()
    payload = {
        "id": object_uuid,
        "name": request.form.get("name", "").strip(),
        "datatype": request.form.get("datatype", request.form.get("type", "auto")).strip(),
        "unit": request.form.get("unit", "").strip(),
        "enabled": "enabled" in request.form,
        "notes": request.form.get("notes", "").strip(),
        "room": request.form.get("room", "").strip(),
        "category": request.form.get("category", "").strip(),
        "icon": request.form.get("icon", "").strip(),
        "scaling": request.form.get("scaling", "").strip(),
        "source_type": request.form.get("source_type", "").strip(),
        "source_address": request.form.get("source_address", "").strip(),
    }
    if source_type == "udp" or any(
        str(request.form.get(field, "") or "").strip()
        for field in (
            "udp_source_host",
            "source_host",
            "udp_host",
            "sender_host",
            "udp_source_port",
            "source_port",
            "udp_sender_port",
            "sender_port",
            "udp_listen_port",
            "listen_port",
            "udp_port",
            "port",
            "source_topic",
            "udp_source_topic",
            "topic",
            "udp_path",
            "path",
            "source_json_path",
            "udp_source_json_path",
            "udp_topic",
            "target_topic",
            "target_host",
            "udp_target_host",
            "target_ip",
            "udp_target_ip",
            "target_port",
            "udp_target_port",
        )
    ):
        udp_adapter = _udp_adapter_from_request(payload["datatype"])
        if (
            str(getattr(udp_adapter, "source_topic", "") or "").strip()
            or str(getattr(udp_adapter, "source_json_path", "") or "").strip()
            or str(getattr(udp_adapter, "listen_port", "") or "").strip()
            or str(getattr(udp_adapter, "target_host", "") or "").strip()
            or str(getattr(udp_adapter, "target_port", "") or "").strip()
            or str(getattr(udp_adapter, "udp_topic", "") or "").strip()
        ):
            payload["udp"] = udp_adapter.serialize()
            payload["source_type"] = "udp"
            payload["source_address"] = (
                str(getattr(udp_adapter, "source_topic", "") or "").strip()
                or str(getattr(udp_adapter, "listen_port", "") or "").strip()
                or str(getattr(udp_adapter, "source_json_path", "") or "").strip()
                or str(getattr(udp_adapter, "udp_topic", "") or "").strip()
            )
    try:
        if object_uuid:
            object_def = object_service.update_object(object_uuid, payload)
            if object_def is None:
                current_app.logger.warning("Object Save skipped: object not found uuid=%s", object_uuid)
                return _objects_index_redirect("", "general", "Objekt nicht gefunden. Liste wurde neu geladen.")
        else:
            object_def = object_service.create_object(payload)
    except ValueError as exc:
        errors = str(exc).split("; ")
        if _wants_ajax_response():
            return jsonify({"ok": False, "errors": errors}), 400
        object_def = object_service.get_object(object_uuid) if object_uuid else object_service.build_object(payload)
        return render_template(
            "objects_v33/edit.html",
            object_def=object_def,
            adapters=_ensure_known_adapters(object_def),
            adapter_template_name=adapter_template_name,
            routing_preview=build_object_routing_preview(object_def),
            errors=errors,
            is_new=not bool(object_uuid),
        ), 400
    except Exception as exc:
        current_app.logger.exception("Objekt speichern fehlgeschlagen")
        return _objects_index_redirect(object_uuid, "general", f"Objekt konnte nicht gespeichert werden: {exc}")

    _safe_reload_object_routes("save")
    if _wants_ajax_response():
        return jsonify({"ok": True, "object_id": object_def.id, "tab": "general"})
    return redirect(url_for("objects_v33.objects_v33_index", selected=object_def.id))


@bp.route("/objects_v33/delete/<object_uuid>", methods=["POST"])
def objects_v33_delete(object_uuid):
    object_uuid = _clean_prefill(object_uuid)
    selected_before = _clean_prefill(request.form.get("selected_before", "") or request.form.get("selected", "") or request.args.get("selected", ""))
    current_app.logger.info("delete_start object_id=%s selected_before=%s", object_uuid, selected_before or "")
    found = False
    deleted = False
    error = ""
    selected_after = "_none"
    try:
        found = object_service.get_object(object_uuid) is not None
        deleted = object_service.delete_object(object_uuid)
        current_app.logger.info("write_objects_done object_id=%s deleted=%s", object_uuid, str(bool(deleted)).lower())
    except Exception as exc:
        error = str(exc)
        current_app.logger.exception("Objektloeschen fehlgeschlagen")

    reload_requested = False
    try:
        reload_requested = bool(_safe_reload_object_routes("delete"))
    except Exception as exc:
        error = f"{error}; {exc}" if error else str(exc)
        current_app.logger.exception("Objektloeschen: Reload-Anforderung fehlgeschlagen")

    cache_invalidated = bool(deleted or found is False)
    current_app.logger.info(
        "DELETE REQUEST requested_id=%s found=%s deleted=%s selected_before=%s selected_after=%s cache_invalidated=%s reload_requested=%s action=%s",
        object_uuid,
        str(bool(found)).lower(),
        str(bool(deleted)).lower(),
        selected_before or "",
        selected_after or "",
        str(bool(cache_invalidated)).lower(),
        str(bool(reload_requested)).lower(),
        "deleted" if deleted else ("not_found" if not found else "error"),
    )
    redirect_target = url_for("objects_v33.objects_v33_index", selected=selected_after)
    current_app.logger.info("delete_response_sent object_id=%s redirect=%s", object_uuid, redirect_target)
    _log_object_delete(object_uuid, found, deleted, redirect_target, error)
    return redirect(redirect_target)


@bp.route("/objects_v33/edit/<object_uuid>/adapter/<protocol>")
def objects_v33_adapter_edit(object_uuid, protocol):
    object_def = object_service.get_object(object_uuid)
    protocol = str(protocol or "").strip().lower()
    if object_def is None or protocol not in ADAPTER_TYPES:
        return redirect(url_for("objects_v33.objects_v33_index"))
    adapter = _adapter_map(object_def).get(protocol) or ADAPTER_TYPES[protocol](enabled=False)
    return render_template(
        "objects_v33/adapter.html",
        object_def=object_def,
        adapter=adapter,
        adapter_template_name=adapter_template_name,
        loxone_target_options=_loxone_target_options(),
        mqtt_broker_choices=_mqtt_broker_choices(),
        selected_source_type=_selected_source_type(object_def),
        errors=[],
    )


@bp.route("/objects_v33/edit/<object_uuid>/adapter/<protocol>/save", methods=["POST"])
def objects_v33_adapter_save(object_uuid, protocol):
    object_def = object_service.get_object(object_uuid)
    protocol = str(protocol or "").strip().lower()
    if object_def is None or protocol not in ADAPTER_TYPES:
        return redirect(url_for("objects_v33.objects_v33_index"))

    adapter = adapter_from_form(protocol, request.form)
    errors = adapter.validate()
    if errors:
        if _wants_ajax_response():
            return jsonify({"ok": False, "errors": errors}), 400
        return render_template(
            "objects_v33/adapter.html",
            object_def=object_def,
            adapter=adapter,
            adapter_template_name=adapter_template_name,
            loxone_target_options=_loxone_target_options(),
            mqtt_broker_choices=_mqtt_broker_choices(),
            errors=errors,
        ), 400

    adapters = _adapter_map(object_def)
    adapters[protocol] = adapter
    object_def.adapters = [adapters[item] for item in ("mqtt", "udp", "knx", "loxone", "influx") if item in adapters]
    payload = object_service.serialize_object(object_def)
    payload[protocol] = adapter.serialize()
    object_service.update_object(object_def.id, payload)
    _safe_reload_object_routes("adapter_save")
    if _wants_ajax_response():
        return jsonify({"ok": True, "object_id": object_def.id, "tab": protocol})
    return redirect(url_for("objects_v33.objects_v33_index", selected=object_def.id))
