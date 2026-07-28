"""Tests légers de l'extracteur source Fakeddit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import src.extractors.datasets.source.fakeddit_extractor as module


# Labels

@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({"2_way_label": "0"}, "false"),
        ({"2_way_label": "1"}, "true"),
        ({"label": "false"}, "false"),
        ({"label": "true"}, "true")
    ]
)

def test_normalize_fakeddit_label(
    row: dict[str, Any],
    expected: str
) -> None:
    assert module.normalize_fakeddit_label(row) == expected


def test_normalize_fakeddit_label_returns_not_classified_for_unknown_label() -> None:
    assert module.normalize_fakeddit_label(
        {
            "label": "unknown"
        }
    ) == "not_classified"


# Recherche des fichiers

def test_find_fakeddit_files_returns_supported_files(
    tmp_path: Path
) -> None:
    csv_file = tmp_path / "train.csv"
    tsv_file = tmp_path / "nested" / "test.tsv"
    ignored_file = tmp_path / "dataset.json"

    tsv_file.parent.mkdir()

    csv_file.write_text(
        "title,text",
        encoding="utf-8"
    )
    tsv_file.write_text(
        "title\ttext",
        encoding="utf-8"
    )
    ignored_file.write_text(
        "{}",
        encoding="utf-8"
    )

    result = module.find_fakeddit_files(
        tmp_path,
        {}
    )

    assert result == sorted(
        [
            csv_file,
            tsv_file
        ],
        key=lambda filepath: str(filepath).lower()
    )


def test_find_fakeddit_files_uses_configured_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    configured_file = tmp_path / "train.tsv"
    configured_file.write_text(
        "title\ttext",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        module,
        "resolve_configured_dataset_file",
        lambda *args: configured_file
    )

    result = module.find_fakeddit_files(
        tmp_path,
        {
            "filename": "train.tsv"
        }
    )

    assert result == [
        configured_file
    ]


def test_find_fakeddit_files_returns_empty_when_configured_file_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "resolve_configured_dataset_file",
        lambda *args: None
    )

    result = module.find_fakeddit_files(
        tmp_path,
        {
            "filename": "missing.csv"
        }
    )

    assert result == []


def test_find_fakeddit_files_raises_runtime_error_on_traversal_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_error = OSError("Accès refusé")

    def fake_rglob(
        path: Path,
        pattern: str
    ) -> Any:
        raise expected_error

    monkeypatch.setattr(
        Path,
        "rglob",
        fake_rglob
    )

    with pytest.raises(
        RuntimeError,
        match="Impossible de parcourir le dossier Fakeddit"
    ) as error_info:
        module.find_fakeddit_files(
            tmp_path,
            {}
        )

    assert error_info.value.__cause__ is expected_error


# Séparateurs

@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        (
            "train.csv",
            ","
        ),
        (
            "train.CSV",
            ","
        ),
        (
            "train.tsv",
            "\t"
        ),
        (
            "train.TSV",
            "\t"
        )
    ]
)
def test_get_separator(
    filename: str,
    expected: str
) -> None:
    assert module.get_separator(
        Path(filename)
    ) == expected


def test_get_separator_rejects_unsupported_format() -> None:
    with pytest.raises(
        ValueError,
        match="Format Fakeddit non pris en charge"
    ):
        module.get_separator(
            Path("train.json")
        )


# Lecture des fichiers

@pytest.mark.parametrize(
    ("filename", "separator"),
    [
        (
            "train.csv",
            ","
        ),
        (
            "train.tsv",
            "\t"
        )
    ]
)
def test_iter_fakeddit_rows_reads_supported_file(
    filename: str,
    separator: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset_file = tmp_path / filename

    pd.DataFrame(
        [
            {
                "Title": "Premier titre",
                "Text": "Premier contenu"
            },
            {
                "Title": "Deuxième titre",
                "Text": "Deuxième contenu"
            }
        ]
    ).to_csv(
        dataset_file,
        index=False,
        sep=separator
    )

    monkeypatch.setattr(
        module,
        "get_dataset_chunk_size",
        lambda *args: 1
    )

    rows = list(
        module.iter_fakeddit_rows(
            [
                dataset_file
            ],
            {}
        )
    )

    assert len(rows) == 2

    first_identifier, first_index, first_row = rows[0]
    second_identifier, second_index, second_row = rows[1]

    assert first_identifier == filename
    assert first_index == 0
    assert first_row["title"] == "Premier titre"
    assert first_row["text"] == "Premier contenu"

    assert second_identifier == filename
    assert second_index == 1
    assert second_row["title"] == "Deuxième titre"
    assert second_row["text"] == "Deuxième contenu"


def test_iter_fakeddit_rows_continues_after_read_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    invalid_file = tmp_path / "invalid.csv"
    valid_file = tmp_path / "valid.csv"

    valid_file.write_text(
        "title,text\nTitre,Contenu",
        encoding="utf-8"
    )

    original_read_csv = module.pd.read_csv

    def fake_read_csv(
        filepath: Path,
        **kwargs: Any
    ) -> Any:
        if filepath == invalid_file:
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

    rows = list(
        module.iter_fakeddit_rows(
            [
                invalid_file,
                valid_file
            ],
            {}
        )
    )

    assert len(rows) == 1
    assert rows[0][0] == "valid.csv"
    assert rows[0][1] == 0
    assert rows[0][2]["title"] == "Titre"


# Construction des articles

def test_build_fakeddit_article_returns_empty_for_invalid_row() -> None:
    assert module.build_fakeddit_article(
        row="invalid",
        row_index=0,
        file_identifier="train.csv",
        source={}
    ) == {}


def test_build_fakeddit_article_builds_expected_article(
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

    row = {
        "id": "abc123",
        "clean_title": "Titre Fakeddit",
        "clean_text": "Contenu Fakeddit",
        "url": "https://example.com/article",
        "image_url": "https://example.com/image.jpg",
        "image_path": "images/article.jpg",
        "created_utc": "1609459200",
        "author": "user42",
        "subreddit": "news",
        "2_way_label": "0"
    }

    result = module.build_fakeddit_article(
        row=row,
        row_index=4,
        file_identifier="train.csv",
        source={
            "name": "Fakeddit Dataset",
            "language": "en",
            "role": "multimodal_reference"
        }
    )

    assert result == received
    assert received["identifier"] == "abc123"
    assert received["source"] == "Fakeddit Dataset"
    assert received["title"] == "Titre Fakeddit"
    assert received["text"] == "Contenu Fakeddit"
    assert received["image_url"] == "https://example.com/image.jpg"
    assert received["image_path"] == "images/article.jpg"
    assert received["published_at"] == "1609459200"
    assert received["url"] == "https://example.com/article"
    assert received["author"] == "user42"
    assert received["language"] == "en"
    assert received["category"] == "news"
    assert received["label"] == "false"
    assert received["dataset_role"] == "multimodal_reference"


def test_build_fakeddit_article_uses_url_as_identifier(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: kwargs
    )

    result = module.build_fakeddit_article(
        row={
            "title": "Titre",
            "text": "Contenu",
            "url": "https://example.com/article",
            "label": "true"
        },
        row_index=2,
        file_identifier="train.csv",
        source={}
    )

    assert result["identifier"] == "https://example.com/article"


def test_build_fakeddit_article_uses_fallback_identifier(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: kwargs
    )

    result = module.build_fakeddit_article(
        row={
            "title": "Titre",
            "text": "Contenu",
            "label": "true"
        },
        row_index=2,
        file_identifier="train.csv",
        source={}
    )

    assert result["identifier"] == "fakeddit:train.csv:2"


def test_build_fakeddit_article_uses_default_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: kwargs
    )

    result = module.build_fakeddit_article(
        row={
            "title": "Titre",
            "text": "Contenu",
            "label": "true"
        },
        row_index=0,
        file_identifier="train.csv",
        source={}
    )

    assert result["source"] == "Fakeddit"
    assert result["language"] == "en"
    assert result["category"] == "social"
    assert result["dataset_role"] == "multimodal_reference"


def test_build_fakeddit_article_uses_configured_category(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "build_standard_article",
        lambda **kwargs: kwargs
    )

    result = module.build_fakeddit_article(
        row={
            "title": "Titre",
            "text": "Contenu",
            "label": "true"
        },
        row_index=0,
        file_identifier="train.csv",
        source={
            "category": "social_media"
        }
    )

    assert result["category"] == "social_media"


# Validation des minimums

@pytest.mark.parametrize(
    ("value", "configured_minimum"),
    [
        (
            None,
            10
        ),
        (
            5.0,
            None
        ),
        (
            5.0,
            ""
        ),
        (
            5.0,
            "invalid"
        ),
        (
            10.0,
            10
        ),
        (
            15.0,
            10
        )
    ]
)
def test_validate_optional_minimum_accepts_value(
    value: float | None,
    configured_minimum: Any
) -> None:
    assert module.validate_optional_minimum(
        value,
        configured_minimum,
        "minimum_insuffisant"
    ) == (
        True,
        ""
    )


def test_validate_optional_minimum_rejects_value_below_minimum() -> None:
    assert module.validate_optional_minimum(
        value=4.0,
        configured_minimum=5,
        rejection_reason="minimum_insuffisant"
    ) == (
        False,
        "minimum_insuffisant"
    )


# Validation des lignes

@pytest.mark.parametrize(
    "row",
    [
        None,
        [],
        "ligne",
        42
    ]
)
def test_validate_fakeddit_row_rejects_invalid_row(
    row: Any
) -> None:
    assert module.validate_fakeddit_row(
        row,
        {},
        {}
    ) == (
        False,
        "ligne_fakeddit_invalide"
    )


def test_validate_fakeddit_row_rejects_invalid_label() -> None:
    assert module.validate_fakeddit_row(
        {
            "title": "Titre",
            "text": "Contenu",
            "label": "unknown"
        },
        {},
        {}
    ) == (
        False,
        "label_fakeddit_invalide"
    )


def test_validate_fakeddit_row_rejects_missing_content() -> None:
    assert module.validate_fakeddit_row(
        {
            "label": "true"
        },
        {},
        {}
    ) == (
        False,
        "contenu_fakeddit_absent"
    )


def test_validate_fakeddit_row_rejects_low_score() -> None:
    assert module.validate_fakeddit_row(
        {
            "label": "true",
            "text": "Contenu",
            "score": "4",
            "num_comments": "10"
        },
        {
            "min_score": 5,
            "min_comments": 5
        },
        {}
    ) == (
        False,
        "score_insuffisant"
    )


def test_validate_fakeddit_row_rejects_low_comment_count() -> None:
    assert module.validate_fakeddit_row(
        {
            "label": "true",
            "text": "Contenu",
            "score": "10",
            "num_comments": "2"
        },
        {
            "min_score": 5,
            "min_comments": 5
        },
        {}
    ) == (
        False,
        "commentaires_insuffisants"
    )


def test_validate_fakeddit_row_accepts_valid_row() -> None:
    assert module.validate_fakeddit_row(
        {
            "label": "true",
            "text": "Contenu",
            "score": "10",
            "num_comments": "8"
        },
        {
            "min_score": 5,
            "min_comments": 5
        },
        {}
    ) == (
        True,
        ""
    )


def test_validate_fakeddit_row_accepts_missing_optional_metrics() -> None:
    assert module.validate_fakeddit_row(
        {
            "label": "false",
            "title": "Titre Fakeddit"
        },
        {
            "min_score": 5,
            "min_comments": 5
        },
        {}
    ) == (
        True,
        ""
    )


# Adaptateur Fakeddit

def test_fakeddit_adapter_configuration() -> None:
    adapter = module.FAKEDDIT_ADAPTER

    assert adapter.source_id == "fakeddit"
    assert adapter.default_name == "Fakeddit"
    assert adapter.supported_extensions == frozenset({
        ".csv",
        ".tsv"
    })
    assert adapter.find_files is module.find_fakeddit_files
    assert adapter.iter_items is module.iter_fakeddit_rows
    assert adapter.build_article is module.build_fakeddit_article
    assert adapter.validate_item is module.validate_fakeddit_row