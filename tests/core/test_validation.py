import pytest
from chad.core.validation import (
    ValidationRule,
    Validator,
    ContentValidator,
    ConfigValidator
)
from chad.core.errors import ValidationError


def test_validation_rule():
    """Test validation rule creation and execution."""
    rule = ValidationRule(
        name="test_rule",
        check=lambda x: isinstance(x, str),
        message="Value must be string",
        details={"type": "string"}
    )

    assert rule.check("test")
    assert not rule.check(123)


def test_validator_basic():
    """Test basic validator functionality."""
    validator = Validator()

    validator.add_rule(ValidationRule(
        name="is_positive",
        check=lambda x: x > 0,
        message="Value must be positive"
    ))

    assert validator.validate(5)

    with pytest.raises(ValidationError) as exc:
        validator.validate(-1)
    assert "Value must be positive" in str(exc.value.details)


def test_content_validator():
    """Test content validator with default rules."""
    validator = ContentValidator()

    assert validator.validate("test content")

    with pytest.raises(ValidationError) as exc:
        validator.validate("")
    assert "Content cannot be empty" in str(exc.value.details)


def test_config_validator():
    """Test configuration validator with schema."""
    schema = {
        "name": str,
        "count": int,
        "enabled": bool
    }

    validator = ConfigValidator(schema)

    valid_config = {
        "name": "test",
        "count": 5,
        "enabled": True
    }
    assert validator.validate(valid_config)

    invalid_config = {
        "name": "test",
        "count": "5",  # should be int
        "enabled": True
    }
    with pytest.raises(ValidationError) as exc:
        validator.validate(invalid_config)
    assert "must be of type" in str(exc.value.details)


def test_multiple_validation_errors():
    """Test collecting multiple validation errors."""
    validator = Validator()

    validator.add_rule(ValidationRule(
        name="length",
        check=lambda x: len(x) >= 3,
        message="Length must be at least 3"
    ))
    validator.add_rule(ValidationRule(
        name="alphanumeric",
        check=lambda x: x.isalnum(),
        message="Must be alphanumeric"
    ))

    with pytest.raises(ValidationError) as exc:
        validator.validate("a!")

    errors = exc.value.details["errors"]
    assert len(errors) == 2
    assert any("Length must be at least 3" in e["message"] for e in errors)
    assert any("Must be alphanumeric" in e["message"] for e in errors)
