import json
from enum import IntEnum
from typing import Any, Dict, Type, TypeVar

from pydantic import BaseModel, ValidationError, TypeAdapter

from app.models.models import CUSTOM_TYPE_REGISTRY


class CustomTypeValidationError(Exception):
    """Raised when JSON cannot be validated into the requested custom type."""


E = TypeVar("E", bound=IntEnum)


def _validate_int_enum(enum_cls: Type[E], raw: Any) -> E:
    """Convert various JSON-ish inputs into an IntEnum instance."""
    if isinstance(raw, enum_cls):
        return raw

    value = raw

    if isinstance(value, (bytes, bytearray)):
        value = value.decode()

    if isinstance(value, str):
        s = value.strip()
        try:
            decoded = json.loads(s)
            if not isinstance(decoded, (dict, list)):
                value = decoded
            else:
                value = s  # keep as string if it's a complex type
        except json.JSONDecodeError:
            value = s

    if isinstance(value, int):
        try:
            return enum_cls(value)
        except ValueError:
            pass

    if isinstance(value, str) and value.isdigit():
        try:
            return enum_cls(int(value))
        except ValueError:
            pass

    if isinstance(value, str):
        try:
            return enum_cls[value]
        except KeyError:
            pass

        for member in enum_cls:
            if str(member.value) == value:
                return member

    valid = ", ".join(f"{m.name}={m.value!r}" for m in enum_cls)
    raise CustomTypeValidationError(
        f"Invalid value for {enum_cls.__name__}: {raw!r}. Allowed: {valid}"
    )


def validate_custom_type(
    type_name: str,
    raw_json: Any,
    *,
    strict: bool = False,
) -> Any:
    """
    Validate arbitrary JSON-like data into a custom type from CUSTOM_TYPE_REGISTRY.

    - type_name: key in CUSTOM_TYPE_REGISTRY (e.g. "ContentStrategy")
    - raw_json: JSON string, bytes, or already-parsed Python value
    - strict: passed through to Pydantic's strict validation
    """
    if type_name not in CUSTOM_TYPE_REGISTRY:
        available = ", ".join(sorted(CUSTOM_TYPE_REGISTRY.keys()))
        raise CustomTypeValidationError(
            f"Unknown custom type '{type_name}'. Available types: {available}"
        )

    type_cls = CUSTOM_TYPE_REGISTRY[type_name]

    if raw_json is None or (isinstance(raw_json, str) and not raw_json.strip()):
        raise CustomTypeValidationError(
            f"No data provided for custom type '{type_name}'"
        )

    if isinstance(type_cls, type) and issubclass(type_cls, BaseModel):
        try:
            if isinstance(raw_json, (str, bytes, bytearray)):
                # Fast JSON path
                return type_cls.model_validate_json(raw_json, strict=strict)
            else:
                # Already a Python dict/list/etc.
                return type_cls.model_validate(raw_json, strict=strict)
        except ValidationError as e:
            # Wrap for easier handling upstream
            raise CustomTypeValidationError(
                f"Failed to validate data as {type_name}: {e}"
            ) from e

    if isinstance(type_cls, type) and issubclass(type_cls, IntEnum):
        return _validate_int_enum(type_cls, raw_json)

    adapter = TypeAdapter(type_cls)
    try:
        if isinstance(raw_json, (str, bytes, bytearray)):
            return adapter.validate_json(raw_json, strict=strict)
        else:
            return adapter.validate_python(raw_json, strict=strict)
    except ValidationError as e:
        raise CustomTypeValidationError(
            f"Failed to validate data as {type_name} via TypeAdapter: {e}"
        ) from e
