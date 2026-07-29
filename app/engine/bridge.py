import threading
import time


def start_bridge(runtime_context, load_config, bridge_runner, add_log_entry, loxwebsocket_available=True, loxwebsocket_status="Loxone: Bibliothek nicht installiert"):
    if not loxwebsocket_available:
        runtime_context.bridge.status = loxwebsocket_status
        add_log_entry(runtime_context.bridge.status)
        return False

    if runtime_context.bridge.running or (runtime_context.bridge.thread and runtime_context.bridge.thread.is_alive()):
        return True

    runtime_context.bridge.stop_requested = False
    runtime_context.bridge.status = "startet"

    cfg = load_config()
    runtime_context.bridge.thread = threading.Thread(target=bridge_runner, args=(cfg,), daemon=True)
    runtime_context.bridge.thread.start()

    time.sleep(0.5)
    return True


def request_bridge_stop(runtime_context):
    runtime_context.bridge.stop_requested = True
    runtime_context.bridge.status = "Stop angefordert"
    return True
