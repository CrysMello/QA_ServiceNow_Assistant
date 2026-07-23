"""BackoffCalculator: pure domain service implementing SAD 19.5 (Politicas
de Retry).

Reuses RetryConfiguration (domain/value_objects/configuration.py, already
validated by ConfigurationValidator since the Configuration Manager
prompt): backoff_strategy is guaranteed to be one of
{"none", "fixed", "linear", "exponential"} by the time it reaches here.
"""

from __future__ import annotations

from qa_servicenow_assistant.domain.value_objects.configuration import (
    RetryConfiguration,
)


class BackoffCalculator:
    """Computes the delay before a given retry attempt."""

    def compute_delay_ms(self, configuration: RetryConfiguration, attempt_number: int) -> int:
        """attempt_number is 1-based: the delay BEFORE retry attempt
        number attempt_number (the original try is not a "retry")."""
        strategy = configuration.backoff_strategy

        if strategy == "none":
            return 0
        if strategy == "fixed":
            return configuration.base_delay_ms
        if strategy == "linear":
            return configuration.base_delay_ms * attempt_number
        if strategy == "exponential":
            return configuration.base_delay_ms * (2 ** (attempt_number - 1))

        # Defensive only: ConfigurationValidator already rejects any other
        # value before an ApplicationConfiguration can be constructed.
        raise ValueError(f"Unknown backoff strategy: {strategy!r}")
