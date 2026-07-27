"""Composants KPI du dashboard CheckIt.AI.

Ce module centralise :

- les KPI de la page Pipeline ;
- les KPI de la page Données ;
- le chargement des données PostgreSQL nécessaires ;
- les calculs de taux et de volumes ;
- la préparation des graphiques Streamlit ;
- la gestion du cache associé aux indicateurs.

Les pages Pipeline et Données restent responsables de leur navigation.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd
import streamlit as st

from dashboard.components.dashboard_layout import (
    render_information_rows,
    render_layout_section_header,
    render_notice
)
from dashboard.components.dashboard_ui_utils import (
    format_boolean,
    format_datetime,
    format_duration,
    format_number,
    format_percentage,
    format_status,
    prepare_chart_dataframe,
    render_metric_cards,
    rows_to_dataframe
)
from dashboard.services.dashboard_postgres_service import (
    get_data_completeness,
    get_database_overview,
    get_image_quality_summary,
    get_latest_pipeline_run,
    get_latest_run_content,
    get_pipeline_runs,
    get_pipeline_summary,
    get_quality_summary,
    get_sources_summary
)
from src.logger import get_logger

logger = get_logger(__name__)


# Cache

@st.cache_data(ttl=30, show_spinner=False)
def load_kpi_database_overview() -> dict[str, Any]:
    """Charge les volumes et couvertures de la base."""

    return get_database_overview()


@st.cache_data(ttl=30, show_spinner=False)
def load_kpi_latest_pipeline_run() -> dict[str, Any] | None:
    """Charge la dernière exécution métier du pipeline."""

    return get_latest_pipeline_run()


@st.cache_data(ttl=30, show_spinner=False)
def load_kpi_latest_run_content() -> dict[str, Any]:
    """Charge le contenu du dernier lot traité."""

    return get_latest_run_content()


@st.cache_data(ttl=30, show_spinner=False)
def load_kpi_pipeline_summary() -> dict[str, Any]:
    """Charge la synthèse globale des exécutions métier."""

    return get_pipeline_summary()


@st.cache_data(ttl=30, show_spinner=False)
def load_kpi_pipeline_history(
    limit: int
) -> list[dict[str, Any]]:
    """Charge l'historique récent des exécutions métier."""

    return get_pipeline_runs(limit=limit)


@st.cache_data(ttl=60, show_spinner=False)
def load_kpi_data_completeness() -> dict[str, Any]:
    """Charge la complétude globale des articles."""

    return get_data_completeness()


@st.cache_data(ttl=60, show_spinner=False)
def load_kpi_quality_summary() -> list[dict[str, Any]]:
    """Charge les statuts qualité des articles."""

    return get_quality_summary()


@st.cache_data(ttl=60, show_spinner=False)
def load_kpi_image_quality_summary() -> list[dict[str, Any]]:
    """Charge les statuts qualité des images."""

    return get_image_quality_summary()


@st.cache_data(ttl=60, show_spinner=False)
def load_kpi_sources_summary() -> list[dict[str, Any]]:
    """Charge les statistiques des sources."""

    return get_sources_summary()


# Utilitaires

def safe_integer(value: Any) -> int:
    """Convertit une valeur en entier sans lever d'erreur."""

    try:
        return int(value or 0)
    except (TypeError, ValueError, OverflowError):
        return 0


def calculate_rate(
    numerator: int | float,
    denominator: int | float
) -> float:
    """Calcule un pourcentage sans division par zéro."""

    if not denominator:
        return 0.0

    return float(numerator) * 100 / float(denominator)


def get_count(
    rows: list[dict[str, Any]],
    field: str,
    *,
    predicate: Callable[[dict[str, Any]], bool] | None = None
) -> int:
    """Additionne un champ numérique dans une liste de résultats."""

    total = 0

    for row in rows:
        if predicate is not None and not predicate(row):
            continue

        total += safe_integer(row.get(field))

    return total


def is_positive_quality_status(value: Any) -> bool:
    """Indique si un statut représente une donnée exploitable."""

    return str(value or "").strip().lower() in {
        "accepted",
        "complete",
        "ready",
        "success",
        "valid",
        "validated"
    }


def is_valid_image_row(row: dict[str, Any]) -> bool:
    """Indique si une ligne représente des images valides."""

    value = row.get("is_valid")

    if isinstance(value, bool):
        return value

    return str(value or "").strip().lower() in {
        "1",
        "true",
        "valid",
        "validated",
        "yes"
    }


def get_missing_columns(
    dataframe: pd.DataFrame,
    required_columns: set[str]
) -> set[str]:
    """Retourne les colonnes attendues absentes du DataFrame."""

    return required_columns.difference(dataframe.columns)


