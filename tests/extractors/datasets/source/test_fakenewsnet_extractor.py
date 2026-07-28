"""Tests légers de l'extracteur source FakeNewsNet."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any

import pytest

import src.extractors.datasets.source.fakenewsnet_extractor as module


# Détection des fichiers

@pytest.mark.parametrize(
    "filename",
    [
        "news content.json",
        "news_content.json",
        "content.json",
        "NEWS_CONTENT.JSON"
    ]
)
def test_is_fakenewsnet_json_file_accepts_expected_names(
    filename: str,
    tmp_path: Path
) -> None:
    filepath = tmp_path / filename
    filepath.write_text(
        "{}",
        encoding="utf-8"
    )

    assert module.is_fakenewsnet_json_file(filepath) is True


@pytest.mark.parametrize(
    "filename",
    [
        "article.json",
        "news.json",
        "content.csv",
        "news_content.txt"
    ]
)
def test_is_fakenewsnet_json_file_rejects_invalid_files(
    filename: str,
    tmp_path: Path
) -> None:
    filepath = tmp_path / filename
    filepath.write_text(
        "{}",
        encoding="utf-8"
    )

    assert module.is_fakenewsnet_json_file(filepath) is False


@pytest.mark.parametrize(
    "filename",
    [
        "gossipcop_fake.csv",
        "gossipcop_real.csv",
        "politifact_fake.csv",
        "politifact_real.csv",
        "POLITIFACT_FAKE.CSV"
    ]
)
def test_is_fakenewsnet_csv_file_accepts_expected_names(
    filename: str,
    tmp_path: Path
) -> None:
    filepath = tmp_path / filename
    filepath.write_text(
        "title,text",
        encoding="utf-8"
    )

    assert module.is_fakenewsnet_csv_file(filepath) is True


@pytest.mark.parametrize(
    "filename",
    [
        "dataset.csv",
        "gossipcop.csv",
        "politifact_fake.json",
        "gossipcop_false.csv"
    ]
)
def test_is_fakenewsnet_csv_file_rejects_invalid_files(
    filename: str,
    tmp_path: Path
) -> None:
    filepath = tmp_path / filename
    filepath.write_text(
        "title,text",
        encoding="utf-8"
    )

    assert module.is_fakenewsnet_csv_file(filepath) is False


def test_is_fakenewsnet_content_file_accepts_json_and_csv(
    tmp_path: Path
) -> None:
    json_file = tmp_path / "content.json"
    csv_file = tmp_path / "gossipcop_fake.csv"

    json_file.write_text(
        "{}",
        encoding="utf-8"
    )
    csv_file.write_text(
        "title,text",
        encoding="utf-8"
    )

    assert module.is_fakenewsnet_content_file(json_file) is True
    assert module.is_fakenewsnet_content_file(csv_file) is True


def test_find_fakenewsnet_files_returns_recognized_files(
    tmp_path: Path
) -> None:
    json_file = (
        tmp_path
        / "gossipcop"
        / "fake"
        / "article"
        / "news content.json"
    )
    csv_file = tmp_path / "politifact_real.csv"
    ignored_file = tmp_path / "dataset.csv"

    json_file.parent.mkdir(parents=True)

    json_file.write_text(
        "{}",
        encoding="utf-8"
    )
    csv_file.write_text(
        "title,text",
        encoding="utf-8"
    )
    ignored_file.write_text(
        "title,text",
        encoding="utf-8"
    )

    result = module.find_fakenewsnet_files(
        tmp_path,
        {}
    )

    assert result == sorted(
        [
            json_file,
            csv_file
        ],
        key=lambda filepath: str(filepath).lower()
    )


def test_find_fakenewsnet_files_uses_configured_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    configured_file = tmp_path / "gossipcop_fake.csv"
    configured_file.write_text(
        "title,text",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        module,
        "resolve_configured_dataset_file",
        lambda *args: configured_file
    )

    result = module.find_fakenewsnet_files(
        tmp_path,
        {
            "filename": "gossipcop_fake.csv"
        }
    )

    assert result == [
        configured_file
    ]


def test_find_fakenewsnet_files_rejects_unrecognized_configured_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    configured_file = tmp_path / "dataset.csv"
    configured_file.write_text(
        "title,text",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        module,
        "resolve_configured_dataset_file",
        lambda *args: configured_file
    )

    assert module.find_fakenewsnet_files(
        tmp_path,
        {
            "filename": "dataset.csv"
        }
    ) == []


# Valeurs extraites des chemins

@pytest.mark.parametrize(
    ("filepath", "expected"),
    [
        (
            Path("gossipcop/fake/article/content.json"),
            "fake"
        ),
        (
            Path("politifact/real/article/content.json"),
            "real"
        ),
        (
            Path("gossipcop_fake.csv"),
            "fake"
        ),
        (
            Path("politifact_real.csv"),
            "real"
        ),
        (
            Path("dataset/content.json"),
            ""
        )
    ]
)
def test_extract_raw_label_from_path(
    filepath: Path,
    expected: str
) -> None:
    assert module.extract_raw_label_from_path(filepath) == expected


@pytest.mark.parametrize(
    ("filepath", "expected"),
    [
        (
            Path("gossipcop/fake/article/content.json"),
            "gossipcop"
        ),
        (
            Path("politifact/real/article/content.json"),
            "politifact"
        ),
        (
            Path("gossipcop_fake.csv"),
            "gossipcop"
        ),
        (
            Path("politifact_real.csv"),
            "politifact"
        ),
        (
            Path("dataset/content.json"),
            ""
        )
    ]
)
def test_extract_category_from_path(
    filepath: Path,
    expected: str
) -> None:
    assert module.extract_category_from_path(filepath) == expected


def test_get_path_value_is_case_insensitive() -> None:
    filepath = Path("GossipCop") / "Fake" / "CONTENT.JSON"

    assert module.get_path_value(
        filepath,
        frozenset({
            "gossipcop",
            "politifact"
        })
    ) == "gossipcop"


# Chargement JSON

def test_load_fakenewsnet_json_returns_mapping(
    tmp_path: Path
) -> None:
    filepath = tmp_path / "content.json"
    filepath.write_text(
        json.dumps(
            {
                "title": "Article",
                "text": "Contenu"
            }
        ),
        encoding="utf-8"
    )

    result = module.load_fakenewsnet_json(filepath)

    assert result == {
        "title": "Article",
        "text": "Contenu"
    }


def test_load_fakenewsnet_json_rejects_non_mapping(
    tmp_path: Path
) -> None:
    filepath = tmp_path / "content.json"
    filepath.write_text(
        json.dumps(
            [
                {
                    "title": "Article"
                }
            ]
        ),
        encoding="utf-8"
    )

    assert module.load_fakenewsnet_json(filepath) == {}


def test_load_fakenewsnet_json_rejects_invalid_json(
    tmp_path: Path
) -> None:
    filepath = tmp_path / "content.json"
    filepath.write_text(
        "{invalid}",
        encoding="utf-8"
    )

    assert module.load_fakenewsnet_json(filepath) == {}


def test_load_fakenewsnet_json_retries_utf8_sig(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    filepath = tmp_path / "content.json"
    calls: list[str] = []

    def fake_load_json_with_encoding(
        path: Path,
        encoding: str
    ) -> Any:
        calls.append(encoding)

        if encoding == "utf-8":
            raise UnicodeDecodeError(
                "utf-8",
                b"x",
                0,
                1,
                "invalid"
            )

        return {
            "title": "Article"
        }

    monkeypatch.setattr(
        module,
        "load_json_with_encoding",
        fake_load_json_with_encoding
    )

    result = module.load_fakenewsnet_json(filepath)

    assert result == {
        "title": "Article"
    }
    assert calls == [
        "utf-8",
        "utf-8-sig"
    ]


# Lecture CSV

def test_detect_csv_encoding_returns_utf8(
    tmp_path: Path
) -> None:
    filepath = tmp_path / "gossipcop_fake.csv"
    filepath.write_text(
        "title,text\nTitre,Contenu",
        encoding="utf-8"
    )

    assert module.detect_csv_encoding(filepath) == "utf-8"


def test_iter_fakenewsnet_csv_rows_reads_rows(
    tmp_path: Path
) -> None:
    filepath = tmp_path / "gossipcop_fake.csv"
    filepath.write_text(
        "Title,Text,URL\n"
        "Premier titre,Premier contenu,https://example.com/1\n"
        "Deuxième titre,Deuxième contenu,https://example.com/2\n",
        encoding="utf-8"
    )

    rows = list(
        module.iter_fakenewsnet_csv_rows(filepath)
    )

    assert len(rows) == 2

    first_identifier, first_index, first_row = rows[0]
    second_identifier, second_index, second_row = rows[1]

    assert first_identifier == f"{filepath}:0"
    assert first_index == 0
    assert first_row["Title"] == "Premier titre"
    assert first_row["Text"] == "Premier contenu"
    assert first_row["_filepath"] == filepath
    assert first_row["_label"] == "fake"
    assert first_row["_category"] == "gossipcop"

    assert second_identifier == f"{filepath}:1"
    assert second_index == 1
    assert second_row["Title"] == "Deuxième titre"


def test_iter_fakenewsnet_csv_rows_returns_empty_without_encoding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    filepath = tmp_path / "gossipcop_fake.csv"

    monkeypatch.setattr(
        module,
        "detect_csv_encoding",
        lambda path: ""
    )

    assert list(
        module.iter_fakenewsnet_csv_rows(filepath)
    ) == []


def test_iter_fakenewsnet_items_combines_json_and_csv(
    tmp_path: Path
) -> None:
    json_file = (
        tmp_path
        / "gossipcop"
        / "fake"
        / "article"
        / "content.json"
    )
    csv_file = tmp_path / "politifact_real.csv"

    json_file.parent.mkdir(parents=True)

    json_file.write_text(
        "{}",
        encoding="utf-8"
    )
    csv_file.write_text(
        "title,text\nTitre,Contenu",
        encoding="utf-8"
    )

    items = list(
        module.iter_fakenewsnet_items(
            [
                json_file,
                csv_file
            ],
            {}
        )
    )

    assert len(items) == 2

    assert items[0] == (
        str(json_file),
        0,
        json_file
    )

    assert items[1][0] == f"{csv_file}:0"
    assert items[1][1] == 1
    assert items[1][2]["_filepath"] == csv_file


# Normalisation des collections

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            " Alice ",
            "Alice"
        ),
        (
            [
                "Alice",
                "Bob",
                "Alice",
                ""
            ],
            "Alice, Bob"
        ),
        (
            (
                "Alice",
                "Bob"
            ),
            "Alice, Bob"
        ),
        (
            None,
            ""
        )
    ]
)
def test_normalize_string_collection(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_string_collection(value) == expected


# Images

def test_get_primary_image_url_uses_direct_field() -> None:
    item = {
        "top_img": "https://example.com/image.jpg",
        "images": [
            "https://example.com/fallback.jpg"
        ]
    }

    assert module.get_primary_image_url(item) == (
        "https://example.com/image.jpg"
    )


def test_get_primary_image_url_uses_images_collection() -> None:
    item = {
        "images": [
            "",
            "example.com/image.jpg"
        ]
    }

    assert module.get_primary_image_url(item) == (
        "https://example.com/image.jpg"
    )

def test_get_primary_image_url_returns_empty_without_valid_image() -> None:
    assert module.get_primary_image_url(
        {
            "images": "invalid"
        }
    ) == ""


def test_find_local_image_returns_first_supported_image(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    content_file = tmp_path / "content.json"
    first_image = tmp_path / "a.jpg"
    second_image = tmp_path / "b.png"
    ignored_file = tmp_path / "notes.txt"

    content_file.write_text(
        "{}",
        encoding="utf-8"
    )
    first_image.write_bytes(b"image")
    second_image.write_bytes(b"image")
    ignored_file.write_text(
        "notes",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        module,
        "make_project_relative_path",
        lambda filepath: f"relative/{filepath.name}"
    )

    assert module.find_local_image(content_file) == "relative/a.jpg"


def test_find_local_image_returns_empty_without_image(
    tmp_path: Path
) -> None:
    content_file = tmp_path / "content.json"
    content_file.write_text(
        "{}",
        encoding="utf-8"
    )

    assert module.find_local_image(content_file) == ""


# Identifiants

def test_get_fakenewsnet_identifier_uses_url() -> None:
    filepath = Path(
        "gossipcop/fake/article/content.json"
    )

    assert module.get_fakenewsnet_identifier(
        filepath,
        "https://example.com/article",
        "123"
    ) == "https://example.com/article"


def test_get_fakenewsnet_identifier_uses_fallback() -> None:
    filepath = Path(
        "gossipcop/fake/article/content.json"
    )

    assert module.get_fakenewsnet_identifier(
        filepath,
        "",
        "123"
    ) == "fakenewsnet:gossipcop:fake:123"


def test_get_fakenewsnet_identifier_uses_path_as_last_fallback(
    tmp_path: Path
) -> None:
    filepath = tmp_path / "content.json"

    result = module.get_fakenewsnet_identifier(
        filepath,
        ""
    )

    assert result.startswith("fakenewsnet:")
    assert str(filepath.resolve()) in result


# Construction des articles

def test_build_fakenewsnet_article_from_file_returns_empty_for_invalid_json(
    tmp_path: Path
) -> None:
    filepath = tmp_path / "content.json"
    filepath.write_text(
        "{invalid}",
        encoding="utf-8"
    )

    assert module.build_fakenewsnet_article_from_file(
        filepath,
        {}
    ) == {}


def test_build_fakenewsnet_article_from_file_builds_article(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    filepath = (
        tmp_path
        / "gossipcop"
        / "fake"
        / "article"
        / "content.json"
    )
    filepath.parent.mkdir(parents=True)
    filepath.write_text(
        "{}",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        module,
        "load_fakenewsnet_json",
        lambda path: {
            "title": "Titre FakeNewsNet",
            "text": "Contenu FakeNewsNet",
            "url": "https://example.com/article",
            "top_img": "https://example.com/image.jpg",
            "authors": [
                "Alice",
                "Bob"
            ],
            "publish_date": "2020-01-01"
        }
    )
    monkeypatch.setattr(
        module,
        "find_local_image",
        lambda path: "images/local.jpg"
    )
    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: kwargs
    )

    result = module.build_fakenewsnet_article_from_file(
        filepath,
        {
            "name": "FakeNewsNet Dataset",
            "language": "en"
        }
    )

    assert result["identifier"] == "https://example.com/article"
    assert result["source"] == "FakeNewsNet Dataset"
    assert result["title"] == "Titre FakeNewsNet"
    assert result["text"] == "Contenu FakeNewsNet"
    assert result["image_url"] == "https://example.com/image.jpg"
    assert result["image_path"] == "images/local.jpg"
    assert result["published_at"] == "2020-01-01"
    assert result["url"] == "https://example.com/article"
    assert result["author"] == "Alice, Bob"
    assert result["language"] == "en"
    assert result["category"] == "gossipcop"
    assert result["label"] == "false"
    assert result["dataset_role"] == "labeled_reference"
    assert result["dataset_label_raw"] == "fake"


def test_build_fakenewsnet_article_from_row_returns_empty_without_path() -> None:
    assert module.build_fakenewsnet_article_from_row(
        {
            "title": "Titre"
        },
        {}
    ) == {}


def test_build_fakenewsnet_article_from_row_builds_article(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    filepath = tmp_path / "politifact_real.csv"
    filepath.write_text(
        "title,text",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: kwargs
    )

    item = {
        "_filepath": filepath,
        "_label": "real",
        "_category": "politifact",
        "id": "article-42",
        "title": "Titre Politifact",
        "text": "Contenu Politifact",
        "url": "https://example.com/article",
        "image_url": "https://example.com/image.jpg",
        "author": "Auteur",
        "published_at": "2020-02-01"
    }

    result = module.build_fakenewsnet_article_from_row(
        item,
        {}
    )

    assert result["identifier"] == "https://example.com/article"
    assert result["source"] == "FakeNewsNet"
    assert result["title"] == "Titre Politifact"
    assert result["text"] == "Contenu Politifact"
    assert result["image_url"] == "https://example.com/image.jpg"
    assert result["image_path"] == ""
    assert result["url"] == "https://example.com/article"
    assert result["author"] == "Auteur"
    assert result["language"] == "en"
    assert result["category"] == "politifact"
    assert result["label"] == "true"
    assert result["dataset_role"] == "labeled_reference"
    assert result["dataset_label_raw"] == "real"


@pytest.mark.parametrize(
    ("item", "expected_function"),
    [
        (
            Path("content.json"),
            "file"
        ),
        (
            {
                "_filepath": Path("gossipcop_fake.csv")
            },
            "row"
        )
    ]
)
def test_build_fakenewsnet_article_delegates_by_item_type(
    item: Any,
    expected_function: str,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_fakenewsnet_article_from_file",
        lambda filepath, source: {
            "type": "file"
        }
    )
    monkeypatch.setattr(
        module,
        "build_fakenewsnet_article_from_row",
        lambda row, source: {
            "type": "row"
        }
    )

    result = module.build_fakenewsnet_article(
        item,
        0,
        "identifier",
        {}
    )

    assert result == {
        "type": expected_function
    }


def test_build_fakenewsnet_article_returns_empty_for_invalid_item() -> None:
    assert module.build_fakenewsnet_article(
        "invalid",
        0,
        "identifier",
        {}
    ) == {}


# Validation

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("fake", True),
        ("real", True),
        ("", False),
        ("unknown", False)
    ]
)
def test_validate_fakenewsnet_raw_label(
    value: Any,
    expected: bool
) -> None:
    assert module.validate_fakenewsnet_raw_label(value) is expected

def test_validate_fakenewsnet_item_accepts_valid_json_file(
    tmp_path: Path
) -> None:
    filepath = (
        tmp_path
        / "gossipcop"
        / "fake"
        / "article"
        / "content.json"
    )
    filepath.parent.mkdir(parents=True)
    filepath.write_text(
        "{}",
        encoding="utf-8"
    )

    assert module.validate_fakenewsnet_item(
        filepath,
        {},
        {}
    ) == (
        True,
        ""
    )


def test_validate_fakenewsnet_item_rejects_missing_file(
    tmp_path: Path
) -> None:
    filepath = (
        tmp_path
        / "gossipcop"
        / "fake"
        / "content.json"
    )

    assert module.validate_fakenewsnet_item(
        filepath,
        {},
        {}
    ) == (
        False,
        "fichier_fakenewsnet_absent"
    )


def test_validate_fakenewsnet_item_rejects_json_without_label(
    tmp_path: Path
) -> None:
    filepath = tmp_path / "gossipcop" / "content.json"
    filepath.parent.mkdir()
    filepath.write_text(
        "{}",
        encoding="utf-8"
    )

    assert module.validate_fakenewsnet_item(
        filepath,
        {},
        {}
    ) == (
        False,
        "label_arborescence_absent"
    )


def test_validate_fakenewsnet_item_accepts_valid_csv_row(
    tmp_path: Path
) -> None:
    filepath = tmp_path / "gossipcop_fake.csv"
    filepath.write_text(
        "title,text",
        encoding="utf-8"
    )

    item = {
        "_filepath": filepath,
        "_label": "fake",
        "_category": "gossipcop",
        "title": "Titre",
        "text": "Contenu"
    }

    assert module.validate_fakenewsnet_item(
        item,
        {},
        {}
    ) == (
        True,
        ""
    )


def test_validate_fakenewsnet_item_rejects_csv_row_without_content(
    tmp_path: Path
) -> None:
    filepath = tmp_path / "gossipcop_fake.csv"
    filepath.write_text(
        "title,text",
        encoding="utf-8"
    )

    item = {
        "_filepath": filepath,
        "_label": "fake",
        "_category": "gossipcop"
    }

    assert module.validate_fakenewsnet_item(
        item,
        {},
        {}
    ) == (
        False,
        "contenu_fakenewsnet_absent"
    )


def test_validate_fakenewsnet_item_rejects_invalid_item() -> None:
    assert module.validate_fakenewsnet_item(
        "invalid",
        {},
        {}
    ) == (
        False,
        "element_fakenewsnet_invalide"
    )


# Adaptateur FakeNewsNet

def test_fakenewsnet_adapter_configuration() -> None:
    adapter = module.FAKENEWSNET_ADAPTER

    assert adapter.source_id == "fakenewsnet"
    assert adapter.default_name == "FakeNewsNet"
    assert adapter.supported_extensions == frozenset({
        ".json",
        ".csv"
    })
    assert adapter.find_files is module.find_fakenewsnet_files
    assert adapter.iter_items is module.iter_fakenewsnet_items
    assert adapter.build_article is module.build_fakenewsnet_article
    assert adapter.validate_item is module.validate_fakenewsnet_item