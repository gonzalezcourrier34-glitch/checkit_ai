"""Tests légers de l'extracteur Google Fact Check Tools."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

import src.extractors.apis.source.google_fact_check_extractor as module
from src.extractors.apis.api_extractor import ApiRequestError


# Configuration

def build_source(**overrides: Any) -> dict[str, Any]:
    """Construit une configuration Google Fact Check minimale."""

    source = {
        "source_id": "google_fact_check",
        "name": "Google Fact Check Tools",
        "endpoint": (
            "https://factchecktools.googleapis.com/"
            "v1alpha1/claims:search"
        ),
        "role": "fact_check_reference",
        "category": "fact_check",
        "max_articles": 10,
        "max_article_age_days": 30,
        "page_size": 100,
        "max_pages": 5
    }
    source.update(overrides)
    return source


def build_item(**overrides: Any) -> dict[str, Any]:
    """Construit un élément Google Fact Check minimal."""

    item = {
        "_claim": {
            "text": "Une affirmation à vérifier",
            "claimant": "Auteur de l'affirmation",
            "claimDate": "2026-07-01T00:00:00Z"
        },
        "_review": {
            "publisher": {
                "name": "Fact Checker"
            },
            "url": "https://example.com/fact-check",
            "title": "Vérification de l'affirmation",
            "textualRating": "Faux",
            "languageCode": "fr",
            "reviewDate": "2026-07-02T00:00:00Z"
        },
        "_requested_query": "climat",
        "_requested_language": "fr"
    }
    item.update(overrides)
    return item


# Requêtes configurées

def test_get_configured_queries_returns_structured_queries(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = [
        {
            "queries": [
                "climat"
            ],
            "languages": [
                "fr"
            ]
        }
    ]

    monkeypatch.setattr(
        module,
        "get_queries_configuration",
        lambda source: expected
    )

    assert module.get_configured_queries({}) == expected


def test_get_configured_queries_uses_source_fallback(
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

    assert module.get_configured_queries(source) == [
        source
    ]


def test_merge_google_fact_check_query_excludes_queries() -> None:
    source = {
        "language": "fr",
        "category": "fact_check",
        "queries": [
            {
                "language": "en"
            }
        ]
    }
    query = {
        "language": "en",
        "query": "climat"
    }

    assert module.merge_google_fact_check_query(
        source,
        query
    ) == {
        "language": "en",
        "category": "fact_check",
        "query": "climat"
    }


# Recherches et langues

def test_get_queries_normalizes_and_removes_duplicates(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_keywords",
        lambda source: [
            " changement climatique ",
            "élections",
            "changement climatique",
            ""
        ]
    )

    assert module.get_queries({}) == [
        "changement climatique",
        "élections"
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
    assert len(result[0]) == module.GOOGLE_FACT_CHECK_MAX_QUERY_LENGTH


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("fr", "fr"),
        ("FR", "fr"),
        ("fr_FR", "fr-FR"),
        ("en-us", "en-US"),
        ("zh_hans_cn", "zh-Hans-CN"),
        ("", ""),
        (None, "")
    ]
)
def test_normalize_language_code(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_language_code(value) == expected


def test_get_languages_normalizes_and_removes_duplicates(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_query_configuration_values",
        lambda *args, **kwargs: [
            "fr",
            "EN_us",
            "fr",
            ""
        ]
    )

    assert module.get_languages({}) == [
        "fr",
        "en-US"
    ]


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
    ) == module.GOOGLE_FACT_CHECK_MAX_PAGE_SIZE


def test_get_max_pages_respects_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_pagination_value",
        lambda *args, **kwargs: 1000
    )

    assert module.get_max_pages({}) == module.GOOGLE_FACT_CHECK_MAX_PAGES


# Paramètres HTTP

def test_build_google_fact_check_request_params(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 30
    )

    result = module.build_google_fact_check_request_params(
        source=build_source(
            publisher_site="example.com"
        ),
        query=" changement climatique ",
        language="FR_fr",
        page_size=50,
        page_token="token-2"
    )

    assert result == {
        "pageSize": 50,
        "maxAgeDays": 30,
        "query": "changement climatique",
        "languageCode": "fr-FR",
        "pageToken": "token-2",
        "reviewPublisherSiteFilter": "example.com"
    }


def test_build_google_fact_check_request_params_excludes_empty_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 30
    )

    result = module.build_google_fact_check_request_params(
        source=build_source(),
        query="",
        language="",
        page_size=100,
        page_token=""
    )

    assert result == {
        "pageSize": 100,
        "maxAgeDays": 30
    }


def test_build_google_fact_check_request_params_respects_limits(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_api_max_article_age_days",
        lambda source: 0
    )

    result = module.build_google_fact_check_request_params(
        source=build_source(),
        query="a" * 600,
        language="",
        page_size=500
    )

    assert result["pageSize"] == module.GOOGLE_FACT_CHECK_MAX_PAGE_SIZE
    assert result["maxAgeDays"] == 1
    assert len(result["query"]) == module.GOOGLE_FACT_CHECK_MAX_QUERY_LENGTH


# Réseau

def test_fetch_google_fact_check_page_delegates_to_fetch_json_object(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_fetch_json_object(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {
            "claims": []
        }

    monkeypatch.setattr(
        module,
        "fetch_json_object",
        fake_fetch_json_object
    )

    result = module.fetch_google_fact_check_page(
        endpoint="https://example.com/api",
        params={
            "query": "climat"
        },
        api_key="secret"
    )

    assert result == {
        "claims": []
    }
    assert captured == {
        "url": "https://example.com/api",
        "params": {
            "query": "climat",
            "key": "secret"
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
def test_get_google_error_message(
    data: Mapping[str, Any],
    expected: str
) -> None:
    assert module.get_google_error_message(data) == expected


# Récupération d'une page

def test_request_google_fact_check_page_rejects_invalid_endpoint() -> None:
    with pytest.raises(
        ValueError,
        match="Endpoint Google Fact Check absent ou invalide"
    ):
        module.request_google_fact_check_page(
            source=build_source(
                endpoint="invalid"
            ),
            query="climat",
            language="fr",
            page_size=100,
            api_key="secret"
        )


def test_request_google_fact_check_page_requires_query_or_publisher() -> None:
    with pytest.raises(
        ValueError,
        match="exige une requête ou un filtre d'éditeur"
    ):
        module.request_google_fact_check_page(
            source=build_source(),
            query="",
            language="fr",
            page_size=100,
            api_key="secret"
        )


def test_request_google_fact_check_page_accepts_publisher_filter(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "fetch_google_fact_check_page",
        lambda **kwargs: {
            "claims": [],
            "nextPageToken": ""
        }
    )

    claims, token = module.request_google_fact_check_page(
        source=build_source(
            publisher_site="example.com"
        ),
        query="",
        language="fr",
        page_size=100,
        api_key="secret"
    )

    assert claims == []
    assert token == ""


def test_request_google_fact_check_page_returns_claims_and_token(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "fetch_google_fact_check_page",
        lambda **kwargs: {
            "claims": [
                {
                    "text": "Claim 1"
                },
                "invalid",
                {
                    "text": "Claim 2"
                }
            ],
            "nextPageToken": "token-2"
        }
    )

    claims, token = module.request_google_fact_check_page(
        source=build_source(),
        query="climat",
        language="fr",
        page_size=100,
        api_key="secret"
    )

    assert claims == [
        {
            "text": "Claim 1"
        },
        {
            "text": "Claim 2"
        }
    ]
    assert token == "token-2"


def test_request_google_fact_check_page_raises_request_error(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "fetch_google_fact_check_page",
        lambda **kwargs: {
            "error": {
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
        module.request_google_fact_check_page(
            source=build_source(),
            query="climat",
            language="fr",
            page_size=100,
            api_key="secret"
        )


# Claims et reviews

def test_get_claim_reviews_keeps_mapping_values() -> None:
    claim = {
        "claimReview": [
            {
                "url": "https://example.com/review-1"
            },
            "invalid",
            {
                "url": "https://example.com/review-2"
            }
        ]
    }

    assert module.get_claim_reviews(claim) == [
        {
            "url": "https://example.com/review-1"
        },
        {
            "url": "https://example.com/review-2"
        }
    ]


def test_get_claim_reviews_rejects_invalid_collection() -> None:
    assert module.get_claim_reviews({
        "claimReview": "invalid"
    }) == []


def test_get_review_publisher_returns_mapping() -> None:
    review = {
        "publisher": {
            "name": "Fact Checker"
        }
    }

    assert module.get_review_publisher(review) == {
        "name": "Fact Checker"
    }


def test_get_review_publisher_rejects_invalid_value() -> None:
    assert module.get_review_publisher({
        "publisher": "invalid"
    }) == {}


# Pagination de plusieurs pages

def test_request_google_fact_check_claims_returns_empty_for_zero_maximum() -> None:
    assert module.request_google_fact_check_claims(
        source=build_source(),
        query="climat",
        language="fr",
        max_reviews=0,
        api_key="secret"
    ) == []


def test_request_google_fact_check_claims_collects_reviews(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 5
    )
    monkeypatch.setattr(
        module,
        "get_page_size",
        lambda source, remaining_articles: remaining_articles
    )
    monkeypatch.setattr(
        module,
        "request_google_fact_check_page",
        lambda **kwargs: (
            [
                {
                    "text": "Claim 1",
                    "claimReview": [
                        {
                            "url": "https://example.com/review-1"
                        },
                        {
                            "url": "https://example.com/review-2"
                        }
                    ]
                }
            ],
            ""
        )
    )

    result = module.request_google_fact_check_claims(
        source=build_source(),
        query="climat",
        language="fr",
        max_reviews=2,
        api_key="secret"
    )

    assert len(result) == 1
    assert len(module.get_claim_reviews(result[0])) == 2


def test_request_google_fact_check_claims_ignores_claim_without_review(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_max_pages",
        lambda source: 1
    )
    monkeypatch.setattr(
        module,
        "request_google_fact_check_page",
        lambda **kwargs: (
            [
                {
                    "text": "Claim sans review"
                }
            ],
            ""
        )
    )

    assert module.request_google_fact_check_claims(
        source=build_source(),
        query="climat",
        language="fr",
        max_reviews=5,
        api_key="secret"
    ) == []


def test_request_google_fact_check_claims_stops_on_repeated_token(
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
        lambda source, remaining_articles: remaining_articles
    )

    def fake_request_page(**kwargs: Any) -> tuple[list[dict[str, Any]], str]:
        nonlocal calls
        calls += 1

        return (
            [
                {
                    "text": f"Claim {calls}",
                    "claimReview": [
                        {
                            "url": f"https://example.com/review-{calls}"
                        }
                    ]
                }
            ],
            "same-token"
        )

    monkeypatch.setattr(
        module,
        "request_google_fact_check_page",
        fake_request_page
    )

    result = module.request_google_fact_check_claims(
        source=build_source(),
        query="climat",
        language="fr",
        max_reviews=10,
        api_key="secret"
    )

    assert len(result) == 2
    assert calls == 2


# Parcours

def test_iter_google_fact_check_items_returns_nothing_for_zero() -> None:
    assert list(
        module.iter_google_fact_check_items(
            build_source(),
            0
        )
    ) == []


def test_iter_google_fact_check_items_requires_query_or_publisher(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_google_fact_check_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "get_configured_queries",
        lambda source: [
            {}
        ]
    )

    with pytest.raises(
        ValueError,
        match="exige au moins une requête"
    ):
        list(
            module.iter_google_fact_check_items(
                build_source(),
                10
            )
        )


def test_iter_google_fact_check_items_enriches_reviews(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "validate_google_fact_check_authentication",
        lambda: "secret"
    )
    monkeypatch.setattr(
        module,
        "get_configured_queries",
        lambda source: [
            {
                "query": "climat",
                "language": "fr"
            }
        ]
    )
    monkeypatch.setattr(
        module,
        "request_google_fact_check_claims",
        lambda **kwargs: [
            {
                "text": "Claim",
                "claimReview": [
                    {
                        "url": "https://example.com/review-1"
                    },
                    {
                        "url": "https://example.com/review-2"
                    }
                ]
            }
        ]
    )

    result = list(
        module.iter_google_fact_check_items(
            build_source(),
            2
        )
    )

    assert result == [
        (
            "query=climat|language=fr|claim=0",
            0,
            {
                "_claim": {
                    "text": "Claim",
                    "claimReview": [
                        {
                            "url": "https://example.com/review-1"
                        },
                        {
                            "url": "https://example.com/review-2"
                        }
                    ]
                },
                "_review": {
                    "url": "https://example.com/review-1"
                },
                "_requested_query": "climat",
                "_requested_language": "fr"
            }
        ),
        (
            "query=climat|language=fr|claim=0",
            1,
            {
                "_claim": {
                    "text": "Claim",
                    "claimReview": [
                        {
                            "url": "https://example.com/review-1"
                        },
                        {
                            "url": "https://example.com/review-2"
                        }
                    ]
                },
                "_review": {
                    "url": "https://example.com/review-2"
                },
                "_requested_query": "climat",
                "_requested_language": "fr"
            }
        )
    ]


# Lecture des éléments

def test_get_claim_data_returns_mapping() -> None:
    claim = {
        "text": "Claim"
    }

    assert module.get_claim_data({
        "_claim": claim
    }) == claim


def test_get_review_data_returns_mapping() -> None:
    review = {
        "title": "Review"
    }

    assert module.get_review_data({
        "_review": review
    }) == review


def test_get_claim_title() -> None:
    assert module.get_claim_title(build_item()) == (
        "Une affirmation à vérifier"
    )


def test_get_review_text_includes_rating_and_review_title() -> None:
    assert module.get_review_text(build_item()) == (
        "Évaluation : Faux | "
        "Vérification : Vérification de l'affirmation"
    )


def test_get_review_text_avoids_duplicate_claim_title() -> None:
    item = build_item()
    item["_review"]["title"] = "Une affirmation à vérifier"

    assert module.get_review_text(item) == "Évaluation : Faux"


def test_get_review_url_returns_valid_url() -> None:
    assert module.get_review_url(build_item()) == (
        "https://example.com/fact-check"
    )


def test_get_review_url_rejects_invalid_url() -> None:
    item = build_item()
    item["_review"]["url"] = "invalid"

    assert module.get_review_url(item) == ""


def test_get_review_publisher_name() -> None:
    assert module.get_review_publisher_name(build_item()) == "Fact Checker"


def test_get_review_language_prefers_review_language() -> None:
    assert module.get_review_language(build_item()) == "fr"


def test_get_review_language_uses_requested_fallback() -> None:
    item = build_item()
    item["_review"]["languageCode"] = ""
    item["_requested_language"] = "en_us"

    assert module.get_review_language(item) == "en-US"


def test_get_review_published_at_prefers_review_date() -> None:
    assert module.get_review_published_at(build_item()) == (
        "2026-07-02T00:00:00Z"
    )


def test_get_review_published_at_uses_claim_date_fallback() -> None:
    item = build_item()
    item["_review"]["reviewDate"] = ""

    assert module.get_review_published_at(item) == (
        "2026-07-01T00:00:00Z"
    )


def test_build_identifier_prefers_review_url() -> None:
    assert module.build_google_fact_check_identifier(
        build_item(),
        "item-1"
    ) == "https://example.com/fact-check"


def test_build_identifier_uses_generated_fallback() -> None:
    item = build_item()
    item["_review"]["url"] = ""

    result = module.build_google_fact_check_identifier(
        item,
        "item-1"
    )

    assert result.startswith("google_fact_check:item-1:")
    assert "Fact Checker" in result
    assert "Une affirmation à vérifier" in result


# Construction de l'article

def test_build_google_fact_check_article_rejects_invalid_item() -> None:
    assert module.build_google_fact_check_article(
        item="invalid",
        item_index=0,
        item_identifier="item-0",
        source=build_source()
    ) == {}


def test_build_google_fact_check_article_builds_standard_article(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    class FakeLabelResult:
        label = "fake"
        raw_value = "Faux"
        normalized_value = "faux"
        reason = "exact_match"
        matched_value = "faux"

    monkeypatch.setattr(
        module,
        "classify_fact_check_label",
        lambda value: FakeLabelResult()
    )

    def fake_build_standard_article(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return dict(kwargs)

    monkeypatch.setattr(
        module,
        "build_standard_article",
        fake_build_standard_article
    )
    monkeypatch.setattr(
        module,
        "convert_date_to_iso",
        lambda value: f"iso:{value}" if value else ""
    )

    result = module.build_google_fact_check_article(
        item=build_item(),
        item_index=0,
        item_identifier="item-1",
        source=build_source()
    )

    assert captured["identifier"] == "https://example.com/fact-check"
    assert captured["source"] == "Fact Checker"
    assert captured["title"] == "Une affirmation à vérifier"
    assert captured["author"] == "Auteur de l'affirmation"
    assert captured["language"] == "fr"
    assert captured["category"] == "climat"
    assert captured["label"] == "fake"
    assert captured["dataset_role"] == "fact_check_reference"

    assert result["claimant"] == "Auteur de l'affirmation"
    assert result["fact_check_rating"] == "Faux"
    assert result["fact_check_rating_normalized"] == "faux"
    assert result["fact_check_label_reason"] == "exact_match"
    assert result["fact_check_label_match"] == "faux"
    assert result["fact_check_publisher"] == "Fact Checker"
    assert result["claim_date"] == "iso:2026-07-01T00:00:00Z"
    assert result["review_date"] == "iso:2026-07-02T00:00:00Z"


def test_build_google_fact_check_article_uses_source_fallback(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    class FakeLabelResult:
        label = "real"
        raw_value = "Vrai"
        normalized_value = "vrai"
        reason = "exact_match"
        matched_value = "vrai"

    item = build_item()
    item["_review"]["publisher"] = {}
    item["_requested_query"] = ""

    monkeypatch.setattr(
        module,
        "classify_fact_check_label",
        lambda value: FakeLabelResult()
    )
    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: captured.update(kwargs) or dict(kwargs)
    )

    module.build_google_fact_check_article(
        item=item,
        item_index=0,
        item_identifier="item-1",
        source=build_source(
            name="Google Fact Check",
            category="politics"
        )
    )

    assert captured["source"] == "Google Fact Check"
    assert captured["category"] == "politics"


# Validation

@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (
            None,
            (
                False,
                "resultat_google_fact_check_invalide"
            )
        ),
        (
            {
                "_claim": {},
                "_review": {}
            },
            (
                False,
                "affirmation_absente"
            )
        ),
        (
            {
                "_claim": {
                    "text": "Affirmation"
                },
                "_review": {}
            },
            (
                False,
                "verification_absente"
            )
        ),
        (
            {
                "_claim": {
                    "text": "Affirmation"
                },
                "_review": {
                    "title": "Vérification",
                    "url": "invalid"
                }
            },
            (
                False,
                "url_verification_invalide"
            )
        ),
        (
            {
                "_claim": {
                    "text": "Affirmation"
                },
                "_review": {
                    "url": "https://example.com/review"
                }
            },
            (
                False,
                "evaluation_absente"
            )
        ),
        (
            {
                "_claim": {
                    "text": "Affirmation"
                },
                "_review": {
                    "url": "https://example.com/review",
                    "textualRating": "Faux"
                }
            },
            (
                True,
                ""
            )
        )
    ]
)
def test_validate_google_fact_check_item(
    item: Any,
    expected: tuple[bool, str]
) -> None:
    assert module.validate_google_fact_check_item(
        item=item,
        filters={},
        source={}
    ) == expected


# API publique

def test_load_google_fact_check_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        type(module.GOOGLE_FACT_CHECK_EXTRACTOR),
        "reload_source",
        lambda self: {
            "source_id": "google_fact_check"
        }
    )

    assert module.load_google_fact_check_source() == {
        "source_id": "google_fact_check"
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
    assert captured["adapter"] is module.GOOGLE_FACT_CHECK_ADAPTER


def test_extract_all_articles(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()

    monkeypatch.setattr(
        type(module.GOOGLE_FACT_CHECK_EXTRACTOR),
        "run",
        lambda self: expected
    )

    assert module.extract_all_articles() is expected