"""Adaptateur utilisé pour extraire les vérifications Google Fact Check.

Ce module contient uniquement les traitements propres
à Google Fact Check Tools :

- normalisation des requêtes et des langues ;
- construction des paramètres HTTP ;
- gestion de la pagination par jeton ;
- lecture des affirmations et des vérifications ;
- transformation des résultats en articles CheckIt.AI ;
- validation spécifique des éléments.

Le chargement, l'orchestration et la gestion des résultats sont délégués
à ApiExtractor et au service générique des extracteurs.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from config.paths import SOURCES_FILE
from src.article.processing.article_cleaner import clean_text
from src.article.fact_check_labels import classify_fact_check_label
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
    raise_if_fatal_api_error,
    validate_api_secret
)
from src.extractors.core.extractor_results import ExtractorResult
from src.logger import get_logger
from src.utils.date_utils import convert_date_to_iso
from src.utils.extractor_utils import build_standard_article
from src.utils.parsing_utils import parse_non_negative_integer
from src.utils.url_utils import is_valid_http_url
from src.utils.value_utils import normalize_value

logger = get_logger(__name__)


# Limites de Google Fact Check Tools

GOOGLE_FACT_CHECK_DEFAULT_PAGE_SIZE = 100
GOOGLE_FACT_CHECK_MAX_PAGE_SIZE = 100
GOOGLE_FACT_CHECK_DEFAULT_MAX_PAGES = 5
GOOGLE_FACT_CHECK_MAX_PAGES = 100
GOOGLE_FACT_CHECK_MAX_QUERY_LENGTH = 500


# Configuration de l'authentification

def validate_google_fact_check_authentication() -> str:
    """Valide et retourne la clé API Google Fact Check."""

    secret_name = GOOGLE_FACT_CHECK_EXTRACTOR.api_key_secret_name

    if not secret_name:
        raise ApiAuthenticationError(
            source_name=GOOGLE_FACT_CHECK_EXTRACTOR.name,
            reason="Le champ api_key_secret_name est absent de la configuration."
        )

    api_key = GOOGLE_FACT_CHECK_EXTRACTOR.api_key

    if not validate_api_secret(
        api_key,
        secret_name,
        GOOGLE_FACT_CHECK_EXTRACTOR.name
    ):
        raise ApiAuthenticationError(
            source_name=GOOGLE_FACT_CHECK_EXTRACTOR.name,
            reason=f"Le secret {secret_name} est absent ou invalide."
        )

    return api_key


# Normalisation des blocs de requête et des filtres

def get_configured_queries(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Retourne les blocs structurés ou la source historique."""

    return get_queries_configuration(source) or [dict(source)]


def merge_google_fact_check_query(
    source: Mapping[str, Any],
    query: Mapping[str, Any]
) -> dict[str, Any]:
    """Fusionne la configuration commune et un bloc de requête."""

    common = {key: value for key, value in source.items() if key != "queries"}
    return {**common, **dict(query)}


def get_queries(source: Mapping[str, Any]) -> list[str]:
    """Retourne les recherches textuelles structurées ou historiques."""

    queries = [
        query[:GOOGLE_FACT_CHECK_MAX_QUERY_LENGTH].strip()
        for query in get_query_keywords(source)
    ]

    return list(dict.fromkeys(query for query in queries if query))


def normalize_language_code(language: Any) -> str:
    """Normalise un code de langue au format BCP-47."""

    normalized = normalize_value(language).replace("_", "-")

    if not normalized:
        return ""

    parts = [part for part in normalized.split("-") if part]

    if not parts:
        return ""

    primary = parts[0].lower()
    normalized_parts: list[str] = []

    for part in parts[1:]:
        if len(part) == 2 and part.isalpha():
            normalized_parts.append(part.upper())
        elif len(part) == 4 and part.isalpha():
            normalized_parts.append(part.title())
        else:
            normalized_parts.append(part.lower())

    return "-".join([primary, *normalized_parts])


