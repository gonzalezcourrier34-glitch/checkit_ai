"""Adaptateur utilisé pour extraire des publications depuis Mastodon."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import parse_qsl, quote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from requests import Response, Session
from requests.exceptions import ConnectionError, RequestException, Timeout
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config.paths import SOURCES_FILE
from config.settings import HTTP_HEADERS, MAX_RETRIES, REQUEST_TIMEOUT, RETRY_DELAY_SECONDS

from src.extractors.social.social_adapter import (
    SocialAdapter,
    SocialItem,
)

from src.extractors.social.social_context import (
    normalize_string_list,
)

from src.extractors.social.social_engine import (
    SocialExtractor,
    extract_social_source,
)

from src.extractors.core.extractor_results import ExtractorResult

from src.logger import get_logger

from src.article.processing.article_cleaner import clean_text
from src.utils.date_utils import convert_date_to_iso
from src.utils.url_utils import is_valid_http_url
from src.utils.value_utils import normalize_value
from src.utils.parsing_utils import (
    parse_boolean,
    parse_optional_float
)
from src.utils.extractor_utils import build_standard_article

logger = get_logger(__name__)


# Configuration générale de Mastodon

MASTODON_API_TAG_PATH = "/api/v1/timelines/tag/{hashtag}"
MASTODON_DEFAULT_PAGE_SIZE = 40
MASTODON_MAX_PAGE_SIZE = 40
MASTODON_MAX_PAGES_PER_TIMELINE = 10
MASTODON_TITLE_MAX_LENGTH = 150


# Lecture de la configuration

def normalize_instance_url(value: Any) -> str:
    """Normalise l'URL d'une instance Mastodon."""

    instance_url = normalize_value(value).rstrip("/")

    if not is_valid_http_url(instance_url):
        return ""

    return instance_url


def get_instances(source: Mapping[str, Any]) -> list[str]:
    """Retourne les instances Mastodon configurées."""

    # Les URL invalides sont ignorées et les doublons sont supprimés.
    instances = [
        normalized
        for value in normalize_string_list(source.get("instances"))
        if (normalized := normalize_instance_url(value))
    ]
    return list(dict.fromkeys(instances))


def normalize_hashtag(value: Any) -> str:
    """Normalise un hashtag Mastodon."""

    return normalize_value(value).lstrip("#").strip()


def get_hashtags(source: Mapping[str, Any]) -> list[str]:
    """Retourne les hashtags Mastodon configurés."""

    hashtags = [
        normalized
        for value in normalize_string_list(source.get("hashtags"))
        if (normalized := normalize_hashtag(value))
    ]
    return list(dict.fromkeys(hashtags))


def get_languages(source: Mapping[str, Any]) -> set[str]:
    """Retourne les langues autorisées."""

    languages = {
        language.lower()
        for language in normalize_string_list(source.get("languages"))
        if language
    }

    # La valeur language reste acceptée pour conserver la compatibilité
    # avec les autres sources du projet.
    single_language = normalize_value(source.get("language")).lower()

    if single_language:
        languages.add(single_language)

    return languages


# Création du client HTTP

def create_mastodon_session() -> Session:
    """Crée une session HTTP configurée pour Mastodon."""

    session = requests.Session()
    session.headers.update(HTTP_HEADERS)
    session.headers.update({"Accept": "application/json"})
    return session


# Nettoyage du contenu Mastodon

def clean_mastodon_html(value: Any) -> str:
    """Transforme le contenu HTML d'un statut en texte propre."""

    content = normalize_value(value)

    if not content:
        return ""

    try:
        soup = BeautifulSoup(content, "html.parser")

        # Les paragraphes et retours HTML sont séparés afin d'éviter
        # la fusion artificielle de plusieurs phrases.
        text = soup.get_text(" ", strip=True)
    except (TypeError, ValueError):
        return clean_text(content)

    return clean_text(text)


def build_mastodon_title(text: Any) -> str:
    """Construit un titre court à partir du contenu d'un statut."""

    normalized_text = clean_text(text)

    if not normalized_text:
        return ""

    # La première phrase fournit généralement un titre plus naturel.
    first_sentence = re.split(r"(?<=[.!?])\s+", normalized_text, maxsplit=1)[0]
    title = first_sentence or normalized_text

    if len(title) <= MASTODON_TITLE_MAX_LENGTH:
        return title

    shortened = title[:MASTODON_TITLE_MAX_LENGTH].rsplit(" ", 1)[0].strip()
    return f"{shortened or title[:MASTODON_TITLE_MAX_LENGTH].strip()}…"


