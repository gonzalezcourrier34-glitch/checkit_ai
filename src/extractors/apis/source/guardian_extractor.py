"""Adaptateur utilisé pour extraire des articles avec The Guardian.

Ce module contient uniquement les traitements propres à Guardian :

- normalisation des requêtes, sections et champs ;
- construction des paramètres HTTP ;
- gestion de la pagination ;
- lecture des réponses Guardian ;
- transformation des résultats en articles CheckIt.AI ;
- validation spécifique des éléments.

Le chargement, l'orchestration et la gestion des résultats sont délégués
à ApiExtractor et au service générique des extracteurs.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from config.paths import SOURCES_FILE

from src.extractors.apis.api_adapter import ApiAdapter
from src.extractors.apis.api_extractor import (
    ApiAuthenticationError,
    ApiRequestError,
    ApiExtractor,
    calculate_page_size,
    extract_api_from_source,
    fetch_json_object,
    filter_mapping_items,
    normalize_page_limit,
    get_pagination_value,
    get_queries_configuration,
    get_query_configuration_values,
    get_query_keywords,
    normalize_string_list,
    raise_if_fatal_api_error,
    validate_api_secret
)
from src.extractors.core.extractor_results import ExtractorResult
from src.article.processing.article_cleaner import clean_text 
from src.utils.url_utils import is_valid_http_url
from src.utils.value_utils import normalize_value
from src.utils.parsing_utils import parse_non_negative_integer
from src.utils.extractor_utils import build_standard_article

from src.logger import get_logger

logger = get_logger(__name__)


# Configuration propre à Guardian

GUARDIAN_MAX_PAGE_SIZE = 200
GUARDIAN_DEFAULT_PAGE_SIZE = 50
GUARDIAN_DEFAULT_MAX_PAGES = 5
GUARDIAN_MAX_PAGES = 100
GUARDIAN_MAX_QUERY_LENGTH = 500

GUARDIAN_SUPPORTED_FIELDS: frozenset[str] = frozenset({
    "headline",
    "trailtext",
    "bodytext",
    "thumbnail",
    "byline",
    "publication",
    "shorturl",
    "wordcount",
    "firstpublicationdate",
    "lastmodified"
})

GUARDIAN_FIELD_MAPPING: dict[str, str] = {
    "headline": "headline",
    "trailtext": "trailText",
    "bodytext": "bodyText",
    "thumbnail": "thumbnail",
    "byline": "byline",
    "publication": "publication",
    "shorturl": "shortUrl",
    "wordcount": "wordcount",
    "firstpublicationdate": "firstPublicationDate",
    "lastmodified": "lastModified"
}


# Configuration de l'authentification

def validate_guardian_authentication() -> str:
    """Valide et retourne la clé API Guardian."""

    secret_name = GUARDIAN_EXTRACTOR.api_key_secret_name

    if not secret_name:
        raise ApiAuthenticationError(
            source_name=GUARDIAN_EXTRACTOR.name,
            reason=(
                "Le champ api_key_secret_name est absent "
                "de la configuration."
            ),
        )

    api_key = GUARDIAN_EXTRACTOR.api_key

    if not validate_api_secret(
        api_key,
        secret_name,
        GUARDIAN_EXTRACTOR.name,
    ):
        raise ApiAuthenticationError(
            source_name=GUARDIAN_EXTRACTOR.name,
            reason=f"Le secret {secret_name} est absent ou invalide.",
        )

    return api_key

# Normalisation des requêtes configurées

def get_configured_queries(
    source: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    """Retourne les blocs structurés ou la configuration historique."""

    queries = get_queries_configuration(source)

    if queries:
        return queries

    raw_queries = source.get("queries")

    if isinstance(raw_queries, Mapping):
        return [raw_queries]

    if isinstance(raw_queries, Sequence) and not isinstance(
        raw_queries,
        (str, bytes),
    ):
        return [query for query in raw_queries if isinstance(query, Mapping)]

    return [dict(source)]

def merge_guardian_query(
    source: Mapping[str, Any],
    query: Mapping[str, Any]
) -> dict[str, Any]:
    """Fusionne une requête avec la configuration commune."""

    return {
        **dict(source),
        **dict(query)
    }


# Normalisation des filtres

def get_queries(source: Mapping[str, Any]) -> list[str]:
    """Retourne les recherches configurées."""

    values = source.get(
        "query"
    )

    if values is None:
        values = source.get(
            "searches"
        )

    queries=[
        query[:GUARDIAN_MAX_QUERY_LENGTH].strip()
        for query in get_query_keywords(source)
    ]

    return list(dict.fromkeys(
        query
        for query in queries
        if query
    ))


def normalize_guardian_section(section: Any) -> str:
    """Normalise un identifiant de section Guardian."""

    return normalize_value(
        section
    ).lower().replace(
        " ",
        "-"
    )


def get_sections(source: Mapping[str, Any]) -> list[str]:
    """Retourne les sections configurées."""

    values = source.get(
        "sections",
        source.get("section")
    )

    sections = [
        normalized
        for section in normalize_string_list(values)
        if (normalized := normalize_guardian_section(section))
    ]

    return list(dict.fromkeys(sections))


def normalize_guardian_field(field: Any) -> str:
    """Normalise et vérifie un champ Guardian."""

    normalized = (
        normalize_value(field)
        .replace("_", "")
        .replace("-", "")
        .lower()
    )

    if not normalized:
        return ""

    if normalized not in GUARDIAN_SUPPORTED_FIELDS:
        logger.warning(
            "Champ Guardian non pris en charge : %s.",
            normalized
        )
        return ""

    return GUARDIAN_FIELD_MAPPING[
        normalized
    ]


def get_show_fields(
    source: Mapping[str, Any]
) -> list[str]:
    """Retourne les champs supplémentaires demandés à Guardian."""

    configured_fields = [
        normalized
        for field in normalize_string_list(source.get("show_fields"))
        if (normalized := normalize_guardian_field(field))
    ]

    required_fields = [
        "headline",
        "trailText",
        "bodyText",
        "thumbnail",
        "byline"
    ]

    return list(
        dict.fromkeys([
            *configured_fields,
            *required_fields
        ])
    )
    
def normalize_guardian_order_by(value: Any) -> str:
    """Normalise le type de tri Guardian."""

    normalized = normalize_value(
        value
    ).lower()

    if normalized in {
        "newest",
        "oldest",
        "relevance"
    }:
        return normalized

    if normalized:
        logger.warning(
            "Tri Guardian non pris en charge : %s. Tri newest utilisé.",
            normalized
        )

    return "newest"


# Gestion de la pagination

def get_page_size(
    source: Mapping[str, Any],
    remaining_articles: int
) -> int:
    """Calcule le nombre de résultats demandé par page."""

    return calculate_page_size(
        configured_value=get_pagination_value(
            source,"page_size",default=GUARDIAN_DEFAULT_PAGE_SIZE
        ),
        remaining_articles=remaining_articles,
        default=GUARDIAN_DEFAULT_PAGE_SIZE,
        maximum=GUARDIAN_MAX_PAGE_SIZE
    )


def get_max_pages(source: Mapping[str, Any]) -> int:
    """Retourne le nombre maximal de pages à parcourir."""

    return normalize_page_limit(
        value=get_pagination_value(
            source,"max_pages",default=GUARDIAN_DEFAULT_MAX_PAGES
        ),
        default=GUARDIAN_DEFAULT_MAX_PAGES,
        maximum=GUARDIAN_MAX_PAGES
    )


# Construction des paramètres HTTP

def build_guardian_request_params(
    source: Mapping[str, Any],
    query: str,
    section: str,
    page_number: int,
    page_size: int
) -> dict[str, Any]:
    """Construit les paramètres envoyés à Guardian."""

    params: dict[str, Any] = {
        "page": min(
            max(
                parse_non_negative_integer(
                    page_number,
                    1
                ),
                1
            ),
            GUARDIAN_MAX_PAGES
        ),
        "page-size": calculate_page_size(
            configured_value=page_size,
            remaining_articles=page_size,
            default=GUARDIAN_DEFAULT_PAGE_SIZE,
            maximum=GUARDIAN_MAX_PAGE_SIZE
        ),
        "order-by": normalize_guardian_order_by(
            source.get("order_by")
        ),
        "format": "json"
    }

    optional_values = {
        "q": normalize_value(
            query
        )[:GUARDIAN_MAX_QUERY_LENGTH],
        "section": normalize_guardian_section(
            section
        ),
        "from-date": normalize_value(
            source.get("from_date")
        ),
        "to-date": normalize_value(
            source.get("to_date")
        )
    }

    params.update({
        key: value
        for key, value in optional_values.items()
        if value
    })

    if fields := get_show_fields(source):
        params["show-fields"] = ",".join(fields)

    params["show-tags"] = "contributor"

    if tags := normalize_string_list(
        source.get("tags")
    ):
        params["tag"] = "|".join(tags)

    if content_types := normalize_string_list(
        source.get("types")
    ):
        params["type"] = "|".join(content_types)
        
    return params


# Envoi des requêtes Guardian

def fetch_guardian_page(
    endpoint: str,
    params: Mapping[str, Any],
    api_key: str
) -> dict[str, Any]:
    """Envoie une requête à Guardian et retourne son objet JSON."""

    return fetch_json_object(
        url=endpoint,
        params={**params, "api-key": api_key},
        headers={"Accept": "application/json"},
    )


def get_guardian_error_message(
    data: Mapping[str, Any]
) -> str:
    """Extrait le message d'erreur retourné par Guardian."""

    response_data = data.get(
        "response",
        {}
    )

    response_data = (
        response_data
        if isinstance(response_data, Mapping)
        else {}
    )

    return (
        normalize_value(response_data.get("message"))
        or normalize_value(data.get("message"))
        or "Erreur non communiquée"
    )


