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

from dashboard.services.dashboard_airflow_service import is_airflow_available
from dashboard.services.dahsboard_postgres_service import (
    get_database_overview,
    get_latest_pipeline_run,
    is_database_available
)
from src.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Navigation
# ============================================================================

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


# ============================================================================
# Cache
# ============================================================================

@st.cache_data(ttl=15, show_spinner=False)
def get_services_status() -> dict[str, bool]:
    """Retourne la disponibilité des services du projet."""

    return {
        "postgres": is_database_available(),
        "airflow": is_airflow_available()
    }


@st.cache_data(ttl=30, show_spinner=False)
def get_sidebar_metrics() -> dict[str, Any]:
    """Retourne les principaux indicateurs PostgreSQL."""

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

        return {
            "articles": 0,
            "images": 0,
            "labels": 0,
            "features": 0,
            "sources": 0,
            "latest_status": "unknown"
        }


# ============================================================================
# Style
# ============================================================================

def render_sidebar_style() -> None:
    """Applique le style visuel de la sidebar."""

    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                min-width: 19rem;
                background:
                    radial-gradient(
                        circle at top left,
                        rgba(67, 97, 238, 0.13),
                        transparent 28%
                    ),
                    var(--background-color);
            }

            [data-testid="stSidebarContent"] {
                padding-top: 1rem;
            }

            [data-testid="stSidebar"] hr {
                margin: 1rem 0;
                opacity: 0.15;
            }

            .checkit-sidebar-header {
                padding: 1rem;
                margin-bottom: 1rem;
                border: 1px solid rgba(128, 132, 149, 0.20);
                border-radius: 1rem;
                background: rgba(128, 132, 149, 0.06);
            }

            .checkit-sidebar-brand {
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }

            .checkit-sidebar-logo {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 2.7rem;
                height: 2.7rem;
                flex-shrink: 0;
                border-radius: 0.85rem;
                font-size: 1.35rem;
                background: linear-gradient(
                    145deg,
                    rgba(67, 97, 238, 0.28),
                    rgba(114, 9, 183, 0.20)
                );
            }

            .checkit-sidebar-title {
                font-size: 1.25rem;
                font-weight: 750;
                line-height: 1.15;
            }

            .checkit-sidebar-subtitle {
                margin-top: 0.2rem;
                color: #808495;
                font-size: 0.76rem;
                line-height: 1.3;
            }

            .checkit-section-title {
                margin: 0 0 0.55rem 0.15rem;
                color: #808495;
                font-size: 0.7rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .checkit-status-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.5rem;
                font-size: 0.84rem;
                font-weight: 600;
            }

            .checkit-status-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                padding: 0.24rem 0.48rem;
                border-radius: 999px;
                font-size: 0.66rem;
                font-weight: 700;
                white-space: nowrap;
            }

            .checkit-status-online {
                color: #31c76a;
                background: rgba(49, 199, 106, 0.13);
            }

            .checkit-status-offline {
                color: #ff5d5d;
                background: rgba(255, 93, 93, 0.13);
            }

            .checkit-status-dot {
                width: 0.4rem;
                height: 0.4rem;
                border-radius: 50%;
                background: currentColor;
            }

            div[data-testid="stRadio"] > label {
                display: none;
            }

            div[data-testid="stRadio"] [role="radiogroup"] {
                gap: 0.3rem;
            }

            div[data-testid="stRadio"] [role="radiogroup"] label {
                min-height: 2.65rem;
                padding: 0.5rem 0.7rem;
                border: 1px solid transparent;
                border-radius: 0.75rem;
                transition:
                    background 0.18s ease,
                    border-color 0.18s ease,
                    transform 0.18s ease;
            }

            div[data-testid="stRadio"] [role="radiogroup"] label:hover {
                border-color: rgba(128, 132, 149, 0.22);
                background: rgba(128, 132, 149, 0.08);
                transform: translateX(2px);
            }

            div[data-testid="stRadio"]
            [role="radiogroup"]
            label:has(input:checked) {
                border-color: rgba(67, 97, 238, 0.38);
                background: rgba(67, 97, 238, 0.14);
                font-weight: 650;
            }

            [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
                border-color: rgba(128, 132, 149, 0.18);
                border-radius: 0.85rem;
                background: rgba(128, 132, 149, 0.045);
            }

            [data-testid="stSidebar"] [data-testid="stMetric"] {
                padding: 0.1rem 0;
            }

            [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
                color: #9094a6;
                font-size: 0.72rem;
            }

            [data-testid="stSidebar"] [data-testid="stMetricValue"] {
                font-size: 1.05rem;
                font-weight: 750;
            }

            [data-testid="stSidebar"] div[data-testid="stButton"] button {
                min-height: 2.55rem;
                border-radius: 0.75rem;
                font-weight: 650;
            }

            .checkit-cache-note {
                margin: 0.5rem 0 0;
                color: #808495;
                font-size: 0.67rem;
                line-height: 1.35;
                text-align: center;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================================
# Formatage
# ============================================================================

def format_number(value: Any) -> str:
    """Formate un nombre avec des espaces entre les milliers."""

    try:
        return f"{int(value):,}".replace(",", " ")

    except (TypeError, ValueError):
        return "0"


def format_pipeline_status(status: Any) -> str:
    """Retourne le statut visuel du dernier pipeline."""

    normalized_status = str(status or "unknown").strip().lower()

    statuses = {
        "success": "🟢 Succès",
        "running": "🔵 En cours",
        "queued": "🟡 En attente",
        "failed": "🔴 Échec",
        "partial": "🟠 Succès partiel",
        "partial_success": "🟠 Succès partiel",
        "empty": "⚪ Aucune donnée",
        "disabled": "⚫ Désactivé",
        "unknown": "⚪ Inconnu"
    }

    return statuses.get(
        normalized_status,
        f"⚪ {normalized_status.replace('_', ' ').capitalize()}"
    )


def get_service_badge(is_available: bool) -> str:
    """Retourne le badge HTML d'un service."""

    if is_available:
        css_class = "checkit-status-online"
        label = "Disponible"
    else:
        css_class = "checkit-status-offline"
        label = "Indisponible"

    return (
        f'<span class="checkit-status-badge {css_class}">'
        '<span class="checkit-status-dot"></span>'
        f"{label}</span>"
    )


def render_section_title(title: str) -> None:
    """Affiche le titre discret d'une section."""

    st.markdown(
        f'<div class="checkit-section-title">{title}</div>',
        unsafe_allow_html=True
    )


# ============================================================================
# En-tête et navigation
# ============================================================================

def render_header() -> None:
    """Affiche l'identité visuelle du dashboard."""

    st.markdown(
        '<div class="checkit-sidebar-header">'
        '<div class="checkit-sidebar-brand">'
        '<div class="checkit-sidebar-logo">🔎</div>'
        '<div>'
        '<div class="checkit-sidebar-title">CheckIt.AI</div>'
        '<div class="checkit-sidebar-subtitle">'
        'Supervision du pipeline multimodal'
        '</div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


def render_navigation() -> str:
    """Affiche la navigation et retourne la page sélectionnée."""

    render_section_title("Navigation")

    return st.radio(
        "Navigation",
        options=PAGES,
        format_func=lambda page: f"{PAGE_ICONS[page]}  {page}",
        label_visibility="collapsed",
        key="dashboard_navigation"
    )


# ============================================================================
# Services
# ============================================================================

def render_service(
    name: str,
    icon: str,
    is_available: bool
) -> None:
    """Affiche l'état d'un service dans une carte."""

    badge = get_service_badge(is_available)

    with st.container(border=True):
        st.markdown(
            f'<div class="checkit-status-row">'
            f'<span>{icon} {name}</span>'
            f"{badge}"
            f"</div>",
            unsafe_allow_html=True
        )


def render_services_status(
    services: dict[str, bool]
) -> None:
    """Affiche l'état de PostgreSQL et Airflow."""

    render_section_title("État des services")

    render_service(
        name="PostgreSQL",
        icon="🐘",
        is_available=services["postgres"]
    )

    render_service(
        name="Airflow",
        icon="🌬️",
        is_available=services["airflow"]
    )


# ============================================================================
# Indicateurs
# ============================================================================

def render_pipeline_metric(status: Any) -> None:
    """Affiche le statut du dernier pipeline."""

    with st.container(border=True):
        st.metric(
            label="Dernier pipeline",
            value=format_pipeline_status(status)
        )


def render_database_metrics(metrics: dict[str, Any]) -> None:
    """Affiche les principaux volumes PostgreSQL."""

    first_column, second_column = st.columns(2)

    with first_column:
        with st.container(border=True):
            st.metric(
                label="📰 Articles",
                value=format_number(metrics["articles"])
            )

        with st.container(border=True):
            st.metric(
                label="🏷️ Labels",
                value=format_number(metrics["labels"])
            )

    with second_column:
        with st.container(border=True):
            st.metric(
                label="🖼️ Images",
                value=format_number(metrics["images"])
            )

        with st.container(border=True):
            st.metric(
                label="🧩 Features",
                value=format_number(metrics["features"])
            )

    with st.container(border=True):
        st.metric(
            label="🌐 Sources",
            value=format_number(metrics["sources"])
        )


def render_quick_overview() -> None:
    """Affiche les principaux indicateurs de la base."""

    metrics = get_sidebar_metrics()

    render_section_title("Vue rapide")
    render_pipeline_metric(metrics["latest_status"])
    render_database_metrics(metrics)


# ============================================================================
# Actualisation
# ============================================================================

def render_refresh_button() -> None:
    """Affiche le bouton d'actualisation."""

    if st.button(
        "🔄 Actualiser les données",
        width="stretch",
        key="refresh_dashboard"
    ):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        '<p class="checkit-cache-note">'
        'Les indicateurs sont mis en cache pendant quelques secondes.'
        '</p>',
        unsafe_allow_html=True
    )


# ============================================================================
# Sidebar complète
# ============================================================================

def render_sidebar() -> str:
    """Affiche la sidebar et retourne la page sélectionnée."""

    services = get_services_status()

    with st.sidebar:
        render_sidebar_style()
        render_header()

        selected_page = render_navigation()

        st.divider()
        render_services_status(services)

        if services["postgres"]:
            st.divider()
            render_quick_overview()

        st.divider()
        render_refresh_button()

    return selected_page