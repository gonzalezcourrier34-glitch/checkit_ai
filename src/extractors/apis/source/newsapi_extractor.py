"""Adaptateur utilisé pour extraire des articles avec NewsAPI.

Ce module contient uniquement les traitements propres à NewsAPI :
- authentification ;
- lecture des requêtes structurées ;
- normalisation des recherches, langues, tris et dates ;
- construction et exécution des requêtes ;
- pagination par numéro de page ;
- transformation et validation des articles.

Le moteur commun, l'orchestration et les résultats sont délégués à
ApiExtractor et aux modules génériques des extracteurs.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import datetime, timedelta, timezone
from itertools import product
from typing import Any

from config.paths import SOURCES_FILE
from src.article.processing.article_cleaner import clean_text
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
    normalize_page_limit,
    normalize_string_list,
    raise_if_fatal_api_error,
    validate_api_secret
)
from src.extractors.core.extractor_results import ExtractorResult
from src.logger import get_logger
from src.utils.date_utils import parse_datetime
from src.utils.extractor_utils import build_standard_article
from src.utils.parsing_utils import parse_non_negative_integer
from src.utils.url_utils import is_valid_http_url
from src.utils.value_utils import normalize_value

logger = get_logger(__name__)


# Limites NewsAPI

NEWSAPI_MAX_PAGE_SIZE = 100
NEWSAPI_DEFAULT_PAGE_SIZE = 100
NEWSAPI_DEFAULT_MAX_PAGES = 5
NEWSAPI_MAX_PAGE_NUMBER = 100
NEWSAPI_MAX_QUERY_LENGTH = 500

NEWSAPI_SORT_VALUES: frozenset[str] = frozenset({
    "relevancy", "popularity", "publishedat"
})

NEWSAPI_LANGUAGES: frozenset[str] = frozenset({
    "ar", "de", "en", "es", "fr", "he", "it",
    "nl", "no", "pt", "ru", "sv", "ud", "zh"
})


# Authentification

def validate_newsapi_authentication() -> str:
    """Valide et retourne la clé API NewsAPI."""

    secret_name = NEWSAPI_EXTRACTOR.api_key_secret_name

    if not secret_name:
        raise ApiAuthenticationError(
            source_name=NEWSAPI_EXTRACTOR.name,
            reason=(
                "Le champ api_key_secret_name est absent "
                "de la configuration."
            )
        )

    api_key = NEWSAPI_EXTRACTOR.api_key

    if not validate_api_secret(
        api_key,
        secret_name,
        NEWSAPI_EXTRACTOR.name
    ):
        raise ApiAuthenticationError(
            source_name=NEWSAPI_EXTRACTOR.name,
            reason=f"Le secret {secret_name} est absent ou invalide."
        )

    return api_key


# Requêtes configurées

def get_newsapi_queries(
    source: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Retourne les blocs de requête structurés ou la source historique."""

    return get_queries_configuration(source) or [dict(source)]


def merge_newsapi_query(
    source: Mapping[str, Any],
    query: Mapping[str, Any]
) -> dict[str, Any]:
    """Fusionne la configuration commune et un bloc de requête."""

    common = {key: value for key, value in source.items() if key != "queries"}
    return {**common, **dict(query)}


# Paramètres métier

def format_list_value(value: Any) -> str:
    """Transforme une collection en texte séparé par des virgules."""

    return ",".join(normalize_string_list(value))


def get_queries(source: Mapping[str, Any]) -> list[str]:
    """Retourne les recherches NewsAPI normalisées."""

    queries = [
        query[:NEWSAPI_MAX_QUERY_LENGTH].strip()
        for query in get_query_keywords(source)
    ]
    return list(dict.fromkeys(query for query in queries if query))


def normalize_newsapi_language(language: Any) -> str:
    """Normalise et valide un code de langue NewsAPI."""

    normalized = normalize_value(language).lower()

    if not normalized:
        return ""

    if normalized not in NEWSAPI_LANGUAGES:
        logger.warning(
            "Langue NewsAPI non prise en charge : %s.",
            normalized
        )
        return ""

    return normalized


def get_languages(source: Mapping[str, Any]) -> list[str]:
    """Retourne les langues reconnues par NewsAPI."""

    languages = [
        normalized
        for language in get_query_configuration_values(
            source, "languages", "language", lowercase=True
        )
        if (normalized := normalize_newsapi_language(language))
    ]
    return list(dict.fromkeys(languages))


