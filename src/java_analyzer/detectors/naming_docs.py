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


class NamingSmells(CodeSmell):
    """
    Detects naming convention violations including:
    - Invalid class names (PascalCase)
    - Invalid method names (camelCase)
    - Invalid field names (camelCase, UPPER_SNAKE_CASE for constants)
    - Short identifiers

    Exceptions handled inside the detector:
    - Constructors are never checked as ordinary methods
    - Enum constants are never checked as ordinary fields
    - @Override methods are still checked: the annotation does not
      excuse a non-compliant name
    """

    # Common short method names that are acceptable
    ALLOWED_SHORT_NAMES = {'is', 'do', 'to', 'of'}
    
    def detect(self, tree: javalang.tree.CompilationUnit, lines: List[str]) -> List[Dict[str, Any]]:
        """Detect all naming convention violations."""
        results = []
        enum_constants = self._collect_enum_constant_names(tree)
        
        # Check class naming conventions
        for _, node in tree.filter(javalang.tree.ClassDeclaration):
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
        
        # Check method naming conventions (constructors excluded)
        for method in self._iter_methods(tree):
            results.extend(self._check_method_name(method))

        # Check field naming conventions (enum constants excluded)
        for field in self._iter_fields(tree):
            results.extend(self._check_field_names(field, enum_constants))
        
        return results

    def _iter_methods(self, tree: javalang.tree.CompilationUnit):
        """
        Yield all method declarations, explicitly skipping constructors.

        Constructors share the class name and must not be judged by
        method naming rules. A method that merely shares the class name
        but declares a return type is NOT a constructor: javalang parses
        it as a MethodDeclaration and it is yielded (and checked) here.
        """
        seen = set()
        for _, class_node in tree.filter(javalang.tree.ClassDeclaration):
            for member in class_node.body or []:
                if isinstance(member, javalang.tree.ConstructorDeclaration):
                    # Constructor exception: not an ordinary method
                    continue
                if isinstance(member, javalang.tree.MethodDeclaration):
                    seen.add(id(member))
                    yield member
        # Methods outside class bodies (interfaces, enums, annotations)
        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            if id(node) not in seen:
                yield node

    def _iter_fields(self, tree: javalang.tree.CompilationUnit):
        """Yield all field declarations, including those inside enums."""
        seen = set()
        for _, class_node in tree.filter(javalang.tree.ClassDeclaration):
            for member in class_node.body or []:
                if isinstance(member, javalang.tree.FieldDeclaration):
                    seen.add(id(member))
                    yield member
        for _, node in tree.filter(javalang.tree.FieldDeclaration):
            if id(node) not in seen:
                yield node

    def _collect_enum_constant_names(self, tree: javalang.tree.CompilationUnit) -> set:
        """Collect enum constant names so they are exempt from field checks."""
        return {
            node.name
            for _, node in tree.filter(javalang.tree.EnumConstantDeclaration)
        }

    def _check_method_name(self, node: javalang.tree.MethodDeclaration) -> List[Dict[str, Any]]:
        """Check a single method name. @Override does not exempt naming."""
        results = []
        if not validate_method_name(node.name):
            results.append(self._create_issue(
                "Invalid Method Name",
                node.name,
                "Low",
                "Method name should follow camelCase convention",
                "Naming"
            ))

        if len(node.name) < 3 and node.name not in self.ALLOWED_SHORT_NAMES:
            results.append(self._create_issue(
                "Short Name",
                node.name,
                "Low",
                "Method name too short (< 3 characters)",
                "Naming"
            ))
        return results

    def _check_field_names(self, node: javalang.tree.FieldDeclaration,
                           enum_constants: set) -> List[Dict[str, Any]]:
        """Check field declarators; enum constants are exempt."""
        results = []
        modifiers = node.modifiers or set()
        is_constant = {'static', 'final'} <= set(modifiers)

        for declarator in node.declarators:
            name = declarator.name
            if name in enum_constants:
                # Enum constant exception: not an ordinary field
                continue

            if is_constant:
                if not validate_constant_name(name):
                    results.append(self._create_issue(
                        "Invalid Constant Name",
                        name,
                        "Low",
                        "Constant name should follow UPPER_SNAKE_CASE convention",
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
        return results


class DocumentationSmells(CodeSmell):
    """
    Detects missing or inadequate documentation including:
    - Missing class Javadoc
    - Missing public method Javadoc

    Methods annotated with @Override are exempt: their contract and
    documentation are defined by the overridden supertype member.
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
            if self._is_override(node):
                # Override exception: documentation lives on the supertype
                continue
            if 'public' in (node.modifiers or []) and not node.documentation:
                results.append(self._create_issue(
                    "Missing Method Documentation",
                    node.name,
                    "Low",
                    "No Javadoc found for public method",
                    "Documentation"
                ))
        
        return results

    def _is_override(self, node: javalang.tree.MethodDeclaration) -> bool:
        """Check whether a method is annotated with @Override."""
        return any(
            annotation.name == 'Override'
            for annotation in (node.annotations or [])
        )
