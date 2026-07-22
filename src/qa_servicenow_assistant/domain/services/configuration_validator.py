"""Domain service that validates an ApplicationConfiguration.

Pure domain logic: it depends only on already-loaded value objects and the
standard library, with no infrastructure dependency, per SAD 8.7 ("A Domain
Layer nao acessa arquivos nem banco de dados") and SAD 8.6 ("Servicos de
Dominio: Validacao das entidades de negocio").
"""

from __future__ import annotations

from urllib.parse import urlparse

from qa_servicenow_assistant.domain.exceptions.configuration import (
    InvalidConfigurationValueError,
    MissingRequiredParameterError,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ApplicationConfiguration,
)

_ALLOWED_BACKOFF_STRATEGIES = frozenset({"none", "fixed", "linear", "exponential"})
_ALLOWED_LOG_LEVELS = frozenset({"TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_ALLOWED_REPORT_FORMATS = frozenset({"html", "json"})


class ConfigurationValidator:
    """Validates an ApplicationConfiguration against SAD Cap. 21 and RF-002."""

    def validate(self, configuration: ApplicationConfiguration) -> None:
        self._validate_required_paths(configuration)
        self._validate_instance_url(configuration)
        self._validate_browser(configuration)
        self._validate_retry(configuration)
        self._validate_navigation(configuration)
        self._validate_logging(configuration)
        self._validate_reporting(configuration)

    def _validate_required_paths(self, configuration: ApplicationConfiguration) -> None:
        spreadsheet_path = configuration.spreadsheet_path
        if not str(spreadsheet_path):
            raise MissingRequiredParameterError("spreadsheet_path is required")
        if spreadsheet_path.suffix.lower() != ".xlsx":
            raise InvalidConfigurationValueError(
                f"spreadsheet_path must point to a .xlsx file: {spreadsheet_path}"
            )
        if not spreadsheet_path.exists():
            raise InvalidConfigurationValueError(
                f"spreadsheet_path does not exist: {spreadsheet_path}"
            )

        knowledge_base_path = configuration.knowledge_base_path
        if not str(knowledge_base_path):
            raise MissingRequiredParameterError("knowledge_base_path is required")
        if not knowledge_base_path.exists():
            raise InvalidConfigurationValueError(
                f"knowledge_base_path does not exist: {knowledge_base_path}"
            )
        if not knowledge_base_path.is_dir():
            raise InvalidConfigurationValueError(
                f"knowledge_base_path must be a directory: {knowledge_base_path}"
            )

    def _validate_instance_url(self, configuration: ApplicationConfiguration) -> None:
        instance_url = configuration.instance_url
        if not instance_url:
            raise MissingRequiredParameterError("instance_url is required")
        parsed = urlparse(instance_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise InvalidConfigurationValueError(
                f"instance_url is not a valid HTTP(S) URL: {instance_url}"
            )

    def _validate_browser(self, configuration: ApplicationConfiguration) -> None:
        browser = configuration.browser
        if browser.timeout_ms <= 0:
            raise InvalidConfigurationValueError("browser.timeout_ms must be positive")
        if browser.viewport_width <= 0 or browser.viewport_height <= 0:
            raise InvalidConfigurationValueError(
                "browser viewport dimensions must be positive"
            )

    def _validate_retry(self, configuration: ApplicationConfiguration) -> None:
        retry = configuration.retry
        if retry.max_attempts < 1:
            raise InvalidConfigurationValueError("retry.max_attempts must be at least 1")
        if retry.backoff_strategy not in _ALLOWED_BACKOFF_STRATEGIES:
            raise InvalidConfigurationValueError(
                f"retry.backoff_strategy must be one of {sorted(_ALLOWED_BACKOFF_STRATEGIES)}"
            )
        if retry.base_delay_ms < 0:
            raise InvalidConfigurationValueError("retry.base_delay_ms cannot be negative")

    def _validate_navigation(self, configuration: ApplicationConfiguration) -> None:
        if configuration.navigation.timeout_ms <= 0:
            raise InvalidConfigurationValueError("navigation.timeout_ms must be positive")

    def _validate_logging(self, configuration: ApplicationConfiguration) -> None:
        logging_cfg = configuration.logging
        if logging_cfg.level not in _ALLOWED_LOG_LEVELS:
            raise InvalidConfigurationValueError(
                f"logging.level must be one of {sorted(_ALLOWED_LOG_LEVELS)}"
            )
        if not logging_cfg.file_name.strip():
            raise InvalidConfigurationValueError("logging.file_name must not be empty")
        if not logging_cfg.rotation.strip():
            raise InvalidConfigurationValueError("logging.rotation must not be empty")
        if not logging_cfg.retention.strip():
            raise InvalidConfigurationValueError("logging.retention must not be empty")
        if not logging_cfg.console_enabled and not logging_cfg.file_enabled:
            raise InvalidConfigurationValueError(
                "logging must have at least one sink enabled (console_enabled or file_enabled)"
            )

    def _validate_reporting(self, configuration: ApplicationConfiguration) -> None:
        if configuration.reporting.format not in _ALLOWED_REPORT_FORMATS:
            raise InvalidConfigurationValueError(
                f"reporting.format must be one of {sorted(_ALLOWED_REPORT_FORMATS)}"
            )