def get_languages(source: Mapping[str, Any]) -> list[str]:
    """Retourne les langues structurées ou historiques."""

    languages = [
        normalized
        for language in get_query_configuration_values(
            source,
            "languages",
            "language"
        )
        if (normalized := normalize_language_code(language))
    ]

    return list(dict.fromkeys(languages))


# Gestion de la pagination

def get_page_size(
    source: Mapping[str, Any],
    remaining_articles: int
) -> int:
    """Calcule le nombre d'affirmations demandé par page."""

    return calculate_page_size(
        configured_value=get_pagination_value(
            source,
            "page_size",
            default=GOOGLE_FACT_CHECK_DEFAULT_PAGE_SIZE
        ),
        remaining_articles=remaining_articles,
        default=GOOGLE_FACT_CHECK_DEFAULT_PAGE_SIZE,
        maximum=GOOGLE_FACT_CHECK_MAX_PAGE_SIZE
    )


def get_max_pages(source: Mapping[str, Any]) -> int:
    """Retourne le nombre maximal de pages à parcourir."""

    return normalize_page_limit(
        value=get_pagination_value(
            source,
            "max_pages",
            default=GOOGLE_FACT_CHECK_DEFAULT_MAX_PAGES
        ),
        default=GOOGLE_FACT_CHECK_DEFAULT_MAX_PAGES,
        maximum=GOOGLE_FACT_CHECK_MAX_PAGES
    )


# Construction des paramètres HTTP

def build_google_fact_check_request_params(
    source: Mapping[str, Any],
    query: str,
    language: str,
    page_size: int,
    page_token: str = ""
) -> dict[str, Any]:
    """Construit les paramètres envoyés à Google Fact Check."""

    requested_page_size = calculate_page_size(
        configured_value=page_size,
        remaining_articles=page_size,
        default=GOOGLE_FACT_CHECK_DEFAULT_PAGE_SIZE,
        maximum=GOOGLE_FACT_CHECK_MAX_PAGE_SIZE
    )

    params: dict[str, Any] = {
        "pageSize": requested_page_size,
        "maxAgeDays": max(get_api_max_article_age_days(source), 1)
    }

    optional_values = {
        "query": normalize_value(query)[:GOOGLE_FACT_CHECK_MAX_QUERY_LENGTH],
        "languageCode": normalize_language_code(language),
        "pageToken": normalize_value(page_token),
        "reviewPublisherSiteFilter": normalize_value(
            source.get(
                "review_publisher_site_filter",
                source.get("publisher_site")
            )
        )
    }

    params.update({
        key: value
        for key, value in optional_values.items()
        if value
    })

    return params


# Envoi des requêtes

def fetch_google_fact_check_page(
    endpoint: str,
    params: Mapping[str, Any],
    api_key: str
) -> dict[str, Any]:
    """Envoie une requête à Google Fact Check et retourne le JSON."""

    return fetch_json_object(
        url=endpoint,
        params={**params, "key": api_key},
        headers={"Accept": "application/json"}
    )


def get_google_error_message(data: Mapping[str, Any]) -> str:
    """Extrait le message d'erreur retourné par Google."""

    error_data = data.get("error", {})
    error_data = error_data if isinstance(error_data, Mapping) else {}

    return (
        normalize_value(error_data.get("message"))
        or normalize_value(data.get("message"))
        or "Erreur non communiquée"
    )


# Récupération d'une page

