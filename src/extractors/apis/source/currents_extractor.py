"""Adaptateur d'extraction des articles de Currents News API."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from datetime import date, datetime, timedelta
from itertools import product
from typing import Any

from config.paths import SOURCES_FILE
from src.extractors.apis.api_adapter import ApiAdapter
from src.extractors.apis.api_extractor import (
    ApiAuthenticationError,
    ApiExtractor,
    ApiRequestError,
    calculate_page_size,
    execute_independent_api_requests,
    extract_api_from_source,
    fetch_json_object,
    filter_mapping_items,
    get_api_max_article_age_days,
    join_normalized_values,
    normalize_page_limit,
    normalize_string_list,
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


# Limites
CURRENTS_MAX_PAGE_SIZE = 300
CURRENTS_DEFAULT_PAGE_SIZE = 30
CURRENTS_DEFAULT_MAX_PAGES = 5
CURRENTS_DEFAULT_MAX_REQUESTS = 50
CURRENTS_MAX_PAGE_NUMBER = 180
CURRENTS_MAX_KEYWORD_LENGTH = 500
CURRENTS_MAX_OFFSET = 5000

# Pays
COUNTRY_MAPPING = {
    "AU": "au",
    "AUSTRALIA": "au",
    "CA": "ca",
    "CANADA": "ca",
    "DE": "de",
    "GERMANY": "de",
    "ES": "es",
    "SPAIN": "es",
    "FR": "fr",
    "FRANCE": "fr",
    "GB": "gb",
    "UK": "gb",
    "UNITED KINGDOM": "gb",
    "IT": "it",
    "ITALY": "it",
    "US": "us",
    "USA": "us",
    "UNITED STATES": "us",
}


# Authentification

def validate_currents_authentication() -> str:
    """Valide et retourne la clé API Currents."""

    secret_name = CURRENTS_EXTRACTOR.api_key_secret_name

    if not secret_name:
        raise ApiAuthenticationError(
            source_name=CURRENTS_EXTRACTOR.name,
            reason=(
                "Le champ api_key_secret_name est absent "
                "de la configuration Currents."
            ),
        )

    api_key = CURRENTS_EXTRACTOR.api_key

    if not validate_api_secret(
        api_key,
        secret_name,
        CURRENTS_EXTRACTOR.name,
    ):
        raise ApiAuthenticationError(
            source_name=CURRENTS_EXTRACTOR.name,
            reason=(
                f"Le secret {secret_name} est absent ou invalide."
            ),
        )

    return api_key

# Paramètres
def get_keywords(source: Mapping[str, Any]) -> list[str]:
    """Retourne les mots-clés compatibles avec Currents."""

    values = source.get("keywords", source.get("queries", source.get("query")))
    keywords = [
        value[:CURRENTS_MAX_KEYWORD_LENGTH].strip()
        for value in normalize_string_list(values)
    ]
    return list(dict.fromkeys(keyword for keyword in keywords if keyword))


def get_languages(source: Mapping[str, Any]) -> list[str]:
    """Retourne les langues configurées en minuscules."""

    return normalize_string_list(
        source.get("languages", source.get("language")),
        lowercase=True,
    )


def get_countries(source: Mapping[str, Any]) -> list[str]:
    """Retourne les pays supportés au format Currents."""

    countries: list[str] = []
    values = source.get("countries", source.get("country"))

    for country in normalize_string_list(values):
        normalized = normalize_value(country).upper()

        if not normalized:
            continue

        mapped_country = COUNTRY_MAPPING.get(normalized)

        if not mapped_country:
            logger.warning("Pays Currents ignoré car non supporté : %s.", country)
            continue

        countries.append(mapped_country)

    return list(dict.fromkeys(countries))


def get_categories(source: Mapping[str, Any]) -> list[str]:
    """Retourne les catégories configurées en minuscules."""

    return normalize_string_list(
        source.get("categories", source.get("category")),
        lowercase=True,
    )


# Pagination
def get_page_size(source: Mapping[str, Any], remaining_articles: int) -> int:
    """Calcule la taille de la prochaine page."""

    return calculate_page_size(
        configured_value=source.get("page_size", CURRENTS_DEFAULT_PAGE_SIZE),
        remaining_articles=remaining_articles,
        default=CURRENTS_DEFAULT_PAGE_SIZE,
        maximum=CURRENTS_MAX_PAGE_SIZE,
    )


def get_max_pages(source: Mapping[str, Any]) -> int:
    """Retourne le nombre maximal de pages."""

    return normalize_page_limit(
        value=source.get("max_pages", CURRENTS_DEFAULT_MAX_PAGES),
        default=CURRENTS_DEFAULT_MAX_PAGES,
        maximum=CURRENTS_MAX_PAGE_NUMBER,
    )


def get_max_requests(source: Mapping[str, Any]) -> int:
    """Retourne le nombre maximal de requêtes indépendantes."""

    return max(
        parse_non_negative_integer(
            source.get("max_requests", CURRENTS_DEFAULT_MAX_REQUESTS),
            CURRENTS_DEFAULT_MAX_REQUESTS,
        ),
        1,
    )


# Dates
def parse_currents_date(value: Any, field_name: str) -> date | None:
    """Convertit une date de configuration au format ISO."""

    normalized = normalize_value(value)

    if not normalized:
        return None

    try:
        return datetime.fromisoformat(normalized.replace("Z", "+00:00")).date()
    except (TypeError, ValueError, OverflowError):
        logger.warning("Date Currents invalide pour %s : %s.", field_name, normalized)
        return None


def get_currents_date_range(source: Mapping[str, Any]) -> tuple[str, str]:
    """Construit une période limitée à l'âge maximal autorisé."""

    max_days = max(get_api_max_article_age_days(source), 1)
    today = date.today()
    start_date = parse_currents_date(
        source.get("start_date", source.get("date_from", source.get("from_date"))),
        "start_date",
    )
    end_date = parse_currents_date(
        source.get("end_date", source.get("date_to", source.get("to_date"))),
        "end_date",
    )

    if start_date and end_date and start_date > end_date:
        logger.warning("Dates Currents inversées : elles ont été permutées.")
        start_date, end_date = end_date, start_date

    if not start_date and not end_date:
        end_date = today
        start_date = end_date - timedelta(days=max_days - 1)
    elif start_date and not end_date:
        end_date = min(today, start_date + timedelta(days=max_days - 1))
    elif end_date and not start_date:
        start_date = end_date - timedelta(days=max_days - 1)

    if start_date and end_date:
        minimum_start = end_date - timedelta(days=max_days - 1)

        if start_date < minimum_start:
            logger.warning("Période Currents réduite à %s jour(s).", max_days)
            start_date = minimum_start

    return (
        start_date.isoformat() if start_date else "",
        end_date.isoformat() if end_date else "",
    )


