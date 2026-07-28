"""Adaptateur utilisé pour extraire le dataset Fakeddit."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import pandas as pd
from config.paths import SOURCES_FILE

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
    get_dataset_title,
    get_dataset_url
)
from src.extractors.core.extractor_results import ExtractorResult
from src.utils.value_utils import normalize_value
from src.utils.parsing_utils import parse_optional_float
from src.article.processing.article_cleaner import clean_text
from src.article.fact_check_labels import classify_fact_check_label

from src.utils.extractor_utils import (
    build_standard_article,
    get_numeric_value,
    get_value
)

from src.logger import get_logger

logger = get_logger(__name__)


# Configuration du dataset

FAKEDDIT_DEFAULT_CHUNK_SIZE = 10_000
FAKEDDIT_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".csv", ".tsv"})

def normalize_fakeddit_label(row: Mapping[str, Any]) -> str:
    """Convertit le label Fakeddit au format CheckIt.AI."""

    raw_label = get_value(row, ("2_way_label", "label"))

    if raw_label == "0":
        raw_label = "false"
    elif raw_label == "1":
        raw_label = "true"

    return classify_fact_check_label(raw_label).label

# Recherche et validation des fichiers

def find_fakeddit_files(
    dataset_directory: Path,
    source: Mapping[str, Any]
) -> list[Path]:
    """Retourne le fichier configuré ou tous les CSV/TSV disponibles."""

    # Un fichier précis peut être imposé dans sources.yaml.
    configured_filename = normalize_value(source.get("filename"))

    if configured_filename:
        configured_file = resolve_configured_dataset_file(
            dataset_directory,
            configured_filename,
            FAKEDDIT_SUPPORTED_EXTENSIONS,
            "Fakeddit"
        )
        return [configured_file] if configured_file else []

    try:
        # Recherche récursivement tous les fichiers pris en charge.
        files = sorted(
            (
                file_path
                for file_path in dataset_directory.rglob("*")
                if file_path.is_file()
                and file_path.suffix.lower() in FAKEDDIT_SUPPORTED_EXTENSIONS
            ),
            key=lambda file_path: str(file_path).lower()
        )
    except OSError as error:
        raise RuntimeError(
            f"Impossible de parcourir le dossier Fakeddit : {error}"
        ) from error

    logger.info("%s fichier(s) Fakeddit détecté(s).", len(files))
    return files


# Paramètres de lecture

def get_separator(dataset_file: Path) -> str:
    """Retourne le séparateur adapté au fichier."""

    extension = dataset_file.suffix.lower()

    if extension == ".tsv":
        return "\t"
    if extension == ".csv":
        return ","

    raise ValueError(
        f"Format Fakeddit non pris en charge : {dataset_file.suffix}"
    )


# Lecture progressive des fichiers

def iter_fakeddit_rows(
    dataset_files: list[Path],
    source: Mapping[str, Any]
) -> Iterator[tuple[str, int, Mapping[str, Any]]]:
    """Lit progressivement les fichiers Fakeddit."""

    # Utilise une lecture par blocs pour limiter la mémoire utilisée.
    chunk_size = get_dataset_chunk_size(
        source,
        FAKEDDIT_DEFAULT_CHUNK_SIZE,
        "Fakeddit"
    )

    for dataset_file in dataset_files:
        try:
            separator = get_separator(dataset_file)

            logger.info(
                "Lecture de %s par blocs de %s lignes.",
                dataset_file.name,
                chunk_size
            )

            # Le context manager garantit la fermeture du lecteur,
            # même lorsqu'une erreur interrompt la lecture.
            with pd.read_csv(
                dataset_file,
                sep=separator,
                chunksize=chunk_size,
                dtype=str,
                keep_default_na=False,
                low_memory=False,
                encoding="utf-8",
                on_bad_lines="warn"
            ) as reader:
                row_index = 0

                for dataframe in reader:
                    dataframe = normalize_dataframe_columns(dataframe)

                    for row in dataframe.to_dict(orient="records"):
                        yield dataset_file.name, row_index, row
                        row_index += 1

        except (
            OSError,
            UnicodeDecodeError,
            pd.errors.ParserError,
            ValueError
        ) as error:
            # Une erreur sur un fichier ne bloque pas les fichiers suivants.
            logger.error(
                "Impossible de lire le fichier Fakeddit %s : %s",
                dataset_file,
                error
            )


# Valeurs métier

FAKEDDIT_TITLE_FIELDS: tuple[str, ...] = (
    "clean_title", "title", "submission_title"
)
FAKEDDIT_TEXT_FIELDS: tuple[str, ...] = (
    "clean_text", "text", "selftext", "body"
)
FAKEDDIT_URL_FIELDS: tuple[str, ...] = (
    "url", "link", "permalink"
)
FAKEDDIT_IMAGE_URL_FIELDS: tuple[str, ...] = (
    "image_url", "img_url", "thumbnail"
)


# Construction des articles

def build_fakeddit_article(
    row: Any,
    row_index: int,
    file_identifier: str,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme une ligne Fakeddit au format CheckIt.AI."""

    if not isinstance(row, Mapping):
        return {}

    title = get_dataset_title(row, FAKEDDIT_TITLE_FIELDS)
    text = get_dataset_text(row, FAKEDDIT_TEXT_FIELDS, FAKEDDIT_TITLE_FIELDS)
    url = get_dataset_url(row, FAKEDDIT_URL_FIELDS)
    original_id = get_value(row, ("id", "submission_id", "post_id"))
    fallback_identifier = f"fakeddit:{file_identifier}:{row_index}"

    return build_standard_article(
        identifier=original_id or url or fallback_identifier,
        source=source.get("name", "Fakeddit"),
        title=title,
        text=text,
        image_url=get_dataset_url(row, FAKEDDIT_IMAGE_URL_FIELDS),
        image_path=get_value(
            row,
            ("image_path", "local_image_path", "img", "image")
        ),
        published_at=get_value(
            row,
            ("created_utc", "created", "timestamp", "published_at", "date")
        ),
        url=url,
        author=clean_text(get_value(row, ("author", "username"))),
        language=source.get("language", "en"),
        category=(
            clean_text(get_value(row, ("subreddit", "domain", "category")))
            or normalize_value(source.get("category"))
            or "social"
        ),
        label=normalize_fakeddit_label(row),
        dataset_role=normalize_value(source.get("role")) or "multimodal_reference"
    )