# Récupération d'une page

def request_guardian_page(
    source: Mapping[str, Any],
    query: str,
    section: str,
    page_number: int,
    page_size: int,
    api_key: str
) -> tuple[list[dict[str, Any]], int, int]:
    """Récupère une page de résultats Guardian."""

    endpoint = normalize_value(
        source.get("endpoint")
    )

    if not is_valid_http_url(endpoint):
        raise ValueError(
            "Endpoint Guardian absent ou invalide : "
            f"{endpoint or 'valeur absente'}."
        )

    params = build_guardian_request_params(
        source=source,
        query=query,
        section=section,
        page_number=page_number,
        page_size=page_size
    )

    logger.debug(
        "Requête Guardian : q='%s', section=%s, page=%s, taille=%s.",
        query or "toutes",
        section or "toutes",
        page_number,
        params["page-size"]
    )

    data = fetch_guardian_page(
        endpoint,
        params,
        api_key,
    )

    response_data = data.get(
        "response",
        {}
    )

    if not isinstance(response_data, Mapping):
        raise ValueError(
            "Le champ response de Guardian n'est pas un objet."
        )

    status = normalize_value(
        response_data.get("status")
    ).lower()

    if status != "ok":
        error_message = get_guardian_error_message(
            data
        )

        raise_if_fatal_api_error(
            error_message,
            "The Guardian Open Platform"
        )

        raise ApiRequestError(
            source_name=GUARDIAN_EXTRACTOR.name,
            reason=f"Erreur retournée par Guardian : {error_message}.",
            parameters=params,
        )

    results = filter_mapping_items(
        items=response_data.get("results", []),
        source_name="Guardian"
    )

    total_pages = parse_non_negative_integer(
        response_data.get("pages"),
        0
    )

    total_results = parse_non_negative_integer(
        response_data.get("total"),
        0
    )

    return (
        results,
        total_pages,
        total_results
    )


