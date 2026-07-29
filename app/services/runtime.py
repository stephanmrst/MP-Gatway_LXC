import json
import os
import shutil
import socket
import subprocess
import time
from datetime import datetime


def add_log(live_log, bump_sse, text):
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"{timestamp} | {text}"

    print(entry)
    live_log.appendleft(entry)
    bump_sse("log")
    bump_sse("status")


def live_log_payload(live_log, limit=12):
    return {"logs": [str(x) for x in list(live_log)[:limit]]}


def get_live_log_entries(live_log, limit=100):
    return [str(x) for x in list(live_log)[:limit]]


def clear_live_log(live_log, bump_sse):
    live_log.clear()
    bump_sse("log")
    bump_sse("status")


def build_status_payload(bridge_status):
    return {"status": bridge_status}


status_event_payload = build_status_payload


def get_bridge_status(bridge_status):
    return bridge_status


def get_plugin_count(load_plugins_config):
    try:
        return len(load_plugins_config())
    except Exception:
        return 0


def get_dashboard_stats(load_config, load_mqtt2lox_config, load_mqtt2udp_config, load_mqtt2knx_config, load_knx2mqtt_config, load_udp2knx_config, load_knx2lox_config):
    cfg = load_config()
    return {
        "mqtt2lox": len(load_mqtt2lox_config()),
        "mqtt2udp": len(load_mqtt2udp_config()),
        "mqtt2knx": len(load_mqtt2knx_config()),
        "knx2mqtt": len(load_knx2mqtt_config()),
        "udp2knx": len(load_udp2knx_config()),
        "knx2lox": len(load_knx2lox_config()),
        "influx": "aktiv" if cfg.get("influx", {}).get("enabled") else "aus",
    }


def get_system_status(bridge_status, load_config, get_internal_broker_status_func):
    return {
        "bridge": bridge_status,
        "influx": "aktiv" if load_config().get("influx", {}).get("enabled") else "aus",
        "internal_broker": get_internal_broker_status_func(),
    }


def status_sse_response(Response, stream_with_context, shell_status_payload_func, bridge_status_getter):
    def event_stream():
        last_status = None
        last_heartbeat = 0
        while True:
            try:
                now = time.time()
                current = str(bridge_status_getter())
                if current != last_status:
                    yield "event: status\n"
                    yield "data: " + json.dumps(shell_status_payload_func(), ensure_ascii=False) + "\n\n"
                    last_status = current
                    last_heartbeat = now
                elif now - last_heartbeat > 15:
                    yield ": keepalive\n\n"
                    last_heartbeat = now
                time.sleep(0.5)
            except GeneratorExit:
                break
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                time.sleep(2)

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    })


def is_tcp_port_open(host, port, timeout=0.4):
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


def get_internal_broker_status(load_internal_broker_config, internal_broker_process, shutil_module=shutil, os_module=os):
    cfg = load_internal_broker_config()
    port_open = is_tcp_port_open(cfg.get("connect_host", "127.0.0.1"), int(cfg.get("port", 1883)))
    process_running = False
    try:
        process_running = bool(internal_broker_process and internal_broker_process.poll() is None)
    except Exception:
        process_running = False

    mosquitto_path = cfg.get("mosquitto_path", "mosquitto") or "mosquitto"
    exe_found = bool(shutil_module.which(mosquitto_path)) or os_module.path.exists(mosquitto_path)

    if process_running:
        state = "läuft (App)"
    elif port_open:
        state = "läuft (Port offen)"
    else:
        state = "gestoppt"

    return {
        "state": state,
        "running": process_running or port_open,
        "process_running": process_running,
        "port_open": port_open,
        "exe_found": exe_found,
        "port": int(cfg.get("port", 1883)),
        "use_as_main": bool(cfg.get("use_as_main", False)),
        "enabled": bool(cfg.get("enabled", False))
    }


def build_mosquitto_config_file(cfg, config_dir, data_dir, add_log_entry, shutil_module=shutil, subprocess_module=subprocess, os_module=os):
    conf_path = os_module.path.join(config_dir, "internal_mosquitto.conf")
    data_dir = os_module.path.join(data_dir, "mosquitto_data")
    os_module.makedirs(data_dir, exist_ok=True)

    host = str(cfg.get("host", "0.0.0.0") or "0.0.0.0").strip()
    port = int(cfg.get("port", 1883))
    allow_anonymous = bool(cfg.get("allow_anonymous", True))
    persistence = bool(cfg.get("persistence", True))

    lines = [
        f"listener {port} {host}",
        "protocol mqtt",
        f"allow_anonymous {'true' if allow_anonymous else 'false'}",
        f"persistence {'true' if persistence else 'false'}",
        f"persistence_location {data_dir.replace(os_module.sep, '/')}/",
        "log_dest stdout",
        "connection_messages true"
    ]

    user = str(cfg.get("user", "") or "").strip()
    password = str(cfg.get("password", "") or "")
    if not allow_anonymous and user and password:
        passwd_tool = shutil_module.which("mosquitto_passwd")
        passwd_file = os_module.path.join(config_dir, "internal_mosquitto.passwd")
        if passwd_tool:
            try:
                subprocess_module.run([passwd_tool, "-b", "-c", passwd_file, user, password], check=True, capture_output=True, text=True)
                lines.append(f"password_file {passwd_file.replace(os_module.sep, '/')}")
            except Exception as e:
                add_log_entry(f"Interner Broker Passwortdatei Fehler: {e}")
        else:
            add_log_entry("Interner Broker: mosquitto_passwd nicht gefunden, User/Pass nicht aktiviert")

    with open(conf_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return conf_path


def start_internal_broker(load_internal_broker_config, get_internal_broker_status_func, build_config_func, add_log_entry, base_dir, subprocess_module=subprocess, time_module=time, shutil_module=shutil, os_module=os):
    cfg = load_internal_broker_config()

    if not cfg.get("enabled", False):
        add_log_entry("Interner Broker nicht aktiviert")
        return False, "Interner Broker ist nicht aktiviert", None

    status = get_internal_broker_status_func()
    if status.get("running"):
        return True, f"Interner Broker läuft bereits auf Port {status.get('port')}", None

    mosquitto_path = cfg.get("mosquitto_path", "mosquitto") or "mosquitto"
    if not (shutil_module.which(mosquitto_path) or os_module.path.exists(mosquitto_path)):
        return False, f"Mosquitto nicht gefunden: {mosquitto_path}", None

    conf_path = build_config_func(cfg)

    try:
        process = subprocess_module.Popen(
            [mosquitto_path, "-c", conf_path],
            cwd=base_dir,
            stdout=subprocess_module.DEVNULL,
            stderr=subprocess_module.DEVNULL
        )
        time_module.sleep(0.7)
        if process.poll() is not None:
            return False, "Mosquitto ist direkt wieder beendet", process
        add_log_entry(f"Interner MQTT Broker gestartet auf Port {cfg.get('port')}")
        return True, "Interner Broker gestartet", process
    except Exception as e:
        return False, str(e), None


def stop_internal_broker(internal_broker_process, add_log_entry):
    try:
        if internal_broker_process and internal_broker_process.poll() is None:
            internal_broker_process.terminate()
            try:
                internal_broker_process.wait(timeout=3)
            except Exception:
                internal_broker_process.kill()
            add_log_entry("Interner MQTT Broker gestoppt")
            return True, "Interner Broker gestoppt", internal_broker_process
        return True, "Kein von der App gestarteter Broker aktiv", internal_broker_process
    except Exception as e:
        return False, str(e), internal_broker_process
