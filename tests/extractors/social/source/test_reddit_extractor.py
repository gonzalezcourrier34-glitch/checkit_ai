"""Tests de l'adaptateur Reddit."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import pytest

from src.extractors.social.social_adapter import SocialItem
from src.extractors.social.source import reddit_extractor as module


# Doubles de test

class FakePost:
    """Simule une publication Reddit."""

    def __init__(self, **attributes: Any) -> None:
        for name, value in attributes.items():
            setattr(self, name, value)


class FakeSubreddit:
    """Simule un subreddit PRAW."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def hot(self, **kwargs: Any) -> list[Any]:
        self.calls.append(("hot", kwargs))
        return ["hot"]

    def new(self, **kwargs: Any) -> list[Any]:
        self.calls.append(("new", kwargs))
        return ["new"]

    def rising(self, **kwargs: Any) -> list[Any]:
        self.calls.append(("rising", kwargs))
        return ["rising"]

    def top(self, **kwargs: Any) -> list[Any]:
        self.calls.append(("top", kwargs))
        return ["top"]


class FakeReddit:
    """Simule un client Reddit."""

    def __init__(self, subreddit: Any = None) -> None:
        self.subreddit_result = subreddit
        self.subreddit_calls: list[str] = []
        self.read_only = False

    def subreddit(self, name: str) -> Any:
        self.subreddit_calls.append(name)
        return self.subreddit_result


class FakeExtractor:
    """Simule l'extracteur Reddit public."""

    def __init__(
        self,
        source: dict[str, Any] | None = None,
        result: Any = None,
        client_id: str = "",
        client_secret: str = ""
    ) -> None:
        self.source = source or {}
        self.result = result
        self.client_id = client_id
        self.client_secret = client_secret
        self.reload_calls = 0
        self.run_calls = 0

    def reload_source(self) -> dict[str, Any]:
        self.reload_calls += 1
        return self.source

    def run(self) -> Any:
        self.run_calls += 1
        return self.result


# Configuration

def test_reddit_adapter_is_configured() -> None:
    assert module.REDDIT_ADAPTER.source_id == "reddit"
    assert module.REDDIT_ADAPTER.default_name == "Reddit"
    assert module.REDDIT_ADAPTER.iter_items is module.iter_reddit_items
    assert module.REDDIT_ADAPTER.build_article is module.build_reddit_article
    assert module.REDDIT_ADAPTER.validate_item is module.validate_reddit_item


def test_reddit_extractor_uses_adapter_and_sources_file() -> None:
    assert module.REDDIT_EXTRACTOR.adapter is module.REDDIT_ADAPTER
    assert module.REDDIT_EXTRACTOR.section_name == "social_sources"
    assert module.REDDIT_EXTRACTOR.sources_file == module.SOURCES_FILE


# Authentification

