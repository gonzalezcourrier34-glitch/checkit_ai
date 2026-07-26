"""Adaptateur utilisé pour extraire des articles avec GNews.

Ce module contient uniquement les traitements propres à GNews :
- authentification ;
- lecture des requêtes structurées ;
- normalisation des langues, pays et catégories ;
- construction et exécution des requêtes ;
- transformation et validation des articles.

Le moteur commun, l'orchestration et les résultats sont délégués à
ApiExtractor et aux modules génériques des extracteurs.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import datetime, timedelta, timezone
from time import monotonic, sleep
from itertools import product
from typing import Any

from config.paths import SOURCES_FILE
from src.extractors.apis.api_adapter import ApiAdapter
from src.extractors.apis.api_extractor import (
    ApiAuthenticationError,
    ApiExtractor,
    ApiRequestError,
    calculate_page_size,
    extract_api_from_source,
    fetch_json_object,
    filter_mapping_items,
    get_api_max_article_age_days,
    get_pagination_value,
    get_queries_configuration,
    get_query_configuration_values,
    get_query_keywords,
    raise_if_fatal_api_error,
    validate_api_secret
)
from src.extractors.core.extractor_results import ExtractorResult
from src.article.article_cleaner import clean_text 
from src.utils.url_utils import is_valid_http_url
from src.utils.value_utils import normalize_value
from src.utils.parsing_utils import parse_non_negative_integer
from src.utils.extractor_utils import build_standard_article

from src.logger import get_logger

logger = get_logger(__name__)

# Limites GNews

GNEWS_API_MAX_RECORDS = 100
GNEWS_DEFAULT_RECORDS_PER_REQUEST = 10
GNEWS_MAX_QUERY_LENGTH = 200

GNEWS_CATEGORIES: frozenset[str] = frozenset({
    "general", "world", "nation", "business", "technology",
    "entertainment", "sports", "science", "health"
})


# Authentification

def validate_gnews_authentication() -> str:
    """Valide et retourne la clé API GNews."""

    secret_name = GNEWS_EXTRACTOR.api_key_secret_name

    if not secret_name:
        raise ApiAuthenticationError(
            source_name=GNEWS_EXTRACTOR.name,
            reason=(
                "Le champ api_key_secret_name est absent "
                "de la configuration."
            ),
        )

    api_key = GNEWS_EXTRACTOR.api_key

    if not validate_api_secret(
        api_key,
        secret_name,
        GNEWS_EXTRACTOR.name,
    ):
        raise ApiAuthenticationError(
            source_name=GNEWS_EXTRACTOR.name,
            reason=f"Le secret {secret_name} est absent ou invalide.",
        )

    return api_key

# Requêtes configurées

def get_gnews_queries(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Retourne les blocs de requête structurés ou la source historique."""

    return get_queries_configuration(source) or [dict(source)]


def merge_gnews_query(
    source: Mapping[str, Any],
    query: Mapping[str, Any]
) -> dict[str, Any]:
    """Fusionne la configuration commune et un bloc de requête."""

    common = {key: value for key, value in source.items() if key != "queries"}
    return {**common, **dict(query)}


# Filtres

def get_keywords(source: Mapping[str, Any]) -> list[str]:
    """Retourne les mots-clés GNews normalisés."""

    keywords = [
        keyword[:GNEWS_MAX_QUERY_LENGTH].strip()
        for keyword in get_query_keywords(source)
    ]
    return list(dict.fromkeys(keyword for keyword in keywords if keyword))


def get_languages(source: Mapping[str, Any]) -> list[str]:
    """Retourne les langues structurées ou historiques."""

    return get_query_configuration_values(
        source, "languages", "language", lowercase=True
    )


def get_countries(source: Mapping[str, Any]) -> list[str]:
    """Retourne les codes pays GNews valides."""

    countries: list[str] = []

    for country in get_query_configuration_values(
        source, "countries", "country", lowercase=True
    ):
        if len(country) != 2 or not country.isalpha():
            logger.warning("Code pays GNews invalide : %s.", country)
            continue
        countries.append(country)

    return list(dict.fromkeys(countries))


