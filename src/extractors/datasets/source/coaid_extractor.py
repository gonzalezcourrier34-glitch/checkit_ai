"""Adaptateur utilisé pour extraire le dataset CoAID."""

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
    get_dataset_title,
    get_dataset_url
)
from src.utils.value_utils import normalize_value
from src.extractors.core.extractor_results import ExtractorResult
from src.article.article_cleaner import clean_text

from src.utils.extractor_utils import (
    build_standard_article,
    get_value,
)
from src.logger import get_logger

from config.paths import SOURCES_FILE

logger = get_logger(__name__)


# Configuration du dataset

COAID_DEFAULT_CHUNK_SIZE = 10_000
COAID_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".csv"})
COAID_LABELS: frozenset[str] = frozenset({"fake", "real"})
COAID_CONTENT_TYPES: frozenset[str] = frozenset({"news", "claim"})
COAID_FILE_MARKERS: tuple[str, ...] = (
    "newsfake", "newsreal", "claimfake", "claimreal"
)
COAID_IGNORED_MARKERS: tuple[str, ...] = (
    "tweet", "reply", "retweet", "engagement", "user", "social"
)

# Détection des fichiers CoAID

def normalize_filename_for_detection(filepath: Path) -> str:
    """Normalise un nom de fichier pour faciliter sa détection."""

    # Supprime les espaces et séparateurs afin de comparer
    # facilement les différentes variantes de noms.
    return filepath.stem.strip().lower().replace(" ", "").replace("-", "").replace("_", "")


def is_ignored_social_file(filepath: Path) -> bool:
    """Vérifie si le fichier contient seulement des données sociales."""

    filename = normalize_filename_for_detection(filepath)
    return any(marker in filename for marker in COAID_IGNORED_MARKERS)


def is_supported_coaid_file(filepath: Path) -> bool:
    """Vérifie qu'un fichier CSV contient des news ou claims CoAID."""

    if not filepath.is_file() or filepath.suffix.lower() not in COAID_SUPPORTED_EXTENSIONS:
        return False

    if is_ignored_social_file(filepath):
        return False

    filename = normalize_filename_for_detection(filepath)
    return any(marker in filename for marker in COAID_FILE_MARKERS)


def find_coaid_files(dataset_directory: Path, source: Mapping[str, Any]) -> list[Path]:
    """Recherche les fichiers NewsFake, NewsReal, ClaimFake et ClaimReal."""

    # Un fichier précis peut être imposé dans datasets.yaml.
    configured_filename = normalize_value(source.get("filename"))

    if configured_filename:
        configured_file = resolve_configured_dataset_file(
            dataset_directory,
            configured_filename,
            COAID_SUPPORTED_EXTENSIONS,
            "CoAID"
        )

        if configured_file and not is_supported_coaid_file(configured_file):
            logger.error("Fichier CoAID non reconnu : %s", configured_file)
            return []

        return [configured_file] if configured_file else []

    try:
        # Recherche récursivement tous les CSV CoAID reconnus.
        files = sorted(
            (
                filepath
                for filepath in dataset_directory.rglob("*.csv")
                if is_supported_coaid_file(filepath)
            ),
            key=lambda filepath: str(filepath).lower()
        )
    except OSError as error:
        logger.error("Impossible de parcourir le dossier CoAID %s : %s", dataset_directory, error)
        return []

    logger.info("%s fichier(s) CoAID exploitable(s) détecté(s).", len(files))
    return files


# Lecture des informations portées par les noms de fichiers

def get_coaid_label_from_file(dataset_file: Path) -> str:
    """Déduit le label fake ou real depuis le nom du fichier."""

    filename = normalize_filename_for_detection(dataset_file)

    if "fake" in filename:
        return "fake"

    if "real" in filename:
        return "real"

    return ""


def get_coaid_content_type_from_file(dataset_file: Path) -> str:
    """Déduit le type news ou claim depuis le nom du fichier."""

    filename = normalize_filename_for_detection(dataset_file)

    if "claim" in filename:
        return "claim"

    if "news" in filename:
        return "news"

    return ""


def get_collection_period(dataset_file: Path) -> str:
    """Récupère une période de collecte depuis l'arborescence."""

    # Parcourt les dossiers parents du plus proche au plus éloigné.
    for part in reversed(dataset_file.parent.parts):
        normalized = normalize_value(part)

        if any(character.isdigit() for character in normalized):
            return normalized

    return ""


# Lecture progressive des fichiers

