"""Page de consultation des données du dashboard CheckIt.AI.

Cette page permet de :

- consulter les principaux volumes PostgreSQL ;
- analyser la couverture des images, labels et features ;
- observer la répartition des sources, langues et labels ;
- suivre la qualité et la complétude des articles ;
- rechercher et consulter les articles stockés ;
- afficher le détail d'un article sélectionné.

Toutes les données sont récupérées en lecture seule.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from dashboard.components.dashboard_layout import (
    apply_dashboard_layout,
    render_information_rows,
    render_layout_section_header,
    render_layout_selection_help,
    render_page_header,
    render_result_summary
)
from dashboard.components.dashboard_kpi import (
    clear_data_kpi_cache,
    is_valid_image_row,
    render_data_kpi_section
)
from dashboard.components.dashboard_ui_utils import (
    format_boolean,
    format_datetime,
    format_number,
    format_percentage,
    format_status,
    get_distinct_values,
    render_metric_cards,
    render_refresh_section,
    rows_to_dataframe
)
from dashboard.services.dashboard_postgres_service import (
    count_articles,
    get_article_details,
    get_articles,
    get_daily_article_counts,
    get_data_completeness,
    get_data_completeness_by_source,
    get_data_completeness_by_source_type,
    get_feature_distribution,
    get_image_completeness,
    get_image_quality_summary,
    get_label_distribution,
    get_language_distribution,
    get_metadata_completeness,
    get_quality_summary,
    get_source_type_distribution,
    get_sources_summary
)
from src.logger import get_logger

logger = get_logger(__name__)


# Configuration

DEFAULT_ARTICLE_LIMIT = 50
MAX_ARTICLE_LIMIT = 200
DEFAULT_HISTORY_DAYS = 30

ARTICLE_SORT_LABELS = {
    "extracted_at": "Date d'extraction",
    "published_at": "Date de publication",
    "created_at": "Date de création",
    "updated_at": "Date de mise à jour",
    "title": "Titre",
    "language": "Langue",
    "data_quality_status": "Statut qualité"
}

SORT_DIRECTION_LABELS = {
    "DESC": "Décroissant",
    "ASC": "Croissant"
}

COMPLETENESS_FIELDS = [
    (
        "Contenu",
        "with_content",
        "with_content_rate"
    ),
    (
        "Date de publication",
        "with_publication_date",
        "with_publication_date_rate"
    ),
    (
        "Auteur",
        "with_author",
        "with_author_rate"
    ),
    (
        "URL",
        "with_url",
        "with_url_rate"
    ),
    (
        "Langue",
        "with_language",
        "with_language_rate"
    ),
    (
        "Image",
        "with_image",
        "with_image_rate"
    ),
    (
        "Label",
        "with_label",
        "with_label_rate"
    ),
    (
        "Features",
        "with_feature",
        "with_feature_rate"
    )
]

RATE_COLUMN_LABELS = {
    "content_rate": "Contenu",
    "publication_date_rate": "Publication",
    "author_rate": "Auteur",
    "url_rate": "URL",
    "language_rate": "Langue",
    "image_rate": "Images",
    "label_rate": "Labels",
    "feature_rate": "Features"
}


# Cache

@st.cache_data(ttl=60, show_spinner=False)
def load_sources_summary() -> list[dict[str, Any]]:
    """Charge les statistiques par source."""

    return get_sources_summary()


@st.cache_data(ttl=60, show_spinner=False)
def load_source_type_distribution() -> list[dict[str, Any]]:
    """Charge la répartition des articles par type de source."""

    return get_source_type_distribution()


@st.cache_data(ttl=60, show_spinner=False)
def load_language_distribution() -> list[dict[str, Any]]:
    """Charge la répartition des articles par langue."""

    return get_language_distribution(limit=30)


@st.cache_data(ttl=60, show_spinner=False)
def load_label_distribution() -> list[dict[str, Any]]:
    """Charge la répartition des labels."""

    return get_label_distribution()


@st.cache_data(ttl=60, show_spinner=False)
def load_quality_summary() -> list[dict[str, Any]]:
    """Charge les statistiques de qualité des articles."""

    return get_quality_summary()


@st.cache_data(ttl=60, show_spinner=False)
def load_image_quality_summary() -> list[dict[str, Any]]:
    """Charge les statistiques de qualité des images."""

    return get_image_quality_summary()


@st.cache_data(ttl=60, show_spinner=False)
def load_feature_distribution() -> list[dict[str, Any]]:
    """Charge la répartition des features."""

    return get_feature_distribution()


@st.cache_data(ttl=60, show_spinner=False)
def load_data_completeness() -> dict[str, Any]:
    """Charge les indicateurs de complétude globale."""

    return get_data_completeness()


@st.cache_data(ttl=60, show_spinner=False)
def load_data_completeness_by_source() -> list[dict[str, Any]]:
    """Charge la complétude détaillée par source."""

    return get_data_completeness_by_source()


@st.cache_data(ttl=60, show_spinner=False)
def load_data_completeness_by_source_type() -> list[dict[str, Any]]:
    """Charge la complétude agrégée par type de source."""

    return get_data_completeness_by_source_type()


@st.cache_data(ttl=60, show_spinner=False)
def load_image_completeness() -> dict[str, Any]:
    """Charge la complétude technique des images."""

    return get_image_completeness()


@st.cache_data(ttl=60, show_spinner=False)
def load_metadata_completeness() -> dict[str, Any]:
    """Charge la complétude des métadonnées éditoriales."""

    return get_metadata_completeness()


@st.cache_data(ttl=60, show_spinner=False)
def load_daily_article_counts(
    days: int
) -> list[dict[str, Any]]:
    """Charge le nombre d'articles extraits par jour."""

    return get_daily_article_counts(days=days)


