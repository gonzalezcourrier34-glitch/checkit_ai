"""Adaptateur utilisé pour extraire des articles avec Mediastack.

Ce module contient uniquement les traitements propres à Mediastack :

- normalisation des filtres ;
- construction des paramètres HTTP ;
- gestion de la pagination par offset ;
- lecture des réponses Mediastack ;
- transformation des résultats en articles CheckIt.AI ;
- validation spécifique des éléments.

Le chargement, l'orchestration et la gestion des résultats sont délégués
à ApiExtractor et au service générique des extracteurs.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import date, timedelta
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
    normalize_page_limit,
    normalize_string_list,
    raise_if_fatal_api_error,
    validate_api_secret
)
from src.logger import get_logger
from src.extractors.core.extractor_results import ExtractorResult
from src.article.article_cleaner import clean_text
from src.utils.url_utils import is_valid_http_url
from src.utils.value_utils import normalize_value
from src.utils.parsing_utils import parse_non_negative_integer
from src.utils.extractor_utils import build_standard_article


logger = get_logger(__name__)


# Limites Mediastack

MEDIASTACK_MAX_LIMIT = 100
MEDIASTACK_DEFAULT_LIMIT = 100
MEDIASTACK_DEFAULT_MAX_PAGES = 5
MEDIASTACK_MAX_PAGES = 100
MEDIASTACK_MAX_KEYWORD_LENGTH = 500

MEDIASTACK_CATEGORIES: frozenset[str] = frozenset({
    "general", "business", "entertainment", "health",
    "science", "sports", "technology"
})

MEDIASTACK_SORT_VALUES: frozenset[str] = frozenset({
    "published_desc", "published_asc", "popularity"
})


# Authentification

def validate_mediastack_authentication() -> str:
    """Valide et retourne la clé API Mediastack."""

    secret_name = MEDIASTACK_EXTRACTOR.api_key_secret_name

    if not secret_name:
        raise ApiAuthenticationError(
            source_name=MEDIASTACK_EXTRACTOR.name,
            reason=(
                "Le champ api_key_secret_name est absent "
                "de la configuration."
            )
        )

    api_key = MEDIASTACK_EXTRACTOR.api_key

    if not validate_api_secret(
        api_key,
        secret_name,
        MEDIASTACK_EXTRACTOR.name
    ):
        raise ApiAuthenticationError(
            source_name=MEDIASTACK_EXTRACTOR.name,
            reason=f"Le secret {secret_name} est absent ou invalide."
        )

    return api_key

# Requêtes configurées

def get_mediastack_queries(
    source: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Retourne les blocs de requête structurés ou la source historique."""

    return get_queries_configuration(source) or [dict(source)]

def merge_mediastack_query(
    source: Mapping[str, Any],
    query: Mapping[str, Any]
) -> dict[str, Any]:
    """Fusionne une requête avec la configuration commune."""

    common = {key: value for key, value in source.items() if key != "queries"}
    return {**common, **dict(query)}


# Filtres

def get_keywords(source: Mapping[str, Any]) -> list[str]:
    """Retourne les mots-clés configurés."""

    keywords=[
        keyword[:MEDIASTACK_MAX_KEYWORD_LENGTH].strip()
        for keyword in get_query_keywords(source)
    ]

    return list(dict.fromkeys(keyword for keyword in keywords if keyword))


def get_languages(source: Mapping[str, Any]) -> list[str]:
    """Retourne les langues configurées en minuscules."""

    return get_query_configuration_values(
        source,"languages","language",lowercase=True
    )


def get_countries(source: Mapping[str, Any]) -> list[str]:
    """Retourne les codes pays ISO valides."""

    countries: list[str] = []

    for country in get_query_configuration_values(
        source,"countries","country",lowercase=True
    ):
        if len(country) != 2 or not country.isalpha():
            logger.warning(
                "Code pays Mediastack invalide : %s.",
                country
            )
            continue

        countries.append(country)

    return list(dict.fromkeys(countries))


