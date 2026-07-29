import json
import re

from flask import request
from markupsafe import escape


def bind_context(context):
    for name, value in vars(context).items():
        if not name.startswith("__"):
            globals()[name] = value


def _object_guess_name(value):
    text = str(value or "").strip().strip("/")
    if not text:
        return ""
    # Bei JSON-Key oder Topic den lesbarsten letzten Teil nehmen.
    parts = re.split(r"[/.]", text)
    clean = [p for p in parts if p]
    if not clean:
        return text
    if len(clean) >= 2 and clean[-1].lower() in ["value", "state", "contact", "temperature", "humidity", "battery", "voltage"]:
        return (clean[-2] + " " + clean[-1]).replace("_", " ").title()
    return clean[-1].replace("_", " ").title()


def _object_apply_prefill(item):
    """Prefill object fields from explorer quick-links via query parameters."""
    field_map = {
        "mqtt_topic": "mqtt_topic",
        "mqtt_json_key": "mqtt_json_key",
        "loxone_topic": "loxone_topic",
        "knx_ga": "knx_ga",
        "udp_topic": "udp_topic",
        "influx_topic": "influx_topic",
        "name": "name",
        "room": "room",
        "type": "type",
    }
    changed = False
    for arg, field in field_map.items():
        val = str(request.args.get(arg, "") or "").strip()
        if not val:
            continue
        if field == "knx_ga":
            val = normalize_knx_group_address(val)
        item[field] = val
        changed = True

    # Generischer Schnelllink: /objects/edit/new?source=mqtt&value=...
    source = str(request.args.get("source", "") or "").strip().lower()
    value = str(request.args.get("value", "") or "").strip()
    if source and value:
        if source == "mqtt":
            item["mqtt_topic"] = value
        elif source == "loxone":
            item["loxone_topic"] = value
        elif source == "knx":
            item["knx_ga"] = normalize_knx_group_address(value)
        elif source == "udp":
            item["udp_topic"] = value
        elif source == "influx":
            item["influx_topic"] = value
        changed = True

    if changed and not str(item.get("name", "")).strip():
        item["name"] = _object_guess_name(
            item.get("influx_topic") or item.get("mqtt_json_key") or item.get("mqtt_topic") or item.get("loxone_topic") or item.get("knx_ga") or item.get("udp_topic")
        )
    return item


def _object_candidate_list(source):
    """Return selectable candidates for object editor datalists."""
    source = str(source or "").lower().strip()
    result = []
    seen = set()

    def add(value, label="", extra=""):
        value = str(value or "").strip()
        if not value or value in seen:
            return
        seen.add(value)
        result.append({"value": value, "label": str(label or ""), "extra": str(extra or "")})

    if source == "mqtt":
        try:
            for _key, info in sorted(mqtt_monitor_values.items(), key=lambda x: str(x[0]).lower()):
                if isinstance(info, dict):
                    add(info.get("topic", _key), info.get("payload", info.get("value", "")), info.get("time", ""))
                else:
                    add(_key, "", "")
        except Exception:
            pass
        for loader, key in [(load_mqtt2lox_config, "source_topic"), (load_mqtt2udp_config, "source_topic"), (load_mqtt2knx_config, "source_topic"), (load_udp2mqtt_config, "mqtt_topic")]:
            try:
                for item in loader():
                    add(item.get(key, ""), item.get("mapping_alias", "") or item.get("set_name", ""), "Mapping")
            except Exception:
                pass

    elif source == "knx":
        try:
            for ga, info in sorted(knx_monitor_values.items(), key=lambda x: x[0]):
                add(ga, info.get("value", ""), info.get("dpt", ""))
        except Exception:
            pass
        for loader in [load_mqtt2knx_config, load_knx2mqtt_config, load_udp2knx_config, load_knx2lox_config]:
            try:
                for item in loader():
                    add(normalize_knx_group_address(item.get("group_address", "")), item.get("mapping_alias", "") or item.get("set_name", ""), "Mapping")
            except Exception:
                pass

    elif source == "loxone":
        try:
            for item in load_mqtt2lox_config():
                add(item.get("loxone_io", ""), item.get("mapping_alias", "") or item.get("set_name", ""), item.get("source_topic", ""))
        except Exception:
            pass
        try:
            for item in load_knx2lox_config():
                add(item.get("loxone_io", ""), item.get("mapping_alias", "") or item.get("set_name", ""), item.get("group_address", ""))
        except Exception:
            pass

    elif source == "udp":
        try:
            for item in load_udp2mqtt_config():
                add(item.get("udp_topic", ""), item.get("mapping_alias", "") or item.get("set_name", ""), "UDP→MQTT")
            for item in load_udp2knx_config():
                add(item.get("source_topic", ""), item.get("mapping_alias", "") or item.get("set_name", ""), "UDP→KNX")
            for item in load_mqtt2udp_config():
                add(item.get("udp_topic", ""), item.get("mapping_alias", "") or item.get("set_name", ""), "MQTT→UDP")
        except Exception:
            pass

    elif source == "influx":
        try:
            ok, _msg, topics = influx_get_topics(search="", limit=600)
            if ok:
                for item in topics:
                    add(item.get("topic", ""), item.get("last_value", ""), item.get("last_time", ""))
        except Exception:
            pass
        try:
            tc = load_topic_config()
            for key, cfg in tc.items():
                if isinstance(cfg, dict) and cfg.get("influx"):
                    add(cfg.get("influx_topic") or key, cfg.get("influx_value_type", ""), "Config")
        except Exception:
            pass

    return result[:1000]


