"""Object manager 2.0 data model groundwork.

This module is intentionally passive. It prepares V33 data structures without
connecting them to routes, runtime state, config files, or existing mappings.
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


SUPPORTED_PROTOCOLS = {"mqtt", "loxone", "udp", "knx", "influx"}
SUPPORTED_DIRECTIONS = {"in", "out", "both"}


@dataclass
class ObjectFlags:
    """Planning flags for future object-centric workflows."""

    auto_create_mappings: bool = False
    sync_from_mappings: bool = False
    influx_enabled: bool = False
    test_mode: bool = False


@dataclass
class ObjectAdapter:
    """Protocol-specific endpoint attached to an object definition."""

    protocol: str
    direction: str = "both"
    address: str = ""
    json_key: str = ""
    value_type: str = "auto"
    enabled: bool = True
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectDefinition:
    """Object-centric description prepared for Object Manager V33."""

    id: str
    uuid: str = ""
    key: str = ""
    name: str = ""
    category: str = ""
    room: str = ""
    type: str = ""
    unit: str = ""
    enabled: bool = True
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    adapters: list[ObjectAdapter] = field(default_factory=list)
    flags: ObjectFlags = field(default_factory=ObjectFlags)


def normalize_object_id(value: str) -> str:
    """Normalize a future object id without enforcing a storage format yet."""
    return str(value or "").strip()


def new_object_uuid() -> str:
    """Create a stable internal object UUID."""
    return str(uuid4())


def is_supported_protocol(protocol: str) -> bool:
    return str(protocol or "").strip().lower() in SUPPORTED_PROTOCOLS


def is_supported_direction(direction: str) -> bool:
    return str(direction or "").strip().lower() in SUPPORTED_DIRECTIONS


def validate_adapter(adapter: ObjectAdapter) -> list[str]:
    """Return validation messages for a future adapter definition."""
    errors = []
    if not is_supported_protocol(adapter.protocol):
        errors.append(f"Unsupported protocol: {adapter.protocol}")
    if not is_supported_direction(adapter.direction):
        errors.append(f"Unsupported direction: {adapter.direction}")
    if adapter.enabled and not str(adapter.address or "").strip():
        errors.append("Enabled adapter requires an address")
    return errors


def validate_object_definition(definition: ObjectDefinition) -> list[str]:
    """Return validation messages without raising or mutating data."""
    errors = []
    if not normalize_object_id(definition.id):
        errors.append("Object id is required")
    for index, adapter in enumerate(definition.adapters):
        for message in validate_adapter(adapter):
            errors.append(f"Adapter {index}: {message}")
    return errors
