"""
Naming Convention and Documentation Smell Detectors
Validates naming standards and documentation coverage
"""

from typing import List, Dict, Any
import javalang
from detectors.base import CodeSmell
from utils.helpers import (
    validate_class_name,
    validate_method_name,
    validate_field_name,
    validate_constant_name,
)


def _has_override_annotation(node) -> bool:
    """Check whether a method node carries an @Override annotation."""
    for annotation in (node.annotations or []):
        name = getattr(annotation, "name", "") or ""
        if name.split(".")[-1] == "Override":
            return True
    return False


def _enclosing_type_name(path) -> str:
    """Return the name of the innermost enclosing class/enum, if any."""
    for ancestor in reversed(path):
        if isinstance(ancestor, (javalang.tree.ClassDeclaration,
                                 javalang.tree.EnumDeclaration)):
            return ancestor.name
    return ""


def _is_constant_field(node) -> bool:
    """Check whether a field declaration is a static final constant."""
    modifiers = node.modifiers or []
    return 'static' in modifiers and 'final' in modifiers


class NamingSmells(CodeSmell):
    """
    Detects naming convention violations including:
    - Invalid class names (PascalCase)
    - Invalid method names (camelCase)
    - Invalid field/constant names
    - Short identifiers

    Exemptions handled internally (base detector interface unchanged):
    - Real constructors are never checked as methods; a method that merely
      shares the class name but declares a return type is still reported.
    - Enum constants follow constant (UPPER_SNAKE_CASE) rules, not field
      rules.
    - @Override does not exempt a method from naming rules: an override
      with a non-compliant name is still reported.
    """
    
    def detect(self, tree: javalang.tree.CompilationUnit, lines: List[str]) -> List[Dict[str, Any]]:
        """Detect all naming convention violations."""
        results = []
        
        # Check class and enum naming conventions
        for _, node in tree.filter((javalang.tree.ClassDeclaration,
                                    javalang.tree.EnumDeclaration)):
            if not validate_class_name(node.name):
                results.append(self._create_issue(
                    "Invalid Class Name",
                    node.name,
                    "Low",
                    "Class name should follow PascalCase convention",
                    "Naming"
                ))
            
            if len(node.name) < 3:
                results.append(self._create_issue(
                    "Short Name",
                    node.name,
                    "Low",
                    "Class name too short (< 3 characters)",
                    "Naming"
                ))
        
        # Check method naming conventions
        # (constructors are javalang ConstructorDeclaration nodes, not
        # MethodDeclaration, so they are exempt from these checks by
        # construction; only look-alike methods are caught below)
        for path, node in tree.filter(javalang.tree.MethodDeclaration):
            enclosing = _enclosing_type_name(path)

            # A method sharing the enclosing type name but declaring a
            # return type is NOT a real constructor: report it.
            if enclosing and node.name == enclosing:
                results.append(self._create_issue(
                    "Invalid Method Name",
                    node.name,
                    "Low",
                    "Method shares the class name but declares a return "
                    "type; it is not a constructor",
                    "Naming"
                ))
                continue

            if not validate_method_name(node.name):
                results.append(self._create_issue(
                    "Invalid Method Name",
                    node.name,
                    "Low",
                    "Method name should follow camelCase convention",
                    "Naming"
                ))
            
            # Allow short common method names
            if len(node.name) < 3 and node.name not in ['is', 'do', 'to', 'of']:
                results.append(self._create_issue(
                    "Short Name",
                    node.name,
                    "Low",
                    "Method name too short (< 3 characters)",
                    "Naming"
                ))
        
        # Check field naming conventions; static final fields are
        # constants and follow UPPER_SNAKE_CASE instead of camelCase.
        for _, node in tree.filter(javalang.tree.FieldDeclaration):
            is_constant = _is_constant_field(node)
            for declarator in (node.declarators or []):
                name = declarator.name
                if is_constant:
                    if not validate_constant_name(name):
                        results.append(self._create_issue(
                            "Invalid Constant Name",
                            name,
                            "Low",
                            "Constant name should follow UPPER_SNAKE_CASE "
                            "convention",
                            "Naming"
                        ))
                elif not validate_field_name(name):
                    results.append(self._create_issue(
                        "Invalid Field Name",
                        name,
                        "Low",
                        "Field name should follow camelCase convention",
                        "Naming"
                    ))

        # Enum constants are constants, not fields: validate them against
        # UPPER_SNAKE_CASE and never against field camelCase rules.
        for _, node in tree.filter(javalang.tree.EnumConstantDeclaration):
            if not validate_constant_name(node.name):
                results.append(self._create_issue(
                    "Invalid Constant Name",
                    node.name,
                    "Low",
                    "Enum constant name should follow UPPER_SNAKE_CASE "
                    "convention",
                    "Naming"
                ))

        return results


class DocumentationSmells(CodeSmell):
    """
    Detects missing or inadequate documentation including:
    - Missing class Javadoc
    - Missing public method Javadoc
    """
    
    def detect(self, tree: javalang.tree.CompilationUnit, lines: List[str]) -> List[Dict[str, Any]]:
        """Detect all documentation issues."""
        results = []
        
        # Check class documentation
        for _, node in tree.filter(javalang.tree.ClassDeclaration):
            if not node.documentation:
                results.append(self._create_issue(
                    "Missing Class Documentation",
                    node.name,
                    "Low",
                    "No Javadoc found for class",
                    "Documentation"
                ))
        
        # Check public method documentation
        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            if 'public' in (node.modifiers or []) and not node.documentation:
                # Overridden methods inherit documentation from the
                # overridden declaration; missing Javadoc is not a smell.
                if _has_override_annotation(node):
                    continue
                results.append(self._create_issue(
                    "Missing Method Documentation",
                    node.name,
                    "Low",
                    "No Javadoc found for public method",
                    "Documentation"
                ))
        
        return results