def _object_datalist_html(source, list_id):
    options = []
    for item in _object_candidate_list(source):
        label = " ".join(x for x in [item.get("label", ""), item.get("extra", "")] if x)
        options.append(f'<option value="{escape(item.get("value", ""))}" label="{escape(label)}"></option>')
    return f'<datalist id="{escape(list_id)}">' + "".join(options) + '</datalist>'


def _object_value_from_sources(item):
    object_id = str(item.get("id", "") or "").strip()
    live_cache = globals().get("OBJECT_LIVE_CACHE", {})
    source_labels = {
        "mqtt": "MQTT",
        "loxone": "Loxone",
        "udp": "UDP",
        "knx": "KNX",
        "influx": "Influx",
    }
    if object_id and isinstance(live_cache, dict):
        live = live_cache.get(object_id)
        if isinstance(live, dict):
            live_value = live.get("value", "")
            if live_value not in ("", None):
                live_source = str(live.get("source") or live.get("original_source") or "").strip()
                if live_source:
                    return source_labels.get(live_source.lower(), live_source.title()), live_value, str(live.get("timestamp", "") or "")
    candidates = []
    mqtt_topic = str(item.get("mqtt_topic", "") or "").strip()
    loxone_topic = str(item.get("loxone_topic", "") or "").strip()
    knx_ga = normalize_knx_group_address(item.get("knx_ga", ""))
    influx_topic = str(item.get("influx_topic", "") or "").strip()
    udp_topic = str(item.get("udp_topic", "") or "").strip()
    if mqtt_topic and 'mqtt_monitor_values' in globals():
        m = mqtt_monitor_values.get(mqtt_topic) or mqtt_monitor_values.get(mqtt_topic.rstrip('/'))
        if not isinstance(m, dict):
            try:
                m = next((info for info in mqtt_monitor_values.values() if isinstance(info, dict) and str(info.get("topic", "")) == mqtt_topic), None)
            except Exception:
                m = None
        if isinstance(m, dict):
            payload = m.get("payload", m.get("value", ""))
            json_key = str(item.get("mqtt_json_key", "") or "").strip()
            if json_key:
                try:
                    data = json.loads(payload) if isinstance(payload, str) else payload
                    val = get_nested_value(data, json_key)
                    if val is not None:
                        payload = val
                except Exception:
                    pass
            candidates.append(("MQTT", payload, m.get("time", "")))
    if loxone_topic and 'display_values' in globals():
        v = display_values.get(loxone_topic, "")
        if v != "":
            candidates.append(("Loxone", v, ""))
    if knx_ga and 'knx_monitor_values' in globals():
        k = knx_monitor_values.get(knx_ga)
        if isinstance(k, dict):
            candidates.append(("KNX", k.get("value", ""), k.get("time", "")))
    if udp_topic and 'udp2mqtt_last_seen' in globals():
        u = udp2mqtt_last_seen.get(udp_topic)
        if isinstance(u, dict):
            candidates.append(("UDP", u.get("value", ""), u.get("time", "")))
    if candidates:
        return candidates[0]
    if influx_topic:
        return ("Influx", "Historie vorhanden/konfiguriert", "")
    return ("-", "-", "")


# ---------- Legacy Objekt -> automatische Mapping-Erzeugung ----------
def _object_clean_text(value):
    return str(value or "").strip()


