"""Deprecated passive Object Manager V33 registry.

DEPRECATED: Production Object Manager V33 uses app.services.object_service and
config/objects.json. This module is kept only to read/migrate old passive
experiments from data/objects_v33.json and must not be wired into active routes.
"""

import json
import os
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

try:
    from app.services.object_adapter_engine import BaseAdapter, deserialize_adapter
    from app.services.object_model import (
        ObjectAdapter,
        ObjectDefinition,
        ObjectFlags,
        new_object_uuid,
        normalize_object_id,
        validate_object_definition,
    )
except ModuleNotFoundError:
    from services.object_adapter_engine import BaseAdapter, deserialize_adapter
    from services.object_model import (
        ObjectAdapter,
        ObjectDefinition,
        ObjectFlags,
        new_object_uuid,
        normalize_object_id,
        validate_object_definition,
    )


APP_ROOT = Path(os.environ.get("MQTT2LOX_APP_ROOT", Path.cwd()))
DATA_DIR = Path(os.environ.get("MQTT2LOX_DATA_DIR", APP_ROOT / "data"))
OBJECTS_FILE = DATA_DIR / "objects_v33.json"
DEPRECATED = True


def _normalize_key(value: str) -> str:
    return normalize_object_id(value)


def _ensure_identity(data: dict[str, Any]) -> tuple[str, str, str]:
    legacy_id = normalize_object_id(data.get("id", ""))
    key = _normalize_key(data.get("key", "")) or legacy_id
    object_uuid = str(data.get("uuid", "") or "").strip()
    if not object_uuid:
        object_uuid = str(uuid5(NAMESPACE_URL, f"mqtt2lox-v33-object:{key}")) if key else new_object_uuid()
    key = key or object_uuid
    object_id = legacy_id or key
    return object_uuid, key, object_id


def _adapter_from_dict(data: dict[str, Any]) -> ObjectAdapter:
    if "datatype" in data:
        return deserialize_adapter(data)
    return ObjectAdapter(
        protocol=str(data.get("protocol", "") or ""),
        direction=str(data.get("direction", "both") or "both"),
        address=str(data.get("address", "") or ""),
        json_key=str(data.get("json_key", "") or ""),
        value_type=str(data.get("value_type", data.get("datatype", "auto")) or "auto"),
        enabled=bool(data.get("enabled", True)),
        meta=dict(data.get("meta") or {}),
    )


def _adapter_to_dict(adapter: ObjectAdapter | BaseAdapter) -> dict[str, Any]:
    if hasattr(adapter, "serialize"):
        return adapter.serialize()
    return {
        "protocol": str(adapter.protocol or ""),
        "direction": str(adapter.direction or "both"),
        "address": str(adapter.address or ""),
        "json_key": str(adapter.json_key or ""),
        "value_type": str(adapter.value_type or "auto"),
        "enabled": bool(adapter.enabled),
        "meta": dict(adapter.meta or {}),
    }


def _flags_from_dict(data: dict[str, Any]) -> ObjectFlags:
    return ObjectFlags(
        auto_create_mappings=bool(data.get("auto_create_mappings", False)),
        sync_from_mappings=bool(data.get("sync_from_mappings", False)),
        influx_enabled=bool(data.get("influx_enabled", False)),
        test_mode=bool(data.get("test_mode", False)),
    )


def _object_from_dict(data: dict[str, Any]) -> ObjectDefinition:
    adapters = [
        _adapter_from_dict(adapter)
        for adapter in data.get("adapters", [])
        if isinstance(adapter, dict)
    ]
    flags_data = data.get("flags") if isinstance(data.get("flags"), dict) else {}
    tags = data.get("tags") if isinstance(data.get("tags"), list) else []
    object_uuid, key, object_id = _ensure_identity(data)
    return ObjectDefinition(
        id=object_id,
        uuid=object_uuid,
        key=key,
        name=str(data.get("name", "") or ""),
        category=str(data.get("category", "") or ""),
        room=str(data.get("room", "") or ""),
        type=str(data.get("type", "") or ""),
        unit=str(data.get("unit", "") or ""),
        enabled=bool(data.get("enabled", True)),
        notes=str(data.get("notes", "") or ""),
        tags=[str(tag) for tag in tags],
        adapters=adapters,
        flags=_flags_from_dict(flags_data),
    )


