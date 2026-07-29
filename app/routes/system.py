"""System and runtime routes."""

from flask import Blueprint, current_app, redirect

try:
    from app.engine import bridge as bridge_engine
except ModuleNotFoundError:
    from engine import bridge as bridge_engine


bp = Blueprint("system", __name__)


def _core():
    return current_app.extensions["app_core"]


@bp.route("/start", methods=["POST"])
def start_bridge():
    core = _core()
    bridge_engine.start_bridge(
        core.runtime_context,
        core.load_config,
        core.bridge_runner,
        core.add_log_entry,
        loxwebsocket_available=getattr(core, "LOXWEBSOCKET_AVAILABLE", True),
        loxwebsocket_status=getattr(core, "LOXWEBSOCKET_STATUS", "Loxone: Bibliothek nicht installiert"),
    )
    return redirect("/")


@bp.route("/stop", methods=["POST"])
def stop_bridge():
    _core().request_gateway_stop_async()
    return redirect("/")


@bp.route("/test/loxone", methods=["POST"])
def test_loxone():
    return _core().test_loxone()


@bp.route("/test/mqtt", methods=["POST"])
def test_mqtt():
    return _core().test_mqtt()


@bp.route("/internal_broker/save", methods=["POST"])
def internal_broker_save():
    return _core().internal_broker_save()


@bp.route("/internal_broker/start", methods=["POST"])
def internal_broker_start():
    return _core().internal_broker_start()


@bp.route("/internal_broker/stop", methods=["POST"])
def internal_broker_stop():
    return _core().internal_broker_stop()


@bp.route("/internal_broker/status")
def internal_broker_status_route():
    return _core().internal_broker_status_route()
