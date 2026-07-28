"""Tests légers de l'extracteur GNews."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

import src.extractors.apis.source.gnews_extractor as module
from src.extractors.apis.api_extractor import ApiRequestError


# Configuration

def build_source(**overrides: Any) -> dict[str, Any]:
    """Construit une configuration GNews minimale."""

    source = {
        "source_id": "gnews",
        "name": "GNews",
        "endpoint": "https://gnews.io/api/v4/search",
        "role": "acquisition",
        "max_articles": 10,
        "max_article_age_days": 30,
        "request_delay_seconds": 0
    }
    source.update(overrides)
    return source


# Requêtes configurées

def test_get_gnews_queries_returns_structured_queries(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = [
        {
            "keywords": [
                "intelligence artificielle"
            ],
            "language": "fr"
        }
    ]

    monkeypatch.setattr(
        module,
        "get_queries_configuration",
        lambda source: expected
    )

    assert module.get_gnews_queries({}) == expected


def test_get_gnews_queries_uses_source_fallback(
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

    assert module.get_gnews_queries(source) == [
        source
    ]


def test_merge_gnews_query_excludes_queries_and_overrides_values() -> None:
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

    assert module.merge_gnews_query(
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
            "a" * 300
        ]
    )

    result = module.get_keywords({})

    assert len(result) == 1
    assert len(result[0]) == module.GNEWS_MAX_QUERY_LENGTH


def test_get_languages_delegates_to_configuration_helper(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_get_values(
        source: Mapping[str, Any],
        plural_key: str,
        singular_key: str,
        lowercase: bool
    ) -> list[str]:
        captured.update({
            "source": source,
            "plural_key": plural_key,
            "singular_key": singular_key,
            "lowercase": lowercase
        })
        return [
            "fr",
            "en"
        ]

    monkeypatch.setattr(
        module,
        "get_query_configuration_values",
        fake_get_values
    )

    source = {
        "languages": [
            "FR",
            "EN"
        ]
    }

    assert module.get_languages(source) == [
        "fr",
        "en"
    ]
    assert captured == {
        "source": source,
        "plural_key": "languages",
        "singular_key": "language",
        "lowercase": True
    }


def test_get_countries_keeps_valid_codes(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_configuration_values",
        lambda *args, **kwargs: [
            "fr",
            "us",
            "fr"
        ]
    )

    assert module.get_countries({}) == [
        "fr",
        "us"
    ]


def test_get_countries_ignores_invalid_codes(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_configuration_values",
        lambda *args, **kwargs: [
            "fr",
            "fra",
            "1a",
            ""
        ]
    )

    assert module.get_countries({}) == [
        "fr"
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("TECHNOLOGY", "technology"),
        ("health", "health"),
        ("general", "general"),
        ("unknown", ""),
        ("", ""),
        (None, "")
    ]
)
def test_normalize_category(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_category(value) == expected


def test_get_categories_keeps_supported_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_configuration_values",
        lambda *args, **kwargs: [
            "technology",
            "unknown",
            "sports",
            "technology"
        ]
    )

    assert module.get_categories({}) == [
        "technology",
        "sports"
    ]


# Pagination

def test_get_max_records_per_request_respects_remaining_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_pagination_value",
        lambda *args, **kwargs: 50
    )

    assert module.get_max_records_per_request(
        source={},
        remaining_articles=12
    ) == 12


def test_get_max_records_per_request_respects_api_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_pagination_value",
        lambda *args, **kwargs: 500
    )

    assert module.get_max_records_per_request(
        source={},
        remaining_articles=500
    ) == module.GNEWS_API_MAX_RECORDS


# Dates

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            "2026-07-20",
            "2026-07-20T00:00:00+00:00"
        ),
        (
            "2026-07-20T10:30:00Z",
            "2026-07-20T10:30:00+00:00"
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
def test_parse_gnews_date(
    value: Any,
    expected: str | None
) -> None:
    result = module.parse_gnews_date(
        value,
        "from"
    )

    assert (
        result.isoformat()
        if result is not None
        else None
    ) == expected


def test_format_gnews_date() -> None:
    parsed = module.parse_gnews_date(
        "2026-07-20T10:30:45Z",
        "from"
    )

    assert parsed is not None
    assert module.format_gnews_date(parsed) == "2026-07-20T10:30:45Z"


def test_get_gnews_date_range_swaps_reversed_dates() -> None:
    source = build_source(
        **{
            "from": "2026-07-20T00:00:00Z",
            "to": "2026-07-10T00:00:00Z"
        }
    )

    assert module.get_gnews_date_range(source) == (
        "2026-07-13T00:00:00Z",
        "2026-07-20T00:00:00Z"
    )


def test_get_gnews_date_range_limits_period() -> None:
    source = build_source(
        max_article_age_days=10,
        **{
            "from": "2026-01-01T00:00:00Z",
            "to": "2026-01-30T00:00:00Z"
        }
    )

    assert module.get_gnews_date_range(source) == (
        "2026-01-23T00:00:00Z",
        "2026-01-30T00:00:00Z"
    )


# Paramètres HTTP

def test_build_gnews_request_params(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_gnews_date_range",
        lambda source: (
            "2026-07-01T00:00:00Z",
            "2026-07-20T00:00:00Z"
        )
    )

    result = module.build_gnews_request_params(
        source=build_source(),
        keyword="intelligence artificielle",
        language="FR",
        category="TECHNOLOGY",
        country="US",
        max_records=30
    )

    assert result == {
        "max": 30,
        "q": "intelligence artificielle",
        "lang": "fr",
        "category": "technology",
        "country": "us",
        "from": "2026-07-01T00:00:00Z",
        "to": "2026-07-20T00:00:00Z"
    }


def test_build_gnews_request_params_excludes_empty_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_gnews_date_range",
        lambda source: (
            "",
            ""
        )
    )

    result = module.build_gnews_request_params(
        source=build_source(),
        keyword="",
        language="",
        category="invalid",
        country="",
        max_records=10
    )

    assert result == {
        "max": 10
    }


def test_build_gnews_request_params_respects_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_gnews_date_range",
        lambda source: (
            "",
            ""
        )
    )

    result = module.build_gnews_request_params(
        source=build_source(),
        keyword="",
        language="",
        category="",
        country="",
        max_records=1000
    )

    assert result["max"] == module.GNEWS_API_MAX_RECORDS


# Réseau

def test_fetch_gnews_data_delegates_to_fetch_json_object(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_fetch_json_object(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {
            "articles": []
        }

    monkeypatch.setattr(
        module,
        "fetch_json_object",
        fake_fetch_json_object
    )

    result = module.fetch_gnews_data(
        endpoint="https://example.com/api",
        params={
            "q": "climat"
        },
        api_key="secret"
    )

    assert result == {
        "articles": []
    }
    assert captured == {
        "url": "https://example.com/api",
        "params": {
            "q": "climat",
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
                "errors": [
                    "Erreur 1",
                    "Erreur 2"
                ]
            },
            "Erreur 1 | Erreur 2"
        ),
        (
            {
                "message": "Erreur principale"
            },
            "Erreur principale"
        ),
        (
            {},
            "Erreur non communiquée"
        )
    ]
)
def test_get_gnews_error_message(
    data: Mapping[str, Any],
    expected: str
) -> None:
    assert module.get_gnews_error_message(data) == expected


def test_request_gnews_articles_rejects_invalid_endpoint() -> None:
    with pytest.raises(
        ValueError,
        match="Endpoint GNews absent ou invalide"
    ):
        module.request_gnews_articles(
            source=build_source(
                endpoint="invalid"
            ),
            keyword="",
            language="",
            category="general",
            country="",
            max_records=10,
            api_key="secret"
        )


def test_request_gnews_articles_returns_mapping_items(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_gnews_request_params",
        lambda **kwargs: {
            "max": 10
        }
    )
    monkeypatch.setattr(
        module,
        "fetch_gnews_data",
        lambda **kwargs: {
            "articles": [
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

    result = module.request_gnews_articles(
        source=build_source(),
        keyword="climat",
        language="fr",
        category="science",
        country="fr",
        max_records=10,
        api_key="secret"
    )

    assert result == [
        {
            "id": "article-1"
        },
        {
            "id": "article-2"
        }
    ]


def test_request_gnews_articles_respects_maximum(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_gnews_request_params",
        lambda **kwargs: {
            "max": 2
        }
    )
    monkeypatch.setattr(
        module,
        "fetch_gnews_data",
        lambda **kwargs: {
            "articles": [
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
        }
    )

    result = module.request_gnews_articles(
        source=build_source(),
        keyword="",
        language="",
        category="general",
        country="",
        max_records=2,
        api_key="secret"
    )

    assert len(result) == 2


def test_request_gnews_articles_raises_request_error(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_gnews_request_params",
        lambda **kwargs: {
            "max": 10
        }
    )
    monkeypatch.setattr(
        module,
        "fetch_gnews_data",
        lambda **kwargs: {
            "errors": [
                "Clé invalide"
            ]
        }
    )
    monkeypatch.setattr(
        module,
        "raise_if_fatal_api_error",
        lambda error, source_name: None
    )

    with pytest.raises(ApiRequestError):
        module.request_gnews_articles(
            source=build_source(),
            keyword="",
            language="",
            category="general",
            country="",
            max_records=10,
            api_key="secret"
        )


# Parcours

def test_iter_gnews_items_returns_nothing_for_zero_maximum() -> None:
    assert list(
        module.iter_gnews_items(
            build_source(),
            0
        )
    ) == []


def test_iter_gnews_items_enriches_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_gnews_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "get_gnews_queries",
        lambda source: [
            {
                "keywords": [
                    "climat"
                ],
                "languages": [
                    "fr"
                ],
                "categories": [
                    "science"
                ],
                "countries": [
                    "fr"
                ]
            }
        ]
    )
    monkeypatch.setattr(
        module,
        "request_gnews_articles",
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
        module.iter_gnews_items(
            build_source(),
            2
        )
    )

    assert result == [
        (
            "query=climat|lang=fr|category=science|country=fr",
            0,
            {
                "id": "article-1",
                "_requested_keyword": "climat",
                "_requested_language": "fr",
                "_requested_category": "science",
                "_requested_country": "fr"
            }
        ),
        (
            "query=climat|lang=fr|category=science|country=fr",
            1,
            {
                "id": "article-2",
                "_requested_keyword": "climat",
                "_requested_language": "fr",
                "_requested_category": "science",
                "_requested_country": "fr"
            }
        )
    ]


def test_iter_gnews_items_respects_maximum(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_gnews_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "request_gnews_articles",
        lambda **kwargs: [
            {
                "id": f"article-{index}"
            }
            for index in range(10)
        ]
    )

    result = list(
        module.iter_gnews_items(
            build_source(
                keywords=[
                    "climat"
                ],
                languages=[
                    "fr"
                ],
                categories=[
                    "science"
                ],
                countries=[
                    "fr"
                ]
            ),
            3
        )
    )

    assert len(result) == 3


# Champs

def test_get_gnews_article_text_prefers_content() -> None:
    assert module.get_gnews_article_text({
        "content": "Contenu complet",
        "description": "Description"
    }) == "Contenu complet"


def test_get_gnews_article_text_uses_description_fallback() -> None:
    assert module.get_gnews_article_text({
        "content": "",
        "description": "Description"
    }) == "Description"


def test_get_gnews_article_author_prefers_author() -> None:
    assert module.get_gnews_article_author({
        "author": "Auteur principal",
        "source": {
            "name": "Nom de la source"
        }
    }) == "Auteur principal"


def test_get_gnews_article_author_uses_source_name() -> None:
    assert module.get_gnews_article_author({
        "source": {
            "name": "Nom de la source"
        }
    }) == "Nom de la source"


# Construction d'article

def test_build_gnews_article_rejects_invalid_item() -> None:
    assert module.build_gnews_article(
        item="invalid",
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_gnews_article_rejects_missing_identifier() -> None:
    assert module.build_gnews_article(
        item={
            "title": "Titre"
        },
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_gnews_article_builds_standard_article(
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

    result = module.build_gnews_article(
        item={
            "id": "article-1",
            "title": "Titre de l'article",
            "content": "Contenu de l'article",
            "url": "https://example.com/article",
            "image": "https://example.com/image.jpg",
            "publishedAt": "2026-07-20T10:00:00Z",
            "author": "Auteur",
            "lang": "FR",
            "_requested_language": "en",
            "_requested_category": "technology"
        },
        item_index=0,
        item_identifier="request-1",
        source=build_source()
    )

    assert result == captured
    assert captured["identifier"] == "article-1"
    assert captured["source"] == "GNews"
    assert captured["language"] == "fr"
    assert captured["category"] == "technology"
    assert captured["url"] == "https://example.com/article"
    assert captured["image_url"] == "https://example.com/image.jpg"


def test_build_gnews_article_uses_requested_fallbacks(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_gnews_article(
        item={
            "id": "article-1",
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


def test_build_gnews_article_removes_invalid_urls(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_gnews_article(
        item={
            "id": "article-1",
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
                "resultat_gnews_invalide"
            )
        ),
        (
            {},
            (
                False,
                "identifiant_gnews_absent"
            )
        ),
        (
            {
                "id": "article-1",
                "url": "invalid"
            },
            (
                False,
                "url_gnews_invalide"
            )
        ),
        (
            {
                "id": "article-1"
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
def test_validate_gnews_item(
    item: Any,
    expected: tuple[bool, str]
) -> None:
    assert module.validate_gnews_item(
        item=item,
        filters={},
        source={}
    ) == expected


# API publique

def test_load_gnews_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        type(module.GNEWS_EXTRACTOR),
        "reload_source",
        lambda self: {
            "source_id": "gnews"
        }
    )

    assert module.load_gnews_source() == {
        "source_id": "gnews"
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
    assert captured["adapter"] is module.GNEWS_ADAPTER


def test_extract_all_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()

    monkeypatch.setattr(
        type(module.GNEWS_EXTRACTOR),
        "run",
        lambda self: expected
    )

    assert module.extract_all_articles() is expected