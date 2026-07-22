"""Loguru-based implementation of the LogPort (SAD 10.3; SAD Cap. 24; ADR-0013).

Provides console and file sinks, rotation, retention and sensitive-data
masking, with correlation by execution_id/module/workflow_step supported
through bind() (SAD 24.5 - Estrutura da Mensagem).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from loguru import logger as _loguru_root_logger

from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.value_objects.configuration import (
    LoggingConfiguration,
)
from qa_servicenow_assistant.infrastructure.logging.sensitive_data_masker import (
    mask_sensitive_data,
)

_LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra} | {message}"
)


class LoguruLogAdapter(LogPort):
    """Full Log Engine adapter satisfying LogPort.

    Intended to be instantiated once by the composition root (bootstrap/),
    since it reconfigures the process-wide Loguru sinks on construction.
    bind() does not reconfigure sinks; it returns a lightweight derived
    instance that reuses the same underlying Loguru logger and carries
    additional bound context (e.g. execution_id, module, workflow_step).
    """

    def __init__(
        self,
        configuration: LoggingConfiguration | None = None,
        *,
        _logger: Any = None,
        _bound_context: dict[str, Any] | None = None,
    ) -> None:
        self._configuration = configuration or LoggingConfiguration()
        self._bound_context: dict[str, Any] = dict(_bound_context or {})

        if _logger is not None:
            self._logger = _logger
            return

        self._logger = self._configure_sinks()

    def _configure_sinks(self) -> Any:
        _loguru_root_logger.remove()
        config = self._configuration

        if config.console_enabled:
            _loguru_root_logger.add(sys.stderr, level=config.level, format=_LOG_FORMAT)

        if config.file_enabled:
            log_directory = Path(config.directory)
            log_directory.mkdir(parents=True, exist_ok=True)
            log_path = log_directory / config.file_name
            _loguru_root_logger.add(
                log_path,
                level=config.level,
                rotation=config.rotation,
                retention=config.retention,
                format=_LOG_FORMAT,
                encoding="utf-8",
            )

        return _loguru_root_logger

    def bind(self, **context: Any) -> "LoguruLogAdapter":
        merged_context = {**self._bound_context, **context}
        return LoguruLogAdapter(
            self._configuration, _logger=self._logger, _bound_context=merged_context
        )

    def trace(self, message: str, **context: Any) -> None:
        self._emit("TRACE", message, context)

    def debug(self, message: str, **context: Any) -> None:
        self._emit("DEBUG", message, context)

    def info(self, message: str, **context: Any) -> None:
        self._emit("INFO", message, context)

    def warning(self, message: str, **context: Any) -> None:
        self._emit("WARNING", message, context)

    def error(self, message: str, **context: Any) -> None:
        self._emit("ERROR", message, context)

    def critical(self, message: str, **context: Any) -> None:
        self._emit("CRITICAL", message, context)

    def _emit(self, level: str, message: str, context: dict[str, Any]) -> None:
        merged_context = {**self._bound_context, **context}
        safe_context = (
            mask_sensitive_data(merged_context)
            if self._configuration.mask_sensitive_data
            else merged_context
        )
        self._logger.bind(**safe_context).log(level, message)