@st.cache_data(ttl=30, show_spinner=False)
def load_articles(
    *,
    limit: int,
    offset: int,
    source_key: str | None,
    language: str | None,
    label: str | None,
    quality_status: str | None,
    search: str | None,
    sort_by: str,
    sort_direction: str
) -> list[dict[str, Any]]:
    """Charge une page d'articles filtrés."""

    return get_articles(
        limit=limit,
        offset=offset,
        source_key=source_key,
        language=language,
        label=label,
        quality_status=quality_status,
        search=search,
        sort_by=sort_by,
        sort_direction=sort_direction
    )


@st.cache_data(ttl=30, show_spinner=False)
def load_article_count(
    *,
    source_key: str | None,
    language: str | None,
    quality_status: str | None
) -> int:
    """Compte les articles correspondant aux filtres principaux."""

    return count_articles(
        source_key=source_key,
        language=language,
        quality_status=quality_status
    )


@st.cache_data(ttl=30, show_spinner=False)
def load_article_details(
    article_id: str
) -> dict[str, Any] | None:
    """Charge le détail complet d'un article."""

    return get_article_details(article_id)


# En-tête

def render_header() -> None:
    """Affiche l'en-tête de la page Données."""

    render_page_header(
        eyebrow="Observatoire des données",
        title="🗄️ Données CheckIt.AI",
        description=(
            "Exploration des articles, images, labels, features et sources "
            "stockés dans PostgreSQL, avec suivi de leur qualité et de leur "
            "complétude."
        ),
        badges=[
            "Lecture seule",
            "PostgreSQL",
            "Qualité des données"
        ]
    )


# Sources

def render_sources_section() -> None:
    """Affiche les statistiques liées aux sources."""

    render_layout_section_header(
        "🌐",
        "Sources",
        "Volumes collectés et répartition par famille de source."
    )

    try:
        sources = load_sources_summary()
        source_types = load_source_type_distribution()
    except Exception as error:
        logger.warning(
            "Impossible de charger les statistiques des sources : %s",
            error
        )

        st.error(
            "Les statistiques des sources ne sont pas disponibles."
        )
        return

    source_column, type_column = st.columns([2, 1])

    with source_column:
        with st.container(border=True):
            st.subheader("Volumes par source")
            render_sources_table(sources)

    with type_column:
        with st.container(border=True):
            st.subheader("Types de source")
            render_source_type_chart(source_types)


def render_sources_table(
    sources: list[dict[str, Any]]
) -> None:
    """Affiche le détail des sources enregistrées."""

    dataframe = rows_to_dataframe(sources)

    if dataframe.empty:
        st.info("Aucune source n'est enregistrée.")
        return

    rename_columns = {
        "source_key": "Identifiant",
        "display_name": "Source",
        "source_type": "Type",
        "default_language": "Langue",
        "is_active": "Active",
        "article_count": "Articles",
        "image_count": "Images",
        "label_count": "Labels",
        "latest_extraction": "Dernière extraction"
    }

    visible_columns = [
        column
        for column in rename_columns
        if column in dataframe.columns
    ]

    dataframe = dataframe[visible_columns].rename(
        columns=rename_columns
    )

    if "Active" in dataframe.columns:
        dataframe["Active"] = dataframe["Active"].map(
            format_boolean
        )

    st.dataframe(
        dataframe,
        width="stretch",
        hide_index=True
    )