def request_google_fact_check_page(
    source: Mapping[str, Any],
    query: str,
    language: str,
    page_size: int,
    api_key: str,
    page_token: str = ""
) -> tuple[list[dict[str, Any]], str]:
    """Récupère une page d'affirmations vérifiées."""

    endpoint = normalize_value(
        source.get("endpoint")
        or source.get("base_url")
        or source.get("url")
    )

    if not is_valid_http_url(endpoint):
        raise ValueError(
            "Endpoint Google Fact Check absent ou invalide : "
            f"{endpoint or 'valeur absente'}."
        )

    publisher_filter = normalize_value(
        source.get(
            "review_publisher_site_filter",
            source.get("publisher_site")
        )
    )

    if not normalize_value(query) and not publisher_filter:
        raise ValueError(
            "Google Fact Check exige une requête ou un filtre d'éditeur."
        )

    params = build_google_fact_check_request_params(
        source=source,
        query=query,
        language=language,
        page_size=page_size,
        page_token=page_token
    )

    requested_page_size = parse_non_negative_integer(
        params.get("pageSize"),
        GOOGLE_FACT_CHECK_DEFAULT_PAGE_SIZE
    )

    logger.debug(
        "Requête Google Fact Check : q='%s', langue=%s, page=%s, taille=%s.",
        query or "aucune",
        language or "toutes",
        "suivante" if page_token else "première",
        requested_page_size
    )

    data = fetch_google_fact_check_page(
        endpoint=endpoint,
        params=params,
        api_key=api_key
    )

    if "error" in data:
        error_message = get_google_error_message(data)

        # Certaines erreurs Google sont contenues dans un JSON valide.
        raise_if_fatal_api_error(
            error_message,
            "Google Fact Check Tools"
        )

        raise ApiRequestError(
            source_name="Google Fact Check Tools",
            reason=f"Erreur Google Fact Check : {error_message}.",
            parameters=params
        )

    claims = filter_mapping_items(
        items=data.get("claims", []),
        source_name="Google Fact Check"
    )

    next_page_token = normalize_value(data.get("nextPageToken"))

    return claims, next_page_token


# Lecture des vérifications

