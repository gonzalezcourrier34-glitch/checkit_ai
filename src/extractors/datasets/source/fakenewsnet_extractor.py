"""Adaptateur utilisé pour extraire le dataset FakeNewsNet.

Ce module prend en charge :

- les fichiers JSON officiels de FakeNewsNet ;
- les exports CSV GossipCop et PolitiFact ;
- la détection des labels et catégories depuis l'arborescence ;
- les images distantes et locales ;
- la normalisation centralisée des labels ;
- la transformation des données au format CheckIt.AI.

Le chargement, l'orchestration et la gestion des résultats sont délégués
au moteur générique des datasets.
"""

from __future__ import annotations

import csv
import json
import sys

from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from config.constants import SUPPORTED_IMAGE_EXTENSIONS
from config.paths import BASE_DIR, SOURCES_FILE

from src.article.fact_check_labels import classify_fact_check_label
from src.extractors.core.extractor_results import ExtractorResult
from src.extractors.datasets.dataset_adapter import DatasetAdapter
from src.extractors.datasets.dataset_engine import (
    DatasetExtractor,
    extract_dataset_from_source
)
from src.extractors.datasets.dataset_file_utils import (
    resolve_configured_dataset_file
)
from src.extractors.datasets.dataset_text_utils import (
    get_dataset_text,
    get_dataset_title,
    get_dataset_url
)
from src.logger import get_logger
from src.utils.extractor_utils import build_standard_article, get_value
from src.utils.url_utils import is_valid_http_url
from src.utils.value_utils import normalize_value

logger = get_logger(__name__)


# Configuration CSV

def configure_csv_field_size_limit() -> None:
    """Configure la taille maximale des champs CSV supportée par Python."""

    maximum_size = sys.maxsize

    while maximum_size > 0:
        try:
            csv.field_size_limit(maximum_size)
            return
        except OverflowError:
            maximum_size //= 10

    logger.warning(
        "Impossible de configurer une taille maximale étendue "
        "pour les champs CSV."
    )


configure_csv_field_size_limit()


# Configuration du dataset

FAKENEWSNET_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    ".json",
    ".csv"
})

FAKENEWSNET_JSON_FILE_NAMES: frozenset[str] = frozenset({
    "news content.json",
    "news_content.json",
    "content.json"
})

FAKENEWSNET_CSV_FILE_NAMES: frozenset[str] = frozenset({
    "gossipcop_fake.csv",
    "gossipcop_real.csv",
    "politifact_fake.csv",
    "politifact_real.csv"
})

FAKENEWSNET_RAW_LABELS: frozenset[str] = frozenset({
    "fake",
    "real"
})

FAKENEWSNET_CATEGORIES: frozenset[str] = frozenset({
    "politifact",
    "gossipcop"
})

FAKENEWSNET_CSV_ENCODINGS: tuple[str, ...] = (
    "utf-8",
    "utf-8-sig",
    "latin-1"
)

FAKENEWSNET_TITLE_FIELDS: tuple[str, ...] = (
    "title",
    "headline",
    "news_title",
    "name"
)

FAKENEWSNET_TEXT_FIELDS: tuple[str, ...] = (
    "text",
    "content",
    "article_text",
    "body",
    "summary",
    "description",
    "news_text"
)

FAKENEWSNET_URL_FIELDS: tuple[str, ...] = (
    "news_url",
    "url",
    "article_url",
    "canonical_link",
    "link",
    "source_url"
)

FAKENEWSNET_IMAGE_URL_FIELDS: tuple[str, ...] = (
    "top_img",
    "top_image",
    "image_url",
    "image",
    "image_link",
    "thumbnail"
)


# Recherche et validation des fichiers

def is_fakenewsnet_json_file(filepath: Path) -> bool:
    """Vérifie qu'un fichier correspond à un contenu JSON FakeNewsNet."""

    return (
        filepath.is_file()
        and filepath.suffix.lower() == ".json"
        and filepath.name.lower() in FAKENEWSNET_JSON_FILE_NAMES
    )


def is_fakenewsnet_csv_file(filepath: Path) -> bool:
    """Vérifie qu'un fichier correspond à un export CSV reconnu."""

    return (
        filepath.is_file()
        and filepath.suffix.lower() == ".csv"
        and filepath.name.lower() in FAKENEWSNET_CSV_FILE_NAMES
    )


