"""Adaptateur utilisé pour extraire des publications depuis Reddit avec PRAW."""

from __future__ import annotations

import html
from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import urljoin, urlparse

import praw
from praw.models import Submission
from prawcore.exceptions import (
    Forbidden,
    NotFound,
    PrawcoreException,
    RequestException,
    ResponseException,
    ServerError,
    TooManyRequests
)
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config.paths import SOURCES_FILE

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
from config.environment import get_environment_variable

from src.logger import get_logger
from config.settings import (
    MAX_RETRIES,
    RETRY_DELAY_SECONDS    
)
from src.article.processing.article_cleaner import clean_text
from src.utils.date_utils import convert_date_to_iso
from src.utils.value_utils import normalize_value
from src.utils.parsing_utils import (
    parse_boolean,
    parse_optional_float
    )
from src.utils.url_utils import is_valid_http_url 
from config.environment import is_valid_secret
from src.utils.extractor_utils import build_standard_article

logger = get_logger(__name__)


# Configuration générale de Reddit

REDDIT_BASE_URL = "https://www.reddit.com"
REDDIT_DEFAULT_LISTING = "hot"
REDDIT_DEFAULT_TIME_FILTER = "day"
REDDIT_RATE_LIMIT_SECONDS = 60

REDDIT_DIRECT_IMAGE_EXTENSIONS: frozenset[str] = frozenset({
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
})
REDDIT_SUPPORTED_LISTINGS: frozenset[str] = frozenset({
    "hot",
    "new",
    "rising",
    "top"
})
REDDIT_SUPPORTED_TIME_FILTERS: frozenset[str] = frozenset({
    "hour",
    "day",
    "week",
    "month",
    "year",
    "all"
})

# valeur des clés

def validate_reddit_authentication() -> tuple[str, str, str]:
    """Valide et retourne les identifiants Reddit."""

    client_id = REDDIT_EXTRACTOR.client_id
    client_secret = REDDIT_EXTRACTOR.client_secret
    user_agent = normalize_value(
        get_environment_variable("USER_AGENT")
    )

    if not is_valid_secret(client_id):
        raise RuntimeError(
            "Le client ID Reddit est absent ou invalide."
        )

    if not is_valid_secret(client_secret):
        raise RuntimeError(
            "Le client secret Reddit est absent ou invalide."
        )

    if not user_agent:
        raise RuntimeError(
            "La variable USER_AGENT est absente ou invalide."
        )

    return client_id, client_secret, user_agent

# Lecture de la configuration

def get_listing_name(source: Mapping[str, Any]) -> str:
    """Retourne le classement Reddit configuré."""

    listing = normalize_value(
        source.get("listing", REDDIT_DEFAULT_LISTING)
    ).lower()

    # Une valeur inconnue ne doit pas provoquer l'échec de l'extraction.
    if listing not in REDDIT_SUPPORTED_LISTINGS:
        logger.warning(
            "Classement Reddit invalide : %s. %s sera utilisé.",
            listing or "valeur absente",
            REDDIT_DEFAULT_LISTING
        )
        return REDDIT_DEFAULT_LISTING

    return listing


def get_time_filter(source: Mapping[str, Any]) -> str:
    """Retourne la période utilisée avec le classement top."""

    time_filter = normalize_value(
        source.get("time_filter", REDDIT_DEFAULT_TIME_FILTER)
    ).lower()

    # Reddit accepte uniquement les périodes déclarées dans cette liste.
    if time_filter not in REDDIT_SUPPORTED_TIME_FILTERS:
        logger.warning(
            "Période Reddit invalide : %s. %s sera utilisé.",
            time_filter or "valeur absente",
            REDDIT_DEFAULT_TIME_FILTER
        )
        return REDDIT_DEFAULT_TIME_FILTER

    return time_filter


def normalize_subreddit_name(value: Any) -> str:
    """Normalise un nom de subreddit."""

    subreddit = normalize_value(value).strip()
    return subreddit.removeprefix("/r/").removeprefix("r/").strip("/")


def get_subreddits(source: Mapping[str, Any]) -> list[str]:
    """Retourne les subreddits configurés."""

    # Les valeurs vides sont supprimées et l'ordre initial est conservé.
    subreddits = [
        normalized
        for value in normalize_string_list(source.get("subreddits"))
        if (normalized := normalize_subreddit_name(value))
    ]
    return list(dict.fromkeys(subreddits))


