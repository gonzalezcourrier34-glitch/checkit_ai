"""Point d'entrée du scraper Reuters Fact Check."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from config.paths import SOURCES_FILE
from src.extractors.core.extractor_results import ExtractorResult
from src.extractors.scrapers.scraper_engine import ScraperExtractor
from src.extractors.scrapers.scraper_extractor import create_standard_scraper_adapter


# Extracteur
REUTERS_ADAPTER = create_standard_scraper_adapter(
    source_id="reuters_fact_check",
    default_name="Reuters Fact Check"
)

REUTERS_EXTRACTOR = ScraperExtractor(
    adapter=REUTERS_ADAPTER,
    sources_file=SOURCES_FILE
)


# Fonctions publiques
def load_reuters_source() -> dict[str, Any]:
    """Recharge et retourne la configuration Reuters Fact Check."""

    return REUTERS_EXTRACTOR.reload_source()


def extract_articles_from_source(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return REUTERS_EXTRACTOR.extract(source)


def extract_reuters_articles_from_source(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Conserve la compatibilité avec l'ancien nom de fonction."""

    return extract_articles_from_source(source)


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction Reuters Fact Check."""

    return REUTERS_EXTRACTOR.run()


# Exécution directe
if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} article(s) Reuters Fact Check extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)

    if result.articles:
        print(result.articles[0])