def is_fakenewsnet_content_file(filepath: Path) -> bool:
    """Vérifie qu'un fichier FakeNewsNet est exploitable."""

    return (
        is_fakenewsnet_json_file(filepath)
        or is_fakenewsnet_csv_file(filepath)
    )


def find_fakenewsnet_files(
    dataset_directory: Path,
    source: Mapping[str, Any]
) -> list[Path]:
    """Recherche les fichiers JSON et CSV FakeNewsNet reconnus."""

    configured_filename = normalize_value(source.get("filename"))

    if configured_filename:
        configured_file = resolve_configured_dataset_file(
            dataset_directory,
            configured_filename,
            FAKENEWSNET_SUPPORTED_EXTENSIONS,
            "FakeNewsNet"
        )

        if (
            configured_file
            and not is_fakenewsnet_content_file(configured_file)
        ):
            logger.error(
                "Fichier FakeNewsNet non reconnu : %s",
                configured_file
            )
            return []

        return [configured_file] if configured_file else []

    try:
        files = sorted(
            (
                filepath
                for filepath in dataset_directory.rglob("*")
                if is_fakenewsnet_content_file(filepath)
            ),
            key=lambda filepath: str(filepath).lower()
        )
    except OSError as error:
        logger.error(
            "Impossible de parcourir le dataset FakeNewsNet %s : %s",
            dataset_directory,
            error
        )
        return []

    json_count = sum(
        filepath.suffix.lower() == ".json"
        for filepath in files
    )

    logger.info(
        "%s fichier(s) FakeNewsNet détecté(s) : %s JSON, %s CSV.",
        len(files),
        json_count,
        len(files) - json_count
    )

    return files


# Extraction des informations depuis les chemins

def get_path_value(
    filepath: Path,
    allowed_values: frozenset[str]
) -> str:
    """Retourne une valeur reconnue dans le chemin ou le nom du fichier."""

    values = {
        part.strip().lower()
        for part in filepath.parts
        if part.strip()
    }

    stem_parts = (
        filepath.stem
        .lower()
        .replace("-", "_")
        .split("_")
    )

    values.update(part for part in stem_parts if part)

    return next(
        (
            value
            for value in sorted(allowed_values)
            if value in values
        ),
        ""
    )


def extract_raw_label_from_path(filepath: Path) -> str:
    """Déduit le label brut fake ou real depuis le chemin."""

    return get_path_value(filepath, FAKENEWSNET_RAW_LABELS)


def extract_category_from_path(filepath: Path) -> str:
    """Déduit la catégorie Politifact ou GossipCop."""

    return get_path_value(filepath, FAKENEWSNET_CATEGORIES)


def classify_fakenewsnet_label(value: Any):
    """Normalise un label FakeNewsNet avec le moteur commun."""

    return classify_fact_check_label(value)


def get_fakenewsnet_label(value: Any) -> str:
    """Retourne uniquement le label CheckIt.AI normalisé."""

    return classify_fakenewsnet_label(value).label


# Lecture robuste des fichiers JSON

def load_json_with_encoding(filepath: Path, encoding: str) -> Any:
    """Charge un fichier JSON avec l'encodage demandé."""

    with filepath.open("r", encoding=encoding) as file:
        return json.load(file)


def load_fakenewsnet_json(filepath: Path) -> dict[str, Any]:
    """Charge un fichier JSON FakeNewsNet."""

    for encoding in ("utf-8", "utf-8-sig"):
        try:
            data = load_json_with_encoding(filepath, encoding)

            if not isinstance(data, dict):
                logger.warning(
                    "Le fichier FakeNewsNet ne contient pas "
                    "un objet JSON : %s",
                    filepath
                )
                return {}

            return data

        except UnicodeDecodeError:
            continue

        except json.JSONDecodeError as error:
            logger.warning(
                "JSON FakeNewsNet invalide dans %s : %s",
                filepath,
                error
            )
            return {}

        except OSError as error:
            logger.warning(
                "Impossible de lire le fichier FakeNewsNet %s : %s",
                filepath,
                error
            )
            return {}

    logger.warning(
        "Impossible de décoder le fichier FakeNewsNet %s.",
        filepath
    )

    return {}


