"""Tests légers de l'extracteur NewsAPI."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

import pytest

import src.extractors.apis.source.newsapi_extractor as module
from src.extractors.apis.api_extractor import ApiRequestError


# Configuration

def build_source(**overrides: Any) -> dict[str, Any]:
    """Construit une configuration NewsAPI minimale."""

    source = {
        "source_id": "newsapi",
        "name": "NewsAPI",
        "endpoint": "https://newsapi.org/v2/everything",
        "role": "acquisition",
        "category": "general",
        "max_article_age_days": 30,
        "page_size": 100,
        "max_pages": 5
    }
    source.update(overrides)
    return source


# Requêtes configurées

def test_get_newsapi_queries_returns_configured_queries(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = [
        {
            "queries": [
                "climat"
            ],
            "language": "fr"
        }
    ]

    monkeypatch.setattr(
        module,
        "get_queries_configuration",
        lambda source: expected
    )

    assert module.get_newsapi_queries({}) == expected


def test_get_newsapi_queries_uses_source_fallback(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    source = {
        "query": "climat",
        "language": "fr"
    }

    monkeypatch.setattr(
        module,
        "get_queries_configuration",
        lambda current_source: []
    )

    assert module.get_newsapi_queries(source) == [
        source
    ]


def test_merge_newsapi_query_excludes_queries() -> None:
    source = {
        "language": "fr",
        "category": "general",
        "queries": [
            {
                "language": "en"
            }
        ]
    }
    query = {
        "language": "en",
        "category": "technology"
    }

    assert module.merge_newsapi_query(
        source,
        query
    ) == {
        "language": "en",
        "category": "technology"
    }


# Paramètres métier

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            [
                "bbc",
                "reuters"
            ],
            "bbc,reuters"
        ),
        (
            "bbc",
            "bbc"
        ),
        (
            [],
            ""
        ),
        (
            None,
            ""
        )
    ]
)
def test_format_list_value(
    value: Any,
    expected: str
) -> None:
    assert module.format_list_value(value) == expected


def test_get_queries_normalizes_and_removes_duplicates(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_keywords",
        lambda source: [
            " intelligence artificielle ",
            "climat",
            "intelligence artificielle",
            ""
        ]
    )

    assert module.get_queries({}) == [
        "intelligence artificielle",
        "climat"
    ]


def test_get_queries_limits_length(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_keywords",
        lambda source: [
            "a" * 600
        ]
    )

    result = module.get_queries({})

    assert len(result) == 1
    assert len(result[0]) == module.NEWSAPI_MAX_QUERY_LENGTH


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("FR", "fr"),
        ("en", "en"),
        ("zh", "zh"),
        ("xx", ""),
        ("", ""),
        (None, "")
    ]
)
def test_normalize_newsapi_language(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_newsapi_language(value) == expected


def test_get_languages_keeps_supported_languages(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_configuration_values",
        lambda *args, **kwargs: [
            "fr",
            "en",
            "xx",
            "fr"
        ]
    )

    assert module.get_languages({}) == [
        "fr",
        "en"
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("relevancy", "relevancy"),
        ("popularity", "popularity"),
        ("publishedAt", "publishedAt"),
        ("PUBLISHEDAT", "publishedAt"),
        ("unknown", "publishedAt"),
        ("", "publishedAt"),
        (None, "publishedAt")
    ]
)
def test_normalize_newsapi_sort(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_newsapi_sort(value) == expected


# Dates

def test_parse_newsapi_date_returns_datetime(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = datetime(
        2026,
        7,
        20,
        10,
        30,
        tzinfo=timezone.utc
    )

    monkeypatch.setattr(
        module,
        "parse_datetime",
        lambda value: expected
    )

    assert module.parse_newsapi_date(
        "2026-07-20T10:30:00Z",
        "date_from"
    ) == expected


def test_parse_newsapi_date_returns_none_for_invalid_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "parse_datetime",
        lambda value: None
    )

    assert module.parse_newsapi_date(
        "date-invalide",
        "date_from"
    ) is None


def test_format_newsapi_date() -> None:
    value = datetime(
        2026,
        7,
        20,
        10,
        30,
        45,
        tzinfo=timezone.utc
    )

    assert module.format_newsapi_date(value) == (
        "2026-07-20T10:30:45Z"
    )


def test_get_newsapi_date_range_swaps_reversed_dates(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 30
    )

    source = build_source(
        date_from="2026-07-20T00:00:00Z",
        date_to="2026-07-10T00:00:00Z"
    )

    assert module.get_newsapi_date_range(source) == (
        "2026-07-10T00:00:00Z",
        "2026-07-20T00:00:00Z"
    )


def test_get_newsapi_date_range_limits_period(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 10
    )

    source = build_source(
        date_from="2026-01-01T00:00:00Z",
        date_to="2026-01-30T00:00:00Z"
    )

    assert module.get_newsapi_date_range(source) == (
        "2026-01-20T00:00:00Z",
        "2026-01-30T00:00:00Z"
    )


def test_get_newsapi_date_range_builds_missing_start_date(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 10
    )

    source = build_source(
        date_to="2026-01-30T00:00:00Z"
    )

    assert module.get_newsapi_date_range(source) == (
        "2026-01-20T00:00:00Z",
        "2026-01-30T00:00:00Z"
    )


def test_get_newsapi_date_range_builds_missing_end_date(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 10
    )

    source = build_source(
        date_from="2026-01-01T00:00:00Z"
    )

    assert module.get_newsapi_date_range(source) == (
        "2026-01-01T00:00:00Z",
        "2026-01-11T00:00:00Z"
    )


# Pagination

def test_get_page_size_respects_remaining_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_pagination_value",
        lambda *args, **kwargs: 100
    )

    assert module.get_page_size(
        source={},
        remaining_articles=12
    ) == 12


def test_get_page_size_respects_api_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_pagination_value",
        lambda *args, **kwargs: 500
    )

    assert module.get_page_size(
        source={},
        remaining_articles=500
    ) == module.NEWSAPI_MAX_PAGE_SIZE


def test_get_max_pages_respects_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_pagination_value",
        lambda *args, **kwargs: 1000
    )

    assert module.get_max_pages({}) == module.NEWSAPI_MAX_PAGE_NUMBER


# Paramètres HTTP

def test_build_newsapi_request_params(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_newsapi_date_range",
        lambda source: (
            "2026-07-01T00:00:00Z",
            "2026-07-20T00:00:00Z"
        )
    )

    result = module.build_newsapi_request_params(
        source=build_source(
            sort_by="popularity",
            sources=[
                "bbc",
                "reuters"
            ],
            domains=[
                "example.com"
            ],
            excluded_domains=[
                "spam.example"
            ],
            search_in=[
                "title",
                "description"
            ]
        ),
        query="intelligence artificielle",
        language="FR",
        page_number=2,
        page_size=50
    )

    assert result == {
        "q": "intelligence artificielle",
        "sortBy": "popularity",
        "pageSize": 50,
        "page": 2,
        "language": "fr",
        "from": "2026-07-01T00:00:00Z",
        "to": "2026-07-20T00:00:00Z",
        "sources": "bbc,reuters",
        "domains": "example.com",
        "excludeDomains": "spam.example",
        "searchIn": "title,description"
    }


def test_build_newsapi_request_params_excludes_empty_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_newsapi_date_range",
        lambda source: (
            "",
            ""
        )
    )

    result = module.build_newsapi_request_params(
        source=build_source(),
        query="",
        language="xx",
        page_number=0,
        page_size=10
    )

    assert result == {
        "q": "",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "page": 1
    }


def test_build_newsapi_request_params_respects_limits(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_newsapi_date_range",
        lambda source: (
            "",
            ""
        )
    )

    result = module.build_newsapi_request_params(
        source=build_source(),
        query="a" * 600,
        language="fr",
        page_number=1000,
        page_size=1000
    )

    assert result["page"] == module.NEWSAPI_MAX_PAGE_NUMBER
    assert result["pageSize"] == module.NEWSAPI_MAX_PAGE_SIZE
    assert len(result["q"]) == module.NEWSAPI_MAX_QUERY_LENGTH


# Réseau

def test_fetch_newsapi_page_delegates_to_fetch_json_object(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_fetch_json_object(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {
            "status": "ok",
            "articles": []
        }

    monkeypatch.setattr(
        module,
        "fetch_json_object",
        fake_fetch_json_object
    )

    result = module.fetch_newsapi_page(
        endpoint="https://example.com/api",
        params={
            "q": "climat"
        },
        api_key="secret"
    )

    assert result == {
        "status": "ok",
        "articles": []
    }
    assert captured == {
        "url": "https://example.com/api",
        "params": {
            "q": "climat"
        },
        "headers": {
            "Accept": "application/json",
            "X-Api-Key": "secret"
        }
    }


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "code": "apiKeyInvalid",
                "message": "Clé invalide"
            },
            (
                "apiKeyInvalid",
                "Clé invalide"
            )
        ),
        (
            {},
            (
                "inconnu",
                "non communiqué"
            )
        )
    ]
)
def test_get_newsapi_error_details(
    data: Mapping[str, Any],
    expected: tuple[str, str]
) -> None:
    assert module.get_newsapi_error_details(data) == expected


# Récupération d'une page

def test_request_newsapi_page_rejects_invalid_endpoint() -> None:
    with pytest.raises(
        ValueError,
        match="Endpoint NewsAPI absent ou invalide"
    ):
        module.request_newsapi_page(
            source=build_source(
                endpoint="invalid"
            ),
            query="climat",
            language="fr",
            page_number=1,
            page_size=100,
            api_key="secret"
        )


def test_request_newsapi_page_rejects_empty_query() -> None:
    with pytest.raises(
        ValueError,
        match="NewsAPI exige une requête non vide"
    ):
        module.request_newsapi_page(
            source=build_source(),
            query="",
            language="fr",
            page_number=1,
            page_size=100,
            api_key="secret"
        )


def test_request_newsapi_page_returns_articles_and_total(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_newsapi_request_params",
        lambda **kwargs: {
            "q": "climat",
            "page": 1,
            "pageSize": 100
        }
    )
    monkeypatch.setattr(
        module,
        "fetch_newsapi_page",
        lambda **kwargs: {
            "status": "ok",
            "totalResults": 50,
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
    )

    articles, total = module.request_newsapi_page(
        source=build_source(),
        query="climat",
        language="fr",
        page_number=1,
        page_size=100,
        api_key="secret"
    )

    assert articles == [
        {
            "url": "https://example.com/article-1"
        },
        {
            "url": "https://example.com/article-2"
        }
    ]
    assert total == 50


def test_request_newsapi_page_raises_request_error(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_newsapi_request_params",
        lambda **kwargs: {
            "q": "climat",
            "page": 1,
            "pageSize": 100
        }
    )
    monkeypatch.setattr(
        module,
        "fetch_newsapi_page",
        lambda **kwargs: {
            "status": "error",
            "code": "apiKeyInvalid",
            "message": "Clé invalide"
        }
    )
    monkeypatch.setattr(
        module,
        "raise_if_fatal_api_error",
        lambda error, source_name: None
    )

    with pytest.raises(ApiRequestError):
        module.request_newsapi_page(
            source=build_source(),
            query="climat",
            language="fr",
            page_number=1,
            page_size=100,
            api_key="secret"
        )


# Pagination multi-pages

def test_request_newsapi_articles_returns_empty_for_zero() -> None:
    assert module.request_newsapi_articles(
        source=build_source(),
        query="climat",
        language="fr",
        max_articles=0,
        api_key="secret"
    ) == []


def test_request_newsapi_articles_collects_multiple_pages(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    responses = iter([
        (
            [
                {
                    "url": "https://example.com/article-1"
                },
                {
                    "url": "https://example.com/article-2"
                }
            ],
            3
        ),
        (
            [
                {
                    "url": "https://example.com/article-3"
                }
            ],
            3
        )
    ])

    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 5
    )
    monkeypatch.setattr(
        module,
        "get_page_size",
        lambda source, remaining_articles: 2
    )
    monkeypatch.setattr(
        module,
        "request_newsapi_page",
        lambda **kwargs: next(responses)
    )

    result = module.request_newsapi_articles(
        source=build_source(),
        query="climat",
        language="fr",
        max_articles=5,
        api_key="secret"
    )

    assert result == [
        {
            "url": "https://example.com/article-1"
        },
        {
            "url": "https://example.com/article-2"
        },
        {
            "url": "https://example.com/article-3"
        }
    ]


def test_request_newsapi_articles_respects_maximum(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 1
    )
    monkeypatch.setattr(
        module,
        "get_page_size",
        lambda source, remaining_articles: 10
    )
    monkeypatch.setattr(
        module,
        "request_newsapi_page",
        lambda **kwargs: (
            [
                {
                    "url": f"https://example.com/article-{index}"
                }
                for index in range(10)
            ],
            10
        )
    )

    result = module.request_newsapi_articles(
        source=build_source(),
        query="climat",
        language="fr",
        max_articles=3,
        api_key="secret"
    )

    assert len(result) == 3


def test_request_newsapi_articles_stops_on_partial_page(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 5
    )
    monkeypatch.setattr(
        module,
        "get_page_size",
        lambda source, remaining_articles: 100
    )

    def fake_request_page(**kwargs: Any) -> tuple[
        list[dict[str, Any]],
        int
    ]:
        nonlocal calls
        calls += 1

        return (
            [
                {
                    "url": "https://example.com/article-1"
                }
            ],
            100
        )

    monkeypatch.setattr(
        module,
        "request_newsapi_page",
        fake_request_page
    )

    result = module.request_newsapi_articles(
        source=build_source(),
        query="climat",
        language="fr",
        max_articles=100,
        api_key="secret"
    )

    assert result == [
        {
            "url": "https://example.com/article-1"
        }
    ]
    assert calls == 1


# Parcours

def test_iter_newsapi_items_returns_nothing_for_zero() -> None:
    assert list(
        module.iter_newsapi_items(
            build_source(),
            0
        )
    ) == []


def test_iter_newsapi_items_requires_query(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_newsapi_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "get_newsapi_queries",
        lambda source: [
            {}
        ]
    )

    with pytest.raises(
        ValueError,
        match="Aucune requête configurée"
    ):
        list(
            module.iter_newsapi_items(
                build_source(),
                10
            )
        )


def test_iter_newsapi_items_enriches_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_newsapi_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "get_newsapi_queries",
        lambda source: [
            {
                "query": "climat",
                "language": "fr"
            }
        ]
    )
    monkeypatch.setattr(
        module,
        "request_newsapi_articles",
        lambda **kwargs: [
            {
                "url": "https://example.com/article-1"
            }
        ]
    )

    result = list(
        module.iter_newsapi_items(
            build_source(),
            1
        )
    )

    assert result == [
        (
            "query=climat|language=fr",
            0,
            {
                "url": "https://example.com/article-1",
                "_requested_query": "climat",
                "_requested_language": "fr"
            }
        )
    ]


def test_iter_newsapi_items_respects_maximum(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_newsapi_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "request_newsapi_articles",
        lambda **kwargs: [
            {
                "url": f"https://example.com/article-{index}"
            }
            for index in range(10)
        ]
    )

    result = list(
        module.iter_newsapi_items(
            build_source(
                query="climat",
                language="fr"
            ),
            3
        )
    )

    assert len(result) == 3


# Champs

def test_get_newsapi_publisher_returns_source_name() -> None:
    assert module.get_newsapi_publisher({
        "source": {
            "name": "Reuters"
        }
    }) == "Reuters"


def test_get_newsapi_publisher_rejects_invalid_source() -> None:
    assert module.get_newsapi_publisher({
        "source": "Reuters"
    }) == ""


def test_get_newsapi_article_text_prefers_content() -> None:
    assert module.get_newsapi_article_text({
        "content": "Contenu complet",
        "description": "Description"
    }) == "Contenu complet"


def test_get_newsapi_article_text_uses_description_fallback() -> None:
    assert module.get_newsapi_article_text({
        "content": "",
        "description": "Description"
    }) == "Description"


def test_build_newsapi_identifier_prefers_url() -> None:
    assert module.build_newsapi_identifier(
        {
            "url": "https://example.com/article"
        },
        "request-1"
    ) == "https://example.com/article"


def test_build_newsapi_identifier_uses_fallback() -> None:
    result = module.build_newsapi_identifier(
        {
            "url": "invalid",
            "publishedAt": "2026-07-28T10:00:00Z",
            "title": "Titre de l'article"
        },
        "request-1"
    )

    assert result == (
        "newsapi:request-1:"
        "2026-07-28T10:00:00Z:"
        "Titre de l'article"
    )


# Construction d'article

def test_build_newsapi_article_rejects_invalid_item() -> None:
    assert module.build_newsapi_article(
        item="invalid",
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_newsapi_article_builds_standard_article(
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

    result = module.build_newsapi_article(
        item={
            "title": "Titre de l'article",
            "content": "Contenu de l'article",
            "url": "https://example.com/article",
            "urlToImage": "https://example.com/image.jpg",
            "publishedAt": "2026-07-28T10:00:00Z",
            "author": "Jane Doe",
            "source": {
                "name": "Reuters"
            },
            "_requested_query": "climat",
            "_requested_language": "FR"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert result == captured
    assert captured["identifier"] == "https://example.com/article"
    assert captured["source"] == "NewsAPI"
    assert captured["title"] == "Titre de l'article"
    assert captured["text"] == "Contenu de l'article"
    assert captured["image_url"] == "https://example.com/image.jpg"
    assert captured["url"] == "https://example.com/article"
    assert captured["author"] == "Jane Doe"
    assert captured["language"] == "fr"
    assert captured["category"] == "climat"
    assert captured["metadata"] == {
        "publisher": "Reuters"
    }


def test_build_newsapi_article_uses_source_category_fallback(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_newsapi_article(
        item={
            "title": "Titre",
            "url": "https://example.com/article",
            "_requested_query": "",
            "_requested_language": "fr"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source(
            category="technology"
        )
    )

    assert captured["category"] == "technology"


def test_build_newsapi_article_removes_invalid_urls(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_newsapi_article(
        item={
            "title": "Titre",
            "url": "invalid",
            "urlToImage": "invalid",
            "_requested_language": "fr"
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
                "resultat_newsapi_invalide"
            )
        ),
        (
            {},
            (
                False,
                "url_newsapi_invalide"
            )
        ),
        (
            {
                "url": "invalid",
                "title": "Titre"
            },
            (
                False,
                "url_newsapi_invalide"
            )
        ),
        (
            {
                "url": "https://example.com/article",
                "title": ""
            },
            (
                False,
                "titre_newsapi_absent"
            )
        ),
        (
            {
                "url": "https://example.com/article",
                "title": "Titre"
            },
            (
                True,
                ""
            )
        )
    ]
)
def test_validate_newsapi_item(
    item: Any,
    expected: tuple[bool, str]
) -> None:
    assert module.validate_newsapi_item(
        item=item,
        filters={},
        source={}
    ) == expected


# API publique

def test_load_newsapi_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        type(module.NEWSAPI_EXTRACTOR),
        "reload_source",
        lambda self: {
            "source_id": "newsapi"
        }
    )

    assert module.load_newsapi_source() == {
        "source_id": "newsapi"
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
    assert captured["adapter"] is module.NEWSAPI_ADAPTER


def test_extract_all_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()

    monkeypatch.setattr(
        type(module.NEWSAPI_EXTRACTOR),
        "run",
        lambda self: expected
    )

    assert module.extract_all_articles() is expected