def test_validate_reddit_authentication_returns_credentials(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    extractor = FakeExtractor(
        client_id="client-id",
        client_secret="client-secret"
    )

    monkeypatch.setattr(
        module,
        "REDDIT_EXTRACTOR",
        extractor
    )
    monkeypatch.setattr(
        module,
        "get_environment_variable",
        lambda name: "CheckItAI/1.0"
    )
    monkeypatch.setattr(
        module,
        "is_valid_secret",
        lambda value: bool(value)
    )

    assert module.validate_reddit_authentication() == (
        "client-id",
        "client-secret",
        "CheckItAI/1.0"
    )


def test_validate_reddit_authentication_rejects_invalid_client_id(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "REDDIT_EXTRACTOR",
        FakeExtractor(
            client_id="",
            client_secret="secret"
        )
    )
    monkeypatch.setattr(
        module,
        "get_environment_variable",
        lambda name: "agent"
    )
    monkeypatch.setattr(
        module,
        "is_valid_secret",
        lambda value: bool(value)
    )

    with pytest.raises(
        RuntimeError,
        match="Le client ID Reddit est absent ou invalide"
    ):
        module.validate_reddit_authentication()


def test_validate_reddit_authentication_rejects_invalid_client_secret(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "REDDIT_EXTRACTOR",
        FakeExtractor(
            client_id="client",
            client_secret=""
        )
    )
    monkeypatch.setattr(
        module,
        "get_environment_variable",
        lambda name: "agent"
    )
    monkeypatch.setattr(
        module,
        "is_valid_secret",
        lambda value: bool(value)
    )

    with pytest.raises(
        RuntimeError,
        match="Le client secret Reddit est absent ou invalide"
    ):
        module.validate_reddit_authentication()


def test_validate_reddit_authentication_rejects_missing_user_agent(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "REDDIT_EXTRACTOR",
        FakeExtractor(
            client_id="client",
            client_secret="secret"
        )
    )
    monkeypatch.setattr(
        module,
        "get_environment_variable",
        lambda name: ""
    )
    monkeypatch.setattr(
        module,
        "is_valid_secret",
        lambda value: True
    )

    with pytest.raises(
        RuntimeError,
        match="La variable USER_AGENT est absente ou invalide"
    ):
        module.validate_reddit_authentication()


# Lecture de configuration

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("hot", "hot"),
        (" NEW ", "new"),
        ("rising", "rising"),
        ("top", "top"),
        ("invalid", "hot"),
        ("", "hot"),
        (None, "hot")
    ]
)
def test_get_listing_name(
    value: Any,
    expected: str
) -> None:
    assert module.get_listing_name(
        {
            "listing": value
        }
    ) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("hour", "hour"),
        (" DAY ", "day"),
        ("week", "week"),
        ("month", "month"),
        ("year", "year"),
        ("all", "all"),
        ("invalid", "day"),
        ("", "day"),
        (None, "day")
    ]
)
def test_get_time_filter(
    value: Any,
    expected: str
) -> None:
    assert module.get_time_filter(
        {
            "time_filter": value
        }
    ) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("news", "news"),
        ("r/news", "news"),
        ("/r/news", "news"),
        ("/r/news/", "news"),
        ("  /r/worldnews/  ", "worldnews"),
        ("", ""),
        (None, "")
    ]
)
def test_normalize_subreddit_name(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_subreddit_name(value) == expected


def test_get_subreddits_normalizes_and_deduplicates() -> None:
    result = module.get_subreddits(
        {
            "subreddits": [
                "r/news",
                "/r/worldnews/",
                "news",
                "",
                None
            ]
        }
    )

    assert result == [
        "news",
        "worldnews"
    ]


# Client Reddit

def test_create_reddit_client_builds_read_only_client(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    reddit = FakeReddit()
    received: dict[str, Any] = {}

    def fake_reddit(**kwargs: Any) -> FakeReddit:
        received.update(kwargs)
        return reddit

    monkeypatch.setattr(
        module.praw,
        "Reddit",
        fake_reddit
    )

    result = module.create_reddit_client(
        "client-id",
        "client-secret",
        "agent"
    )

    assert result is reddit
    assert reddit.read_only is True
    assert received == {
        "client_id": "client-id",
        "client_secret": "client-secret",
        "user_agent": "agent",
        "check_for_async": False,
        "ratelimit_seconds": module.REDDIT_RATE_LIMIT_SECONDS
    }


@pytest.mark.parametrize(
    "error",
    [
        TypeError("invalid"),
        ValueError("invalid")
    ]
)
def test_create_reddit_client_wraps_errors(
    error: Exception,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module.praw,
        "Reddit",
        lambda **kwargs: (_ for _ in ()).throw(error)
    )

    with pytest.raises(
        RuntimeError,
        match="Impossible de créer le client Reddit"
    ):
        module.create_reddit_client(
            "client-id",
            "client-secret",
            "agent"
        )


# URL

def test_build_reddit_post_url_builds_absolute_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(
        permalink="/r/news/comments/123/test/"
    )

    monkeypatch.setattr(
        module,
        "is_valid_http_url",
        lambda value: value.startswith("https://")
    )

    assert module.build_reddit_post_url(post) == (
        "https://www.reddit.com/r/news/comments/123/test/"
    )


def test_build_reddit_post_url_returns_empty_without_permalink() -> None:
    assert module.build_reddit_post_url(
        FakePost(permalink="")
    ) == ""


def test_build_reddit_post_url_rejects_invalid_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "is_valid_http_url",
        lambda value: False
    )

    assert module.build_reddit_post_url(
        FakePost(permalink="/r/news/comments/123/")
    ) == ""


def test_normalize_image_url_decodes_html(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "is_valid_http_url",
        lambda value: value.startswith("https://")
    )

    assert module.normalize_image_url(
        "https://example.org/image.jpg?x=1&amp;y=2"
    ) == "https://example.org/image.jpg?x=1&y=2"


def test_normalize_image_url_rejects_invalid_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "is_valid_http_url",
        lambda value: False
    )

    assert module.normalize_image_url("invalid") == ""


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://example.org/image.jpg", True),
        ("https://example.org/image.jpeg?x=1", True),
        ("https://example.org/image.PNG", True),
        ("https://example.org/image.webp", True),
        ("https://example.org/image.gif", False),
        ("https://example.org/page", False),
        ("", False)
    ]
)
def test_is_direct_image_url(
    value: str,
    expected: bool,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "normalize_image_url",
        lambda current_value: current_value
    )

    assert module.is_direct_image_url(value) is expected


