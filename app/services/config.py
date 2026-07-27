import json
import os
import re
import threading
from pathlib import Path

from engine import port


APP_ROOT = str(port.APP_ROOT)
CONFIG_DIR = str(port.CONFIG_DIR)
DATA_DIR = str(port.DATA_DIR)
BACKUP_DIR = str(port.BACKUP_DIR)

for _dir in (DATA_DIR, CONFIG_DIR, BACKUP_DIR):
    os.makedirs(_dir, exist_ok=True)

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
TOPIC_CONFIG_FILE = os.path.join(CONFIG_DIR, "topic_config.json")
MQTT2LOX_FILE = os.path.join(CONFIG_DIR, "mqtt2lox.json")
MQTT2UDP_FILE = os.path.join(CONFIG_DIR, "mqtt2udp_config.json")
UDP2MQTT_FILE = os.path.join(CONFIG_DIR, "udp2mqtt.json")
UDP_PRESETS_FILE = os.path.join(CONFIG_DIR, "udp_presets.json")
MQTT_BROKERS_FILE = os.path.join(CONFIG_DIR, "mqtt_brokers.json")
MONITOR_SETTINGS_FILE = os.path.join(CONFIG_DIR, "monitor_settings.json")
PLUGIN_CONFIG_FILE = os.path.join(CONFIG_DIR, "plugins.json")
KNX_CONFIG_FILE = os.path.join(CONFIG_DIR, "knx_config.json")
MQTT2KNX_FILE = os.path.join(CONFIG_DIR, "mqtt2knx.json")
KNX2MQTT_FILE = os.path.join(CONFIG_DIR, "knx2mqtt.json")
UDP2KNX_FILE = os.path.join(CONFIG_DIR, "udp2knx.json")
KNX2LOX_FILE = os.path.join(CONFIG_DIR, "knx2lox.json")
SIDEBAR_LINKS_FILE = os.path.join(CONFIG_DIR, "sidebar_links.json")
INTERNAL_BROKER_FILE = os.path.join(CONFIG_DIR, "internal_broker.json")
OBJECTS_FILE = os.path.join(CONFIG_DIR, "objects.json")

CONFIG_FILES = [
    "config.json",
    "mqtt_brokers.json",
    "monitor_settings.json",
    "plugins.json",
    "knx_config.json",
    "sidebar_links.json",
    "internal_broker.json",
    "objects.json",
]

_json_file_lock = threading.RLock()
_log_handler = None


DEFAULT_CONFIG = {
    "loxone": {"host": "", "user": "admin", "password": ""},
    "mqtt": {"host": "127.0.0.1", "port": 1883, "user": "", "password": "", "prefix": "loxone"},
    "udp_input": {
        "enabled": True,
        "port": 7002,
        "prefix": "",
        "retain": False,
        "legacy_fallback": False,
    },
    "influx": {
        "enabled": False,
        "version": "2",
        "host": "127.0.0.1",
        "port": 8086,
        "database": "",
        "bucket": "loxone",
        "org": "home",
        "token": "",
        "user": "",
        "password": "",
        "measurement": "loxone",
    },
    "bridge": {"pulse_time": 0.5, "round_digits": 4, "retain": True, "change_only": True},
}

DEFAULT_PLUGINS = [
    {"id": "mqtt", "name": "MQTT", "enabled": True, "status": "aktiv", "description": "Hauptbroker und zusaetzliche Broker", "route": "/mqtt_settings_embed"},
    {"id": "loxone", "name": "Loxone", "enabled": True, "status": "aktiv", "description": "Loxone Websocket, HTTP und Mapping", "route": "/settings_embed"},
    {"id": "udp", "name": "UDP", "enabled": True, "status": "aktiv", "description": "MQTT -> UDP und UDP -> MQTT", "route": "/mqtt2udp"},
    {"id": "influx", "name": "InfluxDB", "enabled": True, "status": "aktiv", "description": "Zeitreihen-Ausgabe", "route": "/influx_settings_embed"},
    {"id": "zigbee", "name": "Zigbee", "enabled": False, "status": "vorbereitet", "description": "Reserviert fuer Zigbee2MQTT Links und Mapping", "route": ""},
    {"id": "knx", "name": "KNX", "enabled": False, "status": "Foundation", "description": "KNX Gateway, MQTT -> KNX und KNX -> MQTT", "route": "/mqtt2knx"},
]

