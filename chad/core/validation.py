"""Validation framework for CHAD system."""

from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass
from .errors import ValidationError


@dataclass
class ValidationRule:
    """Represents a validation rule with its check function and error message."""
    name: str
    check: Callable[[Any], bool]
    message: str
    details: Optional[Dict[str, Any]] = None


class Validator:
    """Base validator class that can be extended for specific validation needs."""

    def __init__(self):
        self.rules: Dict[str, ValidationRule] = {}
        self._validation_errors: List[Dict[str, Any]] = []

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule."""
        self.rules[rule.name] = rule

    def validate(self, data: Any) -> bool:
        """Validate data against all registered rules.

        Args:
            data: Data to validate

        Returns:
            True if all validations pass

        Raises:
            ValidationError: If any validation fails
        """
        self._validation_errors = []

        for rule in self.rules.values():
            try:
                if not rule.check(data):
                    self._validation_errors.append({
                        "rule": rule.name,
                        "message": rule.message,
                        "details": rule.details
                    })
            except Exception as e:
                self._validation_errors.append({
                    "rule": rule.name,
                    "message": f"Validation check failed: {str(e)}",
                    "details": {"error": str(e)}
                })

        if self._validation_errors:
            raise ValidationError(
                message="Validation failed",
                details={"errors": self._validation_errors}
            )

        return True

    @property
    def errors(self) -> List[Dict[str, Any]]:
        """Get list of validation errors."""
        return self._validation_errors.copy()


class ContentValidator(Validator):
    """Validator for content processing."""

    def __init__(self):
        super().__init__()
        self._add_default_rules()

    def _add_default_rules(self):
        """Add default content validation rules."""
        self.add_rule(ValidationRule(
            name="not_empty",
            check=lambda x: bool(x),
            message="Content cannot be empty"
        ))


class ConfigValidator(Validator):
    """Validator for configuration data."""

    def __init__(self, schema: Dict[str, Type]):
        super().__init__()
        self.schema = schema
        self._add_schema_rules()

    def _add_schema_rules(self):
        """Add rules based on schema definition."""
        for key, expected_type in self.schema.items():
            self.add_rule(ValidationRule(
                name=f"type_{key}",
                check=lambda x, k=key, t=expected_type: isinstance(
                    x.get(k), t),
                message=f"Field '{key}' must be of type {expected_type.__name__}",
                details={"field": key, "expected_type": expected_type.__name__}
            ))