def _object_append_mapping_if_missing(data, match_fn, new_item):
    """Append mapping only if an equivalent mapping does not already exist."""
    if not isinstance(data, list):
        data = []
    for existing in data:
        try:
            if isinstance(existing, dict) and match_fn(existing):
                return data, False
        except Exception:
            pass
    data.append(new_item)
    return data, True


def ensure_object_mappings(item):
    """Create missing bridge mappings from a Smart-Home object.

    The object remains the master/meta layer. This helper only creates missing
    technical mappings; existing mappings are never overwritten. So Stephan can
    safely save an object again without producing duplicate mapping confetti.
    """
    created = []
    warnings = []

    name = _object_clean_text(item.get("name")) or "Objekt"
    room = _object_clean_text(item.get("room"))
    typ = _object_clean_text(item.get("type"))
    alias = " / ".join(x for x in [room, name, typ] if x)

    mqtt_topic = _object_clean_text(item.get("mqtt_topic"))
    mqtt_json_key = _object_clean_text(item.get("mqtt_json_key"))
    loxone_topic = _object_clean_text(item.get("loxone_topic"))
    knx_ga = normalize_knx_group_address(item.get("knx_ga", ""))
    udp_topic = _object_clean_text(item.get("udp_topic"))
    influx_topic = _object_clean_text(item.get("influx_topic")).strip("/")

    payload_mode = "json_key" if mqtt_json_key else "raw"

    # MQTT -> Loxone
    if mqtt_topic and loxone_topic:
        data = load_mqtt2lox_config()
        new_item = {
            "enabled": True,
            "source_topic": mqtt_topic,
            "custom_topic": "",
            "loxone_io": loxone_topic,
            "payload_mode": payload_mode,
            "json_key": mqtt_json_key,
            "output_mode": "single",
            "group": room,
            "set_name": name,
            "mapping_alias": alias or name,
            "object_id": _object_clean_text(item.get("id")),
        }
        data, did = _object_append_mapping_if_missing(
            data,
            lambda x: _object_clean_text(x.get("source_topic")) == mqtt_topic and _object_clean_text(x.get("loxone_io")) == loxone_topic and _object_clean_text(x.get("json_key")) == mqtt_json_key,
            new_item,
        )
        if did:
            save_mqtt2lox_config(data)
            created.append("MQTT→Loxone")

    # MQTT -> UDP
    if mqtt_topic and udp_topic:
        data = load_mqtt2udp_config()
        # Ziel-IP kann aus einem Objekt nicht zuverlässig geraten werden. Wenn es schon
        # vorhandene MQTT→UDP Mappings gibt, übernehmen wir deren Ziel als freundlichen Default.
        default_ip = ""
        default_port = "7000"
        try:
            for old in data:
                if isinstance(old, dict) and old.get("udp_ip"):
                    default_ip = _object_clean_text(old.get("udp_ip"))
                    default_port = _object_clean_text(old.get("udp_port")) or default_port
                    break
        except Exception:
            pass
        new_item = {
            "enabled": True,
            "group": room,
            "set_name": name,
            "mapping_alias": alias or name,
            "source_topic": mqtt_topic,
            "udp_topic": udp_topic,
            "udp_ip": default_ip,
            "udp_port": default_port,
            "udp_format": "topic_value",
            "payload_mode": payload_mode,
            "json_key": mqtt_json_key,
            "test_value": "123",
        }
        data, did = _object_append_mapping_if_missing(
            data,
            lambda x: _object_clean_text(x.get("source_topic")) == mqtt_topic and _object_clean_text(x.get("udp_topic")) == udp_topic and _object_clean_text(x.get("json_key")) == mqtt_json_key,
            new_item,
        )
        if did:
            save_mqtt2udp_config(data)
            created.append("MQTT→UDP")
            if not default_ip:
                warnings.append("MQTT→UDP Ziel-IP fehlt noch")

    # MQTT -> KNX
    if mqtt_topic and knx_ga:
        data = load_mqtt2knx_config()
        new_item = {
            "enabled": True,
            "source_topic": mqtt_topic,
            "payload_mode": payload_mode,
            "json_key": mqtt_json_key,
            "group_address": knx_ga,
            "dpt": "1.001",
            "invert": False,
            "test_value": "1",
            "group": room,
            "set_name": name,
            "mapping_alias": alias or name,
            "object_id": _object_clean_text(item.get("id")),
        }
        data, did = _object_append_mapping_if_missing(
            data,
            lambda x: _object_clean_text(x.get("source_topic")) == mqtt_topic and normalize_knx_group_address(x.get("group_address", "")) == knx_ga and _object_clean_text(x.get("json_key")) == mqtt_json_key,
            new_item,
        )
        if did:
            save_mqtt2knx_config(data)
            created.append("MQTT→KNX")

    # KNX -> MQTT
    if knx_ga and mqtt_topic:
        data = load_knx2mqtt_config()
        new_item = {
            "enabled": True,
            "group_address": knx_ga,
            "mqtt_topic": mqtt_topic,
            "dpt": "1.001",
            "retain": True,
            "invert": False,
            "group": room,
            "set_name": name,
            "mapping_alias": alias or name,
            "object_id": _object_clean_text(item.get("id")),
        }
        data, did = _object_append_mapping_if_missing(
            data,
            lambda x: normalize_knx_group_address(x.get("group_address", "")) == knx_ga and _object_clean_text(x.get("mqtt_topic")) == mqtt_topic,
            new_item,
        )
        if did:
            save_knx2mqtt_config(data)
            created.append("KNX→MQTT")

    # KNX -> Loxone
    if knx_ga and loxone_topic:
        data = load_knx2lox_config()
        new_item = {
            "enabled": True,
            "group_address": knx_ga,
            "loxone_io": loxone_topic,
            "dpt": "1.001",
            "invert": False,
            "group": room,
            "set_name": name,
            "mapping_alias": alias or name,
            "object_id": _object_clean_text(item.get("id")),
        }
        data, did = _object_append_mapping_if_missing(
            data,
            lambda x: normalize_knx_group_address(x.get("group_address", "")) == knx_ga and _object_clean_text(x.get("loxone_io")) == loxone_topic,
            new_item,
        )
        if did:
            save_knx2lox_config(data)
            created.append("KNX→Loxone")

    # UDP -> MQTT
    if udp_topic and mqtt_topic:
        data = load_udp2mqtt_config()
        new_item = {
            "enabled": True,
            "udp_topic": udp_topic,
            "mqtt_topic": mqtt_topic,
            "retain": False,
            "test_value": "123",
            "group": room,
            "set_name": name,
            "mapping_alias": alias or name,
            "object_id": _object_clean_text(item.get("id")),
        }
        data, did = _object_append_mapping_if_missing(
            data,
            lambda x: _object_clean_text(x.get("udp_topic")) == udp_topic and _object_clean_text(x.get("mqtt_topic")) == mqtt_topic,
            new_item,
        )
        if did:
            save_udp2mqtt_config(data)
            created.append("UDP→MQTT")

    # UDP -> KNX
    if udp_topic and knx_ga:
        data = load_udp2knx_config()
        new_item = {
            "enabled": True,
            "source_topic": udp_topic,
            "group_address": knx_ga,
            "dpt": "1.001",
            "invert": False,
            "test_value": "1",
            "group": room,
            "set_name": name,
            "mapping_alias": alias or name,
            "object_id": _object_clean_text(item.get("id")),
        }
        data, did = _object_append_mapping_if_missing(
            data,
            lambda x: _object_clean_text(x.get("source_topic")) == udp_topic and normalize_knx_group_address(x.get("group_address", "")) == knx_ga,
            new_item,
        )
        if did:
            save_udp2knx_config(data)
            created.append("UDP→KNX")

    # Influx-Verknüpfung: MQTT/Loxone/UDP Topic oder KNX GA automatisch für Influx aktivieren.
    try:
        topic_settings = load_topic_config()

        if mqtt_topic and influx_topic:
            current = topic_settings.get(mqtt_topic, {})
            if not isinstance(current, dict):
                current = {}
            current.setdefault("enabled", True)
            current["influx_topic"] = influx_topic
            if mqtt_json_key:
                keys = current.get("influx_json_keys", [])
                if not isinstance(keys, list):
                    keys = []
                if mqtt_json_key not in keys:
                    keys.append(mqtt_json_key)
                types = current.get("influx_json_key_types", {})
                if not isinstance(types, dict):
                    types = {}
                types.setdefault(mqtt_json_key, "auto")
                current["influx_json_keys"] = keys
                current["influx_json_key_types"] = types
            else:
                current["influx"] = True
            topic_settings[mqtt_topic] = current
            created.append("MQTT→Influx")

        for raw_topic, label in [(loxone_topic, "Loxone→Influx"), (udp_topic, "UDP→Influx")]:
            if raw_topic and influx_topic:
                current = topic_settings.get(raw_topic, {})
                if not isinstance(current, dict):
                    current = {}
                current.setdefault("enabled", True)
                current["influx"] = True
                current["influx_topic"] = influx_topic
                topic_settings[raw_topic] = current
                created.append(label)

        if knx_ga and influx_topic:
            key = knx_influx_topic(knx_ga)
            if key:
                current = topic_settings.get(key, {})
                if not isinstance(current, dict):
                    current = {}
                current.setdefault("enabled", True)
                current["influx"] = True
                current["influx_topic"] = influx_topic
                topic_settings[key] = current
                created.append("KNX→Influx")

        save_topic_config(topic_settings)
    except Exception as e:
        warnings.append(f"Influx-Konfig Fehler: {e}")

    # Reihenfolge behalten, Dopplungen aus der Meldung entfernen.
    unique_created = []
    for entry in created:
        if entry not in unique_created:
            unique_created.append(entry)
    return unique_created, warnings