# Images Reddit

def test_get_gallery_image_url_uses_gallery_order(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(
        gallery_data={
            "items": [
                {
                    "media_id": "second"
                },
                {
                    "media_id": "first"
                }
            ]
        },
        media_metadata={
            "first": {
                "s": {
                    "u": "https://example.org/first.jpg"
                }
            },
            "second": {
                "s": {
                    "u": "https://example.org/second.jpg"
                }
            }
        }
    )

    monkeypatch.setattr(
        module,
        "normalize_image_url",
        lambda value: value
    )

    assert module.get_gallery_image_url(post) == (
        "https://example.org/second.jpg"
    )


def test_get_gallery_image_url_uses_metadata_fallback(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(
        gallery_data={},
        media_metadata={
            "first": {
                "s": {
                    "u": "https://example.org/first.jpg"
                }
            }
        }
    )

    monkeypatch.setattr(
        module,
        "normalize_image_url",
        lambda value: value
    )

    assert module.get_gallery_image_url(post) == (
        "https://example.org/first.jpg"
    )


@pytest.mark.parametrize(
    "metadata",
    [
        None,
        [],
        "invalid"
    ]
)
def test_get_gallery_image_url_rejects_invalid_metadata(
    metadata: Any
) -> None:
    post = FakePost(
        gallery_data={},
        media_metadata=metadata
    )

    assert module.get_gallery_image_url(post) == ""


def test_get_preview_image_url_returns_source_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(
        preview={
            "images": [
                {
                    "source": {
                        "url": "https://example.org/preview.jpg"
                    }
                }
            ]
        }
    )

    monkeypatch.setattr(
        module,
        "normalize_image_url",
        lambda value: value
    )

    assert module.get_preview_image_url(post) == (
        "https://example.org/preview.jpg"
    )


@pytest.mark.parametrize(
    "preview",
    [
        None,
        [],
        {},
        {"images": []},
        {"images": "invalid"},
        {"images": [None]},
        {"images": [{"source": None}]}
    ]
)
def test_get_preview_image_url_returns_empty_for_invalid_preview(
    preview: Any
) -> None:
    assert module.get_preview_image_url(
        FakePost(preview=preview)
    ) == ""


def test_get_thumbnail_image_url_accepts_direct_image(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "normalize_image_url",
        lambda value: "https://example.org/thumb.jpg"
    )
    monkeypatch.setattr(
        module,
        "is_direct_image_url",
        lambda value: True
    )

    assert module.get_thumbnail_image_url(
        FakePost(thumbnail="value")
    ) == "https://example.org/thumb.jpg"


def test_get_thumbnail_image_url_rejects_non_image(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "normalize_image_url",
        lambda value: "https://example.org/page"
    )
    monkeypatch.setattr(
        module,
        "is_direct_image_url",
        lambda value: False
    )

    assert module.get_thumbnail_image_url(
        FakePost(thumbnail="value")
    ) == ""


def test_get_post_image_url_prefers_direct_post_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(
        url="https://example.org/image.jpg"
    )

    monkeypatch.setattr(
        module,
        "normalize_image_url",
        lambda value: value
    )
    monkeypatch.setattr(
        module,
        "is_direct_image_url",
        lambda value: True
    )
    monkeypatch.setattr(
        module,
        "get_gallery_image_url",
        lambda current_post: pytest.fail("Galerie non attendue")
    )

    assert module.get_post_image_url(post) == (
        "https://example.org/image.jpg"
    )


def test_get_post_image_url_uses_fallback_order(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(
        url="https://example.org/page"
    )
    calls: list[str] = []

    monkeypatch.setattr(
        module,
        "normalize_image_url",
        lambda value: value
    )
    monkeypatch.setattr(
        module,
        "is_direct_image_url",
        lambda value: False
    )

    def fake_gallery(current_post: Any) -> str:
        calls.append("gallery")
        return ""

    def fake_preview(current_post: Any) -> str:
        calls.append("preview")
        return "https://example.org/preview.jpg"

    def fake_thumbnail(current_post: Any) -> str:
        calls.append("thumbnail")
        return "https://example.org/thumb.jpg"

    monkeypatch.setattr(
        module,
        "get_gallery_image_url",
        fake_gallery
    )
    monkeypatch.setattr(
        module,
        "get_preview_image_url",
        fake_preview
    )
    monkeypatch.setattr(
        module,
        "get_thumbnail_image_url",
        fake_thumbnail
    )

    assert module.get_post_image_url(post) == (
        "https://example.org/preview.jpg"
    )
    assert calls == [
        "gallery",
        "preview"
    ]


# Contenu

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Texte Reddit", "Texte Reddit"),
        (" [deleted] ", ""),
        ("[removed]", ""),
        ("", "")
    ]
)
def test_get_post_text(
    value: str,
    expected: str
) -> None:
    assert module.get_post_text(
        FakePost(selftext=value)
    ) == expected


@pytest.mark.parametrize(
    ("author", "expected"),
    [
        ("alice", "alice"),
        (None, ""),
        ("", "")
    ]
)
def test_get_post_author(
    author: Any,
    expected: str
) -> None:
    assert module.get_post_author(
        FakePost(author=author)
    ) == expected


# Filtrage

def test_should_skip_post_rejects_nsfw_by_default() -> None:
    assert module.should_skip_post(
        FakePost(over_18=True),
        {}
    ) == "contenu_nsfw"


def test_should_skip_post_rejects_spoiler_when_disabled() -> None:
    assert module.should_skip_post(
        FakePost(spoiler=True),
        {
            "include_spoilers": False
        }
    ) == "spoiler"


def test_should_skip_post_rejects_stickied_by_default() -> None:
    assert module.should_skip_post(
        FakePost(stickied=True),
        {}
    ) == "publication_epinglee"


def test_should_skip_post_accepts_enabled_content() -> None:
    post = FakePost(
        over_18=True,
        spoiler=True,
        stickied=True
    )
    source = {
        "include_nsfw": True,
        "include_spoilers": True,
        "include_stickied": True
    }

    assert module.should_skip_post(post, source) == ""


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


def test_validate_reddit_metrics_accepts_valid_metrics() -> None:
    post = FakePost(
        score=10,
        num_comments=5
    )

    assert module.validate_reddit_metrics(
        post,
        {
            "min_score": 10,
            "min_comments": 5
        }
    ) == (
        True,
        ""
    )


def test_validate_reddit_metrics_rejects_score() -> None:
    post = FakePost(
        score=2,
        num_comments=10
    )

    assert module.validate_reddit_metrics(
        post,
        {
            "min_score": 5
        }
    ) == (
        False,
        "score_insuffisant"
    )


def test_validate_reddit_metrics_rejects_comments() -> None:
    post = FakePost(
        score=10,
        num_comments=1
    )

    assert module.validate_reddit_metrics(
        post,
        {
            "min_comments": 5
        }
    ) == (
        False,
        "commentaires_insuffisants"
    )


# Construction et validation

def test_build_reddit_article_rejects_invalid_post() -> None:
    assert module.build_reddit_article(
        None,
        "fallback",
        {},
        {}
    ) == {}


def test_build_reddit_article_requires_identifier_or_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(id="")

    monkeypatch.setattr(
        module,
        "Submission",
        FakePost
    )
    monkeypatch.setattr(
        module,
        "build_reddit_post_url",
        lambda current_post: ""
    )

    assert module.build_reddit_article(
        post,
        "",
        {},
        {}
    ) == {}


def test_build_reddit_article_builds_expected_article(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(
        id="abc123",
        title="Titre Reddit",
        selftext="Texte Reddit",
        created_utc=1234567890,
        author="alice"
    )
    source = {
        "name": "Reddit Source",
        "language": "fr",
        "category": "",
        "role": "social_reference"
    }
    context = {
        "subreddit": "News"
    }
    received: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "Submission",
        FakePost
    )
    monkeypatch.setattr(
        module,
        "build_reddit_post_url",
        lambda current_post: "https://reddit.com/post"
    )
    monkeypatch.setattr(
        module,
        "get_post_text",
        lambda current_post: "Texte Reddit"
    )
    monkeypatch.setattr(
        module,
        "get_post_image_url",
        lambda current_post: "https://example.org/image.jpg"
    )
    monkeypatch.setattr(
        module,
        "convert_date_to_iso",
        lambda value: "2009-02-13T23:31:30+00:00"
    )
    monkeypatch.setattr(
        module,
        "get_post_author",
        lambda current_post: "alice"
    )

    def fake_build_standard_article(**kwargs: Any) -> dict[str, Any]:
        received.update(kwargs)
        return kwargs

    monkeypatch.setattr(
        module,
        "build_standard_article",
        fake_build_standard_article
    )

    result = module.build_reddit_article(
        post,
        "fallback",
        source,
        context
    )

    assert result == received
    assert received == {
        "identifier": "abc123",
        "source": "Reddit Source",
        "title": "Titre Reddit",
        "text": "Texte Reddit",
        "image_url": "https://example.org/image.jpg",
        "image_path": "",
        "published_at": "2009-02-13T23:31:30+00:00",
        "url": "https://reddit.com/post",
        "author": "alice",
        "language": "fr",
        "category": "news",
        "label": "",
        "dataset_role": "social_reference"
    }


def test_build_reddit_article_uses_default_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(
        id="",
        title="Titre",
        created_utc=""
    )
    received: dict[str, Any] = {}

    monkeypatch.setattr(
        module,
        "Submission",
        FakePost
    )
    monkeypatch.setattr(
        module,
        "build_reddit_post_url",
        lambda current_post: "https://reddit.com/post"
    )
    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: received.update(kwargs) or kwargs
    )

    module.build_reddit_article(
        post,
        "fallback-id",
        {},
        {}
    )

    assert received["identifier"] == "fallback-id"
    assert received["source"] == "Reddit"
    assert received["language"] == "en"
    assert received["category"] == "social"
    assert received["dataset_role"] == "social_reference"


