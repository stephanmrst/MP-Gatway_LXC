"""Passive routing preview for Object Manager V33.

This module only describes routes that could be generated later. It does not
write mapping files and does not connect to runtime state.
"""

from typing import Any


PROTOCOL_LABELS = {
    "mqtt": "MQTT",
    "udp": "UDP",
    "knx": "KNX",
    "loxone": "Loxone",
    "influx": "Influx",
}


PREVIEW_ROUTE_PAIRS = (
    ("mqtt", "loxone"),
    ("mqtt", "knx"),
    ("mqtt", "udp"),
    ("mqtt", "influx"),
    ("loxone", "knx"),
    ("knx", "mqtt"),
    ("knx", "loxone"),
    ("knx", "influx"),
    ("udp", "mqtt"),
    ("udp", "knx"),
    ("udp", "influx"),
    ("loxone", "mqtt"),
    ("loxone", "influx"),
)


def _protocol(adapter: Any) -> str:
    return str(getattr(adapter, "protocol", "") or "").strip().lower()


def _direction(adapter: Any) -> str:
    return str(getattr(adapter, "direction", "both") or "both").strip().lower()


def _is_enabled(adapter: Any) -> bool:
    return bool(getattr(adapter, "enabled", False))


def _can_source(adapter: Any) -> bool:
    return _protocol(adapter) != "influx" and _direction(adapter) in {"in", "both"}


def _can_target(adapter: Any) -> bool:
    return _direction(adapter) in {"out", "both"}


def _label(protocol: str) -> str:
    return PROTOCOL_LABELS.get(protocol, protocol.upper())


def build_object_routing_preview(object_def: Any) -> list[dict[str, str]]:
    """Build passive V33 routing preview entries for an object definition."""
    try:
        from app.services.object_service import build_generated_route_entries
    except ModuleNotFoundError:
        from services.object_service import build_generated_route_entries

    generated = build_generated_route_entries(object_def)
    if generated:
        return generated

    adapters = {
        protocol: adapter
        for adapter in getattr(object_def, "adapters", [])
        if (protocol := _protocol(adapter)) and _is_enabled(adapter)
    }
    preview = []
    for source, target in PREVIEW_ROUTE_PAIRS:
        source_adapter = adapters.get(source)
        target_adapter = adapters.get(target)
        if not source_adapter or not target_adapter:
            continue
        if not _can_source(source_adapter) or not _can_target(target_adapter):
            continue
        preview.append(
            {
                "source": _label(source),
                "target": _label(target),
                "direction": f"{_label(source)} -> {_label(target)}",
                "status": "Vorschau",
            }
        )
    return preview
