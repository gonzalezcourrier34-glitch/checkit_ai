"""Point d'entrée du dashboard CheckIt.AI.

Ce module initialise l'application Streamlit, affiche la sidebar
et charge la page sélectionnée par l'utilisateur.

La logique métier reste placée dans les services.
Le contenu des écrans reste placé dans les modules du dashboard.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import streamlit as st


# Chemins

DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_DIR = DASHBOARD_DIR.parent

project_path = str(PROJECT_DIR)

if project_path not in sys.path:
    sys.path.insert(0, project_path)


# Imports internes

from dashboard.dashboard.dashboard_administration import render_administration_page
from dashboard.dashboard.dashboard_data import render_data_page
from dashboard.dashboard.dashboard_pipeline import render_pipeline_page
from dashboard.dashboard.dashboard_sidebar import (
    PAGE_ADMINISTRATION,
    PAGE_DATA,
    PAGE_PIPELINE,
    load_services_status,
    render_sidebar
)
from src.logger import get_logger

logger = get_logger(__name__)


# Configuration

APP_TITLE = "CheckIt.AI"
APP_ICON = "🔎"
APP_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

SERVICE_LABELS = {
    "postgres": "PostgreSQL",
    "airflow": "Airflow"
}

PAGE_RENDERERS: dict[str, Callable[[], None]] = {
    PAGE_PIPELINE: render_pipeline_page,
    PAGE_DATA: render_data_page,
    PAGE_ADMINISTRATION: render_administration_page
}


# Page Streamlit

def configure_page() -> None:
    """Configure la fenêtre principale Streamlit."""

    st.set_page_config(
        page_title=f"{APP_TITLE} | Dashboard",
        page_icon=APP_ICON,
        layout=APP_LAYOUT,
        initial_sidebar_state=SIDEBAR_STATE
    )

    st.set_option(
        "client.showSidebarNavigation",
        False
    )


def apply_dashboard_style() -> None:
    """Applique le style général du dashboard."""

    st.markdown(
        """
        <style>
            .block-container {
                max-width: 1500px;
                padding-top: 1.5rem;
                padding-bottom: 2rem;
            }

            [data-testid="stSidebar"] {
                min-width: 17rem;
            }

            [data-testid="stSidebar"] .block-container {
                padding-top: 1.5rem;
            }

            [data-testid="stMetric"] {
                padding: 0.8rem;
                border: 1px solid rgba(128, 128, 128, 0.2);
                border-radius: 0.75rem;
            }

            [data-testid="stAlert"] {
                border-radius: 0.75rem;
            }

            .stButton > button {
                border-radius: 0.6rem;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


# Services

def get_unavailable_services(
    services_status: dict[str, bool]
) -> list[str]:
    """Retourne les noms des services indisponibles."""

    return [
        SERVICE_LABELS.get(service_name, service_name)
        for service_name, available in services_status.items()
        if not available
    ]


def render_service_warning() -> None:
    """Signale les services actuellement indisponibles."""

    services_status = load_services_status()
    unavailable_services = get_unavailable_services(
        services_status
    )

    if not unavailable_services:
        return

    service_names = ", ".join(unavailable_services)

    st.warning(
        f"Service(s) indisponible(s) : {service_names}. "
        "Certaines informations peuvent ne pas être affichées."
    )


# Navigation

def render_page(page_name: str) -> None:
    """Affiche la page sélectionnée dans la sidebar."""

    renderer = PAGE_RENDERERS.get(page_name)

    if renderer is None:
        logger.warning(
            "Page inconnue demandée dans le dashboard : %s.",
            page_name
        )

        st.error(
            "La page demandée n'existe pas."
        )
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
            st.code(
                str(error),
                language="text"
            )


# Application

def main() -> None:
    """Lance le dashboard CheckIt.AI."""

    configure_page()
    apply_dashboard_style()

    selected_page = render_sidebar()

    render_service_warning()
    render_page(selected_page)


if __name__ == "__main__":
    main()