def test_validate_reddit_item_rejects_invalid_item() -> None:
    assert module.validate_reddit_item(
        None,
        {},
        {}
    ) == (
        False,
        "publication_reddit_invalide"
    )


def test_validate_reddit_item_requires_identifier_or_url(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(id="")

    monkeypatch.setattr(
        module,
        "Submission",
        FakePost
    )
    monkeypatch.setattr(
        module,
        "build_reddit_post_url",
        lambda current_post: ""
    )

    assert module.validate_reddit_item(
        post,
        {},
        {}
    ) == (
        False,
        "identifiant_absent"
    )


def test_validate_reddit_item_delegates_to_metrics(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(id="123")
    filters = {
        "min_score": 5
    }
    received: list[tuple[Any, Mapping[str, Any]]] = []

    monkeypatch.setattr(
        module,
        "Submission",
        FakePost
    )

    def fake_validate_reddit_metrics(
        current_post: Any,
        current_filters: Mapping[str, Any]
    ) -> tuple[bool, str]:
        received.append((current_post, current_filters))
        return False, "score_insuffisant"

    monkeypatch.setattr(
        module,
        "validate_reddit_metrics",
        fake_validate_reddit_metrics
    )

    result = module.validate_reddit_item(
        post,
        filters,
        {}
    )

    assert result == (
        False,
        "score_insuffisant"
    )
    assert received == [
        (post, filters)
    ]


# Listings et récupération

@pytest.mark.parametrize(
    ("listing", "expected_name", "expected_kwargs"),
    [
        ("hot", "hot", {"limit": 10}),
        ("new", "new", {"limit": 10}),
        ("rising", "rising", {"limit": 10}),
        (
            "top",
            "top",
            {
                "time_filter": "week",
                "limit": 10
            }
        )
    ]
)
def test_get_subreddit_listing(
    listing: str,
    expected_name: str,
    expected_kwargs: dict[str, Any]
) -> None:
    subreddit = FakeSubreddit()

    result = module.get_subreddit_listing(
        subreddit,
        listing,
        10,
        "week"
    )

    assert result == [expected_name]
    assert subreddit.calls == [
        (
            expected_name,
            expected_kwargs
        )
    ]


def test_fetch_subreddit_posts_returns_list() -> None:
    subreddit = FakeSubreddit()
    reddit = FakeReddit(subreddit=subreddit)

    result = module.fetch_subreddit_posts.retry_with(
        stop=module.stop_after_attempt(1),
        wait=module.wait_exponential(multiplier=0, min=0, max=0)
    )(
        reddit=reddit,
        subreddit_name="news",
        listing="new",
        limit=0,
        time_filter="day"
    )

    assert result == [
        "new"
    ]
    assert reddit.subreddit_calls == [
        "news"
    ]
    assert subreddit.calls == [
        (
            "new",
            {
                "limit": 1
            }
        )
    ]


# Itérateur Reddit

def test_iter_reddit_items_returns_nothing_without_subreddits(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_subreddits",
        lambda source: []
    )

    assert list(
        module.iter_reddit_items(
            {},
            10
        )
    ) == []


def test_iter_reddit_items_yields_posts(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    posts = [
        FakePost(id="1"),
        FakePost(id="2")
    ]

    monkeypatch.setattr(
        module,
        "get_subreddits",
        lambda source: [
            "news"
        ]
    )
    monkeypatch.setattr(
        module,
        "validate_reddit_authentication",
        lambda: (
            "client",
            "secret",
            "agent"
        )
    )
    monkeypatch.setattr(
        module,
        "create_reddit_client",
        lambda **kwargs: FakeReddit()
    )
    monkeypatch.setattr(
        module,
        "get_listing_name",
        lambda source: "new"
    )
    monkeypatch.setattr(
        module,
        "get_time_filter",
        lambda source: "day"
    )
    monkeypatch.setattr(
        module,
        "fetch_subreddit_posts",
        lambda *args: posts
    )
    monkeypatch.setattr(
        module,
        "should_skip_post",
        lambda post, source: ""
    )

    result = list(
        module.iter_reddit_items(
            {},
            10
        )
    )

    assert result == [
        SocialItem(
            identifier="1",
            item=posts[0],
            context={
                "subreddit": "news"
            }
        ),
        SocialItem(
            identifier="2",
            item=posts[1],
            context={
                "subreddit": "news"
            }
        )
    ]


def test_iter_reddit_items_preserves_skip_reason(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    post = FakePost(id="1")

    monkeypatch.setattr(
        module,
        "get_subreddits",
        lambda source: [
            "news"
        ]
    )
    monkeypatch.setattr(
        module,
        "validate_reddit_authentication",
        lambda: (
            "client",
            "secret",
            "agent"
        )
    )
    monkeypatch.setattr(
        module,
        "create_reddit_client",
        lambda **kwargs: FakeReddit()
    )
    monkeypatch.setattr(
        module,
        "get_listing_name",
        lambda source: "hot"
    )
    monkeypatch.setattr(
        module,
        "get_time_filter",
        lambda source: "day"
    )
    monkeypatch.setattr(
        module,
        "fetch_subreddit_posts",
        lambda *args: [
            post
        ]
    )
    monkeypatch.setattr(
        module,
        "should_skip_post",
        lambda current_post, source: "contenu_nsfw"
    )

    result = list(
        module.iter_reddit_items(
            {},
            10
        )
    )

    assert result == [
        SocialItem(
            identifier="1",
            item=post,
            context={
                "subreddit": "news"
            },
            rejection_reason="contenu_nsfw"
        )
    ]


@pytest.mark.parametrize(
    ("exception_name", "expected_reason"),
    [
        ("NotFound", "subreddit_introuvable"),
        ("Forbidden", "subreddit_interdit"),
        ("TooManyRequests", "limite_requetes"),
        ("ResponseException", "reponse_api_invalide"),
        ("PrawcoreException", "erreur_api")
    ]
)
def test_iter_reddit_items_handles_praw_errors(
    exception_name: str,
    expected_reason: str,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeRedditError(Exception):
        pass

    monkeypatch.setattr(
        module,
        exception_name,
        FakeRedditError
    )
    monkeypatch.setattr(
        module,
        "get_subreddits",
        lambda source: [
            "news"
        ]
    )
    monkeypatch.setattr(
        module,
        "validate_reddit_authentication",
        lambda: (
            "client",
            "secret",
            "agent"
        )
    )
    monkeypatch.setattr(
        module,
        "create_reddit_client",
        lambda **kwargs: FakeReddit()
    )
    monkeypatch.setattr(
        module,
        "get_listing_name",
        lambda source: "hot"
    )
    monkeypatch.setattr(
        module,
        "get_time_filter",
        lambda source: "day"
    )
    monkeypatch.setattr(
        module,
        "fetch_subreddit_posts",
        lambda *args: (_ for _ in ()).throw(
            FakeRedditError("boom")
        )
    )

    result = list(
        module.iter_reddit_items(
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


@pytest.mark.parametrize(
    "error",
    [
        TypeError("invalid"),
        ValueError("invalid"),
        AttributeError("invalid")
    ]
)
def test_iter_reddit_items_handles_configuration_errors(
    error: Exception,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "get_subreddits",
        lambda source: [
            "news"
        ]
    )
    monkeypatch.setattr(
        module,
        "validate_reddit_authentication",
        lambda: (
            "client",
            "secret",
            "agent"
        )
    )
    monkeypatch.setattr(
        module,
        "create_reddit_client",
        lambda **kwargs: FakeReddit()
    )
    monkeypatch.setattr(
        module,
        "get_listing_name",
        lambda source: "hot"
    )
    monkeypatch.setattr(
        module,
        "get_time_filter",
        lambda source: "day"
    )
    monkeypatch.setattr(
        module,
        "fetch_subreddit_posts",
        lambda *args: (_ for _ in ()).throw(error)
    )

    result = list(
        module.iter_reddit_items(
            {},
            10
        )
    )

    assert result == [
        SocialItem(
            "",
            None,
            rejection_reason="configuration_invalide"
        )
    ]
    

# Fonctions publiques

def test_load_reddit_source_delegates_to_extractor(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = {
        "source_id": "reddit",
        "name": "Reddit"
    }
    extractor = FakeExtractor(source=expected)

    monkeypatch.setattr(
        module,
        "REDDIT_EXTRACTOR",
        extractor
    )

    result = module.load_reddit_source()

    assert result == expected
    assert extractor.reload_calls == 1


def test_extract_articles_from_source_delegates_to_social_engine(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    source = {
        "source_id": "reddit"
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
            "adapter": module.REDDIT_ADAPTER
        }
    ]


def test_extract_all_articles_delegates_to_extractor(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = object()
    extractor = FakeExtractor(result=expected)

    monkeypatch.setattr(
        module,
        "REDDIT_EXTRACTOR",
        extractor
    )

    result = module.extract_all_articles()

    assert result is expected
    assert extractor.run_calls == 1