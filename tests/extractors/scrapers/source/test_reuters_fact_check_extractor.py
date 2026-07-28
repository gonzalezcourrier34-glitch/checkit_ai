"""Tests du point d'entrée Reuters Fact Check."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from src.extractors.scrapers.source import reuters_fact_check_extractor as module


# Double de test

class FakeExtractor:
    """Simule uniquement les délégations du point d'entrée."""

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
        """Retourne une configuration simulée."""

        self.reload_calls += 1
        return self.source

    def extract(
        self,
        source: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        """Retourne une liste d'articles simulée."""

        self.received_sources.append(source)
        return self.articles

    def run(self) -> Any:
        """Retourne un résultat d'extraction simulé."""

        self.run_calls += 1
        return self.result


# Configuration

def test_reuters_adapter_is_configured_for_reuters_fact_check() -> None:
    assert module.REUTERS_ADAPTER.source_id == "reuters_fact_check"
    assert module.REUTERS_ADAPTER.default_name == "Reuters Fact Check"


def test_reuters_extractor_uses_adapter_and_sources_file() -> None:
    assert module.REUTERS_EXTRACTOR.adapter is module.REUTERS_ADAPTER
    assert module.REUTERS_EXTRACTOR.sources_file == module.SOURCES_FILE


# Chargement

def test_load_reuters_source_delegates_to_reload_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = {
        "id": "reuters_fact_check",
        "name": "Reuters Fact Check"
    }
    extractor = FakeExtractor(source=expected)

    monkeypatch.setattr(
        module,
        "REUTERS_EXTRACTOR",
        extractor
    )

    result = module.load_reuters_source()

    assert result == expected
    assert extractor.reload_calls == 1


# Extraction

def test_extract_articles_from_source_delegates_to_extractor(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    source: Mapping[str, Any] = {
        "id": "reuters_fact_check"
    }
    expected = [
        {
            "title": "Article Reuters Fact Check"
        }
    ]
    extractor = FakeExtractor(articles=expected)

    monkeypatch.setattr(
        module,
        "REUTERS_EXTRACTOR",
        extractor
    )

    result = module.extract_articles_from_source(source)

    assert result == expected
    assert extractor.received_sources == [source]


def test_extract_reuters_articles_from_source_keeps_compatibility(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    source: Mapping[str, Any] = {
        "id": "reuters_fact_check"
    }
    expected = [
        {
            "title": "Article Reuters Fact Check"
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

    result = module.extract_reuters_articles_from_source(source)

    assert result == expected
    assert received == [source]


def test_extract_all_articles_delegates_to_run(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()
    extractor = FakeExtractor(result=expected)

    monkeypatch.setattr(
        module,
        "REUTERS_EXTRACTOR",
        extractor
    )

    result = module.extract_all_articles()

    assert result is expected
    assert extractor.run_calls == 1