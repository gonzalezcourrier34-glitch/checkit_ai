"""Tests du point d'entrée AFP Factuel."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from src.extractors.scrapers.source import afp_factuel_extractor as module

class FakeExtractor:
    """Simule les méthodes utilisées par le point d'entrée AFP."""

    def __init__(
        self,
        source: dict[str, Any] | None = None,
        articles: list[dict[str, Any]] | None = None,
        result: Any = None
    ) -> None:
        self.source = source or {}
        self.articles = articles or []
        self.result = result
        self.received_sources: list[Mapping[str, Any]] = []
        self.reload_calls = 0
        self.run_calls = 0

    def reload_source(self) -> dict[str, Any]:
        self.reload_calls += 1
        return self.source

    def extract(
        self,
        source: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        self.received_sources.append(source)
        return self.articles

    def run(self) -> Any:
        self.run_calls += 1
        return self.result
    
# Configuration

def test_afp_adapter_is_configured_for_afp_factuel() -> None:
    assert module.AFP_ADAPTER.source_id == "afp_factuel"
    assert module.AFP_ADAPTER.default_name == "AFP Factuel"


def test_afp_extractor_uses_adapter_and_sources_file() -> None:
    assert module.AFP_EXTRACTOR.adapter is module.AFP_ADAPTER
    assert module.AFP_EXTRACTOR.sources_file == module.SOURCES_FILE


# Chargement

def test_load_afp_source_delegates_to_reload_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = {
        "id": "afp_factuel",
        "name": "AFP Factuel"
    }

    extractor = FakeExtractor(source=expected)

    monkeypatch.setattr(
        module,
        "AFP_EXTRACTOR",
        extractor
    )
    
    result = module.load_afp_source()

    assert result == expected
    assert extractor.reload_calls == 1

# Extraction

def test_extract_articles_from_source_delegates_to_extractor(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    source: Mapping[str, Any] = {
        "id": "afp_factuel"
    }
    expected = [
        {
            "title": "Article AFP"
        }
    ]
    extractor = FakeExtractor(articles=expected)

    monkeypatch.setattr(
        module,
        "AFP_EXTRACTOR",
        extractor
    )

    result = module.extract_articles_from_source(source)

    assert result == expected
    assert extractor.received_sources == [source]
    

def test_extract_afp_articles_from_source_keeps_compatibility(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    source: Mapping[str, Any] = {
        "id": "afp_factuel"
    }
    expected = [
        {
            "title": "Article AFP"
        }
    ]
    received: list[Mapping[str, Any]] = []

    def fake_extract_articles_from_source(
        current_source: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        received.append(current_source)
        return expected

    monkeypatch.setattr(
        module,
        "extract_articles_from_source",
        fake_extract_articles_from_source
    )

    result = module.extract_afp_articles_from_source(source)

    assert result == expected
    assert received == [source]


def test_extract_all_articles_delegates_to_run(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()
    extractor = FakeExtractor(result=expected)

    monkeypatch.setattr(
        module,
        "AFP_EXTRACTOR",
        extractor
    )

    result = module.extract_all_articles()

    assert result is expected
    assert extractor.run_calls == 1