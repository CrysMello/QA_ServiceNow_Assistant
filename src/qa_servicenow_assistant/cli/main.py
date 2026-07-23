"""CLI (Module Specifications Cap. 21 - "Interface de linha de comando";
ADR-0016 - no dedicated SAD chapter exists).

Presentation-layer entry point (SAD 5.4 - "CLI | Presentation | Entrada
da aplicacao"): parses command-line arguments into a
LoadConfigurationRequest, hands it to ApplicationController (the
composition root, Prompt 21/ADR-0015) to bootstrap the application, and
maps the outcome to a process exit code and a human-readable message -
never a raw Python traceback (SAD 2.3 - "Confiabilidade: Garantir
execucao previsivel").

Implements SAD 6.3/26.6 passos 1-3 and 5 (inicializacao, configuracao,
Base de Conhecimento, navegador). Passos 4 (planilha Excel), 6
(autenticacao manual) and 7 (Workflow Engine) are deliberately out of
scope - see ADR-0016 and ApplicationController's own docstring for the
underlying reasons (no Excel Importer, no concrete Workflow can be built
without it).

No file-existence/URL-format validation happens in this module (e.g. via
Typer/Click's own `exists=True`): every value is validated exactly once,
by the already-existing ConfigurationValidator, reached through
ApplicationController - SAD 21.8 ("Todas as configuracoes devem ser
centralizadas no Configuration Manager") is read here as "validated in
one place", to avoid two sources of truth with potentially inconsistent
messages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from qa_servicenow_assistant.application.use_cases.load_configuration import (
    LoadConfigurationRequest,
)
from qa_servicenow_assistant.bootstrap.application_controller import (
    ApplicationController,
)
from qa_servicenow_assistant.domain.exceptions.base import QaServiceNowAssistantError
from qa_servicenow_assistant.domain.exceptions.browser import BrowserError
from qa_servicenow_assistant.domain.exceptions.configuration import ConfigurationError
from qa_servicenow_assistant.domain.exceptions.knowledge_base import KnowledgeBaseError

app = typer.Typer(
    add_completion=False,
    help="QA ServiceNow Assistant - bootstraps configuration, the Knowledge Base and the browser.",
)

_EXIT_CONFIGURATION_ERROR = 1
_EXIT_KNOWLEDGE_BASE_ERROR = 2
_EXIT_BROWSER_ERROR = 3
_EXIT_KNOWN_DOMAIN_ERROR = 4
_EXIT_UNEXPECTED_ERROR = 5


def _fail(message: str, *, exit_code: int) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(code=exit_code)


@app.command()
def run(
    spreadsheet: Path = typer.Option(
        ..., "--spreadsheet", "-s", help="Path to the input .xlsx spreadsheet (RF-001)."
    ),
    knowledge_base: Path = typer.Option(
        ..., "--knowledge-base", "-k", help="Path to the Knowledge Base directory."
    ),
    instance_url: str = typer.Option(
        ..., "--instance-url", "-u", help="ServiceNow instance URL (e.g. https://devXXXX.service-now.com)."
    ),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Optional JSON configuration file overriding defaults."
    ),
    knowledge_base_version: str = typer.Option(
        "1.0", "--knowledge-base-version", help="Expected Knowledge Base manifest version."
    ),
    skip_browser_check: bool = typer.Option(
        False,
        "--skip-browser-check",
        help="Skip launching a real browser during bootstrap validation.",
    ),
) -> None:
    """Bootstrap the application: load configuration, load the Knowledge
    Base and, unless skipped, validate that a browser can be launched
    (SAD 6.3 passos 1-5). Does not read the spreadsheet or run a workflow
    (ADR-0016)."""
    request = LoadConfigurationRequest(
        spreadsheet_path=spreadsheet,
        knowledge_base_path=knowledge_base,
        instance_url=instance_url,
        config_file_path=config,
    )

    try:
        controller = ApplicationController(
            request, expected_knowledge_base_version=knowledge_base_version
        )
    except ConfigurationError as error:
        _fail(f"Configuration error: {error}", exit_code=_EXIT_CONFIGURATION_ERROR)
        return
    except KnowledgeBaseError as error:
        _fail(f"Knowledge Base error: {error}", exit_code=_EXIT_KNOWLEDGE_BASE_ERROR)
        return
    except QaServiceNowAssistantError as error:
        _fail(f"Initialization error: {error}", exit_code=_EXIT_KNOWN_DOMAIN_ERROR)
        return
    except Exception as error:  # noqa: BLE001 - intentional isolation boundary: this
        # is the outermost layer of the whole application (SAD 5.4 -
        # "CLI: Presentation: Entrada da aplicacao"); no exception, of any
        # type, may ever surface to the user as a raw Python traceback.
        _fail(f"Unexpected error: {error}", exit_code=_EXIT_UNEXPECTED_ERROR)
        return

    known_page_count = len(controller.knowledge.get_known_pages())
    typer.echo(f"Configuration loaded for instance {instance_url!r}.")
    typer.echo(f"Knowledge Base loaded: {known_page_count} known page(s).")

    if skip_browser_check:
        typer.echo("Browser check skipped (--skip-browser-check).")
    else:
        try:
            controller.start()
            typer.echo("Browser launched successfully.")
        except BrowserError as error:
            _fail(f"Browser error: {error}", exit_code=_EXIT_BROWSER_ERROR)
            return
        finally:
            controller.stop()

    typer.echo("Application bootstrap completed successfully.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
