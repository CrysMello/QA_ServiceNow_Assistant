"""Execution outcome tiers (SAD 22.4 - "Status: Sucesso, falha ou
cancelamento")."""

from __future__ import annotations

from enum import Enum


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