def render_missing_columns_warning(
    section_name: str,
    missing_columns: set[str]
) -> None:
    """Affiche les colonnes absentes d'une section KPI."""

    missing = ", ".join(sorted(missing_columns))

    logger.warning(
        "Colonnes manquantes dans les KPI %s : %s",
        section_name,
        missing
    )

    st.warning(
        f"Les statistiques {section_name} sont incomplètes. "
        f"Colonnes absentes : {missing}."
    )


def render_kpi_error(
    message: str,
    error: Exception
) -> None:
    """Affiche une erreur KPI et son détail technique."""

    st.error(message)

    with st.expander("Détail technique"):
        st.code(f"{type(error).__name__}: {error}")


# KPI Pipeline

def render_pipeline_kpi_section() -> None:
    """Affiche une synthèse compacte du dernier pipeline."""

    render_layout_section_header(
        "🎯",
        "Synthèse du pipeline",
        (
            "Statut du dernier lot, volumes traités, qualité, "
            "stockage et temps d'exécution."
        )
    )

    try:
        latest_run = load_kpi_latest_pipeline_run()
        latest_content = load_kpi_latest_run_content() or {}
        overview = load_kpi_database_overview() or {}
        summary = load_kpi_pipeline_summary() or {}
    except Exception as error:
        logger.exception(
            "Impossible de charger les KPI du pipeline."
        )
        render_kpi_error(
            "Les KPI du pipeline ne sont pas disponibles.",
            error
        )
        return

    if not latest_run:
        st.info(
            "Aucune exécution du pipeline n'est enregistrée "
            "dans PostgreSQL."
        )
        return

    extracted_count = safe_integer(
        latest_run.get("extracted_count")
    )
    transformed_count = safe_integer(
        latest_run.get("transformed_count")
    )
    valid_count = safe_integer(
        latest_run.get("valid_count")
    )
    rejected_count = safe_integer(
        latest_run.get("rejected_count")
    )
    loaded_count = safe_integer(
        latest_run.get("loaded_count")
    )
    downloaded_images = safe_integer(
        latest_run.get("images_downloaded_count")
    )
    valid_images = safe_integer(
        latest_run.get("images_valid_count")
    )
    invalid_images = safe_integer(
        latest_run.get("images_invalid_count")
    )

    render_metric_cards(
        [
            (
                "Dernier statut",
                format_status(latest_run.get("status"))
            ),
            (
                "Articles chargés",
                format_number(loaded_count)
            ),
            (
                "Taux de validation",
                format_percentage(
                    calculate_rate(
                        valid_count,
                        valid_count + rejected_count
                    )
                )
            ),
            (
                "Durée totale",
                format_duration(
                    latest_run.get("duration_seconds")
                )
            )
        ],
        columns_count=4
    )

    article_tab, image_tab, storage_tab, performance_tab = st.tabs([
        "📰 Articles",
        "🖼️ Images",
        "🗄️ Stockage",
        "⏱️ Performance"
    ])

    with article_tab:
        render_pipeline_article_summary(
            extracted_count,
            transformed_count,
            valid_count,
            rejected_count,
            loaded_count
        )

    with image_tab:
        render_pipeline_image_summary(
            downloaded_images,
            valid_images,
            invalid_images
        )

    with storage_tab:
        render_pipeline_storage_summary(
            latest_content,
            overview
        )

    with performance_tab:
        render_pipeline_performance_summary(
            latest_run,
            overview,
            summary
        )

    with st.expander("Informations techniques du dernier lot"):
        render_information_rows([
            (
                "Pipeline",
                latest_run.get("pipeline_name", "inconnu")
            ),
            (
                "Version",
                latest_run.get("pipeline_version", "inconnue")
            ),
            (
                "DAG",
                latest_run.get("dag_id", "inconnu")
            ),
            (
                "Début",
                format_datetime(latest_run.get("started_at"))
            ),
            (
                "Fin",
                format_datetime(latest_run.get("finished_at"))
            )
        ])

        if latest_run.get("error_message"):
            render_notice(
                str(latest_run["error_message"]),
                notice_type="danger",
                title="Erreur enregistrée"
            )


def render_pipeline_article_summary(
    extracted_count: int,
    transformed_count: int,
    valid_count: int,
    rejected_count: int,
    loaded_count: int
) -> None:
    """Affiche le parcours des articles du dernier lot."""

    render_layout_section_header(
        "📰",
        "Parcours des articles",
        "Volumes observés à chaque étape du traitement."
    )

    render_metric_cards(
        [
            (
                "Extraits",
                format_number(extracted_count)
            ),
            (
                "Transformés",
                format_number(transformed_count)
            ),
            (
                "Valides",
                format_number(valid_count)
            ),
            (
                "Chargés",
                format_number(loaded_count)
            )
        ],
        columns_count=4
    )

    render_metric_cards(
        [
            (
                "Rejetés",
                format_number(rejected_count)
            ),
            (
                "Transformation",
                format_percentage(
                    calculate_rate(
                        transformed_count,
                        extracted_count
                    )
                )
            ),
            (
                "Validation",
                format_percentage(
                    calculate_rate(
                        valid_count,
                        valid_count + rejected_count
                    )
                )
            ),
            (
                "Chargement",
                format_percentage(
                    calculate_rate(
                        loaded_count,
                        transformed_count
                    )
                )
            )
        ],
        columns_count=4
    )


