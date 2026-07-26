"""Point d'entrée du dashboard CheckIt.AI.

Ce module initialise l'application Streamlit et gère :

- la configuration générale de la page ;
- l'application du style commun ;
- la navigation fournie par la sidebar ;
- l'affichage de la page sélectionnée ;
- la gestion globale des erreurs d'affichage.

La logique métier reste placée dans les services.
Le contenu des écrans reste placé dans les modules du dossier pages.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import streamlit as st


# ============================================================================
# Chemins du projet
# ============================================================================

DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_DIR = DASHBOARD_DIR.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


# ============================================================================
# Imports du dashboard
# ============================================================================

from dashboard.dashbord_sidebar import (
    PAGE_ADMINISTRATION,
    PAGE_DATA,
    PAGE_PIPELINE,
    get_services_status,
    render_sidebar
)
from dashboard.dashbord_administration import render_administration_page
from dashboard.dashbord_data import render_data_page
from dashboard.dashbord_pipeline import render_pipeline_page
from src.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Configuration
# ============================================================================

APP_TITLE = "CheckIt.AI"
APP_ICON = "🔎"
APP_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

PAGE_RENDERERS: dict[str, Callable[[], None]] = {
    PAGE_PIPELINE: render_pipeline_page,
    PAGE_DATA: render_data_page,
    PAGE_ADMINISTRATION: render_administration_page
}


# ============================================================================
# Configuration de la page
# ============================================================================

def configure_page() -> None:
    """Configure la fenêtre principale Streamlit."""

    st.set_page_config(
        page_title=f"{APP_TITLE} | Dashboard",
        page_icon=APP_ICON,
        layout=APP_LAYOUT,
        initial_sidebar_state=SIDEBAR_STATE
    )

    # Masque la navigation automatique générée par dashboard/pages.
    st.set_option("client.showSidebarNavigation", False)


def apply_dashboard_style() -> None:
    """Applique les styles communs au dashboard."""

    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
            }

            [data-testid="stSidebar"] {
                min-width: 17rem;
            }

            [data-testid="stSidebar"] .block-container {
                padding-top: 1.5rem;
            }

            .checkit-sidebar-header {
                margin-bottom: 1.25rem;
            }

            .checkit-sidebar-title {
                font-size: 1.65rem;
                font-weight: 700;
                margin-bottom: 0;
            }

            .checkit-sidebar-subtitle {
                color: #808495;
                font-size: 0.9rem;
                margin-top: 0;
            }

            .checkit-service-row {
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                margin-bottom: 0.4rem;
            }

            .checkit-muted {
                color: #808495;
                font-size: 0.85rem;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================================
# Affichage
# ============================================================================

def render_service_warning() -> None:
    """Informe l'utilisateur lorsqu'un service est indisponible."""

    services = get_services_status()

    service_labels = {
        "postgres": "PostgreSQL",
        "airflow": "Airflow"
    }

    unavailable_services = [
        service_labels.get(service_name, service_name)
        for service_name, available in services.items()
        if not available
    ]

    if not unavailable_services:
        return

    st.warning(
        "Service(s) indisponible(s) : "
        f"{', '.join(unavailable_services)}. "
        "Certaines informations peuvent ne pas être affichées."
    )


def render_page(page_name: str) -> None:
    """Affiche la page associée à la navigation."""

    renderer = PAGE_RENDERERS.get(page_name)

    if renderer is None:
        st.error("La page demandée n'existe pas.")
        return

    try:
        renderer()

    except Exception as error:
        logger.exception(
            "Erreur pendant l'affichage de la page %s.",
            page_name
        )

        st.error(
            "Une erreur est survenue pendant le chargement "
            "de cette page."
        )

        with st.expander("Détail technique"):
            st.code(str(error))


# ============================================================================
# Application
# ============================================================================

def main() -> None:
    """Lance le dashboard CheckIt.AI."""

    configure_page()
    apply_dashboard_style()

    selected_page = render_sidebar()

    render_service_warning()
    render_page(selected_page)


if __name__ == "__main__":
    main()