# Requêtes
def build_currents_request_params(
    source: Mapping[str, Any],
    keyword: str,
    language: str,
    country: str,
    category: str,
    page_number: int,
    page_size: int,
) -> dict[str, Any]:
    """Construit les paramètres compatibles avec l'endpoint Currents."""

    endpoint = normalize_value(source.get("endpoint")).lower()
    is_search_endpoint = endpoint.rstrip("/").endswith("/search")

    params: dict[str, Any] = {
        "page_number": min(
            max(parse_non_negative_integer(page_number, 1), 1),
            CURRENTS_MAX_PAGE_NUMBER,
        ),
        "page_size": min(
            max(
                parse_non_negative_integer(
                    page_size,
                    CURRENTS_DEFAULT_PAGE_SIZE,
                ),
                1,
            ),
            CURRENTS_MAX_PAGE_SIZE,
        ),
    }

    domain = normalize_value(source.get("domain"))
    excluded_domain = normalize_value(
        source.get("domain_not", source.get("excluded_domain"))
    )

    if domain and excluded_domain:
        logger.warning(
            "Currents : domain_not ignoré car domain est également configuré."
        )
        excluded_domain = ""

    common_values = {
        "language": normalize_value(language).lower(),
        "country": normalize_value(country).lower(),
        "category": normalize_value(category).lower(),
        "domain": domain,
        "domain_not": excluded_domain,
        "author": normalize_value(source.get("author")),
    }
    params.update({
        key: value
        for key, value in common_values.items()
        if value
    })

    # Les mots-clés et les dates sont réservés à /search.
    if is_search_endpoint:
        start_date, end_date = get_currents_date_range(source)
        search_values = {
            "keywords": normalize_value(
                keyword
            )[:CURRENTS_MAX_KEYWORD_LENGTH],
            "start_date": start_date,
            "end_date": end_date,
        }
        params.update({
            key: value
            for key, value in search_values.items()
            if value
        })

    article_type = parse_non_negative_integer(
        source.get("article_type", 0),
        0,
    )

    if article_type in {1, 2, 3}:
        params["type"] = article_type

    return params

