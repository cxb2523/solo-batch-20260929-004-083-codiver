"""
Directory Scanner and Report Aggregation

Collects Java source files under a scan root, runs the analyzer engine,
and aggregates per-file hits. Paths reported by detectors may be relative
(from the collection phase) or absolute (from individual detectors); all
paths are normalized against the scan root before deduplication so the
same file is never counted twice.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from analyzer_engine import StaticAnalyzerEngine


def normalize_scan_path(path: str, root: str) -> str:
    """
    Normalize a reported path against the scan root.

    Applies normpath first, then resolves to an absolute canonical path,
    and finally expresses it relative to the scan root. Separators follow
    the platform convention of the scan root.

    Args:
        path: Reported path (relative or absolute, any separator style)
        root: Scan root directory

    Returns:
        Normalized path relative to the scan root
    """
    normalized = os.path.normpath(path)
    if not os.path.isabs(normalized):
        normalized = os.path.join(os.path.realpath(root), normalized)
    resolved = os.path.realpath(normalized)
    return os.path.relpath(resolved, os.path.realpath(root))


def dedup_key(path: str, root: str) -> str:
    """
    Build the deduplication key for a reported path.

    Uses normcase so case folding matches the platform semantics
    (case-insensitive on Windows, case-sensitive on POSIX).
    """
    return os.path.normcase(normalize_scan_path(path, root))


@dataclass
class ScanHit:
    """A single detector hit tied to the path that was reported."""
    path: str
    issue: Dict[str, Any]


@dataclass
class FileReport:
    """Aggregated hits for one unique file."""
    display_path: str
    key: str
    hits: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ScanReport:
    """Aggregated scan result with dedup statistics."""
    root: str
    raw_hit_count: int
    naive_file_count: int
    files: List[FileReport]

    @property
    def unique_file_count(self) -> int:
        return len(self.files)

    @property
    def collapsed_count(self) -> int:
        return self.naive_file_count - self.unique_file_count


def aggregate_hits(hits: List[ScanHit], root: str) -> ScanReport:
    """
    Aggregate raw detector hits into a deduplicated report.

    Hits whose paths normalize to the same file (relative vs absolute,
    mixed separators, platform case variants) are merged into a single
    FileReport. The display path keeps the original relative form from
    the first occurrence. Output ordering is sorted by dedup key so
    aggregation is stable and reproducible regardless of input order.

    Args:
        hits: Raw hits, each carrying the path as reported
        root: Scan root directory

    Returns:
        ScanReport with deduplicated, deterministically ordered files
    """
    merged: Dict[str, FileReport] = {}
    naive_paths = set()
    for hit in hits:
        naive_paths.add(hit.path)
        key = dedup_key(hit.path, root)
        entry = merged.get(key)
        if entry is None:
            entry = FileReport(display_path=hit.path, key=key)
            merged[key] = entry
        entry.hits.append(hit.issue)

    ordered = [merged[key] for key in sorted(merged.keys())]
    return ScanReport(
        root=root,
        raw_hit_count=len(hits),
        naive_file_count=len(naive_paths),
        files=ordered,
    )


def collect_java_files(root: str) -> List[str]:
    """
    Collect all .java files under the scan root as relative paths.

    Returns:
        Deterministically sorted list of root-relative paths
    """
    collected = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for filename in sorted(filenames):
            if filename.endswith(".java"):
                full = os.path.join(dirpath, filename)
                collected.append(os.path.relpath(full, root))
    return sorted(collected)


class DirectoryScanner:
    """
    Scans a directory tree of Java sources and produces an aggregated,
    deduplicated report. Detector hits are normalized against the scan
    root so relative and absolute reports of the same file merge.
    """

    def __init__(self, root: str, config: Optional[Dict[str, bool]] = None):
        self.root = os.path.realpath(root)
        self.config = config

    def scan(self) -> ScanReport:
        """Run the full scan: collect, analyze, aggregate."""
        hits: List[ScanHit] = []
        for relative_path in collect_java_files(self.root):
            absolute_path = os.path.join(self.root, relative_path)
            with open(absolute_path, "r", encoding="utf-8") as handle:
                source = handle.read()
            engine = StaticAnalyzerEngine(source, self.config)
            try:
                issues, _ = engine.run()
            except ValueError:
                continue
            for issue in issues:
                hits.append(ScanHit(path=relative_path, issue=issue))
        return aggregate_hits(hits, self.root)
