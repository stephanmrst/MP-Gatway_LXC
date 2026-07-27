"""Passive V33 object adapter interface.

Adapters provide validation and serialization hooks only. They do not open
network connections and are not connected to routes or runtime state.
"""

from dataclasses import dataclass, field, fields
from typing import Any, ClassVar

try:
    from app.services.object_model import is_supported_direction
except ModuleNotFoundError:
    from services.object_model import is_supported_direction


ADAPTER_TYPES: dict[str, type["BaseAdapter"]] = {}


@dataclass
class BaseAdapter:
    """Common adapter interface for future object-centric protocol bindings."""

    enabled: bool = True
    direction: str = "both"
    datatype: str = "auto"

    protocol: ClassVar[str] = "base"

    def validate(self) -> list[str]:
        errors = []
        if not is_supported_direction(self.direction):
            errors.append(f"Unsupported direction: {self.direction}")
        if not str(self.datatype or "").strip():
            errors.append("Datatype is required")
        return errors

    def serialize(self) -> dict[str, Any]:
        payload = {"protocol": self.protocol}
        for field in fields(self):
            value = getattr(self, field.name)
            payload[field.name] = value
        payload["enabled"] = bool(payload.get("enabled", True))
        payload["direction"] = str(payload.get("direction") or "both")
        payload["datatype"] = str(payload.get("datatype") or "auto")
        return payload

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "BaseAdapter":
        values = {
            "enabled": bool(data.get("enabled", True)),
            "direction": str(data.get("direction", "both") or "both"),
            "datatype": str(data.get("datatype", data.get("value_type", "auto")) or "auto"),
        }
        for field in fields(cls):
            if field.name in values:
                continue
            if field.name in data:
                values[field.name] = data.get(field.name)
        return cls(**values)


@dataclass
class MQTTAdapter(BaseAdapter):
    protocol: ClassVar[str] = "mqtt"
    topic: str = ""
    qos: int = 0
    retain: bool = False
    json_key: str = ""
    source_broker: str = "Hauptbroker"
    targets: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "MQTTAdapter":
        payload = dict(data or {})
        payload["source_broker"] = str(payload.get("source_broker") or payload.get("broker") or "Hauptbroker").strip() or "Hauptbroker"
        targets = payload.get("targets")
        if not isinstance(targets, list):
            targets = []
        normalized = []
        for index, target in enumerate(targets):
            if not isinstance(target, dict):
                continue
            topic = str(target.get("topic") or "").strip()
            if not topic:
                continue
            try:
                qos = max(0, min(2, int(target.get("qos", 0) or 0)))
            except (TypeError, ValueError):
                qos = 0
            normalized.append({
                "id": str(target.get("id") or f"mqtt_target_{index+1}"),
                "enabled": bool(target.get("enabled", True)),
                "broker": str(target.get("broker") or "Hauptbroker").strip() or "Hauptbroker",
                "topic": topic,
                "qos": qos,
                "retain": bool(target.get("retain", False)),
            })
        # Migration: bisheriges einzelnes MQTT-Ausgangsziel auf Hauptbroker übernehmen.
        direction = str(payload.get("direction", "both") or "both").lower()
        legacy_topic = str(payload.get("topic") or "").strip()
        if not normalized and legacy_topic and direction in {"out", "both"}:
            normalized.append({
                "id": "mqtt_target_1", "enabled": bool(payload.get("enabled", True)),
                "broker": "Hauptbroker", "topic": legacy_topic,
                "qos": max(0, min(2, int(payload.get("qos", 0) or 0))),
                "retain": bool(payload.get("retain", False)),
            })
        payload["targets"] = normalized
        return super().deserialize(payload)


