"""Utilitaires visuels communs du dashboard CheckIt.AI.

Ce module centralise les fonctions réutilisées par les pages Streamlit :

- formatage des nombres, pourcentages, dates et durées ;
- affichage uniforme des statuts ;
- conversion des données en DataFrame ;
- affichage des en-têtes de section ;
- affichage des cartes de métriques ;
- affichage des aides de sélection ;
- affichage du bouton commun d'actualisation.

Le module ne contient aucune logique métier liée à Airflow ou PostgreSQL.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from html import escape
from typing import Any

import pandas as pd
import streamlit as st


# Constantes

DAG_LABELS = {
    "checkit_master_pipeline": "Pipeline complet",
    "checkit_extract_dag": "Extraction",
    "checkit_transform_dag": "Transformation",
    "checkit_load_dag": "Chargement PostgreSQL",
    "checkit_quality_dag": "Contrôle qualité",
    "checkit_cleanup_dag": "Nettoyage",
    "checkit_database_setup": "Initialisation PostgreSQL",
    "test_checkit_postgres": "Test PostgreSQL"
}

STATUS_LABELS = {
    "success": "🟢 Succès",
    "healthy": "🟢 Opérationnel",
    "valid": "🟢 Valide",
    "accepted": "🟢 Accepté",
    "active": "🟢 Actif",
    "running": "🔵 En cours",
    "queued": "🟡 En attente",
    "scheduled": "🟡 Planifié",
    "pending": "🟡 En attente",
    "deferred": "🟣 Différé",
    "partial": "🟠 Partiel",
    "partial_success": "🟠 Succès partiel",
    "warning": "🟠 Attention",
    "up_for_retry": "🟠 Nouvelle tentative",
    "up_for_reschedule": "🟠 Replanification",
    "paused": "🟠 En pause",
    "invalid": "🔴 Invalide",
    "failed": "🔴 Échec",
    "rejected": "🔴 Rejeté",
    "upstream_failed": "🔴 Échec en amont",
    "unhealthy": "🔴 Indisponible",
    "canceled": "⚫ Annulé",
    "cancelled": "⚫ Annulé",
    "removed": "⚫ Supprimé",
    "skipped": "⚪ Ignoré",
    "none": "⚪ Sans état",
    "unknown": "⚪ Inconnu"
}


# Formatage

def format_number(
    value: Any,
    default: str = "0"
) -> str:
    """Formate un nombre entier avec des espaces entre les milliers."""

    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError, OverflowError):
        return default


def format_decimal(
    value: Any,
    decimals: int = 2,
    default: str = "0.00"
) -> str:
    """Formate une valeur décimale avec un nombre fixe de décimales."""

    try:
        safe_decimals = max(0, int(decimals))
        return f"{float(value):.{safe_decimals}f}"
    except (TypeError, ValueError, OverflowError):
        return default


def format_percentage(
    value: Any,
    decimals: int = 2,
    default: str = "0.00 %"
) -> str:
    """Formate une valeur sous la forme d'un pourcentage."""

    try:
        safe_decimals = max(0, int(decimals))
        return f"{float(value):.{safe_decimals}f} %"
    except (TypeError, ValueError, OverflowError):
        return default


def format_boolean(
    value: Any,
    true_label: str = "🟢 Oui",
    false_label: str = "⚪ Non"
) -> str:
    """Transforme une valeur booléenne en indicateur lisible."""

    return true_label if bool(value) else false_label


def format_status(
    status: Any,
    labels: Mapping[str, str] | None = None
) -> str:
    """Retourne un statut accompagné d'un indicateur visuel."""

    normalized_status = str(status or "unknown").strip().lower()

    available_labels = {
        **STATUS_LABELS,
        **dict(labels or {})
    }

    default_label = (
        f"⚪ {normalized_status.replace('_', ' ').capitalize()}"
    )

    return available_labels.get(normalized_status, default_label)


def format_dag_name(
    dag_id: str,
    *,
    include_id: bool = False
) -> str:
    """Retourne le nom lisible d'un DAG CheckIt.AI."""

    normalized_dag_id = str(dag_id or "").strip()

    if not normalized_dag_id:
        return "DAG inconnu"

    default_label = normalized_dag_id.replace("_", " ").capitalize()
    label = DAG_LABELS.get(normalized_dag_id, default_label)

    if include_id:
        return f"{label} · {normalized_dag_id}"

    return label


def format_datetime(
    value: Any,
    date_format: str = "%d/%m/%Y %H:%M:%S",
    default: str = "Non disponible"
) -> str:
    """Formate une date ou une valeur ISO pour l'affichage."""

    if value in {None, ""}:
        return default

    try:
        date = pd.to_datetime(value)

        if pd.isna(date):
            return default

        return date.strftime(date_format)
    except (TypeError, ValueError, OverflowError):
        return str(value)


