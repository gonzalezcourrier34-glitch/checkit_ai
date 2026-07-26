"""Configuration et contexte communs aux extracteurs sociaux."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from config.constants import SOURCE_TYPE_SOCIAL
from config.settings import (
    MAX_ARTICLE_AGE_DAYS,
    MAX_ARTICLES_PER_SOURCE
)
from src.extractors.social.social_adapter import SocialAdapter
from src.logger import get_logger
from src.utils.date_utils import get_current_datetime, parse_datetime
from src.utils.filter_utils import get_filter_configuration
from src.utils.parsing_utils import parse_boolean, parse_non_negative_integer
from src.utils.value_utils import normalize_value

logger = get_logger(__name__)


# Contexte
@dataclass(slots=True)
class SocialExtractionContext:
    """Regroupe l'état d'une extraction sociale."""

    source: dict[str, Any]
    maximum_articles: int
    max_article_age_days: int
    filters: dict[str, Any]
    remove_duplicates: bool
    articles: list[dict[str, Any]] = field(default_factory=list)
    seen_keys: set[str] = field(default_factory=set)
    rejection_stats: Counter[str] = field(default_factory=Counter)
    processed_count: int = 0

    @property
    def source_name(self) -> str:
        """Retourne le nom lisible de la source."""

        return normalize_value(self.source.get("name")) or "source sociale"

    @property
    def source_id(self) -> str:
        """Retourne l'identifiant technique de la source."""

        return normalize_value(self.source.get("source_id")) or "social"

    @property
    def source_type(self) -> str:
        """Retourne le type technique de la source."""

        return SOURCE_TYPE_SOCIAL

    @property
    def completed(self) -> bool:
        """Indique si la limite d'articles est atteinte."""

        return len(self.articles) >= self.maximum_articles

    @property
    def rejected_count(self) -> int:
        """Retourne le nombre total d'éléments rejetés."""

        return sum(self.rejection_stats.values())

    def reject(self, reason: Any) -> None:
        """Enregistre un rejet avec un motif toujours exploitable."""

        self.rejection_stats[
            normalize_value(reason) or "article_invalide"
        ] += 1

    def add_article(self, article: dict[str, Any]) -> None:
        """Ajoute un article au contexte."""

        self.articles.append(article)


# Normalisation
def normalize_string_list(value: Any) -> list[str]:
    """Transforme une valeur en liste de textes uniques."""

    if isinstance(value, str):
        values: Sequence[Any] = value.split(",")

    elif isinstance(value, (list, tuple, set)):
        values = value

    else:
        return []

    normalized_values = [
        text
        for item in values
        if (text := normalize_value(item))
    ]

    return list(dict.fromkeys(normalized_values))


# Paramètres
def get_social_max_articles(source: Mapping[str, Any]) -> int:
    """Retourne le nombre maximal d'éléments à conserver."""

    configured = parse_non_negative_integer(
        source.get("max_articles", MAX_ARTICLES_PER_SOURCE),
        default=MAX_ARTICLES_PER_SOURCE
    )

    return min(configured, MAX_ARTICLES_PER_SOURCE)


def get_max_article_age_days(source: Mapping[str, Any]) -> int:
    """Retourne l'âge maximal autorisé pour les articles sociaux."""

    configured = parse_non_negative_integer(
        source.get("max_article_age_days", MAX_ARTICLE_AGE_DAYS),
        default=MAX_ARTICLE_AGE_DAYS
    )

    if MAX_ARTICLE_AGE_DAYS > 0:
        return min(
            configured or MAX_ARTICLE_AGE_DAYS,
            MAX_ARTICLE_AGE_DAYS
        )

    return configured


# Validation
def validate_article_age(
    article: Mapping[str, Any],
    max_article_age_days: int
) -> tuple[bool, str]:
    """Vérifie que la date d'un article respecte la période autorisée."""

    published_at = normalize_value(article.get("published_at"))

    # Une date absente est gérée par les filtres généraux de l'article.
    if not published_at:
        return True, ""

    article_date = parse_datetime(published_at)

    if article_date is None:
        return False, "date_publication_invalide"

    now = get_current_datetime()

    # Une petite tolérance évite les rejets dus aux écarts d'horloge.
    if article_date > now + timedelta(minutes=5):
        return False, "date_publication_future"

    if (
        max_article_age_days > 0
        and article_date < now - timedelta(days=max_article_age_days)
    ):
        return False, "article_trop_ancien"

    return True, ""


# Préparation
def create_extraction_context(
    source: Mapping[str, Any],
    adapter: SocialAdapter
) -> SocialExtractionContext | None:
    """Valide la source et prépare son contexte d'extraction."""

    if not isinstance(adapter, SocialAdapter):
        raise TypeError("adapter doit être une instance de SocialAdapter.")

    if not isinstance(source, Mapping):
        logger.error(
            "Configuration %s invalide : %s.",
            adapter.default_name,
            type(source).__name__
        )
        return None

    # Une copie évite de modifier directement la configuration d'origine.
    normalized_source = dict(source)

    # L'adaptateur fournit les valeurs de secours techniques et lisibles.
    normalized_source["source_id"] = (
        normalize_value(normalized_source.get("source_id"))
        or adapter.source_id
    )
    normalized_source["name"] = (
        normalize_value(normalized_source.get("name"))
        or adapter.default_name
    )

    source_name = normalize_value(normalized_source.get("name"))

    if not parse_boolean(
        normalized_source.get("enabled"),
        default=False
    ):
        logger.info("Source désactivée : %s.", source_name)
        return None

    maximum_articles = get_social_max_articles(normalized_source)

    if maximum_articles <= 0:
        logger.info("Aucun élément demandé pour %s.", source_name)
        return None

    filters = get_filter_configuration(normalized_source)

    if not isinstance(filters, Mapping):
        logger.error(
            "Configuration des filtres sociaux invalide pour %s.",
            source_name
        )
        return None

    normalized_filters = dict(filters)
    remove_duplicates = parse_boolean(
        normalized_filters.get("remove_duplicates", True),
        default=True
    )
    max_article_age_days = get_max_article_age_days(normalized_source)

    logger.info(
        "Extraction %s : limite=%s, âge maximal=%s jour(s).",
        source_name,
        maximum_articles,
        max_article_age_days or "désactivé"
    )

    return SocialExtractionContext(
        source=normalized_source,
        maximum_articles=maximum_articles,
        max_article_age_days=max_article_age_days,
        filters=normalized_filters,
        remove_duplicates=remove_duplicates
    )