# Lecture progressive des fichiers CSV

def detect_csv_encoding(filepath: Path) -> str:
    """Retourne le premier encodage permettant de lire le fichier CSV."""

    for encoding in FAKENEWSNET_CSV_ENCODINGS:
        try:
            with filepath.open(
                "r",
                encoding=encoding,
                newline=""
            ) as file:
                file.read(4096)

            return encoding

        except UnicodeDecodeError:
            continue

        except OSError as error:
            logger.warning(
                "Impossible de lire le fichier FakeNewsNet %s : %s",
                filepath,
                error
            )
            return ""

    return ""


def iter_fakenewsnet_csv_rows(
    filepath: Path
) -> Iterator[tuple[str, int, dict[str, Any]]]:
    """Produit progressivement les lignes d'un export CSV."""

    encoding = detect_csv_encoding(filepath)

    if not encoding:
        logger.warning(
            "Encodage CSV FakeNewsNet indétectable : %s",
            filepath
        )
        return

    try:
        with filepath.open(
            "r",
            encoding=encoding,
            newline=""
        ) as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                logger.warning(
                    "En-tête CSV FakeNewsNet absent : %s",
                    filepath
                )
                return

            raw_label = extract_raw_label_from_path(filepath)
            category = extract_category_from_path(filepath)

            for index, row in enumerate(reader):
                normalized_row = {
                    normalize_value(key): value
                    for key, value in row.items()
                    if key is not None
                }

                normalized_row["_filepath"] = filepath
                normalized_row["_label"] = raw_label
                normalized_row["_category"] = category

                yield f"{filepath}:{index}", index, normalized_row

    except (csv.Error, OSError) as error:
        logger.warning(
            "Impossible de parcourir le CSV FakeNewsNet %s : %s",
            filepath,
            error
        )


def iter_fakenewsnet_items(
    dataset_files: list[Path],
    source: Mapping[str, Any]
) -> Iterator[tuple[str, int, Any]]:
    """Produit les contenus JSON et les lignes CSV FakeNewsNet."""

    del source

    item_index = 0

    for filepath in dataset_files:
        if is_fakenewsnet_json_file(filepath):
            yield str(filepath), item_index, filepath
            item_index += 1
            continue

        for identifier, _, row in iter_fakenewsnet_csv_rows(filepath):
            yield identifier, item_index, row
            item_index += 1


# Normalisation des données

def normalize_string_collection(value: Any) -> str:
    """Normalise une chaîne ou une collection de chaînes."""

    if isinstance(value, str):
        return normalize_value(value)

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray)
    ):
        values = [
            normalized
            for item in value
            if (normalized := normalize_value(item))
        ]

        return ", ".join(dict.fromkeys(values))

    return normalize_value(value)


def get_primary_image_url(item: Mapping[str, Any]) -> str:
    """Retourne la meilleure URL d'image distante disponible."""

    image_url = get_dataset_url(
        item,
        FAKENEWSNET_IMAGE_URL_FIELDS
    )

    if image_url:
        return image_url

    images = item.get("images", [])

    if not isinstance(images, (list, tuple, set)):
        return ""

    for image in images:
        url = normalize_value(image)

        if url and not url.lower().startswith(
            ("http://", "https://")
        ):
            url = f"https://{url.lstrip('/')}"

        if is_valid_http_url(url):
            return url

    return ""


# Gestion des images locales

def make_project_relative_path(filepath: Path) -> str:
    """Retourne un chemin relatif à la racine du projet si possible."""

    try:
        resolved_path = filepath.resolve(strict=False)
    except (OSError, RuntimeError):
        resolved_path = filepath

    try:
        return str(resolved_path.relative_to(BASE_DIR))
    except ValueError:
        return str(resolved_path)


def find_local_image(content_file: Path) -> str:
    """Recherche une image locale associée au fichier JSON."""

    try:
        image_files = sorted(
            (
                candidate
                for candidate in content_file.parent.iterdir()
                if candidate.is_file()
                and candidate.suffix.lower()
                in SUPPORTED_IMAGE_EXTENSIONS
            ),
            key=lambda candidate: candidate.name.lower()
        )
    except OSError as error:
        logger.debug(
            "Impossible de parcourir le dossier d'images %s : %s",
            content_file.parent,
            error
        )
        return ""

    return (
        make_project_relative_path(image_files[0])
        if image_files
        else ""
    )


