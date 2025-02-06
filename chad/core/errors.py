"""Core error types and error handling utilities for CHAD system."""

from typing import Optional, Dict, Any


class CHADError(Exception):
    """Base exception class for all CHAD errors."""

    def __init__(
        self,
        message: str,
        code: str = None,
        details: Dict[str, Any] = None
    ) -> None:
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


# Configuration Errors
class ConfigurationError(CHADError):
    """Base class for configuration related errors."""
    pass


class ConfigNotFoundError(ConfigurationError):
    """Raised when configuration item is not found."""
    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""
    pass


# Plugin Errors
class PluginError(CHADError):
    """Base class for plugin related errors."""
    pass


class PluginNotFoundError(PluginError):
    """Raised when plugin is not found."""
    pass


class PluginInitError(PluginError):
    """Raised when plugin initialization fails."""
    pass


# Processing Errors
class ProcessingError(CHADError):
    """Base class for content processing errors."""
    pass


class ValidationError(ProcessingError):
    """Raised when content validation fails."""
    pass


class ResourceError(ProcessingError):
    """Raised when required resource is unavailable."""
    pass


# Storage Errors
class StorageError(CHADError):
    """Base class for storage related errors."""
    pass


class DataNotFoundError(StorageError):
    """Raised when data is not found in storage."""
    pass


class StorageConnectionError(StorageError):
    """Raised when storage connection fails."""
    pass