def render_source_type_chart(
    rows: list[dict[str, Any]]
) -> None:
    """Affiche la répartition par type de source."""

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        st.info("Aucune donnée disponible.")
        return

    required_columns = {
        "source_type",
        "article_count"
    }

    if not required_columns.issubset(dataframe.columns):
        st.info(
            "La répartition des sources est incomplète."
        )
        return

    chart_data = dataframe.set_index(
        "source_type"
    )[["article_count"]]

    st.bar_chart(
        chart_data,
        width="stretch"
    )


# Répartitions

def render_distributions_section() -> None:
    """Affiche les principales répartitions métier."""

    render_layout_section_header(
        "🧭",
        "Répartitions",
        "Lecture des données selon leur langue, label et statut qualité."
    )

    language_tab, label_tab, quality_tab, image_tab = st.tabs([
        "🌍 Langues",
        "🏷️ Labels",
        "✅ Articles",
        "🖼️ Images"
    ])

    with language_tab:
        render_language_distribution()

    with label_tab:
        render_label_distribution()

    with quality_tab:
        render_quality_distribution()

    with image_tab:
        render_image_distribution()


def render_language_distribution() -> None:
    """Affiche la répartition des articles par langue."""

    try:
        rows = load_language_distribution()
    except Exception as error:
        st.error(
            "La répartition des langues n'est pas disponible."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        st.info("Aucune langue n'est renseignée.")
        return

    chart_column, table_column = st.columns([2, 1])

    with chart_column:
        with st.container(border=True):
            chart_data = dataframe.set_index(
                "language"
            )[["article_count"]]

            st.bar_chart(
                chart_data,
                width="stretch"
            )

    with table_column:
        with st.container(border=True):
            st.dataframe(
                dataframe.rename(columns={
                    "language": "Langue",
                    "article_count": "Articles"
                }),
                width="stretch",
                hide_index=True
            )


def render_label_distribution() -> None:
    """Affiche la répartition des labels actifs."""

    try:
        rows = load_label_distribution()
    except Exception as error:
        st.error(
            "La répartition des labels n'est pas disponible."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        st.info("Aucun label actif n'est enregistré.")
        return

    chart_column, table_column = st.columns([2, 1])

    with chart_column:
        with st.container(border=True):
            chart_data = dataframe.groupby(
                "label",
                as_index=True
            )["label_count"].sum().to_frame()

            st.bar_chart(
                chart_data,
                width="stretch"
            )

    with table_column:
        with st.container(border=True):
            st.dataframe(
                dataframe.rename(columns={
                    "label": "Label",
                    "label_type": "Type",
                    "label_count": "Nombre"
                }),
                width="stretch",
                hide_index=True
            )


def render_quality_distribution() -> None:
    """Affiche les statuts qualité des articles."""

    try:
        rows = load_quality_summary()
    except Exception as error:
        st.error(
            "Les statistiques de qualité ne sont pas disponibles."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        st.info("Aucun statut qualité n'est renseigné.")
        return

    dataframe["Statut"] = dataframe[
        "data_quality_status"
    ].map(format_status)

    with st.container(border=True):
        st.dataframe(
            dataframe[[
                "Statut",
                "article_count"
            ]].rename(columns={
                "article_count": "Articles"
            }),
            width="stretch",
            hide_index=True
        )


def render_image_distribution() -> None:
    """Affiche les statuts de validation des images."""

    try:
        rows = load_image_quality_summary()
    except Exception as error:
        st.error(
            "Les statistiques des images ne sont pas disponibles."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        st.info("Aucune image n'est enregistrée.")
        return

    dataframe["Valide"] = dataframe["is_valid"].map(
        lambda value: format_boolean(
            is_valid_image_row({"is_valid": value})
        )
    )

    dataframe["Statut"] = dataframe[
        "validation_status"
    ].map(format_status)

    with st.container(border=True):
        st.dataframe(
            dataframe[[
                "Statut",
                "Valide",
                "image_count"
            ]].rename(columns={
                "image_count": "Images"
            }),
            width="stretch",
            hide_index=True
        )


# Complétude

def build_completeness_dataframe(
    completeness: dict[str, Any]
) -> pd.DataFrame:
    """Construit le tableau de complétude globale."""

    rows = []

    for label, count_field, rate_field in COMPLETENESS_FIELDS:
        rows.append({
            "Champ": label,
            "Articles renseignés": int(
                completeness.get(count_field) or 0
            ),
            "Taux de complétude": float(
                completeness.get(rate_field) or 0
            )
        })

    return pd.DataFrame(rows)


def prepare_grouped_completeness_dataframe(
    rows: list[dict[str, Any]],
    group_columns: dict[str, str]
) -> pd.DataFrame:
    """Prépare un tableau de complétude par groupe."""

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        return dataframe

    rename_columns = {
        **group_columns,
        "article_count": "Articles",
        **RATE_COLUMN_LABELS
    }

    visible_columns = [
        column
        for column in rename_columns
        if column in dataframe.columns
    ]

    dataframe = dataframe[visible_columns].rename(
        columns=rename_columns
    )

    for column in RATE_COLUMN_LABELS.values():
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].map(
                format_percentage
            )

    if "Articles" in dataframe.columns:
        dataframe["Articles"] = dataframe["Articles"].map(
            format_number
        )

    return dataframe


def render_global_completeness(
    completeness: dict[str, Any]
) -> None:
    """Affiche la complétude globale des articles."""

    dataframe = build_completeness_dataframe(completeness)
    chart_column, table_column = st.columns([2, 1])

    with chart_column:
        with st.container(border=True):
            st.markdown("#### Vue synthétique")

            chart_data = dataframe.set_index(
                "Champ"
            )[["Taux de complétude"]]

            st.bar_chart(
                chart_data,
                width="stretch"
            )

    with table_column:
        with st.container(border=True):
            st.markdown("#### Détail global")

            display_dataframe = dataframe.copy()

            display_dataframe["Articles renseignés"] = (
                display_dataframe["Articles renseignés"].map(
                    format_number
                )
            )

            display_dataframe["Taux de complétude"] = (
                display_dataframe["Taux de complétude"].map(
                    format_percentage
                )
            )

            st.dataframe(
                display_dataframe,
                width="stretch",
                hide_index=True
            )


def render_completeness_by_source_type() -> None:
    """Affiche la complétude par famille de source."""

    try:
        rows = load_data_completeness_by_source_type()
    except Exception as error:
        st.error(
            "La complétude par type de source n'est pas disponible."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    dataframe = prepare_grouped_completeness_dataframe(
        rows,
        {"source_type": "Type de source"}
    )

    if dataframe.empty:
        st.info(
            "Aucune statistique par type de source n'est disponible."
        )
        return

    with st.container(border=True):
        st.markdown("#### Lecture métier par famille")

        st.caption(
            "Cette vue distingue les datasets, APIs, flux RSS, réseaux "
            "sociaux et scrapers afin d'éviter les comparaisons trompeuses."
        )

        st.dataframe(
            dataframe,
            width="stretch",
            hide_index=True
        )


def render_completeness_by_source() -> None:
    """Affiche la complétude détaillée de chaque source."""

    try:
        rows = load_data_completeness_by_source()
    except Exception as error:
        st.error(
            "La complétude par source n'est pas disponible."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    dataframe = prepare_grouped_completeness_dataframe(
        rows,
        {
            "source_key": "Identifiant",
            "display_name": "Source",
            "source_type": "Type"
        }
    )

    if dataframe.empty:
        st.info(
            "Aucune statistique de complétude par source "
            "n'est disponible."
        )
        return

    with st.container(border=True):
        st.markdown("#### Diagnostic par extracteur")

        st.caption(
            "Les faibles taux deviennent actionnables lorsqu'ils sont "
            "reliés à une source précise."
        )

        st.dataframe(
            dataframe,
            width="stretch",
            hide_index=True,
            height=460
        )


def render_specialized_completeness(
    completeness: dict[str, Any],
    fields: list[tuple[str, str, str]],
    title: str,
    empty_message: str
) -> None:
    """Affiche un tableau spécialisé de complétude."""

    if not completeness:
        st.info(empty_message)
        return

    rows = [
        {
            "Champ": label,
            "Valeurs renseignées": int(
                completeness.get(count_field) or 0
            ),
            "Taux de complétude": float(
                completeness.get(rate_field) or 0
            )
        }
        for label, count_field, rate_field in fields
    ]

    dataframe = pd.DataFrame(rows)

    dataframe["Valeurs renseignées"] = (
        dataframe["Valeurs renseignées"].map(
            format_number
        )
    )

    dataframe["Taux de complétude"] = (
        dataframe["Taux de complétude"].map(
            format_percentage
        )
    )

    with st.container(border=True):
        st.markdown(f"#### {title}")

        st.dataframe(
            dataframe,
            width="stretch",
            hide_index=True
        )


def render_image_completeness() -> None:
    """Affiche la complétude technique des images."""

    try:
        completeness = load_image_completeness()
    except Exception as error:
        st.error(
            "La complétude technique des images n'est pas disponible."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    fields = [
        ("URL distante", "with_remote_url", "with_remote_url_rate"),
        ("Chemin local", "with_local_path", "with_local_path_rate"),
        ("Nom de fichier", "with_file_name", "with_file_name_rate"),
        ("Extension", "with_file_extension", "with_file_extension_rate"),
        ("Format réel", "with_file_format", "with_file_format_rate"),
        ("Type MIME", "with_mime_type", "with_mime_type_rate"),
        ("Largeur", "with_width", "with_width_rate"),
        ("Hauteur", "with_height", "with_height_rate"),
        ("Taille", "with_size_bytes", "with_size_bytes_rate"),
        ("Hash fichier", "with_file_hash", "with_file_hash_rate"),
        (
            "Hash perceptuel",
            "with_perceptual_hash",
            "with_perceptual_hash_rate"
        ),
        (
            "Durée téléchargement",
            "with_download_duration",
            "with_download_duration_rate"
        ),
        ("Score de flou", "with_blur_score", "with_blur_score_rate"),
        (
            "Luminosité",
            "with_brightness_score",
            "with_brightness_score_rate"
        ),
        ("Entropie", "with_entropy_score", "with_entropy_score_rate")
    ]

    render_specialized_completeness(
        completeness,
        fields,
        "Métadonnées techniques des images",
        "Aucune statistique de complétude des images n'est disponible."
    )


def render_metadata_completeness() -> None:
    """Affiche la complétude des métadonnées éditoriales."""

    try:
        completeness = load_metadata_completeness()
    except Exception as error:
        st.error(
            "La complétude des métadonnées n'est pas disponible."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    fields = [
        ("Source", "with_source", "with_source_rate"),
        ("Titre", "with_title", "with_title_rate"),
        ("Contenu", "with_content", "with_content_rate"),
        ("Auteur", "with_author", "with_author_rate"),
        (
            "Date de publication",
            "with_publication_date",
            "with_publication_date_rate"
        ),
        ("URL", "with_url", "with_url_rate"),
        ("Langue", "with_language", "with_language_rate"),
        ("Catégorie", "with_category", "with_category_rate"),
        ("Rôle", "with_role", "with_role_rate"),
        (
            "Statut qualité",
            "with_quality_status",
            "with_quality_status_rate"
        )
    ]

    render_specialized_completeness(
        completeness,
        fields,
        "Métadonnées éditoriales",
        "Aucune statistique de complétude des métadonnées "
        "n'est disponible."
    )


def render_completeness_section() -> None:
    """Affiche les différents niveaux de complétude."""

    render_layout_section_header(
        "🧩",
        "Complétude des données",
        "Analyse globale, par famille, par source et par domaine technique."
    )

    try:
        completeness = load_data_completeness()
    except Exception as error:
        logger.warning(
            "Impossible de charger la complétude globale : %s",
            error
        )

        st.error(
            "Les indicateurs de complétude ne sont pas disponibles."
        )
        return

    if not completeness:
        st.info("Aucune donnée de complétude n'est disponible.")
        return

    global_tab, type_tab, source_tab, image_tab, metadata_tab = st.tabs([
        "🌐 Globale",
        "🗂️ Par type",
        "🎯 Par source",
        "🖼️ Images",
        "📝 Métadonnées"
    ])

    with global_tab:
        render_global_completeness(completeness)

    with type_tab:
        render_completeness_by_source_type()

    with source_tab:
        render_completeness_by_source()

    with image_tab:
        render_image_completeness()

    with metadata_tab:
        render_metadata_completeness()


# Historique

def render_history_section() -> None:
    """Affiche l'évolution du nombre d'articles extraits."""

    render_layout_section_header(
        "📈",
        "Historique des extractions",
        "Évolution quotidienne du volume d'articles collectés."
    )

    with st.container(border=True):
        days = st.slider(
            "Période observée",
            min_value=7,
            max_value=365,
            value=DEFAULT_HISTORY_DAYS,
            step=1,
            format="%d jours",
            key="data_history_days"
        )

    try:
        rows = load_daily_article_counts(days)
    except Exception as error:
        st.error(
            "L'historique des extractions n'est pas disponible."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        st.info(
            "Aucun article n'a été extrait sur cette période."
        )
        return

    dataframe["extraction_date"] = pd.to_datetime(
        dataframe["extraction_date"]
    )

    chart_data = dataframe.set_index(
        "extraction_date"
    )[["article_count"]]

    with st.container(border=True):
        st.line_chart(
            chart_data,
            width="stretch"
        )

    total_articles = int(
        dataframe["article_count"].sum()
    )

    average_articles = float(
        dataframe["article_count"].mean()
    )

    render_metric_cards(
        [
            (
                "Articles sur la période",
                format_number(total_articles)
            ),
            (
                "Moyenne par jour actif",
                f"{average_articles:.1f}"
            )
        ],
        columns_count=2
    )


# Features

def render_features_section() -> None:
    """Affiche la répartition des features générées."""

    render_layout_section_header(
        "🧮",
        "Features",
        "Caractéristiques techniques produites pour les articles."
    )

    try:
        rows = load_feature_distribution()
    except Exception as error:
        st.error(
            "La répartition des features n'est pas disponible."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        st.info("Aucune feature n'est enregistrée.")
        return

    rename_columns = {
        "feature_group": "Groupe",
        "feature_name": "Feature",
        "feature_type": "Type",
        "feature_count": "Nombre"
    }

    visible_columns = [
        column
        for column in rename_columns
        if column in dataframe.columns
    ]

    with st.container(border=True):
        st.dataframe(
            dataframe[visible_columns].rename(
                columns=rename_columns
            ),
            width="stretch",
            hide_index=True
        )


# Explorateur d'articles

def render_articles_section() -> None:
    """Affiche les filtres et la liste des articles."""

    render_layout_section_header(
        "📰",
        "Explorateur d'articles",
        "Recherche multicritère et consultation détaillée du corpus."
    )

    try:
        sources = load_sources_summary()
        languages = load_language_distribution()
        labels = load_label_distribution()
        qualities = load_quality_summary()
    except Exception as error:
        st.error(
            "Les filtres de consultation ne sont pas disponibles."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    filters = render_article_filters(
        sources,
        languages,
        labels,
        qualities
    )

    render_article_results(filters)


def render_article_filters(
    sources: list[dict[str, Any]],
    languages: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    qualities: list[dict[str, Any]]
) -> dict[str, Any]:
    """Affiche les filtres de recherche des articles."""

    source_options = get_distinct_values(
        sources,
        "source_key"
    )

    language_options = get_distinct_values(
        languages,
        "language"
    )

    label_options = get_distinct_values(
        labels,
        "label"
    )

    quality_options = get_distinct_values(
        qualities,
        "data_quality_status"
    )

    with st.container(border=True):
        with st.form(
            "article_filters_form",
            clear_on_submit=False
        ):
            search = st.text_input(
                "Recherche",
                placeholder="Titre, contenu ou auteur",
                key="article_search"
            )

            first_row = st.columns(4)

            with first_row[0]:
                source_key = st.selectbox(
                    "Source",
                    options=["Toutes", *source_options],
                    key="article_source"
                )

            with first_row[1]:
                language = st.selectbox(
                    "Langue",
                    options=["Toutes", *language_options],
                    key="article_language"
                )

            with first_row[2]:
                label = st.selectbox(
                    "Label",
                    options=["Tous", *label_options],
                    key="article_label"
                )

            with first_row[3]:
                quality_status = st.selectbox(
                    "Qualité",
                    options=["Toutes", *quality_options],
                    key="article_quality"
                )

            second_row = st.columns(4)

            with second_row[0]:
                sort_by = st.selectbox(
                    "Trier par",
                    options=list(ARTICLE_SORT_LABELS),
                    format_func=lambda value: (
                        ARTICLE_SORT_LABELS[value]
                    ),
                    key="article_sort_by"
                )

            with second_row[1]:
                sort_direction = st.selectbox(
                    "Ordre",
                    options=list(SORT_DIRECTION_LABELS),
                    format_func=lambda value: (
                        SORT_DIRECTION_LABELS[value]
                    ),
                    key="article_sort_direction"
                )

            with second_row[2]:
                limit = st.selectbox(
                    "Articles par page",
                    options=[
                        25,
                        DEFAULT_ARTICLE_LIMIT,
                        100,
                        MAX_ARTICLE_LIMIT
                    ],
                    index=1,
                    key="article_limit"
                )

            with second_row[3]:
                page = st.number_input(
                    "Page",
                    min_value=1,
                    value=1,
                    step=1,
                    key="article_page"
                )

            submitted = st.form_submit_button(
                "🔍 Rechercher",
                width="stretch",
                type="primary"
            )

    if submitted:
        load_articles.clear()
        load_article_count.clear()

    return {
        "search": search.strip() or None,
        "source_key": (
            None
            if source_key == "Toutes"
            else source_key
        ),
        "language": (
            None
            if language == "Toutes"
            else language
        ),
        "label": (
            None
            if label == "Tous"
            else label
        ),
        "quality_status": (
            None
            if quality_status == "Toutes"
            else quality_status
        ),
        "sort_by": sort_by,
        "sort_direction": sort_direction,
        "limit": int(limit),
        "page": int(page)
    }


def render_article_results(
    filters: dict[str, Any]
) -> None:
    """Affiche les résultats de la recherche."""

    offset = (
        filters["page"] - 1
    ) * filters["limit"]

    try:
        articles = load_articles(
            limit=filters["limit"],
            offset=offset,
            source_key=filters["source_key"],
            language=filters["language"],
            label=filters["label"],
            quality_status=filters["quality_status"],
            search=filters["search"],
            sort_by=filters["sort_by"],
            sort_direction=filters["sort_direction"]
        )

        total_articles = load_article_count(
            source_key=filters["source_key"],
            language=filters["language"],
            quality_status=filters["quality_status"]
        )
    except Exception as error:
        logger.warning(
            "Impossible de charger les articles : %s",
            error
        )

        st.error(
            "Les articles n'ont pas pu être chargés."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    if not articles:
        st.info(
            "Aucun article ne correspond aux filtres sélectionnés."
        )
        return

    page_count = max(
        1,
        (
            total_articles + filters["limit"] - 1
        ) // filters["limit"]
    )

    render_result_summary(
        f"{format_number(total_articles)} article(s) trouvé(s) · "
        f"page {filters['page']} sur {page_count}"
    )

    event = st.dataframe(
        prepare_articles_dataframe(articles),
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="articles_dataframe"
    )

    selected_rows = event.selection.rows

    if not selected_rows:
        render_layout_selection_help(
            "Sélectionne un article dans le tableau pour afficher "
            "son contenu, ses métadonnées et ses données associées."
        )
        return

    article_id = str(
        articles[selected_rows[0]]["id"]
    )

    render_article_details(article_id)


def prepare_articles_dataframe(
    articles: list[dict[str, Any]]
) -> pd.DataFrame:
    """Prépare les articles pour leur affichage."""

    dataframe = rows_to_dataframe(articles)

    rename_columns = {
        "source_name": "Source",
        "title": "Titre",
        "author": "Auteur",
        "language": "Langue",
        "category": "Catégorie",
        "dataset_role": "Rôle",
        "data_quality_status": "Qualité",
        "published_at": "Publication",
        "extracted_at": "Extraction",
        "has_image": "Image",
        "has_label": "Label"
    }

    visible_columns = [
        column
        for column in rename_columns
        if column in dataframe.columns
    ]

    dataframe = dataframe[visible_columns].rename(
        columns=rename_columns
    )

    if "Image" in dataframe.columns:
        dataframe["Image"] = dataframe["Image"].map(
            format_boolean
        )

    if "Label" in dataframe.columns:
        dataframe["Label"] = dataframe["Label"].map(
            format_boolean
        )

    if "Qualité" in dataframe.columns:
        dataframe["Qualité"] = dataframe["Qualité"].map(
            format_status
        )

    return dataframe


# Détail d'un article

def render_article_details(
    article_id: str
) -> None:
    """Affiche le détail complet d'un article."""

    try:
        article = load_article_details(article_id)
    except Exception as error:
        st.error(
            "Le détail de l'article n'est pas disponible."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    if not article:
        st.info("L'article sélectionné n'existe plus.")
        return

    st.divider()

    render_layout_section_header(
        "🔍",
        "Détail de l'article",
        "Contenu, métadonnées et enrichissements "
        "de l'article sélectionné."
    )

    st.subheader(
        str(article.get("title") or "Article sans titre")
    )

    content_column, metadata_column = st.columns([2, 1])

    with content_column:
        render_article_content(article)

    with metadata_column:
        with st.container(border=True):
            render_article_metadata(article)

    render_article_related_data(article)


def render_article_content(
    article: dict[str, Any]
) -> None:
    """Affiche le texte et les liens de l'article."""

    content = (
        article.get("content")
        or article.get("text")
        or ""
    )

    with st.container(border=True):
        if content:
            st.markdown("#### Contenu")
            st.write(content)
        else:
            st.info(
                "Aucun contenu textuel n'est disponible."
            )

    article_url = (
        article.get("canonical_url")
        or article.get("url")
    )

    if article_url:
        st.link_button(
            "🔗 Ouvrir l'article source",
            str(article_url),
            width="stretch"
        )


def render_article_metadata(
    article: dict[str, Any]
) -> None:
    """Affiche les principales métadonnées de l'article."""

    st.markdown("#### Métadonnées")

    metadata = [
        (
            "Source",
            article.get("source_name")
            or article.get("source_key")
        ),
        (
            "Type",
            article.get("source_type")
        ),
        (
            "Auteur",
            article.get("author")
        ),
        (
            "Langue",
            article.get("language")
        ),
        (
            "Catégorie",
            article.get("category")
        ),
        (
            "Rôle",
            article.get("dataset_role")
        ),
        (
            "Qualité",
            format_status(
                article.get("data_quality_status")
            )
        ),
        (
            "Publication",
            format_datetime(
                article.get("published_at")
            )
        ),
        (
            "Extraction",
            format_datetime(
                article.get("extracted_at")
            )
        )
    ]

    render_information_rows(metadata)


def render_article_related_data(
    article: dict[str, Any]
) -> None:
    """Affiche les images, labels, features et prédictions."""

    images_tab, labels_tab, features_tab, predictions_tab = st.tabs([
        "🖼️ Images",
        "🏷️ Labels",
        "🧮 Features",
        "🤖 Prédictions"
    ])

    with images_tab:
        render_related_table(
            article.get("images", []),
            "Aucune image n'est associée à cet article."
        )

    with labels_tab:
        render_related_table(
            article.get("labels", []),
            "Aucun label n'est associé à cet article."
        )

    with features_tab:
        render_related_table(
            article.get("features", []),
            "Aucune feature n'est associée à cet article."
        )

    with predictions_tab:
        render_related_table(
            article.get("predictions", []),
            "Aucune prédiction n'est associée à cet article."
        )


def render_related_table(
    rows: list[dict[str, Any]],
    empty_message: str
) -> None:
    """Affiche une collection liée à l'article."""

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        st.info(empty_message)
        return

    with st.container(border=True):
        st.dataframe(
            dataframe,
            width="stretch",
            hide_index=True
        )


# Actualisation

def clear_data_cache() -> None:
    """Supprime les caches utilisés par la page Données."""

    clear_data_kpi_cache()
    load_sources_summary.clear()
    load_source_type_distribution.clear()
    load_language_distribution.clear()
    load_label_distribution.clear()
    load_quality_summary.clear()
    load_image_quality_summary.clear()
    load_feature_distribution.clear()
    load_data_completeness.clear()
    load_data_completeness_by_source.clear()
    load_data_completeness_by_source_type.clear()
    load_image_completeness.clear()
    load_metadata_completeness.clear()
    load_daily_article_counts.clear()
    load_articles.clear()
    load_article_count.clear()
    load_article_details.clear()


# Page

def render_data_page() -> None:
    """Affiche la page de consultation des données."""

    apply_dashboard_layout(accent="teal")
    render_header()

    overview_tab, kpi_tab, quality_tab, articles_tab = st.tabs([
        "📊 Vue générale",
        "🎯 KPI",
        "✅ Qualité et complétude",
        "📰 Explorateur"
    ])

    with overview_tab:
        render_history_section()
        st.divider()
        render_sources_section()
        st.divider()
        render_distributions_section()
        st.divider()
        render_features_section()

    with kpi_tab:
        render_data_kpi_section()

    with quality_tab:
        render_completeness_section()
        st.divider()
        render_quality_distribution()
        st.divider()
        render_image_distribution()

    with articles_tab:
        render_articles_section()

    render_refresh_section(
        button_label="🔄 Actualiser les données",
        button_key="refresh_data_page",
        cache_message=(
            "Les indicateurs sont conservés en cache "
            "entre 30 et 60 secondes."
        ),
        clear_cache=clear_data_cache
    )