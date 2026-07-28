"""Tests légers de l'extracteur Currents News API."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

import src.extractors.apis.source.currents_extractor as module
from src.extractors.apis.api_extractor import (
    ApiAuthenticationError,
    ApiRequestError
)


# Configuration

def build_source(**overrides: Any) -> dict[str, Any]:
    """Construit une configuration Currents minimale."""

    source = {
        "source_id": "currents",
        "name": "Currents News API",
        "endpoint": "https://api.currentsapi.services/v1/search",
        "role": "acquisition",
        "max_articles": 10,
        "max_article_age_days": 30
    }
    source.update(overrides)
    return source


# Paramètres simples

def test_get_keywords_normalizes_and_removes_duplicates() -> None:
    source = {
        "keywords": [
            " intelligence artificielle ",
            "climat",
            "intelligence artificielle",
            ""
        ]
    }

    assert module.get_keywords(source) == [
        "intelligence artificielle",
        "climat"
    ]


def test_get_keywords_limits_length() -> None:
    keyword = "a" * 600

    result = module.get_keywords({
        "keywords": [
            keyword
        ]
    })

    assert len(result) == 1
    assert len(result[0]) == module.CURRENTS_MAX_KEYWORD_LENGTH


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


def test_get_countries_maps_supported_values() -> None:
    assert module.get_countries({
        "countries": [
            "France",
            "US",
            "UK",
            "france"
        ]
    }) == [
        "fr",
        "us",
        "gb"
    ]


def test_get_countries_ignores_unsupported_values() -> None:
    assert module.get_countries({
        "countries": [
            "France",
            "Atlantis"
        ]
    }) == [
        "fr"
    ]


def test_get_categories_normalizes_values() -> None:
    assert module.get_categories({
        "categories": [
            "TECHNOLOGY",
            "Politics",
            "technology"
        ]
    }) == [
        "technology",
        "politics"
    ]


# Pagination

def test_get_page_size_respects_remaining_articles() -> None:
    source = {
        "page_size": 100
    }

    assert module.get_page_size(
        source,
        remaining_articles=12
    ) == 12


def test_get_page_size_respects_currents_limit() -> None:
    source = {
        "page_size": 1000
    }

    assert module.get_page_size(
        source,
        remaining_articles=500
    ) == module.CURRENTS_MAX_PAGE_SIZE


def test_get_max_pages_respects_limit() -> None:
    assert module.get_max_pages({
        "max_pages": 1000
    }) == module.CURRENTS_MAX_PAGE_NUMBER


def test_get_max_requests_returns_at_least_one() -> None:
    assert module.get_max_requests({
        "max_requests": 0
    }) == 1


# Dates

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-07-20", "2026-07-20"),
        ("2026-07-20T12:30:00Z", "2026-07-20"),
        ("", None),
        (None, None),
        ("date-invalide", None)
    ]
)
def test_parse_currents_date(
    value: Any,
    expected: str | None
) -> None:
    result = module.parse_currents_date(
        value,
        "start_date"
    )

    assert (
        result.isoformat()
        if result is not None
        else None
    ) == expected


def test_get_currents_date_range_swaps_reversed_dates() -> None:
    source = build_source(
        start_date="2026-07-20",
        end_date="2026-07-10",
        max_article_age_days=30
    )

    assert module.get_currents_date_range(source) == (
        "2026-07-14",
        "2026-07-20"
    )


def test_get_currents_date_range_limits_period() -> None:
    source = build_source(
        start_date="2026-01-01",
        end_date="2026-01-30",
        max_article_age_days=10
    )

    assert module.get_currents_date_range(source) == (
        "2026-01-24",
        "2026-01-30"
    )


# Paramètres de requête

def test_build_currents_request_params_for_search(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_currents_date_range",
        lambda source: (
            "2026-07-01",
            "2026-07-20"
        )
    )

    result = module.build_currents_request_params(
        source=build_source(
            domain="example.com",
            author="Auteur",
            article_type=2
        ),
        keyword="intelligence artificielle",
        language="FR",
        country="US",
        category="TECHNOLOGY",
        page_number=1,
        page_size=30
    )

    assert result == {
        "page_number": 1,
        "page_size": 30,
        "language": "fr",
        "country": "us",
        "category": "technology",
        "domain": "example.com",
        "author": "Auteur",
        "keywords": "intelligence artificielle",
        "start_date": "2026-07-01",
        "end_date": "2026-07-20",
        "type": 2
    }


def test_build_currents_request_params_excludes_search_values_for_latest() -> None:
    result = module.build_currents_request_params(
        source=build_source(
            endpoint="https://api.currentsapi.services/v1/latest-news"
        ),
        keyword="intelligence artificielle",
        language="FR",
        country="US",
        category="TECHNOLOGY",
        page_number=1,
        page_size=30
    )

    assert "keywords" not in result
    assert "start_date" not in result
    assert "end_date" not in result


def test_build_currents_request_params_prefers_domain() -> None:
    result = module.build_currents_request_params(
        source=build_source(
            domain="included.example",
            domain_not="excluded.example"
        ),
        keyword="",
        language="",
        country="",
        category="",
        page_number=1,
        page_size=30
    )

    assert result["domain"] == "included.example"
    assert "domain_not" not in result


# Couples et requêtes

def test_get_currents_query_pairs_uses_structured_queries() -> None:
    source = {
        "queries": [
            {
                "keyword": "ia",
                "category": "technology"
            },
            {
                "keyword": "climat",
                "category": "environment"
            }
        ]
    }

    assert module.get_currents_query_pairs(source) == [
        (
            "ia",
            "technology"
        ),
        (
            "climat",
            "environment"
        )
    ]


def test_get_currents_query_pairs_matches_lists_by_position() -> None:
    source = {
        "keywords": [
            "ia",
            "football"
        ],
        "categories": [
            "technology",
            "sports"
        ]
    }

    assert module.get_currents_query_pairs(source) == [
        (
            "ia",
            "technology"
        ),
        (
            "football",
            "sports"
        )
    ]


def test_get_currents_query_pairs_uses_general_fallback() -> None:
    source = {
        "keywords": [
            "ia",
            "climat"
        ],
        "categories": [
            "general"
        ]
    }

    assert module.get_currents_query_pairs(source) == [
        (
            "ia",
            "general"
        ),
        (
            "climat",
            "general"
        )
    ]


def test_build_currents_requests_combines_filters() -> None:
    source = {
        "queries": [
            {
                "keyword": "ia",
                "category": "technology"
            }
        ],
        "languages": [
            "fr",
            "en"
        ],
        "countries": [
            "France"
        ],
        "max_requests": 10
    }

    assert module.build_currents_requests(source) == [
        {
            "keyword": "ia",
            "language": "fr",
            "country": "fr",
            "category": "technology"
        },
        {
            "keyword": "ia",
            "language": "en",
            "country": "fr",
            "category": "technology"
        }
    ]


def test_build_currents_requests_respects_maximum() -> None:
    source = {
        "keywords": [
            "ia",
            "climat"
        ],
        "languages": [
            "fr",
            "en"
        ],
        "countries": [
            "France"
        ],
        "max_requests": 2
    }

    assert len(
        module.build_currents_requests(source)
    ) == 2


# Réseau

def test_fetch_currents_page_delegates_to_fetch_json_object(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_fetch_json_object(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {
            "status": "ok"
        }

    monkeypatch.setattr(
        module,
        "fetch_json_object",
        fake_fetch_json_object
    )

    result = module.fetch_currents_page(
        endpoint="https://example.com/api",
        params={
            "page_number": 1
        },
        api_key="secret"
    )

    assert result == {
        "status": "ok"
    }
    assert captured == {
        "url": "https://example.com/api",
        "params": {
            "page_number": 1,
            "apiKey": "secret"
        },
        "headers": {
            "Accept": "application/json"
        }
    }


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "msg": "Erreur principale"
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
                "details": {
                    "message": "Erreur détaillée"
                }
            },
            "Erreur détaillée"
        ),
        (
            {},
            "Erreur non communiquée"
        )
    ]
)
def test_get_currents_error_message(
    data: Mapping[str, Any],
    expected: str
) -> None:
    assert module.get_currents_error_message(data) == expected


def test_request_currents_page_returns_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "fetch_currents_page",
        lambda **kwargs: {
            "status": "ok",
            "page": 2,
            "news": [
                {
                    "id": "article-1"
                },
                "invalid",
                {
                    "id": "article-2"
                }
            ]
        }
    )

    articles, returned_page = module.request_currents_page(
        source=build_source(),
        keyword="ia",
        language="fr",
        country="fr",
        category="technology",
        page_number=2,
        page_size=30,
        api_key="secret"
    )

    assert articles == [
        {
            "id": "article-1"
        },
        {
            "id": "article-2"
        }
    ]
    assert returned_page == 2


def test_request_currents_page_rejects_invalid_endpoint() -> None:
    with pytest.raises(
        ValueError,
        match="Endpoint Currents absent ou invalide"
    ):
        module.request_currents_page(
            source=build_source(
                endpoint="invalid"
            ),
            keyword="",
            language="",
            country="",
            category="",
            page_number=1,
            page_size=30,
            api_key="secret"
        )


def test_request_currents_page_raises_request_error(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "fetch_currents_page",
        lambda **kwargs: {
            "status": "error",
            "message": "Paramètre refusé"
        }
    )
    monkeypatch.setattr(
        module,
        "raise_if_fatal_api_error",
        lambda error, source_name: "Paramètre refusé"
    )

    with pytest.raises(ApiRequestError):
        module.request_currents_page(
            source=build_source(),
            keyword="ia",
            language="fr",
            country="fr",
            category="technology",
            page_number=1,
            page_size=30,
            api_key="secret"
        )


# Pagination des articles

def test_request_currents_articles_returns_empty_for_zero_maximum() -> None:
    assert module.request_currents_articles(
        source=build_source(),
        keyword="",
        language="",
        country="",
        category="",
        max_articles=0,
        api_key="secret"
    ) == []


def test_request_currents_articles_stops_on_partial_page(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def fake_request_page(**kwargs: Any) -> tuple[list[dict[str, Any]], int]:
        nonlocal calls
        calls += 1

        return (
            [
                {
                    "id": "article-1"
                }
            ],
            1
        )

    monkeypatch.setattr(
        module,
        "request_currents_page",
        fake_request_page
    )
    monkeypatch.setattr(
        module,
        "get_page_size",
        lambda source, remaining_articles: 30
    )
    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 5
    )

    result = module.request_currents_articles(
        source=build_source(),
        keyword="ia",
        language="fr",
        country="fr",
        category="technology",
        max_articles=10,
        api_key="secret"
    )

    assert result == [
        {
            "id": "article-1"
        }
    ]
    assert calls == 1


def test_request_currents_articles_respects_maximum(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "request_currents_page",
        lambda **kwargs: (
            [
                {
                    "id": "article-1"
                },
                {
                    "id": "article-2"
                },
                {
                    "id": "article-3"
                }
            ],
            1
        )
    )
    monkeypatch.setattr(
        module,
        "get_page_size",
        lambda source, remaining_articles: 3
    )
    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 1
    )

    result = module.request_currents_articles(
        source=build_source(),
        keyword="",
        language="",
        country="",
        category="",
        max_articles=2,
        api_key="secret"
    )

    assert len(result) == 2


# Transformation

def test_get_currents_category() -> None:
    assert module.get_currents_category({
        "category": [
            "technology",
            "science",
            "technology"
        ]
    }) == "technology,science"


def test_get_currents_article_text_prefers_description() -> None:
    assert module.get_currents_article_text({
        "description": "Description disponible",
        "content": "Contenu complet"
    }) == "Description disponible"


def test_get_currents_article_text_uses_content_fallback() -> None:
    assert module.get_currents_article_text({
        "description": "",
        "content": "Contenu complet"
    }) == "Contenu complet"


def test_build_currents_article_rejects_invalid_item() -> None:
    assert module.build_currents_article(
        item="invalid",
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_currents_article_rejects_missing_identifier() -> None:
    assert module.build_currents_article(
        item={
            "title": "Titre"
        },
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_currents_article_builds_standard_article(
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

    result = module.build_currents_article(
        item={
            "id": "article-1",
            "title": "Titre de l'article",
            "description": "Description de l'article",
            "url": "https://example.com/article",
            "image": "https://example.com/image.jpg",
            "published": "2026-07-20T10:00:00Z",
            "author": "Auteur",
            "language": "FR",
            "category": [
                "technology"
            ],
            "_requested_language": "en",
            "_requested_category": "general"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert result == captured
    assert captured["identifier"] == "article-1"
    assert captured["source"] == "Currents News API"
    assert captured["language"] == "fr"
    assert captured["category"] == "technology"
    assert captured["url"] == "https://example.com/article"
    assert captured["image_url"] == "https://example.com/image.jpg"


def test_build_currents_article_uses_requested_fallbacks(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_currents_article(
        item={
            "id": "article-1",
            "title": "Titre",
            "url": "https://example.com/article",
            "_requested_language": "fr",
            "_requested_category": "science"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert captured["language"] == "fr"
    assert captured["category"] == "science"


def test_build_currents_article_removes_invalid_urls(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_currents_article(
        item={
            "id": "article-1",
            "title": "Titre",
            "url": "invalid-url",
            "image": "invalid-image"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert captured["url"] == ""
    assert captured["image_url"] == ""


# Validation

@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (
            None,
            (
                False,
                "resultat_currents_invalide"
            )
        ),
        (
            {},
            (
                False,
                "identifiant_currents_absent"
            )
        ),
        (
            {
                "id": "article-1",
                "url": "invalid"
            },
            (
                False,
                "url_currents_invalide"
            )
        ),
        (
            {
                "id": "article-1",
                "url": "https://example.com/article"
            },
            (
                True,
                ""
            )
        )
    ]
)
def test_validate_currents_item(
    item: Any,
    expected: tuple[bool, str]
) -> None:
    assert module.validate_currents_item(
        item=item,
        filters={},
        source={}
    ) == expected


# API publique

def test_load_currents_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        type(module.CURRENTS_EXTRACTOR),
        "reload_source",
        lambda self: {
            "source_id": "currents"
        }
    )

    assert module.load_currents_source() == {
        "source_id": "currents"
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
    assert captured["adapter"] is module.CURRENTS_ADAPTER


def test_extract_all_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()

    monkeypatch.setattr(
        type(module.CURRENTS_EXTRACTOR),
        "run",
        lambda self: expected
    )

    assert module.extract_all_articles() is expected