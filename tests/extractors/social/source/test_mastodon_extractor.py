"""Tests de l'adaptateur Mastodon."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import pytest
import requests
from requests import Response

from src.extractors.social.social_adapter import SocialItem
from src.extractors.social.source import mastodon_extractor as module


# Doubles de test

class FakeResponse:
    """Simule une réponse HTTP Mastodon."""

    def __init__(
        self,
        payload: Any = None,
        links: dict[str, Any] | None = None,
        status_code: int = 200,
        json_error: Exception | None = None
    ) -> None:
        self.payload = payload
        self.links = links or {}
        self.status_code = status_code
        self.json_error = json_error
        self.raise_calls = 0

    def json(self) -> Any:
        if self.json_error is not None:
            raise self.json_error

        return self.payload

    def raise_for_status(self) -> None:
        self.raise_calls += 1


class FakeSession:
    """Simule une session HTTP."""

    def __init__(
        self,
        response: Any = None,
        error: Exception | None = None
    ) -> None:
        self.response = response
        self.error = error
        self.headers: dict[str, str] = {}
        self.get_calls: list[dict[str, Any]] = []
        self.close_calls = 0

    def get(
        self,
        url: str,
        params: Mapping[str, Any],
        timeout: Any
    ) -> Any:
        self.get_calls.append(
            {
                "url": url,
                "params": dict(params),
                "timeout": timeout
            }
        )

        if self.error is not None:
            raise self.error

        return self.response

    def close(self) -> None:
        self.close_calls += 1


class FakeExtractor:
    """Simule l'extracteur Mastodon public."""

    def __init__(
        self,
        source: dict[str, Any] | None = None,
        result: Any = None
    ) -> None:
        self.source = source or {}
        self.result = result
        self.reload_calls = 0
        self.run_calls = 0

    def reload_source(self) -> dict[str, Any]:
        self.reload_calls += 1
        return self.source

    def run(self) -> Any:
        self.run_calls += 1
        return self.result


# Configuration

def test_mastodon_adapter_is_configured() -> None:
    assert module.MASTODON_ADAPTER.source_id == "mastodon"
    assert module.MASTODON_ADAPTER.default_name == "Mastodon"
    assert module.MASTODON_ADAPTER.iter_items is module.iter_mastodon_items
    assert module.MASTODON_ADAPTER.build_article is module.build_mastodon_article
    assert module.MASTODON_ADAPTER.validate_item is module.validate_mastodon_item


def test_mastodon_extractor_uses_adapter_and_sources_file() -> None:
    assert module.MASTODON_EXTRACTOR.adapter is module.MASTODON_ADAPTER
    assert module.MASTODON_EXTRACTOR.section_name == "social_sources"
    assert module.MASTODON_EXTRACTOR.sources_file == module.SOURCES_FILE


# Configuration des sources

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://mastodon.social", "https://mastodon.social"),
        (" https://mastodon.social/ ", "https://mastodon.social"),
        ("http://localhost.example/", "http://localhost.example"),
        ("", ""),
        ("invalid", ""),
        (None, "")
    ]
)
def test_normalize_instance_url(
    value: Any,
    expected: str,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "is_valid_http_url",
        lambda url: url.startswith(("http://", "https://"))
    )

    assert module.normalize_instance_url(value) == expected