def render_pipeline_image_summary(
    downloaded_images: int,
    valid_images: int,
    invalid_images: int
) -> None:
    """Affiche les résultats du traitement des images."""

    render_layout_section_header(
        "🖼️",
        "Traitement des images",
        "Téléchargement et validation technique des fichiers."
    )

    controlled_images = valid_images + invalid_images

    render_metric_cards(
        [
            (
                "Téléchargées",
                format_number(downloaded_images)
            ),
            (
                "Contrôlées",
                format_number(controlled_images)
            ),
            (
                "Valides",
                format_number(valid_images)
            ),
            (
                "Invalides",
                format_number(invalid_images)
            )
        ],
        columns_count=4
    )

    render_metric_cards(
        [
            (
                "Taux valide",
                format_percentage(
                    calculate_rate(
                        valid_images,
                        controlled_images
                    )
                )
            ),
            (
                "Taux invalide",
                format_percentage(
                    calculate_rate(
                        invalid_images,
                        controlled_images
                    )
                )
            ),
            (
                "Contrôle effectué",
                format_percentage(
                    calculate_rate(
                        controlled_images,
                        downloaded_images
                    )
                )
            )
        ],
        columns_count=3
    )


def render_pipeline_storage_summary(
    latest_content: dict[str, Any],
    overview: dict[str, Any]
) -> None:
    """Compare le dernier lot aux volumes PostgreSQL."""

    render_layout_section_header(
        "🗄️",
        "Stockage PostgreSQL",
        "Contenu du dernier lot et volumes cumulés en base."
    )

    latest_column, database_column = st.columns(2)

    with latest_column:
        st.markdown("#### Dernier lot")

        render_metric_cards(
            [
                (
                    "Articles",
                    format_number(
                        latest_content.get("articles")
                    )
                ),
                (
                    "Images",
                    format_number(
                        latest_content.get("images")
                    )
                ),
                (
                    "Labels",
                    format_number(
                        latest_content.get("labels")
                    )
                ),
                (
                    "Features",
                    format_number(
                        latest_content.get("features")
                    )
                )
            ],
            columns_count=2
        )

    with database_column:
        st.markdown("#### Total en base")

        render_metric_cards(
            [
                (
                    "Articles",
                    format_number(
                        overview.get("articles")
                    )
                ),
                (
                    "Images",
                    format_number(
                        overview.get("images")
                    )
                ),
                (
                    "Labels",
                    format_number(
                        overview.get("article_labels")
                    )
                ),
                (
                    "Features",
                    format_number(
                        overview.get("article_features")
                    )
                )
            ],
            columns_count=2
        )


def render_pipeline_performance_summary(
    latest_run: dict[str, Any],
    overview: dict[str, Any],
    summary: dict[str, Any]
) -> None:
    """Affiche les durées et couvertures du pipeline."""

    render_layout_section_header(
        "⏱️",
        "Performance et couverture",
        "Temps d'exécution et présence des enrichissements."
    )

    render_metric_cards(
        [
            (
                "Extraction",
                format_duration(
                    latest_run.get(
                        "extraction_duration_seconds"
                    )
                )
            ),
            (
                "Transformation",
                format_duration(
                    latest_run.get(
                        "transformation_duration_seconds"
                    )
                )
            ),
            (
                "Chargement",
                format_duration(
                    latest_run.get("load_duration_seconds")
                )
            ),
            (
                "Succès global",
                format_percentage(
                    summary.get("success_rate")
                )
            )
        ],
        columns_count=4
    )

    render_metric_cards(
        [
            (
                "Couverture images",
                format_percentage(
                    overview.get("image_coverage")
                )
            ),
            (
                "Couverture labels",
                format_percentage(
                    overview.get("label_coverage")
                )
            ),
            (
                "Couverture features",
                format_percentage(
                    overview.get("feature_coverage")
                )
            )
        ],
        columns_count=3
    )