def cleanup_object_mappings(item):
    """Remove mappings that belong to a deleted object.

    New mappings contain object_id. For older object-created mappings we also
    remove exact matches based on the object's endpoints, so old leftovers can
    be cleaned up too.
    """
    removed = []
    warnings = []
    object_id = _object_clean_text(item.get("id"))
    mqtt_topic = _object_clean_text(item.get("mqtt_topic"))
    mqtt_json_key = _object_clean_text(item.get("mqtt_json_key"))
    loxone_topic = _object_clean_text(item.get("loxone_topic"))
    knx_ga = normalize_knx_group_address(item.get("knx_ga", ""))
    udp_topic = _object_clean_text(item.get("udp_topic"))
    influx_topic = _object_clean_text(item.get("influx_topic")).strip("/")

    def has_object_id(x):
        return object_id and _object_clean_text(x.get("object_id")) == object_id

    def filter_list(label, loader, saver, match_fn):
        try:
            data = loader()
            if not isinstance(data, list):
                data = []
            kept = []
            count = 0
            for x in data:
                try:
                    if isinstance(x, dict) and (has_object_id(x) or match_fn(x)):
                        count += 1
                        continue
                except Exception:
                    pass
                kept.append(x)
            if count:
                saver(kept)
                removed.append(f"{label} ({count})")
        except Exception as e:
            warnings.append(f"{label}: {e}")

    if mqtt_topic and loxone_topic:
        filter_list(
            "MQTT→Loxone", load_mqtt2lox_config, save_mqtt2lox_config,
            lambda x: _object_clean_text(x.get("source_topic")) == mqtt_topic and _object_clean_text(x.get("loxone_io")) == loxone_topic and _object_clean_text(x.get("json_key")) == mqtt_json_key,
        )

    if mqtt_topic and udp_topic:
        filter_list(
            "MQTT→UDP", load_mqtt2udp_config, save_mqtt2udp_config,
            lambda x: _object_clean_text(x.get("source_topic")) == mqtt_topic and _object_clean_text(x.get("udp_topic")) == udp_topic and _object_clean_text(x.get("json_key")) == mqtt_json_key,
        )

    if mqtt_topic and knx_ga:
        filter_list(
            "MQTT→KNX", load_mqtt2knx_config, save_mqtt2knx_config,
            lambda x: _object_clean_text(x.get("source_topic")) == mqtt_topic and normalize_knx_group_address(x.get("group_address", "")) == knx_ga and _object_clean_text(x.get("json_key")) == mqtt_json_key,
        )

    if knx_ga and mqtt_topic:
        filter_list(
            "KNX→MQTT", load_knx2mqtt_config, save_knx2mqtt_config,
            lambda x: normalize_knx_group_address(x.get("group_address", "")) == knx_ga and _object_clean_text(x.get("mqtt_topic")) == mqtt_topic,
        )

    if knx_ga and loxone_topic:
        filter_list(
            "KNX→Loxone", load_knx2lox_config, save_knx2lox_config,
            lambda x: normalize_knx_group_address(x.get("group_address", "")) == knx_ga and _object_clean_text(x.get("loxone_io")) == loxone_topic,
        )

    if udp_topic and mqtt_topic:
        filter_list(
            "UDP→MQTT", load_udp2mqtt_config, save_udp2mqtt_config,
            lambda x: _object_clean_text(x.get("udp_topic")) == udp_topic and _object_clean_text(x.get("mqtt_topic")) == mqtt_topic,
        )

    if udp_topic and knx_ga:
        filter_list(
            "UDP→KNX", load_udp2knx_config, save_udp2knx_config,
            lambda x: _object_clean_text(x.get("source_topic")) == udp_topic and normalize_knx_group_address(x.get("group_address", "")) == knx_ga,
        )

    # Influx activations in topic_config cleanup. We only remove the exact json-key
    # activation or matching influx alias; unrelated topic settings stay alive.
    try:
        cfg = load_topic_config()
        changed = False

        def cleanup_influx_entry(key, json_key=""):
            nonlocal changed
            entry = cfg.get(key)
            if not isinstance(entry, dict):
                return
            if json_key:
                keys = entry.get("influx_json_keys", [])
                if isinstance(keys, list) and json_key in keys:
                    entry["influx_json_keys"] = [k for k in keys if k != json_key]
                    changed = True
                    removed.append(f"Influx JSON-Key {key}.{json_key}")
                types = entry.get("influx_json_key_types", {})
                if isinstance(types, dict) and json_key in types:
                    types.pop(json_key, None)
                    entry["influx_json_key_types"] = types
                    changed = True
            else:
                if entry.get("influx") and (not influx_topic or _object_clean_text(entry.get("influx_topic")).strip("/") == influx_topic):
                    entry.pop("influx", None)
                    changed = True
                    removed.append(f"Influx {key}")
            if influx_topic and _object_clean_text(entry.get("influx_topic")).strip("/") == influx_topic:
                entry.pop("influx_topic", None)
                changed = True
            cfg[key] = entry

        if mqtt_topic:
            cleanup_influx_entry(mqtt_topic, mqtt_json_key)
        for raw_topic in [loxone_topic, udp_topic]:
            if raw_topic:
                cleanup_influx_entry(raw_topic, "")
        if knx_ga:
            cleanup_influx_entry(knx_influx_topic(knx_ga), "")

        if changed:
            save_topic_config(cfg)
    except Exception as e:
        warnings.append(f"Influx-Config: {e}")


    return removed, warnings