def normalize_newsapi_sort(value: Any) -> str:
    """Normalise et valide le tri NewsAPI."""

    normalized = normalize_value(value).lower()

    if not normalized:
        return "publishedAt"

    if normalized not in NEWSAPI_SORT_VALUES:
        logger.warning(
            "Tri NewsAPI inconnu : %s. publishedAt sera utilisé.",
            normalized
        )
        return "publishedAt"

    return "publishedAt" if normalized == "publishedat" else normalized


# Dates

def parse_newsapi_date(
    value: Any,
    field_name: str
) -> datetime | None:
    """Convertit une date NewsAPI."""

    parsed_date = parse_datetime(value)

    if value and parsed_date is None:
        logger.warning(
            "Date NewsAPI invalide pour %s : %r.",
            field_name,
            value
        )

    return parsed_date


def format_newsapi_date(value: datetime) -> str:
    """Formate une date au format ISO 8601 attendu par NewsAPI."""

    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def get_newsapi_date_range(
    source: Mapping[str, Any]
) -> tuple[str, str]:
    """Construit une période limitée à l'âge maximal autorisé."""

    max_days = max(get_api_max_article_age_days(source), 1)
    now = datetime.now(timezone.utc)
    start_date = parse_newsapi_date(source.get("date_from"), "date_from")
    end_date = parse_newsapi_date(source.get("date_to"), "date_to")

    if start_date and end_date and start_date > end_date:
        logger.warning("Dates NewsAPI inversées : elles ont été permutées.")
        start_date, end_date = end_date, start_date

    if not start_date and not end_date:
        end_date = now
        start_date = end_date - timedelta(days=max_days)
    elif start_date and not end_date:
        end_date = min(now, start_date + timedelta(days=max_days))
    elif end_date and not start_date:
        start_date = end_date - timedelta(days=max_days)

    if start_date and end_date:
        minimum_start = end_date - timedelta(days=max_days)

        if start_date < minimum_start:
            logger.warning("Période NewsAPI réduite à %s jour(s).", max_days)
            start_date = minimum_start

    return (
        format_newsapi_date(start_date) if start_date else "",
        format_newsapi_date(end_date) if end_date else ""
    )


# Pagination

def get_page_size(
    source: Mapping[str, Any],
    remaining_articles: int
) -> int:
    """Calcule le nombre de résultats à demander par page."""

    configured = get_pagination_value(
        source,
        "page_size",
        default=NEWSAPI_DEFAULT_PAGE_SIZE
    )
    return calculate_page_size(
        configured_value=configured,
        remaining_articles=remaining_articles,
        default=NEWSAPI_DEFAULT_PAGE_SIZE,
        maximum=NEWSAPI_MAX_PAGE_SIZE
    )


def get_max_pages(source: Mapping[str, Any]) -> int:
    """Retourne le nombre maximal de pages à parcourir."""

    return normalize_page_limit(
        value=get_pagination_value(
            source,
            "max_pages",
            default=NEWSAPI_DEFAULT_MAX_PAGES
        ),
        default=NEWSAPI_DEFAULT_MAX_PAGES,
        maximum=NEWSAPI_MAX_PAGE_NUMBER
    )


# Paramètres HTTP

def build_newsapi_request_params(
    source: Mapping[str, Any],
    query: str,
    language: str,
    page_number: int,
    page_size: int
) -> dict[str, Any]:
    """Construit les paramètres envoyés à NewsAPI."""

    requested_page_size = calculate_page_size(
        configured_value=page_size,
        remaining_articles=page_size,
        default=NEWSAPI_DEFAULT_PAGE_SIZE,
        maximum=NEWSAPI_MAX_PAGE_SIZE
    )
    params: dict[str, Any] = {
        "q": normalize_value(query)[:NEWSAPI_MAX_QUERY_LENGTH],
        "sortBy": normalize_newsapi_sort(source.get("sort_by")),
        "pageSize": requested_page_size,
        "page": min(
            max(parse_non_negative_integer(page_number, 1), 1),
            NEWSAPI_MAX_PAGE_NUMBER
        )
    }
    date_from, date_to = get_newsapi_date_range(source)
    optional_values = {
        "language": normalize_newsapi_language(language),
        "from": date_from,
        "to": date_to,
        "sources": format_list_value(source.get("sources")),
        "domains": format_list_value(source.get("domains")),
        "excludeDomains": format_list_value(source.get("excluded_domains")),
        "searchIn": format_list_value(source.get("search_in"))
    }
    params.update({
        key: value
        for key, value in optional_values.items()
        if value
    })
    return params


