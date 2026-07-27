import json
import json
import os
import socket
import threading
from datetime import datetime

from services import config


mqtt2udp_last_seen = {}
udp2mqtt_last_seen = {}
udp_input_last_seen = {}
_UDP_STOP_EVENT = threading.Event()

DEFAULT_UDP_PRESETS = [
    {"port": "7000", "label": "Loxone UDP 7000"},
    {"port": "7001", "label": "Loxone UDP 7001"},
    {"port": "7010", "label": "Loxone Test 7010"},
]


def _log(add_log_entry, message):
    if add_log_entry:
        add_log_entry(message)


def request_udp_stop():
    _UDP_STOP_EVENT.set()


def reset_udp_stop():
    _UDP_STOP_EVENT.clear()


def is_udp_stop_requested():
    return _UDP_STOP_EVENT.is_set()


def parse_udp_input_details(text):
    text = str(text or "").strip()
    details = {
        "raw": text,
        "mode": "Wert",
        "topic": "",
        "value": None,
        "json_key": "",
        "json_data": None,
    }

    if not text:
        return details

    def _parse_json_candidate(raw_text, _depth=0):
        raw_text = str(raw_text or "").strip()
        if not raw_text:
            return None

        # 1) Direktes JSON
        try:
            parsed = json.loads(raw_text)
            # Doppelt kodiertes JSON: "{\"a\":1}"
            if isinstance(parsed, str) and _depth < 2:
                nested = _parse_json_candidate(parsed, _depth + 1)
                if isinstance(nested, (dict, list)):
                    return nested
            if isinstance(parsed, (dict, list)):
                return parsed
        except Exception:
            pass

        # 2) JSON aus Text extrahieren: "UDP: { ... }"
        first_candidates = [idx for idx in (raw_text.find("{"), raw_text.find("[")) if idx >= 0]
        if not first_candidates:
            return None
        first_start = min(first_candidates)
        last_end = max(raw_text.rfind("}"), raw_text.rfind("]"))
        if last_end <= first_start:
            return None
        candidate = raw_text[first_start:last_end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, str) and _depth < 2:
                nested = _parse_json_candidate(parsed, _depth + 1)
                if isinstance(nested, (dict, list)):
                    return nested
            if isinstance(parsed, (dict, list)):
                return parsed
        except Exception:
            return None
        return None

    # JSON IMMER zuerst prüfen. Ein JSON ohne topic/value ist trotzdem gültig.
    parsed = _parse_json_candidate(text)
    if isinstance(parsed, (dict, list)):
        topic = ""
        value = None
        json_key = ""
        if isinstance(parsed, dict):
            topic = str(
                parsed.get("topic")
                or parsed.get("udp_topic")
                or parsed.get("source_topic")
                or parsed.get("name")
                or ""
            ).strip()
            if not topic and isinstance(parsed.get("source"), dict):
                source_block = parsed.get("source") or {}
                topic = str(
                    source_block.get("topic")
                    or source_block.get("udp_topic")
                    or source_block.get("name")
                    or ""
                ).strip()
            value = parsed.get("value")
            if value is None:
                value = parsed.get("payload")
            if value is None:
                value = parsed.get("data")
            if value is None:
                value = parsed.get("val")
            if value is None:
                value = parsed.get("message")
            json_key = str(parsed.get("json_key") or parsed.get("key") or parsed.get("path") or "").strip()

        details.update({
            "mode": "JSON",
            "topic": topic,
            "value": value if value is not None else "JSON",
            "json_key": json_key,
            "json_data": parsed,
        })
        return details

    if ":" in text:
        topic, value = text.split(":", 1)
        details["mode"] = "Topic:Wert"
    elif "=" in text:
        topic, value = text.split("=", 1)
        details["mode"] = "Topic:Wert"
    else:
        details["value"] = text
        return details

    details["topic"] = str(topic).strip()
    details["value"] = str(value).strip()
    return details

def parse_udp_input_message(text):
    details = parse_udp_input_details(text)
    topic = str(details.get("topic") or "").strip()
    if not topic:
        return None, None
    return topic, details.get("value")