def normalize_mediastack_category(category: Any) -> str:
    """Normalise et vérifie une catégorie Mediastack."""

    normalized = normalize_value(category).lower()

    if not normalized:
        return ""

    if normalized not in MEDIASTACK_CATEGORIES:
        logger.warning(
            "Catégorie Mediastack non prise en charge : %s.",
            normalized
        )
        return ""

    return normalized


def get_categories(source: Mapping[str, Any]) -> list[str]:
    """Retourne uniquement les catégories valides."""

    categories = [
        normalized
        for category in get_query_configuration_values(
            source,"categories","category"
        )
        if (normalized := normalize_mediastack_category(category))
    ]

    return list(dict.fromkeys(categories))


def normalize_mediastack_sort(value: Any) -> str:
    """Normalise le type de tri Mediastack."""

    normalized = normalize_value(value).lower()

    if not normalized:
        return "published_desc"

    if normalized not in MEDIASTACK_SORT_VALUES:
        logger.warning(
            "Tri Mediastack inconnu : %s. published_desc sera utilisé.",
            normalized
        )
        return "published_desc"

    return normalized


def build_sources_filter(source: Mapping[str, Any]) -> str:
    """Construit le filtre des sources incluses et exclues."""

    included = normalize_string_list(
        source.get("sources"),
        lowercase=True
    )
    excluded = normalize_string_list(
        source.get("excluded_sources"),
        lowercase=True
    )
    values = included + [f"-{item}" for item in excluded]

    return ",".join(dict.fromkeys(values))


# Période

def parse_mediastack_date(
    value: Any,
    field_name: str
) -> date | None:
    """Convertit une date ISO en objet date."""

    normalized = normalize_value(value)

    if not normalized:
        return None

    try:
        return date.fromisoformat(normalized)

    except ValueError:
        logger.warning(
            "Date Mediastack invalide pour %s : %s.",
            field_name,
            normalized
        )
        return None


def build_mediastack_date_filter(
    source: Mapping[str, Any]
) -> str:
    """Construit une période ISO limitée à l'âge maximal autorisé."""

    raw_date = normalize_value(source.get("date"))
    raw_from = source.get("date_from")
    raw_to = source.get("date_to")

    if raw_date:
        date_parts = [
            part.strip()
            for part in raw_date.split(",", 1)
        ]
        raw_from = date_parts[0]
        raw_to = (
            date_parts[1]
            if len(date_parts) == 2
            else date_parts[0]
        )

    date_from = parse_mediastack_date(
        raw_from,
        "date_from"
    )
    date_to = parse_mediastack_date(
        raw_to,
        "date_to"
    )
    today = date.today()
    max_days = max(
        get_api_max_article_age_days(source),
        1
    )

    if date_from is None and date_to is None:
        date_to = today
        date_from = date_to - timedelta(days=max_days)

    elif date_from is None and date_to is not None:
        date_from = date_to - timedelta(days=max_days)

    elif date_from is not None and date_to is None:
        date_to = min(
            date_from + timedelta(days=max_days),
            today
        )

    if date_from is None or date_to is None:
        raise ValueError(
            "Impossible de construire la période Mediastack."
        )

    if date_from > date_to:
        logger.warning(
            "Période Mediastack inversée : %s > %s. "
            "Les dates sont permutées.",
            date_from.isoformat(),
            date_to.isoformat()
        )
        date_from, date_to = date_to, date_from

    earliest_allowed = date_to - timedelta(days=max_days)

    if date_from < earliest_allowed:
        logger.warning(
            "Période Mediastack limitée à %s jour(s).",
            max_days
        )
        date_from = earliest_allowed

    return (
        f"{date_from.isoformat()},"
        f"{date_to.isoformat()}"
    )


# Pagination