def iter_coaid_items(
    dataset_files: list[Path],
    source: Mapping[str, Any]
) -> Iterator[tuple[str, int, Mapping[str, Any]]]:
    """Lit progressivement les fichiers CSV CoAID."""

    chunk_size = get_dataset_chunk_size(source, COAID_DEFAULT_CHUNK_SIZE, "CoAID")

    for dataset_file in dataset_files:
        # Les principales métadonnées sont déduites du nom du fichier.
        label = get_coaid_label_from_file(dataset_file)
        content_type = get_coaid_content_type_from_file(dataset_file)
        collection_period = get_collection_period(dataset_file)

        if not label or not content_type:
            logger.warning("Fichier CoAID impossible à classer : %s", dataset_file)
            continue

        logger.info("Lecture de %s par blocs de %s lignes.", dataset_file.name, chunk_size)

        try:
            # Le context manager garantit la fermeture du fichier,
            # y compris lorsqu'une exception interrompt la lecture.
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

                for dataframe in reader:
                    dataframe = normalize_dataframe_columns(dataframe)

                    for raw_row in dataframe.to_dict(orient="records"):
                        row = {
                            **raw_row,
                            "_label": label,
                            "_content_type": content_type,
                            "_source_file": dataset_file.name,
                            "_collection_period": collection_period,
                            "_row_index": row_index
                        }

                        identifier = f"{dataset_file.name}:{row_index}"
                        yield identifier, row_index, row
                        row_index += 1

        except (OSError, UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
            # Une erreur sur un fichier ne bloque pas la lecture des suivants.
            logger.error("Impossible de lire le fichier CoAID %s : %s", dataset_file, error)


# Valeurs métier

COAID_TITLE_FIELDS: tuple[str, ...] = (
    "title", "headline", "claim", "statement", "news", "text"
)
COAID_TEXT_FIELDS: tuple[str, ...] = (
    "content", "article_text", "body", "description", "abstract", "summary"
)
COAID_URL_FIELDS: tuple[str, ...] = (
    "url", "link", "news_url", "claim_url"
)
COAID_IMAGE_FIELDS: tuple[str, ...] = (
    "image_url", "image", "thumbnail", "top_img"
)


def build_coaid_identifier(row: Mapping[str, Any], item_identifier: str) -> str:
    """Construit un identifiant stable pour une ligne CoAID."""

    original_id = get_value(row, ("id", "news_id", "claim_id", "article_id"))
    if original_id:
        return f"coaid:{original_id}"

    url = get_dataset_url(row, COAID_URL_FIELDS)
    if url:
        return f"coaid:{url}"

    source_file = normalize_value(row.get("_source_file"))
    return f"coaid:{source_file}:{item_identifier}"


def get_coaid_category(row: Mapping[str, Any], source: Mapping[str, Any]) -> str:
    """Retourne la catégorie fournie ou health par défaut."""

    category = clean_text(get_value(row, ("category", "topic", "subject")))
    return category or normalize_value(source.get("category")) or "health"


def get_coaid_role(row: Mapping[str, Any], source: Mapping[str, Any]) -> str:
    """Retourne le rôle canonique configuré pour le dataset."""

    del row
    return normalize_value(source.get("role")) or "labeled_reference"


# Construction d'un article CheckIt.AI

def build_coaid_article(
    item: Any,
    item_index: int,
    item_identifier: str,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme une ligne CoAID au format CheckIt.AI."""

    # L'index est déjà inclus dans item_identifier.
    del item_index

    if not isinstance(item, Mapping):
        return {}

    title = get_dataset_title(item, COAID_TITLE_FIELDS)
    text = get_dataset_text(item, COAID_TEXT_FIELDS, COAID_TITLE_FIELDS)

    return build_standard_article(
        identifier=build_coaid_identifier(item, item_identifier),
        source=source.get("name", "CoAID"),
        title=title,
        text=text,
        image_url=get_dataset_url(item, COAID_IMAGE_FIELDS),
        image_path="",
        published_at=get_value(
            item,
            ("publish_date", "published_at", "published", "date", "created_at")
        ),
        url=get_dataset_url(item, COAID_URL_FIELDS),
        author=clean_text(get_value(item, ("author", "authors", "creator", "source"))),
        language=source.get("language", "en"),
        category=get_coaid_category(item, source),
        label=normalize_value(item.get("_label")).lower(),
        dataset_role=get_coaid_role(item, source)
    )


# Validation spécifique à CoAID

def validate_coaid_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les contrôles propres au dataset CoAID."""

    # Paramètres imposés par l'interface commune, mais inutiles ici.
    del filters, source

    if not isinstance(item, Mapping):
        return False, "ligne_coaid_invalide"

    label = normalize_value(item.get("_label")).lower()

    if label not in COAID_LABELS:
        return False, "label_coaid_invalide"

    content_type = normalize_value(item.get("_content_type")).lower()

    if content_type not in COAID_CONTENT_TYPES:
        return False, "type_contenu_coaid_invalide"

    if not get_dataset_text(item, COAID_TEXT_FIELDS, COAID_TITLE_FIELDS):
        return False, "contenu_coaid_absent"

    return True, ""


# Adaptateur et extracteur CoAID

COAID_ADAPTER = DatasetAdapter(
    source_id="coaid",
    default_name="CoAID",
    supported_extensions=COAID_SUPPORTED_EXTENSIONS,
    find_files=find_coaid_files,
    iter_items=iter_coaid_items,
    build_article=build_coaid_article,
    validate_item=validate_coaid_item
)

COAID_EXTRACTOR = DatasetExtractor(
    source_id="coaid",
    default_name="CoAID",
    adapter=COAID_ADAPTER,
    section_name="datasets",
    sources_file=SOURCES_FILE
)


# Fonctions publiques

def load_coaid_source() -> dict[str, Any]:
    """Recharge et retourne la configuration CoAID."""

    return COAID_EXTRACTOR.reload_source()


def extract_articles_from_source(source: Mapping[str, Any]) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_dataset_from_source(source=source, adapter=COAID_ADAPTER)


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction CoAID."""

    return COAID_EXTRACTOR.run()


# Exécution directe du module

if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} élément(s) CoAID extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])