@dataclass
class LoxoneAdapter(BaseAdapter):
    protocol: ClassVar[str] = "loxone"
    uuid: str = ""
    io_address: str = ""
    control_type: str = ""
    visu_name: str = ""
    room: str = ""
    unit: str = ""
    source_uuid: str = ""
    source_io: str = ""
    source_name: str = ""
    source_room: str = ""
    source_category: str = ""
    source_enabled: bool = True
    target_uuid: str = ""
    target_name: str = ""
    target_room: str = ""
    target_category: str = ""
    target_type: str = ""
    target_enabled: bool = False
    active: bool = False

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "LoxoneAdapter":
        payload = dict(data or {})
        payload.setdefault("source_uuid", payload.get("uuid", ""))
        payload.setdefault("source_io", payload.get("source_io", payload.get("io_address", "")))
        payload.setdefault("source_name", payload.get("source_name", payload.get("visu_name", payload.get("name", ""))))
        payload.setdefault("source_room", payload.get("source_room", payload.get("room", "")))
        payload.setdefault("source_category", payload.get("source_category", payload.get("control_type", payload.get("category", payload.get("type", "")))))
        if "source_enabled" not in payload and any(
            str(payload.get(field, "") or "").strip()
            for field in ("source_uuid", "source_io", "source_name", "uuid", "io_address", "visu_name")
        ):
            payload["source_enabled"] = payload.get("enabled", True)
        payload.setdefault("target_uuid", payload.get("target_uuid", ""))
        payload.setdefault("target_name", payload.get("target_name", ""))
        payload.setdefault("target_room", payload.get("target_room", payload.get("room", "")))
        payload.setdefault("target_category", payload.get("target_category", payload.get("category", "")))
        payload.setdefault("target_type", payload.get("target_type", payload.get("control_type", payload.get("type", ""))))
        if "target_enabled" not in payload and "active" in payload:
            payload["target_enabled"] = payload.get("active", False)
        if "target_enabled" not in payload and payload.get("target_uuid"):
            payload["target_enabled"] = payload.get("enabled", True)
        if "active" not in payload and "target_enabled" in payload:
            payload["active"] = payload.get("target_enabled", False)
        adapter = super().deserialize(payload)
        if not str(adapter.source_uuid or "").strip():
            adapter.source_uuid = str(adapter.uuid or "").strip()
        if not str(adapter.source_io or "").strip():
            adapter.source_io = str(adapter.io_address or "").strip()
        if not str(adapter.source_name or "").strip():
            adapter.source_name = str(adapter.visu_name or "").strip()
        if not str(adapter.source_room or "").strip():
            adapter.source_room = str(adapter.room or "").strip()
        if not str(adapter.source_category or "").strip():
            adapter.source_category = str(adapter.control_type or "").strip() or str(data.get("category", "") or "").strip() or str(data.get("type", "") or "").strip()
        if not str(adapter.target_room or "").strip():
            adapter.target_room = str(adapter.room or "").strip()
        if not str(adapter.target_category or "").strip():
            adapter.target_category = str(data.get("category", "") or "").strip()
        if not str(adapter.target_type or "").strip():
            adapter.target_type = str(adapter.control_type or "").strip() or str(data.get("type", "") or "").strip()
        if str(adapter.uuid or "").strip() == "" and str(adapter.source_uuid or "").strip():
            adapter.uuid = str(adapter.source_uuid or "").strip()
        if str(adapter.io_address or "").strip() == "" and str(adapter.source_io or "").strip():
            adapter.io_address = str(adapter.source_io or "").strip()
        if str(adapter.visu_name or "").strip() == "" and str(adapter.source_name or "").strip():
            adapter.visu_name = str(adapter.source_name or "").strip()
        if str(adapter.room or "").strip() == "" and str(adapter.source_room or "").strip():
            adapter.room = str(adapter.source_room or "").strip()
        if str(adapter.control_type or "").strip() == "" and str(adapter.source_category or "").strip():
            adapter.control_type = str(adapter.source_category or "").strip()
        if "source_enabled" in payload:
            adapter.source_enabled = bool(payload.get("source_enabled", False))
        if "target_enabled" in payload:
            adapter.target_enabled = bool(payload.get("target_enabled", False))
        adapter.active = bool(getattr(adapter, "active", False) or adapter.target_enabled)
        if not adapter.source_enabled and (adapter.source_uuid or adapter.source_io or adapter.source_name):
            adapter.source_enabled = True
        if not str(adapter.target_uuid or "").strip():
            adapter.target_enabled = False
            adapter.active = bool(adapter.source_enabled)
        if not adapter.target_enabled and str(adapter.target_uuid or "").strip():
            adapter.target_enabled = True
            adapter.active = True
        return adapter