def get_page_limit(
    source: Mapping[str, Any],
    remaining_articles: int
) -> int:
    """Calcule le nombre d'articles demandé par page."""

    return calculate_page_size(
        configured_value=get_pagination_value(
            source,"limit",default=MEDIASTACK_DEFAULT_LIMIT
        ),
        remaining_articles=remaining_articles,
        default=MEDIASTACK_DEFAULT_LIMIT,
        maximum=MEDIASTACK_MAX_LIMIT
    )


def get_max_pages(source: Mapping[str, Any]) -> int:
    """Retourne le nombre maximal de pages à parcourir."""

    return normalize_page_limit(
        value=get_pagination_value(
            source,"max_pages",default=MEDIASTACK_DEFAULT_MAX_PAGES
        ),
        default=MEDIASTACK_DEFAULT_MAX_PAGES,
        maximum=MEDIASTACK_MAX_PAGES
    )


# Paramètres HTTP

def build_mediastack_request_params(
    source: Mapping[str, Any],
    keyword: str,
    language: str,
    country: str,
    category: str,
    limit: int,
    offset: int
) -> dict[str, Any]:
    """Construit les paramètres métier envoyés à Mediastack."""

    params: dict[str, Any] = {
        "limit": calculate_page_size(
            configured_value=limit,
            remaining_articles=limit,
            default=MEDIASTACK_DEFAULT_LIMIT,
            maximum=MEDIASTACK_MAX_LIMIT
        ),
        "offset": parse_non_negative_integer(offset, 0),
        "sort": normalize_mediastack_sort(source.get("sort")),
        "date": build_mediastack_date_filter(source),
    }

    optional_values = {
        "keywords": normalize_value(keyword)[:MEDIASTACK_MAX_KEYWORD_LENGTH],
        "languages": normalize_value(language).lower(),
        "countries": normalize_value(country).lower(),
        "categories": normalize_mediastack_category(category),
        "sources": build_sources_filter(source),
    }

    params.update({
        key: value
        for key, value in optional_values.items()
        if value
    })

    return params

# Réseau

def fetch_mediastack_page(
    endpoint: str,
    params: Mapping[str, Any],
    api_key: str
) -> dict[str, Any]:
    """Envoie une requête à Mediastack et retourne son objet JSON."""

    return fetch_json_object(
        url=endpoint,
        params={**params, "access_key": api_key},
        headers={"Accept": "application/json"}
    )


def get_mediastack_error_details(
    data: Mapping[str, Any]
) -> tuple[str, str]:
    """Extrait le code et le message d'une erreur Mediastack."""

    error_data = data.get("error", {})
    error_data = error_data if isinstance(error_data, Mapping) else {}

    context = error_data.get("context", {})
    context = context if isinstance(context, Mapping) else {}

    code = (
        normalize_value(error_data.get("code"))
        or normalize_value(data.get("code"))
        or "inconnu"
    )
    message = (
        normalize_value(error_data.get("message"))
        or normalize_value(context.get("message"))
        or normalize_value(data.get("message"))
        or "non communiqué"
    )

    return code, message


