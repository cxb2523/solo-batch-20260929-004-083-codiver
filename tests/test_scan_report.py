"""
Tests for scan path normalization and finding aggregation deduplication.
"""

import os

from scan_report import aggregate_findings
from utils.paths import normalize_scan_path, display_scan_path


def _finding(path, smell_type="Issue"):
    return {"file": path, "Type": smell_type}


def test_relative_and_absolute_paths_merge(tmp_path):
    """Collector-relative and detector-absolute paths of the same file
    must collapse into a single aggregated entry."""
    root = str(tmp_path)
    relative = "src/Foo.java"
    absolute = str(tmp_path / "src" / "Foo.java")
    dotted = os.path.join("src", ".", "Foo.java")

    findings = [_finding(relative), _finding(absolute), _finding(dotted)]
    files, stats = aggregate_findings(findings, root)

    assert stats == {"raw_hits": 3, "unique_files": 1, "collapsed": 2}
    assert len(files) == 1
    assert len(files[0].findings) == 3
    # Display layer keeps the original relative spelling
    assert files[0].display_path == os.path.normpath(relative)


def test_absolute_first_falls_back_to_relative_display(tmp_path):
    """When the absolute path arrives first, the display path is still
    shown relative to the scan root."""
    root = str(tmp_path)
    absolute = str(tmp_path / "src" / "Foo.java")
    relative = os.path.join("src", "Foo.java")

    files, stats = aggregate_findings(
        [_finding(absolute), _finding(relative)], root
    )

    assert stats["unique_files"] == 1
    assert files[0].display_path == os.path.normpath(relative)


def test_aggregation_order_is_stable_and_reproducible(tmp_path):
    """File groups are sorted by canonical key regardless of input order."""
    root = str(tmp_path)
    names = ["b/Bravo.java", "a/Alpha.java", "c/Charlie.java"]

    forward, _ = aggregate_findings([_finding(n) for n in names], root)
    backward, _ = aggregate_findings(
        [_finding(n) for n in reversed(names)], root
    )

    forward_keys = [f.key for f in forward]
    backward_keys = [f.key for f in backward]
    assert forward_keys == backward_keys
    assert forward_keys == sorted(forward_keys)
    assert [f.display_path for f in forward] == [
        os.path.normpath(n) for n in ("a/Alpha.java", "b/Bravo.java", "c/Charlie.java")
    ]


def test_separator_and_case_alignment_follow_platform(tmp_path):
    """Separator and casing equivalence matches the host platform rules."""
    root = str(tmp_path)
    lower = os.path.join("src", "foo.java")
    upper = os.path.join("SRC", "FOO.JAVA")

    files, stats = aggregate_findings([_finding(lower), _finding(upper)], root)

    if os.path.normcase("ABC") == "abc":
        # Case-insensitive platform (e.g. Windows): paths merge
        assert stats["unique_files"] == 1
        assert stats["collapsed"] == 1
    else:
        # Case-sensitive platform: distinct files
        assert stats["unique_files"] == 2
        assert stats["collapsed"] == 0


def test_normalize_then_resolve_against_root(tmp_path):
    """normpath runs before resolving so dot segments never leak into keys."""
    root = str(tmp_path)
    messy = os.path.join("src", "..", "src", ".", "Foo.java")
    clean = os.path.join("src", "Foo.java")

    assert normalize_scan_path(messy, root) == normalize_scan_path(clean, root)
    assert ".." not in normalize_scan_path(messy, root)
    assert display_scan_path(messy, root) == os.path.normpath(messy)