def build_udp_message(udp_topic, value, udp_format):
    udp_format = str(udp_format or "topic_value").strip()
    udp_topic = str(udp_topic or "").strip()

    if udp_format == "json":
        return json.dumps({"topic": udp_topic, "value": value}, ensure_ascii=False)

    if udp_format == "json_number":
        try:
            parsed_value = float(value)
        except Exception:
            parsed_value = value
        return json.dumps({"topic": udp_topic, "value": parsed_value}, ensure_ascii=False)

    if udp_format == "value_only":
        return str(value)

    if not udp_topic:
        return str(value)

    return f"{udp_topic}:{value}"


def send_mqtt2udp(
    ip_list,
    port,
    udp_topic,
    value,
    udp_format="topic_value",
    add_log_entry=None,
    object_id="",
    source="mqtt",
):
    try:
        port = int(port)
        message = build_udp_message(udp_topic, value, udp_format)
        _log(
            add_log_entry,
            f"UDP Senden Start host={str(ip_list or '').strip()} port={port} udp_topic={str(udp_topic or '').strip()} payload={message}",
        )
        targets = []
        seen_targets = set()
        for raw_ip in str(ip_list).split(","):
            ip = raw_ip.strip()
            if not ip or ip in seen_targets:
                continue
            seen_targets.add(ip)
            targets.append(ip)

        if not targets:
            _log(add_log_entry, "MQTT2UDP Fehler: keine Ziel-IP angegeben")
            return False

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            for ip in targets:
                sock.sendto(message.encode("utf-8"), (ip, port))
                _log(
                    add_log_entry,
                    f"UDP send object_id={str(object_id or '').strip()} source={str(source or '').strip()} value={value} udp_target={str(udp_topic or '').strip()} payload={message} target_host={ip} target_port={port}",
                )
            _log(add_log_entry, f"UDP Senden OK bytes={len(message.encode('utf-8'))}")
        finally:
            sock.close()
        return True

    except Exception as exc:
        _log(add_log_entry, f"UDP Senden Fehler: {type(exc).__name__}: {exc}")
        return False


def handle_mqtt_to_udp(
    topic,
    payload,
    load_mqtt2udp_config,
    extract_mqtt_mapping_value,
    add_log_entry=None,
    send_udp_func=None,
    update_last_seen=None,
):
    mappings = load_mqtt2udp_config()
    sender = send_udp_func or (lambda ip, port, udp_topic, value, udp_format: send_mqtt2udp(
        ip,
        port,
        udp_topic,
        value,
        udp_format,
        add_log_entry,
    ))

    for item in mappings:
        if not item.get("enabled", True):
            continue

        source_topic = item.get("source_topic", "").strip()
        udp_topic = item.get("udp_topic", "").strip()
        udp_ip = item.get("udp_ip", "").strip()
        udp_port = item.get("udp_port", "7000").strip()
        udp_format = item.get("udp_format", "topic_value")

        if not source_topic:
            continue

        if topic != source_topic:
            continue

        mapped_value = extract_mqtt_mapping_value(item, payload)
        if mapped_value is None:
            _log(add_log_entry, f"MQTT2UDP kein gueltiger Wert fuer {topic}")
            return True

        mqtt2udp_last_seen[source_topic] = {
            "value": mapped_value,
            "time": datetime.now().strftime("%H:%M:%S"),
        }
        if update_last_seen:
            update_last_seen("mqtt2udp", source_topic, mqtt2udp_last_seen[source_topic])

        if udp_topic and udp_ip and udp_port:
            sender(udp_ip, udp_port, udp_topic, mapped_value, udp_format)

        return True

    return False