# Validation spécifique à Fakeddit

def validate_optional_minimum(
    value: float | None,
    configured_minimum: Any,
    rejection_reason: str
) -> tuple[bool, str]:
    """Compare une métrique à un minimum facultatif."""

    minimum = parse_optional_float(configured_minimum)

    if minimum is None or value is None:
        return True, ""

    if value < minimum:
        return False, rejection_reason

    return True, ""


def validate_fakeddit_row(
    row: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les contrôles propres à Fakeddit."""

    # Paramètre imposé par l'interface commune, mais inutilisé ici.
    del source

    if not isinstance(row, Mapping):
        return False, "ligne_fakeddit_invalide"
    label = normalize_fakeddit_label(row)

    if not label or label == "not_classified":
        return False, "label_fakeddit_invalide"
    
    if not get_dataset_text(row, FAKEDDIT_TEXT_FIELDS, FAKEDDIT_TITLE_FIELDS):
        return False, "contenu_fakeddit_absent"

    # Vérifie le score minimum si l'option est configurée.
    score = get_numeric_value(row, ("score", "reddit_score"))
    valid, reason = validate_optional_minimum(
        score,
        filters.get("min_score"),
        "score_insuffisant"
    )

    if not valid:
        return False, reason

    # Vérifie le nombre minimum de commentaires.
    comments = get_numeric_value(
        row,
        ("num_comments", "comments", "comment_count")
    )

    return validate_optional_minimum(
        comments,
        filters.get("min_comments"),
        "commentaires_insuffisants"
    )


# Adaptateur et extracteur Fakeddit

FAKEDDIT_ADAPTER = DatasetAdapter(
    source_id="fakeddit",
    default_name="Fakeddit",
    supported_extensions=FAKEDDIT_SUPPORTED_EXTENSIONS,
    find_files=find_fakeddit_files,
    iter_items=iter_fakeddit_rows,
    build_article=build_fakeddit_article,
    validate_item=validate_fakeddit_row
)

FAKEDDIT_EXTRACTOR = DatasetExtractor(
    source_id="fakeddit",
    default_name="Fakeddit",
    adapter=FAKEDDIT_ADAPTER,
    section_name="datasets",
    sources_file=SOURCES_FILE
)


# Fonctions publiques

def load_fakeddit_source() -> dict[str, Any]:
    """Recharge et retourne la configuration Fakeddit."""

    return FAKEDDIT_EXTRACTOR.reload_source()


def extract_articles_from_source(source: Mapping[str, Any]) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_dataset_from_source(source=source, adapter=FAKEDDIT_ADAPTER)


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction Fakeddit."""

    return FAKEDDIT_EXTRACTOR.run()


# Exécution directe du module

if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} publication(s) Fakeddit extraite(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])