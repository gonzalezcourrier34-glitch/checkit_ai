"""Adaptateur utilisé pour extraire des articles avec NewsData.io.

Ce module contient uniquement les traitements propres à NewsData.io :
- authentification ;
- lecture des requêtes structurées ;
- normalisation des recherches, langues et catégories ;
- construction et exécution des requêtes ;
- pagination par jeton ;
- transformation et validation des articles.

Le moteur commun, l'orchestration et les résultats sont délégués à
ApiExtractor et aux modules génériques des extracteurs.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from itertools import product
from typing import Any

from config.paths import SOURCES_FILE
from src.article.article_cleaner import clean_text
from src.extractors.apis.api_adapter import ApiAdapter
from src.extractors.apis.api_extractor import (
    ApiAuthenticationError,
    ApiExtractor,
    ApiRequestError,
    extract_api_from_source,
    fetch_json_object,
    filter_mapping_items,
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
from src.utils.extractor_utils import build_standard_article
from src.utils.parsing_utils import parse_boolean, parse_non_negative_integer
from src.utils.url_utils import is_valid_http_url
from src.utils.value_utils import normalize_value

logger = get_logger(__name__)


# Limites NewsData.io

NEWSDATA_DEFAULT_MAX_PAGES = 5
NEWSDATA_MAX_PAGES = 100
NEWSDATA_MAX_QUERY_LENGTH = 500


# Authentification

def validate_newsdata_authentication() -> str:
    """Valide et retourne la clé API NewsData.io."""

    secret_name = NEWSDATA_EXTRACTOR.api_key_secret_name

    if not secret_name:
        raise ApiAuthenticationError(
            source_name=NEWSDATA_EXTRACTOR.name,
            reason=(
                "Le champ api_key_secret_name est absent "
                "de la configuration."
            )
        )

    api_key = NEWSDATA_EXTRACTOR.api_key

    if not validate_api_secret(
        api_key,
        secret_name,
        NEWSDATA_EXTRACTOR.name
    ):
        raise ApiAuthenticationError(
            source_name=NEWSDATA_EXTRACTOR.name,
            reason=f"Le secret {secret_name} est absent ou invalide."
        )

    return api_key


# Requêtes configurées

def get_newsdata_queries(
    source: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Retourne les blocs de requête structurés ou la source historique."""

    return get_queries_configuration(source) or [dict(source)]


