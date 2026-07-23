"""Integration tests for the CLI (ADR-0016), using Typer's CliRunner
against the real Typer app - exercises real configuration loading, real
Knowledge Base loading and (for one test) a real Chromium browser launch,
the same "real adapters over fakes" philosophy used for
ApplicationController's own tests.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from qa_servicenow_assistant.cli.main import app

runner = CliRunner()


def _write_knowledge_base(directory: Path, *, version: str = "1.0") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "manifest.json").write_text(json.dumps({"version": version}), encoding="utf-8")


def _base_args(tmp_path: Path, *, kb_version: str = "1.0", with_kb: bool = True) -> list[str]:
    spreadsheet = tmp_path / "input.xlsx"
    spreadsheet.write_bytes(b"fake-xlsx-content")

    knowledge_base_dir = tmp_path / "knowledge_base"
    if with_kb:
        _write_knowledge_base(knowledge_base_dir, version=kb_version)
    else:
        knowledge_base_dir.mkdir(parents=True, exist_ok=True)

    # Redirect checkpoints/reporting/export under tmp_path so the test
    # never writes outside it, same rationale as the ApplicationController
    # integration tests.
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "checkpoints": {"directory": str(tmp_path / "checkpoints")},
                "reporting": {"directory": str(tmp_path / "reports")},
                "export": {"directory": str(tmp_path / "exports")},
            }
        ),
        encoding="utf-8",
    )

    return [
        "--spreadsheet", str(spreadsheet),
        "--knowledge-base", str(knowledge_base_dir),
        "--instance-url", "https://dev12345.service-now.com",
        "--config", str(config_file),
    ]


def test_successful_bootstrap_with_browser_check_skipped_exits_zero(tmp_path: Path) -> None:
    args = _base_args(tmp_path) + ["--skip-browser-check"]

    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.output
    assert "Configuration loaded" in result.output
    assert "Knowledge Base loaded: 0 known page(s)" in result.output
    assert "Browser check skipped" in result.output
    assert "Application bootstrap completed successfully" in result.output


def test_successful_bootstrap_with_real_browser_launch(tmp_path: Path) -> None:
    args = _base_args(tmp_path)

    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.output
    assert "Browser launched successfully" in result.output
    assert "Application bootstrap completed successfully" in result.output


def test_invalid_instance_url_exits_with_configuration_error_code(tmp_path: Path) -> None:
    args = _base_args(tmp_path, with_kb=False)
    # Overwrite the instance URL with an invalid one.
    args[args.index("--instance-url") + 1] = "not-a-valid-url"
    args.append("--skip-browser-check")

    result = runner.invoke(app, args)

    assert result.exit_code == 1, result.output
    assert "Configuration error" in result.output


def test_missing_knowledge_base_manifest_exits_with_knowledge_base_error_code(tmp_path: Path) -> None:
    args = _base_args(tmp_path, with_kb=False) + ["--skip-browser-check"]

    result = runner.invoke(app, args)

    assert result.exit_code == 2, result.output
    assert "Knowledge Base error" in result.output


def test_incompatible_knowledge_base_version_exits_with_knowledge_base_error_code(tmp_path: Path) -> None:
    args = _base_args(tmp_path, kb_version="9.9") + ["--skip-browser-check"]

    result = runner.invoke(app, args)

    assert result.exit_code == 2, result.output
    assert "Knowledge Base error" in result.output


def test_custom_knowledge_base_version_is_accepted(tmp_path: Path) -> None:
    args = _base_args(tmp_path, kb_version="2.5") + [
        "--skip-browser-check",
        "--knowledge-base-version", "2.5",
    ]

    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.output


def test_missing_required_option_is_rejected_by_typer(tmp_path: Path) -> None:
    args = _base_args(tmp_path)
    spreadsheet_index = args.index("--spreadsheet")
    del args[spreadsheet_index : spreadsheet_index + 2]  # drop the required option entirely

    result = runner.invoke(app, args)

    assert result.exit_code != 0
