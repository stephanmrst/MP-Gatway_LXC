"""API, search, and conflict routes.

These routes delegate to the app core handlers during the migration.
"""

from flask import Blueprint, current_app, jsonify, request

try:
    from app.services import object_service
except ModuleNotFoundError:
    from services import object_service


bp = Blueprint("api", __name__)


def _core():
    return current_app.extensions["app_core"]


def _object_service():
    try:
        core = _core()
        return getattr(core, "object_core_service", object_service)
    except Exception:
        return object_service


def _reload_object_routes():
    try:
        core = _core()
        if hasattr(core, "reload_object_routes_async"):
            core.reload_object_routes_async("api")
        elif hasattr(core, "reload_object_routes"):
            core.reload_object_routes("api")
    except Exception:
        current_app.logger.exception("Object route reload failed")


def _sync_object_live_from_core():
    try:
        core = _core()
    except Exception:
        return
    try:
        config = getattr(core, "load_config", lambda: {})() or {}
        topic_config = getattr(core, "load_topic_config", lambda: {})() or {}
        mqtt_prefix = str(((config.get("mqtt") or {}).get("prefix") or "loxone")).strip()
        state_mapping = getattr(core, "state_mapping", {}) or {}
        display_values = getattr(core, "display_values", {}) or {}
        last_values = getattr(core, "last_values", {}) or {}
        build_state_topic = getattr(core, "build_state_topic", None)

        for uuid, state_name in dict(state_mapping).items():
            default_topic = build_state_topic(mqtt_prefix, state_name) if build_state_topic else f"{mqtt_prefix}/{state_name}"
            settings = topic_config.get(default_topic, {}) if isinstance(topic_config, dict) else {}
            custom_name = str((settings or {}).get("custom_name", "") or "").strip()
            candidate_topics = [custom_name, default_topic] if custom_name else [default_topic]
            value = None
            for topic in candidate_topics:
                if not topic:
                    continue
                if topic in display_values and display_values.get(topic) not in (None, ""):
                    value = display_values.get(topic)
                    break
                if topic in last_values and last_values.get(topic) not in (None, ""):
                    value = last_values.get(topic)
                    break
            if value in (None, ""):
                continue
            _object_service().record_live_value(
                "loxone",
                value,
                loxone_uuid=uuid,
                loxone_io=state_name,
                name=state_name,
            )
    except Exception:
        current_app.logger.exception("Object live Loxone sync failed")
    try:
        for info in getattr(core, "get_mqtt_monitor_values", lambda: {})().values():
            if isinstance(info, dict):
                _object_service().record_live_value("mqtt", info.get("payload"), topic=info.get("topic", ""), timestamp=info.get("timestamp", info.get("time", "")))
    except Exception:
        current_app.logger.exception("Object live MQTT sync failed")
    try:
        for ga, info in getattr(core, "get_knx_monitor_values", lambda: {})().items():
            if isinstance(info, dict):
                _object_service().record_live_value("knx", info.get("value"), group_address=info.get("ga", ga), timestamp=info.get("timestamp", info.get("time", "")))
    except Exception:
        current_app.logger.exception("Object live KNX sync failed")
    try:
        for topic, info in getattr(core, "get_udp_last_seen", lambda kind: {})("udp2mqtt").items():
            if isinstance(info, dict):
                _object_service().record_live_value("udp", info.get("value"), udp_topic=topic, timestamp=info.get("timestamp", info.get("time", "")))
    except Exception:
        current_app.logger.exception("Object live UDP sync failed")


@bp.route("/global_search")
def global_search():
    return _core().global_search()


@bp.route("/global_search_page")
def global_search_page():
    return _core().global_search_page()


@bp.route("/conflicts")
def conflicts():
    return _core().conflicts()


@bp.route("/conflicts_page")
def conflicts_page():
    return _core().conflicts_page()


@bp.route("/api/objects")
def api_objects_list():
    objects = [object_service.serialize_object(item) for item in object_service.list_objects()]
    return jsonify({"objects": objects})


@bp.route("/api/objects/<object_id>")
def api_objects_get(object_id):
    item = object_service.get_object(object_id)
    if item is None:
        return jsonify({"success": False, "error": "object_not_found"}), 404
    return jsonify(object_service.serialize_object(item))


@bp.route("/api/objects/live")
def api_objects_live():
    _sync_object_live_from_core()
    service = _object_service()
    objects = service.list_object_live_status()
    for payload in objects:
        object_id = str((payload or {}).get("object_id", "") or "").strip()
        if not object_id:
            continue
        item = service.get_object(object_id)
        memory_live_state = dict(getattr(service, "OBJECT_LIVE_CACHE", {}).get(object_id) or {})
        current_app.logger.info(
            "LIVE TAB DEBUG object_id=%s memory_live_state=%s object.live_value=%s object.last_value=%s return=%s",
            object_id,
            memory_live_state,
            getattr(item, "live_value", None) if item is not None else None,
            getattr(item, "last_value", None) if item is not None else None,
            payload,
        )
    return jsonify({"objects": objects})