def test_get_instances_normalizes_filters_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "normalize_instance_url",
        lambda value: {
            "one": "https://one.example",
            "duplicate": "https://one.example",
            "two": "https://two.example",
            "invalid": ""
        }[value]
    )

    result = module.get_instances(
        {
            "instances": [
                "one",
                "duplicate",
                "invalid",
                "two"
            ]
        }
    )

    assert result == [
        "https://one.example",
        "https://two.example"
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("#factcheck", "factcheck"),
        ("  ##News  ", "News"),
        ("", ""),
        ("###", ""),
        (None, "")
    ]
)
def test_normalize_hashtag(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_hashtag(value) == expected


def test_get_hashtags_normalizes_and_deduplicates() -> None:
    result = module.get_hashtags(
        {
            "hashtags": [
                "#news",
                " news ",
                "#factcheck",
                "",
                "###"
            ]
        }
    )

    assert result == [
        "news",
        "factcheck"
    ]


def test_get_languages_combines_list_and_legacy_value() -> None:
    result = module.get_languages(
        {
            "languages": [
                "FR",
                "en",
                " fr "
            ],
            "language": "DE"
        }
    )

    assert result == {
        "fr",
        "en",
        "de"
    }


def test_get_languages_returns_empty_set_without_configuration() -> None:
    assert module.get_languages({}) == set()


# Session HTTP

def test_create_mastodon_session_configures_headers(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    session = FakeSession()

    monkeypatch.setattr(
        module.requests,
        "Session",
        lambda: session
    )
    monkeypatch.setattr(
        module,
        "HTTP_HEADERS",
        {
            "User-Agent": "CheckItAI"
        }
    )

    result = module.create_mastodon_session()

    assert result is session
    assert session.headers == {
        "User-Agent": "CheckItAI",
        "Accept": "application/json"
    }


# Nettoyage et titre

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("<p>Bonjour <strong>Mastodon</strong></p>", "Bonjour Mastodon"),
        ("<p>Première phrase.</p><p>Deuxième phrase.</p>", "Première phrase. Deuxième phrase."),
        ("", ""),
        (None, "")
    ]
)
def test_clean_mastodon_html(
    value: Any,
    expected: str
) -> None:
    assert module.clean_mastodon_html(value) == expected


def test_clean_mastodon_html_falls_back_to_clean_text(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "BeautifulSoup",
        lambda *args, **kwargs: (_ for _ in ()).throw(TypeError("invalid"))
    )
    monkeypatch.setattr(
        module,
        "clean_text",
        lambda value: f"clean:{value}"
    )

    assert module.clean_mastodon_html("<p>Test</p>") == "clean:<p>Test</p>"


def test_build_mastodon_title_returns_first_sentence() -> None:
    result = module.build_mastodon_title(
        "Première phrase. Deuxième phrase plus longue."
    )

    assert result == "Première phrase."


def test_build_mastodon_title_returns_empty_string_for_empty_text() -> None:
    assert module.build_mastodon_title("") == ""


def test_build_mastodon_title_truncates_long_title(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "MASTODON_TITLE_MAX_LENGTH",
        20
    )

    result = module.build_mastodon_title(
        "Une publication Mastodon particulièrement longue sans ponctuation"
    )

    assert result == "Une publication…"
    assert len(result) <= 21


def test_build_mastodon_title_truncates_long_word(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "MASTODON_TITLE_MAX_LENGTH",
        10
    )

    result = module.build_mastodon_title(
        "abcdefghijklmno"
    )

    assert result == "abcdefghij…"


# Lecture d'un statut

def test_get_original_status_returns_reblog() -> None:
    original = {
        "id": "original"
    }
    status = {
        "id": "share",
        "reblog": original
    }

    assert module.get_original_status(status) is original


@pytest.mark.parametrize(
    "reblog",
    [
        None,
        "",
        [],
        42
    ]
)
def test_get_original_status_returns_status_without_valid_reblog(
    reblog: Any
) -> None:
    status = {
        "id": "status",
        "reblog": reblog
    }

    assert module.get_original_status(status) is status


def test_get_status_identifier_normalizes_value() -> None:
    assert module.get_status_identifier(
        {
            "id": "  123  "
        }
    ) == "123"


def test_get_status_url_accepts_valid_http_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "is_valid_http_url",
        lambda value: value == "https://mastodon.social/@user/1"
    )

    assert module.get_status_url(
        {
            "url": " https://mastodon.social/@user/1 "
        }
    ) == "https://mastodon.social/@user/1"


def test_get_status_url_rejects_invalid_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "is_valid_http_url",
        lambda value: False
    )

    assert module.get_status_url(
        {
            "url": "invalid"
        }
    ) == ""