def get_currents_query_pairs(source: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Associe chaque mot-clé à une catégorie cohérente."""

    configured_queries = source.get("queries")
    pairs: list[tuple[str, str]] = []

    # Le format dictionnaire permet de définir explicitement le couple
    # mot-clé/catégorie dans le YAML sans dépendre de leur position.
    if isinstance(configured_queries, Sequence) and not isinstance(
        configured_queries,
        (str, bytes, bytearray),
    ):
        for query in configured_queries:
            if not isinstance(query, Mapping):
                continue

            keyword = normalize_value(
                query.get("keyword", query.get("keywords", query.get("query")))
            )[:CURRENTS_MAX_KEYWORD_LENGTH].strip()
            category = normalize_value(query.get("category")).lower()

            if keyword or category:
                pairs.append((keyword, category))

    if pairs:
        return list(dict.fromkeys(pairs))

    keywords = get_keywords(source)
    categories = get_categories(source)

    if not keywords:
        return [("", category) for category in categories] or [("", "")]

    # Lorsque les listes ont la même taille, leur position définit le couple.
    if len(keywords) == len(categories):
        return list(dict.fromkeys(zip(keywords, categories)))

    # Une catégorie générale supplémentaire est ignorée afin d'éviter le
    # produit cartésien qui générait de nombreuses requêtes redondantes.
    specific_categories = [category for category in categories if category != "general"]

    if len(keywords) == len(specific_categories):
        return list(dict.fromkeys(zip(keywords, specific_categories)))

    # En dernier recours, chaque mot-clé utilise la catégorie générale.
    fallback_category = "general" if "general" in categories else ""
    return [(keyword, fallback_category) for keyword in keywords]


def build_currents_requests(source: Mapping[str, Any]) -> list[dict[str, str]]:
    """Construit des requêtes cohérentes sans produit cartésien inutile."""

    query_pairs = get_currents_query_pairs(source)
    languages = get_languages(source) or [""]
    countries = get_countries(source) or [""]
    maximum_requests = get_max_requests(source)
    requests: list[dict[str, str]] = []

    for (keyword, category), language, country in product(
        query_pairs,
        languages,
        countries,
    ):
        requests.append({
            "keyword": keyword,
            "language": language,
            "country": country,
            "category": category,
        })

        if len(requests) >= maximum_requests:
            logger.warning(
                "Currents : nombre de requêtes limité à %s.",
                maximum_requests,
            )
            break

    return requests or [
        {"keyword": "", "language": "", "country": "", "category": ""}
    ]


# Réseau
def fetch_currents_page(
    endpoint: str,
    params: Mapping[str, Any],
    api_key: str,
) -> dict[str, Any]:
    """Envoie une requête Currents et retourne son objet JSON."""

    return fetch_json_object(
        url=endpoint,
        params={**params, "apiKey": api_key},
        headers={"Accept": "application/json"},
    )


def get_currents_error_message(data: Mapping[str, Any]) -> str:
    """Extrait le message d'erreur renvoyé par Currents."""

    details = data.get("details")
    details = details if isinstance(details, Mapping) else {}

    return (
        normalize_value(data.get("msg"))
        or normalize_value(data.get("message"))
        or normalize_value(details.get("message"))
        or "Erreur non communiquée"
    )


def request_currents_page(
    source: Mapping[str, Any],
    keyword: str,
    language: str,
    country: str,
    category: str,
    page_number: int,
    page_size: int,
    api_key: str,
) -> tuple[list[dict[str, Any]], int]:
    """Récupère et contrôle une page Currents."""

    endpoint = normalize_value(source.get("endpoint"))

    if not is_valid_http_url(endpoint):
        raise ValueError(
            f"Endpoint Currents absent ou invalide : {endpoint or 'valeur absente'}."
        )

    params = build_currents_request_params(
        source=source,
        keyword=keyword,
        language=language,
        country=country,
        category=category,
        page_number=page_number,
        page_size=page_size,
    )

    logger.debug(
        "Requête Currents : mot-clé=%s, langue=%s, pays=%s, "
        "catégorie=%s, page=%s, taille=%s.",
        keyword or "tous",
        language or "toutes",
        country or "tous",
        category or "toutes",
        page_number,
        page_size,
    )

    data = fetch_currents_page(
        endpoint=endpoint,
        params=params,
        api_key=api_key,
    )
    
    status = normalize_value(data.get("status")).lower()

    if status not in {"ok", "success"}:
        error_message = get_currents_error_message(data)
        raise_if_fatal_api_error(error_message, "Currents News API")

        raise ApiRequestError(
            source_name="Currents News API",
            reason=f"Erreur retournée par Currents : {error_message}.",
            parameters=params,
        )

    articles = filter_mapping_items(
        items=data.get("news", []),
        source_name="Currents",
    )
    returned_page = parse_non_negative_integer(
        data.get("page", page_number),
        page_number,
    )
    return articles, returned_page


# Pages
def request_currents_articles(
    source: Mapping[str, Any],
    keyword: str,
    language: str,
    country: str,
    category: str,
    max_articles: int,
    api_key: str,
) -> list[dict[str, Any]]:
    """Récupère plusieurs pages sans dépasser les limites Currents."""

    maximum = parse_non_negative_integer(max_articles, 0)

    if maximum <= 0:
        return []

    articles: list[dict[str, Any]] = []

    for page_number in range(1, get_max_pages(source) + 1):
        remaining = maximum - len(articles)

        if remaining <= 0:
            break

        page_size = get_page_size(source, remaining)
        offset = (page_number - 1) * page_size

        if offset > CURRENTS_MAX_OFFSET:
            logger.warning(
                "Pagination Currents arrêtée : offset %s supérieur à %s.",
                offset,
                CURRENTS_MAX_OFFSET,
            )
            break

        page_articles, returned_page = request_currents_page(
            source=source,
            keyword=keyword,
            language=language,
            country=country,
            category=category,
            page_number=page_number,
            page_size=page_size,
            api_key=api_key,
        )

        if not page_articles:
            break

        articles.extend(page_articles)

        if returned_page and returned_page != page_number:
            logger.warning(
                "Currents a retourné la page %s au lieu de %s.",
                returned_page,
                page_number,
            )

        if len(articles) >= maximum or len(page_articles) < page_size:
            break

    return articles[:maximum]


# Combinaisons
def iter_currents_items(
    source: Mapping[str, Any],
    maximum_articles: int,
) -> Iterator[tuple[str, int, Mapping[str, Any]]]:
    """Parcourt les combinaisons de filtres configurées."""

    maximum = parse_non_negative_integer(maximum_articles, 0)

    if maximum <= 0:
        return

    api_key = validate_currents_authentication()
    requests = build_currents_requests(source)
    request_limit = max((maximum + len(requests) - 1) // len(requests), 1)

    def execute_request(request: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        keyword = normalize_value(request.get("keyword"))
        language = normalize_value(request.get("language")).lower()
        country = normalize_value(request.get("country")).lower()
        category = normalize_value(request.get("category")).lower()
        items = request_currents_articles(
            source=source,
            keyword=keyword,
            language=language,
            country=country,
            category=category,
            max_articles=request_limit,
            api_key=api_key,
        )
        identifier = (
            f"keyword={keyword or 'all'}|language={language or 'all'}|"
            f"country={country or 'all'}|category={category or 'all'}"
        )

        return [
            {
                **item,
                "_request_identifier": identifier,
                "_requested_keyword": keyword,
                "_requested_language": language,
                "_requested_country": country,
                "_requested_category": category,
            }
            for item in items
        ]

    items = execute_independent_api_requests(
        requests=requests,
        request_function=execute_request,
        source_name="Currents News API",
    )

    for index, item in enumerate(items):
        if index >= maximum:
            return

        identifier = normalize_value(
            item.get("_request_identifier") if isinstance(item, Mapping) else ""
        ) or f"currents:{index}"
        yield identifier, index, item


# Champs
def get_currents_category(item: Mapping[str, Any]) -> str:
    """Retourne les catégories Currents sous forme de texte."""

    return join_normalized_values(item.get("category"))


def get_currents_article_text(item: Mapping[str, Any]) -> str:
    """Retourne le meilleur texte disponible."""

    return clean_text(item.get("description")) or clean_text(item.get("content"))


# Article
def build_currents_article(
    item: Any,
    item_index: int,
    item_identifier: str,
    source: Mapping[str, Any],
) -> dict[str, Any]:
    """Transforme un résultat Currents au format CheckIt.AI."""

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
    requested_category = normalize_value(item.get("_requested_category")).lower()

    return build_standard_article(
        identifier=article_id or url or item_identifier,
        source=source.get("name", "Currents News API"),
        title=clean_text(item.get("title")),
        text=get_currents_article_text(item),
        image_url=image_url,
        image_path="",
        published_at=item.get("published"),
        url=url,
        author=clean_text(item.get("author")),
        language=normalize_value(item.get("language")).lower() or requested_language,
        category=get_currents_category(item) or requested_category or "general",
        label="",
        dataset_role=source.get("role", "acquisition"),
    )


# Validation
def validate_currents_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any],
) -> tuple[bool, str]:
    """Applique les contrôles propres à Currents."""

    del filters, source

    if not isinstance(item, Mapping):
        return False, "resultat_currents_invalide"

    article_id = normalize_value(item.get("id"))
    url = normalize_value(item.get("url"))

    if not article_id and not url:
        return False, "identifiant_currents_absent"

    if not is_valid_http_url(url):
        return False, "url_currents_invalide"

    return True, ""


# Adaptateur
CURRENTS_ADAPTER = ApiAdapter(
    source_id="currents",
    default_name="Currents News API",
    iter_items=iter_currents_items,
    build_article=build_currents_article,
    validate_item=validate_currents_item,
)

CURRENTS_EXTRACTOR = ApiExtractor(
    source_id="currents",
    default_name="Currents News API",
    adapter=CURRENTS_ADAPTER,
    section_name="api_sources",
    sources_file=SOURCES_FILE,
)


# API publique
def load_currents_source() -> dict[str, Any]:
    """Recharge et retourne la configuration Currents."""

    return dict(CURRENTS_EXTRACTOR.reload_source())


def extract_articles_from_source(
    source: Mapping[str, Any],
) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_api_from_source(source=source, adapter=CURRENTS_ADAPTER)


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction Currents."""

    return CURRENTS_EXTRACTOR.run()


# Exécution directe
if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} article(s) Currents extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])