"""Port for reading raw configuration data (SAD 8.5 - Ports/Contratos)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ConfigurationRepository(ABC):
    """Contract implemented by infrastructure adapters that load raw
    configuration data from an external source (e.g. a JSON file)."""

    @abstractmethod
    def load(self, config_path: Path) -> dict[str, Any]:
        """Load and return the raw configuration mapping at config_path."""
        raise NotImplementedError
