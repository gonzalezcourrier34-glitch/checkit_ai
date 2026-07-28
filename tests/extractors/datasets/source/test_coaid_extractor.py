"""Tests légers de l'extracteur source CoAID."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import src.extractors.datasets.source.coaid_extractor as module


# Détection des fichiers

@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("NewsFake.csv", "newsfake"),
        ("News Fake.csv", "newsfake"),
        ("News-Fake.csv", "newsfake"),
        ("News_Fake.csv", "newsfake"),
        (" Claim Real .CSV", "claimreal")
    ]
)
def test_normalize_filename_for_detection(
    filename: str,
    expected: str
) -> None:
    assert module.normalize_filename_for_detection(
        Path(filename)
    ) == expected


@pytest.mark.parametrize(
    "filename",
    [
        "NewsFakeTweet.csv",
        "ClaimRealReply.csv",
        "NewsRealRetweet.csv",
        "ClaimFakeEngagement.csv",
        "NewsFakeUser.csv",
        "ClaimRealSocial.csv"
    ]
)
def test_is_ignored_social_file(filename: str) -> None:
    assert module.is_ignored_social_file(Path(filename)) is True


@pytest.mark.parametrize(
    "filename",
    [
        "NewsFake.csv",
        "NewsReal.csv",
        "ClaimFake.csv",
        "ClaimReal.csv"
    ]
)
def test_is_supported_coaid_file_accepts_expected_files(
    filename: str,
    tmp_path: Path
) -> None:
    filepath = tmp_path / filename
    filepath.write_text(
        "title,content",
        encoding="utf-8"
    )

    assert module.is_supported_coaid_file(filepath) is True


@pytest.mark.parametrize(
    "filename",
    [
        "NewsFakeTweet.csv",
        "dataset.csv",
        "NewsFake.json"
    ]
)
def test_is_supported_coaid_file_rejects_invalid_files(
    filename: str,
    tmp_path: Path
) -> None:
    filepath = tmp_path / filename
    filepath.write_text(
        "content",
        encoding="utf-8"
    )

    assert module.is_supported_coaid_file(filepath) is False


def test_find_coaid_files_returns_supported_files(
    tmp_path: Path
) -> None:
    news_file = tmp_path / "NewsFake.csv"
    claim_file = tmp_path / "nested" / "ClaimReal.csv"
    social_file = tmp_path / "NewsFakeTweet.csv"
    invalid_file = tmp_path / "dataset.csv"

    claim_file.parent.mkdir()

    for filepath in (
        news_file,
        claim_file,
        social_file,
        invalid_file
    ):
        filepath.write_text(
            "title,content",
            encoding="utf-8"
        )

    result = module.find_coaid_files(
        tmp_path,
        {}
    )

    assert result == sorted(
        [
            claim_file,
            news_file
        ],
        key=lambda filepath: str(filepath).lower()
    )


def test_find_coaid_files_uses_configured_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    configured_file = tmp_path / "NewsFake.csv"
    configured_file.write_text(
        "title,content",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        module,
        "resolve_configured_dataset_file",
        lambda *args: configured_file
    )

    result = module.find_coaid_files(
        tmp_path,
        {
            "filename": "NewsFake.csv"
        }
    )

    assert result == [
        configured_file
    ]


def test_find_coaid_files_rejects_invalid_configured_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    configured_file = tmp_path / "dataset.csv"
    configured_file.write_text(
        "title,content",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        module,
        "resolve_configured_dataset_file",
        lambda *args: configured_file
    )

    assert module.find_coaid_files(
        tmp_path,
        {
            "filename": "dataset.csv"
        }
    ) == []


# Métadonnées des fichiers

@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("NewsFake.csv", "fake"),
        ("ClaimFake.csv", "fake"),
        ("NewsReal.csv", "real"),
        ("ClaimReal.csv", "real"),
        ("dataset.csv", "")
    ]
)
def test_get_coaid_label_from_file(
    filename: str,
    expected: str
) -> None:
    assert module.get_coaid_label_from_file(
        Path(filename)
    ) == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("NewsFake.csv", "news"),
        ("NewsReal.csv", "news"),
        ("ClaimFake.csv", "claim"),
        ("ClaimReal.csv", "claim"),
        ("dataset.csv", "")
    ]
)
def test_get_coaid_content_type_from_file(
    filename: str,
    expected: str
) -> None:
    assert module.get_coaid_content_type_from_file(
        Path(filename)
    ) == expected


def test_get_collection_period_returns_nearest_dated_directory() -> None:
    filepath = (
        Path("datasets")
        / "2020"
        / "05-01"
        / "NewsFake.csv"
    )

    assert module.get_collection_period(filepath) == "05-01"


def test_get_collection_period_returns_empty_without_date() -> None:
    filepath = (
        Path("datasets")
        / "coaid"
        / "NewsFake.csv"
    )

    assert module.get_collection_period(filepath) == ""


# Lecture du dataset

def test_iter_coaid_items_reads_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset_file = tmp_path / "2020-05" / "NewsFake.csv"
    dataset_file.parent.mkdir()

    pd.DataFrame(
        [
            {
                "Title": "Premier article",
                "Content": "Premier contenu"
            },
            {
                "Title": "Deuxième article",
                "Content": "Deuxième contenu"
            }
        ]
    ).to_csv(
        dataset_file,
        index=False
    )

    monkeypatch.setattr(
        module,
        "get_dataset_chunk_size",
        lambda *args: 1
    )

    items = list(
        module.iter_coaid_items(
            [
                dataset_file
            ],
            {}
        )
    )

    assert len(items) == 2

    first_identifier, first_index, first_row = items[0]
    second_identifier, second_index, second_row = items[1]

    assert first_identifier == "NewsFake.csv:0"
    assert first_index == 0
    assert first_row["title"] == "Premier article"
    assert first_row["content"] == "Premier contenu"
    assert first_row["_label"] == "fake"
    assert first_row["_content_type"] == "news"
    assert first_row["_source_file"] == "NewsFake.csv"
    assert first_row["_collection_period"] == "2020-05"
    assert first_row["_row_index"] == 0

    assert second_identifier == "NewsFake.csv:1"
    assert second_index == 1
    assert second_row["_row_index"] == 1


def test_iter_coaid_items_skips_unclassified_file(
    tmp_path: Path
) -> None:
    dataset_file = tmp_path / "dataset.csv"
    dataset_file.write_text(
        "title,content\nArticle,Contenu",
        encoding="utf-8"
    )

    assert list(
        module.iter_coaid_items(
            [
                dataset_file
            ],
            {}
        )
    ) == []


def test_iter_coaid_items_continues_after_read_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    first_file = tmp_path / "NewsFake.csv"
    second_file = tmp_path / "ClaimReal.csv"

    original_read_csv = module.pd.read_csv

    def fake_read_csv(
        filepath: Path,
        **kwargs: Any
    ) -> Any:
        if filepath == first_file:
            raise pd.errors.ParserError("CSV invalide")

        return original_read_csv(
            filepath,
            **kwargs
        )

    second_file.write_text(
        "claim,content\nAffirmation,Contenu valide",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        module.pd,
        "read_csv",
        fake_read_csv
    )

    items = list(
        module.iter_coaid_items(
            [
                first_file,
                second_file
            ],
            {}
        )
    )

    assert len(items) == 1
    assert items[0][0] == "ClaimReal.csv:0"
    assert items[0][2]["_label"] == "real"
    assert items[0][2]["_content_type"] == "claim"


# Valeurs métier

@pytest.mark.parametrize(
    ("row", "item_identifier", "expected"),
    [
        (
            {
                "id": "123"
            },
            "file.csv:0",
            "coaid:123"
        ),
        (
            {
                "news_id": "news-42"
            },
            "file.csv:0",
            "coaid:news-42"
        ),
        (
            {
                "url": "https://example.com/article"
            },
            "file.csv:0",
            "coaid:https://example.com/article"
        ),
        (
            {
                "_source_file": "NewsFake.csv"
            },
            "NewsFake.csv:3",
            "coaid:NewsFake.csv:NewsFake.csv:3"
        )
    ]
)
def test_build_coaid_identifier(
    row: dict[str, Any],
    item_identifier: str,
    expected: str
) -> None:
    assert module.build_coaid_identifier(
        row,
        item_identifier
    ) == expected


def test_get_coaid_category_uses_row_category() -> None:
    assert module.get_coaid_category(
        {
            "category": " Public Health "
        },
        {
            "category": "configured"
        }
    ) == "Public Health"


def test_get_coaid_category_uses_source_category() -> None:
    assert module.get_coaid_category(
        {},
        {
            "category": "medicine"
        }
    ) == "medicine"


def test_get_coaid_category_uses_health_by_default() -> None:
    assert module.get_coaid_category(
        {},
        {}
    ) == "health"


def test_get_coaid_role_uses_configured_role() -> None:
    assert module.get_coaid_role(
        {},
        {
            "role": "claim_reference"
        }
    ) == "claim_reference"


def test_get_coaid_role_uses_default_role() -> None:
    assert module.get_coaid_role(
        {},
        {}
    ) == "labeled_reference"


# Construction d'article

def test_build_coaid_article_returns_empty_for_invalid_item() -> None:
    assert module.build_coaid_article(
        item="invalid",
        item_index=0,
        item_identifier="item-0",
        source={}
    ) == {}


def test_build_coaid_article_builds_expected_article(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    received: dict[str, Any] = {}

    def fake_build_standard_article(
        **kwargs: Any
    ) -> dict[str, Any]:
        received.update(kwargs)
        return kwargs

    monkeypatch.setattr(
        module,
        "build_standard_article",
        fake_build_standard_article
    )

    item = {
        "id": "123",
        "title": "Titre CoAID",
        "content": "Contenu de l'article CoAID",
        "image_url": "https://example.com/image.jpg",
        "url": "https://example.com/article",
        "publish_date": "2020-05-01",
        "author": "Auteur",
        "category": "health",
        "_label": "FAKE"
    }

    result = module.build_coaid_article(
        item=item,
        item_index=4,
        item_identifier="NewsFake.csv:4",
        source={
            "name": "CoAID Dataset",
            "language": "en",
            "role": "labeled_reference"
        }
    )

    assert result == received
    assert received["identifier"] == "coaid:123"
    assert received["source"] == "CoAID Dataset"
    assert received["title"] == "Titre CoAID"
    assert received["text"] == "Contenu de l'article CoAID"
    assert received["image_url"] == "https://example.com/image.jpg"
    assert received["image_path"] == ""
    assert received["published_at"] == "2020-05-01"
    assert received["url"] == "https://example.com/article"
    assert received["author"] == "Auteur"
    assert received["language"] == "en"
    assert received["category"] == "health"
    assert received["label"] == "fake"
    assert received["dataset_role"] == "labeled_reference"


def test_build_coaid_article_uses_default_source_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: kwargs
    )

    result = module.build_coaid_article(
        item={
            "title": "Titre",
            "content": "Contenu",
            "_label": "real"
        },
        item_index=0,
        item_identifier="NewsReal.csv:0",
        source={}
    )

    assert result["source"] == "CoAID"
    assert result["language"] == "en"
    assert result["category"] == "health"
    assert result["dataset_role"] == "labeled_reference"


# Validation spécifique

@pytest.mark.parametrize(
    "item",
    [
        None,
        [],
        "ligne",
        42
    ]
)
def test_validate_coaid_item_rejects_invalid_item(
    item: Any
) -> None:
    assert module.validate_coaid_item(
        item,
        {},
        {}
    ) == (
        False,
        "ligne_coaid_invalide"
    )


@pytest.mark.parametrize(
    "label",
    [
        "",
        "unknown",
        "partially_fake"
    ]
)
def test_validate_coaid_item_rejects_invalid_label(
    label: str
) -> None:
    assert module.validate_coaid_item(
        {
            "_label": label,
            "_content_type": "news",
            "content": "Contenu"
        },
        {},
        {}
    ) == (
        False,
        "label_coaid_invalide"
    )


@pytest.mark.parametrize(
    "content_type",
    [
        "",
        "article",
        "tweet"
    ]
)
def test_validate_coaid_item_rejects_invalid_content_type(
    content_type: str
) -> None:
    assert module.validate_coaid_item(
        {
            "_label": "fake",
            "_content_type": content_type,
            "content": "Contenu"
        },
        {},
        {}
    ) == (
        False,
        "type_contenu_coaid_invalide"
    )


def test_validate_coaid_item_rejects_missing_content() -> None:
    assert module.validate_coaid_item(
        {
            "_label": "real",
            "_content_type": "claim"
        },
        {},
        {}
    ) == (
        False,
        "contenu_coaid_absent"
    )


@pytest.mark.parametrize(
    ("label", "content_type"),
    [
        ("fake", "news"),
        ("fake", "claim"),
        ("real", "news"),
        ("real", "claim"),
        (" FAKE ", " NEWS "),
        (" REAL ", " CLAIM ")
    ]
)
def test_validate_coaid_item_accepts_valid_item(
    label: str,
    content_type: str
) -> None:
    assert module.validate_coaid_item(
        {
            "_label": label,
            "_content_type": content_type,
            "content": "Contenu CoAID"
        },
        {},
        {}
    ) == (
        True,
        ""
    )


def test_validate_coaid_item_accepts_title_as_content() -> None:
    assert module.validate_coaid_item(
        {
            "_label": "fake",
            "_content_type": "claim",
            "claim": "Affirmation à vérifier"
        },
        {},
        {}
    ) == (
        True,
        ""
    )


# Adaptateur CoAID

def test_coaid_adapter_configuration() -> None:
    adapter = module.COAID_ADAPTER

    assert adapter.source_id == "coaid"
    assert adapter.default_name == "CoAID"
    assert adapter.supported_extensions == frozenset({
        ".csv"
    })
    assert adapter.find_files is module.find_coaid_files
    assert adapter.iter_items is module.iter_coaid_items
    assert adapter.build_article is module.build_coaid_article
    assert adapter.validate_item is module.validate_coaid_item