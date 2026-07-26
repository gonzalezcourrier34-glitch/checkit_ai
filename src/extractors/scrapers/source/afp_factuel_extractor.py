"""Point d'entrée du scraper AFP Factuel."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from config.paths import SOURCES_FILE
from src.extractors.core.extractor_results import ExtractorResult
from src.extractors.scrapers.scraper_engine import ScraperExtractor
from src.extractors.scrapers.scraper_extractor import create_standard_scraper_adapter


# Extracteur
AFP_ADAPTER = create_standard_scraper_adapter(
    source_id="afp_factuel",
    default_name="AFP Factuel"
)

AFP_EXTRACTOR = ScraperExtractor(
    adapter=AFP_ADAPTER,
    sources_file=SOURCES_FILE
)


# Fonctions publiques
def load_afp_source() -> dict[str, Any]:
    """Recharge et retourne la configuration AFP Factuel."""

    return AFP_EXTRACTOR.reload_source()


def extract_articles_from_source(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Lance l'extraction depuis une configuration déjà chargée."""

    return AFP_EXTRACTOR.extract(source)


def extract_afp_articles_from_source(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Conserve la compatibilité avec l'ancien nom de fonction."""

    return extract_articles_from_source(source)


def extract_all_articles() -> ExtractorResult:
    """Charge la configuration puis lance l'extraction AFP Factuel."""

    return AFP_EXTRACTOR.run()


# Exécution directe
if __name__ == "__main__":
    result = extract_all_articles()

    print(
        f"{len(result.articles)} article(s) AFP Factuel extrait(s). "
        f"Statut : {result.status}."
    )

    if result.message:
        print(result.message)
    if result.articles:
        print(result.articles[0])