def merge_newsdata_query(
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
    """Retourne les recherches NewsData.io normalisées."""

    queries = [
        query[:NEWSDATA_MAX_QUERY_LENGTH].strip()
        for query in get_query_keywords(source)
    ]
    return list(dict.fromkeys(query for query in queries if query))


def get_languages(source: Mapping[str, Any]) -> list[str]:
    """Retourne les langues structurées ou historiques."""

    return get_query_configuration_values(
        source, "languages", "language", lowercase=True
    )


def get_categories(source: Mapping[str, Any]) -> list[str]:
    """Retourne les catégories structurées ou historiques."""

    return get_query_configuration_values(
        source, "categories", "category", lowercase=True
    )


# Pagination

def get_max_pages(source: Mapping[str, Any]) -> int:
    """Retourne le nombre maximal de pages à parcourir."""

    return normalize_page_limit(
        value=get_pagination_value(
            source,
            "max_pages",
            default=NEWSDATA_DEFAULT_MAX_PAGES
        ),
        default=NEWSDATA_DEFAULT_MAX_PAGES,
        maximum=NEWSDATA_MAX_PAGES
    )


# Paramètres HTTP

def build_newsdata_request_params(
    source: Mapping[str, Any],
    language: str,
    category: str,
    page_token: str = ""
) -> dict[str, Any]:
    """Construit les paramètres envoyés à NewsData.io."""

    queries = get_queries(source)
    optional_values = {
        "language": normalize_value(language).lower(),
        "category": normalize_value(category).lower(),
        "page": normalize_value(page_token),
        "q": " OR ".join(queries),
        "country": format_list_value(source.get("countries")),
        "domain": format_list_value(source.get("domains")),
        "excludedomain": format_list_value(source.get("excluded_domains"))
    }
    params = {
        key: value
        for key, value in optional_values.items()
        if value
    }

    if parse_boolean(source.get("exclude_duplicates", True), default=True):
        params["removeduplicate"] = "1"

    return params


# Réseau

def fetch_newsdata_page(
    endpoint: str,
    params: Mapping[str, Any],
    api_key: str
) -> dict[str, Any]:
    """Envoie une requête authentifiée à NewsData.io."""

    return fetch_json_object(
        url=endpoint,
        params={**params, "apikey": api_key},
        headers={"Accept": "application/json"}
    )


def get_newsdata_error_details(
    data: Mapping[str, Any]
) -> tuple[str, str]:
    """Extrait le code et le message d'une erreur NewsData.io."""

    results = data.get("results", {})
    results = results if isinstance(results, Mapping) else {}

    code = (
        normalize_value(results.get("code"))
        or normalize_value(data.get("code"))
        or "inconnu"
    )
    message = (
        normalize_value(results.get("message"))
        or normalize_value(data.get("message"))
        or "non communiqué"
    )
    return code, message


def request_newsdata_page(
    source: Mapping[str, Any],
    language: str,
    category: str,
    api_key: str,
    page_token: str = ""
) -> tuple[list[dict[str, Any]], str]:
    """Récupère une page de résultats NewsData.io."""

    endpoint = normalize_value(source.get("endpoint"))

    if not is_valid_http_url(endpoint):
        raise ValueError(
            f"Endpoint NewsData.io absent ou invalide : "
            f"{endpoint or 'valeur absente'}."
        )

    params = build_newsdata_request_params(
        source=source,
        language=language,
        category=category,
        page_token=page_token
    )

    logger.debug(
        "Requête NewsData.io : langue=%s, catégorie=%s, page=%s.",
        normalize_value(language).lower() or "toutes",
        normalize_value(category).lower() or "toutes",
        "suivante" if page_token else "première"
    )

    data = fetch_newsdata_page(
        endpoint=endpoint,
        params=params,
        api_key=api_key
    )
    status = normalize_value(data.get("status")).lower()

    if status != "success":
        error_code, error_message = get_newsdata_error_details(data)
        error_details = f"{error_code} : {error_message}"

        # NewsData.io peut retourner une erreur dans un objet JSON valide.
        raise_if_fatal_api_error(error_details, NEWSDATA_EXTRACTOR.name)
        raise ApiRequestError(
            source_name=NEWSDATA_EXTRACTOR.name,
            reason=f"Erreur NewsData.io : {error_details}.",
            parameters=params
        )

    articles = filter_mapping_items(data.get("results", []), "NewsData.io")
    next_page = normalize_value(data.get("nextPage"))
    return articles, next_page


def request_newsdata_articles(
    source: Mapping[str, Any],
    language: str,
    category: str,
    max_articles: int,
    api_key: str
) -> list[dict[str, Any]]:
    """Récupère plusieurs pages NewsData.io."""

    maximum = parse_non_negative_integer(max_articles, 0)

    if maximum <= 0:
        return []

    articles: list[dict[str, Any]] = []
    page_token = ""
    visited_tokens: set[str] = set()

    for page_number in range(1, get_max_pages(source) + 1):
        remaining = maximum - len(articles)

        if remaining <= 0:
            break

        page_articles, next_page = request_newsdata_page(
            source=source,
            language=language,
            category=category,
            api_key=api_key,
            page_token=page_token
        )

        if not page_articles:
            logger.debug(
                "Pagination NewsData.io arrêtée à la page %s.",
                page_number
            )
            break

        articles.extend(page_articles[:remaining])

        if len(articles) >= maximum or not next_page:
            break

        if next_page == page_token or next_page in visited_tokens:
            logger.warning(
                "Jeton nextPage déjà rencontré. Pagination arrêtée."
            )
            break

        visited_tokens.add(next_page)
        page_token = next_page

    return articles[:maximum]


# Parcours

def iter_newsdata_items(
    source: Mapping[str, Any],
    maximum_articles: int
) -> Iterator[tuple[str, int, Mapping[str, Any]]]:
    """Parcourt les langues et catégories NewsData.io configurées."""

    maximum = parse_non_negative_integer(maximum_articles, 0)

    if maximum <= 0:
        return

    api_key = validate_newsdata_authentication()
    yielded_count = 0

    for query_block in get_newsdata_queries(source):
        query_configuration = merge_newsdata_query(source, query_block)
        languages = get_languages(query_configuration) or [""]
        categories = get_categories(query_configuration) or [""]

        for language, category in product(languages, categories):
            remaining = maximum - yielded_count

            if remaining <= 0:
                return

            articles = request_newsdata_articles(
                source=query_configuration,
                language=language,
                category=category,
                max_articles=remaining,
                api_key=api_key
            )
            identifier = (
                f"language={language or 'all'}|"
                f"category={category or 'all'}"
            )

            for index, item in enumerate(articles):
                if yielded_count >= maximum:
                    return

                yield identifier, index, {
                    **item,
                    "_requested_language": language,
                    "_requested_category": category
                }
                yielded_count += 1


# Champs

def get_newsdata_article_text(item: Mapping[str, Any]) -> str:
    """Retourne le meilleur contenu textuel disponible."""

    return clean_text(item.get("content")) or clean_text(item.get("description"))


def get_newsdata_publisher(item: Mapping[str, Any]) -> str:
    """Retourne le média éditorial fourni par NewsData.io."""

    return (
        clean_text(item.get("source_name"))
        or clean_text(item.get("source_id"))
    )


def build_newsdata_identifier(
    item: Mapping[str, Any],
    item_identifier: str
) -> str:
    """Construit un identifiant stable pour l'article."""

    article_id = normalize_value(item.get("article_id"))

    if article_id:
        return article_id

    url = normalize_value(item.get("link"))

    if is_valid_http_url(url):
        return url

    return (
        f"newsdata:{item_identifier}:"
        f"{normalize_value(item.get('pubDate'))}:"
        f"{clean_text(item.get('title'))}"
    )


# Article

def build_newsdata_article(
    item: Any,
    item_index: int,
    item_identifier: str,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme un résultat NewsData.io au format CheckIt.AI."""

    del item_index

    if not isinstance(item, Mapping):
        return {}

    article_id = normalize_value(item.get("article_id"))
    url = normalize_value(item.get("link"))

    if url and not is_valid_http_url(url):
        url = ""

    if not article_id and not url:
        return {}

    image_url = normalize_value(item.get("image_url"))

    if image_url and not is_valid_http_url(image_url):
        image_url = ""

    requested_language = normalize_value(
        item.get("_requested_language")
    ).lower()
    requested_category = normalize_value(
        item.get("_requested_category")
    ).lower()
    api_language = normalize_value(item.get("language")).lower()
    api_categories = format_list_value(item.get("category"))

    # "source" identifie l'API technique. Le média éditorial reste en metadata.
    return build_standard_article(
        identifier=build_newsdata_identifier(item, item_identifier),
        source=source.get("name", "newsdata"),
        title=clean_text(item.get("title")),
        text=get_newsdata_article_text(item),
        image_url=image_url,
        image_path="",
        published_at=item.get("pubDate"),
        url=url,
        author=format_list_value(item.get("creator")),
        language=api_language or requested_language,
        category=(
            api_categories
            or requested_category
            or normalize_value(source.get("category"))
            or "general"
        ),
        label="",
        dataset_role=source.get("role", "acquisition"),
        metadata={
            "publisher": get_newsdata_publisher(item),
            "source_id": clean_text(item.get("source_id")),
            "source_priority": item.get("source_priority")
        }
    )


# Validation

def validate_newsdata_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les contrôles propres à NewsData.io."""

    del filters

    if not isinstance(item, Mapping):
        return False, "resultat_newsdata_invalide"

    if (
        parse_boolean(source.get("exclude_duplicates", True), default=True)
        and parse_boolean(item.get("duplicate"), default=False)
    ):
        return False, "doublon_signale_api"

    article_id = normalize_value(item.get("article_id"))
    url = normalize_value(item.get("link"))

    if not article_id and not is_valid_http_url(url):
        return False, "identifiant_newsdata_absent"

    if url and not is_valid_http_url(url):
        return False, "url_newsdata_invalide"

    if not clean_text(item.get("title")):
        return False, "titre_newsdata_absent"

    return True, ""


# Adaptateur

NEWSDATA_ADAPTER = ApiAdapter(
    source_id="newsdata",
    default_name="NewsData.io",
    iter_items=iter_newsdata_items,
    build_article=build_newsdata_article,
    validate_item=validate_newsdata_item
)

NEWSDATA_EXTRACTOR = ApiExtractor(
    source_id="newsdata",
    default_name="NewsData.io",
    adapter=NEWSDATA_ADAPTER,
    section_name="api_sources",
    sources_file=SOURCES_FILE
)


# API publique

def load_newsdata_source() -> dict[str, Any]:
    """Recharge et retourne la configuration NewsData.io."""

    return dict(NEWSDATA_EXTRACTOR.reload_source())


def extract_articles_from_source(
    source: Mapping[str, Any]
) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_api_from_source(source=source, adapter=NEWSDATA_ADAPTER)


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction NewsData.io."""

    return NEWSDATA_EXTRACTOR.run()


# Exécution directe

if __name__ == "__main__":
    result = extract_all_articles()
    print(
        f"{len(result.articles)} article(s) NewsData.io extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])