def normalize_category(category: Any) -> str:
    """Normalise et valide une catégorie GNews."""

    normalized = normalize_value(category).lower()

    if not normalized:
        return ""

    if normalized not in GNEWS_CATEGORIES:
        logger.warning("Catégorie GNews non prise en charge : %s.", normalized)
        return ""

    return normalized


def get_categories(source: Mapping[str, Any]) -> list[str]:
    """Retourne uniquement les catégories reconnues par GNews."""

    categories = [
        normalized
        for category in get_query_configuration_values(
            source, "categories", "category", lowercase=True
        )
        if (normalized := normalize_category(category))
    ]
    return list(dict.fromkeys(categories))


# Pagination

def get_max_records_per_request(
    source: Mapping[str, Any],
    remaining_articles: int
) -> int:
    """Calcule le nombre d'articles à demander."""

    configured = get_pagination_value(
        source,
        "page_size",
        "max_per_request",
        default=GNEWS_DEFAULT_RECORDS_PER_REQUEST
    )
    return calculate_page_size(
        configured_value=configured,
        remaining_articles=remaining_articles,
        default=GNEWS_DEFAULT_RECORDS_PER_REQUEST,
        maximum=GNEWS_API_MAX_RECORDS
    )


# Période

def parse_gnews_date(value: Any, field_name: str) -> datetime | None:
    """Convertit une date au format ISO 8601 UTC."""

    normalized = normalize_value(value)

    if not normalized:
        return None

    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        logger.warning("Date GNews invalide pour %s : %s.", field_name, normalized)
        return None


def format_gnews_date(value: datetime) -> str:
    """Formate une date au format ISO 8601 attendu par GNews."""

    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def get_gnews_date_range(source: Mapping[str, Any]) -> tuple[str, str]:
    """Construit une période limitée à l'âge maximal autorisé."""

    max_days = max(get_api_max_article_age_days(source), 1)
    now = datetime.now(timezone.utc)
    start_date = parse_gnews_date(
        source.get("from", source.get("date_from", source.get("from_date"))),
        "from"
    )
    end_date = parse_gnews_date(
        source.get("to", source.get("date_to", source.get("to_date"))),
        "to"
    )

    if start_date and end_date and start_date > end_date:
        logger.warning("Dates GNews inversées : elles ont été permutées.")
        start_date, end_date = end_date, start_date

    if not start_date and not end_date:
        end_date, start_date = now, now - timedelta(days=max_days)
    elif start_date and not end_date:
        end_date = min(now, start_date + timedelta(days=max_days))
    elif end_date and not start_date:
        start_date = end_date - timedelta(days=max_days)

    if start_date and end_date:
        minimum_start = end_date - timedelta(days=max_days)
        if start_date < minimum_start:
            logger.warning("Période GNews réduite à %s jour(s).", max_days)
            start_date = minimum_start

    return (
        format_gnews_date(start_date) if start_date else "",
        format_gnews_date(end_date) if end_date else ""
    )


# Paramètres HTTP

def build_gnews_request_params(
    source: Mapping[str, Any],
    keyword: str,
    language: str,
    category: str,
    country: str,
    max_records: int
) -> dict[str, Any]:
    """Construit les paramètres métier envoyés à GNews."""

    requested_records = min(
        max(
            parse_non_negative_integer(
                max_records,
                GNEWS_DEFAULT_RECORDS_PER_REQUEST
            ),
            1
        ),
        GNEWS_API_MAX_RECORDS
    )
    date_from, date_to = get_gnews_date_range(source)
    params: dict[str, Any] = {"max": requested_records}
    optional_values = {
        "q": normalize_value(keyword)[:GNEWS_MAX_QUERY_LENGTH],
        "lang": normalize_value(language).lower(),
        "category": normalize_category(category),
        "country": normalize_value(country).lower(),
        "from": date_from,
        "to": date_to
    }
    params.update({
        key: value
        for key, value in optional_values.items()
        if value
    })
    return params