@pytest.mark.parametrize(
    ("account", "expected"),
    [
        ({"display_name": " Alice ", "acct": "alice"}, "Alice"),
        ({"display_name": "", "acct": "alice@example.org"}, "alice@example.org"),
        ({"username": "alice"}, "alice"),
        ({}, ""),
        (None, ""),
        ("invalid", "")
    ]
)
def test_get_status_author(
    account: Any,
    expected: str
) -> None:
    assert module.get_status_author(
        {
            "account": account
        }
    ) == expected


def test_get_status_language_normalizes_lowercase() -> None:
    assert module.get_status_language(
        {
            "language": " FR "
        }
    ) == "fr"


def test_get_status_image_url_returns_first_valid_image(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "is_valid_http_url",
        lambda value: value.startswith("https://")
    )

    status = {
        "media_attachments": [
            {
                "type": "video",
                "url": "https://example.org/video.mp4"
            },
            {
                "type": "image",
                "url": ""
            },
            {
                "type": "image",
                "remote_url": "https://example.org/image.jpg"
            },
            {
                "type": "image",
                "url": "https://example.org/second.jpg"
            }
        ]
    }

    assert module.get_status_image_url(status) == "https://example.org/image.jpg"


@pytest.mark.parametrize(
    "attachments",
    [
        None,
        {},
        "invalid",
        []
    ]
)
def test_get_status_image_url_returns_empty_without_valid_attachment(
    attachments: Any
) -> None:
    assert module.get_status_image_url(
        {
            "media_attachments": attachments
        }
    ) == ""


def test_get_status_text_prefers_content() -> None:
    status = {
        "content": "<p>Contenu principal</p>",
        "spoiler_text": "Avertissement"
    }

    assert module.get_status_text(status) == "Contenu principal"


def test_get_status_text_falls_back_to_spoiler_text() -> None:
    status = {
        "content": "",
        "spoiler_text": "<p>Avertissement</p>"
    }

    assert module.get_status_text(status) == "Avertissement"


# Filtrage spécifique

def test_should_skip_status_rejects_reblog_by_default() -> None:
    status = {
        "reblog": {
            "id": "original"
        }
    }

    assert module.should_skip_status(status, {}) == "reblog_exclu"


def test_should_skip_status_rejects_reply_by_default() -> None:
    status = {
        "in_reply_to_id": "123"
    }

    assert module.should_skip_status(status, {}) == "reponse_exclue"


def test_should_skip_status_rejects_sensitive_content_by_default() -> None:
    status = {
        "sensitive": True
    }

    assert module.should_skip_status(status, {}) == "contenu_sensible"


def test_should_skip_status_rejects_unauthorized_language() -> None:
    status = {
        "language": "en"
    }
    source = {
        "languages": [
            "fr"
        ]
    }

    assert module.should_skip_status(status, source) == "langue_non_autorisee"


def test_should_skip_status_checks_original_status_language() -> None:
    status = {
        "reblog": {
            "language": "fr"
        }
    }
    source = {
        "include_reblogs": True,
        "languages": [
            "en"
        ]
    }

    assert module.should_skip_status(status, source) == "langue_non_autorisee"


def test_should_skip_status_accepts_enabled_content() -> None:
    status = {
        "reblog": {
            "language": "fr"
        },
        "in_reply_to_id": "123",
        "sensitive": True
    }
    source = {
        "include_reblogs": True,
        "include_replies": True,
        "include_sensitive": True,
        "languages": [
            "fr"
        ]
    }

    assert module.should_skip_status(status, source) == ""


@pytest.mark.parametrize(
    ("value", "minimum", "expected"),
    [
        (5, None, (True, "")),
        (None, 5, (True, "")),
        (5, 5, (True, "")),
        (6, 5, (True, "")),
        (4, 5, (False, "insuffisant")),
        ("4.5", "5", (False, "insuffisant")),
        ("invalid", 5, (True, ""))
    ]
)
def test_validate_minimum(
    value: Any,
    minimum: Any,
    expected: tuple[bool, str]
) -> None:
    assert module.validate_minimum(
        value,
        minimum,
        "insuffisant"
    ) == expected