# ---------- Legacy Object-Master / Expert-Mapping-Sync ----------
def _object_new_id(prefix="obj"):
    try:
        import time as _time
        return f"{prefix}_{int(_time.time()*1000)}"
    except Exception:
        return f"{prefix}_{len(load_objects_config())+1}"


def _object_mapping_label(item, fallback="Objekt"):
    """Build a friendly object name from mapping metadata."""
    alias = _object_clean_text(item.get("mapping_alias"))
    set_name = _object_clean_text(item.get("set_name"))
    group = _object_clean_text(item.get("group"))
    if alias:
        return alias
    if set_name:
        return set_name
    if group:
        return group
    return fallback


def _object_match_score(obj, cand):
    """Score how well an existing object matches a candidate made from a mapping.

    Important: MQTT JSON keys are part of the identity. One Zigbee JSON topic may
    contain temperature, humidity, contact, battery ... and those are different
    objects even if the MQTT base topic is identical.
    """
    score = 0
    mqtt = _object_clean_text(cand.get("mqtt_topic"))
    json_key = _object_clean_text(cand.get("mqtt_json_key"))
    if mqtt and _object_clean_text(obj.get("mqtt_topic")) == mqtt:
        obj_key = _object_clean_text(obj.get("mqtt_json_key"))
        if json_key or obj_key:
            if obj_key == json_key:
                score += 80
            else:
                score -= 100
        else:
            score += 40
    knx = normalize_knx_group_address(cand.get("knx_ga", "")) if cand.get("knx_ga") else ""
    if knx and normalize_knx_group_address(obj.get("knx_ga", "")) == knx:
        score += 70
    lox = _object_clean_text(cand.get("loxone_topic"))
    if lox and _object_clean_text(obj.get("loxone_topic")) == lox:
        score += 45
    udp = _object_clean_text(cand.get("udp_topic"))
    if udp and _object_clean_text(obj.get("udp_topic")) == udp:
        score += 35
    influx = _object_clean_text(cand.get("influx_topic")).strip("/")
    if influx and _object_clean_text(obj.get("influx_topic")).strip("/") == influx:
        score += 25
    return score