# Réseau

def fetch_gnews_data(
    endpoint: str,
    params: Mapping[str, Any],
    api_key: str
) -> dict[str, Any]:
    """Envoie une requête authentifiée à GNews."""

    return fetch_json_object(
        url=endpoint,
        params={**params, "apikey": api_key},
        headers={"Accept": "application/json"}
    )


def get_gnews_error_message(data: Mapping[str, Any]) -> str:
    """Extrait le message d'erreur retourné par GNews."""

    errors = data.get("errors", [])

    if isinstance(errors, list):
        messages = [
            message for error in errors
            if (message := normalize_value(error))
        ]
        if messages:
            return " | ".join(messages)

    return normalize_value(data.get("message")) or "Erreur non communiquée"


def request_gnews_articles(
    source: Mapping[str, Any],
    keyword: str,
    language: str,
    category: str,
    country: str,
    max_records: int,
    api_key: str
) -> list[dict[str, Any]]:
    """Récupère les articles pour une combinaison de filtres."""

    endpoint = normalize_value(source.get("endpoint"))

    if not is_valid_http_url(endpoint):
        raise ValueError(
            f"Endpoint GNews absent ou invalide : {endpoint or 'valeur absente'}."
        )

    params = build_gnews_request_params(
        source=source,
        keyword=keyword,
        language=language,
        category=category,
        country=country,
        max_records=max_records
    )

    requested_records = parse_non_negative_integer(
        params.get("max"), GNEWS_DEFAULT_RECORDS_PER_REQUEST
    )

    logger.debug(
        "Requête GNews : mot-clé=%s, langue=%s, catégorie=%s, pays=%s, max=%s.",
        keyword or "tous",
        language or "toutes",
        normalize_category(category) or "general",
        country or "tous",
        requested_records
    )

    data = fetch_gnews_data(
        endpoint=endpoint,
        params=params,
        api_key=api_key
    )
    
    if "errors" in data or ("articles" not in data and data.get("message")):
        error_message = get_gnews_error_message(data)
        raise_if_fatal_api_error(error_message, "GNews")
        raise ApiRequestError(
            source_name="GNews",
            reason=f"Erreur retournée par GNews : {error_message}.",
            parameters=params
        )

    articles = filter_mapping_items(data.get("articles", []), "GNews")
    return articles[:requested_records]


# Parcours

def iter_gnews_items(
    source: Mapping[str, Any],
    maximum_articles: int
) -> Iterator[tuple[str, int, Mapping[str, Any]]]:
    """Parcourt les requêtes GNews en respectant leur cadence."""

    maximum = parse_non_negative_integer(maximum_articles, 0)

    if maximum <= 0:
        return

    api_key = validate_gnews_authentication()
    request_delay = max(
        float(source.get("request_delay_seconds", 2.0) or 0.0),
        0.0
    )
    yielded_count = 0
    last_request_time: float | None = None

    for query in get_gnews_queries(source):
        query_configuration = merge_gnews_query(source, query)
        keywords = get_keywords(query_configuration) or [""]
        languages = get_languages(query_configuration) or [""]
        categories = get_categories(query_configuration) or ["general"]
        countries = get_countries(query_configuration) or [""]

        for keyword, language, category, country in product(
            keywords, languages, categories, countries
        ):
            remaining = maximum - yielded_count

            if remaining <= 0:
                return

            # Respecte le délai minimal entre deux appels GNews
            if last_request_time is not None and request_delay > 0:
                elapsed = monotonic() - last_request_time
                wait_time = request_delay - elapsed

                if wait_time > 0:
                    logger.debug(
                        "Attente GNews de %.2f seconde(s) avant la requête suivante.",
                        wait_time
                    )
                    sleep(wait_time)

            max_records = get_max_records_per_request(
                query_configuration,
                remaining
            )

            try:
                articles = request_gnews_articles(
                    source=query_configuration,
                    keyword=keyword,
                    language=language,
                    category=category,
                    country=country,
                    max_records=max_records,
                    api_key=api_key
                )
            finally:
                last_request_time = monotonic()

            identifier = (
                f"query={keyword or 'all'}|lang={language or 'all'}|"
                f"category={category or 'general'}|country={country or 'all'}"
            )

            for index, item in enumerate(articles):
                if yielded_count >= maximum:
                    return

                yield identifier, index, {
                    **item,
                    "_requested_keyword": keyword,
                    "_requested_language": language,
                    "_requested_category": category,
                    "_requested_country": country
                }
                yielded_count += 1

