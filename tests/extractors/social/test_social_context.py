"""Tests de la configuration et du contexte des extracteurs sociaux."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from src.extractors.social import social_context as module
from src.extractors.social.social_adapter import SocialAdapter


# Fonctions simulées

def fake_iter_items(
    source: Mapping[str, Any],
    maximum_items: int
) -> Iterable[Any]:
    del source, maximum_items
    return []


def fake_build_article(
    item: Any,
    identifier: str,
    context: Mapping[str, Any],
    source: Mapping[str, Any]
) -> dict[str, Any]:
    del item, identifier, context, source
    return {}


def build_adapter() -> SocialAdapter:
    """Construit un adaptateur social minimal valide."""

    return SocialAdapter(
        source_id="reddit",
        default_name="Reddit",
        iter_items=fake_iter_items,
        build_article=fake_build_article
    )


def build_context(
    source: dict[str, Any] | None = None,
    maximum_articles: int = 10,
    max_article_age_days: int = 30,
    filters: dict[str, Any] | None = None,
    remove_duplicates: bool = True
) -> module.SocialExtractionContext:
    """Construit un contexte social minimal."""

    return module.SocialExtractionContext(
        source=source or {},
        maximum_articles=maximum_articles,
        max_article_age_days=max_article_age_days,
        filters=filters or {},
        remove_duplicates=remove_duplicates
    )


# Contexte

def test_social_extraction_context_uses_empty_collections_by_default() -> None:
    context = build_context()

    assert context.articles == []
    assert context.seen_keys == set()
    assert context.rejection_stats == Counter()
    assert context.processed_count == 0


def test_social_extraction_context_defaults_are_independent() -> None:
    first = build_context()
    second = build_context()

    first.articles.append({"title": "Article"})
    first.seen_keys.add("key")
    first.rejection_stats["invalid"] += 1

    assert second.articles == []
    assert second.seen_keys == set()
    assert second.rejection_stats == Counter()


def test_source_name_returns_normalized_name() -> None:
    context = build_context(
        source={
            "name": "  Reddit France  "
        }
    )

    assert context.source_name == "Reddit France"


@pytest.mark.parametrize(
    "source",
    [
        {},
        {"name": ""},
        {"name": "   "},
        {"name": None}
    ]
)
def test_source_name_uses_default_value(
    source: dict[str, Any]
) -> None:
    context = build_context(source=source)

    assert context.source_name == "source sociale"


def test_source_id_returns_normalized_identifier() -> None:
    context = build_context(
        source={
            "source_id": "  reddit  "
        }
    )

    assert context.source_id == "reddit"


@pytest.mark.parametrize(
    "source",
    [
        {},
        {"source_id": ""},
        {"source_id": "   "},
        {"source_id": None}
    ]
)
def test_source_id_uses_default_value(
    source: dict[str, Any]
) -> None:
    context = build_context(source=source)

    assert context.source_id == "social"


def test_source_type_returns_social_constant() -> None:
    context = build_context()

    assert context.source_type == module.SOURCE_TYPE_SOCIAL


@pytest.mark.parametrize(
    ("article_count", "maximum_articles", "expected"),
    [
        (0, 1, False),
        (1, 1, True),
        (2, 1, True),
        (2, 3, False)
    ]
)
def test_completed_depends_on_article_limit(
    article_count: int,
    maximum_articles: int,
    expected: bool
) -> None:
    context = build_context(maximum_articles=maximum_articles)
    context.articles.extend(
        {"title": f"Article {index}"}
        for index in range(article_count)
    )

    assert context.completed is expected


def test_rejected_count_returns_total_rejections() -> None:
    context = build_context()
    context.rejection_stats.update(
        {
            "date_invalide": 2,
            "doublon": 3
        }
    )

    assert context.rejected_count == 5


@pytest.mark.parametrize(
    ("reason", "expected_reason"),
    [
        ("  date_invalide  ", "date_invalide"),
        ("", "article_invalide"),
        ("   ", "article_invalide"),
        (None, "article_invalide")
    ]
)
def test_reject_records_normalized_reason(
    reason: Any,
    expected_reason: str
) -> None:
    context = build_context()

    context.reject(reason)
    context.reject(reason)

    assert context.rejection_stats[expected_reason] == 2
    assert context.rejected_count == 2


def test_add_article_appends_article() -> None:
    context = build_context()
    article = {
        "title": "Publication sociale"
    }

    context.add_article(article)

    assert context.articles == [article]
    assert context.articles[0] is article


def test_social_extraction_context_rejects_unknown_attributes() -> None:
    context = build_context()

    with pytest.raises(AttributeError):
        context.unknown_attribute = "value"


# Normalisation

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("reddit,mastodon", ["reddit", "mastodon"]),
        (" reddit , mastodon ", ["reddit", "mastodon"]),
        (["reddit", "mastodon"], ["reddit", "mastodon"]),
        (("reddit", "mastodon"), ["reddit", "mastodon"]),
        ({"reddit", "mastodon"}, ["reddit", "mastodon"])
    ]
)
def test_normalize_string_list_accepts_supported_collections(
    value: Any,
    expected: list[str]
) -> None:
    result = module.normalize_string_list(value)

    if isinstance(value, set):
        assert set(result) == set(expected)
    else:
        assert result == expected


def test_normalize_string_list_removes_empty_and_duplicate_values() -> None:
    result = module.normalize_string_list(
        [
            " reddit ",
            "",
            None,
            "reddit",
            "mastodon",
            "  "
        ]
    )

    assert result == [
        "reddit",
        "mastodon"
    ]


@pytest.mark.parametrize(
    "value",
    [
        None,
        42,
        3.14,
        {},
        object()
    ]
)
def test_normalize_string_list_rejects_unsupported_values(
    value: Any
) -> None:
    assert module.normalize_string_list(value) == []


# Paramètres

def test_get_social_max_articles_returns_configured_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "MAX_ARTICLES_PER_SOURCE", 100)

    result = module.get_social_max_articles(
        {
            "max_articles": 25
        }
    )

    assert result == 25


def test_get_social_max_articles_caps_configured_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "MAX_ARTICLES_PER_SOURCE", 100)

    result = module.get_social_max_articles(
        {
            "max_articles": 250
        }
    )

    assert result == 100


def test_get_social_max_articles_uses_global_default(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "MAX_ARTICLES_PER_SOURCE", 75)

    result = module.get_social_max_articles({})

    assert result == 75


def test_get_social_max_articles_uses_parser_default(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    received: list[tuple[Any, int]] = []

    def fake_parse_non_negative_integer(
        value: Any,
        default: int
    ) -> int:
        received.append((value, default))
        return default

    monkeypatch.setattr(module, "MAX_ARTICLES_PER_SOURCE", 50)
    monkeypatch.setattr(
        module,
        "parse_non_negative_integer",
        fake_parse_non_negative_integer
    )

    result = module.get_social_max_articles(
        {
            "max_articles": "invalid"
        }
    )

    assert result == 50
    assert received == [
        ("invalid", 50)
    ]


def test_get_max_article_age_days_returns_configured_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "MAX_ARTICLE_AGE_DAYS", 90)

    result = module.get_max_article_age_days(
        {
            "max_article_age_days": 30
        }
    )

    assert result == 30


def test_get_max_article_age_days_caps_configured_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "MAX_ARTICLE_AGE_DAYS", 90)

    result = module.get_max_article_age_days(
        {
            "max_article_age_days": 120
        }
    )

    assert result == 90


def test_get_max_article_age_days_uses_global_limit_when_configured_zero(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "MAX_ARTICLE_AGE_DAYS", 90)

    result = module.get_max_article_age_days(
        {
            "max_article_age_days": 0
        }
    )

    assert result == 90


def test_get_max_article_age_days_allows_unlimited_global_setting(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "MAX_ARTICLE_AGE_DAYS", 0)

    result = module.get_max_article_age_days(
        {
            "max_article_age_days": 45
        }
    )

    assert result == 45


# Validation des dates

@pytest.mark.parametrize(
    "published_at",
    [
        None,
        "",
        "   "
    ]
)
def test_validate_article_age_accepts_missing_date(
    published_at: Any
) -> None:
    result = module.validate_article_age(
        {
            "published_at": published_at
        },
        max_article_age_days=30
    )

    assert result == (True, "")


def test_validate_article_age_rejects_invalid_date(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "parse_datetime",
        lambda value: None
    )

    result = module.validate_article_age(
        {
            "published_at": "invalid"
        },
        max_article_age_days=30
    )

    assert result == (
        False,
        "date_publication_invalide"
    )


def test_validate_article_age_rejects_date_too_far_in_future(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime(
        2026,
        7,
        28,
        12,
        0,
        tzinfo=timezone.utc
    )
    article_date = now + timedelta(minutes=6)

    monkeypatch.setattr(
        module,
        "parse_datetime",
        lambda value: article_date
    )
    monkeypatch.setattr(
        module,
        "get_current_datetime",
        lambda: now
    )

    result = module.validate_article_age(
        {
            "published_at": "2026-07-28T12:06:00+00:00"
        },
        max_article_age_days=30
    )

    assert result == (
        False,
        "date_publication_future"
    )


def test_validate_article_age_accepts_future_date_within_tolerance(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime(
        2026,
        7,
        28,
        12,
        0,
        tzinfo=timezone.utc
    )
    article_date = now + timedelta(minutes=5)

    monkeypatch.setattr(
        module,
        "parse_datetime",
        lambda value: article_date
    )
    monkeypatch.setattr(
        module,
        "get_current_datetime",
        lambda: now
    )

    result = module.validate_article_age(
        {
            "published_at": "2026-07-28T12:05:00+00:00"
        },
        max_article_age_days=30
    )

    assert result == (True, "")


def test_validate_article_age_rejects_old_article(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime(
        2026,
        7,
        28,
        12,
        0,
        tzinfo=timezone.utc
    )
    article_date = now - timedelta(days=31)

    monkeypatch.setattr(
        module,
        "parse_datetime",
        lambda value: article_date
    )
    monkeypatch.setattr(
        module,
        "get_current_datetime",
        lambda: now
    )

    result = module.validate_article_age(
        {
            "published_at": "2026-06-27T12:00:00+00:00"
        },
        max_article_age_days=30
    )

    assert result == (
        False,
        "article_trop_ancien"
    )


def test_validate_article_age_accepts_article_on_age_boundary(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime(
        2026,
        7,
        28,
        12,
        0,
        tzinfo=timezone.utc
    )
    article_date = now - timedelta(days=30)

    monkeypatch.setattr(
        module,
        "parse_datetime",
        lambda value: article_date
    )
    monkeypatch.setattr(
        module,
        "get_current_datetime",
        lambda: now
    )

    result = module.validate_article_age(
        {
            "published_at": "2026-06-28T12:00:00+00:00"
        },
        max_article_age_days=30
    )

    assert result == (True, "")


def test_validate_article_age_disables_age_limit_when_zero(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime(
        2026,
        7,
        28,
        12,
        0,
        tzinfo=timezone.utc
    )
    article_date = now - timedelta(days=3650)

    monkeypatch.setattr(
        module,
        "parse_datetime",
        lambda value: article_date
    )
    monkeypatch.setattr(
        module,
        "get_current_datetime",
        lambda: now
    )

    result = module.validate_article_age(
        {
            "published_at": "2016-07-30T12:00:00+00:00"
        },
        max_article_age_days=0
    )

    assert result == (True, "")


# Création du contexte

def test_create_extraction_context_rejects_invalid_adapter() -> None:
    with pytest.raises(
        TypeError,
        match="adapter doit être une instance de SocialAdapter"
    ):
        module.create_extraction_context(
            {
                "enabled": True
            },
            object()
        )


@pytest.mark.parametrize(
    "source",
    [
        None,
        [],
        "invalid",
        42
    ]
)
def test_create_extraction_context_rejects_invalid_source(
    source: Any,
    caplog: pytest.LogCaptureFixture
) -> None:
    adapter = build_adapter()

    result = module.create_extraction_context(
        source,
        adapter
    )

    assert result is None
    assert "Configuration Reddit invalide" in caplog.text


def test_create_extraction_context_uses_adapter_fallback_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = build_adapter()

    monkeypatch.setattr(
        module,
        "get_social_max_articles",
        lambda source: 10
    )
    monkeypatch.setattr(
        module,
        "get_filter_configuration",
        lambda source: {
            "remove_duplicates": True
        }
    )
    monkeypatch.setattr(
        module,
        "get_max_article_age_days",
        lambda source: 30
    )

    source = {
        "enabled": True,
        "source_id": "   ",
        "name": ""
    }

    result = module.create_extraction_context(
        source,
        adapter
    )

    assert result is not None
    assert result.source["source_id"] == "reddit"
    assert result.source["name"] == "Reddit"


def test_create_extraction_context_does_not_modify_original_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = build_adapter()
    source = {
        "enabled": True
    }

    monkeypatch.setattr(
        module,
        "get_social_max_articles",
        lambda current_source: 10
    )
    monkeypatch.setattr(
        module,
        "get_filter_configuration",
        lambda current_source: {}
    )
    monkeypatch.setattr(
        module,
        "get_max_article_age_days",
        lambda current_source: 30
    )

    result = module.create_extraction_context(
        source,
        adapter
    )

    assert result is not None
    assert source == {
        "enabled": True
    }
    assert result.source is not source


@pytest.mark.parametrize(
    "enabled",
    [
        False,
        None,
        "",
        "false",
        "0"
    ]
)
def test_create_extraction_context_ignores_disabled_source(
    enabled: Any
) -> None:
    result = module.create_extraction_context(
        {
            "enabled": enabled
        },
        build_adapter()
    )

    assert result is None


def test_create_extraction_context_ignores_zero_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_social_max_articles",
        lambda source: 0
    )

    result = module.create_extraction_context(
        {
            "enabled": True
        },
        build_adapter()
    )

    assert result is None


@pytest.mark.parametrize(
    "filters",
    [
        None,
        [],
        "invalid",
        42
    ]
)
def test_create_extraction_context_rejects_invalid_filters(
    filters: Any,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_social_max_articles",
        lambda source: 10
    )
    monkeypatch.setattr(
        module,
        "get_filter_configuration",
        lambda source: filters
    )

    result = module.create_extraction_context(
        {
            "enabled": True
        },
        build_adapter()
    )

    assert result is None


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        (True, True),
        (False, False),
        ("true", True),
        ("false", False),
        (None, True)
    ]
)
def test_create_extraction_context_normalizes_remove_duplicates(
    configured: Any,
    expected: bool,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_social_max_articles",
        lambda source: 12
    )
    monkeypatch.setattr(
        module,
        "get_filter_configuration",
        lambda source: {
            "remove_duplicates": configured
        }
    )
    monkeypatch.setattr(
        module,
        "get_max_article_age_days",
        lambda source: 45
    )

    result = module.create_extraction_context(
        {
            "enabled": True
        },
        build_adapter()
    )

    assert result is not None
    assert result.maximum_articles == 12
    assert result.max_article_age_days == 45
    assert result.filters == {
        "remove_duplicates": configured
    }
    assert result.remove_duplicates is expected


def test_create_extraction_context_returns_complete_context(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    source = {
        "enabled": True,
        "source_id": "custom_social",
        "name": "Custom Social"
    }
    filters = {
        "remove_duplicates": False,
        "require_title": True
    }

    monkeypatch.setattr(
        module,
        "get_social_max_articles",
        lambda current_source: 25
    )
    monkeypatch.setattr(
        module,
        "get_filter_configuration",
        lambda current_source: filters
    )
    monkeypatch.setattr(
        module,
        "get_max_article_age_days",
        lambda current_source: 15
    )

    result = module.create_extraction_context(
        source,
        build_adapter()
    )

    assert result is not None
    assert result.source == source
    assert result.source is not source
    assert result.maximum_articles == 25
    assert result.max_article_age_days == 15
    assert result.filters == filters
    assert result.filters is not filters
    assert result.remove_duplicates is False
    assert result.articles == []
    assert result.seen_keys == set()
    assert result.rejection_stats == Counter()
    assert result.processed_count == 0