def _object_merge_candidate(objects, cand):
    cand = dict(cand or {})
    if cand.get("knx_ga"):
        cand["knx_ga"] = normalize_knx_group_address(cand.get("knx_ga"))
    cand["influx_topic"] = _object_clean_text(cand.get("influx_topic")).strip("/")

    best_i = None
    best_score = 0
    for i, obj in enumerate(objects):
        score = _object_match_score(obj, cand)
        if score > best_score:
            best_i = i
            best_score = score

    if best_i is None or best_score <= 0:
        new_obj = {
            "id": _object_new_id("obj"),
            "enabled": True,
            "name": _object_clean_text(cand.get("name")) or _object_guess_name(cand.get("influx_topic") or cand.get("mqtt_json_key") or cand.get("mqtt_topic") or cand.get("loxone_topic") or cand.get("knx_ga") or cand.get("udp_topic")),
            "room": _object_clean_text(cand.get("room")),
            "type": _object_clean_text(cand.get("type")),
            "mqtt_topic": _object_clean_text(cand.get("mqtt_topic")),
            "mqtt_json_key": _object_clean_text(cand.get("mqtt_json_key")),
            "loxone_topic": _object_clean_text(cand.get("loxone_topic")),
            "knx_ga": normalize_knx_group_address(cand.get("knx_ga", "")) if cand.get("knx_ga") else "",
            "udp_topic": _object_clean_text(cand.get("udp_topic")),
            "influx_topic": _object_clean_text(cand.get("influx_topic")).strip("/"),
            "notes": "aus Expertenmapping übernommen",
        }
        objects.append(new_obj)
        return True

    obj = dict(objects[best_i])
    changed = False
    for key in ["mqtt_topic", "mqtt_json_key", "loxone_topic", "udp_topic", "influx_topic", "room", "type"]:
        val = _object_clean_text(cand.get(key))
        if key == "influx_topic":
            val = val.strip("/")
        if val and not _object_clean_text(obj.get(key)):
            obj[key] = val
            changed = True
    knx = normalize_knx_group_address(cand.get("knx_ga", "")) if cand.get("knx_ga") else ""
    if knx and not normalize_knx_group_address(obj.get("knx_ga", "")):
        obj["knx_ga"] = knx
        changed = True
    if _object_clean_text(cand.get("name")) and (not _object_clean_text(obj.get("name")) or obj.get("name", "").startswith("Mapping")):
        obj["name"] = _object_clean_text(cand.get("name"))
        changed = True
    if changed:
        objects[best_i] = obj
    return changed