@dataclass
class UDPAdapter(BaseAdapter):
    protocol: ClassVar[str] = "udp"
    source_enabled: bool = False
    source_host: str = ""
    source_port: str = ""
    listen_port: str = ""
    source_payload_mode: str = "value"
    source_topic: str = ""
    source_json_path: str = ""
    target_enabled: bool = False
    target_host: str = ""
    target_ip: str = ""
    target_port: str = ""
    target_payload_mode: str = "topic_value"
    udp_topic: str = ""
    format: str = ""
    payload_mode: str = "topic_value"

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "UDPAdapter":
        payload = dict(data or {})
        direction = str(payload.get("direction", "both") or "both").strip().lower()
        if "source_enabled" not in payload:
            payload["source_enabled"] = direction in {"in", "both"} and any(
                str(payload.get(field, "") or "").strip()
                for field in ("listen_port", "source_topic", "source_json_path", "source_host", "source_port")
            )
        if "target_enabled" not in payload:
            payload["target_enabled"] = direction in {"out", "both"} and any(
                str(payload.get(field, "") or "").strip()
                for field in ("target_host", "target_ip", "target_port", "udp_topic", "format")
            )
        if "source_payload_mode" not in payload:
            payload["source_payload_mode"] = payload.get("source_payload_mode") or payload.get("payload_mode") or "value"
        if "target_payload_mode" not in payload:
            payload["target_payload_mode"] = payload.get("target_payload_mode") or payload.get("payload_mode") or "topic_value"
        if "udp_topic" not in payload:
            legacy_format = str(payload.get("format", "") or "").strip()
            if legacy_format and legacy_format not in {"text", "topic_value", "value_only", "json", "json_number", "value"}:
                payload["udp_topic"] = legacy_format
        if not payload.get("udp_topic") and payload.get("target_topic"):
            payload["udp_topic"] = payload.get("target_topic")
        if not payload.get("target_host") and payload.get("target_ip"):
            payload["target_host"] = payload.get("target_ip")
        if not payload.get("target_ip") and payload.get("target_host"):
            payload["target_ip"] = payload.get("target_host")
        if not payload.get("payload_mode") and payload.get("target_payload_mode"):
            payload["payload_mode"] = payload.get("target_payload_mode")
        adapter = super().deserialize(payload)
        if not str(adapter.target_host or "").strip() and str(adapter.target_ip or "").strip():
            adapter.target_host = str(adapter.target_ip or "").strip()
        if not str(adapter.target_ip or "").strip() and str(adapter.target_host or "").strip():
            adapter.target_ip = str(adapter.target_host or "").strip()
        if not str(adapter.target_payload_mode or "").strip():
            adapter.target_payload_mode = str(adapter.payload_mode or "topic_value").strip() or "topic_value"
        if not str(adapter.payload_mode or "").strip():
            adapter.payload_mode = str(adapter.target_payload_mode or "topic_value").strip() or "topic_value"
        if not str(adapter.source_payload_mode or "").strip():
            adapter.source_payload_mode = "value"
        if not str(adapter.source_topic or "").strip() and str(adapter.udp_topic or "").strip():
            adapter.target_enabled = True
        if not str(adapter.source_topic or "").strip() and str(adapter.format or "").strip():
            legacy_format = str(adapter.format or "").strip()
            if legacy_format not in {"text", "topic_value", "value_only", "json", "json_number", "value"}:
                adapter.source_topic = legacy_format
        if not str(adapter.udp_topic or "").strip() and str(adapter.format or "").strip():
            legacy_format = str(adapter.format or "").strip()
            if legacy_format not in {"text", "topic_value", "value_only", "json", "json_number", "value"}:
                adapter.udp_topic = legacy_format
        if direction == "in" and not adapter.source_enabled:
            adapter.source_enabled = True
        if direction == "out" and not adapter.target_enabled:
            adapter.target_enabled = True
        if direction == "both":
            if any(str(getattr(adapter, field, "") or "").strip() for field in ("listen_port", "source_topic", "source_json_path", "source_host", "source_port")):
                adapter.source_enabled = True
            if any(str(getattr(adapter, field, "") or "").strip() for field in ("target_host", "target_ip", "target_port", "udp_topic")):
                adapter.target_enabled = True
        if adapter.source_enabled and adapter.target_enabled:
            adapter.direction = "both"
        elif adapter.source_enabled:
            adapter.direction = "in"
        elif adapter.target_enabled:
            adapter.direction = "out"
        adapter.active = bool(adapter.source_enabled or adapter.target_enabled or adapter.enabled)
        return adapter


@dataclass
class KNXAdapter(BaseAdapter):
    protocol: ClassVar[str] = "knx"
    group_address: str = ""
    dpt: str = ""

    def validate(self) -> list[str]:
        errors = super().validate()
        if not str(self.group_address or "").strip():
            errors.append("KNX: Gruppenadresse fehlt")
        if not str(self.dpt or "").strip():
            errors.append("KNX: DPT fehlt")
        return errors


@dataclass
class InfluxAdapter(BaseAdapter):
    protocol: ClassVar[str] = "influx"
    bucket: str = ""
    measurement: str = ""
    field: str = ""
    topic: str = ""
    tags: str = ""


