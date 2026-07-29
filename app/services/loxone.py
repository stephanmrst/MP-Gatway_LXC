import json
from datetime import datetime

import requests


def convert_lox_value(value):
    if isinstance(value, bool):
        return "1" if value else "0"

    if value is None:
        return ""

    return str(value)


def build_mqtt2lox_messages(mapping, mqtt_payload, get_nested_value, flatten_json):
    payload_mode = mapping.get("payload_mode", "raw")
    json_key = mapping.get("json_key", "").strip()
    output_mode = mapping.get("output_mode", "single")
    loxone_io = mapping.get("loxone_io", "").strip()

    if not loxone_io:
        return []

    # bytes sauber zu Text machen
    if isinstance(mqtt_payload, bytes):
        mqtt_payload = mqtt_payload.decode("utf-8", errors="ignore")

    # RAW wie bisher
    if payload_mode == "raw":
        return [f"{loxone_io}:{convert_lox_value(mqtt_payload)}"]

    # JSON parsen
    try:
        if isinstance(mqtt_payload, str):
            data = json.loads(mqtt_payload)
        else:
            data = mqtt_payload
    except Exception as e:
        print(f"MQTT2LOX JSON Fehler bei {loxone_io}: {e}")
        return []

    # Einzelnen JSON-Key holen
    if payload_mode == "json_key":
        if not json_key:
            return []

        value = get_nested_value(data, json_key)

        if value is None:
            return []

        return [
            f"{loxone_io}:{convert_lox_value(value)}"
        ]

    # Alle JSON-Werte aufteilen
    if payload_mode == "json_all":
        flat = flatten_json(data)

        if output_mode == "split":
            messages = []

            for key, value in flat.items():
                messages.append(
                    f"{loxone_io}/{key}:{convert_lox_value(value)}"
                )

            return messages

        # Sammeln in eine UDP-Nachricht
        values = ",".join(
            f"{key}:{convert_lox_value(value)}"
            for key, value in flat.items()
        )

        return [
            f"{loxone_io}/{values}"
        ]

    return []


def handle_mqtt_to_loxone(
    config,
    topic,
    payload,
    load_mqtt2lox_config,
    mqtt2lox_last_seen,
    add_log_entry,
    requests,
    get_nested_value,
    flatten_json,
):
    mappings = load_mqtt2lox_config()

    for item in mappings:

        if not item.get("enabled", True):
            continue

        source_topic = item.get("source_topic", "").strip()
        custom_topic = item.get("custom_topic", "").strip()
        loxone_io = item.get("loxone_io", "").strip()

        if not loxone_io:
            continue

        topic_match = False

        if source_topic and topic == source_topic:
            topic_match = True

        if custom_topic and topic == custom_topic:
            topic_match = True

        if not topic_match:
            continue

        mqtt2lox_last_seen[source_topic] = {
            "value": payload,
            "time": datetime.now().strftime("%H:%M:%S")
        }

        messages = build_mqtt2lox_messages(item, payload, get_nested_value, flatten_json)

        if not messages:
            add_log_entry(f"MQTT2LOX keine gültige Nachricht für {topic}")
            return True

        try:
            for message in messages:
                if ":" not in message:
                    add_log_entry(f"MQTT2LOX ungültiges Format: {message}")
                    continue

                target_io, target_value = message.split(":", 1)

                url = f"http://{config['loxone']['host']}/dev/sps/io/{target_io}/{target_value}"

                r = requests.get(
                    url,
                    auth=(config["loxone"]["user"], config["loxone"]["password"]),
                    timeout=5
                )

                if r.status_code == 200:
                    add_log_entry(
                        f"MQTT2LOX -> {topic} => {target_io} = {target_value}"
                    )
                else:
                    add_log_entry(
                        f"MQTT2LOX Fehler HTTP {r.status_code}: {r.text}"
                    )

        except Exception as e:
            add_log_entry(f"MQTT2LOX Fehler: {e}")

        return True

    return False


def send_loxone_value(config, loxone_io, value, add_log_entry=None, requests_module=requests):
    loxone_io = str(loxone_io or "").strip()
    if not loxone_io:
        if add_log_entry:
            add_log_entry("LOXONE Fehler: IO-Adresse fehlt")
        return False
    try:
        url = f"http://{config['loxone']['host']}/dev/sps/io/{loxone_io}/{convert_lox_value(value)}"
        response = requests_module.get(
            url,
            auth=(config["loxone"]["user"], config["loxone"]["password"]),
            timeout=5,
        )
        if response.status_code == 200:
            if add_log_entry:
                add_log_entry(f"LOXONE Senden OK io={loxone_io} value={value}")
            return True
        if add_log_entry:
            add_log_entry(f"LOXONE Senden Fehler HTTP {response.status_code}: {response.text}")
        return False
    except Exception as exc:
        if add_log_entry:
            add_log_entry(f"LOXONE Senden Fehler: {type(exc).__name__}: {exc}")
        return False


def get_loxone_state_topic_options(
    config=None,
    load_config=None,
    load_mapping=None,
    add_log_entry=None,
    load_topic_config=None,
    get_state_mapping=None,
    build_state_topic=None,
):
    """Return current Loxone state MQTT topics plus configured custom topics."""
    if config is None:
        config = load_config()
    try:
        load_mapping(config)
    except Exception as e:
        add_log_entry(f"Loxone State Liste Fehler: {e}")
    topic_settings = load_topic_config()
    options = set()
    for uuid, name in get_state_mapping().items():
        topic = build_state_topic(config["mqtt"].get("prefix", "loxone"), name)
        options.add(topic)
        custom = str(topic_settings.get(topic, {}).get("custom_name", "")).strip()
        if custom:
            options.add(custom)
    return sorted(options, key=lambda x: str(x).casefold())


def get_loxone_io_options(
    config=None,
    load_config=None,
    load_mapping=None,
    add_log_entry=None,
    get_control_mapping=None,
):
    """Return current Loxone control/input names for /dev/sps/io/<name>/<value>."""
    if config is None:
        config = load_config()
    try:
        load_mapping(config)
    except Exception as e:
        add_log_entry(f"Loxone IO Liste Fehler: {e}")
    return sorted(get_control_mapping().keys(), key=lambda x: str(x).casefold())


def get_loxone_explorer_count(
    load_config,
    load_mapping,
    add_log_entry,
    load_topic_config,
    get_state_mapping,
    build_state_topic,
):
    try:
        return len(get_loxone_state_topic_options(
            load_config(),
            load_config,
            load_mapping,
            add_log_entry,
            load_topic_config,
            get_state_mapping,
            build_state_topic,
        ))
    except Exception as e:
        add_log_entry(f"Loxone Explorer Anzahl Fehler: {e}")
        return 0
