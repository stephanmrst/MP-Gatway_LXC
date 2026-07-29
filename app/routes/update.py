"""Weboberfläche für den MP-Gateway-Updater."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

from app.update import UpdateError, UpdateManager


bp = Blueprint("update", __name__)


def _manager() -> UpdateManager:
    return UpdateManager()


def _core():
    return current_app.extensions["app_core"]


def _render(message: str = "", error: str = ""):
    message = message or request.args.get("message", "")
    error = error or request.args.get("error", "")
    manager = _manager()
    info = manager.system_info()
    pending = info.get("pending") or {}
    package = pending.get("package") or {}
    content = render_template(
        "update/index.html",
        info=info,
        pending=pending,
        package=package,
        message=message,
        error=error,
    )
    if request.path.endswith("_embed"):
        return _core().embedded_page("Update", content)
    return _core().render_layout(
        "Update",
        content,
        active="update",
        subtitle="Plattformneutrale Updates für Docker, LXC und Debian",
    )


@bp.route("/update")
def update_page():
    return _render()


@bp.route("/update_embed")
def update_embed():
    return _render()


@bp.route("/update/check", methods=["POST"])
def update_check():
    manager = _manager()
    upload = request.files.get("update_file")
    if upload is None:
        return redirect(url_for("update.update_embed", error="Bitte zuerst eine Update-ZIP auswählen."))
    try:
        archive = manager.save_upload(upload)
        pending = manager.prepare(archive)
        version = pending.get("package", {}).get("version", "?")
        return redirect(url_for("update.update_embed", checked=version))
    except UpdateError as exc:
        return redirect(url_for("update.update_embed", error=str(exc)))


@bp.route("/update/online/check", methods=["POST"])
def update_online_check():
    manager = _manager()
    try:
        online = manager.check_online_update()
        return jsonify({"ok": True, "message": manager.read_status().get("message", ""), "online": online, "status": manager.read_status()})
    except UpdateError as exc:
        return jsonify({"ok": False, "message": str(exc), "online": manager.read_online(), "status": manager.read_status()}), 400


@bp.route("/update/online/download", methods=["POST"])
def update_online_download():
    manager = _manager()
    try:
        manager.download_online_update()
        result = manager.install_pending()
        return jsonify({
            "ok": True,
            "message": (
                f"Online-Update von {result['old_version']} auf {result['new_version']} wurde installiert. "
                "Bitte MP-Gateway jetzt neu starten."
            ),
            "old_version": result["old_version"],
            "new_version": result["new_version"],
            "restart_required": bool(result.get("restart_required", True)),
            "status": manager.read_status(),
            "runtime": result.get("runtime", {}),
        })
    except UpdateError as exc:
        return jsonify({"ok": False, "message": str(exc), "status": manager.read_status()}), 400


@bp.route("/update/install", methods=["POST"])
def update_install():
    manager = _manager()
    try:
        result = manager.install_pending()
        return jsonify(
            {
                "ok": True,
                "message": (
                    f"Update von {result['old_version']} auf {result['new_version']} wurde installiert. "
                    "Bitte MP-Gateway jetzt neu starten."
                ),
                "old_version": result["old_version"],
                "new_version": result["new_version"],
                "restart_required": bool(result.get("restart_required", True)),
                "status": manager.read_status(),
                "runtime": result.get("runtime", {}),
            }
        )
    except UpdateError as exc:
        return jsonify({"ok": False, "message": str(exc), "status": manager.read_status()}), 400


@bp.route("/update/status")
def update_status():
    return jsonify(_manager().system_info())


@bp.route("/update/sidebar-status")
def update_sidebar_status():
    return jsonify(_manager().sidebar_status())


@bp.route("/update/restart", methods=["POST"])
def update_restart():
    try:
        return jsonify(_manager().request_restart())
    except UpdateError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
