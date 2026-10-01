"""
Scan Path Normalization Utilities
Unifies relative collector paths and absolute detector paths against the
scan root so aggregation can deduplicate deterministically.
"""

import os
from typing import Union

PathLike = Union[str, os.PathLike]


def normalize_scan_path(path: PathLike, root: PathLike) -> str:
    """
    Normalize a collected or detector-reported path against the scan root.

    The path is first passed through ``os.path.normpath`` and then resolved
    (relative paths are anchored at ``root``). Separators and letter casing
    are aligned to the host platform via ``os.path.normcase`` so the result
    is a stable, comparable canonical key.

    Args:
        path: Relative (collector) or absolute (detector) path
        root: Scan root directory

    Returns:
        Canonical absolute path key for deduplication
    """
    candidate = os.path.normpath(os.fspath(path))
    if not os.path.isabs(candidate):
        candidate = os.path.join(os.fspath(root), candidate)
    resolved = os.path.realpath(candidate)
    return os.path.normcase(os.path.normpath(resolved))


def display_scan_path(path: PathLike, root: PathLike) -> str:
    """
    Compute the display form of a scan path.

    Relative paths keep their original relative spelling (separators
    normalized for the platform); absolute detector paths are converted
    back to a path relative to the scan root.

    Args:
        path: Original collected or reported path
        root: Scan root directory

    Returns:
        Relative path string suitable for display
    """
    raw = os.fspath(path)
    if not os.path.isabs(raw):
        return os.path.normpath(raw)
    resolved = os.path.realpath(os.path.normpath(raw))
    return os.path.relpath(resolved, os.fspath(root))