DEFAULT_INTERNAL_BROKER_CONFIG = {
    "enabled": False,
    "use_as_main": False,
    "host": "0.0.0.0",
    "connect_host": "127.0.0.1",
    "port": 1883,
    "allow_anonymous": True,
    "user": "",
    "password": "",
    "persistence": True,
    "mosquitto_path": "mosquitto",
}

DEFAULT_KNX_CONFIG = {
    "enabled": False,
    "gateway_ip": "",
    "gateway_port": 3671,
    "connection_type": "tunneling",
    "local_ip": "",
    "physical_address": "1.1.250",
}


def set_log_handler(handler):
    global _log_handler
    _log_handler = handler


def _log(message):
    if _log_handler:
        try:
            _log_handler(message)
            return
        except Exception:
            pass
    print(message)


def safe_load_json_file(path, default_value):
    with _json_file_lock:
        try:
            if not os.path.exists(path):
                return default_value
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read().strip()
            if not raw:
                return default_value
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            _log(f"JSON Lesefehler {os.path.basename(path)}: {exc}")
            return default_value
        except Exception as exc:
            _log(f"JSON Lesefehler {os.path.basename(path)}: {exc}")
            return default_value


def safe_save_json_file(path, data, indent=2):
    with _json_file_lock:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)


def merge_defaults(config, defaults):
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
        elif isinstance(value, dict) and isinstance(config.get(key), dict):
            merge_defaults(config[key], value)
    return config


def load_config():
    config = safe_load_json_file(CONFIG_FILE, dict(DEFAULT_CONFIG))
    if not isinstance(config, dict):
        config = dict(DEFAULT_CONFIG)
    config = merge_defaults(config, DEFAULT_CONFIG)
    if not os.path.exists(CONFIG_FILE):
        save_config(config)
    return config


def save_config(config):
    safe_save_json_file(CONFIG_FILE, config, indent=2)


def load_topic_config():
    data = safe_load_json_file(TOPIC_CONFIG_FILE, {})
    if not isinstance(data, dict):
        data = {}
    if not os.path.exists(TOPIC_CONFIG_FILE):
        save_topic_config(data)
    return data


def save_topic_config(data):
    safe_save_json_file(TOPIC_CONFIG_FILE, data if isinstance(data, dict) else {}, indent=2)


def load_mqtt2lox_config():
    data = safe_load_json_file(MQTT2LOX_FILE, [])
    if not isinstance(data, list):
        data = []
    for m in data:
        if isinstance(m, dict):
            m.setdefault("payload_mode", "raw")
            m.setdefault("json_key", "")
            m.setdefault("output_mode", "single")
            m.setdefault("group", "")
            m.setdefault("set_name", "")
            m.setdefault("mapping_alias", "")
    if not os.path.exists(MQTT2LOX_FILE):
        save_mqtt2lox_config(data)
    return data


def save_mqtt2lox_config(data):
    safe_save_json_file(MQTT2LOX_FILE, data if isinstance(data, list) else [], indent=2)


def load_mqtt2udp_config():
    data = safe_load_json_file(MQTT2UDP_FILE, [])
    if not isinstance(data, list):
        data = []
    for m in data:
        if isinstance(m, dict):
            m.setdefault("enabled", True)
            m.setdefault("group", "")
            m.setdefault("set_name", "")
            m.setdefault("mapping_alias", "")
            m.setdefault("source_topic", "")
            m.setdefault("udp_topic", "")
            m.setdefault("udp_ip", "")
            m.setdefault("udp_port", "7000")
            m.setdefault("udp_format", "topic_value")
            m.setdefault("payload_mode", "raw")
            m.setdefault("json_key", "")
            m.setdefault("test_value", "123")
    if not os.path.exists(MQTT2UDP_FILE):
        save_mqtt2udp_config(data)
    return data


def save_mqtt2udp_config(data):
    safe_save_json_file(MQTT2UDP_FILE, data if isinstance(data, list) else [], indent=2)


