"""Loxone routes.

These routes delegate to the app core handlers during the migration.
"""

from flask import Blueprint, current_app, redirect


bp = Blueprint("loxone", __name__)


def _core():
    return current_app.extensions["app_core"]


@bp.route("/mqtt2lox")
def mqtt2lox():
    # Legacy Mapping-Explorer entfernt. Konfiguration bleibt fuer Bestandsrouten erhalten.
    return redirect("/objects_v33")


@bp.route("/mqtt2lox/save", methods=["POST"])
def mqtt2lox_save():
    return redirect("/objects_v33")


@bp.route("/mqtt2lox/test/<int:index>", methods=["POST"])
def mqtt2lox_test(index):
    return redirect("/objects_v33")


@bp.route("/mqtt2lox_data")
def mqtt2lox_data():
    return redirect("/objects_v33")