# Construction des articles CheckIt.AI

def get_fakenewsnet_identifier(
    filepath: Path,
    article_url: str,
    fallback: Any = ""
) -> str:
    """Construit un identifiant stable."""

    if article_url:
        return article_url

    fallback_value = normalize_value(fallback)
    category = extract_category_from_path(filepath)
    raw_label = extract_raw_label_from_path(filepath)

    if fallback_value:
        return (
            f"fakenewsnet:{category}:"
            f"{raw_label}:{fallback_value}"
        )

    try:
        resolved_path = filepath.resolve(strict=False)
    except (OSError, RuntimeError):
        resolved_path = filepath

    return f"fakenewsnet:{resolved_path}"


def enrich_fakenewsnet_article_label(
    article: dict[str, Any],
    raw_label: Any
) -> dict[str, Any]:
    """Ajoute les détails de normalisation du label à l'article."""

    label_result = classify_fakenewsnet_label(raw_label)

    article["dataset_label_raw"] = label_result.raw_value
    article["dataset_label_normalized"] = label_result.normalized_value
    article["dataset_label_reason"] = label_result.reason
    article["dataset_label_match"] = label_result.matched_value

    return article


def build_fakenewsnet_article_from_file(
    filepath: Path,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme un fichier JSON FakeNewsNet au format CheckIt.AI."""

    item = load_fakenewsnet_json(filepath)

    if not item:
        return {}

    raw_label = extract_raw_label_from_path(filepath)
    label_result = classify_fakenewsnet_label(raw_label)
    article_url = get_dataset_url(item, FAKENEWSNET_URL_FIELDS)
    authors = (
        item.get("authors")
        or item.get("author")
        or item.get("creator")
    )

    article = build_standard_article(
        identifier=get_fakenewsnet_identifier(
            filepath,
            article_url
        ),
        source=source.get("name", "FakeNewsNet"),
        title=get_dataset_title(
            item,
            FAKENEWSNET_TITLE_FIELDS
        ),
        text=get_dataset_text(
            item,
            FAKENEWSNET_TEXT_FIELDS,
            FAKENEWSNET_TITLE_FIELDS
        ),
        image_url=get_primary_image_url(item),
        image_path=find_local_image(filepath),
        published_at=get_value(
            item,
            (
                "publish_date",
                "published_at",
                "published",
                "date",
                "created_at"
            )
        ),
        url=article_url,
        author=normalize_string_collection(authors),
        language=source.get("language", "en"),
        category=(
            extract_category_from_path(filepath)
            or normalize_value(source.get("category"))
            or "general"
        ),
        label=label_result.label,
        dataset_role=(
            normalize_value(source.get("role"))
            or "labeled_reference"
        )
    )

    return enrich_fakenewsnet_article_label(
        article,
        raw_label
    )


def build_fakenewsnet_article_from_row(
    item: Mapping[str, Any],
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme une ligne CSV FakeNewsNet au format CheckIt.AI."""

    filepath = item.get("_filepath")

    if not isinstance(filepath, Path):
        return {}

    raw_label = item.get("_label")
    label_result = classify_fakenewsnet_label(raw_label)
    article_url = get_dataset_url(item, FAKENEWSNET_URL_FIELDS)
    title = get_dataset_title(item, FAKENEWSNET_TITLE_FIELDS)
    identifier = get_value(
        item,
        (
            "id",
            "news_id",
            "article_id",
            "index",
            "unnamed: 0"
        )
    )

    article = build_standard_article(
        identifier=get_fakenewsnet_identifier(
            filepath,
            article_url,
            identifier or title
        ),
        source=source.get("name", "FakeNewsNet"),
        title=title,
        text=get_dataset_text(
            item,
            FAKENEWSNET_TEXT_FIELDS,
            FAKENEWSNET_TITLE_FIELDS
        ),
        image_url=get_primary_image_url(item),
        image_path="",
        published_at=get_value(
            item,
            (
                "publish_date",
                "published_at",
                "published",
                "date",
                "created_at"
            )
        ),
        url=article_url,
        author=normalize_string_collection(
            get_value(
                item,
                (
                    "authors",
                    "author",
                    "creator",
                    "byline"
                )
            )
        ),
        language=source.get("language", "en"),
        category=(
            normalize_value(item.get("_category"))
            or normalize_value(source.get("category"))
            or "general"
        ),
        label=label_result.label,
        dataset_role=(
            normalize_value(source.get("role"))
            or "labeled_reference"
        )
    )

    return enrich_fakenewsnet_article_label(
        article,
        raw_label
    )


def build_fakenewsnet_article(
    item: Any,
    item_index: int,
    item_identifier: str,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Adapte un fichier JSON ou une ligne CSV au moteur commun."""

    del item_index, item_identifier

    if isinstance(item, Path):
        return build_fakenewsnet_article_from_file(
            item,
            source
        )

    if isinstance(item, Mapping):
        return build_fakenewsnet_article_from_row(
            item,
            source
        )

    return {}


# Validation spécifique à FakeNewsNet

def validate_fakenewsnet_raw_label(value: Any) -> bool:
    """Vérifie qu'un label brut peut être normalisé."""

    label_result = classify_fakenewsnet_label(value)

    return bool(
        label_result.raw_value
        and label_result.label
        and label_result.label != "not_classified"
    )


def validate_fakenewsnet_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les contrôles propres aux versions JSON et CSV."""

    del filters, source

    if isinstance(item, Path):
        if not item.is_file():
            return False, "fichier_fakenewsnet_absent"

        if not is_fakenewsnet_json_file(item):
            return False, "fichier_fakenewsnet_non_reconnu"

        raw_label = extract_raw_label_from_path(item)

        if not raw_label:
            return False, "label_arborescence_absent"

        if not validate_fakenewsnet_raw_label(raw_label):
            return False, "label_arborescence_invalide"

        if not extract_category_from_path(item):
            return False, "categorie_arborescence_absente"

        return True, ""

    if isinstance(item, Mapping):
        filepath = item.get("_filepath")

        if (
            not isinstance(filepath, Path)
            or not is_fakenewsnet_csv_file(filepath)
        ):
            return False, "ligne_csv_fakenewsnet_invalide"

        raw_label = item.get("_label")

        if not normalize_value(raw_label):
            return False, "label_fichier_absent"

        if not validate_fakenewsnet_raw_label(raw_label):
            return False, "label_fichier_invalide"

        if not normalize_value(item.get("_category")):
            return False, "categorie_fichier_absente"

        if not get_dataset_text(
            item,
            FAKENEWSNET_TEXT_FIELDS,
            FAKENEWSNET_TITLE_FIELDS
        ):
            return False, "contenu_fakenewsnet_absent"

        return True, ""

    return False, "element_fakenewsnet_invalide"


# Adaptateur et extracteur FakeNewsNet

FAKENEWSNET_ADAPTER = DatasetAdapter(
    source_id="fakenewsnet",
    default_name="FakeNewsNet",
    supported_extensions=FAKENEWSNET_SUPPORTED_EXTENSIONS,
    find_files=find_fakenewsnet_files,
    iter_items=iter_fakenewsnet_items,
    build_article=build_fakenewsnet_article,
    validate_item=validate_fakenewsnet_item
)

FAKENEWSNET_EXTRACTOR = DatasetExtractor(
    source_id="fakenewsnet",
    default_name="FakeNewsNet",
    adapter=FAKENEWSNET_ADAPTER,
    section_name="datasets",
    sources_file=SOURCES_FILE
)


# Fonctions publiques

def load_fakenewsnet_source() -> dict[str, Any]:
    """Recharge et retourne la configuration FakeNewsNet."""

    return FAKENEWSNET_EXTRACTOR.reload_source()


def extract_articles_from_source(
    source: Mapping[str, Any]
) -> ExtractorResult:
    """Lance l'extraction depuis une configuration chargée."""

    return extract_dataset_from_source(
        source=source,
        adapter=FAKENEWSNET_ADAPTER
    )


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance FakeNewsNet."""

    return FAKENEWSNET_EXTRACTOR.run()


# Exécution directe

if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} article(s) FakeNewsNet extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])