def load_udp2mqtt_config():
    data = safe_load_json_file(UDP2MQTT_FILE, [])
    if not isinstance(data, list):
        data = []
    for m in data:
        if isinstance(m, dict):
            m.setdefault("enabled", True)
            m.setdefault("udp_topic", "")
            m.setdefault("mqtt_topic", "")
            m.setdefault("retain", False)
            m.setdefault("test_value", "123")
            m.setdefault("group", "")
            m.setdefault("set_name", "")
            m.setdefault("mapping_alias", "")
    if not os.path.exists(UDP2MQTT_FILE):
        save_udp2mqtt_config(data)
    return data


def save_udp2mqtt_config(data):
    safe_save_json_file(UDP2MQTT_FILE, data if isinstance(data, list) else [], indent=2)


def load_mqtt_brokers():
    data = safe_load_json_file(MQTT_BROKERS_FILE, [])
    if not isinstance(data, list):
        data = []
    if not os.path.exists(MQTT_BROKERS_FILE):
        save_mqtt_brokers(data)
    return data


def save_mqtt_brokers(data):
    safe_save_json_file(MQTT_BROKERS_FILE, data if isinstance(data, list) else [], indent=2)


def load_monitor_settings():
    data = safe_load_json_file(MONITOR_SETTINGS_FILE, {"favorites": [], "aliases": {}})
    if not isinstance(data, dict):
        data = {"favorites": [], "aliases": {}}
    data.setdefault("favorites", [])
    data.setdefault("aliases", {})
    if not os.path.exists(MONITOR_SETTINGS_FILE):
        save_monitor_settings(data)
    return data


def save_monitor_settings(data):
    safe_save_json_file(MONITOR_SETTINGS_FILE, data if isinstance(data, dict) else {"favorites": [], "aliases": {}}, indent=4)


def load_plugins_config():
    data = safe_load_json_file(PLUGIN_CONFIG_FILE, [])
    if not isinstance(data, list):
        data = []
    known = {item.get("id"): item for item in data if isinstance(item, dict)}
    merged = []
    for default in DEFAULT_PLUGINS:
        item = dict(default)
        item.update(known.get(default["id"], {}))
        merged.append(item)
    if not os.path.exists(PLUGIN_CONFIG_FILE) or merged != data:
        save_plugins_config(merged)
    return merged


def save_plugins_config(data):
    safe_save_json_file(PLUGIN_CONFIG_FILE, data if isinstance(data, list) else [], indent=2)


def load_sidebar_links():
    data = safe_load_json_file(SIDEBAR_LINKS_FILE, [])
    if not isinstance(data, list):
        data = []
    cleaned = []
    for item in data:
        if not isinstance(item, dict):
            continue
        enabled = item.get("active", item.get("enabled", True))
        label = item.get("name", item.get("label", ""))
        cleaned.append({
            "enabled": bool(enabled),
            "active": bool(enabled),
            "label": str(label).strip(),
            "name": str(label).strip(),
            "url": str(item.get("url", "")).strip(),
            "new_tab": bool(item.get("new_tab", True)),
        })
    if not os.path.exists(SIDEBAR_LINKS_FILE) or cleaned != data:
        save_sidebar_links(cleaned)
    return cleaned


def save_sidebar_links(data):
    safe_save_json_file(SIDEBAR_LINKS_FILE, data if isinstance(data, list) else [], indent=2)


def normalize_knx_group_address(value):
    text = str(value or "").strip().replace(" ", "")
    if not text:
        return ""
    if "/" in text:
        parts = [p for p in text.split("/") if p != ""]
        if len(parts) >= 3:
            return f"{parts[0]}/{parts[1]}/{parts[2]}"
        if len(parts) == 2:
            a, b = parts[0], parts[1]
            b_digits = re.sub(r"\D", "", b)
            if len(b_digits) >= 2:
                return f"{a}/{b_digits[0]}/{b_digits[1:]}"
            return f"{a}/{b}"
        if len(parts) == 1:
            return normalize_knx_group_address(parts[0])
        return ""
    digits = re.sub(r"\D", "", text)
    if not digits:
        return text
    if len(digits) == 1:
        return digits
    if len(digits) == 2:
        return f"{digits[0]}/{digits[1]}"
    return f"{digits[0]}/{digits[1]}/{digits[2:]}"


