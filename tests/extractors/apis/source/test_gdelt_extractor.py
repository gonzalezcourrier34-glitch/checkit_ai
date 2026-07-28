"""Tests légers de l'extracteur GDELT DOC 2.0."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

import src.extractors.apis.source.gdelt_extractor as module
from src.extractors.apis.api_extractor import (
    ApiExtractionStoppedError,
    ApiRequestError
)


# Configuration

def build_source(**overrides: Any) -> dict[str, Any]:
    """Construit une configuration GDELT minimale."""

    source = {
        "source_id": "gdelt",
        "name": "GDELT",
        "endpoint": "https://api.gdeltproject.org/api/v2/doc/doc",
        "role": "acquisition",
        "max_articles": 10,
        "max_article_age_days": 30,
        "request_delay_seconds": 5
    }
    source.update(overrides)
    return source


# Requêtes configurées

def test_get_configured_queries_returns_structured_queries(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = [
        {
            "language": "fr",
            "theme": "ENV_CLIMATECHANGE"
        }
    ]

    monkeypatch.setattr(
        module,
        "get_queries_configuration",
        lambda source: expected
    )

    assert module.get_configured_queries({}) == expected


def test_get_configured_queries_uses_root_fallback(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    source = {
        "language": "fr",
        "theme": "ENV_CLIMATECHANGE"
    }

    monkeypatch.setattr(
        module,
        "get_queries_configuration",
        lambda current_source: []
    )

    assert module.get_configured_queries(source) == [
        source
    ]


def test_merge_gdelt_query_overrides_root_values() -> None:
    source = {
        "language": "fr",
        "theme": "GENERAL",
        "max_articles": 20
    }
    query = {
        "language": "en",
        "theme": "ENV_CLIMATECHANGE"
    }

    assert module.merge_gdelt_query(
        source,
        query
    ) == {
        "language": "en",
        "theme": "ENV_CLIMATECHANGE",
        "max_articles": 20
    }


# Filtres

def test_get_languages_normalizes_values() -> None:
    assert module.get_languages({
        "languages": [
            "FR",
            "En",
            "fr"
        ]
    }) == [
        "fr",
        "en"
    ]


def test_get_themes_normalizes_values() -> None:
    assert module.get_themes({
        "themes": [
            "ENV_CLIMATECHANGE",
            "TERROR",
            "ENV_CLIMATECHANGE"
        ]
    }) == [
        "ENV_CLIMATECHANGE",
        "TERROR"
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("fr", "french"),
        ("FR", "french"),
        ("en", "english"),
        ("spanish", "spanish"),
        ("", "")
    ]
)
def test_normalize_gdelt_language(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_gdelt_language(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ENV_CLIMATECHANGE", "theme:ENV_CLIMATECHANGE"),
        ("theme:ENV_CLIMATECHANGE", "theme:ENV_CLIMATECHANGE"),
        ("climate change", "climate change"),
        ("", ""),
        (None, "")
    ]
)
def test_normalize_gdelt_theme(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_gdelt_theme(value) == expected


@pytest.mark.parametrize(
    ("language", "theme", "expected"),
    [
        (
            "fr",
            "ENV_CLIMATECHANGE",
            "theme:ENV_CLIMATECHANGE sourcelang:french"
        ),
        (
            "en",
            "",
            "sourcelang:english"
        ),
        (
            "",
            "TERROR",
            "theme:TERROR"
        ),
        (
            "",
            "",
            "news"
        )
    ]
)
def test_build_gdelt_query(
    language: Any,
    theme: Any,
    expected: str
) -> None:
    assert module.build_gdelt_query(
        language,
        theme
    ) == expected


# Période

def test_normalize_gdelt_timespan_uses_default(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 30
    )

    assert module.normalize_gdelt_timespan({}) == "30d"


@pytest.mark.parametrize(
    ("timespan", "expected"),
    [
        ("10d", "10d"),
        ("2 weeks", "2weeks"),
        ("12h", "12h"),
        ("30min", "30min")
    ]
)
def test_normalize_gdelt_timespan_accepts_valid_values(
    monkeypatch: pytest.MonkeyPatch,
    timespan: str,
    expected: str
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 30
    )

    assert module.normalize_gdelt_timespan({
        "timespan": timespan
    }) == expected


@pytest.mark.parametrize(
    "timespan",
    [
        "invalid",
        "0d",
        "-5d",
        "10years"
    ]
)
def test_normalize_gdelt_timespan_uses_limit_for_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
    timespan: str
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 30
    )

    assert module.normalize_gdelt_timespan({
        "timespan": timespan
    }) == "30d"


def test_normalize_gdelt_timespan_reduces_long_period(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 30
    )

    assert module.normalize_gdelt_timespan({
        "timespan": "3months"
    }) == "30d"


# Temporisation

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (10, 10.0),
        ("7.5", 7.5),
        (1, module.GDELT_MIN_REQUEST_INTERVAL_SECONDS),
        (0, module.GDELT_MIN_REQUEST_INTERVAL_SECONDS),
        ("invalid", module.GDELT_MIN_REQUEST_INTERVAL_SECONDS),
        (None, module.GDELT_MIN_REQUEST_INTERVAL_SECONDS)
    ]
)
def test_get_gdelt_request_interval(
    value: Any,
    expected: float
) -> None:
    assert module.get_gdelt_request_interval({
        "request_delay_seconds": value
    }) == expected


def test_wait_for_gdelt_rate_limit_without_wait(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    times = iter([
        20.0,
        20.0
    ])
    sleep_calls: list[float] = []

    monkeypatch.setattr(
        module,
        "monotonic",
        lambda: next(times)
    )
    monkeypatch.setattr(
        module,
        "sleep",
        lambda duration: sleep_calls.append(duration)
    )
    monkeypatch.setattr(
        module,
        "_last_gdelt_request_at",
        10.0
    )

    module.wait_for_gdelt_rate_limit(5.0)

    assert sleep_calls == []
    assert module._last_gdelt_request_at == 20.0


def test_wait_for_gdelt_rate_limit_waits_remaining_time(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    times = iter([
        12.0,
        15.0
    ])
    sleep_calls: list[float] = []

    monkeypatch.setattr(
        module,
        "monotonic",
        lambda: next(times)
    )
    monkeypatch.setattr(
        module,
        "sleep",
        lambda duration: sleep_calls.append(duration)
    )
    monkeypatch.setattr(
        module,
        "_last_gdelt_request_at",
        10.0
    )

    module.wait_for_gdelt_rate_limit(5.0)

    assert sleep_calls == [
        3.0
    ]
    assert module._last_gdelt_request_at == 15.0


# Erreurs

@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "error": "Erreur principale"
            },
            "Erreur principale"
        ),
        (
            {
                "message": "Erreur secondaire"
            },
            "Erreur secondaire"
        ),
        (
            {
                "status": "error"
            },
            "error"
        ),
        (
            {},
            ""
        )
    ]
)
def test_get_gdelt_error_message(
    data: Mapping[str, Any],
    expected: str
) -> None:
    assert module.get_gdelt_error_message(data) == expected


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("One every 5 seconds", True),
        ("Too many requests", True),
        ("Rate limit exceeded", True),
        ("High-traffic server", True),
        ("Erreur inconnue", False),
        ("", False),
        (None, False)
    ]
)
def test_is_gdelt_rate_limit_message(
    message: Any,
    expected: bool
) -> None:
    assert module.is_gdelt_rate_limit_message(message) is expected


# Réseau

def test_fetch_gdelt_data_returns_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    wait_calls: list[float] = []

    monkeypatch.setattr(
        module,
        "wait_for_gdelt_rate_limit",
        lambda interval: wait_calls.append(interval)
    )
    monkeypatch.setattr(
        module,
        "fetch_json_object",
        lambda **kwargs: {
            "articles": [
                {
                    "url": "https://example.com/article"
                }
            ]
        }
    )

    result = module.fetch_gdelt_data(
        endpoint="https://example.com/api",
        params={
            "query": "news"
        },
        interval_seconds=5
    )

    assert result == {
        "articles": [
            {
                "url": "https://example.com/article"
            }
        ]
    }
    assert wait_calls == [
        5
    ]


def test_fetch_gdelt_data_returns_non_rate_limit_error(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "wait_for_gdelt_rate_limit",
        lambda interval: None
    )
    monkeypatch.setattr(
        module,
        "fetch_json_object",
        lambda **kwargs: {
            "error": "Erreur de requête"
        }
    )

    assert module.fetch_gdelt_data(
        endpoint="https://example.com/api",
        params={},
        interval_seconds=5
    ) == {
        "error": "Erreur de requête"
    }


def test_fetch_gdelt_data_retries_after_rate_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    responses = iter([
        {
            "error": "One every 5 seconds"
        },
        {
            "articles": [
                {
                    "url": "https://example.com/article"
                }
            ]
        }
    ])
    calls = 0

    monkeypatch.setattr(
        module,
        "wait_for_gdelt_rate_limit",
        lambda interval: None
    )

    def fake_fetch_json_object(**kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return next(responses)

    monkeypatch.setattr(
        module,
        "fetch_json_object",
        fake_fetch_json_object
    )

    result = module.fetch_gdelt_data(
        endpoint="https://example.com/api",
        params={},
        interval_seconds=5
    )

    assert result["articles"]
    assert calls == 2


def test_fetch_gdelt_data_stops_after_repeated_rate_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "wait_for_gdelt_rate_limit",
        lambda interval: None
    )
    monkeypatch.setattr(
        module,
        "fetch_json_object",
        lambda **kwargs: {
            "error": "Too many requests"
        }
    )

    with pytest.raises(ApiExtractionStoppedError) as captured:
        module.fetch_gdelt_data(
            endpoint="https://example.com/api",
            params={},
            interval_seconds=5
        )

    assert captured.value.status_code == 429


# Récupération

def test_request_gdelt_articles_rejects_invalid_endpoint() -> None:
    with pytest.raises(
        ValueError,
        match="Endpoint GDELT absent ou invalide"
    ):
        module.request_gdelt_articles(
            source=build_source(
                endpoint="invalid"
            ),
            language="fr",
            theme="ENV_CLIMATECHANGE",
            max_records=10
        )


def test_request_gdelt_articles_builds_request(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "normalize_gdelt_timespan",
        lambda source: "30d"
    )
    monkeypatch.setattr(
        module,
        "get_gdelt_request_interval",
        lambda source: 5.0
    )

    def fake_fetch_gdelt_data(
        endpoint: str,
        params: Mapping[str, Any],
        interval_seconds: float
    ) -> dict[str, Any]:
        captured.update({
            "endpoint": endpoint,
            "params": dict(params),
            "interval_seconds": interval_seconds
        })
        return {
            "articles": [
                {
                    "url": "https://example.com/article-1"
                },
                "invalid",
                {
                    "url": "https://example.com/article-2"
                }
            ]
        }

    monkeypatch.setattr(
        module,
        "fetch_gdelt_data",
        fake_fetch_gdelt_data
    )

    result = module.request_gdelt_articles(
        source=build_source(),
        language="fr",
        theme="ENV_CLIMATECHANGE",
        max_records=10
    )

    assert result == [
        {
            "url": "https://example.com/article-1"
        },
        {
            "url": "https://example.com/article-2"
        }
    ]
    assert captured["params"] == {
        "query": "theme:ENV_CLIMATECHANGE sourcelang:french",
        "mode": "artlist",
        "format": "json",
        "maxrecords": 10,
        "sort": "datedesc",
        "timespan": "30d"
    }
    assert captured["interval_seconds"] == 5.0


def test_request_gdelt_articles_respects_maximum(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "normalize_gdelt_timespan",
        lambda source: "30d"
    )
    monkeypatch.setattr(
        module,
        "get_gdelt_request_interval",
        lambda source: 5.0
    )
    monkeypatch.setattr(
        module,
        "fetch_gdelt_data",
        lambda endpoint, params, interval_seconds: {
            "articles": [
                {
                    "url": f"https://example.com/article-{index}"
                }
                for index in range(20)
            ]
        }
    )

    result = module.request_gdelt_articles(
        source=build_source(),
        language="",
        theme="",
        max_records=3
    )

    assert len(result) == 3


def test_request_gdelt_articles_raises_request_error(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "normalize_gdelt_timespan",
        lambda source: "30d"
    )
    monkeypatch.setattr(
        module,
        "get_gdelt_request_interval",
        lambda source: 5.0
    )
    monkeypatch.setattr(
        module,
        "fetch_gdelt_data",
        lambda endpoint, params, interval_seconds: {
            "error": "Paramètre invalide"
        }
    )
    monkeypatch.setattr(
        module,
        "raise_if_fatal_api_error",
        lambda error, source_name: "Paramètre invalide"
    )

    with pytest.raises(ApiRequestError):
        module.request_gdelt_articles(
            source=build_source(),
            language="fr",
            theme="ENV_CLIMATECHANGE",
            max_records=10
        )


# Itérateur

def test_iter_gdelt_items_returns_nothing_for_zero_maximum() -> None:
    assert list(
        module.iter_gdelt_items(
            build_source(),
            0
        )
    ) == []


def test_iter_gdelt_items_enriches_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_configured_queries",
        lambda source: [
            {
                "language": "fr",
                "theme": "ENV_CLIMATECHANGE"
            }
        ]
    )
    monkeypatch.setattr(
        module,
        "request_gdelt_articles",
        lambda **kwargs: [
            {
                "url": "https://example.com/article-1"
            },
            {
                "url": "https://example.com/article-2"
            }
        ]
    )

    result = list(
        module.iter_gdelt_items(
            build_source(),
            2
        )
    )

    assert result == [
        (
            "theme:ENV_CLIMATECHANGE sourcelang:french",
            0,
            {
                "url": "https://example.com/article-1",
                "_requested_language": "fr",
                "_requested_theme": "ENV_CLIMATECHANGE"
            }
        ),
        (
            "theme:ENV_CLIMATECHANGE sourcelang:french",
            1,
            {
                "url": "https://example.com/article-2",
                "_requested_language": "fr",
                "_requested_theme": "ENV_CLIMATECHANGE"
            }
        )
    ]


def test_iter_gdelt_items_respects_maximum(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_configured_queries",
        lambda source: [
            {
                "language": "fr",
                "theme": "ENV_CLIMATECHANGE"
            }
        ]
    )
    monkeypatch.setattr(
        module,
        "request_gdelt_articles",
        lambda **kwargs: [
            {
                "url": f"https://example.com/article-{index}"
            }
            for index in range(10)
        ]
    )

    result = list(
        module.iter_gdelt_items(
            build_source(),
            3
        )
    )

    assert len(result) == 3


# Construction d'article

def test_build_gdelt_article_rejects_invalid_item() -> None:
    assert module.build_gdelt_article(
        item="invalid",
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


@pytest.mark.parametrize(
    "item",
    [
        {},
        {
            "url": "invalid"
        },
        {
            "url_mobile": "invalid"
        }
    ]
)
def test_build_gdelt_article_rejects_invalid_url(
    item: Mapping[str, Any]
) -> None:
    assert module.build_gdelt_article(
        item=item,
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_gdelt_article_builds_standard_article(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_build_standard_article(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return dict(kwargs)

    monkeypatch.setattr(
        module,
        "build_standard_article",
        fake_build_standard_article
    )

    result = module.build_gdelt_article(
        item={
            "url": "https://example.com/article",
            "title": "Titre de l'article",
            "socialimage": "https://example.com/image.jpg",
            "seendate": "20260728T100000Z",
            "language": "French",
            "_requested_language": "fr",
            "_requested_theme": "ENV_CLIMATECHANGE"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert result == captured
    assert captured["identifier"] == "https://example.com/article"
    assert captured["source"] == "GDELT"
    assert captured["title"] == "Titre de l'article"
    assert captured["language"] == "french"
    assert captured["category"] == "ENV_CLIMATECHANGE"
    assert captured["image_url"] == "https://example.com/image.jpg"


def test_build_gdelt_article_uses_fallback_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_gdelt_article(
        item={
            "url_mobile": "https://example.com/mobile",
            "title": "Titre",
            "language": "",
            "_requested_language": "fr",
            "_requested_theme": ""
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert captured["identifier"] == "https://example.com/mobile"
    assert captured["language"] == "fr"
    assert captured["category"] == "general"


def test_build_gdelt_article_removes_invalid_image(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_gdelt_article(
        item={
            "url": "https://example.com/article",
            "socialimage": "invalid-image"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert captured["image_url"] == ""


# Validation

@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (
            None,
            (
                False,
                "resultat_gdelt_invalide"
            )
        ),
        (
            {},
            (
                False,
                "url_gdelt_invalide"
            )
        ),
        (
            {
                "url": "invalid"
            },
            (
                False,
                "url_gdelt_invalide"
            )
        ),
        (
            {
                "url_mobile": "https://example.com/mobile"
            },
            (
                True,
                ""
            )
        ),
        (
            {
                "url": "https://example.com/article"
            },
            (
                True,
                ""
            )
        )
    ]
)
def test_validate_gdelt_item(
    item: Any,
    expected: tuple[bool, str]
) -> None:
    assert module.validate_gdelt_item(
        item=item,
        filters={},
        source={}
    ) == expected


# API publique

def test_load_gdelt_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        type(module.GDELT_EXTRACTOR),
        "reload_source",
        lambda self: {
            "source_id": "gdelt"
        }
    )

    assert module.load_gdelt_source() == {
        "source_id": "gdelt"
    }


def test_extract_articles_from_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()
    captured: dict[str, Any] = {}
    source = build_source()

    def fake_extract_api_from_source(
        *,
        source: Mapping[str, Any],
        adapter: Any
    ) -> Any:
        captured.update({
            "source": source,
            "adapter": adapter
        })
        return expected

    monkeypatch.setattr(
        module,
        "extract_api_from_source",
        fake_extract_api_from_source
    )

    result = module.extract_articles_from_source(source)

    assert result is expected
    assert captured["source"] is source
    assert captured["adapter"] is module.GDELT_ADAPTER


def test_extract_all_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()

    monkeypatch.setattr(
        type(module.GDELT_EXTRACTOR),
        "run",
        lambda self: expected
    )

    assert module.extract_all_articles() is expected