def _register(adapter_cls: type[BaseAdapter]) -> type[BaseAdapter]:
    ADAPTER_TYPES[adapter_cls.protocol] = adapter_cls
    return adapter_cls


for _adapter_cls in (MQTTAdapter, LoxoneAdapter, UDPAdapter, KNXAdapter, InfluxAdapter):
    _register(_adapter_cls)


def deserialize_adapter(data: dict[str, Any]) -> BaseAdapter:
    protocol = str(data.get("protocol", "") or "").strip().lower()
    adapter_cls = ADAPTER_TYPES.get(protocol, BaseAdapter)
    return adapter_cls.deserialize(data)


def adapter_from_form(protocol: str, form_data: Any) -> BaseAdapter:
    """Build a passive adapter instance from an adapter editor form."""
    protocol = str(protocol or "").strip().lower()
    payload = {
        "protocol": protocol,
        "enabled": True if protocol == "loxone" else ("enabled" in form_data),
        "direction": form_data.get("direction", "both"),
        "datatype": form_data.get("datatype", "auto"),
    }
    adapter_cls = ADAPTER_TYPES.get(protocol, BaseAdapter)
    for field in fields(adapter_cls):
        if field.name in payload:
            continue
        if field.name in form_data:
            if protocol == "loxone" and field.name == "target_enabled":
                payload[field.name] = field.name in form_data
            else:
                payload[field.name] = form_data.get(field.name, "")
    if protocol == "mqtt":
        payload["retain"] = "retain" in form_data
        payload["source_broker"] = str(form_data.get("source_broker", "Hauptbroker") or "Hauptbroker").strip() or "Hauptbroker"
        try:
            payload["qos"] = int(form_data.get("qos", 0) or 0)
        except (TypeError, ValueError):
            payload["qos"] = 0
        targets = []
        broker_values = form_data.getlist("mqtt_target_broker[]") if hasattr(form_data, "getlist") else []
        topic_values = form_data.getlist("mqtt_target_topic[]") if hasattr(form_data, "getlist") else []
        qos_values = form_data.getlist("mqtt_target_qos[]") if hasattr(form_data, "getlist") else []
        retain_values = set(form_data.getlist("mqtt_target_retain[]")) if hasattr(form_data, "getlist") else set()
        enabled_values = set(form_data.getlist("mqtt_target_enabled[]")) if hasattr(form_data, "getlist") else set()
        for index, topic_value in enumerate(topic_values):
            topic_value = str(topic_value or "").strip()
            if not topic_value:
                continue
            try:
                target_qos = max(0, min(2, int(qos_values[index] if index < len(qos_values) else 0)))
            except (TypeError, ValueError):
                target_qos = 0
            key = str(index)
            targets.append({
                "id": f"mqtt_target_{index+1}",
                "enabled": key in enabled_values,
                "broker": str(broker_values[index] if index < len(broker_values) else "Hauptbroker").strip() or "Hauptbroker",
                "topic": topic_value,
                "qos": target_qos,
                "retain": key in retain_values,
            })
        payload["targets"] = targets
    if protocol == "loxone" and "target_enabled" not in payload:
        payload["target_enabled"] = "target_enabled" in form_data
    if protocol == "udp":
        # Checkbox fields are absent from submitted form data when unchecked.
        # Normalize them explicitly instead of leaving stale values or strings.
        source_enabled = "source_enabled" in form_data
        target_enabled = "target_enabled" in form_data
        payload["source_enabled"] = source_enabled
        payload["target_enabled"] = target_enabled
        payload["enabled"] = bool(source_enabled or target_enabled)
        payload["direction"] = (
            "both" if source_enabled and target_enabled
            else "in" if source_enabled
            else "out" if target_enabled
            else "both"
        )
        target_host = str(payload.get("target_host") or payload.get("target_ip") or "").strip()
        payload["target_host"] = target_host
        payload["target_ip"] = target_host
        target_mode = str(payload.get("target_payload_mode") or payload.get("payload_mode") or "topic_value").strip() or "topic_value"
        payload["target_payload_mode"] = target_mode
        payload["payload_mode"] = target_mode
    return deserialize_adapter(payload)


def adapter_template_name(protocol: str) -> str:
    protocol = str(protocol or "").strip().lower()
    if protocol not in ADAPTER_TYPES:
        return "objects_v33/adapters/base.html"
    return f"objects_v33/adapters/{protocol}.html"
