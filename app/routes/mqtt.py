"""MQTT routes.

These routes delegate to the app core handlers during the migration.
"""

from flask import Blueprint, current_app, redirect


bp = Blueprint("mqtt", __name__)


def _core():
    return current_app.extensions["app_core"]


@bp.route("/mqtt")
def mqtt_hub():
    # Legacy-Hub entfernt: direkter Einstieg in den MQTT Explorer.
    return redirect("/monitor")


@bp.route("/monitor")
def monitor():
    return _core().monitor()


@bp.route("/monitor_data")
def monitor_data():
    return _core().monitor_data()


@bp.route("/monitor_settings")
def monitor_settings():
    return _core().monitor_settings()


@bp.route("/monitor_topic_config")
def monitor_topic_config():
    return _core().monitor_topic_config()


@bp.route("/monitor/influx_topic", methods=["POST"])
def monitor_influx_topic():
    return _core().monitor_influx_topic()


@bp.route("/monitor/influx_json_key", methods=["POST"])
def monitor_influx_json_key():
    return _core().monitor_influx_json_key()


@bp.route("/monitor/influx_json_key_type", methods=["POST"])
def monitor_influx_json_key_type():
    return _core().monitor_influx_json_key_type()


@bp.route("/monitor/favorite", methods=["POST"])
def monitor_favorite():
    return _core().monitor_favorite()


@bp.route("/monitor/alias", methods=["POST"])
def monitor_alias():
    return _core().monitor_alias()


@bp.route("/topics")
def topics():
    return _core().topics()


@bp.route("/topics_data")
def topics_data():
    return _core().topics_data()


@bp.route("/topics/save", methods=["POST"])
def topics_save():
    return _core().topics_save()


@bp.route("/topics2")
def topics2_page():
    return _core().topics2_page()


@bp.route("/topics2/data")
def topics2_data():
    return _core().topics2_data()


@bp.route("/topics2/save", methods=["POST"])
def topics2_save():
    return _core().topics2_save()


@bp.route("/mqtt_brokers")
def mqtt_brokers_page():
    return _core().mqtt_brokers_page()


@bp.route("/mqtt_brokers/save", methods=["POST"])
def mqtt_brokers_save():
    return _core().mqtt_brokers_save()


@bp.route("/test/mqtt_broker/<int:index>", methods=["POST"])
def test_mqtt_broker(index):
    return _core().test_mqtt_broker(index)