def render_pipeline_quality_kpi_section() -> None:
    """Affiche les KPI de qualité du pipeline par domaine."""

    render_layout_section_header(
        "🧪",
        "Qualité du pipeline",
        (
            "Contrôle des articles, validation des images "
            "et complétude des données collectées."
        )
    )

    try:
        quality_rows = load_kpi_quality_summary()
        image_rows = load_kpi_image_quality_summary()
        completeness = load_kpi_data_completeness()

    except Exception as error:
        logger.exception(
            "Impossible de charger les KPI qualité du pipeline."
        )
        render_kpi_error(
            "Les indicateurs de qualité ne sont pas disponibles.",
            error
        )
        return

    quality_counts = {
        str(
            row.get("data_quality_status")
            or "unknown"
        ): safe_integer(
            row.get("article_count")
        )
        for row in quality_rows
    }

    total_articles = sum(quality_counts.values())
    valid_articles = quality_counts.get("valid", 0)

    valid_images = sum(
        safe_integer(row.get("image_count"))
        for row in image_rows
        if row.get("is_valid") is True
    )

    invalid_images = sum(
        safe_integer(row.get("image_count"))
        for row in image_rows
        if row.get("is_valid") is False
    )

    pending_images = sum(
        safe_integer(row.get("image_count"))
        for row in image_rows
        if row.get("is_valid") is None
    )

    controlled_images = (
        valid_images
        + invalid_images
        + pending_images
    )

    render_article_quality_group(
        total_articles,
        valid_articles,
        quality_counts
    )

    st.divider()

    render_image_quality_group(
        controlled_images,
        valid_images,
        invalid_images,
        pending_images
    )

    st.divider()

    render_completeness_group(completeness)