def handle_udp_to_mqtt(
    raw_topic,
    value,
    load_udp2mqtt_config,
    publish_func,
    add_log_entry=None,
    default_prefix="",
    default_retain=False,
    legacy_fallback=False,
    update_last_seen=None,
):
    topic = str(raw_topic or "").strip()
    if not topic:
        return False

    matched = False
    for item in load_udp2mqtt_config():
        if not item.get("enabled", True):
            continue
        udp_topic = str(item.get("udp_topic", "")).strip()
        mqtt_topic = str(item.get("mqtt_topic", "")).strip()
        if not udp_topic or not mqtt_topic or udp_topic != topic:
            continue
        matched = True
        udp2mqtt_last_seen[udp_topic] = {
            "value": value,
            "time": datetime.now().strftime("%H:%M:%S"),
            "mqtt_topic": mqtt_topic,
        }
        if update_last_seen:
            update_last_seen("udp2mqtt", udp_topic, udp2mqtt_last_seen[udp_topic])
        if publish_func:
            publish_func(mqtt_topic, value, bool(item.get("retain", False)))
            _log(add_log_entry, f"UDP2MQTT Mapping -> {udp_topic} => {mqtt_topic} = {value}")
        else:
            _log(add_log_entry, "UDP2MQTT Fehler: MQTT Client nicht bereit")

    if matched:
        return True

    if not legacy_fallback:
        _log(add_log_entry, f"UDP2MQTT kein Mapping fuer {topic} - Legacy aus")
        return False

    final_topic = f"{default_prefix}/{topic}" if default_prefix else topic
    udp2mqtt_last_seen[topic] = {
        "value": value,
        "time": datetime.now().strftime("%H:%M:%S"),
        "mqtt_topic": final_topic,
        "legacy": True,
    }
    if update_last_seen:
        update_last_seen("udp2mqtt", topic, udp2mqtt_last_seen[topic])
    if publish_func:
        publish_func(final_topic, value, bool(default_retain))
        _log(add_log_entry, f"UDP2MQTT Legacy -> {final_topic} = {value}")
        return True
    _log(add_log_entry, "UDP2MQTT Legacy Fehler: MQTT Client nicht bereit")
    return False


def udp_input_listener(config, load_config, handle_udp_to_knx, handle_udp_to_mqtt_func, add_log_entry=None, update_last_seen=None, add_monitor_entry=None, listen_port=None, stop_event=None):
    _log(add_log_entry, "UDP Input Funktion wurde aufgerufen")
    sock = None
    stop_event = stop_event or _UDP_STOP_EVENT

    try:
        udp_config = config.get("udp_input", {})
        _log(add_log_entry, f"UDP Input Config: {udp_config}")

        enabled = bool(listen_port is not None or udp_config.get("enabled", False))
        port = int(listen_port if listen_port is not None else udp_config.get("port", 7002))
        prefix = udp_config.get("prefix", "").strip().strip("/")
        retain = bool(udp_config.get("retain", False))
        legacy_fallback = bool(udp_config.get("legacy_fallback", False))

        if not enabled:
            _log(add_log_entry, "UDP Input deaktiviert")
            return

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        sock.bind(("0.0.0.0", port))

        _log(add_log_entry, f"UDP Input lauscht auf Port {port}")

        while not stop_event.is_set():
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError as exc:
                if stop_event.is_set():
                    break
                raise

            text = data.decode("utf-8", errors="ignore").strip()
            _log(add_log_entry, f"UDP RX roh von {addr[0]}:{addr[1]} | {text}")
            _log(add_log_entry, "UDP RAW BYTES: " + repr(data))
            _log(add_log_entry, "UDP TEXT REPR: " + repr(text))

            udp_input_last_seen["last"] = {
                "ip": addr[0],
                "port": addr[1],
                "raw": text,
                "time": datetime.now().strftime("%H:%M:%S"),
            }
            if update_last_seen:
                update_last_seen("udp_input", "last", udp_input_last_seen["last"])

            details = parse_udp_input_details(text)
            _log(add_log_entry, "UDP DETAILS: " + repr(parse_udp_input_details(text)))
            topic, value = parse_udp_input_message(text)
            if details.get("mode") == "JSON":
                topic = str(details.get("topic") or "").strip()
                value = details.get("value")

            if not topic and details.get("mode") != "JSON":
                _log(add_log_entry, f"UDP Input ungueltig: {text}")

            if add_monitor_entry:
                try:
                    add_monitor_entry(
                        {
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "direction": "RX",
                            "sender_ip": addr[0],
                            "sender_port": addr[1],
                            "listen_port": port,
                            "payload_raw": text,
                            "mode": details.get("mode", "Wert"),
                            "topic": topic or "",
                            "key": details.get("json_key", "") or ("JSON" if details.get("mode") == "JSON" else ""),
                            "value": value,
                            "json_data": details.get("json_data"),
                        }
                    )
                except Exception as exc:
                    _log(add_log_entry, f"UDP Monitor Log Fehler: {exc}")

            _log(add_log_entry, f"UDP RX parsed topic={topic} value={value}")

            if not topic and details.get("mode") != "JSON":
                continue

            try:
                live_udp_cfg = load_config().get("udp_input", {})
                prefix = str(live_udp_cfg.get("prefix", prefix) or "").strip().strip("/")
                retain = bool(live_udp_cfg.get("retain", retain))
                legacy_fallback = bool(live_udp_cfg.get("legacy_fallback", legacy_fallback))
            except Exception as exc:
                _log(add_log_entry, f"UDP Input Live-Config Fehler: {exc}")

            handled_object_routes = bool(
                handle_udp_to_knx(
                    topic,
                    value,
                    {
                        "udp_topic": topic,
                        "payload_raw": text,
                        "json_data": details.get("json_data"),
                        "udp_source_host": addr[0],
                        "udp_source_port": addr[1],
                        "udp_listen_port": port,
                        "mode": details.get("mode", "Wert"),
                        "json_key": details.get("json_key", ""),
                        "source_json_path": details.get("json_key", ""),
                    },
                )
            )
            if not handled_object_routes:
                handle_udp_to_mqtt_func(topic, value, prefix, retain, legacy_fallback)

    except Exception as exc:
        _log(add_log_entry, f"UDP Input Start/Runtime Fehler: {repr(exc)}")
    finally:
        try:
            sock.close()
        except Exception:
            pass