def _object_to_dict(object_def: ObjectDefinition) -> dict[str, Any]:
    object_uuid = str(object_def.uuid or "").strip() or new_object_uuid()
    key = _normalize_key(object_def.key) or normalize_object_id(object_def.id) or object_uuid
    object_id = normalize_object_id(object_def.id) or key
    return {
        "id": object_id,
        "uuid": object_uuid,
        "key": key,
        "name": str(object_def.name or ""),
        "category": str(object_def.category or ""),
        "room": str(object_def.room or ""),
        "type": str(object_def.type or ""),
        "unit": str(object_def.unit or ""),
        "enabled": bool(object_def.enabled),
        "notes": str(object_def.notes or ""),
        "tags": [str(tag) for tag in object_def.tags],
        "adapters": [_adapter_to_dict(adapter) for adapter in object_def.adapters],
        "flags": {
            "auto_create_mappings": bool(object_def.flags.auto_create_mappings),
            "sync_from_mappings": bool(object_def.flags.sync_from_mappings),
            "influx_enabled": bool(object_def.flags.influx_enabled),
            "test_mode": bool(object_def.flags.test_mode),
        },
    }


def load_objects() -> list[ObjectDefinition]:
    """Load V33 objects. Missing files return an empty list."""
    if not OBJECTS_FILE.exists():
        return []
    try:
        with OBJECTS_FILE.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return []

    items = raw.get("objects", raw) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return []
    return [_object_from_dict(item) for item in items if isinstance(item, dict)]


def save_objects(objects: list[ObjectDefinition]) -> None:
    """Deprecated legacy persist helper for data/objects_v33.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"objects": [_object_to_dict(item) for item in objects]}
    with OBJECTS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def list_objects() -> list[ObjectDefinition]:
    return load_objects()


def get_object(object_id: str) -> ObjectDefinition | None:
    normalized_id = normalize_object_id(object_id)
    for item in load_objects():
        if normalized_id in {
            normalize_object_id(item.uuid),
            normalize_object_id(item.key),
            normalize_object_id(item.id),
        }:
            return item
    return None


def upsert_object(object_def: ObjectDefinition) -> ObjectDefinition:
    if not str(object_def.uuid or "").strip():
        object_def.uuid = new_object_uuid()
    if not _normalize_key(object_def.key):
        object_def.key = normalize_object_id(object_def.id) or object_def.uuid
    if not normalize_object_id(object_def.id):
        object_def.id = object_def.key

    errors = validate_object(object_def)
    if errors:
        raise ValueError("; ".join(errors))

    normalized_uuid = normalize_object_id(object_def.uuid)
    objects = load_objects()
    for index, item in enumerate(objects):
        if normalize_object_id(item.uuid) == normalized_uuid:
            objects[index] = object_def
            save_objects(objects)
            return object_def

    objects.append(object_def)
    save_objects(objects)
    return object_def


def delete_object(object_id: str) -> bool:
    normalized_id = normalize_object_id(object_id)
    objects = load_objects()
    remaining = [
        item
        for item in objects
        if normalized_id
        not in {
            normalize_object_id(item.uuid),
            normalize_object_id(item.key),
            normalize_object_id(item.id),
        }
    ]
    if len(remaining) == len(objects):
        return False
    save_objects(remaining)
    return True


def validate_object(object_def: ObjectDefinition) -> list[str]:
    errors = []
    if not normalize_object_id(object_def.uuid):
        errors.append("Object uuid is required")
    if not _normalize_key(object_def.key):
        errors.append("Object key is required")
    adapters = object_def.adapters
    object_def.adapters = [
        adapter for adapter in adapters if not hasattr(adapter, "serialize")
    ]
    try:
        errors.extend(validate_object_definition(object_def))
    finally:
        object_def.adapters = adapters

    for index, adapter in enumerate(adapters):
        if hasattr(adapter, "validate"):
            for message in adapter.validate():
                errors.append(f"Adapter {index}: {message}")
    return errors