def sync_objects_from_expert_mappings():
    """Make expert mappings visible in the object manager.

    This is the bridge between old expert pages and the new object-master idea:
    if Stephan creates a technical mapping somewhere, the matching object is
    created/updated automatically. It does not delete anything.
    """
    objects = load_objects_config()
    before = json.dumps(objects, sort_keys=True, ensure_ascii=False)

    def meta(item, fallback):
        return {
            "name": _object_mapping_label(item, fallback),
            "room": _object_clean_text(item.get("group")),
            "type": _object_clean_text(item.get("set_name")),
        }

    try:
        for m in load_mqtt2lox_config():
            if not isinstance(m, dict):
                continue
            cand = meta(m, "MQTT Loxone")
            cand.update({"mqtt_topic": m.get("source_topic"), "mqtt_json_key": m.get("json_key"), "loxone_topic": m.get("loxone_io")})
            _object_merge_candidate(objects, cand)
    except Exception as e:
        add_log_entry(f"Objekt-Sync MQTT→Loxone Fehler: {e}")

    try:
        for m in load_mqtt2udp_config():
            if not isinstance(m, dict):
                continue
            cand = meta(m, "MQTT UDP")
            cand.update({"mqtt_topic": m.get("source_topic"), "mqtt_json_key": m.get("json_key"), "udp_topic": m.get("udp_topic")})
            _object_merge_candidate(objects, cand)
    except Exception as e:
        add_log_entry(f"Objekt-Sync MQTT→UDP Fehler: {e}")

    try:
        for m in load_mqtt2knx_config():
            if not isinstance(m, dict):
                continue
            cand = meta(m, "MQTT KNX")
            cand.update({"mqtt_topic": m.get("source_topic"), "mqtt_json_key": m.get("json_key"), "knx_ga": m.get("group_address")})
            _object_merge_candidate(objects, cand)
    except Exception as e:
        add_log_entry(f"Objekt-Sync MQTT→KNX Fehler: {e}")

    try:
        for m in load_knx2mqtt_config():
            if not isinstance(m, dict):
                continue
            cand = meta(m, "KNX MQTT")
            cand.update({"knx_ga": m.get("group_address"), "mqtt_topic": m.get("mqtt_topic")})
            _object_merge_candidate(objects, cand)
    except Exception as e:
        add_log_entry(f"Objekt-Sync KNX→MQTT Fehler: {e}")

    try:
        for m in load_knx2lox_config():
            if not isinstance(m, dict):
                continue
            cand = meta(m, "KNX Loxone")
            cand.update({"knx_ga": m.get("group_address"), "loxone_topic": m.get("loxone_io")})
            _object_merge_candidate(objects, cand)
    except Exception as e:
        add_log_entry(f"Objekt-Sync KNX→Loxone Fehler: {e}")

    try:
        for m in load_udp2mqtt_config():
            if not isinstance(m, dict):
                continue
            cand = meta(m, "UDP MQTT")
            cand.update({"udp_topic": m.get("udp_topic"), "mqtt_topic": m.get("mqtt_topic")})
            _object_merge_candidate(objects, cand)
    except Exception as e:
        add_log_entry(f"Objekt-Sync UDP→MQTT Fehler: {e}")

    try:
        for m in load_udp2knx_config():
            if not isinstance(m, dict):
                continue
            cand = meta(m, "UDP KNX")
            cand.update({"udp_topic": m.get("source_topic"), "knx_ga": m.get("group_address")})
            _object_merge_candidate(objects, cand)
    except Exception as e:
        add_log_entry(f"Objekt-Sync UDP→KNX Fehler: {e}")

    # Influx settings from topic_config are also treated as object links.
    try:
        cfg = load_topic_config()
        if isinstance(cfg, dict):
            for topic, item in cfg.items():
                if not isinstance(item, dict):
                    continue
                influx_topic = _object_clean_text(item.get("influx_topic")).strip("/")
                if item.get("influx_json_keys") and isinstance(item.get("influx_json_keys"), list):
                    for key in item.get("influx_json_keys", []):
                        cand = {"mqtt_topic": topic, "mqtt_json_key": key, "influx_topic": influx_topic or topic, "name": _object_guess_name(str(key))}
                        _object_merge_candidate(objects, cand)
                elif item.get("influx"):
                    cand = {"mqtt_topic": topic if not str(topic).startswith("knx/") else "", "knx_ga": str(topic)[4:] if str(topic).startswith("knx/") else "", "influx_topic": influx_topic or topic, "name": _object_guess_name(influx_topic or topic)}
                    _object_merge_candidate(objects, cand)
    except Exception as e:
        add_log_entry(f"Objekt-Sync Influx Fehler: {e}")

    after = json.dumps(objects, sort_keys=True, ensure_ascii=False)
    if after != before:
        save_objects_config(objects)
        add_log_entry("Objekt-Sync: Expertenmapping in Objekte übernommen")
        return True
    return False