# Réseau

def fetch_newsapi_page(
    endpoint: str,
    params: Mapping[str, Any],
    api_key: str
) -> dict[str, Any]:
    """Envoie une requête authentifiée à NewsAPI."""

    return fetch_json_object(
        url=endpoint,
        params=params,
        headers={
            "Accept": "application/json",
            "X-Api-Key": api_key
        }
    )


def get_newsapi_error_details(
    data: Mapping[str, Any]
) -> tuple[str, str]:
    """Extrait le code et le message d'une erreur NewsAPI."""

    code = normalize_value(data.get("code")) or "inconnu"
    message = normalize_value(data.get("message")) or "non communiqué"
    return code, message


def request_newsapi_page(
    source: Mapping[str, Any],
    query: str,
    language: str,
    page_number: int,
    page_size: int,
    api_key: str
) -> tuple[list[dict[str, Any]], int]:
    """Récupère une page de résultats NewsAPI."""

    endpoint = normalize_value(source.get("endpoint"))

    if not is_valid_http_url(endpoint):
        raise ValueError(
            f"Endpoint NewsAPI absent ou invalide : "
            f"{endpoint or 'valeur absente'}."
        )

    normalized_query = normalize_value(query)

    if not normalized_query:
        raise ValueError("NewsAPI exige une requête non vide.")

    params = build_newsapi_request_params(
        source=source,
        query=normalized_query,
        language=language,
        page_number=page_number,
        page_size=page_size
    )

    logger.debug(
        "Requête NewsAPI : q=%s, langue=%s, page=%s, taille=%s.",
        normalized_query,
        normalize_value(language).lower() or "toutes",
        params["page"],
        params["pageSize"]
    )

    data = fetch_newsapi_page(
        endpoint=endpoint,
        params=params,
        api_key=api_key
    )
    status = normalize_value(data.get("status")).lower()

    if status != "ok":
        error_code, error_message = get_newsapi_error_details(data)
        error_details = f"{error_code} : {error_message}"

        # NewsAPI peut retourner une erreur dans un objet JSON valide.
        raise_if_fatal_api_error(error_details, NEWSAPI_EXTRACTOR.name)
        raise ApiRequestError(
            source_name=NEWSAPI_EXTRACTOR.name,
            reason=f"Erreur NewsAPI : {error_details}.",
            parameters=params
        )

    articles = filter_mapping_items(data.get("articles", []), "NewsAPI")
    total_results = parse_non_negative_integer(data.get("totalResults"), 0)
    return articles, total_results


def request_newsapi_articles(
    source: Mapping[str, Any],
    query: str,
    language: str,
    max_articles: int,
    api_key: str
) -> list[dict[str, Any]]:
    """Récupère plusieurs pages NewsAPI."""

    maximum = parse_non_negative_integer(max_articles, 0)

    if maximum <= 0:
        return []

    articles: list[dict[str, Any]] = []

    for page_number in range(1, get_max_pages(source) + 1):
        remaining = maximum - len(articles)

        if remaining <= 0:
            break

        page_size = get_page_size(source, remaining)
        page_articles, total_results = request_newsapi_page(
            source=source,
            query=query,
            language=language,
            page_number=page_number,
            page_size=page_size,
            api_key=api_key
        )

        if not page_articles:
            logger.debug(
                "Pagination NewsAPI arrêtée à la page %s.",
                page_number
            )
            break

        articles.extend(page_articles[:remaining])

        if len(articles) >= maximum:
            break

        if total_results > 0 and len(articles) >= total_results:
            break

        if len(page_articles) < page_size:
            break

    return articles[:maximum]


# Parcours

