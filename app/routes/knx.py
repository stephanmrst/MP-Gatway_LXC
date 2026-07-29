"""KNX routes.

These routes delegate to the app core handlers during the migration.
"""

from datetime import datetime

from flask import Blueprint, current_app, jsonify, redirect, request

try:
    from app.services import knx as knx_service
except ModuleNotFoundError:
    from services import knx as knx_service


bp = Blueprint("knx", __name__)


def _core():
    return current_app.extensions["app_core"]


def _knx_test_error_response(exc, status_code=500):
    group_address = knx_service.normalize_knx_ga(request.form.get("group_address", ""))
    selected_dpt = str(request.form.get("dpt", "auto") or "auto").strip() or "auto"
    raw_value = str(request.form.get("value", "") or "").strip()
    in_monitor = str(request.form.get("show_in_monitor", "1")) == "1"
    resolved_dpt = "9.001" if selected_dpt.lower() == "auto" else selected_dpt
    payload = {
        "ok": False,
        "error": str(exc),
        "diagnostic": {
            "time": datetime.now().strftime("%H:%M:%S"),
            "telegram_type": "GroupValueWrite",
            "group_address": group_address,
            "dpt": resolved_dpt,
            "resolved_dpt": resolved_dpt,
            "raw_value": raw_value,
            "converted_value": "-",
            "apdu": "-",
            "status": "FEHLER",
            "in_monitor": in_monitor,
            "show_in_monitor": in_monitor,
            "http_status": int(status_code),
        },
    }
    return jsonify(payload), int(status_code)


@bp.route("/knx")
def knx_hub():
    return _core().knx_hub()


@bp.route("/knx_settings_embed")
def knx_settings_embed():
    return _core().knx_settings_embed()


@bp.route("/knx/save", methods=["POST"])
def knx_save():
    return _core().knx_save()


@bp.route("/knx/test", methods=["POST"])
def knx_test():
    try:
        return _core().knx_test()
    except Exception as exc:
        current_app.logger.exception("KNX test route failed")
        return _knx_test_error_response(exc, 500)


@bp.route("/knx_test/send", methods=["POST"])
def knx_test_send():
    try:
        return _core().knx_test_send()
    except Exception as exc:
        current_app.logger.exception("KNX test send failed")
        return _knx_test_error_response(exc, 500)


@bp.route("/knx_test/repeat", methods=["POST"])
def knx_test_repeat():
    try:
        return _core().knx_test_repeat()
    except Exception as exc:
        current_app.logger.exception("KNX test repeat failed")
        return _knx_test_error_response(exc, 500)


@bp.route("/knx_test/clear_monitor", methods=["POST"])
def knx_test_clear_monitor():
    try:
        return _core().knx_test_clear_monitor()
    except Exception as exc:
        current_app.logger.exception("KNX test clear monitor failed")
        return _knx_test_error_response(exc, 500)


@bp.route("/mqtt2knx")
def mqtt2knx():
    # Legacy Mapping-Explorer entfernt. Bestehende Laufzeitkonfiguration bleibt kompatibel.
    return redirect("/objects_v33")


@bp.route("/mqtt2knx/save", methods=["POST"])
def mqtt2knx_save():
    return redirect("/objects_v33")


@bp.route("/mqtt2knx/test/<int:index>", methods=["POST"])
def mqtt2knx_test(index):
    return redirect("/objects_v33")


@bp.route("/mqtt2knx_data")
def mqtt2knx_data():
    return redirect("/objects_v33")


@bp.route("/udp2knx")
def udp2knx():
    # Legacy Mapping-Explorer entfernt. Bestehende Laufzeitkonfiguration bleibt kompatibel.
    return redirect("/objects_v33")


@bp.route("/udp2knx/save", methods=["POST"])
def udp2knx_save():
    return redirect("/objects_v33")


@bp.route("/udp2knx/test/<int:index>", methods=["POST"])
def udp2knx_test(index):
    return redirect("/objects_v33")


@bp.route("/udp2knx_data")
def udp2knx_data():
    return redirect("/objects_v33")


@bp.route("/knx2mqtt")
def knx2mqtt():
    # Legacy Mapping-Explorer entfernt. Bestehende Laufzeitkonfiguration bleibt kompatibel.
    return redirect("/objects_v33")


@bp.route("/knx2mqtt/save", methods=["POST"])
def knx2mqtt_save():
    return redirect("/objects_v33")


@bp.route("/knx2mqtt_data")
def knx2mqtt_data():
    return redirect("/objects_v33")


@bp.route("/knx2lox")
def knx2lox():
    # Legacy Mapping-Explorer entfernt. Bestehende Laufzeitkonfiguration bleibt kompatibel.
    return redirect("/objects_v33")


@bp.route("/knx2lox/save", methods=["POST"])
def knx2lox_save():
    return redirect("/objects_v33")


@bp.route("/knx2lox_data")
def knx2lox_data():
    return redirect("/objects_v33")


@bp.route("/knx_monitor")
def knx_monitor():
    return _core().knx_monitor()


@bp.route("/knx_monitor_data")
def knx_monitor_data():
    return _core().knx_monitor_data()


@bp.route("/knx_monitor/influx", methods=["POST"])
def knx_monitor_influx():
    return _core().knx_monitor_influx()


@bp.route("/knx_monitor/influx_type", methods=["POST"])
def knx_monitor_influx_type():
    return _core().knx_monitor_influx_type()


@bp.route("/knx_monitor/influx_topic", methods=["POST"])
def knx_monitor_influx_topic():
    return _core().knx_monitor_influx_topic()


@bp.route("/knx_listener_start", methods=["POST"])
def knx_listener_start():
    return _core().knx_listener_start()
