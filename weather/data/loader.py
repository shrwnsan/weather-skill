"""
Data loader for weather/data/*.json shared data files.

Uses importlib.resources so it works in editable installs, built wheels,
and zipapps. Loaded eagerly at module import time by callers — matches
the previous hardcoded-dict semantics.
"""
from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


def load_json(*path_parts: str) -> Any:
    """
    Load a JSON file from the weather/data/ resource tree.

    Args:
        *path_parts: relative path segments under weather/data/.
            E.g. load_json("condition_maps", "hko-icons.json")

    Returns:
        Parsed JSON content.
    """
    if not path_parts:
        raise ValueError("at least one path part required")

    resource = files("weather.data")
    for part in path_parts:
        resource = resource.joinpath(part)
    return json.loads(resource.read_text(encoding="utf-8"))