# Récupération de plusieurs pages

def request_guardian_articles(
    source: Mapping[str, Any],
    query: str,
    section: str,
    max_articles: int,
    api_key: str
) -> list[dict[str, Any]]:
    """Récupère plusieurs pages Guardian."""

    maximum = parse_non_negative_integer(
        max_articles,
        0
    )

    if maximum <= 0:
        return []

    articles: list[dict[str, Any]] = []

    for page_number in range(
        1,
        get_max_pages(source) + 1
    ):
        remaining = (
            maximum
            - len(articles)
        )

        if remaining <= 0:
            break

        page_size = get_page_size(
            source,
            remaining
        )

        page_articles, total_pages, total_results = request_guardian_page(
            source=source,
            query=query,
            section=section,
            page_number=page_number,
            page_size=page_size,
            api_key=api_key,
        )

        if not page_articles:
            break

        articles.extend(
            page_articles
        )

        if len(articles) >= maximum:
            break

        if total_pages > 0 and page_number >= total_pages:
            break

        if total_results > 0 and len(articles) >= total_results:
            break

        if len(page_articles) < page_size:
            break

    return articles[
        :maximum
    ]


# Parcours des combinaisons configurées

def iter_guardian_items(
    source: Mapping[str, Any],
    maximum_articles: int
) -> Iterator[tuple[str, int, Mapping[str, Any]]]:
    """Parcourt les combinaisons de requêtes et de sections."""

    maximum = parse_non_negative_integer(
        maximum_articles,
        0
    )

    if maximum <= 0:
        return

    api_key = validate_guardian_authentication()

    yielded_count = 0

    for query_block in get_configured_queries(source):
        query_configuration = merge_guardian_query(
            source,
            query_block
        )

        queries = get_queries(
            query_configuration
        ) or [""]

        sections = get_sections(
            query_configuration
        ) or [""]

        for query in queries:
            for section in sections:
                remaining = (
                    maximum
                    - yielded_count
                )

                if remaining <= 0:
                    return

                articles = request_guardian_articles(
                    source=query_configuration,
                    query=query,
                    section=section,
                    max_articles=remaining,
                    api_key=api_key
                )

                identifier = (
                    f"query={query or 'all'}|"
                    f"section={section or 'all'}"
                )

                for index, item in enumerate(articles):
                    if yielded_count >= maximum:
                        return

                    yield identifier, index, {
                        **item,
                        "_requested_query": query,
                        "_requested_section": section
                    }

                    yielded_count += 1


