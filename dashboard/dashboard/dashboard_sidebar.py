"""Sidebar du dashboard CheckIt.AI.

Ce module gère :

- la navigation principale ;
- l'état de PostgreSQL et Airflow ;
- les principaux indicateurs du projet ;
- l'actualisation des données affichées.

La sidebar reste indépendante du contenu des pages.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.dashboard.dashboard_ui_utils import (
    format_number,
    format_status
)
from dashboard.services.dashboard_airflow_service import (
    is_airflow_available
)
from dashboard.services.dashboard_postgres_service import (
    get_database_overview,
    get_latest_pipeline_run,
    is_database_available
)
from src.logger import get_logger

logger = get_logger(__name__)


# Navigation

PAGE_PIPELINE = "Pipeline"
PAGE_DATA = "Données"
PAGE_ADMINISTRATION = "Administration"

PAGE_ICONS = {
    PAGE_PIPELINE: "📊",
    PAGE_DATA: "🗄️",
    PAGE_ADMINISTRATION: "🛠️"
}

PAGES = [
    PAGE_PIPELINE,
    PAGE_DATA,
    PAGE_ADMINISTRATION
]


# Cache

@st.cache_data(ttl=15, show_spinner=False)
def load_services_status() -> dict[str, bool]:
    """Charge la disponibilité des services du projet."""

    return {
        "postgres": is_database_available(),
        "airflow": is_airflow_available()
    }


@st.cache_data(ttl=30, show_spinner=False)
def load_sidebar_metrics() -> dict[str, Any]:
    """Charge les principaux indicateurs PostgreSQL."""

    default_metrics = {
        "articles": 0,
        "images": 0,
        "labels": 0,
        "features": 0,
        "sources": 0,
        "latest_status": "unknown"
    }

    try:
        overview = get_database_overview()
        latest_run = get_latest_pipeline_run()

        return {
            "articles": overview.get("articles", 0),
            "images": overview.get("images", 0),
            "labels": overview.get("article_labels", 0),
            "features": overview.get("article_features", 0),
            "sources": overview.get("sources", 0),
            "latest_status": (
                latest_run.get("status")
                if latest_run
                else "unknown"
            )
        }

    except Exception as error:
        logger.warning(
            "Impossible de charger les indicateurs de la sidebar : %s",
            error
        )

        return default_metrics


# En-tête

def render_header() -> None:
    """Affiche l'identité du dashboard."""

    st.title("🔎 CheckIt.AI")

    st.caption(
        "Supervision du pipeline d'acquisition multimodale."
    )


# Navigation

def render_navigation() -> str:
    """Affiche la navigation principale."""

    st.subheader("Navigation")

    return st.radio(
        "Page",
        options=PAGES,
        format_func=lambda page: (
            f"{PAGE_ICONS[page]} {page}"
        ),
        label_visibility="collapsed",
        key="dashboard_navigation"
    )


# Services

def render_service_status(
    name: str,
    icon: str,
    is_available: bool
) -> None:
    """Affiche la disponibilité d'un service."""

    label = f"{icon} {name}"

    if is_available:
        st.success(f"{label} disponible")
        return

    st.error(f"{label} indisponible")


def render_services_status(
    services: dict[str, bool]
) -> None:
    """Affiche l'état de PostgreSQL et Airflow."""

    st.subheader("État des services")

    render_service_status(
        name="PostgreSQL",
        icon="🐘",
        is_available=services.get("postgres", False)
    )

    render_service_status(
        name="Airflow",
        icon="🌬️",
        is_available=services.get("airflow", False)
    )


# Indicateurs

def render_database_metrics(
    metrics: dict[str, Any]
) -> None:
    """Affiche les principaux volumes PostgreSQL."""

    first_column, second_column = st.columns(2)

    with first_column:
        st.metric(
            label="📰 Articles",
            value=format_number(metrics.get("articles"))
        )

        st.metric(
            label="🏷️ Labels",
            value=format_number(metrics.get("labels"))
        )

    with second_column:
        st.metric(
            label="🖼️ Images",
            value=format_number(metrics.get("images"))
        )

        st.metric(
            label="🧩 Features",
            value=format_number(metrics.get("features"))
        )

    st.metric(
        label="🌐 Sources",
        value=format_number(metrics.get("sources"))
    )


def render_quick_overview() -> None:
    """Affiche une synthèse rapide du projet."""

    metrics = load_sidebar_metrics()

    st.subheader("Vue rapide")

    st.metric(
        label="Dernier pipeline",
        value=format_status(
            metrics.get("latest_status")
        )
    )

    render_database_metrics(metrics)


# Actualisation

def clear_sidebar_cache() -> None:
    """Supprime uniquement le cache de la sidebar."""

    load_services_status.clear()
    load_sidebar_metrics.clear()


def render_refresh_button() -> None:
    """Affiche le bouton d'actualisation."""

    if st.button(
        "🔄 Actualiser",
        width="stretch",
        key="refresh_dashboard_sidebar"
    ):
        clear_sidebar_cache()
        st.rerun()

    st.caption(
        "Les indicateurs sont conservés en cache "
        "pendant quelques secondes."
    )


# Sidebar

def render_sidebar() -> str:
    """Affiche la sidebar et retourne la page sélectionnée."""

    services = load_services_status()

    with st.sidebar:
        render_header()
        selected_page = render_navigation()

        st.divider()
        render_services_status(services)

        if services.get("postgres", False):
            st.divider()
            render_quick_overview()

        st.divider()
        render_refresh_button()

    return selected_page