def purge_all_technical_mappings(clear_influx_flags=True):
    """Empty all technical mapping tables. Objects stay alive."""
    removed = []
    specs = [
        ("MQTT→Loxone", load_mqtt2lox_config, save_mqtt2lox_config),
        ("MQTT→UDP", load_mqtt2udp_config, save_mqtt2udp_config),
        ("MQTT→KNX", load_mqtt2knx_config, save_mqtt2knx_config),
        ("KNX→MQTT", load_knx2mqtt_config, save_knx2mqtt_config),
        ("KNX→Loxone", load_knx2lox_config, save_knx2lox_config),
        ("UDP→MQTT", load_udp2mqtt_config, save_udp2mqtt_config),
        ("UDP→KNX", load_udp2knx_config, save_udp2knx_config),
    ]
    for label, loader, saver in specs:
        try:
            count = len(loader())
            saver([])
            if count:
                removed.append(f"{label} ({count})")
        except Exception as e:
            removed.append(f"{label} Fehler: {e}")
    if clear_influx_flags:
        try:
            cfg = load_topic_config()
            if isinstance(cfg, dict):
                for key, item in list(cfg.items()):
                    if not isinstance(item, dict):
                        continue
                    for k in ["influx", "influx_topic", "influx_json_keys", "influx_json_key_types", "influx_value_type"]:
                        item.pop(k, None)
                    cfg[key] = item
                save_topic_config(cfg)
                removed.append("Influx-Markierungen bereinigt")
        except Exception as e:
            removed.append(f"Influx-Bereinigung Fehler: {e}")
    return removed


def rebuild_technical_mappings_from_objects(clear_first=True):
    """Clean rebuild: objects are the master, technical mappings are generated."""
    removed = purge_all_technical_mappings(clear_influx_flags=True) if clear_first else []
    created = []
    warnings = []
    for obj in load_objects_config():
        if not obj.get("enabled", True):
            continue
        c, w = ensure_object_mappings(obj)
        created.extend(c)
        warnings.extend(w)
    unique_created = []
    for x in created:
        if x not in unique_created:
            unique_created.append(x)
    return removed, unique_created, warnings
