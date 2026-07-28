"""Tests légers de l'extracteur source ISOT."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import src.extractors.datasets.source.isot_extractor as module


# Recherche des fichiers

def test_find_expected_isot_files_returns_standard_files(
    tmp_path: Path
) -> None:
    fake_file = tmp_path / "Fake.csv"
    true_file = tmp_path / "nested" / "True.csv"
    ignored_file = tmp_path / "Other.csv"

    true_file.parent.mkdir()

    fake_file.write_text(
        "title,text",
        encoding="utf-8"
    )
    true_file.write_text(
        "title,text",
        encoding="utf-8"
    )
    ignored_file.write_text(
        "title,text",
        encoding="utf-8"
    )

    result = module.find_expected_isot_files(tmp_path)

    assert result == [
        fake_file,
        true_file
    ]


def test_find_expected_isot_files_is_case_insensitive(
    tmp_path: Path
) -> None:
    fake_file = tmp_path / "FAKE.CSV"
    true_file = tmp_path / "true.csv"

    fake_file.write_text(
        "title,text",
        encoding="utf-8"
    )
    true_file.write_text(
        "title,text",
        encoding="utf-8"
    )

    assert module.find_expected_isot_files(tmp_path) == [
        fake_file,
        true_file
    ]


def test_find_expected_isot_files_returns_empty_on_traversal_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_rglob(
        path: Path,
        pattern: str
    ) -> Any:
        raise OSError("Accès refusé")

    monkeypatch.setattr(
        Path,
        "rglob",
        fake_rglob
    )

    assert module.find_expected_isot_files(tmp_path) == []


def test_find_isot_files_uses_configured_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    configured_file = tmp_path / "Fake.csv"
    configured_file.write_text(
        "title,text",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        module,
        "resolve_configured_dataset_file",
        lambda *args: configured_file
    )

    result = module.find_isot_files(
        tmp_path,
        {
            "filename": "Fake.csv"
        }
    )

    assert result == [
        configured_file
    ]


def test_find_isot_files_rejects_unrecognized_configured_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    configured_file = tmp_path / "articles.csv"
    configured_file.write_text(
        "title,text",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        module,
        "resolve_configured_dataset_file",
        lambda *args: configured_file
    )

    assert module.find_isot_files(
        tmp_path,
        {
            "filename": "articles.csv"
        }
    ) == []


def test_find_isot_files_returns_standard_files_first(
    tmp_path: Path
) -> None:
    fake_file = tmp_path / "Fake.csv"
    true_file = tmp_path / "True.csv"
    other_file = tmp_path / "Other.csv"

    for filepath in (
        fake_file,
        true_file,
        other_file
    ):
        filepath.write_text(
            "title,text",
            encoding="utf-8"
        )

    assert module.find_isot_files(
        tmp_path,
        {}
    ) == [
        fake_file,
        true_file
    ]


def test_find_isot_files_uses_csv_fallback(
    tmp_path: Path
) -> None:
    first_file = tmp_path / "a.csv"
    second_file = tmp_path / "nested" / "b.csv"

    second_file.parent.mkdir()

    first_file.write_text(
        "title,text",
        encoding="utf-8"
    )
    second_file.write_text(
        "title,text",
        encoding="utf-8"
    )

    result = module.find_isot_files(
        tmp_path,
        {}
    )

    assert result == sorted(
        [
            first_file,
            second_file
        ],
        key=lambda filepath: str(filepath).lower()
    )


# Labels

@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        (
            "Fake.csv",
            "fake"
        ),
        (
            "FAKE.CSV",
            "fake"
        ),
        (
            "True.csv",
            "real"
        ),
        (
            "TRUE.CSV",
            "real"
        ),
        (
            "Other.csv",
            ""
        )
    ]
)
def test_get_isot_label_from_file(
    filename: str,
    expected: str
) -> None:
    assert module.get_isot_label_from_file(
        Path(filename)
    ) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("fake", "false"),
        ("false", "false"),
        ("real", "true"),
        ("true", "true"),
        ("unknown", "not_classified")
    ]
)
def test_get_isot_label(
    value: Any,
    expected: str
) -> None:
    assert module.get_isot_label(value) == expected

# Contrôle des colonnes

def test_log_missing_columns_does_not_warn_when_complete(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    dataframe = pd.DataFrame(
        columns=[
            "title",
            "text",
            "subject",
            "date"
        ]
    )
    warnings: list[tuple[Any, ...]] = []

    monkeypatch.setattr(
        module.logger,
        "warning",
        lambda *args: warnings.append(args)
    )

    module.log_missing_columns(
        dataframe,
        Path("Fake.csv")
    )

    assert warnings == []


def test_log_missing_columns_warns_for_missing_columns(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    dataframe = pd.DataFrame(
        columns=[
            "Title",
            "Text"
        ]
    )
    warnings: list[tuple[Any, ...]] = []

    monkeypatch.setattr(
        module.logger,
        "warning",
        lambda *args: warnings.append(args)
    )

    module.log_missing_columns(
        dataframe,
        Path("Fake.csv")
    )

    assert warnings == [
        (
            "Colonnes ISOT absentes dans %s : %s.",
            "Fake.csv",
            "date, subject"
        )
    ]


# Lecture CSV

def test_iter_isot_items_reads_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset_file = tmp_path / "Fake.csv"

    pd.DataFrame(
        [
            {
                "Title": "Premier titre",
                "Text": "Premier contenu",
                "Subject": "politics",
                "Date": "January 1, 2020"
            },
            {
                "Title": "Deuxième titre",
                "Text": "Deuxième contenu",
                "Subject": "worldnews",
                "Date": "January 2, 2020"
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
        module.iter_isot_items(
            [
                dataset_file
            ],
            {}
        )
    )

    assert len(items) == 2

    first_identifier, first_index, first_row = items[0]
    second_identifier, second_index, second_row = items[1]

    assert first_identifier == "Fake.csv:0"
    assert first_index == 0
    assert first_row["title"] == "Premier titre"
    assert first_row["text"] == "Premier contenu"
    assert first_row["subject"] == "politics"
    assert first_row["_label"] == "fake"
    assert first_row["_source_file"] == "Fake.csv"
    assert first_row["_row_index"] == 0

    assert second_identifier == "Fake.csv:1"
    assert second_index == 1
    assert second_row["_row_index"] == 1


def test_iter_isot_items_skips_file_without_known_label(
    tmp_path: Path
) -> None:
    dataset_file = tmp_path / "Other.csv"
    dataset_file.write_text(
        "title,text\nTitre,Contenu",
        encoding="utf-8"
    )

    assert list(
        module.iter_isot_items(
            [
                dataset_file
            ],
            {}
        )
    ) == []


def test_iter_isot_items_continues_after_read_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_file = tmp_path / "Fake.csv"
    true_file = tmp_path / "True.csv"

    true_file.write_text(
        "title,text,subject,date\n"
        "Titre,Contenu,politics,2020-01-01",
        encoding="utf-8"
    )

    original_read_csv = module.pd.read_csv

    def fake_read_csv(
        filepath: Path,
        **kwargs: Any
    ) -> Any:
        if filepath == fake_file:
            raise pd.errors.ParserError("CSV invalide")

        return original_read_csv(
            filepath,
            **kwargs
        )

    monkeypatch.setattr(
        module.pd,
        "read_csv",
        fake_read_csv
    )

    items = list(
        module.iter_isot_items(
            [
                fake_file,
                true_file
            ],
            {}
        )
    )

    assert len(items) == 1
    assert items[0][0] == "True.csv:0"
    assert items[0][2]["_label"] == "real"


# Identifiants et catégories

def test_build_isot_identifier_uses_title() -> None:
    row = {
        "title": "Titre ISOT",
        "_source_file": "Fake.csv"
    }

    assert module.build_isot_identifier(
        row,
        "Fake.csv:0"
    ) == "isot:Fake.csv:Fake.csv:0:Titre ISOT"


def test_build_isot_identifier_without_title() -> None:
    row = {
        "_source_file": "True.csv"
    }

    assert module.build_isot_identifier(
        row,
        "True.csv:2"
    ) == "isot:True.csv:True.csv:2"


def test_get_isot_category_uses_subject() -> None:
    assert module.get_isot_category(
        {
            "subject": " politicsNews "
        },
        {
            "category": "configured"
        }
    ) == "politicsNews"


def test_get_isot_category_uses_configured_category() -> None:
    assert module.get_isot_category(
        {},
        {
            "category": "news"
        }
    ) == "news"


def test_get_isot_category_uses_default() -> None:
    assert module.get_isot_category(
        {},
        {}
    ) == "general"


# Construction d'article

def test_build_isot_article_returns_empty_for_invalid_item() -> None:
    assert module.build_isot_article(
        item="invalid",
        item_index=0,
        item_identifier="Fake.csv:0",
        source={}
    ) == {}


def test_build_isot_article_builds_expected_article(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: kwargs
    )

    item = {
        "title": "Titre ISOT",
        "text": "Contenu ISOT",
        "subject": "politics",
        "date": "January 1, 2020",
        "_label": "fake",
        "_source_file": "Fake.csv"
    }

    result = module.build_isot_article(
        item=item,
        item_index=0,
        item_identifier="Fake.csv:0",
        source={
            "name": "ISOT Dataset",
            "language": "en",
            "role": "labeled_reference"
        }
    )

    assert result["identifier"] == (
        "isot:Fake.csv:Fake.csv:0:Titre ISOT"
    )
    assert result["source"] == "ISOT Dataset"
    assert result["title"] == "Titre ISOT"
    assert result["text"] == "Contenu ISOT"
    assert result["image_url"] == ""
    assert result["image_path"] == ""
    assert result["published_at"] == "January 1, 2020"
    assert result["url"] == ""
    assert result["author"] == ""
    assert result["language"] == "en"
    assert result["category"] == "politics"
    assert result["label"] == "false"
    assert result["dataset_role"] == "labeled_reference"
    assert result["dataset_label_raw"] == "fake"


def test_build_isot_article_uses_default_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: kwargs
    )

    result = module.build_isot_article(
        item={
            "title": "Titre",
            "text": "Contenu",
            "_label": "real",
            "_source_file": "True.csv"
        },
        item_index=0,
        item_identifier="True.csv:0",
        source={}
    )

    assert result["source"] == "ISOT Fake News Dataset"
    assert result["language"] == "en"
    assert result["category"] == "general"
    assert result["dataset_role"] == "labeled_reference"
    assert result["label"] == "true"


# Validation

@pytest.mark.parametrize(
    "item",
    [
        None,
        [],
        "ligne",
        42
    ]
)
def test_validate_isot_item_rejects_invalid_item(
    item: Any
) -> None:
    assert module.validate_isot_item(
        item,
        {},
        {}
    ) == (
        False,
        "ligne_isot_invalide"
    )


@pytest.mark.parametrize(
    "label",
    [
        "",
        "unknown",
        "not_classified"
    ]
)
def test_validate_isot_item_rejects_invalid_label(
    label: str
) -> None:
    assert module.validate_isot_item(
        {
            "_label": label,
            "_source_file": "Fake.csv",
            "title": "Titre",
            "text": "Contenu"
        },
        {},
        {}
    ) == (
        False,
        "label_isot_invalide"
    )


def test_validate_isot_item_rejects_missing_source_file() -> None:
    assert module.validate_isot_item(
        {
            "_label": "fake",
            "title": "Titre",
            "text": "Contenu"
        },
        {},
        {}
    ) == (
        False,
        "fichier_source_absent"
    )


def test_validate_isot_item_rejects_missing_title() -> None:
    assert module.validate_isot_item(
        {
            "_label": "fake",
            "_source_file": "Fake.csv",
            "text": "Contenu"
        },
        {},
        {}
    ) == (
        False,
        "titre_isot_absent"
    )


def test_validate_isot_item_rejects_missing_text() -> None:
    assert module.validate_isot_item(
        {
            "_label": "real",
            "_source_file": "True.csv",
            "title": "Titre"
        },
        {},
        {}
    ) == (
        False,
        "texte_isot_absent"
    )


@pytest.mark.parametrize(
    "label",
    [
        "fake",
        "real"
    ]
)
def test_validate_isot_item_accepts_valid_item(
    label: str
) -> None:
    assert module.validate_isot_item(
        {
            "_label": label,
            "_source_file": "Fake.csv",
            "title": "Titre",
            "text": "Contenu"
        },
        {},
        {}
    ) == (
        True,
        ""
    )


# Adaptateur ISOT

def test_isot_adapter_configuration() -> None:
    adapter = module.ISOT_ADAPTER

    assert adapter.source_id == "isot"
    assert adapter.default_name == "ISOT Fake News Dataset"
    assert adapter.supported_extensions == frozenset({
        ".csv"
    })
    assert adapter.find_files is module.find_isot_files
    assert adapter.iter_items is module.iter_isot_items
    assert adapter.build_article is module.build_isot_article
    assert adapter.validate_item is module.validate_isot_item