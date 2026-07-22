"""JSON-based implementation of the ConfigurationRepository port.

JSON was chosen because it is already an approved technology for this
project (SAD 2.5) and requires no additional dependency. YAML and TOML were
not selected because they are not on the approved technology list and would
require adding a new library without prior approval.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_servicenow_assistant.application.ports.configuration_repository import (
    ConfigurationRepository,
)
from qa_servicenow_assistant.domain.exceptions.configuration import (
    ConfigurationFileNotFoundError,
    ConfigurationFormatError,
)


class JsonConfigurationRepository(ConfigurationRepository):
    """Reads configuration data from a JSON file on the local filesystem."""

    def load(self, config_path: Path) -> dict[str, Any]:
        if not config_path.exists():
            raise ConfigurationFileNotFoundError(
                f"Configuration file not found: {config_path}"
            )
        try:
            with config_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ConfigurationFormatError(
                f"Invalid JSON in configuration file {config_path}: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ConfigurationFormatError(
                f"Configuration file must contain a JSON object: {config_path}"
            )
        return data
