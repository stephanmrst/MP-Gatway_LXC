"""Influx routes.

These routes delegate to the app core handlers during the migration.
"""

from flask import Blueprint, current_app


bp = Blueprint("influx", __name__)


def _core():
    return current_app.extensions["app_core"]


@bp.route("/test/influx", methods=["POST"])
def test_influx():
    return _core().test_influx()


@bp.route("/influx_explorer")
def influx_explorer():
    return _core().influx_explorer()


@bp.route("/influx_explorer/data")
def influx_explorer_data():
    return _core().influx_explorer_data()


@bp.route("/influx_explorer/delete", methods=["POST"])
def influx_explorer_delete():
    return _core().influx_explorer_delete()


@bp.route("/influx_explorer/delete_selected", methods=["POST"])
def influx_explorer_delete_selected():
    return _core().influx_explorer_delete_selected()
