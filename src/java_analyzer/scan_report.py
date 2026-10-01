"""
Scan Report Aggregation
Merges findings reported under different path spellings (relative collector
paths vs. absolute detector paths) into per-file groups with stable,
reproducible ordering.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Tuple

from utils.paths import normalize_scan_path, display_scan_path


@dataclass
class FileFindings:
    """Findings grouped under one canonical file."""

    key: str
    display_path: str
    findings: List[Dict[str, Any]] = field(default_factory=list)


def aggregate_findings(
    findings: Iterable[Dict[str, Any]],
    root: str,
) -> Tuple[List[FileFindings], Dict[str, int]]:
    """
    Group finding records by their canonical file path.

    Each finding must carry a ``file`` entry holding either a relative
    (collector) or absolute (detector) path. Grouping uses the canonical
    key from :func:`normalize_scan_path`; the display layer keeps the
    original relative spelling via :func:`display_scan_path`.

    Ordering is deterministic: files are sorted by canonical key and
    findings keep their original arrival order within each file.

    Args:
        findings: Finding dictionaries, each with a ``file`` key
        root: Scan root directory used as the normalization anchor

    Returns:
        Tuple of (per-file groups sorted by canonical key, stats dict with
        ``raw_hits``, ``unique_files`` and ``collapsed`` counts)
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}
    display_paths: Dict[str, str] = {}
    raw_hits = 0

    for finding in findings:
        raw_hits += 1
        key = normalize_scan_path(finding["file"], root)
        groups.setdefault(key, []).append(finding)
        if key not in display_paths:
            display_paths[key] = display_scan_path(finding["file"], root)

    files = [
        FileFindings(key=key, display_path=display_paths[key], findings=groups[key])
        for key in sorted(groups)
    ]
    stats = {
        "raw_hits": raw_hits,
        "unique_files": len(files),
        "collapsed": raw_hits - len(files),
    }
    return files, stats