def load_objects_config():
    data = safe_load_json_file(OBJECTS_FILE, [])
    if isinstance(data, dict) and isinstance(data.get("objects"), list):
        data = data.get("objects", [])
    if not isinstance(data, list):
        data = []
    cleaned = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        mqtt_cfg = item.get("mqtt") if isinstance(item.get("mqtt"), dict) else {}
        loxone_cfg = item.get("loxone") if isinstance(item.get("loxone"), dict) else {}
        knx_cfg = item.get("knx") if isinstance(item.get("knx"), dict) else {}
        udp_cfg = item.get("udp") if isinstance(item.get("udp"), dict) else {}
        influx_cfg = item.get("influx") if isinstance(item.get("influx"), dict) else {}
        cleaned.append({
            "id": str(item.get("id") or f"obj_{idx + 1}"),
            "enabled": bool(item.get("enabled", True)),
            "name": str(item.get("name", "") or "").strip(),
            "room": str(item.get("room", "") or "").strip(),
            "type": str(item.get("type") or item.get("datatype", "") or "").strip(),
            "mqtt_topic": str(item.get("mqtt_topic") or mqtt_cfg.get("topic", "") or "").strip(),
            "mqtt_json_key": str(item.get("mqtt_json_key", "") or "").strip(),
            "loxone_topic": str(item.get("loxone_topic") or loxone_cfg.get("uuid", "") or "").strip(),
            "knx_ga": normalize_knx_group_address(item.get("knx_ga") or knx_cfg.get("group_address", "")),
            "udp_topic": str(item.get("udp_topic") or udp_cfg.get("template", "") or "").strip(),
            "influx_topic": str(item.get("influx_topic") or influx_cfg.get("measurement", "") or "").strip(),
            "notes": str(item.get("notes", "") or "").strip(),
        })
    if not os.path.exists(OBJECTS_FILE):
        save_objects_config(cleaned)
    return cleaned


def save_objects_config(data):
    current = safe_load_json_file(OBJECTS_FILE, [])
    payload = data if isinstance(data, list) else []
    if isinstance(current, dict) and "objects" in current:
        current["objects"] = payload
        safe_save_json_file(OBJECTS_FILE, current, indent=2)
    else:
        safe_save_json_file(OBJECTS_FILE, payload, indent=2)


def load_internal_broker_config():
    data = safe_load_json_file(INTERNAL_BROKER_FILE, {})
    if not isinstance(data, dict):
        data = {}
    cfg = dict(DEFAULT_INTERNAL_BROKER_CONFIG)
    cfg.update(data)
    try:
        cfg["port"] = int(cfg.get("port", 1883))
    except Exception:
        cfg["port"] = 1883
    if not os.path.exists(INTERNAL_BROKER_FILE):
        save_internal_broker_config(cfg)
    return cfg


def save_internal_broker_config(data):
    cfg = dict(DEFAULT_INTERNAL_BROKER_CONFIG)
    if isinstance(data, dict):
        cfg.update(data)
    try:
        cfg["port"] = int(cfg.get("port", 1883))
    except Exception:
        cfg["port"] = 1883
    safe_save_json_file(INTERNAL_BROKER_FILE, cfg, indent=2)


def load_knx_config():
    data = safe_load_json_file(KNX_CONFIG_FILE, None)
    if not isinstance(data, dict):
        cfg = dict(DEFAULT_KNX_CONFIG)
        if not os.path.exists(KNX_CONFIG_FILE):
            save_knx_config(cfg)
        return cfg
    cfg = dict(DEFAULT_KNX_CONFIG)
    cfg.update(data)
    try:
        cfg["gateway_port"] = int(cfg.get("gateway_port", 3671))
    except Exception:
        cfg["gateway_port"] = 3671
    return cfg


