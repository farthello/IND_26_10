"""Capture function calls only while a runner explicitly enables recording."""

from contextvars import ContextVar
from functools import wraps
from inspect import signature
from pathlib import Path
import math

import ifcopenshell
import numpy as np

ACTIVE_RECORDS = ContextVar("daylight_records", default=None)


def json_value(value):
    if isinstance(value, ifcopenshell.entity_instance):
        return {"id": value.id(), "type": value.is_a(),
                "global_id": getattr(value, "GlobalId", None),
                "name": getattr(value, "Name", None)}
    if isinstance(value, ifcopenshell.file):
        return {"type": "IfcModel", "schema": value.schema}
    if isinstance(value, np.ndarray):
        return json_value(value.tolist())
    if isinstance(value, np.generic):
        return json_value(value.item())
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return {"non_finite": str(value)}
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if callable(value):
        return {"callback": getattr(value, "__name__", type(value).__name__)}
    if isinstance(value, ifcopenshell.geom.settings):
        return {"type": "geometry_settings", "use_world_coords": value.get(value.USE_WORLD_COORDS)}
    raise TypeError(f"Unsupported recorded value: {type(value).__name__}")


def recorded(function):
    parameters = signature(function)

    @wraps(function)
    def wrapper(*args, **kwargs):
        records = ACTIVE_RECORDS.get()
        if records is None:
            return function(*args, **kwargs)
        bound = parameters.bind(*args, **kwargs)
        bound.apply_defaults()
        calls = records[function.__name__]["calls"]
        call = {"call_index": len(calls) + 1, "inputs": json_value(bound.arguments)}
        calls.append(call)
        try:
            result = function(*args, **kwargs)
            call.update(status="success", output=json_value(result))
            return result
        except Exception as error:
            call.update(status="error", error={"type": type(error).__name__, "message": str(error)})
            raise

    return wrapper