@pytest.mark.parametrize(
    ("status", "filters", "expected"),
    [
        (
            {
                "favourites_count": 2,
                "reblogs_count": 3,
                "replies_count": 4
            },
            {
                "min_favourites": 2,
                "min_reblogs": 3,
                "min_replies": 4
            },
            (True, "")
        ),
        (
            {
                "favourites_count": 1,
                "reblogs_count": 10,
                "replies_count": 10
            },
            {
                "min_favourites": 2
            },
            (False, "favoris_insuffisants")
        ),
        (
            {
                "favourites_count": 10,
                "reblogs_count": 1,
                "replies_count": 10
            },
            {
                "min_reblogs": 2
            },
            (False, "reblogs_insuffisants")
        ),
        (
            {
                "favourites_count": 10,
                "reblogs_count": 10,
                "replies_count": 1
            },
            {
                "min_replies": 2
            },
            (False, "reponses_insuffisantes")
        )
    ]
)
def test_validate_mastodon_metrics(
    status: Mapping[str, Any],
    filters: Mapping[str, Any],
    expected: tuple[bool, str]
) -> None:
    assert module.validate_mastodon_metrics(status, filters) == expected


def test_validate_mastodon_item_rejects_invalid_item() -> None:
    assert module.validate_mastodon_item(
        None,
        {},
        {}
    ) == (
        False,
        "statut_mastodon_invalide"
    )


def test_validate_mastodon_item_requires_identifier_or_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_status_identifier",
        lambda status: ""
    )
    monkeypatch.setattr(
        module,
        "get_status_url",
        lambda status: ""
    )

    assert module.validate_mastodon_item(
        {},
        {},
        {}
    ) == (
        False,
        "identifiant_absent"
    )


def test_validate_mastodon_item_requires_content(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_status_identifier",
        lambda status: "123"
    )
    monkeypatch.setattr(
        module,
        "get_status_url",
        lambda status: ""
    )
    monkeypatch.setattr(
        module,
        "get_status_text",
        lambda status: ""
    )

    assert module.validate_mastodon_item(
        {},
        {},
        {}
    ) == (
        False,
        "contenu_absent"
    )


def test_validate_mastodon_item_delegates_to_metrics(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    filters = {
        "min_favourites": 5
    }
    received: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []

    monkeypatch.setattr(
        module,
        "get_status_identifier",
        lambda status: "123"
    )
    monkeypatch.setattr(
        module,
        "get_status_url",
        lambda status: ""
    )
    monkeypatch.setattr(
        module,
        "get_status_text",
        lambda status: "Contenu"
    )

    def fake_validate_mastodon_metrics(
        status: Mapping[str, Any],
        current_filters: Mapping[str, Any]
    ) -> tuple[bool, str]:
        received.append((status, current_filters))
        return False, "favoris_insuffisants"

    monkeypatch.setattr(
        module,
        "validate_mastodon_metrics",
        fake_validate_mastodon_metrics
    )

    status = {
        "id": "123"
    }

    result = module.validate_mastodon_item(
        status,
        filters,
        {
            "name": "Mastodon"
        }
    )

    assert result == (
        False,
        "favoris_insuffisants"
    )
    assert received == [
        (status, filters)
    ]


# Construction de l'article

def test_build_mastodon_article_rejects_invalid_status() -> None:
    assert module.build_mastodon_article(
        None,
        "fallback",
        {},
        {}
    ) == {}


def test_build_mastodon_article_requires_identifier_or_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_status_identifier",
        lambda status: ""
    )
    monkeypatch.setattr(
        module,
        "get_status_url",
        lambda status: ""
    )

    assert module.build_mastodon_article(
        {},
        "",
        {},
        {}
    ) == {}