def request_mediastack_page(
    source: Mapping[str, Any],
    keyword: str,
    language: str,
    country: str,
    category: str,
    limit: int,
    offset: int,
    api_key: str
) -> tuple[list[dict[str, Any]], int, int]:
    """Récupère une page de résultats Mediastack."""

    endpoint = normalize_value(
        source.get("endpoint")
    )

    if not is_valid_http_url(endpoint):
        raise ValueError(
            "Endpoint Mediastack absent ou invalide : "
            f"{endpoint or 'valeur absente'}."
        )

    params = build_mediastack_request_params(
        source=source,
        keyword=keyword,
        language=language,
        country=country,
        category=category,
        limit=limit,
        offset=offset
    )

    logger.debug(
        "Requête Mediastack : mot-clé='%s', langue=%s, pays=%s, "
        "catégorie=%s, limite=%s, offset=%s.",
        keyword or "tous",
        language or "toutes",
        country or "tous",
        category or "toutes",
        params["limit"],
        params["offset"]
    )

    data = fetch_mediastack_page(
        endpoint=endpoint,
        params=params,
        api_key=api_key
    )

    if "error" in data:
        error_code, error_message = (
            get_mediastack_error_details(data)
        )
        error_details = (
            f"{error_code} : {error_message}"
        )

        # Mediastack peut retourner une erreur dans un JSON valide.
        raise_if_fatal_api_error(
            error_details,
            MEDIASTACK_EXTRACTOR.name
        )

        raise ApiRequestError(
            source_name=MEDIASTACK_EXTRACTOR.name,
            reason=f"Erreur Mediastack : {error_details}.",
            parameters=params
        )

    articles = filter_mapping_items(
        items=data.get("data", []),
        source_name="Mediastack"
    )
    pagination = data.get("pagination", {})
    pagination = pagination if isinstance(pagination, Mapping) else {}
    total_results = parse_non_negative_integer(
        pagination.get("total", 0),
        0
    )
    returned_offset = parse_non_negative_integer(
        pagination.get("offset", offset),
        offset
    )

    return articles, total_results, returned_offset


def request_mediastack_articles(
    source: Mapping[str, Any],
    keyword: str,
    language: str,
    country: str,
    category: str,
    max_articles: int,
    api_key: str
) -> list[dict[str, Any]]:
    """Récupère plusieurs pages Mediastack."""

    maximum = parse_non_negative_integer(max_articles, 0)

    if maximum <= 0:
        return []

    articles: list[dict[str, Any]] = []
    offset = 0

    for page_number in range(
        1,
        get_max_pages(source) + 1
    ):
        remaining = maximum - len(articles)

        if remaining <= 0:
            break

        limit = get_page_limit(source, remaining)
        page_articles, total_results, returned_offset = request_mediastack_page(
            source=source,
            keyword=keyword,
            language=language,
            country=country,
            category=category,
            limit=limit,
            offset=offset,
            api_key=api_key
        )

        if not page_articles:
            logger.debug(
                "Pagination Mediastack arrêtée à la page %s.",
                page_number
            )
            break

        articles.extend(page_articles)
        next_offset = returned_offset + len(page_articles)

        if len(articles) >= maximum:
            break

        if total_results > 0 and next_offset >= total_results:
            break

        if len(page_articles) < limit:
            break

        if next_offset <= offset:
            logger.warning(
                "Offset Mediastack inchangé. "
                "Pagination interrompue."
            )
            break

        offset = next_offset

    return articles[:maximum]


# Parcours

def iter_mediastack_items(
    source: Mapping[str, Any],
    maximum_articles: int
) -> Iterator[tuple[str, int, Mapping[str, Any]]]:
    """Parcourt toutes les combinaisons configurées."""

    maximum = parse_non_negative_integer(maximum_articles, 0)

    if maximum <= 0:
        return

    api_key = validate_mediastack_authentication()
    yielded_count = 0

    for query_block in get_mediastack_queries(source):
        query_configuration = merge_mediastack_query(
            source,
            query_block
        )

        keywords = get_keywords(
            query_configuration
        ) or [""]

        languages = get_languages(
            query_configuration
        ) or [""]

        countries = get_countries(
            query_configuration
        ) or [""]

        categories = get_categories(
            query_configuration
        ) or [""]

        for keyword, language, country, category in product(
            keywords, languages, countries, categories
        ):
            remaining = maximum - yielded_count

            if remaining <= 0:
                return

            articles = request_mediastack_articles(
                source=query_configuration,
                keyword=keyword,
                language=language,
                country=country,
                category=category,
                max_articles=remaining,
                api_key=api_key
            )
            identifier = (
                f"keyword={keyword or 'all'}|"
                f"language={language or 'all'}|"
                f"country={country or 'all'}|"
                f"category={category or 'all'}"
            )

            for index, item in enumerate(articles):
                if yielded_count >= maximum:
                    return

                yield identifier, index, {
                    **item,
                    "_requested_keyword": keyword,
                    "_requested_language": language,
                    "_requested_country": country,
                    "_requested_category": category
                }
                yielded_count += 1