# Création du client Reddit

def create_reddit_client(
    client_id: str,
    client_secret: str,
    user_agent: str
) -> praw.Reddit:
    """Crée un client PRAW en lecture seule."""

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            check_for_async=False,
            ratelimit_seconds=REDDIT_RATE_LIMIT_SECONDS
        )
        reddit.read_only = True
        logger.info("Client Reddit créé en lecture seule.")
        return reddit

    except (PrawcoreException, TypeError, ValueError) as error:
        raise RuntimeError(
            f"Impossible de créer le client Reddit : {error}"
        ) from error
        

# Construction et validation des URL

def build_reddit_post_url(post: Submission) -> str:
    """Construit l'URL permanente d'une publication."""

    permalink = normalize_value(getattr(post, "permalink", ""))

    if not permalink:
        return ""

    url = urljoin(REDDIT_BASE_URL, permalink)
    return url if is_valid_http_url(url) else ""


def normalize_image_url(value: Any) -> str:
    """Décode et vérifie une URL d'image."""

    url = html.unescape(normalize_value(value))
    return url if is_valid_http_url(url) else ""


def is_direct_image_url(value: Any) -> bool:
    """Vérifie qu'une URL pointe vers une image prise en charge."""

    url = normalize_image_url(value)

    if not url:
        return False

    try:
        path = urlparse(url).path.lower()
    except ValueError:
        return False

    return any(path.endswith(extension) for extension in REDDIT_DIRECT_IMAGE_EXTENSIONS)


# Extraction des images Reddit

def get_gallery_image_url(post: Submission) -> str:
    """Retourne la première image valide d'une galerie Reddit."""

    gallery_data = getattr(post, "gallery_data", {})
    media_metadata = getattr(post, "media_metadata", {})

    if not isinstance(media_metadata, Mapping):
        return ""

    media_ids: list[str] = []

    # L'ordre fourni par gallery_data est utilisé en priorité.
    if isinstance(gallery_data, Mapping):
        items = gallery_data.get("items", [])

        if isinstance(items, list):
            media_ids = [
                media_id
                for item in items
                if isinstance(item, Mapping)
                and (media_id := normalize_value(item.get("media_id")))
            ]

    # Les métadonnées servent de solution de secours.
    if not media_ids:
        media_ids = [
            normalized_id
            for media_id in media_metadata
            if (normalized_id := normalize_value(media_id))
        ]

    for media_id in media_ids:
        metadata = media_metadata.get(media_id, {})

        if not isinstance(metadata, Mapping):
            continue

        source_data = metadata.get("s", {})

        if not isinstance(source_data, Mapping):
            continue

        image_url = normalize_image_url(
            source_data.get("u") or source_data.get("gif")
        )

        if image_url:
            return image_url

    return ""


def get_preview_image_url(post: Submission) -> str:
    """Retourne l'image principale du champ preview."""

    preview = getattr(post, "preview", {})

    if not isinstance(preview, Mapping):
        return ""

    images = preview.get("images", [])

    if not isinstance(images, list) or not images:
        return ""

    first_image = images[0]

    if not isinstance(first_image, Mapping):
        return ""

    source_data = first_image.get("source", {})

    if not isinstance(source_data, Mapping):
        return ""

    return normalize_image_url(source_data.get("url"))


def get_thumbnail_image_url(post: Submission) -> str:
    """Retourne une miniature Reddit valide."""

    thumbnail = normalize_image_url(getattr(post, "thumbnail", ""))
    return thumbnail if is_direct_image_url(thumbnail) else ""


def get_post_image_url(post: Submission) -> str:
    """Retourne la meilleure image disponible."""

    post_url = normalize_image_url(getattr(post, "url", ""))

    if is_direct_image_url(post_url):
        return post_url

    # Les sources sont testées de la plus fiable à la plus approximative.
    return (
        get_gallery_image_url(post)
        or get_preview_image_url(post)
        or get_thumbnail_image_url(post)
    )


# Extraction du contenu Reddit

def get_post_text(post: Submission) -> str:
    """Retourne le texte principal de la publication."""

    text = clean_text(getattr(post, "selftext", ""))

    # Reddit remplace certains contenus supprimés par ces marqueurs.
    return "" if text.lower() in {"[deleted]", "[removed]"} else text


