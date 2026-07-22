"""Loguru-based implementation of the LogPort (SAD 10.3 - Log Adapter).

Scope note: a full-featured Log Engine (per-execution correlation IDs,
structured file sinks, retention policy - SAD Cap. 24) is intentionally out
of scope here. Module Specifications does not reserve a dedicated chapter
for Log Engine, so this adapter provides only the minimum LoadConfiguration
needs today to comply with AI Coding Standards Sec.12 ("nunca utilizar
print()"). It should be revisited and likely extended once Log Engine is
formally scheduled as its own module.
"""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger

from qa_servicenow_assistant.application.ports.log_port import LogPort


class LoguruLogAdapter(LogPort):
    """Minimal Loguru adapter satisfying LogPort.

    Intended to be instantiated once by the composition root (bootstrap/),
    since it reconfigures the process-wide Loguru sink on construction.
    """

    def __init__(self, level: str = "INFO") -> None:
        logger.remove()
        logger.add(sys.stderr, level=level)
        self._logger = logger

    def debug(self, message: str, **context: Any) -> None:
        self._logger.bind(**context).debug(message)

    def info(self, message: str, **context: Any) -> None:
        self._logger.bind(**context).info(message)

    def warning(self, message: str, **context: Any) -> None:
        self._logger.bind(**context).warning(message)

    def error(self, message: str, **context: Any) -> None:
        self._logger.bind(**context).error(message)
