"""Shared utility functions."""

import copy

from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries, with override values taking precedence.

    Supports merging nested dictionaries and arrays. Arrays are merged element-by-element,
    with dict elements being recursively merged.

    Uses deep copy to prevent mutation of the base dictionary.
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key not in result:
            result[key] = value
        elif isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        elif isinstance(result[key], list) and isinstance(value, list):
            merged_array = copy.deepcopy(result[key])
            for i, item in enumerate(value):
                if i < len(merged_array):
                    if isinstance(merged_array[i], dict) and isinstance(item, dict):
                        merged_array[i] = deep_merge(merged_array[i], item)
                    else:
                        merged_array[i] = item
                else:
                    merged_array.append(item)
            result[key] = merged_array
        else:
            result[key] = value
    return result