def iter_newsapi_items(
    source: Mapping[str, Any],
    maximum_articles: int
) -> Iterator[tuple[str, int, Mapping[str, Any]]]:
    """Parcourt les recherches et langues NewsAPI configurées."""

    maximum = parse_non_negative_integer(maximum_articles, 0)

    if maximum <= 0:
        return

    api_key = validate_newsapi_authentication()
    yielded_count = 0

    for query_block in get_newsapi_queries(source):
        query_configuration = merge_newsapi_query(source, query_block)
        queries = get_queries(query_configuration)

        if not queries:
            raise ValueError("Aucune requête configurée pour NewsAPI.")

        languages = get_languages(query_configuration) or [""]

        for query, language in product(queries, languages):
            remaining = maximum - yielded_count

            if remaining <= 0:
                return

            articles = request_newsapi_articles(
                source=query_configuration,
                query=query,
                language=language,
                max_articles=remaining,
                api_key=api_key
            )
            identifier = (
                f"query={query}|"
                f"language={language or 'all'}"
            )

            for index, item in enumerate(articles):
                if yielded_count >= maximum:
                    return

                yield identifier, index, {
                    **item,
                    "_requested_query": query,
                    "_requested_language": language
                }
                yielded_count += 1


# Champs

def get_newsapi_publisher(item: Mapping[str, Any]) -> str:
    """Retourne le média éditorial fourni par NewsAPI."""

    source_data = item.get("source", {})

    if not isinstance(source_data, Mapping):
        return ""

    return clean_text(source_data.get("name"))


def get_newsapi_article_text(item: Mapping[str, Any]) -> str:
    """Retourne le meilleur contenu textuel disponible."""

    return clean_text(item.get("content")) or clean_text(item.get("description"))


def build_newsapi_identifier(
    item: Mapping[str, Any],
    item_identifier: str
) -> str:
    """Construit un identifiant stable."""

    url = normalize_value(item.get("url"))

    if is_valid_http_url(url):
        return url

    return (
        f"newsapi:{item_identifier}:"
        f"{normalize_value(item.get('publishedAt'))}:"
        f"{clean_text(item.get('title'))}"
    )


# Article

def build_newsapi_article(
    item: Any,
    item_index: int,
    item_identifier: str,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme un résultat NewsAPI au format CheckIt.AI."""

    del item_index

    if not isinstance(item, Mapping):
        return {}

    url = normalize_value(item.get("url"))

    if url and not is_valid_http_url(url):
        url = ""

    image_url = normalize_value(item.get("urlToImage"))

    if image_url and not is_valid_http_url(image_url):
        image_url = ""

    requested_language = normalize_newsapi_language(
        item.get("_requested_language")
    )
    requested_query = clean_text(item.get("_requested_query"))

    # "source" identifie l'API technique. Le média éditorial reste en metadata.
    return build_standard_article(
        identifier=build_newsapi_identifier(item, item_identifier),
        source=source.get("name", "newsapi"),
        title=clean_text(item.get("title")),
        text=get_newsapi_article_text(item),
        image_url=image_url,
        image_path="",
        published_at=item.get("publishedAt"),
        url=url,
        author=clean_text(item.get("author")),
        language=requested_language,
        category=(
            requested_query
            or normalize_value(source.get("category"))
            or "general"
        ),
        label="",
        dataset_role=source.get("role", "acquisition"),
        metadata={"publisher": get_newsapi_publisher(item)}
    )


# Validation

def validate_newsapi_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les contrôles propres à NewsAPI."""

    del filters, source

    if not isinstance(item, Mapping):
        return False, "resultat_newsapi_invalide"

    if not is_valid_http_url(normalize_value(item.get("url"))):
        return False, "url_newsapi_invalide"

    if not clean_text(item.get("title")):
        return False, "titre_newsapi_absent"

    return True, ""


# Adaptateur

NEWSAPI_ADAPTER = ApiAdapter(
    source_id="newsapi",
    default_name="NewsAPI",
    iter_items=iter_newsapi_items,
    build_article=build_newsapi_article,
    validate_item=validate_newsapi_item
)

NEWSAPI_EXTRACTOR = ApiExtractor(
    source_id="newsapi",
    default_name="NewsAPI",
    adapter=NEWSAPI_ADAPTER,
    section_name="api_sources",
    sources_file=SOURCES_FILE
)


# API publique

def load_newsapi_source() -> dict[str, Any]:
    """Recharge et retourne la configuration NewsAPI."""

    return dict(NEWSAPI_EXTRACTOR.reload_source())


def extract_articles_from_source(
    source: Mapping[str, Any]
) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_api_from_source(source=source, adapter=NEWSAPI_ADAPTER)


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction NewsAPI."""

    return NEWSAPI_EXTRACTOR.run()


# Exécution directe

if __name__ == "__main__":
    result = extract_all_articles()
    print(
        f"{len(result.articles)} article(s) NewsAPI extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])