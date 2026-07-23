"""Workflow lifecycle states (SAD 12.4 - Ciclo de Vida)."""

from __future__ import annotations

from enum import Enum


class WorkflowState(str, Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    WAITING = "waiting"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