def test_build_mastodon_article_builds_expected_article(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    status = {
        "id": "123",
        "created_at": "2026-07-28T12:00:00Z"
    }
    source = {
        "name": "Mastodon Source",
        "language": "fr",
        "category": "",
        "role": "social_reference"
    }
    context = {
        "hashtag": "FactCheck"
    }
    received: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "get_original_status",
        lambda current_status: current_status
    )
    monkeypatch.setattr(
        module,
        "get_status_url",
        lambda current_status: "https://mastodon.social/@user/123"
    )
    monkeypatch.setattr(
        module,
        "get_status_identifier",
        lambda current_status: "123"
    )
    monkeypatch.setattr(
        module,
        "get_status_text",
        lambda current_status: "Texte du statut."
    )
    monkeypatch.setattr(
        module,
        "build_mastodon_title",
        lambda text: "Titre Mastodon"
    )
    monkeypatch.setattr(
        module,
        "get_status_image_url",
        lambda current_status: "https://example.org/image.jpg"
    )
    monkeypatch.setattr(
        module,
        "convert_date_to_iso",
        lambda value: "2026-07-28T12:00:00+00:00"
    )
    monkeypatch.setattr(
        module,
        "get_status_author",
        lambda current_status: "Alice"
    )
    monkeypatch.setattr(
        module,
        "get_status_language",
        lambda current_status: "fr"
    )

    def fake_build_standard_article(**kwargs: Any) -> dict[str, Any]:
        received.update(kwargs)
        return kwargs

    monkeypatch.setattr(
        module,
        "build_standard_article",
        fake_build_standard_article
    )

    result = module.build_mastodon_article(
        status,
        "fallback",
        source,
        context
    )

    assert result == received
    assert received == {
        "identifier": "123",
        "source": "Mastodon Source",
        "title": "Titre Mastodon",
        "text": "Texte du statut.",
        "image_url": "https://example.org/image.jpg",
        "image_path": "",
        "published_at": "2026-07-28T12:00:00+00:00",
        "url": "https://mastodon.social/@user/123",
        "author": "Alice",
        "language": "fr",
        "category": "factcheck",
        "label": "",
        "dataset_role": "social_reference"
    }


def test_build_mastodon_article_uses_fallback_identifier(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    received: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "get_status_identifier",
        lambda status: ""
    )
    monkeypatch.setattr(
        module,
        "get_status_url",
        lambda status: "https://example.org/status"
    )
    monkeypatch.setattr(
        module,
        "get_status_text",
        lambda status: "Texte"
    )
    monkeypatch.setattr(
        module,
        "get_status_language",
        lambda status: ""
    )
    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: received.update(kwargs) or kwargs
    )

    module.build_mastodon_article(
        {},
        "fallback-id",
        {
            "language": "fr"
        },
        {}
    )

    assert received["identifier"] == "fallback-id"
    assert received["language"] == "fr"
    assert received["category"] == "social"
    assert received["dataset_role"] == "acquisition"


# URL et pagination

def test_build_hashtag_timeline_url_encodes_hashtag() -> None:
    result = module.build_hashtag_timeline_url(
        "https://mastodon.social",
        "fake news"
    )

    assert result == (
        "https://mastodon.social/api/v1/timelines/tag/fake%20news"
    )


def test_get_next_max_id_returns_pagination_identifier() -> None:
    response = FakeResponse(
        links={
            "next": {
                "url": "https://mastodon.social/api/v1/timelines/tag/news?limit=40&max_id=123"
            }
        }
    )

    assert module.get_next_max_id(response) == "123"


@pytest.mark.parametrize(
    "links",
    [
        {},
        {"next": None},
        {"next": []},
        {"next": {}},
        {"next": {"url": ""}},
        {"next": {"url": "https://example.org/path"}}
    ]
)
def test_get_next_max_id_returns_empty_without_valid_parameter(
    links: dict[str, Any]
) -> None:
    response = FakeResponse(links=links)

    assert module.get_next_max_id(response) == ""


