"""Point d'entrée du scraper Full Fact."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from config.paths import SOURCES_FILE
from src.extractors.core.extractor_results import ExtractorResult
from src.extractors.scrapers.scraper_engine import ScraperExtractor
from src.extractors.scrapers.scraper_extractor import create_standard_scraper_adapter


# Extracteur
FULL_FACT_ADAPTER = create_standard_scraper_adapter(
    source_id="full_fact",
    default_name="Full Fact"
)

FULL_FACT_EXTRACTOR = ScraperExtractor(
    adapter=FULL_FACT_ADAPTER,
    sources_file=SOURCES_FILE
)


# Fonctions publiques
def load_full_fact_source() -> dict[str, Any]:
    """Recharge et retourne la configuration Full Fact."""

    return FULL_FACT_EXTRACTOR.reload_source()


def extract_articles_from_source(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return FULL_FACT_EXTRACTOR.extract(source)


def extract_full_fact_articles_from_source(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Conserve la compatibilité avec l'ancien nom de fonction."""

    return extract_articles_from_source(source)


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction Full Fact."""

    return FULL_FACT_EXTRACTOR.run()


# Exécution directe
if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} article(s) Full Fact extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)
    if result.articles:
        print(result.articles[0])