# Lecture des données d'un statut

def get_original_status(status: Mapping[str, Any]) -> Mapping[str, Any]:
    """Retourne le statut original lorsqu'il s'agit d'un repartage."""

    reblog = status.get("reblog")
    return reblog if isinstance(reblog, Mapping) else status


def get_status_identifier(status: Mapping[str, Any]) -> str:
    """Retourne l'identifiant d'un statut."""

    return normalize_value(status.get("id"))


def get_status_url(status: Mapping[str, Any]) -> str:
    """Retourne l'URL publique d'un statut."""

    url = normalize_value(status.get("url"))
    return url if is_valid_http_url(url) else ""


def get_status_author(status: Mapping[str, Any]) -> str:
    """Retourne le nom de l'auteur d'un statut."""

    account = status.get("account", {})

    if not isinstance(account, Mapping):
        return ""

    return (
        normalize_value(account.get("display_name"))
        or normalize_value(account.get("acct"))
        or normalize_value(account.get("username"))
    )


def get_status_language(status: Mapping[str, Any]) -> str:
    """Retourne la langue déclarée d'un statut."""

    return normalize_value(status.get("language")).lower()


def get_status_image_url(status: Mapping[str, Any]) -> str:
    """Retourne la première image valide attachée à un statut."""

    attachments = status.get("media_attachments", [])

    if not isinstance(attachments, list):
        return ""

    # Seules les images fixes sont transmises au service d'images.
    for attachment in attachments:
        if not isinstance(attachment, Mapping):
            continue

        media_type = normalize_value(attachment.get("type")).lower()

        if media_type != "image":
            continue

        image_url = normalize_value(
            attachment.get("url")
            or attachment.get("remote_url")
            or attachment.get("preview_url")
        )

        if is_valid_http_url(image_url):
            return image_url

    return ""


def get_status_text(status: Mapping[str, Any]) -> str:
    """Retourne le texte exploitable d'un statut."""

    content = clean_mastodon_html(status.get("content"))

    # Certains statuts utilisent uniquement un avertissement de contenu.
    if content:
        return content

    return clean_mastodon_html(status.get("spoiler_text"))


# Filtrage spécifique aux statuts Mastodon

def should_skip_status(
    status: Mapping[str, Any],
    source: Mapping[str, Any]
) -> str:
    """Retourne un motif de rejet propre à Mastodon."""

    include_reblogs = parse_boolean(source.get("include_reblogs", False), False)
    include_replies = parse_boolean(source.get("include_replies", False), False)
    include_sensitive = parse_boolean(source.get("include_sensitive", False), False)

    if not include_reblogs and isinstance(status.get("reblog"), Mapping):
        return "reblog_exclu"

    if not include_replies and normalize_value(status.get("in_reply_to_id")):
        return "reponse_exclue"

    if not include_sensitive and parse_boolean(status.get("sensitive"), False):
        return "contenu_sensible"

    allowed_languages = get_languages(source)
    status_language = get_status_language(get_original_status(status))

    if allowed_languages and status_language and status_language not in allowed_languages:
        return "langue_non_autorisee"

    return ""


def validate_minimum(
    value: Any,
    minimum: Any,
    rejection_reason: str
) -> tuple[bool, str]:
    """Compare une métrique Mastodon à un minimum facultatif."""

    minimum_value = parse_optional_float(minimum)

    # Une valeur null désactive le filtre correspondant.
    if minimum_value is None:
        return True, ""

    numeric_value = parse_optional_float(value)

    # Une métrique absente n'est pas assimilée arbitrairement à zéro.
    if numeric_value is None:
        return True, ""

    if numeric_value < minimum_value:
        return False, rejection_reason

    return True, ""


