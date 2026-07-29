"""Core object model for MP-Gateway V33."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


SOURCE_TYPES = {"mqtt", "knx", "loxone", "udp"}
TARGET_TYPES = {"", "mqtt", "knx", "loxone", "udp", "influx"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_object_id() -> str:
    return f"obj_{uuid4().hex}"


@dataclass
class GatewayObject:
    """Central object definition stored in config/objects.json."""

    id: str = ""
    name: str = ""
    source_type: str = "mqtt"
    source_address: str = ""
    target_type: str = ""
    target_address: str = ""
    datatype: str = "auto"
    unit: str = ""
    enabled: bool = True
    influx_enabled: bool = False
    created_at: str = ""
    updated_at: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def uuid(self) -> str:
        return self.id

    @property
    def key(self) -> str:
        return self.id

    @property
    def type(self) -> str:
        return self.datatype

    @property
    def category(self) -> str:
        return str(self.meta.get("category", "") or "")

    @property
    def active(self) -> bool:
        return bool(self.enabled)

    @property
    def room(self) -> str:
        return str(self.meta.get("room", "") or "")

    @property
    def notes(self) -> str:
        return str(self.meta.get("notes", "") or "")

    @property
    def icon(self) -> str:
        return str(self.meta.get("icon", "") or "")

    @property
    def scaling(self) -> str:
        return str(self.meta.get("scaling", "") or "")

    @property
    def adapters(self) -> list[Any]:
        try:
            from app.services.object_adapter_engine import deserialize_adapter
        except ModuleNotFoundError:
            from services.object_adapter_engine import deserialize_adapter

        adapters = self.meta.get("adapters", {})
        if isinstance(adapters, dict):
            values = list(adapters.values())
        else:
            values = list(adapters or [])
        return [deserialize_adapter(adapter) if isinstance(adapter, dict) else adapter for adapter in values]

    @adapters.setter
    def adapters(self, value: list[Any]) -> None:
        adapters = {}
        for adapter in list(value or []):
            protocol = ""
            if isinstance(adapter, dict):
                protocol = str(adapter.get("protocol", "") or "").strip().lower()
            else:
                protocol = str(getattr(adapter, "protocol", "") or "").strip().lower()
            if protocol:
                adapters[protocol] = adapter
        self.meta["adapters"] = adapters

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "id": self.id,
            "name": self.name,
            "datatype": self.datatype,
            "unit": self.unit,
            "enabled": bool(self.enabled),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        for key, value in self.meta.items():
            if key == "adapters":
                raw_adapters = value if isinstance(value, dict) else {
                    str((adapter.get("protocol") if isinstance(adapter, dict) else getattr(adapter, "protocol", "")) or "").strip().lower(): adapter
                    for adapter in list(value or [])
                    if str((adapter.get("protocol") if isinstance(adapter, dict) else getattr(adapter, "protocol", "")) or "").strip()
                }
                for protocol, adapter in raw_adapters.items():
                    if protocol:
                        payload[protocol] = adapter.serialize() if hasattr(adapter, "serialize") else adapter
                continue
            if key not in payload:
                payload[key] = value
        payload.setdefault("notes", self.notes)
        return payload


def normalize_source_type(value: str) -> str:
    text = str(value or "").strip().lower()
    return text if text in SOURCE_TYPES else "mqtt"


def normalize_target_type(value: str) -> str:
    text = str(value or "").strip().lower()
    return text if text in TARGET_TYPES else ""


def object_name_from_address(address: str) -> str:
    text = str(address or "").strip().strip("/")
    if not text:
        return "Neues Objekt"
    chunk = text.split("/")[-1] or text
    chunk = chunk.replace("_", " ").replace("-", " ").strip()
    return " ".join(part.capitalize() for part in chunk.split()) or text
