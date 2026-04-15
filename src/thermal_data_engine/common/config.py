import copy
import os
from dataclasses import fields, is_dataclass
from typing import Any, Dict, Type, TypeVar

import yaml

from .models import EdgeConfig, PolicyConfig, TrackingConfig, UploadConfig, VisionRequestConfig

T = TypeVar("T")


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _dataclass_to_dict(instance: Any) -> Dict[str, Any]:
    result = {}
    for item in fields(instance):
        value = getattr(instance, item.name)
        if is_dataclass(value):
            result[item.name] = _dataclass_to_dict(value)
        else:
            result[item.name] = value
    return result


def _build_dataclass(cls: Type[T], payload: Dict[str, Any]) -> T:
    kwargs = {}
    for item in fields(cls):
        if item.name not in payload:
            continue
        value = payload[item.name]
        nested_type = item.type
        if hasattr(nested_type, "__dataclass_fields__") and isinstance(value, dict):
            kwargs[item.name] = _build_dataclass(nested_type, value)
        else:
            kwargs[item.name] = value
    return cls(**kwargs)


def _load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("CONFIG_MUST_BE_MAPPING: {}".format(path))
    return data


def load_edge_config(path: str, overrides: Dict[str, Any] = None) -> EdgeConfig:
    base = _dataclass_to_dict(EdgeConfig())
    loaded = _load_yaml(path)
    merged = _deep_merge(base, loaded)
    if overrides:
        merged = _deep_merge(merged, overrides)
    config = _build_dataclass(EdgeConfig, merged)
    config.output_root = os.path.expanduser(config.output_root)
    if config.upload.local_root:
        config.upload.local_root = os.path.expanduser(config.upload.local_root)
    return config


def load_policy_config(path: str, overrides: Dict[str, Any] = None) -> PolicyConfig:
    base = _dataclass_to_dict(PolicyConfig())
    loaded = _load_yaml(path)
    merged = _deep_merge(base, loaded)
    if overrides:
        merged = _deep_merge(merged, overrides)
    return _build_dataclass(PolicyConfig, merged)


__all__ = [
    "EdgeConfig",
    "PolicyConfig",
    "TrackingConfig",
    "UploadConfig",
    "VisionRequestConfig",
    "load_edge_config",
    "load_policy_config",
]
