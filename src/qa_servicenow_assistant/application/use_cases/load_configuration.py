"""LoadConfiguration use case (SAD 9.3; fluxo de inicializacao SAD 21.4)."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from qa_servicenow_assistant.application.ports.configuration_repository import (
    ConfigurationRepository,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.services.configuration_validator import (
    ConfigurationValidator,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    ApplicationConfiguration,
    BrowserConfiguration,
    CheckpointConfiguration,
    ExportConfiguration,
    LoggingConfiguration,
    NavigationConfiguration,
    ReportingConfiguration,
    RetryConfiguration,
    ScreenshotConfiguration,
)

_ENV_PREFIX = "QA_SNA_"


@dataclass(frozen=True)
class LoadConfigurationRequest:
    """Input for the LoadConfiguration use case.

    spreadsheet_path, knowledge_base_path and instance_url are mandatory,
    per RF-001 (SRS): the CLI must always supply them explicitly. They are
    intentionally not defaulted from a configuration file or environment
    variable. config_file_path is optional: when omitted, only environment
    overrides and built-in defaults are applied.
    """

    spreadsheet_path: Path
    knowledge_base_path: Path
    instance_url: str
    config_file_path: Path | None = None


class LoadConfigurationUseCase:
    """Coordinates loading, overriding, building and validating the
    application configuration (SAD Cap. 21)."""

    def __init__(
        self,
        configuration_repository: ConfigurationRepository,
        log_port: LogPort,
        validator: ConfigurationValidator | None = None,
    ) -> None:
        self._configuration_repository = configuration_repository
        self._log_port = log_port
        self._validator = validator or ConfigurationValidator()

    def execute(self, request: LoadConfigurationRequest) -> ApplicationConfiguration:
        raw_data = self._load_raw_data(request.config_file_path)
        overrides = _read_environment_overrides()
        configuration = _build_configuration(request, raw_data, overrides)
        self._validator.validate(configuration)
        self._log_summary(configuration)
        return configuration

    def _load_raw_data(self, config_file_path: Path | None) -> dict[str, Any]:
        if config_file_path is None:
            return {}
        return self._configuration_repository.load(config_file_path)

    def _log_summary(self, configuration: ApplicationConfiguration) -> None:
        self._log_port.info(
            "Configuration loaded",
            instance_url=configuration.instance_url,
            spreadsheet_path=str(configuration.spreadsheet_path),
            knowledge_base_path=str(configuration.knowledge_base_path),
            browser_headless=configuration.browser.headless,
            retry_max_attempts=configuration.retry.max_attempts,
            log_level=configuration.logging.level,
        )


def _build_configuration(
    request: LoadConfigurationRequest,
    raw_data: dict[str, Any],
    overrides: dict[str, Any],
) -> ApplicationConfiguration:
    browser = _merge(BrowserConfiguration(), raw_data.get("browser", {}), overrides.get("browser", {}))
    retry = _merge(RetryConfiguration(), raw_data.get("retry", {}), overrides.get("retry", {}))
    navigation = _merge(NavigationConfiguration(), raw_data.get("navigation", {}))
    logging_cfg = _merge(LoggingConfiguration(), raw_data.get("logging", {}), overrides.get("logging", {}))
    screenshots = _merge(ScreenshotConfiguration(), raw_data.get("screenshots", {}))
    reporting = _merge(ReportingConfiguration(), raw_data.get("reporting", {}))
    checkpoints = _merge(CheckpointConfiguration(), raw_data.get("checkpoints", {}))
    export = _merge(ExportConfiguration(), raw_data.get("export", {}))

    instance_url = overrides.get("instance_url", request.instance_url)

    return ApplicationConfiguration(
        spreadsheet_path=request.spreadsheet_path,
        knowledge_base_path=request.knowledge_base_path,
        instance_url=instance_url,
        browser=browser,
        retry=retry,
        navigation=navigation,
        logging=logging_cfg,
        screenshots=screenshots,
        reporting=reporting,
        checkpoints=checkpoints,
        export=export,
    )


def _merge(base: Any, *sources: dict[str, Any]) -> Any:
    """Applies each mapping in sources onto a copy of base, field by field.

    Unknown keys (not present as fields on base) are ignored rather than
    raising, so forward-compatible configuration files do not break older
    binaries; unknown-key rejection can be added later if desired.
    """
    for source in sources:
        for key, value in source.items():
            if hasattr(base, key):
                base = replace(base, **{key: value})
    return base


def _read_environment_overrides() -> dict[str, Any]:
    """Reads a fixed, documented set of QA_SNA_* environment variables
    (SAD 21.5 - Sobrescrita por ambiente).

    Only the fields most likely to vary between environments are covered in
    this first version; additional fields can be added incrementally
    without breaking existing callers.
    """
    overrides: dict[str, Any] = {}

    instance_url = os.environ.get(f"{_ENV_PREFIX}INSTANCE_URL")
    if instance_url is not None:
        overrides["instance_url"] = instance_url

    headless = os.environ.get(f"{_ENV_PREFIX}BROWSER_HEADLESS")
    if headless is not None:
        overrides.setdefault("browser", {})["headless"] = (
            headless.strip().lower() in {"1", "true", "yes"}
        )

    browser_timeout = os.environ.get(f"{_ENV_PREFIX}BROWSER_TIMEOUT_MS")
    if browser_timeout is not None:
        overrides.setdefault("browser", {})["timeout_ms"] = int(browser_timeout)

    max_attempts = os.environ.get(f"{_ENV_PREFIX}RETRY_MAX_ATTEMPTS")
    if max_attempts is not None:
        overrides.setdefault("retry", {})["max_attempts"] = int(max_attempts)

    log_level = os.environ.get(f"{_ENV_PREFIX}LOG_LEVEL")
    if log_level is not None:
        overrides.setdefault("logging", {})["level"] = log_level.strip().upper()

    return overrides
