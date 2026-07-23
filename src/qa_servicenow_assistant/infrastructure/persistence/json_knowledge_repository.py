"""JSON-file-based implementation of KnowledgeRepository (SAD 10.3 -
"Knowledge Adapter | KnowledgeRepository | JSON | Carregar a Base de
Conhecimento"; SAD Cap. 11).

Loads the Knowledge Base eagerly at construction time (SAD 11.4 -
"Carregar a Base de Conhecimento na inicializacao"; same eager-I/O-in-
constructor precedent as LoguruLogAdapter, JsonFileCheckpointRepository,
FileReportRepository and ZipExportRepository), builds an in-memory
KnowledgeBaseIndex once (SAD 11.6 - Estrategia de Cache), and never
re-reads the filesystem afterward.

JSON schema (this project's own interpretation - no example Knowledge
Base or schema is provided by any document; ServiceNow Knowledge Builder,
which actually produces these files, is external and out of scope):

    manifest.json (required)      {"version": "1.0", "generated_at": "...", "metadata": {...}}
    pages.json (optional)         [{"key", "url_pattern", "title"?, "fingerprint"?,
                                     "required_element_keys"?, "metadata"?}, ...]
    elements.json (optional)      [{"key", "page_key", "description"?, "attributes"?}, ...]
    selectors.json (optional)     [{"element_key", "strategy", "value", "priority"}, ...]
    workflows.json (optional)     [{"key", "description"?, "step_keys"?}, ...]
    fingerprints.json (optional)  {"<page_key>": "<fingerprint>", ...}

SAD 11.7 distinguishes two failure tiers, followed literally here:
"Manifest inexistente -> Abortar" and "JSON invalido -> Interromper
carregamento" both raise (KnowledgeBaseNotFoundError/
KnowledgeBaseFormatError); "Arquivo ausente [demais arquivos] ->
Registrar diagnostico detalhado" is soft - a missing optional file is
logged as a warning and treated as an empty collection, not an abort.

fingerprints.json values are merged into the loaded KnowledgePage.fingerprint
field (fingerprints.json takes precedence over an inline "fingerprint" in
pages.json, being the more specific artifact), so existing consumers of
KnowledgePage.fingerprint see it populated regardless of which file it
came from.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Sequence, TypeVar

from qa_servicenow_assistant.application.ports.knowledge_repository_port import (
    KnowledgeRepository,
)
from qa_servicenow_assistant.application.ports.log_port import LogPort
from qa_servicenow_assistant.domain.entities.knowledge_element import KnowledgeElement
from qa_servicenow_assistant.domain.entities.knowledge_page import KnowledgePage
from qa_servicenow_assistant.domain.exceptions.knowledge_base import (
    KnowledgeBaseFormatError,
    KnowledgeBaseNotFoundError,
    IncompatibleKnowledgeBaseVersionError,
)
from qa_servicenow_assistant.domain.services.knowledge_base_index import (
    KnowledgeBaseIndex,
)
from qa_servicenow_assistant.domain.value_objects.knowledge_base_artifacts import (
    KnowledgeBaseArtifacts,
)
from qa_servicenow_assistant.domain.value_objects.knowledge_manifest import (
    KnowledgeManifest,
)
from qa_servicenow_assistant.domain.value_objects.knowledge_selector import (
    KnowledgeSelector,
)
from qa_servicenow_assistant.domain.value_objects.knowledge_workflow import (
    KnowledgeWorkflow,
)
from qa_servicenow_assistant.domain.value_objects.selector import Selector

T = TypeVar("T")

_MANIFEST_FILE = "manifest.json"
_PAGES_FILE = "pages.json"
_ELEMENTS_FILE = "elements.json"
_SELECTORS_FILE = "selectors.json"
_WORKFLOWS_FILE = "workflows.json"
_FINGERPRINTS_FILE = "fingerprints.json"


class JsonKnowledgeRepository(KnowledgeRepository):
    def __init__(
        self,
        directory: Path,
        log_port: LogPort,
        expected_version: str = "1.0",
    ) -> None:
        self._directory = Path(directory)
        self._log_port = log_port
        self._expected_version = expected_version

        if not self._directory.is_dir():
            raise KnowledgeBaseNotFoundError(
                f"Knowledge Base directory not found: {self._directory}"
            )

        self._manifest = self._load_manifest()
        if self._manifest.version != self._expected_version:
            raise IncompatibleKnowledgeBaseVersionError(
                f"Knowledge Base version {self._manifest.version!r} is not supported "
                f"(expected {self._expected_version!r})"
            )

        pages = self._load_collection(_PAGES_FILE, _parse_pages)
        elements = self._load_collection(_ELEMENTS_FILE, _parse_elements)
        selectors = self._load_collection(_SELECTORS_FILE, _parse_selectors)
        workflows = self._load_collection(_WORKFLOWS_FILE, _parse_workflows)
        fingerprints = self._load_fingerprints()

        pages = tuple(
            replace(page, fingerprint=fingerprints.get(page.key, page.fingerprint))
            for page in pages
        )

        self._index = KnowledgeBaseIndex(
            KnowledgeBaseArtifacts(
                manifest=self._manifest,
                pages=pages,
                elements=elements,
                selectors=selectors,
                workflows=workflows,
            )
        )

        self._log_port.info(
            "Knowledge Base loaded",
            directory=str(self._directory),
            version=self._manifest.version,
            page_count=len(pages),
            element_count=len(elements),
            selector_count=len(selectors),
            workflow_count=len(workflows),
        )

    def get_known_pages(self) -> Sequence[KnowledgePage]:
        return self._index.all_pages()

    def get_page(self, key: str) -> KnowledgePage | None:
        return self._index.get_page(key)

    def get_element(self, key: str) -> KnowledgeElement | None:
        return self._index.get_element(key)

    def get_selector(self, element_key: str) -> Selector | None:
        return self._index.get_selector(element_key)

    def get_workflow(self, key: str) -> KnowledgeWorkflow | None:
        return self._index.get_workflow(key)

    def get_fingerprint(self, page_key: str) -> str | None:
        return self._index.get_fingerprint(page_key)

    def validate_version(self) -> bool:
        """Always True once construction has succeeded - an incompatible
        version aborts __init__ (SAD 11.8: detection happens during
        initialization, not lazily on demand)."""
        return self._manifest.version == self._expected_version

    def _load_manifest(self) -> KnowledgeManifest:
        path = self._directory / _MANIFEST_FILE
        if not path.is_file():
            raise KnowledgeBaseNotFoundError(f"Required Knowledge Base file not found: {path}")
        data = self._read_json(path)
        try:
            return _parse_manifest(data)
        except (KeyError, TypeError, AttributeError) as error:
            raise KnowledgeBaseFormatError(f"Malformed {_MANIFEST_FILE}") from error

    def _load_collection(self, file_name: str, parser: Callable[[Any], T]) -> T:
        raw = self._read_optional_json(file_name, [])
        try:
            return parser(raw)
        except (KeyError, TypeError, AttributeError) as error:
            raise KnowledgeBaseFormatError(f"Malformed entries in {file_name}") from error

    def _load_fingerprints(self) -> dict[str, str]:
        raw = self._read_optional_json(_FINGERPRINTS_FILE, {})
        try:
            return dict(raw)
        except (TypeError, ValueError) as error:
            raise KnowledgeBaseFormatError(f"Malformed {_FINGERPRINTS_FILE}") from error

    def _read_optional_json(self, file_name: str, default: Any) -> Any:
        path = self._directory / file_name
        if not path.is_file():
            self._log_port.warning(
                "Knowledge Base file missing, treating as empty", file=str(path)
            )
            return default
        return self._read_json(path)

    def _read_json(self, path: Path) -> Any:
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except OSError as error:
            raise KnowledgeBaseNotFoundError(f"Failed to read Knowledge Base file: {path}") from error
        except json.JSONDecodeError as error:
            raise KnowledgeBaseFormatError(f"Invalid JSON in Knowledge Base file: {path}") from error


def _parse_manifest(data: dict[str, Any]) -> KnowledgeManifest:
    return KnowledgeManifest(
        version=data["version"],
        generated_at=data.get("generated_at"),
        metadata=dict(data.get("metadata") or {}),
    )


def _parse_pages(data: list[dict[str, Any]]) -> tuple[KnowledgePage, ...]:
    return tuple(
        KnowledgePage(
            key=entry["key"],
            url_pattern=entry["url_pattern"],
            title=entry.get("title"),
            fingerprint=entry.get("fingerprint"),
            required_element_keys=tuple(entry.get("required_element_keys") or ()),
            metadata=dict(entry.get("metadata") or {}),
        )
        for entry in data
    )


def _parse_elements(data: list[dict[str, Any]]) -> tuple[KnowledgeElement, ...]:
    return tuple(
        KnowledgeElement(
            key=entry["key"],
            page_key=entry["page_key"],
            description=entry.get("description", ""),
            attributes=dict(entry.get("attributes") or {}),
        )
        for entry in data
    )


def _parse_selectors(data: list[dict[str, Any]]) -> tuple[KnowledgeSelector, ...]:
    return tuple(
        KnowledgeSelector(
            element_key=entry["element_key"],
            selector=Selector(
                strategy=entry["strategy"], value=entry["value"], priority=entry["priority"]
            ),
        )
        for entry in data
    )


def _parse_workflows(data: list[dict[str, Any]]) -> tuple[KnowledgeWorkflow, ...]:
    return tuple(
        KnowledgeWorkflow(
            key=entry["key"],
            description=entry.get("description", ""),
            step_keys=tuple(entry.get("step_keys") or ()),
        )
        for entry in data
    )