# Lecture des champs Guardian

def get_guardian_fields(
    item: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Retourne les champs supplémentaires d'un contenu."""

    fields = item.get(
        "fields",
        {}
    )

    return (
        fields
        if isinstance(fields, Mapping)
        else {}
    )


def get_guardian_title(
    item: Mapping[str, Any]
) -> str:
    """Retourne le meilleur titre disponible."""

    fields = get_guardian_fields(
        item
    )

    return (
        clean_text(fields.get("headline"))
        or clean_text(item.get("webTitle"))
    )


def get_guardian_text(
    item: Mapping[str, Any]
) -> str:
    """Retourne le meilleur contenu textuel."""

    fields = get_guardian_fields(
        item
    )

    return (
        clean_text(fields.get("bodyText"))
        or clean_text(fields.get("trailText"))
    )


def get_guardian_author(
    item: Mapping[str, Any]
) -> str:
    """Retourne le meilleur auteur disponible pour Guardian."""

    byline = clean_text(
        get_guardian_fields(item).get("byline")
    )

    if byline:
        return byline

    tags = item.get("tags", [])

    if not isinstance(tags, Sequence) or isinstance(
        tags,
        (str, bytes)
    ):
        return ""

    authors = [
        clean_text(tag.get("webTitle"))
        for tag in tags
        if (
            isinstance(tag, Mapping)
            and normalize_value(tag.get("type")).lower()
            == "contributor"
        )
    ]

    return ", ".join(
        dict.fromkeys(
            author
            for author in authors
            if author
        )
    )


def get_guardian_image_url(
    item: Mapping[str, Any]
) -> str:
    """Retourne l'URL de miniature lorsqu'elle est valide."""

    image_url = normalize_value(
        get_guardian_fields(item).get("thumbnail")
    )

    return (
        image_url
        if is_valid_http_url(image_url)
        else ""
    )


def get_guardian_language(
    source: Mapping[str, Any]
) -> str:
    """Retourne la langue principale configurée."""

    language = normalize_value(
        source.get("language")
    ).lower()

    if language:
        return language

    languages = get_query_configuration_values(
        source,"languages","language",lowercase=True
    )

    return (
        languages[0]
        if languages
        else "en"
    )


# Construction de l'article standard

def build_guardian_article(
    item: Any,
    item_index: int,
    item_identifier: str,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme un résultat Guardian au format CheckIt.AI."""

    del item_index

    if not isinstance(item, Mapping):
        return {}

    content_id = normalize_value(
        item.get("id")
    )

    url = normalize_value(
        item.get("webUrl")
    )

    if url and not is_valid_http_url(url):
        url = ""

    if not content_id and not url:
        return {}

    requested_section = normalize_guardian_section(
        item.get("_requested_section")
    )

    section_id = normalize_guardian_section(
        item.get("sectionId")
    )

    category = (
        section_id
        or requested_section
        or normalize_value(source.get("category"))
        or "general"
    )

    return build_standard_article(
        identifier=content_id or url or item_identifier,
        source=source.get(
            "name",
            "The Guardian Open Platform"
        ),
        title=get_guardian_title(item),
        text=get_guardian_text(item),
        image_url=get_guardian_image_url(item),
        image_path="",
        published_at=item.get("webPublicationDate"),
        url=url,
        author=get_guardian_author(item),
        language=get_guardian_language(source),
        category=category,
        label="",
        dataset_role=source.get(
            "role",
            "acquisition"
        )
    )


# Validation spécifique à Guardian

def validate_guardian_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les contrôles propres à Guardian."""

    del filters, source

    if not isinstance(item, Mapping):
        return False, "resultat_guardian_invalide"

    content_id = normalize_value(
        item.get("id")
    )

    url = normalize_value(
        item.get("webUrl")
    )

    if not content_id and not url:
        return False, "identifiant_guardian_absent"

    if not is_valid_http_url(url):
        return False, "url_guardian_invalide"

    return True, ""


# Adaptateur et extracteur Guardian

GUARDIAN_ADAPTER = ApiAdapter(
    source_id="guardian_api",
    default_name="The Guardian Open Platform",
    iter_items=iter_guardian_items,
    build_article=build_guardian_article,
    validate_item=validate_guardian_item
)

GUARDIAN_EXTRACTOR = ApiExtractor(
    source_id="guardian_api",
    default_name="The Guardian Open Platform",
    adapter=GUARDIAN_ADAPTER,
    section_name="api_sources",
    sources_file=SOURCES_FILE
)


# Fonctions publiques

def load_guardian_source() -> dict[str, Any]:
    """Recharge et retourne la configuration Guardian."""

    return dict(
        GUARDIAN_EXTRACTOR.reload_source()
    )


def extract_articles_from_source(
    source: Mapping[str, Any]
) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_api_from_source(
        source=source,
        adapter=GUARDIAN_ADAPTER
    )


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction Guardian."""

    return GUARDIAN_EXTRACTOR.run()


# Exécution directe

if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} article(s) Guardian extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(
            result.message
        )

    if result.articles:
        print(
            result.articles[0]
        )