# Champs

def get_gnews_article_text(item: Mapping[str, Any]) -> str:
    """Retourne le meilleur contenu textuel disponible."""

    return clean_text(item.get("content")) or clean_text(item.get("description"))


def get_gnews_article_author(item: Mapping[str, Any]) -> str:
    """Retourne l'auteur ou le nom de la source."""

    author = clean_text(item.get("author"))

    if author:
        return author

    source_data = item.get("source", {})
    return (
        clean_text(source_data.get("name"))
        if isinstance(source_data, Mapping)
        else ""
    )


# Article

def build_gnews_article(
    item: Any,
    item_index: int,
    item_identifier: str,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme un résultat GNews au format CheckIt.AI."""

    del item_index

    if not isinstance(item, Mapping):
        return {}

    article_id = normalize_value(item.get("id"))
    url = normalize_value(item.get("url"))

    if url and not is_valid_http_url(url):
        url = ""

    if not article_id and not url:
        return {}

    image_url = normalize_value(item.get("image"))

    if image_url and not is_valid_http_url(image_url):
        image_url = ""

    requested_language = normalize_value(item.get("_requested_language")).lower()
    requested_category = normalize_category(item.get("_requested_category"))
    language = normalize_value(item.get("lang")).lower() or requested_language

    return build_standard_article(
        identifier=article_id or url or item_identifier,
        source=source.get("name", "GNews"),
        title=clean_text(item.get("title")),
        text=get_gnews_article_text(item),
        image_url=image_url,
        image_path="",
        published_at=item.get("publishedAt"),
        url=url,
        author=get_gnews_article_author(item),
        language=language,
        category=requested_category or "general",
        label="",
        dataset_role=source.get("role", "acquisition")
    )


# Validation

def validate_gnews_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les contrôles propres à GNews."""

    del filters, source

    if not isinstance(item, Mapping):
        return False, "resultat_gnews_invalide"

    article_id = normalize_value(item.get("id"))
    url = normalize_value(item.get("url"))

    if not article_id and not is_valid_http_url(url):
        return False, "identifiant_gnews_absent"

    if url and not is_valid_http_url(url):
        return False, "url_gnews_invalide"

    return True, ""


# Adaptateur

GNEWS_ADAPTER = ApiAdapter(
    source_id="gnews",
    default_name="GNews",
    iter_items=iter_gnews_items,
    build_article=build_gnews_article,
    validate_item=validate_gnews_item
)

GNEWS_EXTRACTOR = ApiExtractor(
    source_id="gnews",
    default_name="GNews",
    adapter=GNEWS_ADAPTER,
    section_name="api_sources",
    sources_file=SOURCES_FILE
)


# API publique

def load_gnews_source() -> dict[str, Any]:
    """Recharge et retourne la configuration GNews."""

    return dict(GNEWS_EXTRACTOR.reload_source())


def extract_articles_from_source(
    source: Mapping[str, Any]
) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_api_from_source(source=source, adapter=GNEWS_ADAPTER)


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction GNews."""

    return GNEWS_EXTRACTOR.run()


# Exécution directe

if __name__ == "__main__":
    result = extract_all_articles()
    print(
        f"{len(result.articles)} article(s) GNews extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])