def get_post_author(post: Submission) -> str:
    """Retourne le nom de l'auteur."""

    author = getattr(post, "author", None)
    return normalize_value(author) if author is not None else ""


# Filtrage spécifique aux publications Reddit

def should_skip_post(post: Submission, source: Mapping[str, Any]) -> str:
    """Retourne un motif de rejet propre à Reddit."""

    include_nsfw = parse_boolean(source.get("include_nsfw", False), False)
    include_spoilers = parse_boolean(source.get("include_spoilers", True), True)
    include_stickied = parse_boolean(source.get("include_stickied", False), False)

    if not include_nsfw and bool(getattr(post, "over_18", False)):
        return "contenu_nsfw"

    if not include_spoilers and bool(getattr(post, "spoiler", False)):
        return "spoiler"

    if not include_stickied and bool(getattr(post, "stickied", False)):
        return "publication_epinglee"

    return ""


def validate_minimum(
    value: Any,
    minimum: Any,
    rejection_reason: str
) -> tuple[bool, str]:
    """Compare une métrique à un minimum facultatif."""

    minimum_value = parse_optional_float(minimum)

    # L'absence de minimum signifie que le filtre n'est pas activé.
    if minimum_value is None:
        return True, ""

    numeric_value = parse_optional_float(value)

    # Une métrique absente ne doit pas être confondue avec une valeur nulle.
    if numeric_value is None:
        return True, ""

    if numeric_value < minimum_value:
        return False, rejection_reason

    return True, ""


def validate_reddit_metrics(
    post: Submission,
    filters: Mapping[str, Any]
) -> tuple[bool, str]:
    """Applique les filtres de score et de commentaires."""

    valid, reason = validate_minimum(
        getattr(post, "score", None),
        filters.get("min_score"),
        "score_insuffisant"
    )

    if not valid:
        return False, reason

    return validate_minimum(
        getattr(post, "num_comments", None),
        filters.get("min_comments"),
        "commentaires_insuffisants"
    )


# Construction d'un article CheckIt.AI

def build_reddit_article(
    post: Any,
    item_identifier: str,
    source: Mapping[str, Any],
    context: Mapping[str, Any]
) -> dict[str, Any]:
    """Transforme une publication Reddit au format CheckIt.AI."""

    if not isinstance(post, Submission):
        return {}

    post_url = build_reddit_post_url(post)
    reddit_id = normalize_value(getattr(post, "id", "")) or item_identifier

    if not reddit_id and not post_url:
        return {}

    subreddit_name = normalize_value(context.get("subreddit"))

    # published_at est utilisé par le moteur général pour filtrer l'âge.
    return build_standard_article(
        identifier=reddit_id or post_url,
        source=source.get("name", "Reddit"),
        title=clean_text(getattr(post, "title", "")),
        text=get_post_text(post),
        image_url=get_post_image_url(post),
        image_path="",
        published_at=convert_date_to_iso(getattr(post, "created_utc", "")),
        url=post_url,
        author=get_post_author(post),
        language=source.get("language", "en"),
        category=(
            normalize_value(source.get("category"))
            or subreddit_name.lower()
            or "social"
        ),
        label="",
        dataset_role=source.get("role", "social_reference")
    )