def test_fetch_mastodon_page_builds_request(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    response = FakeResponse()
    session = FakeSession(response=response)

    monkeypatch.setattr(
        module,
        "build_hashtag_timeline_url",
        lambda instance, hashtag: "https://example.org/timeline"
    )

    result = module.fetch_mastodon_page.retry_with(
        stop=module.stop_after_attempt(1),
        wait=module.wait_exponential(multiplier=0, min=0, max=0)
    )(
        session=session,
        instance="https://mastodon.social",
        hashtag="news",
        limit=100,
        max_id="123"
    )

    assert result is response
    assert response.raise_calls == 1
    assert session.get_calls == [
        {
            "url": "https://example.org/timeline",
            "params": {
                "limit": module.MASTODON_MAX_PAGE_SIZE,
                "max_id": "123"
            },
            "timeout": module.REQUEST_TIMEOUT
        }
    ]


def test_fetch_mastodon_page_enforces_minimum_limit(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    response = FakeResponse()
    session = FakeSession(response=response)

    monkeypatch.setattr(
        module,
        "build_hashtag_timeline_url",
        lambda instance, hashtag: "https://example.org/timeline"
    )

    module.fetch_mastodon_page.retry_with(
        stop=module.stop_after_attempt(1),
        wait=module.wait_exponential(multiplier=0, min=0, max=0)
    )(
        session=session,
        instance="https://mastodon.social",
        hashtag="news",
        limit=0
    )

    assert session.get_calls[0]["params"] == {
        "limit": 1
    }


def test_parse_mastodon_response_returns_mapping_items() -> None:
    response = FakeResponse(
        payload=[
            {
                "id": "1"
            },
            "invalid",
            {
                "id": "2"
            },
            None
        ]
    )

    assert module.parse_mastodon_response(response) == [
        {
            "id": "1"
        },
        {
            "id": "2"
        }
    ]


def test_parse_mastodon_response_rejects_invalid_json() -> None:
    error = requests.exceptions.JSONDecodeError(
        "invalid",
        "document",
        0
    )
    response = FakeResponse(json_error=error)

    with pytest.raises(
        ValueError,
        match="réponse JSON Mastodon invalide"
    ):
        module.parse_mastodon_response(response)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        "invalid",
        42
    ]
)
def test_parse_mastodon_response_rejects_invalid_payload(
    payload: Any
) -> None:
    response = FakeResponse(payload=payload)

    with pytest.raises(
        ValueError,
        match="format de réponse Mastodon inattendu"
    ):
        module.parse_mastodon_response(response)


