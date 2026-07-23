"""Outcome of ReportingEngine.generate_report() (SAD Cap. 22)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReportGenerationResult:
    """Never raised for expected failures (persistence I/O errors) -
    consistent with Navigation Engine, Page Recognition, Selector
    Resolver, Retry Engine and Checkpoint Engine. UnsupportedReportFormatError
    is the exception, reserved for caller-contract violations (an explicit
    format override outside the configured/supported set)."""

    success: bool
    report_path: Path | None
    error_message: str | None = None
