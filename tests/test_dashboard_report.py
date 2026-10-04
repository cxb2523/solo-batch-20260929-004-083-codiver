"""Tests for the dashboard scan summary column and HTML export."""

import os

from scanner import ScanHit, aggregate_hits
from dashboard import export_scan_report_html


def _report(root):
    hits = [
        ScanHit(path=os.path.join("src", "A.java"), issue={"Type": "T", "Target": "a",
                                                           "Severity": "Low", "Reason": "r",
                                                           "Category": "Naming"}),
        ScanHit(path=os.path.join(root, "src", "A.java"), issue={"Type": "T", "Target": "b",
                                                                 "Severity": "Low", "Reason": "r",
                                                                 "Category": "Naming"}),
        ScanHit(path=os.path.join("src", "B.java"), issue={"Type": "T", "Target": "c",
                                                           "Severity": "Low", "Reason": "r",
                                                           "Category": "Naming"}),
    ]
    return aggregate_hits(hits, root)


def test_scan_report_counts(tmp_path):
    report = _report(str(tmp_path))
    assert report.raw_hit_count == 3
    assert report.unique_file_count == 2
    assert report.collapsed_count == 1


def test_export_scan_report_html_is_directly_openable(tmp_path):
    report = _report(str(tmp_path))
    output = str(tmp_path / "report.html")
    export_scan_report_html(report, output)

    with open(output, "r", encoding="utf-8") as handle:
        html = handle.read()

    assert html.startswith("<!DOCTYPE html>")
    assert "Raw Hits" in html
    assert "Unique Files" in html
    assert "Collapsed" in html
    # raw=3, unique=2, collapsed=1 rendered into the page
    assert ">3</div>Raw Hits" in html
    assert ">2</div>Unique Files" in html
    assert ">1</div>Collapsed" in html
    # display path stays the original relative form
    assert os.path.join("src", "A.java") in html
