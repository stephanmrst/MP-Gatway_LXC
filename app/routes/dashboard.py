"""Dashboard routes.

These routes delegate to the app core handlers during the migration.
"""

from flask import Blueprint, current_app


bp = Blueprint("dashboard", __name__)


def _core():
    return current_app.extensions["app_core"]


@bp.route("/")
def index():
    return _core().index()


@bp.route("/dashboard_embed")
def dashboard_embed():
    return _core().dashboard_embed()


@bp.route("/shell_status")
def shell_status():
    return _core().shell_status()


@bp.route("/live_log")
def live_log_console():
    return _core().live_log_console()


@bp.route("/live_log_page")
def live_log_page():
    return _core().live_log_page()


@bp.route("/live_log_data")
def live_log_data():
    return _core().live_log_data()


@bp.route("/clear_log")
def clear_log():
    return _core().clear_log()


@bp.route("/clear_monitor")
def clear_monitor():
    return _core().clear_monitor()
