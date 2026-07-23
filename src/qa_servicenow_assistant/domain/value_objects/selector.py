"""Selector (SAD 8.4 - "Representar um locator validado")."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Selector:
    """A single candidate or chosen locator.

    strategy is one of the sources in SAD 17.3, reconciled with the finer
    priority list in AI Coding Standards Anexo B (see SelectorResolver
    module docstring): "knowledge_base", "data_testid", "id", "aria",
    "css", "text". "xpath" is a documented gap - see SelectorResolver.
    """

    strategy: str
    value: str
    priority: int
