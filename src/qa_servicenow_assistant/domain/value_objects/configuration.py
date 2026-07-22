"""Immutable configuration value objects for the QA ServiceNow Assistant.

Categories follow SAD Capitulo 21.3 (Categorias de Configuracao). All values
are optional with sensible defaults except the three fields required by
RF-001 (SRS): spreadsheet_path, knowledge_base_path and instance_url.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class BrowserConfiguration:
    """Browser automation parameters (SAD 21.3 - categoria Browser)."""

    headless: bool = True
    timeout_ms: int = 30_000
    viewport_width: int = 1920
    viewport_height: int = 1080


@dataclass(frozen=True)
class RetryConfiguration:
    """Retry policy parameters (SAD 21.3 - categoria Retry / SAD Cap. 19)."""

    max_attempts: int = 3
    backoff_strategy: str = "exponential"
    base_delay_ms: int = 2_000


@dataclass(frozen=True)
class NavigationConfiguration:
    """Navigation timeouts (SAD 21.3 - categoria Navigation)."""

    timeout_ms: int = 30_000


@dataclass(frozen=True)
class LoggingConfiguration:
    """Logging level and destination (SAD 21.3 - categoria Logs)."""

    level: str = "INFO"
    directory: Path = Path("logs")


@dataclass(frozen=True)
class ScreenshotConfiguration:
    """Evidence capture parameters (SAD 21.3 - categoria Evidencias)."""

    enabled: bool = True
    directory: Path = Path("screenshots")


@dataclass(frozen=True)
class ReportingConfiguration:
    """Report output parameters (SAD 21.3 - categoria Relatorios).

    format is restricted to {"html", "json"}, matching SRS Cap. 7 (Dados e
    Artefatos), which is narrower than the illustrative list in SAD 22.5.
    """

    format: str = "html"
    directory: Path = Path("reports")


@dataclass(frozen=True)
class CheckpointConfiguration:
    """Checkpoint persistence parameters (SAD Cap. 20)."""

    directory: Path = Path("temp/checkpoints")


@dataclass(frozen=True)
class ApplicationConfiguration:
    """Aggregate, immutable configuration for a single execution.

    Immutability (frozen dataclass) satisfies SAD 21.5 "Configuracao
    imutavel: mantem consistencia durante a execucao".
    """

    spreadsheet_path: Path
    knowledge_base_path: Path
    instance_url: str
    browser: BrowserConfiguration = field(default_factory=BrowserConfiguration)
    retry: RetryConfiguration = field(default_factory=RetryConfiguration)
    navigation: NavigationConfiguration = field(default_factory=NavigationConfiguration)
    logging: LoggingConfiguration = field(default_factory=LoggingConfiguration)
    screenshots: ScreenshotConfiguration = field(default_factory=ScreenshotConfiguration)
    reporting: ReportingConfiguration = field(default_factory=ReportingConfiguration)
    checkpoints: CheckpointConfiguration = field(default_factory=CheckpointConfiguration)
