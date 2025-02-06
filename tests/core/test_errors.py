import pytest
from chad.core.errors import (
    CHADError,
    ConfigurationError,
    ConfigNotFoundError,
    PluginError,
    ProcessingError,
    ValidationError
)


def test_base_error():
    """Test base error creation and attributes."""
    error = CHADError(
        message="Test error",
        code="TEST_ERROR",
        details={"key": "value"}
    )

    assert str(error) == "Test error"
    assert error.code == "TEST_ERROR"
    assert error.details == {"key": "value"}


def test_error_inheritance():
    """Test error class inheritance."""
    assert issubclass(ConfigurationError, CHADError)
    assert issubclass(ConfigNotFoundError, ConfigurationError)
    assert issubclass(PluginError, CHADError)
    assert issubclass(ProcessingError, CHADError)
    assert issubclass(ValidationError, ProcessingError)


def test_error_without_optional_params():
    """Test error creation without optional parameters."""
    error = CHADError("Simple error")

    assert str(error) == "Simple error"
    assert error.code == "CHADError"
    assert error.details == {}


def test_specific_errors():
    """Test specific error types."""
    config_error = ConfigNotFoundError(
        message="Config not found",
        details={"path": "config.yaml"}
    )
    assert isinstance(config_error, (ConfigNotFoundError,
                      ConfigurationError, CHADError))

    validation_error = ValidationError(
        message="Validation failed",
        details={"field": "title", "reason": "required"}
    )
    assert isinstance(validation_error, (ValidationError,
                      ProcessingError, CHADError))