# Champs

def get_mediastack_article_text(
    item: Mapping[str, Any]
) -> str:
    """Retourne le meilleur contenu textuel."""

    return clean_text(item.get("description")) or clean_text(item.get("content"))


def get_mediastack_publisher(item: Mapping[str, Any]) -> str:
    """Retourne le nom du média éditorial fourni par Mediastack."""

    return clean_text(item.get("source"))

def build_mediastack_identifier(
    item: Mapping[str, Any],
    item_identifier: str
) -> str:
    """Construit un identifiant stable."""

    url = normalize_value(item.get("url"))

    if is_valid_http_url(url):
        return url

    return (
        f"mediastack:{item_identifier}:"
        f"{normalize_value(item.get('published_at'))}:"
        f"{clean_text(item.get('title'))}"
    )


# Article

def build_mediastack_article(
    item: Any,
    item_index: int,
    item_identifier: str,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme un résultat Mediastack au format CheckIt.AI."""

    del item_index

    if not isinstance(item, Mapping):
        return {}

    url = normalize_value(item.get("url"))

    if url and not is_valid_http_url(url):
        url = ""

    image_url = normalize_value(item.get("image"))

    if image_url and not is_valid_http_url(image_url):
        image_url = ""

    requested_language = normalize_value(item.get("_requested_language")).lower()
    requested_country = normalize_value(item.get("_requested_country")).lower()
    requested_category = normalize_value(item.get("_requested_category")).lower()
    api_language = normalize_value(item.get("language")).lower()
    api_country = normalize_value(item.get("country")).lower()
    api_category = normalize_mediastack_category(item.get("category"))

    # La source identifie l'API technique. Le média reste dans les métadonnées.
    return build_standard_article(
        identifier=build_mediastack_identifier(item, item_identifier),
        source=source.get("name", "mediastack"),
        title=clean_text(item.get("title")),
        text=get_mediastack_article_text(item),
        image_url=image_url,
        image_path="",
        published_at=item.get("published_at"),
        url=url,
        author=clean_text(item.get("author")),
        language=api_language or requested_language,
        category=(
            api_category
            or requested_category
            or normalize_value(source.get("category"))
            or "general"
        ),
        label="",
        dataset_role=source.get("role", "acquisition"),
        metadata={
            "publisher": get_mediastack_publisher(item),
            "country": api_country or requested_country
        }
    )


# Validation

def validate_mediastack_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les contrôles propres à Mediastack."""

    del filters, source

    if not isinstance(item, Mapping):
        return False, "resultat_mediastack_invalide"

    if not is_valid_http_url(
        normalize_value(item.get("url"))
    ):
        return False, "url_mediastack_invalide"

    if not clean_text(item.get("title")):
        return False, "titre_mediastack_absent"

    return True, ""


# Adaptateur

MEDIASTACK_ADAPTER = ApiAdapter(
    source_id="mediastack",
    default_name="Mediastack",
    iter_items=iter_mediastack_items,
    build_article=build_mediastack_article,
    validate_item=validate_mediastack_item
)

MEDIASTACK_EXTRACTOR = ApiExtractor(
    source_id="mediastack",
    default_name="Mediastack",
    adapter=MEDIASTACK_ADAPTER,
    section_name="api_sources",
    sources_file=SOURCES_FILE
)


# API publique

def load_mediastack_source() -> dict[str, Any]:
    """Recharge et retourne la configuration Mediastack."""

    return dict(MEDIASTACK_EXTRACTOR.reload_source())


def extract_articles_from_source(
    source: Mapping[str, Any]
) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_api_from_source(
        source=source,
        adapter=MEDIASTACK_ADAPTER
    )


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction Mediastack."""

    return MEDIASTACK_EXTRACTOR.run()


# Exécution directe

if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} article(s) Mediastack extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])