def test_iter_hashtag_statuses_yields_paginated_statuses(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    responses = [
        FakeResponse(
            payload=[
                {
                    "id": "1"
                },
                {
                    "id": "2"
                }
            ],
            links={
                "next": {
                    "url": "https://example.org?max_id=2"
                }
            }
        ),
        FakeResponse(
            payload=[
                {
                    "id": "3"
                }
            ]
        )
    ]
    calls: list[dict[str, Any]] = []

    def fake_fetch_mastodon_page(**kwargs: Any) -> FakeResponse:
        calls.append(kwargs)
        return responses.pop(0)

    monkeypatch.setattr(
        module,
        "fetch_mastodon_page",
        fake_fetch_mastodon_page
    )

    result = list(
        module.iter_hashtag_statuses(
            session=FakeSession(),
            instance="https://mastodon.social",
            hashtag="news",
            maximum_articles=3
        )
    )

    assert result == [
        {
            "id": "1"
        },
        {
            "id": "2"
        },
        {
            "id": "3"
        }
    ]
    assert calls == [
        {
            "session": calls[0]["session"],
            "instance": "https://mastodon.social",
            "hashtag": "news",
            "limit": 3,
            "max_id": ""
        },
        {
            "session": calls[1]["session"],
            "instance": "https://mastodon.social",
            "hashtag": "news",
            "limit": 1,
            "max_id": "2"
        }
    ]


def test_iter_hashtag_statuses_stops_on_empty_page(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def fake_fetch_mastodon_page(**kwargs: Any) -> FakeResponse:
        nonlocal calls
        calls += 1
        return FakeResponse(payload=[])

    monkeypatch.setattr(
        module,
        "fetch_mastodon_page",
        fake_fetch_mastodon_page
    )

    result = list(
        module.iter_hashtag_statuses(
            FakeSession(),
            "https://mastodon.social",
            "news",
            10
        )
    )

    assert result == []
    assert calls == 1


def test_iter_hashtag_statuses_stops_on_repeated_max_id(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def fake_fetch_mastodon_page(**kwargs: Any) -> FakeResponse:
        nonlocal calls
        calls += 1
        return FakeResponse(
            payload=[
                {
                    "id": str(calls)
                }
            ],
            links={
                "next": {
                    "url": "https://example.org?max_id=same"
                }
            }
        )

    monkeypatch.setattr(
        module,
        "fetch_mastodon_page",
        fake_fetch_mastodon_page
    )

    result = list(
        module.iter_hashtag_statuses(
            FakeSession(),
            "https://mastodon.social",
            "news",
            10
        )
    )

    assert result == [
        {
            "id": "1"
        },
        {
            "id": "2"
        }
    ]
    assert calls == 2


# Itérateur Mastodon

def test_iter_mastodon_items_returns_nothing_without_instances(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_instances",
        lambda source: []
    )
    monkeypatch.setattr(
        module,
        "get_hashtags",
        lambda source: [
            "news"
        ]
    )

    assert list(
        module.iter_mastodon_items(
            {},
            10
        )
    ) == []


def test_iter_mastodon_items_returns_nothing_without_hashtags(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_instances",
        lambda source: [
            "https://mastodon.social"
        ]
    )
    monkeypatch.setattr(
        module,
        "get_hashtags",
        lambda source: []
    )

    assert list(
        module.iter_mastodon_items(
            {},
            10
        )
    ) == []


def test_iter_mastodon_items_yields_statuses_and_closes_session(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    session = FakeSession()
    statuses = [
        {
            "id": "1"
        },
        {
            "id": "2"
        }
    ]

    monkeypatch.setattr(
        module,
        "get_instances",
        lambda source: [
            "https://mastodon.social"
        ]
    )
    monkeypatch.setattr(
        module,
        "get_hashtags",
        lambda source: [
            "news"
        ]
    )
    monkeypatch.setattr(
        module,
        "create_mastodon_session",
        lambda: session
    )
    monkeypatch.setattr(
        module,
        "iter_hashtag_statuses",
        lambda *args: statuses
    )
    monkeypatch.setattr(
        module,
        "should_skip_status",
        lambda status, source: ""
    )

    result = list(
        module.iter_mastodon_items(
            {},
            10
        )
    )

    assert result == [
        SocialItem(
            identifier="1",
            item=statuses[0],
            context={
                "instance": "https://mastodon.social",
                "hashtag": "news"
            }
        ),
        SocialItem(
            identifier="2",
            item=statuses[1],
            context={
                "instance": "https://mastodon.social",
                "hashtag": "news"
            }
        )
    ]
    assert session.close_calls == 1


def test_iter_mastodon_items_preserves_skip_reason(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    session = FakeSession()
    status = {
        "id": "1"
    }

    monkeypatch.setattr(
        module,
        "get_instances",
        lambda source: [
            "https://mastodon.social"
        ]
    )
    monkeypatch.setattr(
        module,
        "get_hashtags",
        lambda source: [
            "news"
        ]
    )
    monkeypatch.setattr(
        module,
        "create_mastodon_session",
        lambda: session
    )
    monkeypatch.setattr(
        module,
        "iter_hashtag_statuses",
        lambda *args: [
            status
        ]
    )
    monkeypatch.setattr(
        module,
        "should_skip_status",
        lambda current_status, source: "langue_non_autorisee"
    )

    result = list(
        module.iter_mastodon_items(
            {},
            10
        )
    )

    assert result == [
        SocialItem(
            identifier="1",
            item=status,
            context={
                "instance": "https://mastodon.social",
                "hashtag": "news"
            },
            rejection_reason="langue_non_autorisee"
        )
    ]
    assert session.close_calls == 1


def test_iter_mastodon_items_handles_http_error(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    session = FakeSession()
    response = Response()
    response.status_code = 429
    error = requests.exceptions.HTTPError(response=response)

    monkeypatch.setattr(
        module,
        "get_instances",
        lambda source: [
            "https://mastodon.social"
        ]
    )
    monkeypatch.setattr(
        module,
        "get_hashtags",
        lambda source: [
            "news"
        ]
    )
    monkeypatch.setattr(
        module,
        "create_mastodon_session",
        lambda: session
    )
    monkeypatch.setattr(
        module,
        "iter_hashtag_statuses",
        lambda *args: (_ for _ in ()).throw(error)
    )

    result = list(
        module.iter_mastodon_items(
            {},
            10
        )
    )

    assert result == [
        SocialItem(
            "",
            None,
            rejection_reason="erreur_http_429"
        )
    ]
    assert session.close_calls == 1


@pytest.mark.parametrize(
    ("error", "expected_reason"),
    [
        (
            requests.exceptions.ConnectionError("offline"),
            "instance_indisponible"
        ),
        (
            requests.exceptions.Timeout("timeout"),
            "instance_indisponible"
        ),
        (
            requests.exceptions.RequestException("request"),
            "extraction_timeline_impossible"
        ),
        (
            ValueError("invalid"),
            "extraction_timeline_impossible"
        ),
        (
            TypeError("invalid"),
            "extraction_timeline_impossible"
        )
    ]
)
def test_iter_mastodon_items_handles_timeline_errors(
    error: Exception,
    expected_reason: str,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    session = FakeSession()

    monkeypatch.setattr(
        module,
        "get_instances",
        lambda source: [
            "https://mastodon.social"
        ]
    )
    monkeypatch.setattr(
        module,
        "get_hashtags",
        lambda source: [
            "news"
        ]
    )
    monkeypatch.setattr(
        module,
        "create_mastodon_session",
        lambda: session
    )
    monkeypatch.setattr(
        module,
        "iter_hashtag_statuses",
        lambda *args: (_ for _ in ()).throw(error)
    )

    result = list(
        module.iter_mastodon_items(
            {},
            10
        )
    )

    assert result == [
        SocialItem(
            "",
            None,
            rejection_reason=expected_reason
        )
    ]
    assert session.close_calls == 1


# Fonctions publiques

def test_load_mastodon_source_delegates_to_extractor(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = {
        "source_id": "mastodon",
        "name": "Mastodon"
    }
    extractor = FakeExtractor(source=expected)

    monkeypatch.setattr(
        module,
        "MASTODON_EXTRACTOR",
        extractor
    )

    result = module.load_mastodon_source()

    assert result == expected
    assert extractor.reload_calls == 1


def test_extract_articles_from_source_delegates_to_social_engine(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    source = {
        "source_id": "mastodon"
    }
    expected = object()
    received: list[dict[str, Any]] = []

    def fake_extract_social_source(**kwargs: Any) -> Any:
        received.append(kwargs)
        return expected

    monkeypatch.setattr(
        module,
        "extract_social_source",
        fake_extract_social_source
    )

    result = module.extract_articles_from_source(source)

    assert result is expected
    assert received == [
        {
            "source": source,
            "adapter": module.MASTODON_ADAPTER
        }
    ]


def test_extract_all_articles_delegates_to_extractor(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()
    extractor = FakeExtractor(result=expected)

    monkeypatch.setattr(
        module,
        "MASTODON_EXTRACTOR",
        extractor
    )

    result = module.extract_all_articles()

    assert result is expected
    assert extractor.run_calls == 1