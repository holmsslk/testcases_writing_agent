"""Validation helpers shared by MVP dataclass schemas."""

from collections.abc import Iterable
from dataclasses import is_dataclass


def ensure_non_empty_str(value: str, field_name: str) -> str:
    """Validate and normalize a non-empty string field."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str, got {type(value).__name__}")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def ensure_str_list(value: object, field_name: str) -> list[str]:
    """Validate list[str] fields and normalize item whitespace."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be list[str]")
    normalized: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str):
            raise TypeError(f"{field_name}[{idx}] must be str")
        stripped = item.strip()
        if not stripped:
            raise ValueError(f"{field_name}[{idx}] must not be empty")
        normalized.append(stripped)
    return normalized


def ensure_in_set(value: str, field_name: str, allowed: set[str]) -> str:
    """Validate enum-like string fields."""
    normalized = ensure_non_empty_str(value, field_name).lower()
    if normalized not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {allowed_values}")
    return normalized


def ensure_bool(value: object, field_name: str) -> bool:
    """Validate boolean fields."""
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be bool")
    return value


def ensure_dict(value: object, field_name: str) -> dict:
    """Validate dictionary fields."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError(f"{field_name} must be dict")
    return value


def ensure_dataclass_list(
    value: object,
    field_name: str,
    expected_type: type,
) -> list:
    """Validate list of dataclass instances."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be list[{expected_type.__name__}]")
    validated = []
    for idx, item in enumerate(value):
        if not isinstance(item, expected_type) or not is_dataclass(item):
            raise TypeError(
                f"{field_name}[{idx}] must be {expected_type.__name__} dataclass instance"
            )
        validated.append(item)
    return validated


def ensure_iterable_of_str(
    value: object,
    field_name: str,
) -> list[str]:
    """Accept any non-string iterable of strings and return list[str]."""
    if value is None:
        return []
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be an iterable of strings")
    return ensure_str_list(list(value), field_name)
