"""Application factory for MP-Gateway."""

from .engine import port
from .branding import APP_LEGACY_NAME, APP_NAME, APP_SUBTITLE


def _register_blueprints(app):
    from .routes.api import bp as api_bp
    from .routes.backup import bp as backup_bp
    from .routes.config import bp as config_bp
    from .routes.dashboard import bp as dashboard_bp
    from .routes.events import bp as events_bp
    from .routes.influx import bp as influx_bp
    from .routes.knx import bp as knx_bp
    from .routes.loxone import bp as loxone_bp
    from .routes.mqtt import bp as mqtt_bp
    from .routes.objects import bp as objects_bp
    from .routes.objects_v33 import bp as objects_v33_bp
    from .routes.openccu import bp as openccu_bp
    from .routes.system import bp as system_bp
    from .routes.udp import bp as udp_bp
    from .routes.update import bp as update_bp

    blueprints = (
        dashboard_bp,
        config_bp,
        backup_bp,
        objects_bp,
        objects_v33_bp,
        openccu_bp,
        mqtt_bp,
        udp_bp,
        loxone_bp,
        influx_bp,
        api_bp,
        events_bp,
        knx_bp,
        system_bp,
        update_bp,
    )
    for blueprint in blueprints:
        if blueprint.name not in app.blueprints:
            app.register_blueprint(blueprint)


def create_app():
    """Create the Flask application."""
    port.configure_paths()
    port.run_startup_check()

    # A successful process start after an update clears the restart request.
    # This works equally for Docker restart policies, systemd/LXC and standalone starts.
    try:
        from .update import UpdateManager
        UpdateManager().reconcile_startup_status()
    except Exception:
        # Startup must never fail merely because updater status metadata is unavailable.
        pass

    from . import core

    # app/main.py can make the same service importable under two module names:
    # ``services.object_service`` (legacy core) and
    # ``app.services.object_service`` (blueprints/new services). Python would
    # otherwise create two module instances with two independent live caches.
    # Force both import paths to use the core singleton before blueprints and
    # the OpenCCU runtime are imported.
    import sys
    from . import services as services_package
    sys.modules["app.services.object_service"] = core.object_core_service
    setattr(services_package, "object_service", core.object_core_service)

    core.APP_VERSION = port.APP_VERSION
    core.LOXWEBSOCKET_AVAILABLE = port.LOXWEBSOCKET_AVAILABLE
    core.LOXWEBSOCKET_STATUS = port.LOXWEBSOCKET_STATUS

    if not port.LOXWEBSOCKET_AVAILABLE:
        try:
            core.runtime_context.bridge.status = port.LOXWEBSOCKET_STATUS
        except Exception:
            pass
        try:
            core.add_log_entry(port.LOXWEBSOCKET_STATUS)
        except Exception:
            pass

    app = core.app
    app.config["APP_VERSION"] = port.APP_VERSION
    app.config["APP_NAME"] = APP_NAME
    app.config["APP_SUBTITLE"] = APP_SUBTITLE
    app.config["APP_LEGACY_NAME"] = APP_LEGACY_NAME
    app.config["PORT_MODE"] = "v32"
    app.config["LOXWEBSOCKET_AVAILABLE"] = port.LOXWEBSOCKET_AVAILABLE
    app.config["STARTUP_STATUS"] = port.startup_status()
    app.config["JSON_AS_ASCII"] = False
    if hasattr(app, "json"):
        app.json.ensure_ascii = False

    app.extensions["app_core"] = core
    app.extensions["runtime_context"] = core.runtime_context

    _register_blueprints(app)

    # Dedicated CCU-Jack MQTT discovery runtime. It is deliberately separate
    # from the regular gateway MQTT bridge and therefore cannot disturb it.
    try:
        from .services.openccu_mqtt import OpenCcuMqttRuntime
        from .services.openccu_rest import OpenCcuRestCache
        from .services import object_service as _object_service

        # XML-Gerätecache bewusst unabhängig von MQTT anlegen. So bleibt der
        # Explorer nutzbar, selbst wenn CCU-Jack oder paho-mqtt ausfällt.
        openccu_metadata = OpenCcuRestCache(core.load_config, app.logger)
        app.extensions["openccu_metadata_cache"] = openccu_metadata
        openccu_metadata.ensure_fresh()

        def _openccu_value(topic, value, timestamp):
            live_items = _object_service.record_live_value(
                "openccu", value, topic=topic, timestamp=timestamp, original_source="openccu", route_after_record=True
            )

            # Sicherheitsnetz fuer OpenCCU: Der Endpoint-Index kann direkt nach
            # Erstellen/Aktualisieren eines Objekts noch einen alten Stand
            # enthalten. Deshalb bei leerem Lookup das gespeicherte
            # openccu_topic einmal direkt gegen alle Objekte pruefen und den
            # zentralen Live-Cache per Objekt-ID aktualisieren.
            direct_updates = []
            if not live_items:
                normalized_topic = str(topic or "").strip()
                for item in _object_service.list_objects():
                    meta = dict(getattr(item, "meta", {}) or {})
                    semantic_source = str(meta.get("source") or meta.get("origin_source") or "").strip().lower()
                    stored_topic = str(meta.get("openccu_topic") or "").strip()
                    if semantic_source != "openccu" or not normalized_topic or stored_topic != normalized_topic:
                        continue
                    live = _object_service.update_object_live_value(
                        item.id,
                        value,
                        source="openccu",
                        endpoint="openccu.topic",
                        source_address=normalized_topic,
                        timestamp=timestamp,
                        status="aktiv",
                    )
                    if live:
                        direct_updates.append({"object": item.to_dict(), "live": live})
                live_items = direct_updates

            # OpenCCU ist die fachliche Quelle. Der separate CCU-Jack-Broker ist
            # nur der Eingangstransport. Dadurch darf das Objekt anschließend
            # an den normalen MQTT-Adapter des MP-Gateway weitergeleitet werden.
            # Direkte Fallback-Updates umgehen record_live_value(); nur diese
            # muessen deshalb hier noch explizit an den Router uebergeben werden.
            if direct_updates:
                core._dispatch_object_routes(
                    direct_updates, "openccu", topic, value,
                    metadata={"topic": topic, "gateway_origin": "openccu", "use_event_value": False},
                )

        openccu_runtime = OpenCcuMqttRuntime(core.load_config, app.logger, on_value=_openccu_value, metadata=openccu_metadata)
        app.extensions["openccu_mqtt_runtime"] = openccu_runtime
        openccu_runtime.start()
    except Exception:
        app.logger.exception("OpenCCU MQTT runtime could not be started")

    @app.context_processor
    def inject_app_identity():
        try:
            from app.update import UpdateManager
            update_sidebar = UpdateManager().sidebar_status()
        except Exception:
            update_sidebar = {
                "state": "unknown",
                "label": "Update noch nicht geprüft",
                "current_version": port.current_app_version(),
                "available_version": "",
                "checked_at": "",
            }
        return {
            "app_name": APP_NAME,
            "app_subtitle": APP_SUBTITLE,
            "app_legacy_name": APP_LEGACY_NAME,
            "app_version": port.current_app_version(),
            "update_sidebar": update_sidebar,
        }

    if "startup_status_route" not in app.view_functions:
        @app.route("/startup_status")
        def startup_status_route():
            return port.startup_status()

    return app
