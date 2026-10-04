"""
Tests for naming detector exceptions:
- Constructors are not judged as ordinary methods
- @Override methods are exempt from documentation checks but
  still checked for naming compliance
- Enum constants are not judged as ordinary fields
Real violations must still be reported.
"""

import javalang

from detectors.naming_docs import DocumentationSmells, NamingSmells


def _naming_issues(code):
    tree = javalang.parse.parse(code)
    return NamingSmells().detect(tree, code.split("\n"))


def _doc_issues(code):
    tree = javalang.parse.parse(code)
    return DocumentationSmells().detect(tree, code.split("\n"))


def test_constructor_is_not_flagged_as_method():
    code = (
        "public class Report {\n"
        "    public Report() {}\n"
        "    public Report(int size) {}\n"
        "    public void render() {}\n"
        "}\n"
    )
    issues = _naming_issues(code)
    assert [i for i in issues if i["Target"] == "Report"] == []


def test_same_name_method_with_return_type_is_flagged():
    code = (
        "public class Report {\n"
        "    public Report() {}\n"
        "    void Report() {}\n"
        "}\n"
    )
    issues = _naming_issues(code)
    matches = [i for i in issues if i["Target"] == "Report" and i["Type"] == "Invalid Method Name"]
    assert len(matches) == 1


def test_override_method_exempt_from_documentation_check():
    code = (
        "public class Report {\n"
        "    @Override\n"
        "    public String toString() { return \"r\"; }\n"
        "}\n"
    )
    doc_issues = _doc_issues(code)
    assert [i for i in doc_issues if i["Target"] == "toString"] == []


def test_override_method_with_bad_name_still_reported():
    code = (
        "public class Report {\n"
        "    @Override\n"
        "    public int BadName() { return 1; }\n"
        "}\n"
    )
    issues = _naming_issues(code)
    matches = [i for i in issues if i["Target"] == "BadName" and i["Type"] == "Invalid Method Name"]
    assert len(matches) == 1


def test_plain_public_method_still_needs_documentation():
    code = (
        "public class Report {\n"
        "    public void render() {}\n"
        "}\n"
    )
    doc_issues = _doc_issues(code)
    matches = [i for i in doc_issues if i["Type"] == "Missing Method Documentation"]
    assert len(matches) == 1


def test_enum_constants_are_not_flagged_as_fields():
    code = (
        "enum Color {\n"
        "    RED, GREEN, Blue;\n"
        "    private int code;\n"
        "    public int getCode() { return code; }\n"
        "}\n"
    )
    issues = _naming_issues(code)
    assert [i for i in issues if i["Target"] in ("RED", "GREEN", "Blue")] == []


def test_real_field_violations_still_reported():
    code = (
        "public class Report {\n"
        "    private int MyField;\n"
        "    private static final int MAX_COUNT = 5;\n"
        "    private static final int maxCount = 5;\n"
        "    private int validField;\n"
        "}\n"
    )
    issues = _naming_issues(code)
    invalid_fields = [i for i in issues if i["Type"] == "Invalid Field Name"]
    invalid_constants = [i for i in issues if i["Type"] == "Invalid Constant Name"]
    assert [i["Target"] for i in invalid_fields] == ["MyField"]
    assert [i["Target"] for i in invalid_constants] == ["maxCount"]


def test_real_method_violation_still_reported():
    code = (
        "public class Report {\n"
        "    public void Do_Things() {}\n"
        "}\n"
    )
    issues = _naming_issues(code)
    matches = [i for i in issues if i["Type"] == "Invalid Method Name"]
    assert len(matches) == 1
