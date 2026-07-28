"""Tests légers de l'extracteur Mediastack."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

import src.extractors.apis.source.mediastack_extractor as module
from src.extractors.apis.api_extractor import ApiRequestError


# Configuration

def build_source(**overrides: Any) -> dict[str, Any]:
    """Construit une configuration Mediastack minimale."""

    source = {
        "source_id": "mediastack",
        "name": "Mediastack",
        "endpoint": "https://api.mediastack.com/v1/news",
        "role": "acquisition",
        "max_article_age_days": 30,
        "limit": 100,
        "max_pages": 5
    }
    source.update(overrides)
    return source


# Requêtes configurées

def test_get_mediastack_queries_returns_configured_queries(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = [
        {
            "keywords": [
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

    assert module.get_mediastack_queries({}) == expected


def test_get_mediastack_queries_uses_source_fallback(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    source = {
        "keywords": [
            "climat"
        ],
        "language": "fr"
    }

    monkeypatch.setattr(
        module,
        "get_queries_configuration",
        lambda current_source: []
    )

    assert module.get_mediastack_queries(source) == [
        source
    ]


def test_merge_mediastack_query_excludes_queries() -> None:
    source = {
        "language": "fr",
        "country": "fr",
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

    assert module.merge_mediastack_query(
        source,
        query
    ) == {
        "language": "en",
        "country": "fr",
        "category": "technology"
    }


# Filtres

def test_get_keywords_normalizes_and_removes_duplicates(
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

    assert module.get_keywords({}) == [
        "intelligence artificielle",
        "climat"
    ]


def test_get_keywords_limits_length(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_keywords",
        lambda source: [
            "a" * 600
        ]
    )

    result = module.get_keywords({})

    assert len(result) == 1
    assert len(result[0]) == module.MEDIASTACK_MAX_KEYWORD_LENGTH


def test_get_languages_delegates_to_configuration_helper(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_configuration_values",
        lambda *args, **kwargs: [
            "fr",
            "en"
        ]
    )

    assert module.get_languages({}) == [
        "fr",
        "en"
    ]


def test_get_countries_keeps_valid_codes(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_configuration_values",
        lambda *args, **kwargs: [
            "fr",
            "us",
            "fra",
            "1a",
            "fr"
        ]
    )

    assert module.get_countries({}) == [
        "fr",
        "us"
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("TECHNOLOGY", "technology"),
        ("science", "science"),
        ("general", "general"),
        ("unknown", ""),
        ("", ""),
        (None, "")
    ]
)
def test_normalize_mediastack_category(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_mediastack_category(value) == expected


def test_get_categories_keeps_valid_categories(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_configuration_values",
        lambda *args, **kwargs: [
            "technology",
            "unknown",
            "science",
            "technology"
        ]
    )

    assert module.get_categories({}) == [
        "technology",
        "science"
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("published_desc", "published_desc"),
        ("PUBLISHED_ASC", "published_asc"),
        ("popularity", "popularity"),
        ("unknown", "published_desc"),
        ("", "published_desc"),
        (None, "published_desc")
    ]
)
def test_normalize_mediastack_sort(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_mediastack_sort(value) == expected


def test_build_sources_filter_combines_included_and_excluded() -> None:
    source = {
        "sources": [
            "BBC",
            "Reuters"
        ],
        "excluded_sources": [
            "Example",
            "Reuters"
        ]
    }

    assert module.build_sources_filter(source) == (
        "bbc,reuters,-example,-reuters"
    )


# Dates

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            "2026-07-20",
            "2026-07-20"
        ),
        (
            "",
            None
        ),
        (
            None,
            None
        ),
        (
            "date-invalide",
            None
        )
    ]
)
def test_parse_mediastack_date(
    value: Any,
    expected: str | None
) -> None:
    result = module.parse_mediastack_date(
        value,
        "date_from"
    )

    assert (
        result.isoformat()
        if result is not None
        else None
    ) == expected


def test_build_mediastack_date_filter_uses_configured_period(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 30
    )

    source = build_source(
        date_from="2026-07-01",
        date_to="2026-07-20"
    )

    assert module.build_mediastack_date_filter(source) == (
        "2026-07-01,2026-07-20"
    )


def test_build_mediastack_date_filter_swaps_reversed_dates(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 30
    )

    source = build_source(
        date_from="2026-07-20",
        date_to="2026-07-10"
    )

    assert module.build_mediastack_date_filter(source) == (
        "2026-07-10,2026-07-20"
    )


def test_build_mediastack_date_filter_limits_period(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 10
    )

    source = build_source(
        date_from="2026-01-01",
        date_to="2026-01-30"
    )

    assert module.build_mediastack_date_filter(source) == (
        "2026-01-20,2026-01-30"
    )


def test_build_mediastack_date_filter_accepts_compact_date(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 30
    )

    assert module.build_mediastack_date_filter(
        build_source(
            date="2026-07-01,2026-07-20"
        )
    ) == "2026-07-01,2026-07-20"


def test_build_mediastack_date_filter_accepts_single_date(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 30
    )

    assert module.build_mediastack_date_filter(
        build_source(
            date="2026-07-20"
        )
    ) == "2026-07-20,2026-07-20"


# Pagination

def test_get_page_limit_respects_remaining_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_pagination_value",
        lambda *args, **kwargs: 100
    )

    assert module.get_page_limit(
        source={},
        remaining_articles=12
    ) == 12


def test_get_page_limit_respects_api_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_pagination_value",
        lambda *args, **kwargs: 500
    )

    assert module.get_page_limit(
        source={},
        remaining_articles=500
    ) == module.MEDIASTACK_MAX_LIMIT


def test_get_max_pages_respects_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_pagination_value",
        lambda *args, **kwargs: 1000
    )

    assert module.get_max_pages({}) == module.MEDIASTACK_MAX_PAGES


# Paramètres HTTP

def test_build_mediastack_request_params(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_mediastack_date_filter",
        lambda source: "2026-07-01,2026-07-20"
    )

    result = module.build_mediastack_request_params(
        source=build_source(
            sort="popularity",
            sources=[
                "bbc"
            ],
            excluded_sources=[
                "example"
            ]
        ),
        keyword="intelligence artificielle",
        language="FR",
        country="US",
        category="TECHNOLOGY",
        limit=50,
        offset=100
    )

    assert result == {
        "limit": 50,
        "offset": 100,
        "sort": "popularity",
        "date": "2026-07-01,2026-07-20",
        "keywords": "intelligence artificielle",
        "languages": "fr",
        "countries": "us",
        "categories": "technology",
        "sources": "bbc,-example"
    }


def test_build_mediastack_request_params_excludes_empty_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_mediastack_date_filter",
        lambda source: "2026-07-01,2026-07-20"
    )

    result = module.build_mediastack_request_params(
        source=build_source(),
        keyword="",
        language="",
        country="",
        category="invalid",
        limit=10,
        offset=-5
    )

    assert result == {
        "limit": 10,
        "offset": 0,
        "sort": "published_desc",
        "date": "2026-07-01,2026-07-20"
    }


# Réseau

def test_fetch_mediastack_page_delegates_to_fetch_json_object(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_fetch_json_object(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {
            "data": []
        }

    monkeypatch.setattr(
        module,
        "fetch_json_object",
        fake_fetch_json_object
    )

    result = module.fetch_mediastack_page(
        endpoint="https://example.com/api",
        params={
            "limit": 10
        },
        api_key="secret"
    )

    assert result == {
        "data": []
    }
    assert captured == {
        "url": "https://example.com/api",
        "params": {
            "limit": 10,
            "access_key": "secret"
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
                "error": {
                    "code": "invalid_access_key",
                    "message": "Clé invalide"
                }
            },
            (
                "invalid_access_key",
                "Clé invalide"
            )
        ),
        (
            {
                "error": {
                    "context": {
                        "message": "Paramètre invalide"
                    }
                }
            },
            (
                "inconnu",
                "Paramètre invalide"
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
def test_get_mediastack_error_details(
    data: Mapping[str, Any],
    expected: tuple[str, str]
) -> None:
    assert module.get_mediastack_error_details(data) == expected


def test_request_mediastack_page_rejects_invalid_endpoint() -> None:
    with pytest.raises(
        ValueError,
        match="Endpoint Mediastack absent ou invalide"
    ):
        module.request_mediastack_page(
            source=build_source(
                endpoint="invalid"
            ),
            keyword="climat",
            language="fr",
            country="fr",
            category="science",
            limit=10,
            offset=0,
            api_key="secret"
        )


def test_request_mediastack_page_returns_articles_and_pagination(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_mediastack_request_params",
        lambda **kwargs: {
            "limit": 10,
            "offset": 20
        }
    )
    monkeypatch.setattr(
        module,
        "fetch_mediastack_page",
        lambda **kwargs: {
            "data": [
                {
                    "url": "https://example.com/article-1"
                },
                "invalid",
                {
                    "url": "https://example.com/article-2"
                }
            ],
            "pagination": {
                "total": 100,
                "offset": 20
            }
        }
    )

    articles, total, offset = module.request_mediastack_page(
        source=build_source(),
        keyword="climat",
        language="fr",
        country="fr",
        category="science",
        limit=10,
        offset=20,
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
    assert total == 100
    assert offset == 20


def test_request_mediastack_page_raises_request_error(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_mediastack_request_params",
        lambda **kwargs: {
            "limit": 10,
            "offset": 0
        }
    )
    monkeypatch.setattr(
        module,
        "fetch_mediastack_page",
        lambda **kwargs: {
            "error": {
                "code": "invalid_access_key",
                "message": "Clé invalide"
            }
        }
    )
    monkeypatch.setattr(
        module,
        "raise_if_fatal_api_error",
        lambda error, source_name: None
    )

    with pytest.raises(ApiRequestError):
        module.request_mediastack_page(
            source=build_source(),
            keyword="",
            language="",
            country="",
            category="",
            limit=10,
            offset=0,
            api_key="secret"
        )


# Pagination multi-pages

def test_request_mediastack_articles_returns_empty_for_zero() -> None:
    assert module.request_mediastack_articles(
        source=build_source(),
        keyword="",
        language="",
        country="",
        category="",
        max_articles=0,
        api_key="secret"
    ) == []


def test_request_mediastack_articles_collects_multiple_pages(
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
            3,
            0
        ),
        (
            [
                {
                    "url": "https://example.com/article-3"
                }
            ],
            3,
            2
        )
    ])

    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 5
    )
    monkeypatch.setattr(
        module,
        "get_page_limit",
        lambda source, remaining_articles: 2
    )
    monkeypatch.setattr(
        module,
        "request_mediastack_page",
        lambda **kwargs: next(responses)
    )

    result = module.request_mediastack_articles(
        source=build_source(),
        keyword="climat",
        language="fr",
        country="fr",
        category="science",
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


def test_request_mediastack_articles_respects_maximum(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 1
    )
    monkeypatch.setattr(
        module,
        "get_page_limit",
        lambda source, remaining_articles: 10
    )
    monkeypatch.setattr(
        module,
        "request_mediastack_page",
        lambda **kwargs: (
            [
                {
                    "url": f"https://example.com/article-{index}"
                }
                for index in range(10)
            ],
            10,
            0
        )
    )

    result = module.request_mediastack_articles(
        source=build_source(),
        keyword="",
        language="",
        country="",
        category="",
        max_articles=3,
        api_key="secret"
    )

    assert len(result) == 3


# Parcours

def test_iter_mediastack_items_returns_nothing_for_zero() -> None:
    assert list(
        module.iter_mediastack_items(
            build_source(),
            0
        )
    ) == []


def test_iter_mediastack_items_enriches_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_mediastack_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "get_mediastack_queries",
        lambda source: [
            {
                "keywords": [
                    "climat"
                ],
                "languages": [
                    "fr"
                ],
                "countries": [
                    "fr"
                ],
                "categories": [
                    "science"
                ]
            }
        ]
    )
    monkeypatch.setattr(
        module,
        "request_mediastack_articles",
        lambda **kwargs: [
            {
                "url": "https://example.com/article-1"
            }
        ]
    )

    result = list(
        module.iter_mediastack_items(
            build_source(),
            1
        )
    )

    assert result == [
        (
            (
                "keyword=climat|language=fr|"
                "country=fr|category=science"
            ),
            0,
            {
                "url": "https://example.com/article-1",
                "_requested_keyword": "climat",
                "_requested_language": "fr",
                "_requested_country": "fr",
                "_requested_category": "science"
            }
        )
    ]


# Champs et identifiant

def test_get_mediastack_article_text_prefers_description() -> None:
    assert module.get_mediastack_article_text({
        "description": "Description",
        "content": "Contenu"
    }) == "Description"


def test_get_mediastack_article_text_uses_content_fallback() -> None:
    assert module.get_mediastack_article_text({
        "description": "",
        "content": "Contenu"
    }) == "Contenu"


def test_get_mediastack_publisher() -> None:
    assert module.get_mediastack_publisher({
        "source": "Reuters"
    }) == "Reuters"


def test_build_mediastack_identifier_prefers_url() -> None:
    assert module.build_mediastack_identifier(
        {
            "url": "https://example.com/article"
        },
        "request-1"
    ) == "https://example.com/article"


def test_build_mediastack_identifier_uses_fallback() -> None:
    result = module.build_mediastack_identifier(
        {
            "url": "invalid",
            "published_at": "2026-07-28T10:00:00Z",
            "title": "Titre de l'article"
        },
        "request-1"
    )

    assert result == (
        "mediastack:request-1:"
        "2026-07-28T10:00:00Z:"
        "Titre de l'article"
    )


# Construction d'article

def test_build_mediastack_article_rejects_invalid_item() -> None:
    assert module.build_mediastack_article(
        item="invalid",
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_mediastack_article_builds_standard_article(
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

    result = module.build_mediastack_article(
        item={
            "title": "Titre de l'article",
            "description": "Description de l'article",
            "url": "https://example.com/article",
            "image": "https://example.com/image.jpg",
            "published_at": "2026-07-28T10:00:00Z",
            "author": "Jane Doe",
            "source": "Reuters",
            "language": "FR",
            "country": "FR",
            "category": "TECHNOLOGY",
            "_requested_language": "en",
            "_requested_country": "us",
            "_requested_category": "science"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert result == captured
    assert captured["identifier"] == "https://example.com/article"
    assert captured["source"] == "Mediastack"
    assert captured["title"] == "Titre de l'article"
    assert captured["text"] == "Description de l'article"
    assert captured["image_url"] == "https://example.com/image.jpg"
    assert captured["url"] == "https://example.com/article"
    assert captured["author"] == "Jane Doe"
    assert captured["language"] == "fr"
    assert captured["category"] == "technology"
    assert captured["metadata"] == {
        "publisher": "Reuters",
        "country": "fr"
    }


def test_build_mediastack_article_uses_requested_fallbacks(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_mediastack_article(
        item={
            "title": "Titre",
            "url": "https://example.com/article",
            "_requested_language": "fr",
            "_requested_country": "fr",
            "_requested_category": "science"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert captured["language"] == "fr"
    assert captured["category"] == "science"
    assert captured["metadata"]["country"] == "fr"


def test_build_mediastack_article_removes_invalid_urls(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_mediastack_article(
        item={
            "title": "Titre",
            "url": "invalid",
            "image": "invalid"
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
                "resultat_mediastack_invalide"
            )
        ),
        (
            {},
            (
                False,
                "url_mediastack_invalide"
            )
        ),
        (
            {
                "url": "invalid",
                "title": "Titre"
            },
            (
                False,
                "url_mediastack_invalide"
            )
        ),
        (
            {
                "url": "https://example.com/article",
                "title": ""
            },
            (
                False,
                "titre_mediastack_absent"
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
def test_validate_mediastack_item(
    item: Any,
    expected: tuple[bool, str]
) -> None:
    assert module.validate_mediastack_item(
        item=item,
        filters={},
        source={}
    ) == expected


# API publique

def test_load_mediastack_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        type(module.MEDIASTACK_EXTRACTOR),
        "reload_source",
        lambda self: {
            "source_id": "mediastack"
        }
    )

    assert module.load_mediastack_source() == {
        "source_id": "mediastack"
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
    assert captured["adapter"] is module.MEDIASTACK_ADAPTER


def test_extract_all_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()

    monkeypatch.setattr(
        type(module.MEDIASTACK_EXTRACTOR),
        "run",
        lambda self: expected
    )

    assert module.extract_all_articles() is expected