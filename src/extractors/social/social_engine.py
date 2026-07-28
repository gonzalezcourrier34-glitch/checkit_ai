"""Moteur générique utilisé par les extracteurs de réseaux sociaux."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config.constants import SOURCE_TYPE_SOCIAL
from config.environment import get_secret
from config.paths import SOURCES_FILE
from config.source_config import load_validated_source
from src.article.processing.article_deduplicator import (
    is_duplicate_article,
    register_article
)
from src.extractors.core.extractor_service import (
    ExtractorResult,
    execute_configured_extractor
)
from src.extractors.social.social_adapter import SocialAdapter, SocialItem
from src.extractors.social.social_context import (
    SocialExtractionContext,
    create_extraction_context,
    validate_article_age
)
from src.logger import get_logger
from src.utils.extractor_utils import log_extraction_summary, validate_article
from src.utils.value_utils import normalize_value

logger = get_logger(__name__)


# Extracteur
@dataclass(slots=True)
class SocialExtractor:
    """Représente un extracteur social configurable et exécutable."""

    adapter: SocialAdapter
    section_name: str = "social_sources"
    sources_file: Path = SOURCES_FILE
    _source: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Normalise et valide la configuration de l'extracteur."""

        self.section_name = normalize_value(self.section_name) or "social_sources"

        if not isinstance(self.adapter, SocialAdapter):
            raise TypeError("adapter doit être une instance de SocialAdapter.")
        if self.sources_file is None:
            raise ValueError("Le fichier de configuration des sources est requis.")

    # Configuration
    def load_source(self, force_reload: bool = False) -> dict[str, Any]:
        """Charge et met en cache la configuration sociale validée."""

        if self._source and not force_reload:
            return dict(self._source)

        loaded_source = load_validated_source(
            self.sources_file,
            self.adapter.source_id
        )
        self._source = dict(loaded_source)
        return dict(self._source)

    def reload_source(self) -> dict[str, Any]:
        """Recharge explicitement la configuration depuis le fichier YAML."""

        return self.load_source(force_reload=True)

    def get_source(self) -> dict[str, Any]:
        """Retourne la configuration actuellement disponible."""

        return self.load_source()

    @property
    def source(self) -> Mapping[str, Any]:
        """Retourne la configuration courante de la plateforme sociale."""

        return self.load_source()

    # Secrets
    @property
    def client_id_secret_name(self) -> str:
        """Retourne le nom du secret contenant le client ID."""

        return normalize_value(self.source.get("client_id_secret_name"))

    @property
    def client_secret_secret_name(self) -> str:
        """Retourne le nom du secret contenant le client secret."""

        return normalize_value(self.source.get("client_secret_secret_name"))

    @property
    def client_id(self) -> str:
        """Résout le client ID depuis Docker Secrets ou l'environnement."""

        secret_name = self.client_id_secret_name
        return get_secret(secret_name) if secret_name else ""

    @property
    def client_secret(self) -> str:
        """Résout le client secret depuis Docker Secrets ou l'environnement."""

        secret_name = self.client_secret_secret_name
        return get_secret(secret_name) if secret_name else ""

    # Exécution
    def extract(self, source: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Lance le moteur social avec l'adaptateur configuré."""

        return extract_social_source(source, self.adapter)

    def run(self) -> ExtractorResult:
        """Charge la configuration puis exécute l'extracteur social."""

        return execute_configured_extractor(
            extractor_name=self.adapter.default_name,
            source_type=SOURCE_TYPE_SOCIAL,
            source_loader=self.reload_source,
            extraction_function=self.extract
        )


# Validation spécifique
def validate_social_item(
    social_item: SocialItem,
    adapter: SocialAdapter,
    context: SocialExtractionContext
) -> tuple[bool, str]:
    """Applique la validation spécifique d'un élément social."""

    if social_item.rejection_reason:
        return False, social_item.rejection_reason

    if adapter.validate_item is None:
        return True, ""

    try:
        result = adapter.validate_item(
            social_item.item,
            context.filters,
            context.source
        )

    except Exception as error:
        logger.exception(
            "Validation %s impossible pour %s : %s",
            adapter.default_name,
            social_item.identifier or "élément sans identifiant",
            error
        )
        return False, "validation_impossible"

    if not isinstance(result, tuple) or len(result) != 2:
        logger.error(
            "Résultat de validation invalide pour %s.",
            adapter.default_name
        )
        return False, "validation_invalide"

    valid, reason = result

    if not isinstance(valid, bool):
        logger.error(
            "Statut de validation invalide pour %s.",
            adapter.default_name
        )
        return False, "validation_invalide"

    return valid, normalize_value(reason)


# Construction
def build_social_article(
    social_item: SocialItem,
    adapter: SocialAdapter,
    context: SocialExtractionContext
) -> dict[str, Any] | None:
    """Construit et normalise un article social."""

    try:
        article = adapter.build_article(
            social_item.item,
            social_item.identifier,
            context.source,
            social_item.context
        )

    except Exception as error:
        logger.exception(
            "Construction %s impossible pour %s : %s",
            adapter.default_name,
            social_item.identifier or "élément sans identifiant",
            error
        )
        return None

    if not isinstance(article, Mapping) or not article:
        return None

    normalized_article = dict(article)

    # L'adaptateur peut placer la plateforme ou la communauté dans "source".
    # Le moteur conserve cette information avant de restaurer l'identifiant
    # technique attendu par le pipeline.
    publisher = normalize_value(
        normalized_article.get("publisher")
        or normalized_article.get("source")
    )

    if (
        publisher
        and context.source_id
        and publisher.casefold() != context.source_id.casefold()
    ):
        normalized_article["publisher"] = publisher

    normalized_article["source"] = context.source_id
    normalized_article["source_type"] = context.source_type
    normalized_article.setdefault("source_name", context.source_name)

    return normalized_article


# Traitement
def process_social_item(
    social_item: SocialItem,
    adapter: SocialAdapter,
    context: SocialExtractionContext
) -> None:
    """Valide, transforme et conserve un élément social."""

    context.processed_count += 1

    # Validation propre à la plateforme sociale
    valid, reason = validate_social_item(
        social_item,
        adapter,
        context
    )

    if not valid:
        context.reject(reason or "element_invalide")
        return

    # Construction et normalisation de l'article
    article = build_social_article(
        social_item,
        adapter,
        context
    )

    if not article:
        context.reject("construction_invalide")
        return

    # Contrôle de l'ancienneté de la publication
    valid, reason = validate_article_age(
        article,
        context.max_article_age_days
    )

    if not valid:
        context.reject(reason or "article_trop_ancien")
        return

    # Validation commune à tous les articles
    try:
        valid, reason = validate_article(
            article,
            context.filters
        )

    except Exception as error:
        logger.exception(
            "Validation de l'article %s impossible : %s",
            social_item.identifier or "sans identifiant",
            error
        )
        context.reject("validation_article_impossible")
        return

    if not valid:
        context.reject(reason or "article_invalide")
        return

    # Déduplication au niveau de la source sociale
    if (
        context.remove_duplicates
        and is_duplicate_article(article, context.seen_keys)
    ):
        context.reject("doublon")
        return

    if context.remove_duplicates:
        register_article(article, context.seen_keys)

    context.add_article(article)


# Extraction
def extract_social_source(
    source: Mapping[str, Any],
    adapter: SocialAdapter
) -> list[dict[str, Any]]:
    """Extrait une source sociale avec l'adaptateur fourni."""

    if not isinstance(adapter, SocialAdapter):
        logger.error(
            "Adaptateur social invalide : %s.",
            type(adapter).__name__
        )
        return []

    context = create_extraction_context(source, adapter)

    if context is None:
        return []

    # L'itérateur est créé séparément pour pouvoir isoler une erreur
    # d'initialisation d'une erreur survenant pendant son parcours.
    try:
        social_items = iter(
            adapter.iter_items(
                context.source,
                context.maximum_articles
            )
        )

    except Exception as error:
        logger.exception(
            "Initialisation %s impossible : %s",
            context.source_name,
            error
        )
        context.reject("initialisation_impossible")
        social_items = iter(())

    while not context.completed:
        try:
            social_item = next(social_items)

        except StopIteration:
            break

        except Exception as error:
            logger.exception(
                "Parcours %s interrompu : %s",
                context.source_name,
                error
            )
            context.reject("parcours_interrompu")
            break

        if not isinstance(social_item, SocialItem):
            logger.warning(
                "Élément social invalide retourné par %s.",
                adapter.default_name
            )
            context.processed_count += 1
            context.reject("element_social_invalide")
            continue

        try:
            process_social_item(
                social_item,
                adapter,
                context
            )

        except Exception as error:
            # Ce dernier filet protège l'extraction globale contre une donnée
            # isolée qui aurait échappé aux validations précédentes.
            logger.exception(
                "Erreur inattendue pendant le traitement %s : %s",
                social_item.identifier or "d'un élément sans identifiant",
                error
            )
            context.reject("erreur_inattendue")

    # Bilan commun de l'extraction
    log_extraction_summary(
        source_name=context.source_name,
        extracted_count=len(context.articles),
        processed_count=context.processed_count,
        rejection_stats=context.rejection_stats
    )

    if len(context.articles) < context.maximum_articles:
        logger.warning(
            "%s : %s élément(s) valide(s) trouvé(s) sur %s demandés.",
            context.source_name,
            len(context.articles),
            context.maximum_articles
        )

    return context.articles