@bp.route("/api/objects/<object_id>/live")
def api_objects_live_get(object_id):
    _sync_object_live_from_core()
    service = _object_service()
    live = service.get_object_live_status(object_id)
    if live is None:
        return jsonify({"success": False, "error": "object_not_found"}), 404
    item = service.get_object(object_id)
    memory_live_state = dict(getattr(service, "OBJECT_LIVE_CACHE", {}).get(str(object_id or "").strip()) or {})
    current_app.logger.info(
        "LIVE TAB DEBUG object_id=%s memory_live_state=%s object.live_value=%s object.last_value=%s return=%s",
        object_id,
        memory_live_state,
        getattr(item, "live_value", None) if item is not None else None,
        getattr(item, "last_value", None) if item is not None else None,
        live,
    )
    return jsonify(live)


@bp.route("/api/objects", methods=["POST"])
def api_objects_create():
    try:
        payload = request.get_json(silent=True) or request.form.to_dict()
        item = object_service.create_object(payload)
        _reload_object_routes()
        return jsonify({"success": True, "object": object_service.serialize_object(item)}), 201
    except PermissionError as exc:
        current_app.logger.warning("Object create blocked by file lock: %s", exc)
        return jsonify({"success": False, "error": "objects_file_locked", "message": "Objektdatei ist gerade gesperrt. Bitte erneut versuchen."}), 423
    except Exception as exc:
        current_app.logger.exception("Object create failed: %s", exc)
        return jsonify({"success": False, "error": "object_create_failed"}), 500


@bp.route("/api/objects/<object_id>", methods=["PUT"])
def api_objects_update(object_id):
    try:
        payload = request.get_json(silent=True) or request.form.to_dict()
        item = object_service.update_object(object_id, payload)
        if item is None:
            return jsonify({"success": False, "error": "object_not_found"}), 404
        _reload_object_routes()
        return jsonify({"success": True, "object": object_service.serialize_object(item)})
    except PermissionError as exc:
        current_app.logger.warning("Object update blocked by file lock: %s", exc)
        return jsonify({"success": False, "error": "objects_file_locked", "message": "Objektdatei ist gerade gesperrt. Bitte erneut versuchen."}), 423
    except Exception as exc:
        current_app.logger.exception("Object update failed: %s", exc)
        return jsonify({"success": False, "error": "object_update_failed"}), 500


@bp.route("/api/objects/<object_id>", methods=["DELETE"])
def api_objects_delete(object_id):
    try:
        current_app.logger.info("delete_start object_id=%s", object_id)
        deleted = object_service.delete_object(object_id)
        if not deleted:
            current_app.logger.info("write_objects_done object_id=%s deleted=false", object_id)
            current_app.logger.info("cache_invalidated object_id=%s reload_requested=false", object_id)
            current_app.logger.info("delete_response_sent object_id=%s", object_id)
            return jsonify({"success": True, "deleted": False, "notice": "object_not_found"}), 200
        _reload_object_routes()
        current_app.logger.info("write_objects_done object_id=%s deleted=true", object_id)
        current_app.logger.info("cache_invalidated object_id=%s reload_requested=true", object_id)
        current_app.logger.info("delete_response_sent object_id=%s", object_id)
        return jsonify({"success": True, "deleted": True})
    except PermissionError as exc:
        current_app.logger.warning("Object delete blocked by file lock: %s", exc)
        return jsonify({"success": False, "error": "objects_file_locked", "message": "Objektdatei ist gerade gesperrt. Bitte erneut versuchen."}), 423
    except Exception as exc:
        current_app.logger.exception("Object delete failed: %s", exc)
        return jsonify({"success": False, "error": "object_delete_failed"}), 500


@bp.route("/api/objects/<object_id>/toggle", methods=["POST"])
def api_objects_toggle(object_id):
    try:
        payload = request.get_json(silent=True) or request.form.to_dict()
        enabled = payload.get("enabled", True)
        if isinstance(enabled, str):
            enabled = enabled.lower() in {"1", "true", "yes", "on"}
        item = object_service.toggle_object(object_id, bool(enabled))
        if item is None:
            return jsonify({"success": False, "error": "object_not_found"}), 404
        _reload_object_routes()
        return jsonify({"success": True, "object": object_service.serialize_object(item)})
    except Exception as exc:
        current_app.logger.exception("Object toggle failed: %s", exc)
        return jsonify({"success": False, "error": "object_toggle_failed"}), 500