def save_knx_config(data):
    cfg = dict(DEFAULT_KNX_CONFIG)
    if isinstance(data, dict):
        cfg.update(data)
    cfg["enabled"] = bool(cfg.get("enabled", False))
    cfg["gateway_ip"] = str(cfg.get("gateway_ip", DEFAULT_KNX_CONFIG["gateway_ip"]) or "").strip() or DEFAULT_KNX_CONFIG["gateway_ip"]
    try:
        cfg["gateway_port"] = int(cfg.get("gateway_port", 3671))
    except Exception:
        cfg["gateway_port"] = 3671
    cfg["connection_type"] = str(cfg.get("connection_type", "tunneling") or "tunneling").strip()
    if cfg["connection_type"] not in ["tunneling", "routing"]:
        cfg["connection_type"] = "tunneling"
    cfg["local_ip"] = str(cfg.get("local_ip", "") or "").strip()
    cfg["physical_address"] = str(cfg.get("physical_address", "1.1.250") or "1.1.250").strip()
    safe_save_json_file(KNX_CONFIG_FILE, cfg, indent=2)


def load_mqtt2knx_config():
    data = safe_load_json_file(MQTT2KNX_FILE, [])
    if not isinstance(data, list):
        data = []
    for m in data:
        if isinstance(m, dict):
            m.setdefault("enabled", True)
            m.setdefault("source_topic", "")
            m.setdefault("payload_mode", "raw")
            m.setdefault("json_key", "")
            m.setdefault("group_address", "")
            m.setdefault("dpt", "1.001")
            m.setdefault("invert", False)
            m.setdefault("test_value", "1")
    if not os.path.exists(MQTT2KNX_FILE):
        save_mqtt2knx_config(data)
    return data


def save_mqtt2knx_config(data):
    safe_save_json_file(MQTT2KNX_FILE, data if isinstance(data, list) else [], indent=2)


def load_knx2mqtt_config():
    data = safe_load_json_file(KNX2MQTT_FILE, [])
    if not isinstance(data, list):
        data = []
    for m in data:
        if isinstance(m, dict):
            m.setdefault("enabled", True)
            m.setdefault("group_address", "")
            m.setdefault("mqtt_topic", "")
            m.setdefault("dpt", "1.001")
            m.setdefault("retain", True)
            m.setdefault("invert", False)
    if not os.path.exists(KNX2MQTT_FILE):
        save_knx2mqtt_config(data)
    return data


def save_knx2mqtt_config(data):
    safe_save_json_file(KNX2MQTT_FILE, data if isinstance(data, list) else [], indent=2)


def load_udp2knx_config():
    data = safe_load_json_file(UDP2KNX_FILE, [])
    if not isinstance(data, list):
        data = []
    for m in data:
        if isinstance(m, dict):
            m.setdefault("enabled", True)
            m.setdefault("source_topic", "")
            m.setdefault("group_address", "")
            m.setdefault("dpt", "1.001")
            m.setdefault("invert", False)
            m.setdefault("test_value", "1")
    if not os.path.exists(UDP2KNX_FILE):
        save_udp2knx_config(data)
    return data


def save_udp2knx_config(data):
    safe_save_json_file(UDP2KNX_FILE, data if isinstance(data, list) else [], indent=2)


def load_knx2lox_config():
    data = safe_load_json_file(KNX2LOX_FILE, [])
    if not isinstance(data, list):
        data = []
    for m in data:
        if isinstance(m, dict):
            m.setdefault("enabled", True)
            m.setdefault("group_address", "")
            m.setdefault("loxone_io", "")
            m.setdefault("dpt", "1.001")
            m.setdefault("invert", False)
    if not os.path.exists(KNX2LOX_FILE):
        save_knx2lox_config(data)
    return data


def save_knx2lox_config(data):
    safe_save_json_file(KNX2LOX_FILE, data if isinstance(data, list) else [], indent=2)


def port_info():
    return {
        "version": port.APP_VERSION,
        "config_dir": CONFIG_DIR,
        "data_dir": DATA_DIR,
        "backup_dir": BACKUP_DIR,
        "config_files": [str(Path(CONFIG_DIR) / name) for name in CONFIG_FILES],
        "loxwebsocket_available": port.LOXWEBSOCKET_AVAILABLE,
        "loxone_status": port.LOXWEBSOCKET_STATUS,
    }
