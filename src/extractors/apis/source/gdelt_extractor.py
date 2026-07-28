"""Adaptateur utilisé pour extraire des articles avec GDELT DOC 2.0.

Ce module contient uniquement les traitements propres à GDELT :

- normalisation des langues et des thèmes ;
- construction des requêtes GDELT ;
- limitation du rythme et relance après rate limit ;
- récupération des résultats ;
- transformation des résultats en articles CheckIt.AI ;
- validation spécifique des éléments.

Le chargement, l'orchestration et la gestion des résultats sont délégués
à ApiExtractor et aux modules génériques des extracteurs.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from threading import Lock
from time import monotonic, sleep
from typing import Any

from config.paths import SOURCES_FILE
from src.extractors.apis.api_adapter import ApiAdapter
from src.extractors.apis.api_extractor import (
    ApiExtractionStoppedError,
    ApiExtractor,
    ApiRequestError,
    calculate_page_size,
    get_queries_configuration,
    extract_api_from_source,
    fetch_json_object,
    filter_mapping_items,
    get_api_max_article_age_days,
    normalize_string_list,
    raise_if_fatal_api_error
)

from src.extractors.core.extractor_results import ExtractorResult
from src.article.processing.article_cleaner import clean_text 
from src.utils.url_utils import is_valid_http_url
from src.utils.value_utils import normalize_value
from src.utils.parsing_utils import parse_non_negative_integer
from src.utils.extractor_utils import build_standard_article

from src.logger import get_logger

logger = get_logger(__name__)


# Configuration propre à GDELT

GDELT_MAX_RECORDS = 250
GDELT_DEFAULT_RECORDS = 1
GDELT_MIN_REQUEST_INTERVAL_SECONDS = 5.0
GDELT_RATE_LIMIT_RETRIES = 1

GDELT_TIMESPAN_PATTERN = re.compile(
    r"^(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>min|minutes?|h|hours?|d|days?|w|weeks?|m|months?)$",
    re.IGNORECASE
)

GDELT_RATE_LIMIT_PATTERN = re.compile(
    r"(?:one every 5 seconds|rate.?limit|too many requests|high-traffic)",
    re.IGNORECASE
)

GDELT_TIMESPAN_UNIT_TO_DAYS: dict[str, float] = {
    "min": 1 / 1440,
    "minute": 1 / 1440,
    "minutes": 1 / 1440,
    "h": 1 / 24,
    "hour": 1 / 24,
    "hours": 1 / 24,
    "d": 1,
    "day": 1,
    "days": 1,
    "w": 7,
    "week": 7,
    "weeks": 7,
    "m": 30,
    "month": 30,
    "months": 30
}

LANGUAGE_MAPPING: dict[str, str] = {
    "ar": "arabic",
    "de": "german",
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "it": "italian",
    "ja": "japanese",
    "ko": "korean",
    "nl": "dutch",
    "pt": "portuguese",
    "ru": "russian",
    "zh": "chinese"
}

_gdelt_request_lock = Lock()
_last_gdelt_request_at = 0.0


# Normalisation des requêtes configurées

def get_configured_queries(source: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Retourne les blocs structurés ou la configuration racine."""

    return get_queries_configuration(source) or [dict(source)]


def merge_gdelt_query(
    source: Mapping[str, Any],
    query: Mapping[str, Any]
) -> dict[str, Any]:
    """Fusionne une requête avec la configuration commune."""

    return {**dict(source), **dict(query)}


# Normalisation des filtres

def get_languages(source: Mapping[str, Any]) -> list[str]:
    """Retourne les langues configurées en minuscules."""

    return normalize_string_list(
        source.get("languages", source.get("language")),
        lowercase=True
    )


def get_themes(source: Mapping[str, Any]) -> list[str]:
    """Retourne les thèmes configurés."""

    return normalize_string_list(
        source.get("themes", source.get("theme"))
    )


def normalize_gdelt_language(language: Any) -> str:
    """Convertit un code ISO en nom de langue accepté par GDELT."""

    normalized = normalize_value(language).lower()
    return LANGUAGE_MAPPING.get(normalized, normalized)


def normalize_gdelt_theme(theme: Any) -> str:
    """Normalise un thème pour une requête GDELT."""

    normalized = normalize_value(theme)

    if not normalized:
        return ""

    if ":" in normalized or " " in normalized:
        return normalized

    return f"theme:{normalized}"


def build_gdelt_query(language: Any = "", theme: Any = "") -> str:
    """Construit une requête compatible avec GDELT."""

    parts: list[str] = []
    normalized_theme = normalize_gdelt_theme(theme)
    normalized_language = normalize_gdelt_language(language)

    if normalized_theme:
        parts.append(normalized_theme)

    if normalized_language:
        parts.append(f"sourcelang:{normalized_language}")

    return " ".join(parts) or "news"