def load_udp_presets():
    if not os.path.exists(config.UDP_PRESETS_FILE):
        save_udp_presets(DEFAULT_UDP_PRESETS)
    data = config.safe_load_json_file(config.UDP_PRESETS_FILE, DEFAULT_UDP_PRESETS)
    return data if isinstance(data, list) else []


def save_udp_presets(data):
    config.safe_save_json_file(config.UDP_PRESETS_FILE, data if isinstance(data, list) else [], indent=2)


def get_udp_port_presets(load_mqtt2udp_config):
    presets = load_udp_presets()
    known = {}

    for item in presets:
        port = str(item.get("port", "")).strip()
        label = str(item.get("label", "")).strip()
        if port:
            known[port] = label

    for item in load_mqtt2udp_config():
        port = str(item.get("udp_port", "")).strip()
        if port and port not in known:
            known[port] = "aus MQTT->UDP gelernt"

    return [
        {"port": port, "label": label}
        for port, label in sorted(known.items(), key=lambda item: int(item[0]) if item[0].isdigit() else 999999)
    ]


def send_udp_input_test(port, test_topic, test_value, add_log_entry=None):
    message = f"{test_topic}:{test_value}"
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(message.encode("utf-8"), ("127.0.0.1", int(port)))
        finally:
            sock.close()
        _log(add_log_entry, f"UDP Test gesendet -> {message}")
        return True
    except Exception as exc:
        _log(add_log_entry, f"UDP Test Fehler: {exc}")
        return False


def run_udp2mqtt_test(index, form, load_udp2mqtt_config, save_udp2mqtt_config, publish_func, add_log_entry=None, update_last_seen=None):
    mappings = load_udp2mqtt_config()
    if index < 0 or index >= len(mappings):
        return False

    test_value = form.get(f"test_value_{index}", "123").strip()
    mappings[index]["test_value"] = test_value
    save_udp2mqtt_config(mappings)
    item = mappings[index]
    mqtt_topic = str(item.get("mqtt_topic", "")).strip()
    udp_topic = str(item.get("udp_topic", "")).strip()

    udp2mqtt_last_seen[udp_topic] = {
        "value": test_value,
        "time": datetime.now().strftime("%H:%M:%S"),
        "mqtt_topic": mqtt_topic,
    }
    if update_last_seen:
        update_last_seen("udp2mqtt", udp_topic, udp2mqtt_last_seen[udp_topic])
    if publish_func and mqtt_topic:
        publish_func(mqtt_topic, test_value, bool(item.get("retain", False)))
        _log(add_log_entry, f"UDP2MQTT Test -> {udp_topic} => {mqtt_topic} = {test_value}")
    return True
