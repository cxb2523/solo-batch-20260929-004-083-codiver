"""
Pytest configuration: make the java_analyzer source tree importable so
detectors, engines and report utilities resolve their top-level imports
(detectors.*, utils.*, scan_report, ...).
"""

import sys
from pathlib import Path

JAVA_ANALYZER_DIR = Path(__file__).resolve().parent / "src" / "java_analyzer"
if str(JAVA_ANALYZER_DIR) not in sys.path:
    sys.path.insert(0, str(JAVA_ANALYZER_DIR))