# Gestion de la période

def normalize_gdelt_timespan(source: Mapping[str, Any]) -> str:
    """Normalise la période sans dépasser la limite globale autorisée."""

    maximum_days = max(get_api_max_article_age_days(source), 1)
    configured_timespan = normalize_value(source.get("timespan"))

    if not configured_timespan:
        return f"{maximum_days}d"

    match = GDELT_TIMESPAN_PATTERN.fullmatch(configured_timespan)

    if not match:
        logger.warning(
            "Période GDELT invalide : %s. Limite utilisée : %s jour(s).",
            configured_timespan,
            maximum_days
        )
        return f"{maximum_days}d"

    value = float(match.group("value"))
    unit = match.group("unit").lower()

    if value <= 0:
        logger.warning(
            "Période GDELT non positive : %s. Limite utilisée : %s jour(s).",
            configured_timespan,
            maximum_days
        )
        return f"{maximum_days}d"

    if value * GDELT_TIMESPAN_UNIT_TO_DAYS[unit] > maximum_days:
        logger.warning(
            "Période GDELT réduite de %s à %s jour(s).",
            configured_timespan,
            maximum_days
        )
        return f"{maximum_days}d"

    return configured_timespan.replace(" ", "")


# Limitation et envoi des requêtes

def get_gdelt_request_interval(source: Mapping[str, Any]) -> float:
    """Retourne le délai GDELT configuré sans descendre sous 5 secondes."""

    configured_value = source.get("request_delay_seconds")

    try:
        configured_interval = float(configured_value)
    except (TypeError, ValueError):
        configured_interval = GDELT_MIN_REQUEST_INTERVAL_SECONDS

    return max(configured_interval, GDELT_MIN_REQUEST_INTERVAL_SECONDS)


def wait_for_gdelt_rate_limit(interval_seconds: float) -> None:
    """Espace les requêtes GDELT au sein du processus courant."""

    global _last_gdelt_request_at

    with _gdelt_request_lock:
        remaining = interval_seconds - (monotonic() - _last_gdelt_request_at)

        if remaining > 0:
            logger.debug(
                "Attente GDELT de %.2f seconde(s) avant la requête.",
                remaining
            )
            sleep(remaining)

        _last_gdelt_request_at = monotonic()


def get_gdelt_error_message(data: Mapping[str, Any]) -> str:
    """Extrait un éventuel message d'erreur GDELT."""

    return (
        normalize_value(data.get("error"))
        or normalize_value(data.get("message"))
        or normalize_value(data.get("status"))
    )


def is_gdelt_rate_limit_message(message: Any) -> bool:
    """Indique si un message correspond à la limitation GDELT."""

    normalized = normalize_value(message)
    return bool(normalized and GDELT_RATE_LIMIT_PATTERN.search(normalized))


def fetch_gdelt_data(
    endpoint: str,
    params: Mapping[str, Any],
    interval_seconds: float
) -> dict[str, Any]:
    """Envoie une requête GDELT avec limitation et relance unique contrôlée."""

    for attempt in range(GDELT_RATE_LIMIT_RETRIES + 1):
        wait_for_gdelt_rate_limit(interval_seconds)

        data = fetch_json_object(
            url=endpoint,
            params=params,
            headers={"Accept": "application/json"}
        )
        error_message = get_gdelt_error_message(data)

        if isinstance(data.get("articles"), list):
            return data

        if not is_gdelt_rate_limit_message(error_message):
            return data

        if attempt < GDELT_RATE_LIMIT_RETRIES:
            logger.warning(
                "Limitation GDELT détectée. Une nouvelle tentative sera effectuée "
                "après %.1f seconde(s).",
                interval_seconds
            )
            continue

        raise ApiExtractionStoppedError(
            source_name="GDELT",
            reason=(
                "GDELT refuse temporairement la requête car la fréquence "
                f"maximale est dépassée : {error_message}"
            ),
            status_code=429
        )

    return {}


# Récupération des articles

