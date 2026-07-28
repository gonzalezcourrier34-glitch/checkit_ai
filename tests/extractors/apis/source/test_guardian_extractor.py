"""Tests légers de l'extracteur The Guardian Open Platform."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

import src.extractors.apis.source.guardian_extractor as module
from src.extractors.apis.api_extractor import ApiRequestError


# Configuration

def build_source(**overrides: Any) -> dict[str, Any]:
    """Construit une configuration Guardian minimale."""

    source = {
        "source_id": "guardian_api",
        "name": "The Guardian Open Platform",
        "endpoint": "https://content.guardianapis.com/search",
        "role": "acquisition",
        "language": "en",
        "category": "general",
        "page_size": 50,
        "max_pages": 5
    }
    source.update(overrides)
    return source


# Requêtes configurées

def test_get_configured_queries_returns_structured_queries(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = [
        {
            "query": "climate",
            "section": "environment"
        }
    ]

    monkeypatch.setattr(
        module,
        "get_queries_configuration",
        lambda source: expected
    )

    assert module.get_configured_queries({}) == expected


def test_get_configured_queries_accepts_mapping_fallback(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    query = {
        "query": "technology",
        "section": "technology"
    }

    monkeypatch.setattr(
        module,
        "get_queries_configuration",
        lambda source: []
    )

    assert module.get_configured_queries({
        "queries": query
    }) == [
        query
    ]


def test_get_configured_queries_accepts_sequence_fallback(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_queries_configuration",
        lambda source: []
    )

    result = module.get_configured_queries({
        "queries": [
            {
                "query": "climate"
            },
            "invalid",
            {
                "query": "technology"
            }
        ]
    })

    assert result == [
        {
            "query": "climate"
        },
        {
            "query": "technology"
        }
    ]


def test_get_configured_queries_uses_source_fallback(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    source = {
        "query": "climate",
        "section": "environment"
    }

    monkeypatch.setattr(
        module,
        "get_queries_configuration",
        lambda current_source: []
    )

    assert module.get_configured_queries(source) == [
        source
    ]


def test_merge_guardian_query_overrides_source_values() -> None:
    source = {
        "query": "climate",
        "section": "environment",
        "language": "en"
    }
    query = {
        "query": "artificial intelligence",
        "section": "technology"
    }

    assert module.merge_guardian_query(
        source,
        query
    ) == {
        "query": "artificial intelligence",
        "section": "technology",
        "language": "en"
    }


# Recherches et sections

def test_get_queries_normalizes_and_removes_duplicates(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_keywords",
        lambda source: [
            " climate change ",
            "artificial intelligence",
            "climate change",
            ""
        ]
    )

    assert module.get_queries({}) == [
        "climate change",
        "artificial intelligence"
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
    assert len(result[0]) == module.GUARDIAN_MAX_QUERY_LENGTH


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("World News", "world-news"),
        ("technology", "technology"),
        (" Science ", "science"),
        ("", ""),
        (None, "")
    ]
)
def test_normalize_guardian_section(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_guardian_section(value) == expected


def test_get_sections_normalizes_and_removes_duplicates() -> None:
    assert module.get_sections({
        "sections": [
            "World News",
            "Technology",
            "world news",
            ""
        ]
    }) == [
        "world-news",
        "technology"
    ]


# Champs Guardian

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("headline", "headline"),
        ("trail_text", "trailText"),
        ("body-text", "bodyText"),
        ("first_publication_date", "firstPublicationDate"),
        ("unknown", ""),
        ("", "")
    ]
)
def test_normalize_guardian_field(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_guardian_field(value) == expected


def test_get_show_fields_adds_required_fields() -> None:
    result = module.get_show_fields({
        "show_fields": [
            "publication",
            "short_url"
        ]
    })

    assert result == [
        "publication",
        "shortUrl",
        "headline",
        "trailText",
        "bodyText",
        "thumbnail",
        "byline"
    ]


def test_get_show_fields_removes_duplicates_and_invalid_fields() -> None:
    result = module.get_show_fields({
        "show_fields": [
            "headline",
            "headline",
            "invalid"
        ]
    })

    assert result == [
        "headline",
        "trailText",
        "bodyText",
        "thumbnail",
        "byline"
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("newest", "newest"),
        ("OLDEST", "oldest"),
        ("relevance", "relevance"),
        ("invalid", "newest"),
        ("", "newest"),
        (None, "newest")
    ]
)
def test_normalize_guardian_order_by(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_guardian_order_by(value) == expected


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


def test_get_page_size_respects_guardian_limit(
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
    ) == module.GUARDIAN_MAX_PAGE_SIZE


def test_get_max_pages_respects_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_pagination_value",
        lambda *args, **kwargs: 1000
    )

    assert module.get_max_pages({}) == module.GUARDIAN_MAX_PAGES


# Paramètres HTTP

def test_build_guardian_request_params() -> None:
    result = module.build_guardian_request_params(
        source=build_source(
            order_by="relevance",
            from_date="2026-07-01",
            to_date="2026-07-28",
            show_fields=[
                "publication",
                "short_url"
            ],
            tags=[
                "technology/artificial-intelligence",
                "environment/climate-change"
            ],
            types=[
                "article",
                "liveblog"
            ]
        ),
        query="artificial intelligence",
        section="Technology",
        page_number=2,
        page_size=100
    )

    assert result == {
        "page": 2,
        "page-size": 100,
        "order-by": "relevance",
        "format": "json",
        "q": "artificial intelligence",
        "section": "technology",
        "from-date": "2026-07-01",
        "to-date": "2026-07-28",
        "show-fields": (
            "publication,shortUrl,headline,trailText,"
            "bodyText,thumbnail,byline"
        ),
        "show-tags": "contributor",
        "tag": (
            "technology/artificial-intelligence|"
            "environment/climate-change"
        ),
        "type": "article|liveblog"
    }


def test_build_guardian_request_params_excludes_empty_values() -> None:
    result = module.build_guardian_request_params(
        source=build_source(),
        query="",
        section="",
        page_number=0,
        page_size=0
    )

    assert result["page"] == 1
    assert result["page-size"] == 1
    assert result["order-by"] == "newest"
    assert result["format"] == "json"
    assert result["show-tags"] == "contributor"
    assert "q" not in result
    assert "section" not in result
    assert "from-date" not in result
    assert "to-date" not in result
    assert "tag" not in result
    assert "type" not in result


def test_build_guardian_request_params_respects_limits() -> None:
    result = module.build_guardian_request_params(
        source=build_source(),
        query="a" * 600,
        section="World News",
        page_number=1000,
        page_size=1000
    )

    assert result["page"] == module.GUARDIAN_MAX_PAGES
    assert result["page-size"] == module.GUARDIAN_MAX_PAGE_SIZE
    assert len(result["q"]) == module.GUARDIAN_MAX_QUERY_LENGTH
    assert result["section"] == "world-news"


# Réseau

def test_fetch_guardian_page_delegates_to_fetch_json_object(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_fetch_json_object(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {
            "response": {
                "status": "ok"
            }
        }

    monkeypatch.setattr(
        module,
        "fetch_json_object",
        fake_fetch_json_object
    )

    result = module.fetch_guardian_page(
        endpoint="https://example.com/api",
        params={
            "page": 1
        },
        api_key="secret"
    )

    assert result == {
        "response": {
            "status": "ok"
        }
    }
    assert captured == {
        "url": "https://example.com/api",
        "params": {
            "page": 1,
            "api-key": "secret"
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
                "response": {
                    "message": "Clé invalide"
                }
            },
            "Clé invalide"
        ),
        (
            {
                "message": "Erreur générale"
            },
            "Erreur générale"
        ),
        (
            {},
            "Erreur non communiquée"
        )
    ]
)
def test_get_guardian_error_message(
    data: Mapping[str, Any],
    expected: str
) -> None:
    assert module.get_guardian_error_message(data) == expected


# Récupération d'une page

def test_request_guardian_page_rejects_invalid_endpoint() -> None:
    with pytest.raises(
        ValueError,
        match="Endpoint Guardian absent ou invalide"
    ):
        module.request_guardian_page(
            source=build_source(
                endpoint="invalid"
            ),
            query="climate",
            section="environment",
            page_number=1,
            page_size=50,
            api_key="secret"
        )


def test_request_guardian_page_rejects_invalid_response(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "fetch_guardian_page",
        lambda *args, **kwargs: {
            "response": "invalid"
        }
    )

    with pytest.raises(
        ValueError,
        match="response de Guardian"
    ):
        module.request_guardian_page(
            source=build_source(),
            query="climate",
            section="environment",
            page_number=1,
            page_size=50,
            api_key="secret"
        )


def test_request_guardian_page_returns_results(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "fetch_guardian_page",
        lambda *args, **kwargs: {
            "response": {
                "status": "ok",
                "pages": 3,
                "total": 120,
                "results": [
                    {
                        "id": "article-1"
                    },
                    "invalid",
                    {
                        "id": "article-2"
                    }
                ]
            }
        }
    )

    results, total_pages, total_results = module.request_guardian_page(
        source=build_source(),
        query="climate",
        section="environment",
        page_number=1,
        page_size=50,
        api_key="secret"
    )

    assert results == [
        {
            "id": "article-1"
        },
        {
            "id": "article-2"
        }
    ]
    assert total_pages == 3
    assert total_results == 120


def test_request_guardian_page_raises_request_error(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "fetch_guardian_page",
        lambda *args, **kwargs: {
            "response": {
                "status": "error",
                "message": "Clé API invalide"
            }
        }
    )
    monkeypatch.setattr(
        module,
        "raise_if_fatal_api_error",
        lambda error, source_name: None
    )

    with pytest.raises(ApiRequestError):
        module.request_guardian_page(
            source=build_source(),
            query="climate",
            section="environment",
            page_number=1,
            page_size=50,
            api_key="secret"
        )


# Pagination multi-pages

def test_request_guardian_articles_returns_empty_for_zero_maximum() -> None:
    assert module.request_guardian_articles(
        source=build_source(),
        query="climate",
        section="environment",
        max_articles=0,
        api_key="secret"
    ) == []


def test_request_guardian_articles_collects_multiple_pages(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    responses = iter([
        (
            [
                {
                    "id": "article-1"
                },
                {
                    "id": "article-2"
                }
            ],
            2,
            3
        ),
        (
            [
                {
                    "id": "article-3"
                }
            ],
            2,
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
        "request_guardian_page",
        lambda **kwargs: next(responses)
    )

    result = module.request_guardian_articles(
        source=build_source(),
        query="climate",
        section="environment",
        max_articles=5,
        api_key="secret"
    )

    assert result == [
        {
            "id": "article-1"
        },
        {
            "id": "article-2"
        },
        {
            "id": "article-3"
        }
    ]


def test_request_guardian_articles_respects_maximum(
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
        "request_guardian_page",
        lambda **kwargs: (
            [
                {
                    "id": f"article-{index}"
                }
                for index in range(10)
            ],
            1,
            10
        )
    )

    result = module.request_guardian_articles(
        source=build_source(),
        query="",
        section="",
        max_articles=3,
        api_key="secret"
    )

    assert len(result) == 3


def test_request_guardian_articles_stops_on_partial_page(
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
        lambda source, remaining_articles: 50
    )

    def fake_request_page(**kwargs: Any) -> tuple[
        list[dict[str, Any]],
        int,
        int
    ]:
        nonlocal calls
        calls += 1

        return (
            [
                {
                    "id": "article-1"
                }
            ],
            5,
            100
        )

    monkeypatch.setattr(
        module,
        "request_guardian_page",
        fake_request_page
    )

    result = module.request_guardian_articles(
        source=build_source(),
        query="climate",
        section="environment",
        max_articles=100,
        api_key="secret"
    )

    assert result == [
        {
            "id": "article-1"
        }
    ]
    assert calls == 1


# Parcours

def test_iter_guardian_items_returns_nothing_for_zero() -> None:
    assert list(
        module.iter_guardian_items(
            build_source(),
            0
        )
    ) == []


def test_iter_guardian_items_enriches_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_guardian_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "get_configured_queries",
        lambda source: [
            {
                "query": "climate",
                "section": "environment"
            }
        ]
    )
    monkeypatch.setattr(
        module,
        "request_guardian_articles",
        lambda **kwargs: [
            {
                "id": "article-1"
            },
            {
                "id": "article-2"
            }
        ]
    )

    result = list(
        module.iter_guardian_items(
            build_source(),
            2
        )
    )

    assert result == [
        (
            "query=climate|section=environment",
            0,
            {
                "id": "article-1",
                "_requested_query": "climate",
                "_requested_section": "environment"
            }
        ),
        (
            "query=climate|section=environment",
            1,
            {
                "id": "article-2",
                "_requested_query": "climate",
                "_requested_section": "environment"
            }
        )
    ]


def test_iter_guardian_items_respects_maximum(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_guardian_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "request_guardian_articles",
        lambda **kwargs: [
            {
                "id": f"article-{index}"
            }
            for index in range(10)
        ]
    )

    result = list(
        module.iter_guardian_items(
            build_source(
                query="climate",
                section="environment"
            ),
            3
        )
    )

    assert len(result) == 3


# Lecture des champs

def test_get_guardian_fields_returns_mapping() -> None:
    fields = {
        "headline": "Titre"
    }

    assert module.get_guardian_fields({
        "fields": fields
    }) == fields


def test_get_guardian_fields_rejects_invalid_value() -> None:
    assert module.get_guardian_fields({
        "fields": "invalid"
    }) == {}


def test_get_guardian_title_prefers_headline() -> None:
    assert module.get_guardian_title({
        "webTitle": "Titre web",
        "fields": {
            "headline": "Titre principal"
        }
    }) == "Titre principal"


def test_get_guardian_title_uses_web_title_fallback() -> None:
    assert module.get_guardian_title({
        "webTitle": "Titre web",
        "fields": {}
    }) == "Titre web"


def test_get_guardian_text_prefers_body_text() -> None:
    assert module.get_guardian_text({
        "fields": {
            "bodyText": "Corps complet",
            "trailText": "Résumé"
        }
    }) == "Corps complet"


def test_get_guardian_text_uses_trail_text_fallback() -> None:
    assert module.get_guardian_text({
        "fields": {
            "bodyText": "",
            "trailText": "Résumé"
        }
    }) == "Résumé"


def test_get_guardian_author_prefers_byline() -> None:
    assert module.get_guardian_author({
        "fields": {
            "byline": "Jane Doe"
        },
        "tags": [
            {
                "type": "contributor",
                "webTitle": "John Doe"
            }
        ]
    }) == "Jane Doe"


def test_get_guardian_author_uses_contributor_tags() -> None:
    assert module.get_guardian_author({
        "fields": {},
        "tags": [
            {
                "type": "contributor",
                "webTitle": "Jane Doe"
            },
            {
                "type": "keyword",
                "webTitle": "Technology"
            },
            {
                "type": "contributor",
                "webTitle": "John Doe"
            },
            {
                "type": "contributor",
                "webTitle": "Jane Doe"
            }
        ]
    }) == "Jane Doe, John Doe"


def test_get_guardian_author_rejects_invalid_tags() -> None:
    assert module.get_guardian_author({
        "fields": {},
        "tags": "invalid"
    }) == ""


def test_get_guardian_image_url_returns_valid_url() -> None:
    assert module.get_guardian_image_url({
        "fields": {
            "thumbnail": "https://example.com/image.jpg"
        }
    }) == "https://example.com/image.jpg"


def test_get_guardian_image_url_rejects_invalid_url() -> None:
    assert module.get_guardian_image_url({
        "fields": {
            "thumbnail": "invalid"
        }
    }) == ""


def test_get_guardian_language_prefers_language() -> None:
    assert module.get_guardian_language({
        "language": "FR",
        "languages": [
            "en"
        ]
    }) == "fr"


def test_get_guardian_language_uses_languages_fallback(
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

    assert module.get_guardian_language({}) == "fr"


def test_get_guardian_language_uses_english_default(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_configuration_values",
        lambda *args, **kwargs: []
    )

    assert module.get_guardian_language({}) == "en"


# Construction d'article

def test_build_guardian_article_rejects_invalid_item() -> None:
    assert module.build_guardian_article(
        item="invalid",
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_guardian_article_rejects_missing_identifier() -> None:
    assert module.build_guardian_article(
        item={
            "webTitle": "Titre"
        },
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_guardian_article_builds_standard_article(
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

    result = module.build_guardian_article(
        item={
            "id": "technology/2026/jul/28/article",
            "webUrl": "https://example.com/article",
            "webPublicationDate": "2026-07-28T10:00:00Z",
            "sectionId": "Technology",
            "fields": {
                "headline": "Titre de l'article",
                "bodyText": "Contenu complet",
                "thumbnail": "https://example.com/image.jpg",
                "byline": "Jane Doe"
            },
            "_requested_section": "general"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source(
            language="EN"
        )
    )

    assert result == captured
    assert captured["identifier"] == (
        "technology/2026/jul/28/article"
    )
    assert captured["source"] == "The Guardian Open Platform"
    assert captured["title"] == "Titre de l'article"
    assert captured["text"] == "Contenu complet"
    assert captured["url"] == "https://example.com/article"
    assert captured["image_url"] == "https://example.com/image.jpg"
    assert captured["author"] == "Jane Doe"
    assert captured["language"] == "en"
    assert captured["category"] == "technology"


def test_build_guardian_article_uses_requested_section_fallback(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_guardian_article(
        item={
            "id": "article-1",
            "webUrl": "https://example.com/article",
            "sectionId": "",
            "_requested_section": "World News"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert captured["category"] == "world-news"


def test_build_guardian_article_uses_source_category_fallback(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_guardian_article(
        item={
            "id": "article-1",
            "webUrl": "https://example.com/article"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source(
            category="politics"
        )
    )

    assert captured["category"] == "politics"


def test_build_guardian_article_removes_invalid_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_guardian_article(
        item={
            "id": "article-1",
            "webUrl": "invalid"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert captured["url"] == ""


# Validation

@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (
            None,
            (
                False,
                "resultat_guardian_invalide"
            )
        ),
        (
            {},
            (
                False,
                "identifiant_guardian_absent"
            )
        ),
        (
            {
                "id": "article-1",
                "webUrl": "invalid"
            },
            (
                False,
                "url_guardian_invalide"
            )
        ),
        (
            {
                "id": "article-1",
                "webUrl": "https://example.com/article"
            },
            (
                True,
                ""
            )
        )
    ]
)
def test_validate_guardian_item(
    item: Any,
    expected: tuple[bool, str]
) -> None:
    assert module.validate_guardian_item(
        item=item,
        filters={},
        source={}
    ) == expected


# API publique

def test_load_guardian_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        type(module.GUARDIAN_EXTRACTOR),
        "reload_source",
        lambda self: {
            "source_id": "guardian_api"
        }
    )

    assert module.load_guardian_source() == {
        "source_id": "guardian_api"
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
    assert captured["adapter"] is module.GUARDIAN_ADAPTER


def test_extract_all_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()

    monkeypatch.setattr(
        type(module.GUARDIAN_EXTRACTOR),
        "run",
        lambda self: expected
    )

    assert module.extract_all_articles() is expected