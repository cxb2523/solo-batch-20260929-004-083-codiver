"""
Tests for naming/documentation detector exemptions:
constructors, @Override methods and enum constants.
"""

import javalang

from detectors.naming_docs import NamingSmells, DocumentationSmells


CLASS_CODE = """
public class Sample {
    private int goodField;
    private int BadField;
    private static final int MAX_LIMIT = 10;
    private static final int badLimit = 5;

    public Sample() {
    }

    public Sample(int value) {
        this.goodField = value;
    }

    public void Sample() {
    }

    public void validMethod() {
    }

    @Override
    public String toString() {
        return "sample";
    }

    @Override
    public void Bad_Override() {
    }

    public void undocumented() {
    }
}
"""

ENUM_CODE = """
public enum Color {
    RED,
    GREEN,
    blue_sky
}
"""


def _detect(code, detector_cls):
    tree = javalang.parse.parse(code)
    return detector_cls().detect(tree, code.split("\n"))


def test_real_constructors_are_not_flagged_as_methods():
    """Genuine constructors (no return type) must not raise naming issues."""
    issues = _detect(CLASS_CODE, NamingSmells)
    sample_issues = [i for i in issues if i["Target"] == "Sample"]
    # Only the look-alike `void Sample()` method may be reported
    assert len(sample_issues) == 1
    assert "not a constructor" in sample_issues[0]["Reason"]


def test_same_name_method_with_return_type_still_reported():
    """A method sharing the class name but declaring a return type is a
    true violation and must still be reported."""
    issues = _detect(CLASS_CODE, NamingSmells)
    assert any(
        i["Type"] == "Invalid Method Name" and i["Target"] == "Sample"
        for i in issues
    )


def test_override_methods_exempt_from_doc_requirement():
    """@Override methods inherit documentation; missing Javadoc is not
    reported for them, but regular public methods still are."""
    issues = _detect(CLASS_CODE, DocumentationSmells)
    doc_targets = [
        i["Target"] for i in issues
        if i["Type"] == "Missing Method Documentation"
    ]
    assert "toString" not in doc_targets
    assert "Bad_Override" not in doc_targets
    assert "undocumented" in doc_targets


def test_override_with_noncompliant_name_still_reported():
    """@Override does not excuse a method name that violates camelCase."""
    issues = _detect(CLASS_CODE, NamingSmells)
    assert any(
        i["Type"] == "Invalid Method Name" and i["Target"] == "Bad_Override"
        for i in issues
    )
    assert not any(i["Target"] == "toString" for i in issues)


def test_enum_constants_use_constant_rules_not_field_rules():
    """Enum constants are validated as UPPER_SNAKE_CASE constants and
    never as camelCase fields."""
    issues = _detect(ENUM_CODE, NamingSmells)
    assert not [i for i in issues if i["Type"] == "Invalid Field Name"]
    constant_targets = [
        i["Target"] for i in issues if i["Type"] == "Invalid Constant Name"
    ]
    assert "blue_sky" in constant_targets
    assert "RED" not in constant_targets
    assert "GREEN" not in constant_targets


def test_field_and_constant_naming_rules():
    """Instance fields follow camelCase; static final constants follow
    UPPER_SNAKE_CASE. True violations in either group are reported."""
    issues = _detect(CLASS_CODE, NamingSmells)
    types_by_target = {}
    for issue in issues:
        types_by_target.setdefault(issue["Target"], []).append(issue["Type"])

    assert "Invalid Field Name" in types_by_target.get("BadField", [])
    assert "Invalid Constant Name" in types_by_target.get("badLimit", [])
    assert "goodField" not in types_by_target
    assert "MAX_LIMIT" not in types_by_target