def get_claim_reviews(
    claim: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    """Retourne les vérifications associées à une affirmation."""

    reviews = claim.get("claimReview", [])

    if not isinstance(reviews, list):
        return []

    return [
        review
        for review in reviews
        if isinstance(review, Mapping)
    ]


def get_review_publisher(
    review: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Retourne les données de l'éditeur du fact-check."""

    publisher = review.get("publisher", {})
    return publisher if isinstance(publisher, Mapping) else {}


# Récupération de plusieurs pages

def request_google_fact_check_claims(
    source: Mapping[str, Any],
    query: str,
    language: str,
    max_reviews: int,
    api_key: str
) -> list[dict[str, Any]]:
    """Récupère les claims nécessaires pour produire au plus N reviews."""

    maximum_reviews = parse_non_negative_integer(max_reviews, 0)

    if maximum_reviews <= 0:
        return []

    claims: list[dict[str, Any]] = []
    collected_reviews = 0
    page_token = ""
    visited_tokens: set[str] = set()

    for page_number in range(1, get_max_pages(source) + 1):
        remaining_reviews = maximum_reviews - collected_reviews

        if remaining_reviews <= 0:
            break

        page_claims, next_token = request_google_fact_check_page(
            source=source,
            query=query,
            language=language,
            page_size=get_page_size(source, remaining_reviews),
            api_key=api_key,
            page_token=page_token
        )

        # Une réponse valide sans claim indique la fin naturelle.
        if not page_claims:
            logger.debug(
                "Pagination Google Fact Check arrêtée à la page %s.",
                page_number
            )
            break

        for claim in page_claims:
            reviews = get_claim_reviews(claim)

            if not reviews:
                continue

            claims.append(claim)
            collected_reviews += len(reviews)

            if collected_reviews >= maximum_reviews:
                break

        if collected_reviews >= maximum_reviews or not next_token:
            break

        if next_token == page_token or next_token in visited_tokens:
            logger.warning(
                "Jeton nextPageToken déjà rencontré. Pagination arrêtée."
            )
            break

        visited_tokens.add(next_token)
        page_token = next_token

    logger.debug(
        "%s claim(s) récupéré(s) pour %s review(s), limite : %s.",
        len(claims),
        collected_reviews,
        maximum_reviews
    )

    return claims


# Parcours des requêtes, langues et vérifications

def iter_google_fact_check_items(
    source: Mapping[str, Any],
    maximum_articles: int
) -> Iterator[tuple[str, int, Mapping[str, Any]]]:
    """Parcourt les requêtes, langues et vérifications trouvées."""

    maximum = parse_non_negative_integer(maximum_articles, 0)

    if maximum <= 0:
        return

    api_key = validate_google_fact_check_authentication()
    yielded_count = 0

    for query_block in get_configured_queries(source):
        query_configuration = merge_google_fact_check_query(
            source,
            query_block
        )

        queries = get_queries(query_configuration) or [""]
        languages = get_languages(query_configuration) or [""]

        publisher_filter = normalize_value(
            query_configuration.get(
                "review_publisher_site_filter",
                query_configuration.get("publisher_site")
            )
        )

        if queries == [""] and not publisher_filter:
            raise ValueError(
                "Google Fact Check exige au moins une requête "
                "ou un filtre d'éditeur."
            )

        for query in queries:
            for language in languages:
                remaining = maximum - yielded_count

                if remaining <= 0:
                    return

                claims = request_google_fact_check_claims(
                    source=query_configuration,
                    query=query,
                    language=language,
                    max_reviews=remaining,
                    api_key=api_key
                )

                for claim_index, claim in enumerate(claims):
                    reviews = get_claim_reviews(claim)

                    for review_index, review in enumerate(reviews):
                        if yielded_count >= maximum:
                            return

                        identifier = (
                            f"query={query or 'all'}|"
                            f"language={language or 'all'}|"
                            f"claim={claim_index}"
                        )

                        yield identifier, review_index, {
                            "_claim": dict(claim),
                            "_review": dict(review),
                            "_requested_query": query,
                            "_requested_language": language
                        }

                        yielded_count += 1


# Lecture des éléments Google Fact Check

def get_claim_data(
    item: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Retourne l'affirmation contenue dans l'élément."""

    claim = item.get("_claim", {})
    return claim if isinstance(claim, Mapping) else {}


def get_review_data(
    item: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Retourne la vérification contenue dans l'élément."""

    review = item.get("_review", {})
    return review if isinstance(review, Mapping) else {}


def get_claim_title(item: Mapping[str, Any]) -> str:
    """Retourne le texte de l'affirmation."""

    return clean_text(get_claim_data(item).get("text"))


def get_review_text(item: Mapping[str, Any]) -> str:
    """Construit le texte de la vérification."""

    review = get_review_data(item)
    rating = clean_text(review.get("textualRating"))
    review_title = clean_text(review.get("title"))
    claim_title = get_claim_title(item)
    parts: list[str] = []

    if rating:
        parts.append(f"Évaluation : {rating}")

    if review_title and review_title.lower() != claim_title.lower():
        parts.append(f"Vérification : {review_title}")

    return " | ".join(parts)


def get_review_url(item: Mapping[str, Any]) -> str:
    """Retourne l'URL valide du fact-check."""

    url = normalize_value(get_review_data(item).get("url"))
    return url if is_valid_http_url(url) else ""


def get_review_publisher_name(
    item: Mapping[str, Any]
) -> str:
    """Retourne le nom de l'organisme de fact-checking."""

    publisher = get_review_publisher(get_review_data(item))
    return clean_text(publisher.get("name"))


def get_review_language(item: Mapping[str, Any]) -> str:
    """Retourne la langue de la vérification."""

    review_language = normalize_language_code(
        get_review_data(item).get("languageCode")
    )

    requested_language = normalize_language_code(
        item.get("_requested_language")
    )

    return review_language or requested_language


def get_review_published_at(item: Mapping[str, Any]) -> Any:
    """Retourne la date brute la plus pertinente."""

    review = get_review_data(item)
    claim = get_claim_data(item)

    return review.get("reviewDate") or claim.get("claimDate")

def build_google_fact_check_identifier(
    item: Mapping[str, Any],
    item_identifier: str
) -> str:
    """Construit un identifiant stable."""

    review_url = get_review_url(item)

    if review_url:
        return review_url

    return (
        f"google_fact_check:{item_identifier}:"
        f"{get_review_publisher_name(item)}:"
        f"{get_claim_title(item)}"
    )


# Construction de l'article standard

def build_google_fact_check_article(
    item: Any,
    item_index: int,
    item_identifier: str,
    source: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme une vérification au format CheckIt.AI."""

    del item_index

    if not isinstance(item, Mapping):
        return {}

    claim = get_claim_data(item)
    review = get_review_data(item)
    claimant = clean_text(claim.get("claimant"))
    publisher_name = get_review_publisher_name(item)
    review_url = get_review_url(item)
    requested_query = clean_text(item.get("_requested_query"))
    raw_rating = clean_text(review.get("textualRating"))
    label_result = classify_fact_check_label(raw_rating)

    article = build_standard_article(
        identifier=build_google_fact_check_identifier(
            item,
            item_identifier
        ),
        source=(
            publisher_name
            or source.get("name", "Google Fact Check Tools")
        ),
        title=get_claim_title(item),
        text=get_review_text(item),
        image_url="",
        image_path="",
        published_at=get_review_published_at(item),
        url=review_url,
        author=claimant,
        language=get_review_language(item),
        category=(
            requested_query
            or normalize_value(source.get("category"))
            or "fact_check"
        ),
        label=label_result.label,
        dataset_role=source.get(
            "role",
            "fact_check_reference"
        )
    )

    # Conserve les données spécifiques utiles aux étapes suivantes.
    article["claimant"] = claimant
    article["fact_check_rating"] = label_result.raw_value
    article["fact_check_rating_normalized"] = label_result.normalized_value
    article["fact_check_label_reason"] = label_result.reason
    article["fact_check_label_match"] = label_result.matched_value
    article["fact_check_publisher"] = publisher_name
    article["claim_date"] = convert_date_to_iso(claim.get("claimDate"))
    article["review_date"] = convert_date_to_iso(review.get("reviewDate"))

    logger.debug(
        "Google Fact Check : rating=%r | normalized=%r | "
        "label=%r | reason=%r | match=%r",
        label_result.raw_value,
        label_result.normalized_value,
        label_result.label,
        label_result.reason,
        label_result.matched_value
    )

    return article


# Validation spécifique

def validate_google_fact_check_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les contrôles propres à Google Fact Check."""

    del filters, source

    if not isinstance(item, Mapping):
        return False, "resultat_google_fact_check_invalide"

    if not get_claim_title(item):
        return False, "affirmation_absente"

    review = get_review_data(item)

    if not review:
        return False, "verification_absente"

    if not get_review_url(item):
        return False, "url_verification_invalide"

    rating = clean_text(review.get("textualRating"))
    review_title = clean_text(review.get("title"))

    if not rating and not review_title:
        return False, "evaluation_absente"

    return True, ""


# Adaptateur et extracteur Google Fact Check

GOOGLE_FACT_CHECK_ADAPTER = ApiAdapter(
    source_id="google_fact_check",
    default_name="Google Fact Check Tools",
    iter_items=iter_google_fact_check_items,
    build_article=build_google_fact_check_article,
    validate_item=validate_google_fact_check_item
)

GOOGLE_FACT_CHECK_EXTRACTOR = ApiExtractor(
    source_id="google_fact_check",
    default_name="Google Fact Check Tools",
    adapter=GOOGLE_FACT_CHECK_ADAPTER,
    section_name="api_sources",
    sources_file=SOURCES_FILE
)


# Fonctions publiques

def load_google_fact_check_source() -> dict[str, Any]:
    """Recharge et retourne la configuration Google Fact Check."""

    return dict(GOOGLE_FACT_CHECK_EXTRACTOR.reload_source())


def extract_articles_from_source(
    source: Mapping[str, Any]
) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_api_from_source(
        source=source,
        adapter=GOOGLE_FACT_CHECK_ADAPTER
    )


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction."""

    return GOOGLE_FACT_CHECK_EXTRACTOR.run()


# Exécution directe

if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} vérification(s) "
        f"Google Fact Check extraite(s). Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])