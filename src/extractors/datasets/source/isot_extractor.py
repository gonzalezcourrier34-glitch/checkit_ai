"""Adaptateur utilisé pour extraire le dataset ISOT Fake News."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from src.extractors.datasets.dataset_adapter import DatasetAdapter
from src.extractors.datasets.dataset_engine import (
    DatasetExtractor,
    extract_dataset_from_source,
    get_dataset_chunk_size
)
from src.extractors.datasets.dataset_file_utils import (
    normalize_dataframe_columns,
    resolve_configured_dataset_file
)
from src.extractors.datasets.dataset_text_utils import (
    get_dataset_text,
    get_dataset_title
)

from config.paths import SOURCES_FILE
from src.logger import get_logger
from src.extractors.core.extractor_results import ExtractorResult
from src.article.article_cleaner import clean_text
from src.article.fact_check_labels import classify_fact_check_label
from src.utils.extractor_utils import (
    build_standard_article,
    get_value,
    normalize_value
)

logger = get_logger(__name__)


# Configuration du dataset

ISOT_DEFAULT_CHUNK_SIZE = 10_000
ISOT_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".csv"})
ISOT_EXPECTED_FILE_NAMES: tuple[str, ...] = ("Fake.csv", "True.csv")
ISOT_FILE_LABEL_MAPPING: dict[str, str] = {
    "fake.csv": "fake",
    "true.csv": "real"
}
ISOT_EXPECTED_COLUMNS: frozenset[str] = frozenset({
    "title", "text", "subject", "date"
})

ISOT_TITLE_FIELDS: tuple[str, ...] = (
    "title", "headline", "name"
)
ISOT_TEXT_FIELDS: tuple[str, ...] = (
    "text", "content", "article_text", "body", "description"
)

# Recherche et validation des fichiers

def find_expected_isot_files(dataset_directory: Path) -> list[Path]:
    """Recherche Fake.csv et True.csv sans tenir compte de la casse."""

    try:
        csv_files = [
            filepath
            for filepath in dataset_directory.rglob("*.csv")
            if filepath.is_file()
        ]
    except OSError as error:
        logger.error(
            "Impossible de parcourir le dossier ISOT %s : %s",
            dataset_directory,
            error
        )
        return []

    files_by_name = {filepath.name.lower(): filepath for filepath in csv_files}

    return [
        files_by_name[name.lower()]
        for name in ISOT_EXPECTED_FILE_NAMES
        if name.lower() in files_by_name
    ]


def find_isot_files(
    dataset_directory: Path,
    source: Mapping[str, Any]
) -> list[Path]:
    """Recherche les fichiers CSV du dataset ISOT."""

    configured_filename = normalize_value(source.get("filename"))

    if configured_filename:
        configured_file = resolve_configured_dataset_file(
            dataset_directory,
            configured_filename,
            ISOT_SUPPORTED_EXTENSIONS,
            "ISOT"
        )

        if configured_file and not get_isot_label_from_file(configured_file):
            logger.error("Fichier ISOT non reconnu : %s", configured_file)
            return []

        return [configured_file] if configured_file else []

    expected_files = find_expected_isot_files(dataset_directory)

    if expected_files:
        logger.info("%s fichier(s) ISOT standard détecté(s).", len(expected_files))
        return expected_files

    try:
        # Solution de secours lorsque les noms standards sont absents.
        files = sorted(
            (
                filepath
                for filepath in dataset_directory.rglob("*.csv")
                if filepath.is_file()
            ),
            key=lambda filepath: str(filepath).lower()
        )
    except OSError as error:
        logger.error(
            "Impossible de parcourir le dossier ISOT %s : %s",
            dataset_directory,
            error
        )
        return []

    logger.warning(
        "Fake.csv et True.csv non détectés. %s autre(s) CSV trouvé(s).",
        len(files)
    )
    return files


# Normalisation et contrôle des données CSV

def get_isot_label_from_file(dataset_file: Path) -> str:
    """Déduit le label depuis le nom du fichier."""

    return ISOT_FILE_LABEL_MAPPING.get(dataset_file.name.lower(), "")

def classify_isot_label(value: Any):
    """Normalise un label ISOT avec le moteur commun."""

    return classify_fact_check_label(value)


def get_isot_label(value: Any) -> str:
    """Retourne le label CheckIt.AI normalisé."""

    return classify_isot_label(value).label

def log_missing_columns(dataframe: pd.DataFrame, dataset_file: Path) -> None:
    """Journalise les colonnes standards absentes."""

    available_columns = {str(column).strip().lower() for column in dataframe.columns}
    missing_columns = ISOT_EXPECTED_COLUMNS - available_columns

    if missing_columns:
        logger.warning(
            "Colonnes ISOT absentes dans %s : %s.",
            dataset_file.name,
            ", ".join(sorted(missing_columns))
        )


# Lecture progressive des fichiers CSV

def iter_isot_items(
    dataset_files: list[Path],
    source: Mapping[str, Any]
) -> Iterator[tuple[str, int, Mapping[str, Any]]]:
    """Lit progressivement les fichiers CSV ISOT."""

    chunk_size = get_dataset_chunk_size(source, ISOT_DEFAULT_CHUNK_SIZE, "ISOT")

    for dataset_file in dataset_files:
        label = get_isot_label_from_file(dataset_file)

        if not label:
            logger.warning("Label impossible à déterminer pour %s.", dataset_file.name)
            continue

        logger.info(
            "Lecture de %s par blocs de %s lignes.",
            dataset_file.name,
            chunk_size
        )

        try:
            # Le context manager garantit la fermeture du lecteur pandas.
            with pd.read_csv(
                dataset_file,
                chunksize=chunk_size,
                dtype=str,
                keep_default_na=False,
                low_memory=False,
                encoding="utf-8",
                on_bad_lines="warn"
            ) as reader:
                row_index = 0
                columns_checked = False

                for dataframe in reader:
                    dataframe = normalize_dataframe_columns(dataframe)

                    if not columns_checked:
                        log_missing_columns(dataframe, dataset_file)
                        columns_checked = True

                    for raw_row in dataframe.to_dict(orient="records"):
                        row = {
                            **raw_row,
                            "_label": label,
                            "_source_file": dataset_file.name,
                            "_row_index": row_index
                        }

                        yield f"{dataset_file.name}:{row_index}", row_index, row
                        row_index += 1

        except (OSError, UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
            # Une erreur isolée ne bloque pas les fichiers suivants.
            logger.error(
                "Impossible de lire le fichier ISOT %s : %s",
                dataset_file,
                error
            )


# Construction des articles CheckIt.AI

def build_isot_identifier(row: Mapping[str, Any], item_identifier: str) -> str:
    """Construit un identifiant stable pour une ligne ISOT."""

    title = get_dataset_title(row, ISOT_TITLE_FIELDS)
    source_filename = normalize_value(row.get("_source_file"))

    return (
        f"isot:{source_filename}:{item_identifier}:{title}"
        if title
        else f"isot:{source_filename}:{item_identifier}"
    )


def get_isot_category(row: Mapping[str, Any], source: Mapping[str, Any]) -> str:
    """Retourne le sujet ISOT ou la catégorie configurée."""

    category = clean_text(get_value(row, ("subject", "category", "topic")))
    return category or normalize_value(source.get("category")) or "general"


def build_isot_article(
    item: Any,
    item_index: int,
    item_identifier: str,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme une ligne ISOT au format CheckIt.AI."""

    del item_index

    if not isinstance(item, Mapping):
        return {}

    title = get_dataset_title(item, ISOT_TITLE_FIELDS)
    text = get_dataset_text(item, ISOT_TEXT_FIELDS, ISOT_TITLE_FIELDS)
    
    raw_label = item.get("_label")
    label_result = classify_isot_label(raw_label)

    article = build_standard_article(
        identifier=build_isot_identifier(item, item_identifier),
        source=source.get("name", "ISOT Fake News Dataset"),
        title=title,
        text=text,
        image_url="",
        image_path="",
        published_at=get_value(
            item,
            ("date", "published_at", "published", "publication_date")
        ),
        url="",
        author="",
        language=source.get("language", "en"),
        category=get_isot_category(item, source),
        label=label_result.label,
        dataset_role=normalize_value(source.get("role")) or "labeled_reference"
    )

    article["dataset_label_raw"] = label_result.raw_value
    article["dataset_label_normalized"] = label_result.normalized_value
    article["dataset_label_reason"] = label_result.reason
    article["dataset_label_match"] = label_result.matched_value

    return article

