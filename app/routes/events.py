"""Server-sent event routes."""

from flask import Blueprint, Response, current_app, stream_with_context

try:
    from app.utils import sse as sse_utils
except ModuleNotFoundError:
    from utils import sse as sse_utils


bp = Blueprint("events", __name__)


def _core():
    return current_app.extensions["app_core"]


def _sse_version(version_name):
    core = _core()
    if version_name == "knx":
        return core.get_knx_monitor_version()
    return int(core.sse_versions.get(version_name, 0))


@bp.route("/events/status")
def events_status():
    core = _core()
    return sse_utils.status_sse_response(
        Response,
        stream_with_context,
        core.shell_status_payload,
        lambda: core.runtime_context.bridge.status,
    )


@bp.route("/events/live_log")
def events_live_log():
    core = _core()
    return sse_utils.sse_response(
        Response,
        stream_with_context,
        "live_log",
        core.live_log_payload,
        lambda: _sse_version("log"),
    )


@bp.route("/events/live_log_full")
def events_live_log_full():
    core = _core()
    return sse_utils.sse_response(
        Response,
        stream_with_context,
        "live_log",
        core.live_log_full_payload,
        lambda: _sse_version("log"),
    )


@bp.route("/events/mqtt_monitor")
def events_mqtt_monitor():
    core = _core()
    return sse_utils.sse_response(
        Response,
        stream_with_context,
        "mqtt_monitor",
        core.get_mqtt_monitor_values,
        lambda: _sse_version("mqtt"),
        interval=0.1,
    )


@bp.route("/events/knx_monitor")
def events_knx_monitor():
    core = _core()

    def payload():
        print("[KNX SSE]", len(core.get_knx_monitor_log()))
        return core.knx_monitor_payload()

    return sse_utils.sse_response(
        Response,
        stream_with_context,
        "knx_monitor",
        payload,
        lambda: _sse_version("knx"),
    )
