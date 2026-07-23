"""Unit tests for BackoffCalculator (SAD 19.5 - Politicas de Retry)."""

from __future__ import annotations

import pytest

from qa_servicenow_assistant.domain.services.backoff_calculator import (
    BackoffCalculator,
)
from qa_servicenow_assistant.domain.value_objects.configuration import (
    RetryConfiguration,
)


def test_none_strategy_never_waits() -> None:
    calculator = BackoffCalculator()
    configuration = RetryConfiguration(backoff_strategy="none", base_delay_ms=2_000)

    assert calculator.compute_delay_ms(configuration, 1) == 0
    assert calculator.compute_delay_ms(configuration, 3) == 0


def test_fixed_strategy_always_returns_base_delay() -> None:
    calculator = BackoffCalculator()
    configuration = RetryConfiguration(backoff_strategy="fixed", base_delay_ms=2_000)

    assert calculator.compute_delay_ms(configuration, 1) == 2_000
    assert calculator.compute_delay_ms(configuration, 2) == 2_000
    assert calculator.compute_delay_ms(configuration, 3) == 2_000


def test_linear_strategy_scales_with_attempt_number() -> None:
    calculator = BackoffCalculator()
    configuration = RetryConfiguration(backoff_strategy="linear", base_delay_ms=2_000)

    assert calculator.compute_delay_ms(configuration, 1) == 2_000
    assert calculator.compute_delay_ms(configuration, 2) == 4_000
    assert calculator.compute_delay_ms(configuration, 3) == 6_000


def test_exponential_strategy_doubles_each_attempt() -> None:
    calculator = BackoffCalculator()
    configuration = RetryConfiguration(backoff_strategy="exponential", base_delay_ms=2_000)

    assert calculator.compute_delay_ms(configuration, 1) == 2_000
    assert calculator.compute_delay_ms(configuration, 2) == 4_000
    assert calculator.compute_delay_ms(configuration, 3) == 8_000


def test_unknown_strategy_raises_value_error() -> None:
    calculator = BackoffCalculator()
    configuration = RetryConfiguration.__new__(RetryConfiguration)
    object.__setattr__(configuration, "max_attempts", 3)
    object.__setattr__(configuration, "backoff_strategy", "unknown")
    object.__setattr__(configuration, "base_delay_ms", 2_000)

    with pytest.raises(ValueError, match="Unknown backoff strategy"):
        calculator.compute_delay_ms(configuration, 1)