def render_article_quality_group(
    total_articles: int,
    valid_articles: int,
    quality_counts: dict[str, int]
) -> None:
    """Affiche les KPI de validation des articles."""

    with st.container(border=True):
        render_layout_section_header(
            "📰",
            "Qualité des articles",
            (
                "Résultat des contrôles appliqués aux articles "
                "transformés par le pipeline."
            )
        )

        invalid_articles = max(
            0,
            total_articles - valid_articles
        )

        render_metric_cards(
            [
                (
                    "Articles contrôlés",
                    format_number(total_articles)
                ),
                (
                    "Articles valides",
                    format_number(valid_articles)
                ),
                (
                    "Articles non valides",
                    format_number(invalid_articles)
                ),
                (
                    "Taux de qualité",
                    format_percentage(
                        calculate_rate(
                            valid_articles,
                            total_articles
                        )
                    )
                )
            ],
            columns_count=4
        )

        if not quality_counts:
            st.info(
                "Aucun détail sur les statuts qualité "
                "n'est disponible."
            )
            return

        rows = [
            {
                "Statut": format_status(status),
                "Articles": count,
                "Part": format_percentage(
                    calculate_rate(
                        count,
                        total_articles
                    )
                )
            }
            for status, count in sorted(
                quality_counts.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ]

        with st.expander("Consulter les statuts qualité"):
            st.dataframe(
                pd.DataFrame(rows),
                width="stretch",
                hide_index=True
            )


def render_image_quality_group(
    controlled_images: int,
    valid_images: int,
    invalid_images: int,
    pending_images: int
) -> None:
    """Affiche les KPI de validation des images."""

    with st.container(border=True):
        render_layout_section_header(
            "🖼️",
            "Qualité des images",
            (
                "Validation technique des fichiers téléchargés "
                "et détection des images inutilisables."
            )
        )

        render_metric_cards(
            [
                (
                    "Images contrôlées",
                    format_number(controlled_images)
                ),
                (
                    "Images valides",
                    format_number(valid_images)
                ),
                (
                    "Images invalides",
                    format_number(invalid_images)
                ),
                (
                    "Taux de validation",
                    format_percentage(
                        calculate_rate(
                            valid_images,
                            valid_images + invalid_images
                        )
                    )
                )
            ],
            columns_count=4
        )

        if pending_images > 0:
            st.caption(
                f"{format_number(pending_images)} image(s) "
                "sont encore en attente de validation."
            )


def render_completeness_group(
    completeness: dict[str, Any]
) -> None:
    """Affiche les KPI de complétude par famille."""

    with st.container(border=True):
        render_layout_section_header(
            "🧩",
            "Complétude des données",
            (
                "Présence des informations éditoriales, "
                "multimodales et techniques."
            )
        )

        st.markdown("#### Métadonnées éditoriales")

        render_metric_cards(
            [
                (
                    "Contenu",
                    format_percentage(
                        completeness.get("with_content_rate")
                    )
                ),
                (
                    "Date de publication",
                    format_percentage(
                        completeness.get(
                            "with_publication_date_rate"
                        )
                    )
                ),
                (
                    "Auteur",
                    format_percentage(
                        completeness.get("with_author_rate")
                    )
                ),
                (
                    "URL",
                    format_percentage(
                        completeness.get("with_url_rate")
                    )
                )
            ],
            columns_count=4
        )

        st.markdown("#### Enrichissements techniques")

        render_metric_cards(
            [
                (
                    "Langue",
                    format_percentage(
                        completeness.get("with_language_rate")
                    )
                ),
                (
                    "Image",
                    format_percentage(
                        completeness.get("with_image_rate")
                    )
                ),
                (
                    "Label",
                    format_percentage(
                        completeness.get("with_label_rate")
                    )
                ),
                (
                    "Features",
                    format_percentage(
                        completeness.get("with_feature_rate")
                    )
                )
            ],
            columns_count=4
        )

        rows = [
            {
                "Famille": "Métadonnée éditoriale",
                "Champ": "Contenu",
                "Articles renseignés": format_number(
                    completeness.get("with_content")
                ),
                "Taux": format_percentage(
                    completeness.get("with_content_rate")
                )
            },
            {
                "Famille": "Métadonnée éditoriale",
                "Champ": "Date de publication",
                "Articles renseignés": format_number(
                    completeness.get("with_publication_date")
                ),
                "Taux": format_percentage(
                    completeness.get(
                        "with_publication_date_rate"
                    )
                )
            },
            {
                "Famille": "Métadonnée éditoriale",
                "Champ": "Auteur",
                "Articles renseignés": format_number(
                    completeness.get("with_author")
                ),
                "Taux": format_percentage(
                    completeness.get("with_author_rate")
                )
            },
            {
                "Famille": "Métadonnée éditoriale",
                "Champ": "URL",
                "Articles renseignés": format_number(
                    completeness.get("with_url")
                ),
                "Taux": format_percentage(
                    completeness.get("with_url_rate")
                )
            },
            {
                "Famille": "Enrichissement technique",
                "Champ": "Langue",
                "Articles renseignés": format_number(
                    completeness.get("with_language")
                ),
                "Taux": format_percentage(
                    completeness.get("with_language_rate")
                )
            },
            {
                "Famille": "Enrichissement technique",
                "Champ": "Image",
                "Articles renseignés": format_number(
                    completeness.get("with_image")
                ),
                "Taux": format_percentage(
                    completeness.get("with_image_rate")
                )
            },
            {
                "Famille": "Enrichissement technique",
                "Champ": "Label",
                "Articles renseignés": format_number(
                    completeness.get("with_label")
                ),
                "Taux": format_percentage(
                    completeness.get("with_label_rate")
                )
            },
            {
                "Famille": "Enrichissement technique",
                "Champ": "Features",
                "Articles renseignés": format_number(
                    completeness.get("with_feature")
                ),
                "Taux": format_percentage(
                    completeness.get("with_feature_rate")
                )
            }
        ]

        with st.expander("Consulter le détail de la complétude"):
            st.dataframe(
                pd.DataFrame(rows),
                width="stretch",
                hide_index=True
            )

def render_pipeline_sources_kpi_section() -> None:
    """Affiche les KPI de performance des sources."""

    render_layout_section_header(
        "📰",
        "Performance des sources",
        "Volumes collectés et couverture multimodale par source."
    )

    try:
        sources = load_kpi_sources_summary() or []
    except Exception as error:
        logger.exception("Impossible de charger les KPI des sources.")
        render_kpi_error(
            "Les KPI des sources ne sont pas disponibles.",
            error
        )
        return

    if not sources:
        st.info("Aucune source n'est enregistrée dans PostgreSQL.")
        return

    active_sources = sum(
        bool(source.get("is_active"))
        for source in sources
    )
    productive_sources = sum(
        safe_integer(source.get("article_count")) > 0
        for source in sources
    )
    total_articles = get_count(sources, "article_count")
    total_images = get_count(sources, "image_count")

    render_metric_cards([
        ("Sources enregistrées", format_number(len(sources))),
        ("Sources actives", format_number(active_sources)),
        ("Sources productives", format_number(productive_sources)),
        ("Articles collectés", format_number(total_articles))
    ])

    render_metric_cards([
        ("Images associées", format_number(total_images)),
        (
            "Couverture image",
            format_percentage(
                calculate_rate(total_images, total_articles)
            )
        ),
        (
            "Productivité moyenne",
            format_number(
                round(total_articles / productive_sources)
                if productive_sources
                else 0
            )
        ),
        (
            "Sources sans article",
            format_number(len(sources) - productive_sources)
        )
    ])

    dataframe = rows_to_dataframe(sources)

    required_columns = {
        "source_key",
        "display_name",
        "article_count",
        "image_count",
        "label_count"
    }
    missing_columns = get_missing_columns(
        dataframe,
        required_columns
    )

    if missing_columns:
        render_missing_columns_warning(
            "de performance des sources",
            missing_columns
        )
        return

    dataframe["Source"] = dataframe["display_name"].fillna(
        dataframe["source_key"]
    )

    numeric_columns = [
        "article_count",
        "image_count",
        "label_count"
    ]

    numeric_data = prepare_chart_dataframe(
        dataframe[numeric_columns]
    )

    dataframe[numeric_columns] = numeric_data
    dataframe = dataframe.sort_values(
        "article_count",
        ascending=False
    )

    chart_data = dataframe.head(15).set_index("Source")[
        numeric_columns
    ].rename(columns={
        "article_count": "Articles",
        "image_count": "Images",
        "label_count": "Labels"
    })

    st.bar_chart(
        chart_data,
        width="stretch"
    )

    with st.expander("Détail de toutes les sources"):
        visible_columns = [
            "Source",
            "source_type",
            "is_active",
            *numeric_columns,
            "latest_extraction"
        ]

        visible_columns = [
            column
            for column in visible_columns
            if column in dataframe.columns
        ]

        st.dataframe(
            dataframe[visible_columns].rename(columns={
                "source_type": "Type",
                "is_active": "Active",
                "article_count": "Articles",
                "image_count": "Images",
                "label_count": "Labels",
                "latest_extraction": "Dernière extraction"
            }),
            width="stretch",
            hide_index=True
        )


def render_pipeline_history_kpi_section() -> None:
    """Affiche l'évolution récente des KPI du pipeline."""

    render_layout_section_header(
        "📉",
        "Évolution du pipeline",
        "Comparaison des volumes et durées des dernières exécutions."
    )

    with st.container(border=True):
        limit = st.selectbox(
            "Nombre d'exécutions métier",
            options=[10, 25, 50, 100],
            index=1,
            key="business_pipeline_history_limit"
        )

    try:
        runs = load_kpi_pipeline_history(int(limit)) or []
    except Exception as error:
        logger.exception(
            "Impossible de charger l'historique du pipeline."
        )
        render_kpi_error(
            "L'historique du pipeline n'est pas disponible.",
            error
        )
        return

    dataframe = rows_to_dataframe(runs)

    if dataframe.empty:
        st.info("Aucune exécution métier n'est disponible.")
        return

    required_columns = {
        "started_at",
        "extracted_count",
        "transformed_count",
        "valid_count",
        "rejected_count",
        "loaded_count",
        "extraction_duration_seconds",
        "transformation_duration_seconds",
        "load_duration_seconds",
        "duration_seconds"
    }
    missing_columns = get_missing_columns(
        dataframe,
        required_columns
    )

    if missing_columns:
        render_missing_columns_warning(
            "d'historique du pipeline",
            missing_columns
        )
        return

    dataframe["started_at"] = pd.to_datetime(
        dataframe["started_at"],
        errors="coerce"
    )
    dataframe = dataframe.dropna(
        subset=["started_at"]
    ).sort_values("started_at")

    if dataframe.empty:
        st.info(
            "Les exécutions disponibles ne contiennent "
            "aucune date exploitable."
        )
        return

    dataframe["Exécution"] = dataframe["started_at"].dt.strftime(
        "%d/%m %H:%M"
    )

    volume_columns = {
        "extracted_count": "Extraits",
        "transformed_count": "Transformés",
        "valid_count": "Valides",
        "rejected_count": "Rejetés",
        "loaded_count": "Chargés"
    }
    duration_columns = {
        "extraction_duration_seconds": "Extraction",
        "transformation_duration_seconds": "Transformation",
        "load_duration_seconds": "Chargement",
        "duration_seconds": "Total"
    }

    volume_chart = prepare_chart_dataframe(
        dataframe[[
            "Exécution",
            *volume_columns
        ]].rename(
            columns=volume_columns
        ).set_index("Exécution")
    )

    duration_chart = prepare_chart_dataframe(
        dataframe[[
            "Exécution",
            *duration_columns
        ]].rename(
            columns=duration_columns
        ).set_index("Exécution")
    )

    volume_column, duration_column = st.columns(2)

    with volume_column:
        st.subheader("Volumes par exécution")
        st.line_chart(
            volume_chart,
            width="stretch"
        )

    with duration_column:
        st.subheader("Durées par étape")
        st.line_chart(
            duration_chart,
            width="stretch"
        )

    with st.expander("Historique détaillé"):
        visible_columns = [
            "status",
            "started_at",
            "duration_seconds",
            "extracted_count",
            "transformed_count",
            "valid_count",
            "rejected_count",
            "loaded_count",
            "images_valid_count",
            "images_invalid_count"
        ]

        visible_columns = [
            column
            for column in visible_columns
            if column in dataframe.columns
        ]

        st.dataframe(
            dataframe[visible_columns].rename(columns={
                "status": "Statut",
                "started_at": "Début",
                "duration_seconds": "Durée",
                "extracted_count": "Extraits",
                "transformed_count": "Transformés",
                "valid_count": "Valides",
                "rejected_count": "Rejetés",
                "loaded_count": "Chargés",
                "images_valid_count": "Images valides",
                "images_invalid_count": "Images invalides"
            }),
            width="stretch",
            hide_index=True
        )


# KPI Données

def render_data_kpi_section() -> None:
    """Affiche une synthèse transversale des KPI de données."""

    render_layout_section_header(
        "🎯",
        "KPI des données",
        (
            "Synthèse des volumes, de la couverture, de la qualité "
            "et de la productivité des sources."
        )
    )

    try:
        overview = load_kpi_database_overview() or {}
        completeness = load_kpi_data_completeness() or {}
        quality_rows = load_kpi_quality_summary() or []
        image_rows = load_kpi_image_quality_summary() or []
        sources = load_kpi_sources_summary() or []
    except Exception as error:
        logger.exception("Impossible de charger les KPI des données.")
        render_kpi_error(
            "La synthèse des KPI de données n'est pas disponible.",
            error
        )
        return

    total_articles = safe_integer(overview.get("articles"))
    total_images = safe_integer(overview.get("images"))
    total_labels = safe_integer(overview.get("article_labels"))
    total_features = safe_integer(overview.get("article_features"))

    render_metric_cards([
        ("📰 Articles", format_number(total_articles)),
        ("🖼️ Images", format_number(total_images)),
        ("🏷️ Labels", format_number(total_labels)),
        ("🧩 Features", format_number(total_features))
    ])

    render_metric_cards([
        (
            "Couverture images",
            format_percentage(overview.get("image_coverage"))
        ),
        (
            "Couverture labels",
            format_percentage(overview.get("label_coverage"))
        ),
        (
            "Couverture features",
            format_percentage(overview.get("feature_coverage"))
        ),
        (
            "Sources enregistrées",
            format_number(overview.get("sources"))
        )
    ])

    st.divider()
    render_data_quality_kpi_block(
        total_articles,
        quality_rows
    )

    st.divider()
    render_data_image_kpi_block(
        total_images,
        image_rows
    )

    st.divider()
    render_data_completeness_kpi_block(completeness)

    st.divider()
    render_data_source_kpi_block(sources)


def render_data_quality_kpi_block(
    total_articles: int,
    rows: list[dict[str, Any]]
) -> None:
    """Affiche les KPI qualité des articles."""

    render_layout_section_header(
        "✅",
        "Qualité des articles",
        "État de validation et part des articles exploitables."
    )

    positive_articles = get_count(
        rows,
        "article_count",
        predicate=lambda row: is_positive_quality_status(
            row.get("data_quality_status")
        )
    )
    classified_articles = get_count(rows, "article_count")
    unclassified_articles = max(
        0,
        total_articles - classified_articles
    )

    render_metric_cards([
        ("Articles exploitables", format_number(positive_articles)),
        (
            "Taux exploitable",
            format_percentage(
                calculate_rate(
                    positive_articles,
                    total_articles
                )
            )
        ),
        ("Articles classés", format_number(classified_articles)),
        (
            "Sans statut qualité",
            format_number(unclassified_articles)
        )
    ])

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        st.info("Aucun statut qualité détaillé n'est disponible.")
        return

    missing_columns = get_missing_columns(
        dataframe,
        {"data_quality_status", "article_count"}
    )

    if missing_columns:
        render_missing_columns_warning(
            "de qualité des articles",
            missing_columns
        )
        return

    dataframe["Statut"] = dataframe[
        "data_quality_status"
    ].map(format_status)

    dataframe["Part"] = dataframe["article_count"].map(
        lambda count: format_percentage(
            calculate_rate(
                safe_integer(count),
                total_articles
            )
        )
    )

    with st.container(border=True):
        st.dataframe(
            dataframe[[
                "Statut",
                "article_count",
                "Part"
            ]].rename(columns={
                "article_count": "Articles"
            }),
            width="stretch",
            hide_index=True
        )


def render_data_image_kpi_block(
    total_images: int,
    rows: list[dict[str, Any]]
) -> None:
    """Affiche les KPI qualité des images."""

    render_layout_section_header(
        "🖼️",
        "Qualité des images",
        "Validation des fichiers téléchargés et suivi des anomalies."
    )

    valid_images = get_count(
        rows,
        "image_count",
        predicate=is_valid_image_row
    )
    classified_images = get_count(rows, "image_count")
    invalid_images = max(
        0,
        classified_images - valid_images
    )
    pending_images = max(
        0,
        total_images - classified_images
    )

    render_metric_cards([
        ("Images valides", format_number(valid_images)),
        ("Images invalides", format_number(invalid_images)),
        ("Images non classées", format_number(pending_images)),
        (
            "Taux de validation",
            format_percentage(
                calculate_rate(valid_images, total_images)
            )
        )
    ])

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        st.info(
            "Aucun détail sur la validation des images "
            "n'est disponible."
        )
        return

    missing_columns = get_missing_columns(
        dataframe,
        {"is_valid", "validation_status", "image_count"}
    )

    if missing_columns:
        render_missing_columns_warning(
            "de qualité des images",
            missing_columns
        )
        return

    dataframe["Valide"] = dataframe["is_valid"].map(
        lambda value: format_boolean(
            is_valid_image_row({"is_valid": value})
        )
    )
    dataframe["Statut"] = dataframe[
        "validation_status"
    ].map(format_status)
    dataframe["Part"] = dataframe["image_count"].map(
        lambda count: format_percentage(
            calculate_rate(
                safe_integer(count),
                total_images
            )
        )
    )

    with st.container(border=True):
        st.dataframe(
            dataframe[[
                "Statut",
                "Valide",
                "image_count",
                "Part"
            ]].rename(columns={
                "image_count": "Images"
            }),
            width="stretch",
            hide_index=True
        )


def render_data_completeness_kpi_block(
    completeness: dict[str, Any]
) -> None:
    """Affiche les principaux taux de complétude."""

    render_layout_section_header(
        "🧩",
        "Complétude essentielle",
        (
            "Présence des champs nécessaires à l'exploitation "
            "éditoriale et technique."
        )
    )

    key_fields = [
        ("Contenu", "with_content", "with_content_rate"),
        (
            "Date de publication",
            "with_publication_date",
            "with_publication_date_rate"
        ),
        ("Auteur", "with_author", "with_author_rate"),
        ("URL", "with_url", "with_url_rate"),
        ("Langue", "with_language", "with_language_rate"),
        ("Image", "with_image", "with_image_rate"),
        ("Label", "with_label", "with_label_rate"),
        ("Features", "with_feature", "with_feature_rate")
    ]

    render_metric_cards(
        [
            (
                label,
                format_percentage(completeness.get(rate_field))
            )
            for label, _, rate_field in key_fields
        ],
        columns_count=4
    )

    rows = [
        {
            "Champ": label,
            "Articles renseignés": format_number(
                completeness.get(count_field)
            ),
            "Taux": format_percentage(
                completeness.get(rate_field)
            )
        }
        for label, count_field, rate_field in key_fields
    ]

    with st.expander("Consulter le détail de la complétude"):
        st.dataframe(
            pd.DataFrame(rows),
            width="stretch",
            hide_index=True
        )


def render_data_source_kpi_block(
    sources: list[dict[str, Any]]
) -> None:
    """Affiche les KPI de productivité des sources."""

    render_layout_section_header(
        "🌐",
        "Productivité des sources",
        "Activité des connecteurs et contribution au corpus."
    )

    active_sources = sum(
        bool(source.get("is_active"))
        for source in sources
    )
    productive_sources = sum(
        safe_integer(source.get("article_count")) > 0
        for source in sources
    )
    total_source_articles = get_count(
        sources,
        "article_count"
    )
    average_articles = (
        total_source_articles / productive_sources
        if productive_sources
        else 0
    )

    render_metric_cards([
        ("Sources actives", format_number(active_sources)),
        ("Sources productives", format_number(productive_sources)),
        (
            "Taux de productivité",
            format_percentage(
                calculate_rate(
                    productive_sources,
                    active_sources
                )
            )
        ),
        (
            "Articles par source productive",
            f"{average_articles:.1f}"
        )
    ])

    dataframe = rows_to_dataframe(sources)

    if dataframe.empty:
        st.info("Aucune source n'est enregistrée.")
        return

    expected_columns = [
        "display_name",
        "source_type",
        "article_count",
        "image_count",
        "label_count",
        "latest_extraction"
    ]
    visible_columns = [
        column
        for column in expected_columns
        if column in dataframe.columns
    ]

    if not visible_columns:
        st.warning(
            "Les statistiques des sources ne contiennent "
            "aucune colonne exploitable."
        )
        return

    ranking = dataframe[visible_columns].copy()

    if "article_count" in ranking.columns:
        ranking["article_count"] = pd.to_numeric(
            ranking["article_count"],
            errors="coerce"
        ).fillna(0)

        ranking = ranking.sort_values(
            "article_count",
            ascending=False
        )

    ranking = ranking.head(10).rename(columns={
        "display_name": "Source",
        "source_type": "Type",
        "article_count": "Articles",
        "image_count": "Images",
        "label_count": "Labels",
        "latest_extraction": "Dernière extraction"
    })

    with st.container(border=True):
        st.markdown("#### Sources les plus productives")

        st.dataframe(
            ranking,
            width="stretch",
            hide_index=True
        )


# Actualisation

def clear_kpi_cache() -> None:
    """Supprime tous les caches KPI du dashboard."""

    load_kpi_database_overview.clear()
    load_kpi_latest_pipeline_run.clear()
    load_kpi_latest_run_content.clear()
    load_kpi_pipeline_summary.clear()
    load_kpi_pipeline_history.clear()
    load_kpi_data_completeness.clear()
    load_kpi_quality_summary.clear()
    load_kpi_image_quality_summary.clear()
    load_kpi_sources_summary.clear()


def clear_data_kpi_cache() -> None:
    """Conserve la compatibilité avec la page Données."""

    clear_kpi_cache()


def clear_pipeline_kpi_cache() -> None:
    """Conserve la compatibilité avec la page Pipeline."""

    clear_kpi_cache()