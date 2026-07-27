"""Backup routes.

These routes delegate to the app core handlers during the migration.
"""

from flask import Blueprint, current_app


bp = Blueprint("backup", __name__)


def _core():
    return current_app.extensions["app_core"]


@bp.route("/backup")
def backup_config():
    return _core().backup_config()


@bp.route("/restore", methods=["POST"])
def restore_config():
    return _core().restore_config()