# Validation spécifique au dataset ISOT

def validate_isot_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les contrôles propres au dataset ISOT."""

    del filters, source

    if not isinstance(item, Mapping):
        return False, "ligne_isot_invalide"

    label_result = classify_isot_label(item.get("_label"))

    if not label_result.label:
        return False, "label_isot_invalide"

    if label_result.label == "not_classified":
        return False, "label_isot_invalide"

    if not normalize_value(item.get("_source_file")):
        return False, "fichier_source_absent"

    if not get_dataset_title(item, ISOT_TITLE_FIELDS):
        return False, "titre_isot_absent"
    if not get_dataset_text(item, ISOT_TEXT_FIELDS, ISOT_TITLE_FIELDS):
        return False, "texte_isot_absent"

    return True, ""


# Adaptateur et extracteur ISOT

ISOT_ADAPTER = DatasetAdapter(
    source_id="isot",
    default_name="ISOT Fake News Dataset",
    supported_extensions=ISOT_SUPPORTED_EXTENSIONS,
    find_files=find_isot_files,
    iter_items=iter_isot_items,
    build_article=build_isot_article,
    validate_item=validate_isot_item
)

ISOT_EXTRACTOR = DatasetExtractor(
    source_id="isot",
    default_name="ISOT Fake News Dataset",
    adapter=ISOT_ADAPTER,
    section_name="datasets",
    sources_file=SOURCES_FILE
)


# Fonctions publiques

def load_isot_source() -> dict[str, Any]:
    """Recharge et retourne la configuration ISOT."""

    return ISOT_EXTRACTOR.reload_source()


def extract_articles_from_source(source: Mapping[str, Any]) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_dataset_from_source(source=source, adapter=ISOT_ADAPTER)


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction ISOT."""

    return ISOT_EXTRACTOR.run()


# Exécution directe

if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} article(s) ISOT extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])