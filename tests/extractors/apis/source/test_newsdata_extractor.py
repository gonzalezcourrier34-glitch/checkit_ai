"""Tests légers de l'extracteur NewsData.io."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

import src.extractors.apis.source.newsdata_extractor as module
from src.extractors.apis.api_extractor import ApiRequestError


# Configuration

def build_source(**overrides: Any) -> dict[str, Any]:
    """Construit une configuration NewsData.io minimale."""

    source = {
        "source_id": "newsdata",
        "name": "NewsData.io",
        "endpoint": "https://newsdata.io/api/1/latest",
        "role": "acquisition",
        "category": "general",
        "max_pages": 5,
        "exclude_duplicates": True
    }
    source.update(overrides)
    return source


# Requêtes configurées

def test_get_newsdata_queries_returns_configured_queries(
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

    assert module.get_newsdata_queries({}) == expected


def test_get_newsdata_queries_uses_source_fallback(
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

    assert module.get_newsdata_queries(source) == [
        source
    ]


def test_merge_newsdata_query_excludes_queries() -> None:
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

    assert module.merge_newsdata_query(
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
                "fr",
                "us"
            ],
            "fr,us"
        ),
        (
            "fr",
            "fr"
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
    assert len(result[0]) == module.NEWSDATA_MAX_QUERY_LENGTH


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


def test_get_categories_delegates_to_configuration_helper(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_configuration_values",
        lambda *args, **kwargs: [
            "technology",
            "science"
        ]
    )

    assert module.get_categories({}) == [
        "technology",
        "science"
    ]


# Pagination

def test_get_max_pages_respects_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_pagination_value",
        lambda *args, **kwargs: 1000
    )

    assert module.get_max_pages({}) == module.NEWSDATA_MAX_PAGES


# Paramètres HTTP

def test_build_newsdata_request_params(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_queries",
        lambda source: [
            "climat",
            "énergie"
        ]
    )

    result = module.build_newsdata_request_params(
        source=build_source(
            countries=[
                "fr",
                "be"
            ],
            domains=[
                "example.com"
            ],
            excluded_domains=[
                "spam.example"
            ]
        ),
        language="FR",
        category="TECHNOLOGY",
        page_token="token-2"
    )

    assert result == {
        "language": "fr",
        "category": "technology",
        "page": "token-2",
        "q": "climat OR énergie",
        "country": "fr,be",
        "domain": "example.com",
        "excludedomain": "spam.example",
        "removeduplicate": "1"
    }


def test_build_newsdata_request_params_excludes_empty_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_queries",
        lambda source: []
    )

    result = module.build_newsdata_request_params(
        source=build_source(
            exclude_duplicates=False
        ),
        language="",
        category="",
        page_token=""
    )

    assert result == {}


def test_build_newsdata_request_params_can_disable_duplicates(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_queries",
        lambda source: [
            "climat"
        ]
    )

    result = module.build_newsdata_request_params(
        source=build_source(
            exclude_duplicates=False
        ),
        language="fr",
        category="science"
    )

    assert result == {
        "language": "fr",
        "category": "science",
        "q": "climat"
    }


# Réseau

def test_fetch_newsdata_page_delegates_to_fetch_json_object(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_fetch_json_object(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {
            "status": "success",
            "results": []
        }

    monkeypatch.setattr(
        module,
        "fetch_json_object",
        fake_fetch_json_object
    )

    result = module.fetch_newsdata_page(
        endpoint="https://example.com/api",
        params={
            "language": "fr"
        },
        api_key="secret"
    )

    assert result == {
        "status": "success",
        "results": []
    }
    assert captured == {
        "url": "https://example.com/api",
        "params": {
            "language": "fr",
            "apikey": "secret"
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
                "results": {
                    "code": "apiKeyInvalid",
                    "message": "Clé invalide"
                }
            },
            (
                "apiKeyInvalid",
                "Clé invalide"
            )
        ),
        (
            {
                "code": "rateLimit",
                "message": "Limite atteinte"
            },
            (
                "rateLimit",
                "Limite atteinte"
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
def test_get_newsdata_error_details(
    data: Mapping[str, Any],
    expected: tuple[str, str]
) -> None:
    assert module.get_newsdata_error_details(data) == expected


# Récupération d'une page

def test_request_newsdata_page_rejects_invalid_endpoint() -> None:
    with pytest.raises(
        ValueError,
        match="Endpoint NewsData.io absent ou invalide"
    ):
        module.request_newsdata_page(
            source=build_source(
                endpoint="invalid"
            ),
            language="fr",
            category="technology",
            api_key="secret"
        )


def test_request_newsdata_page_returns_articles_and_token(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_newsdata_request_params",
        lambda **kwargs: {
            "language": "fr"
        }
    )
    monkeypatch.setattr(
        module,
        "fetch_newsdata_page",
        lambda **kwargs: {
            "status": "success",
            "results": [
                {
                    "article_id": "article-1"
                },
                "invalid",
                {
                    "article_id": "article-2"
                }
            ],
            "nextPage": "token-2"
        }
    )

    articles, token = module.request_newsdata_page(
        source=build_source(),
        language="fr",
        category="technology",
        api_key="secret"
    )

    assert articles == [
        {
            "article_id": "article-1"
        },
        {
            "article_id": "article-2"
        }
    ]
    assert token == "token-2"


def test_request_newsdata_page_raises_request_error(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_newsdata_request_params",
        lambda **kwargs: {
            "language": "fr"
        }
    )
    monkeypatch.setattr(
        module,
        "fetch_newsdata_page",
        lambda **kwargs: {
            "status": "error",
            "results": {
                "code": "apiKeyInvalid",
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
        module.request_newsdata_page(
            source=build_source(),
            language="fr",
            category="technology",
            api_key="secret"
        )


# Pagination multi-pages

def test_request_newsdata_articles_returns_empty_for_zero() -> None:
    assert module.request_newsdata_articles(
        source=build_source(),
        language="fr",
        category="technology",
        max_articles=0,
        api_key="secret"
    ) == []


def test_request_newsdata_articles_collects_multiple_pages(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    responses = iter([
        (
            [
                {
                    "article_id": "article-1"
                },
                {
                    "article_id": "article-2"
                }
            ],
            "token-2"
        ),
        (
            [
                {
                    "article_id": "article-3"
                }
            ],
            ""
        )
    ])

    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 5
    )
    monkeypatch.setattr(
        module,
        "request_newsdata_page",
        lambda **kwargs: next(responses)
    )

    result = module.request_newsdata_articles(
        source=build_source(),
        language="fr",
        category="technology",
        max_articles=5,
        api_key="secret"
    )

    assert result == [
        {
            "article_id": "article-1"
        },
        {
            "article_id": "article-2"
        },
        {
            "article_id": "article-3"
        }
    ]


def test_request_newsdata_articles_respects_maximum(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 1
    )
    monkeypatch.setattr(
        module,
        "request_newsdata_page",
        lambda **kwargs: (
            [
                {
                    "article_id": f"article-{index}"
                }
                for index in range(10)
            ],
            ""
        )
    )

    result = module.request_newsdata_articles(
        source=build_source(),
        language="fr",
        category="technology",
        max_articles=3,
        api_key="secret"
    )

    assert len(result) == 3


def test_request_newsdata_articles_stops_on_repeated_token(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 5
    )

    def fake_request_page(**kwargs: Any) -> tuple[
        list[dict[str, Any]],
        str
    ]:
        nonlocal calls
        calls += 1

        return (
            [
                {
                    "article_id": f"article-{calls}"
                }
            ],
            "same-token"
        )

    monkeypatch.setattr(
        module,
        "request_newsdata_page",
        fake_request_page
    )

    result = module.request_newsdata_articles(
        source=build_source(),
        language="fr",
        category="technology",
        max_articles=10,
        api_key="secret"
    )

    assert result == [
        {
            "article_id": "article-1"
        },
        {
            "article_id": "article-2"
        }
    ]
    assert calls == 2


# Parcours

def test_iter_newsdata_items_returns_nothing_for_zero() -> None:
    assert list(
        module.iter_newsdata_items(
            build_source(),
            0
        )
    ) == []


def test_iter_newsdata_items_enriches_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_newsdata_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "get_newsdata_queries",
        lambda source: [
            {
                "languages": [
                    "fr"
                ],
                "categories": [
                    "technology"
                ]
            }
        ]
    )
    monkeypatch.setattr(
        module,
        "request_newsdata_articles",
        lambda **kwargs: [
            {
                "article_id": "article-1"
            }
        ]
    )

    result = list(
        module.iter_newsdata_items(
            build_source(),
            1
        )
    )

    assert result == [
        (
            "language=fr|category=technology",
            0,
            {
                "article_id": "article-1",
                "_requested_language": "fr",
                "_requested_category": "technology"
            }
        )
    ]


def test_iter_newsdata_items_respects_maximum(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_newsdata_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "request_newsdata_articles",
        lambda **kwargs: [
            {
                "article_id": f"article-{index}"
            }
            for index in range(10)
        ]
    )

    result = list(
        module.iter_newsdata_items(
            build_source(
                language="fr",
                category="technology"
            ),
            3
        )
    )

    assert len(result) == 3


# Champs

def test_get_newsdata_article_text_prefers_content() -> None:
    assert module.get_newsdata_article_text({
        "content": "Contenu complet",
        "description": "Description"
    }) == "Contenu complet"


def test_get_newsdata_article_text_uses_description_fallback() -> None:
    assert module.get_newsdata_article_text({
        "content": "",
        "description": "Description"
    }) == "Description"


def test_get_newsdata_publisher_prefers_source_name() -> None:
    assert module.get_newsdata_publisher({
        "source_name": "Reuters",
        "source_id": "reuters"
    }) == "Reuters"


def test_get_newsdata_publisher_uses_source_id_fallback() -> None:
    assert module.get_newsdata_publisher({
        "source_name": "",
        "source_id": "reuters"
    }) == "reuters"


def test_build_newsdata_identifier_prefers_article_id() -> None:
    assert module.build_newsdata_identifier(
        {
            "article_id": "article-123",
            "link": "https://example.com/article"
        },
        "request-1"
    ) == "article-123"


def test_build_newsdata_identifier_uses_url_fallback() -> None:
    assert module.build_newsdata_identifier(
        {
            "link": "https://example.com/article"
        },
        "request-1"
    ) == "https://example.com/article"


def test_build_newsdata_identifier_uses_generated_fallback() -> None:
    result = module.build_newsdata_identifier(
        {
            "link": "invalid",
            "pubDate": "2026-07-28 10:00:00",
            "title": "Titre de l'article"
        },
        "request-1"
    )

    assert result == (
        "newsdata:request-1:"
        "2026-07-28 10:00:00:"
        "Titre de l'article"
    )


# Construction d'article

def test_build_newsdata_article_rejects_invalid_item() -> None:
    assert module.build_newsdata_article(
        item="invalid",
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_newsdata_article_rejects_missing_identifier() -> None:
    assert module.build_newsdata_article(
        item={
            "title": "Titre"
        },
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_newsdata_article_builds_standard_article(
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

    result = module.build_newsdata_article(
        item={
            "article_id": "article-123",
            "title": "Titre de l'article",
            "content": "Contenu complet",
            "link": "https://example.com/article",
            "image_url": "https://example.com/image.jpg",
            "pubDate": "2026-07-28 10:00:00",
            "creator": [
                "Jane Doe",
                "John Doe"
            ],
            "language": "FR",
            "category": [
                "technology",
                "science"
            ],
            "source_name": "Reuters",
            "source_id": "reuters",
            "source_priority": 1,
            "_requested_language": "en",
            "_requested_category": "general"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert result == captured
    assert captured["identifier"] == "article-123"
    assert captured["source"] == "NewsData.io"
    assert captured["title"] == "Titre de l'article"
    assert captured["text"] == "Contenu complet"
    assert captured["image_url"] == "https://example.com/image.jpg"
    assert captured["url"] == "https://example.com/article"
    assert captured["author"] == "Jane Doe,John Doe"
    assert captured["language"] == "fr"
    assert captured["category"] == "technology,science"
    assert captured["metadata"] == {
        "publisher": "Reuters",
        "source_id": "reuters",
        "source_priority": 1
    }


def test_build_newsdata_article_uses_requested_fallbacks(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_newsdata_article(
        item={
            "article_id": "article-123",
            "title": "Titre",
            "_requested_language": "fr",
            "_requested_category": "science"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert captured["language"] == "fr"
    assert captured["category"] == "science"


def test_build_newsdata_article_removes_invalid_urls(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_newsdata_article(
        item={
            "article_id": "article-123",
            "title": "Titre",
            "link": "invalid",
            "image_url": "invalid"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert captured["url"] == ""
    assert captured["image_url"] == ""


# Validation

@pytest.mark.parametrize(
    ("item", "source", "expected"),
    [
        (
            None,
            build_source(),
            (
                False,
                "resultat_newsdata_invalide"
            )
        ),
        (
            {
                "article_id": "article-1",
                "duplicate": True,
                "title": "Titre"
            },
            build_source(
                exclude_duplicates=True
            ),
            (
                False,
                "doublon_signale_api"
            )
        ),
        (
            {
                "title": "Titre"
            },
            build_source(),
            (
                False,
                "identifiant_newsdata_absent"
            )
        ),
        (
            {
                "article_id": "article-1",
                "link": "invalid",
                "title": "Titre"
            },
            build_source(),
            (
                False,
                "url_newsdata_invalide"
            )
        ),
        (
            {
                "article_id": "article-1",
                "title": ""
            },
            build_source(),
            (
                False,
                "titre_newsdata_absent"
            )
        ),
        (
            {
                "article_id": "article-1",
                "title": "Titre"
            },
            build_source(),
            (
                True,
                ""
            )
        ),
        (
            {
                "article_id": "article-1",
                "duplicate": True,
                "title": "Titre"
            },
            build_source(
                exclude_duplicates=False
            ),
            (
                True,
                ""
            )
        )
    ]
)
def test_validate_newsdata_item(
    item: Any,
    source: Mapping[str, Any],
    expected: tuple[bool, str]
) -> None:
    assert module.validate_newsdata_item(
        item=item,
        filters={},
        source=source
    ) == expected


# API publique

def test_load_newsdata_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        type(module.NEWSDATA_EXTRACTOR),
        "reload_source",
        lambda self: {
            "source_id": "newsdata"
        }
    )

    assert module.load_newsdata_source() == {
        "source_id": "newsdata"
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
    assert captured["adapter"] is module.NEWSDATA_ADAPTER


def test_extract_all_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()

    monkeypatch.setattr(
        type(module.NEWSDATA_EXTRACTOR),
        "run",
        lambda self: expected
    )

    assert module.extract_all_articles() is expected