def request_gdelt_articles(
    source: Mapping[str, Any],
    language: str,
    theme: str,
    max_records: int
) -> list[dict[str, Any]]:
    """Récupère les articles correspondant à une langue et un thème."""

    endpoint = normalize_value(source.get("endpoint"))

    if not is_valid_http_url(endpoint):
        raise ValueError(
            "Endpoint GDELT absent ou invalide : "
            f"{endpoint or 'valeur absente'}."
        )

    requested_records = calculate_page_size(
        configured_value=max_records,
        remaining_articles=max_records,
        default=GDELT_DEFAULT_RECORDS,
        maximum=GDELT_MAX_RECORDS
    )

    query = build_gdelt_query(language, theme)
    params: dict[str, Any] = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": requested_records,
        "sort": "datedesc",
        "timespan": normalize_gdelt_timespan(source)
    }

    logger.debug(
        "Requête GDELT : query='%s', maxrecords=%s, timespan=%s.",
        query,
        requested_records,
        params["timespan"]
    )

    interval_seconds = get_gdelt_request_interval(source)
    data = fetch_gdelt_data(endpoint, params, interval_seconds)
    error_message = get_gdelt_error_message(data)

    if error_message and not isinstance(data.get("articles"), list):
        raise_if_fatal_api_error(error_message, "GDELT")
        raise ApiRequestError(
            source_name="GDELT",
            reason=f"Erreur retournée par GDELT : {error_message}.",
            parameters=params
        )

    articles = filter_mapping_items(
        items=data.get("articles", []),
        source_name="GDELT"
    )

    return articles[:requested_records]


# Parcours des combinaisons configurées

def iter_gdelt_items(
    source: Mapping[str, Any],
    maximum_articles: int
) -> Iterator[tuple[str, int, Mapping[str, Any]]]:
    """Parcourt les combinaisons de langues et de thèmes."""

    maximum = parse_non_negative_integer(maximum_articles, 0)

    if maximum <= 0:
        return

    yielded_count = 0

    for query_block in get_configured_queries(source):
        query_configuration = merge_gdelt_query(source, query_block)
        languages = get_languages(query_configuration) or [""]
        themes = get_themes(query_configuration) or [""]

        for language in languages:
            for theme in themes:
                remaining = maximum - yielded_count

                if remaining <= 0:
                    return

                articles = request_gdelt_articles(
                    source=query_configuration,
                    language=language,
                    theme=theme,
                    max_records=remaining
                )
                identifier = build_gdelt_query(language, theme)

                for index, item in enumerate(articles):
                    if yielded_count >= maximum:
                        return

                    yield identifier, index, {
                        **item,
                        "_requested_language": language,
                        "_requested_theme": theme
                    }
                    yielded_count += 1


# Construction de l'article standard

def build_gdelt_article(
    item: Any,
    item_index: int,
    item_identifier: str,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme un résultat GDELT au format CheckIt.AI."""

    del item_index, item_identifier

    if not isinstance(item, Mapping):
        return {}

    url = normalize_value(item.get("url") or item.get("url_mobile"))

    if not is_valid_http_url(url):
        return {}

    image_url = normalize_value(item.get("socialimage"))

    if image_url and not is_valid_http_url(image_url):
        image_url = ""

    requested_language = normalize_value(item.get("_requested_language"))
    requested_theme = normalize_value(item.get("_requested_theme"))
    language = normalize_value(item.get("language")) or requested_language

    return build_standard_article(
        identifier=url,
        source=source.get("name", "GDELT"),
        title=clean_text(item.get("title")),
        text="",
        image_url=image_url,
        image_path="",
        published_at=item.get("seendate"),
        url=url,
        author="",
        language=language.lower(),
        category=requested_theme or "general",
        label="",
        dataset_role=source.get("role", "acquisition")
    )


# Validation spécifique

def validate_gdelt_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les contrôles propres à GDELT."""

    del filters, source

    if not isinstance(item, Mapping):
        return False, "resultat_gdelt_invalide"

    url = normalize_value(item.get("url") or item.get("url_mobile"))

    if not is_valid_http_url(url):
        return False, "url_gdelt_invalide"

    return True, ""


# Adaptateur et extracteur GDELT

GDELT_ADAPTER = ApiAdapter(
    source_id="gdelt",
    default_name="GDELT",
    iter_items=iter_gdelt_items,
    build_article=build_gdelt_article,
    validate_item=validate_gdelt_item
)

GDELT_EXTRACTOR = ApiExtractor(
    source_id="gdelt",
    default_name="GDELT",
    adapter=GDELT_ADAPTER,
    section_name="api_sources",
    sources_file=SOURCES_FILE
)


# Fonctions publiques

def load_gdelt_source() -> dict[str, Any]:
    """Recharge et retourne la configuration GDELT."""

    return dict(GDELT_EXTRACTOR.reload_source())


def extract_articles_from_source(
    source: Mapping[str, Any]
) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_api_from_source(source=source, adapter=GDELT_ADAPTER)


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction GDELT."""

    return GDELT_EXTRACTOR.run()


# Exécution directe

if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} article(s) GDELT extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])