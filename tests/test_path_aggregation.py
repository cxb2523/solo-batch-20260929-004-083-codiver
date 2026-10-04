"""
Tests for scan path normalization and hit aggregation dedup.

Covers the bug where the same file was counted twice because the
collection phase recorded relative paths while some detectors
reported absolute paths.
"""

import os

import pytest

from scanner import (
    DirectoryScanner,
    ScanHit,
    aggregate_hits,
    collect_java_files,
    dedup_key,
    normalize_scan_path,
)


@pytest.fixture
def scan_root(tmp_path):
    """Create a scan root with two Java files."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Alpha.java").write_text(
        "public class Alpha {\n"
        "    public void doWork() {\n"
        "        int a = 42;\n"
        "        int b = 43;\n"
        "        int c = 44;\n"
        "        int d = 45;\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    (src_dir / "Beta.java").write_text(
        "public class Beta {\n"
        "    public void doWork() {\n"
        "        int a = 42;\n"
        "        int b = 43;\n"
        "        int c = 44;\n"
        "        int d = 45;\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    return str(tmp_path)


def _issue(name):
    return {
        "Type": "Magic Numbers",
        "Target": name,
        "Severity": "Low",
        "Reason": "test",
        "Category": "Implementation",
    }


def test_relative_and_absolute_paths_merge(scan_root):
    relative = os.path.join("src", "Alpha.java")
    absolute = os.path.join(scan_root, "src", "Alpha.java")
    hits = [
        ScanHit(path=relative, issue=_issue("a")),
        ScanHit(path=absolute, issue=_issue("b")),
    ]
    report = aggregate_hits(hits, scan_root)

    assert report.raw_hit_count == 2
    assert report.unique_file_count == 1
    assert report.collapsed_count == 1
    # Display keeps the original relative path from collection
    assert report.files[0].display_path == relative
    assert len(report.files[0].hits) == 2


def test_separator_and_dot_segments_merge(scan_root):
    variants = [
        os.path.join("src", "Alpha.java"),
        os.path.join("src", ".", "Alpha.java"),
        os.path.join("src", "sub", "..", "Alpha.java"),
    ]
    hits = [ScanHit(path=v, issue=_issue(v)) for v in variants]
    report = aggregate_hits(hits, scan_root)

    assert report.unique_file_count == 1
    assert report.collapsed_count == len(variants) - 1


@pytest.mark.skipif(
    os.path.normcase("ABC") != "abc",
    reason="platform is case-sensitive",
)
def test_case_variants_merge_on_case_insensitive_platforms(scan_root):
    hits = [
        ScanHit(path=os.path.join("SRC", "ALPHA.JAVA"), issue=_issue("a")),
        ScanHit(path=os.path.join("src", "Alpha.java"), issue=_issue("b")),
    ]
    report = aggregate_hits(hits, scan_root)
    assert report.unique_file_count == 1
    assert report.collapsed_count == 1


def test_aggregation_order_is_reproducible(scan_root):
    hits = [
        ScanHit(path=os.path.join("src", "Beta.java"), issue=_issue("b1")),
        ScanHit(path=os.path.join(scan_root, "src", "Alpha.java"), issue=_issue("a1")),
        ScanHit(path=os.path.join("src", "Alpha.java"), issue=_issue("a2")),
        ScanHit(path=os.path.join(scan_root, "src", "Beta.java"), issue=_issue("b2")),
    ]
    forward = aggregate_hits(hits, scan_root)
    reverse = aggregate_hits(list(reversed(hits)), scan_root)

    forward_keys = [f.key for f in forward.files]
    reverse_keys = [f.key for f in reverse.files]
    assert forward_keys == reverse_keys
    assert forward_keys == sorted(forward_keys)
    assert forward.unique_file_count == 2
    assert forward.raw_hit_count == 4
    assert forward.collapsed_count == 2


def test_normalize_then_resolve_against_root(scan_root):
    relative = os.path.join("src", "Alpha.java")
    absolute = os.path.join(scan_root, "src", "Alpha.java")
    assert normalize_scan_path(relative, scan_root) == normalize_scan_path(absolute, scan_root)
    assert dedup_key(relative, scan_root) == dedup_key(absolute, scan_root)


def test_collect_java_files_is_sorted_and_relative(scan_root):
    collected = collect_java_files(scan_root)
    assert collected == sorted(collected)
    assert collected == [
        os.path.join("src", "Alpha.java"),
        os.path.join("src", "Beta.java"),
    ]


def test_directory_scanner_end_to_end(scan_root):
    report = DirectoryScanner(scan_root).scan()
    assert report.unique_file_count == 2
    assert report.raw_hit_count >= 2
    assert report.collapsed_count == 0
    keys = [f.key for f in report.files]
    assert keys == sorted(keys)
