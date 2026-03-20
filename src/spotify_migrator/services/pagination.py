"""Utility functions."""

from typing import Any


def chunk_list(items: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split a list into chunks of specified size."""
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
