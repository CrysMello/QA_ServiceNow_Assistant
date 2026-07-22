"""Configuration-specific exceptions (SAD 21.6 - Tratamento de Excecoes)."""

from __future__ import annotations

from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError


class ConfigurationError(QaServiceNowAssistantError):
    """Base exception for configuration-related failures."""


class ConfigurationFileNotFoundError(ConfigurationError):
    """Raised when a required configuration file cannot be located on disk."""


class ConfigurationFormatError(ConfigurationError):
    """Raised when a configuration file cannot be parsed."""


class MissingRequiredParameterError(ConfigurationError):
    """Raised when a mandatory configuration parameter is missing or empty."""


class InvalidConfigurationValueError(ConfigurationError):
    """Raised when a configuration value is present but fails validation."""