def validate_mastodon_metrics(
    status: Mapping[str, Any],
    filters: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les seuils d'engagement facultatifs."""

    checks = (
        (
            status.get("favourites_count"),
            filters.get("min_favourites"),
            "favoris_insuffisants"
        ),
        (
            status.get("reblogs_count"),
            filters.get("min_reblogs"),
            "reblogs_insuffisants"
        ),
        (
            status.get("replies_count"),
            filters.get("min_replies"),
            "reponses_insuffisantes"
        )
    )

    for value, minimum, reason in checks:
        valid, rejection_reason = validate_minimum(value, minimum, reason)

        if not valid:
            return False, rejection_reason

    return True, ""


def validate_mastodon_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Vérifie qu'un statut Mastodon est exploitable."""

    del source

    if not isinstance(item, Mapping):
        return False, "statut_mastodon_invalide"

    status = get_original_status(item)
    identifier = get_status_identifier(status)
    status_url = get_status_url(status)

    if not identifier and not status_url:
        return False, "identifiant_absent"

    if not get_status_text(status):
        return False, "contenu_absent"

    # Les filtres ont déjà été fusionnés par le moteur social commun.
    return validate_mastodon_metrics(status, filters)


# Construction d'un article CheckIt.AI

def build_mastodon_article(
    status: Any,
    item_identifier: str,
    source: Mapping[str, Any],
    context: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Transforme un statut Mastodon au format CheckIt.AI."""

    if not isinstance(status, Mapping):
        return {}

    original_status = get_original_status(status)
    status_url = get_status_url(original_status)
    status_id = get_status_identifier(original_status) or item_identifier

    if not status_id and not status_url:
        return {}

    text = get_status_text(original_status)
    hashtag = normalize_value(context.get("hashtag"))
    language = get_status_language(original_status)

    # published_at permet au moteur général d'appliquer max_article_age_days.
    return build_standard_article(
        identifier=status_id or status_url,
        source=source.get("name", "Mastodon"),
        title=build_mastodon_title(text),
        text=text,
        image_url=get_status_image_url(original_status),
        image_path="",
        published_at=convert_date_to_iso(original_status.get("created_at", "")),
        url=status_url,
        author=get_status_author(original_status),
        language=language or source.get("language", ""),
        category=normalize_value(source.get("category")) or hashtag.lower() or "social",
        label="",
        dataset_role=source.get("role", "acquisition")
    )


# Construction des requêtes Mastodon

def build_hashtag_timeline_url(instance: str, hashtag: str) -> str:
    """Construit l'URL de la timeline publique d'un hashtag."""

    path = MASTODON_API_TAG_PATH.format(hashtag=quote(hashtag, safe=""))
    return urljoin(f"{instance}/", path.lstrip("/"))


def get_next_max_id(response: Response) -> str:
    """Extrait le prochain identifiant de pagination Mastodon."""

    next_link = response.links.get("next", {})

    if not isinstance(next_link, Mapping):
        return ""

    next_url = normalize_value(next_link.get("url"))

    if not next_url:
        return ""

    try:
        parameters = dict(parse_qsl(urlsplit(next_url).query))
    except (TypeError, ValueError):
        return ""

    return normalize_value(parameters.get("max_id"))


@retry(
    retry=retry_if_exception_type((
        ConnectionError,
        Timeout
    )),
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(
        multiplier=RETRY_DELAY_SECONDS,
        min=RETRY_DELAY_SECONDS,
        max=max(RETRY_DELAY_SECONDS * 5, RETRY_DELAY_SECONDS)
    ),
    reraise=True
)
def fetch_mastodon_page(
    session: Session,
    instance: str,
    hashtag: str,
    limit: int,
    max_id: str = ""
) -> Response:
    """Récupère une page de statuts Mastodon."""

    parameters: dict[str, Any] = {
        "limit": min(max(limit, 1), MASTODON_MAX_PAGE_SIZE)
    }

    if max_id:
        parameters["max_id"] = max_id

    response = session.get(
        build_hashtag_timeline_url(instance, hashtag),
        params=parameters,
        timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response


def parse_mastodon_response(response: Response) -> list[Mapping[str, Any]]:
    """Valide et retourne les statuts d'une réponse Mastodon."""

    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError as error:
        raise ValueError("réponse JSON Mastodon invalide") from error

    if not isinstance(payload, list):
        raise ValueError("format de réponse Mastodon inattendu")

    return [status for status in payload if isinstance(status, Mapping)]


# Récupération progressive des statuts

def iter_hashtag_statuses(
    session: Session,
    instance: str,
    hashtag: str,
    maximum_articles: int
) -> Iterable[Mapping[str, Any]]:
    """Produit les statuts d'une timeline de hashtag."""

    remaining = maximum_articles
    max_id = ""
    visited_max_ids: set[str] = set()

    for _ in range(MASTODON_MAX_PAGES_PER_TIMELINE):
        if remaining <= 0:
            break

        response = fetch_mastodon_page(
            session=session,
            instance=instance,
            hashtag=hashtag,
            limit=min(remaining, MASTODON_DEFAULT_PAGE_SIZE),
            max_id=max_id
        )
        statuses = parse_mastodon_response(response)

        if not statuses:
            break

        yield from statuses
        remaining -= len(statuses)

        next_max_id = get_next_max_id(response)

        # L'absence de pagination ou une valeur répétée indique la fin.
        if not next_max_id or next_max_id in visited_max_ids:
            break

        visited_max_ids.add(next_max_id)
        max_id = next_max_id


# Adaptation des statuts au moteur social commun

def iter_mastodon_items(
    source: Mapping[str, Any],
    maximum_articles: int
) -> Iterable[SocialItem]:
    """Produit progressivement les statuts Mastodon."""

    instances = get_instances(source)
    hashtags = get_hashtags(source)

    if not instances:
        logger.warning("Aucune instance Mastodon valide configurée.")
        return

    if not hashtags:
        logger.warning("Aucun hashtag Mastodon valide configuré.")
        return

    session = create_mastodon_session()

    try:
        # Le moteur général arrête la consommation dès que max_articles
        # publications valides ont été enregistrées.
        for instance in instances:
            for hashtag in hashtags:
                logger.info(
                    "Extraction Mastodon : instance=%s, hashtag=#%s, limite=%s.",
                    instance,
                    hashtag,
                    maximum_articles
                )

                try:
                    statuses = iter_hashtag_statuses(
                        session,
                        instance,
                        hashtag,
                        maximum_articles
                    )

                    for status in statuses:
                        original_status = get_original_status(status)
                        identifier = get_status_identifier(original_status)

                        item_context = {
                            "instance": instance,
                            "hashtag": hashtag
                        }

                        # Ces filtres dépendent directement du modèle Mastodon.
                        if skip_reason := should_skip_status(status, source):
                            yield SocialItem(
                                identifier=identifier,
                                item=status,
                                context=item_context,
                                rejection_reason=skip_reason
                            )
                            continue

                        yield SocialItem(
                            identifier=identifier,
                            item=status,
                            context=item_context
                        )

                except requests.exceptions.HTTPError as error:
                    status_code = (
                        error.response.status_code
                        if error.response is not None
                        else "inconnu"
                    )
                    logger.error(
                        "Erreur HTTP Mastodon pour %s #%s : code=%s.",
                        instance,
                        hashtag,
                        status_code
                    )
                    yield SocialItem(
                        "",
                        None,
                        rejection_reason=f"erreur_http_{status_code}"
                    )

                except (ConnectionError, Timeout) as error:
                    logger.error(
                        "Instance Mastodon indisponible %s pour #%s : %s",
                        instance,
                        hashtag,
                        error
                    )
                    yield SocialItem(
                        "",
                        None,
                        rejection_reason="instance_indisponible"
                    )

                except (RequestException, ValueError, TypeError) as error:
                    logger.error(
                        "Extraction Mastodon impossible pour %s #%s : %s",
                        instance,
                        hashtag,
                        error
                    )
                    yield SocialItem(
                        "",
                        None,
                        rejection_reason="extraction_timeline_impossible"
                    )

    finally:
        session.close()


# Adaptateur Mastodon

MASTODON_ADAPTER = SocialAdapter(
    source_id="mastodon",
    default_name="Mastodon",
    iter_items=iter_mastodon_items,
    build_article=build_mastodon_article,
    validate_item=validate_mastodon_item
)


# Extracteur Mastodon

MASTODON_EXTRACTOR = SocialExtractor(
    adapter=MASTODON_ADAPTER,
    section_name="social_sources",
    sources_file=SOURCES_FILE
)


# Fonctions publiques

def load_mastodon_source() -> dict[str, Any]:
    """Recharge et retourne la configuration Mastodon."""

    return MASTODON_EXTRACTOR.reload_source()


def extract_articles_from_source(
    source: Mapping[str, Any]
) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_social_source(
        source=source,
        adapter=MASTODON_ADAPTER
    )


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction Mastodon."""

    return MASTODON_EXTRACTOR.run()


# Exécution directe

if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} publication(s) Mastodon extraite(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])