def validate_reddit_item(
    item: Any,
    filters: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    """Vérifie qu'un élément Reddit est exploitable."""

    del source

    if not isinstance(item, Submission):
        return False, "publication_reddit_invalide"

    if not normalize_value(getattr(item, "id", "")) and not build_reddit_post_url(item):
        return False, "identifiant_absent"

    # Les filtres ont déjà été normalisés par le moteur social commun.
    return validate_reddit_metrics(item, filters)


# Récupération des publications avec PRAW

def get_subreddit_listing(
    subreddit: Any,
    listing: str,
    limit: int,
    time_filter: str
) -> Iterable[Submission]:
    """Retourne le listing PRAW demandé."""

    if listing == "new":
        return subreddit.new(limit=limit)

    if listing == "rising":
        return subreddit.rising(limit=limit)

    if listing == "top":
        return subreddit.top(time_filter=time_filter, limit=limit)

    return subreddit.hot(limit=limit)


@retry(
    retry=retry_if_exception_type((
        RequestException,
        ServerError,
        TooManyRequests
    )),
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(
        multiplier=RETRY_DELAY_SECONDS,
        min=RETRY_DELAY_SECONDS,
        max=max(RETRY_DELAY_SECONDS * 5, RETRY_DELAY_SECONDS)
    ),
    reraise=True
)
def fetch_subreddit_posts(
    reddit: praw.Reddit,
    subreddit_name: str,
    listing: str,
    limit: int,
    time_filter: str
) -> list[Submission]:
    """Récupère les publications d'un subreddit."""

    # Une limite minimale de 1 évite les appels PRAW incohérents.
    subreddit = reddit.subreddit(subreddit_name)
    posts = get_subreddit_listing(subreddit, listing, max(limit, 1), time_filter)
    return list(posts)


# Adaptation des publications au moteur social commun

def iter_reddit_items(
    source: Mapping[str, Any],
    maximum_articles: int
) -> Iterable[SocialItem]:
    """Produit progressivement les publications Reddit."""

    subreddits = get_subreddits(source)

    if not subreddits:
        logger.warning("Aucun subreddit valide configuré.")
        return

    client_id, client_secret, user_agent = (
        validate_reddit_authentication()
    )

    reddit = create_reddit_client(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    listing = get_listing_name(source)
    time_filter = get_time_filter(source)

    # Le moteur général arrête la consommation dès que max_articles est atteint.
    for subreddit_name in subreddits:
        logger.info(
            "Extraction Reddit : r/%s, classement=%s, limite=%s.",
            subreddit_name,
            listing,
            maximum_articles
        )

        try:
            posts = fetch_subreddit_posts(
                reddit,
                subreddit_name,
                listing,
                maximum_articles,
                time_filter
            )
        except NotFound:
            logger.error("Subreddit introuvable : r/%s.", subreddit_name)
            yield SocialItem("", None, rejection_reason="subreddit_introuvable")
            continue
        except Forbidden:
            logger.error("Accès interdit au subreddit r/%s.", subreddit_name)
            yield SocialItem("", None, rejection_reason="subreddit_interdit")
            continue
        except TooManyRequests as error:
            logger.error(
                "Limite de requêtes Reddit atteinte pour r/%s : %s",
                subreddit_name,
                error
            )
            yield SocialItem("", None, rejection_reason="limite_requetes")
            continue
        except ResponseException as error:
            logger.error(
                "Réponse Reddit invalide pour r/%s : %s",
                subreddit_name,
                error
            )
            yield SocialItem("", None, rejection_reason="reponse_api_invalide")
            continue
        except PrawcoreException as error:
            logger.error(
                "Erreur API Reddit pour r/%s : %s",
                subreddit_name,
                error
            )
            yield SocialItem("", None, rejection_reason="erreur_api")
            continue
        except (TypeError, ValueError, AttributeError) as error:
            logger.error(
                "Configuration Reddit invalide pour r/%s : %s",
                subreddit_name,
                error
            )
            yield SocialItem("", None, rejection_reason="configuration_invalide")
            continue

        for post in posts:
            identifier = normalize_value(getattr(post, "id", ""))

            # Ces filtres sont propres au modèle de données Reddit.
            item_context = {
                "subreddit": subreddit_name
            }

            if skip_reason := should_skip_post(post, source):
                yield SocialItem(
                    identifier=identifier,
                    item=post,
                    context=item_context,
                    rejection_reason=skip_reason
                )
                continue

            yield SocialItem(
                identifier=identifier,
                item=post,
                context=item_context
            )


# Adaptateur Reddit

REDDIT_ADAPTER = SocialAdapter(
    source_id="reddit",
    default_name="Reddit",
    iter_items=iter_reddit_items,
    build_article=build_reddit_article,
    validate_item=validate_reddit_item
)


# Extracteur Reddit

REDDIT_EXTRACTOR = SocialExtractor(
    adapter=REDDIT_ADAPTER,
    section_name="social_sources",
    sources_file=SOURCES_FILE
)


# Fonctions publiques

def load_reddit_source() -> dict[str, Any]:
    """Recharge et retourne la configuration Reddit."""

    return REDDIT_EXTRACTOR.reload_source()


def extract_articles_from_source(
    source: Mapping[str, Any]
) -> ExtractorResult:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return extract_social_source(
        source=source,
        adapter=REDDIT_ADAPTER
    )


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction Reddit."""

    return REDDIT_EXTRACTOR.run()


# Exécution directe

if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} publication(s) Reddit extraite(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])