def format_duration(
    value: Any,
    default: str = "Non disponible"
) -> str:
    """Transforme une durée en secondes en valeur lisible."""

    try:
        total_seconds = max(0, int(float(value)))
    except (TypeError, ValueError, OverflowError):
        return default

    days, remainder = divmod(total_seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)

    parts = []

    if days:
        parts.append(f"{days} j")

    if hours or days:
        parts.append(f"{hours:02d} h")

    if minutes or hours or days:
        parts.append(f"{minutes:02d} min")

    if parts:
        parts.append(f"{seconds:02d} s")
    else:
        parts.append(f"{seconds} s")

    return " ".join(parts)


# Données

def rows_to_dataframe(
    rows: Sequence[Mapping[str, Any]] | None
) -> pd.DataFrame:
    """Convertit une collection de lignes en DataFrame."""

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame([dict(row) for row in rows])


def get_distinct_values(
    rows: Sequence[Mapping[str, Any]] | None,
    field: str
) -> list[str]:
    """Retourne les valeurs distinctes et non vides d'un champ."""

    if not rows or not field:
        return []

    values = {
        str(row[field]).strip()
        for row in rows
        if row.get(field) not in {None, ""}
        and str(row[field]).strip()
    }

    return sorted(values)


# Composants visuels

def render_section_header(
    icon: str,
    title: str,
    description: str
) -> None:
    """Affiche l'en-tête visuel commun d'une section."""

    safe_icon = escape(str(icon or ""))
    safe_title = escape(str(title or ""))
    safe_description = escape(str(description or ""))

    st.markdown(
        '<div class="checkit-section-header">'
        f'<div class="checkit-section-icon">{safe_icon}</div>'
        '<div>'
        f'<div class="checkit-section-title">{safe_title}</div>'
        '<div class="checkit-section-description">'
        f"{safe_description}"
        "</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )


def render_metric_cards(
    metrics: Sequence[tuple[str, Any]],
    columns_count: int = 4
) -> None:
    """Affiche plusieurs indicateurs dans des cartes Streamlit."""

    if not metrics:
        return

    safe_columns_count = max(
        1,
        min(len(metrics), int(columns_count))
    )

    columns = st.columns(safe_columns_count)

    for index, (label, value) in enumerate(metrics):
        column = columns[index % safe_columns_count]

        with column:
            with st.container(border=True):
                st.metric(
                    label=str(label),
                    value=value
                )


def render_selection_help(message: str) -> None:
    """Affiche une aide discrète sous un tableau sélectionnable."""

    safe_message = escape(str(message or ""))

    st.markdown(
        '<div class="checkit-selection-help">'
        f"{safe_message}"
        "</div>",
        unsafe_allow_html=True
    )


def render_information_block(
    values: Sequence[tuple[str, Any]],
    *,
    use_code: bool = True,
    empty_message: str = "Aucune information disponible."
) -> None:
    """Affiche plusieurs informations dans une fiche homogène."""

    rows = []

    for label, value in values:
        if value in {None, ""}:
            continue

        safe_label = escape(str(label))
        safe_value = escape(str(value))

        if use_code:
            displayed_value = f"<code>{safe_value}</code>"
        else:
            displayed_value = safe_value

        rows.append(
            '<div class="checkit-info-row">'
            f'<div class="checkit-info-label">{safe_label}</div>'
            '<div class="checkit-info-value">'
            f"{displayed_value}"
            "</div>"
            "</div>"
        )

    if not rows:
        st.caption(empty_message)
        return

    st.markdown(
        '<div class="checkit-info-card">'
        f"{''.join(rows)}"
        "</div>",
        unsafe_allow_html=True
    )


def render_refresh_section(
    *,
    button_label: str,
    button_key: str,
    cache_message: str,
    clear_cache: Callable[[], None]
) -> None:
    """Affiche le bouton commun d'actualisation d'une page."""

    st.divider()

    _, center_column, _ = st.columns([1, 2, 1])

    with center_column:
        refresh_requested = st.button(
            button_label,
            width="stretch",
            key=button_key
        )

        if refresh_requested:
            clear_cache()
            st.rerun()

    safe_cache_message = escape(str(cache_message or ""))

    st.markdown(
        '<div class="checkit-footer-note">'
        f"{safe_cache_message}"
        "</div>",
        unsafe_allow_html=True
    )


# Calcul des durées

def calculate_duration_seconds(
    start_value: Any,
    end_value: Any = None,
    *,
    running: bool = False
) -> float | None:
    """Calcule une durée en secondes à partir de deux dates."""

    if start_value in {None, ""}:
        return None

    try:
        start = pd.to_datetime(start_value)

        if pd.isna(start):
            return None

        if end_value not in {None, ""}:
            end = pd.to_datetime(end_value)
        elif running:
            end = pd.Timestamp(datetime.now(timezone.utc))
        else:
            return None

        if pd.isna(end):
            return None

        if start.tzinfo is None:
            start = start.tz_localize("UTC")

        if end.tzinfo is None:
            end = end.tz_localize("UTC")

        duration_seconds = float((end - start).total_seconds())

        return max(0.0, duration_seconds)
    except (TypeError, ValueError, OverflowError):
        return None