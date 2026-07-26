"""Page de supervision du pipeline CheckIt.AI.

Cette page permet de :

- surveiller l'état général d'Airflow ;
- consulter les DAGs CheckIt.AI ;
- analyser les dernières exécutions ;
- afficher le détail des tâches d'un DagRun ;
- consulter les logs d'une tentative ;
- identifier rapidement les derniers échecs.

Les actions d'administration restent dans administration.py.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from dashboard.services.dashboard_airflow_service import (
    AirflowServiceError,
    get_checkit_dag_overview,
    get_dag_run_summary,
    get_dag_runs,
    get_health_summary,
    get_recent_failures,
    get_run_duration_seconds,
    get_task_instances,
    get_task_log
)
from dashboard.dashboard_ui_utils import (
    calculate_duration_seconds,
    format_dag_name,
    format_datetime,
    format_duration,
    format_number,
    format_percentage,
    format_status,
    render_metric_cards,
    render_refresh_section,
    render_section_header,
    render_selection_help
)
from src.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Configuration
# ============================================================================

DAG_OPTIONS = [
    "checkit_master_pipeline",
    "checkit_extract_dag",
    "checkit_transform_dag",
    "checkit_load_dag",
    "checkit_quality_dag",
    "checkit_cleanup_dag",
    "checkit_database_setup",
    "test_checkit_postgres"
]

RUN_LIMIT_OPTIONS = [10, 25, 50, 100, 200]
DEFAULT_RUN_LIMIT = 25

TERMINAL_STATES = {
    "success",
    "failed",
    "canceled"
}


# ============================================================================
# Cache
# ============================================================================

@st.cache_data(ttl=15, show_spinner=False)
def load_health_summary() -> dict[str, Any]:
    """Charge l'état de santé d'Airflow."""

    return get_health_summary()


@st.cache_data(ttl=15, show_spinner=False)
def load_dag_overview() -> list[dict[str, Any]]:
    """Charge la synthèse des DAGs CheckIt.AI."""

    return get_checkit_dag_overview()


@st.cache_data(ttl=15, show_spinner=False)
def load_run_summary(
    dag_id: str,
    limit: int
) -> dict[str, Any]:
    """Charge les statistiques d'exécution d'un DAG."""

    return get_dag_run_summary(
        dag_id=dag_id,
        limit=limit
    )


@st.cache_data(ttl=15, show_spinner=False)
def load_dag_runs(
    dag_id: str,
    limit: int
) -> list[dict[str, Any]]:
    """Charge les dernières exécutions d'un DAG."""

    return get_dag_runs(
        dag_id,
        limit=limit,
        order_by="-start_date"
    )


@st.cache_data(ttl=15, show_spinner=False)
def load_task_instances(
    dag_id: str,
    dag_run_id: str
) -> list[dict[str, Any]]:
    """Charge les tâches d'une exécution Airflow."""

    return get_task_instances(
        dag_id,
        dag_run_id
    )


@st.cache_data(ttl=15, show_spinner=False)
def load_recent_failures(
    limit: int
) -> list[dict[str, Any]]:
    """Charge les derniers échecs Airflow."""

    return get_recent_failures(limit)


@st.cache_data(ttl=15, show_spinner=False)
def load_task_log(
    dag_id: str,
    dag_run_id: str,
    task_id: str,
    try_number: int,
    map_index: int
) -> str:
    """Charge le log d'une tentative de tâche."""

    return get_task_log(
        dag_id,
        dag_run_id,
        task_id,
        task_try_number=try_number,
        map_index=map_index,
        full_content=True
    )


# ============================================================================
# Style
# ============================================================================

def render_pipeline_style() -> None:
    """Applique le style visuel de la page Pipeline."""

    st.markdown(
        """
        <style>
            .checkit-page-header {
                padding: 1.35rem 1.5rem;
                margin-bottom: 1.25rem;
                border: 1px solid rgba(128, 132, 149, 0.18);
                border-radius: 1.1rem;
                background:
                    radial-gradient(
                        circle at top right,
                        rgba(67, 97, 238, 0.18),
                        transparent 36%
                    ),
                    rgba(128, 132, 149, 0.045);
            }

            .checkit-page-eyebrow {
                margin-bottom: 0.45rem;
                color: #8d91a4;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.11em;
                text-transform: uppercase;
            }

            .checkit-page-title {
                margin: 0;
                font-size: 2rem;
                font-weight: 780;
                line-height: 1.15;
            }

            .checkit-page-description {
                max-width: 52rem;
                margin-top: 0.55rem;
                color: #9397a8;
                font-size: 0.92rem;
                line-height: 1.5;
            }

            .checkit-section-header {
                display: flex;
                align-items: center;
                gap: 0.65rem;
                margin: 1.1rem 0 0.85rem;
            }

            .checkit-section-icon {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 2rem;
                height: 2rem;
                flex: 0 0 2rem;
                border-radius: 0.65rem;
                font-size: 0.92rem;
                background: rgba(67, 97, 238, 0.13);
            }

            .checkit-section-title {
                margin: 0;
                font-size: 1.05rem;
                font-weight: 720;
                line-height: 1.2;
            }

            .checkit-section-description {
                margin-top: 0.15rem;
                color: #8d91a4;
                font-size: 0.76rem;
                line-height: 1.35;
            }

            .checkit-run-reference {
                padding: 0.8rem 1rem;
                margin: 0.75rem 0;
                border-left: 3px solid rgba(67, 97, 238, 0.75);
                border-radius: 0 0.7rem 0.7rem 0;
                background: rgba(67, 97, 238, 0.07);
                font-size: 0.82rem;
                line-height: 1.65;
            }

            .checkit-run-reference code {
                font-size: 0.76rem;
            }

            .checkit-selection-help {
                padding: 0.8rem 1rem;
                margin-top: 0.75rem;
                border: 1px dashed rgba(128, 132, 149, 0.25);
                border-radius: 0.75rem;
                color: #8d91a4;
                font-size: 0.78rem;
                text-align: center;
            }

            .checkit-success-card {
                padding: 1rem 1.1rem;
                border: 1px solid rgba(49, 199, 106, 0.26);
                border-radius: 0.85rem;
                background: rgba(49, 199, 106, 0.08);
                color: #52d584;
                font-size: 0.86rem;
                font-weight: 600;
            }

            div[data-testid="stMetric"] {
                padding: 0.2rem 0;
            }

            div[data-testid="stMetricLabel"] {
                color: #9296a8;
                font-size: 0.78rem;
            }

            div[data-testid="stMetricValue"] {
                font-size: 1.35rem;
                font-weight: 750;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                border-color: rgba(128, 132, 149, 0.18);
                border-radius: 0.9rem;
                background: rgba(128, 132, 149, 0.035);
            }

            button[data-baseweb="tab"] {
                height: 3rem;
                padding-left: 1rem;
                padding-right: 1rem;
                font-weight: 650;
            }

            [data-testid="stDataFrame"] {
                border: 1px solid rgba(128, 132, 149, 0.16);
                border-radius: 0.8rem;
                overflow: hidden;
            }

            div[data-testid="stSelectbox"] label,
            div[data-testid="stNumberInput"] label {
                color: #8d91a4;
                font-size: 0.77rem;
                font-weight: 600;
            }

            div[data-testid="stButton"] button,
            div[data-testid="stDownloadButton"] button {
                min-height: 2.6rem;
                border-radius: 0.75rem;
                font-weight: 650;
            }

            div[data-testid="stCode"] {
                border: 1px solid rgba(128, 132, 149, 0.16);
                border-radius: 0.85rem;
            }

            .checkit-footer-note {
                margin-top: 0.6rem;
                color: #85899b;
                font-size: 0.72rem;
                text-align: center;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================================
# En-tête
# ============================================================================

def render_header() -> None:
    """Affiche l'en-tête de la page."""

    st.markdown(
        '<div class="checkit-page-header">'
        '<div class="checkit-page-eyebrow">'
        'Centre de supervision'
        '</div>'
        '<div class="checkit-page-title">'
        '📊 Pipeline CheckIt.AI'
        '</div>'
        '<div class="checkit-page-description">'
        'Suivi opérationnel des DAGs Airflow, des exécutions, '
        'des tâches et des journaux techniques du pipeline multimodal.'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================================
# Santé Airflow
# ============================================================================

def render_health_section() -> None:
    """Affiche l'état général des composants Airflow."""

    render_section_header(
        "📡",
        "État d'Airflow",
        "Disponibilité générale des composants d'orchestration."
    )

    try:
        health = load_health_summary()

    except Exception as error:
        logger.warning(
            "Impossible de charger la santé Airflow : %s",
            error
        )

        st.error("L'état d'Airflow n'est pas disponible.")

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    render_metric_cards([
        (
            "État global",
            format_status(health.get("status"))
        ),
        (
            "Composants opérationnels",
            format_number(health.get("healthy_count"))
        ),
        (
            "Composants indisponibles",
            format_number(health.get("unhealthy_count"))
        ),
        (
            "État inconnu",
            format_number(health.get("unknown_count"))
        )
    ])

    components = health.get("components", {})

    if not components:
        return

    rows = []

    for name, component in components.items():
        rows.append({
            "Composant": name.replace("_", " ").capitalize(),
            "État": format_status(component.get("status")),
            "Dernier battement": format_datetime(
                component.get("latest_heartbeat")
                or component.get("latest_scheduler_heartbeat")
                or component.get("last_heartbeat")
            )
        })

    with st.expander("Consulter le détail des composants"):
        st.dataframe(
            pd.DataFrame(rows),
            width="stretch",
            hide_index=True
        )


# ============================================================================
# Vue générale des DAGs
# ============================================================================

def render_dag_overview_section() -> None:
    """Affiche une synthèse des DAGs CheckIt.AI."""

    render_section_header(
        "🧭",
        "DAGs CheckIt.AI",
        "État de planification et dernière exécution de chaque DAG."
    )

    try:
        dags = load_dag_overview()

    except Exception as error:
        logger.warning(
            "Impossible de charger les DAGs CheckIt.AI : %s",
            error
        )

        st.error("Les DAGs CheckIt.AI ne sont pas disponibles.")
        return

    if not dags:
        st.info("Aucun DAG CheckIt.AI n'a été trouvé.")
        return

    active_count = sum(
        not bool(dag.get("is_paused"))
        for dag in dags
    )

    failed_count = sum(
        str(dag.get("last_state") or "").lower() == "failed"
        for dag in dags
    )

    running_count = sum(
        str(dag.get("last_state") or "").lower() == "running"
        for dag in dags
    )

    render_metric_cards([
        ("DAGs enregistrés", format_number(len(dags))),
        ("DAGs actifs", format_number(active_count)),
        ("En cours", format_number(running_count)),
        ("Derniers runs échoués", format_number(failed_count))
    ])

    st.dataframe(
        prepare_dag_overview_dataframe(dags),
        width="stretch",
        hide_index=True
    )


def prepare_dag_overview_dataframe(
    dags: list[dict[str, Any]]
) -> pd.DataFrame:
    """Prépare les DAGs pour leur affichage."""

    rows = []

    for dag in dags:
        rows.append({
            "DAG": format_dag_name(str(dag.get("dag_id") or "")),
            "Identifiant": dag.get("dag_id"),
            "Planification": (
                "🟠 En pause"
                if dag.get("is_paused")
                else "🟢 Actif"
            ),
            "Dernier état": format_status(dag.get("last_state")),
            "Dernier démarrage": format_datetime(
                dag.get("last_start_date")
            ),
            "Durée": format_duration(
                dag.get("last_duration_seconds")
            )
        })

    return pd.DataFrame(rows)


# ============================================================================
# Statistiques des exécutions
# ============================================================================

def render_run_summary_section() -> None:
    """Affiche les statistiques des dernières exécutions."""

    render_section_header(
        "📈",
        "Statistiques des exécutions",
        "Analyse synthétique des derniers DagRuns du DAG sélectionné."
    )

    dag_id, limit = render_run_filters("summary")

    try:
        summary = load_run_summary(
            dag_id,
            limit
        )

    except Exception as error:
        logger.warning(
            "Impossible de charger les statistiques Airflow : %s",
            error
        )

        st.error(
            "Les statistiques d'exécution ne sont pas disponibles."
        )
        return

    render_metric_cards([
        (
            "Exécutions analysées",
            format_number(summary.get("total_runs"))
        ),
        (
            "Succès",
            format_number(summary.get("successful_runs"))
        ),
        (
            "Échecs",
            format_number(summary.get("failed_runs"))
        ),
        (
            "Taux de réussite",
            format_percentage(summary.get("success_rate"))
        )
    ])

    render_metric_cards([
        (
            "En cours",
            format_number(summary.get("running_runs"))
        ),
        (
            "En attente",
            format_number(summary.get("queued_runs"))
        ),
        (
            "Durée moyenne",
            format_duration(summary.get("average_duration_seconds"))
        ),
        (
            "Durée maximale",
            format_duration(summary.get("maximum_duration_seconds"))
        )
    ])

    state_counts = summary.get("state_counts", {})

    if not state_counts:
        return

    dataframe = pd.DataFrame([
        {
            "État": format_status(state),
            "Nombre": count
        }
        for state, count in state_counts.items()
    ])

    with st.expander("Répartition détaillée des états"):
        st.dataframe(
            dataframe,
            width="stretch",
            hide_index=True
        )


# ============================================================================
# Historique des exécutions
# ============================================================================

def render_runs_section() -> None:
    """Affiche la liste des DagRuns et leur détail."""

    render_section_header(
        "🧩",
        "Historique des exécutions",
        "Sélection d'un run pour consulter ses tâches et ses journaux."
    )

    dag_id, limit = render_run_filters("history")

    try:
        runs = load_dag_runs(
            dag_id,
            limit
        )

    except Exception as error:
        logger.warning(
            "Impossible de charger les DagRuns : %s",
            error
        )

        st.error(
            "L'historique des exécutions n'est pas disponible."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    if not runs:
        st.info("Aucune exécution n'a été trouvée.")
        return

    event = st.dataframe(
        prepare_runs_dataframe(runs),
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="pipeline_runs_dataframe"
    )

    selected_rows = event.selection.rows

    if not selected_rows:
        render_selection_help(
            "Sélectionne une exécution dans le tableau pour afficher "
            "ses tâches et ses journaux."
        )
        return

    selected_run = runs[selected_rows[0]]

    selected_dag_id = str(
        selected_run.get("dag_id")
        or dag_id
    )

    selected_run_id = str(
        selected_run.get("dag_run_id")
        or selected_run.get("run_id")
        or ""
    )

    if not selected_dag_id or not selected_run_id:
        st.warning(
            "Cette exécution ne contient pas les identifiants "
            "nécessaires à la consultation des tâches."
        )
        return

    render_run_details(
        selected_dag_id,
        selected_run_id,
        selected_run
    )


def render_run_filters(
    key_prefix: str
) -> tuple[str, int]:
    """Affiche les filtres communs aux exécutions."""

    with st.container(border=True):
        first_column, second_column = st.columns([3, 1])

        with first_column:
            dag_id = st.selectbox(
                "DAG analysé",
                options=DAG_OPTIONS,
                format_func=lambda value: format_dag_name(
                    value,
                    include_id=True
                ),
                key=f"{key_prefix}_dag_id"
            )

        with second_column:
            limit = st.selectbox(
                "Nombre de runs",
                options=RUN_LIMIT_OPTIONS,
                index=RUN_LIMIT_OPTIONS.index(DEFAULT_RUN_LIMIT),
                key=f"{key_prefix}_run_limit"
            )

    return dag_id, int(limit)


def prepare_runs_dataframe(
    runs: list[dict[str, Any]]
) -> pd.DataFrame:
    """Prépare les DagRuns pour leur affichage."""

    rows = []

    for run in runs:
        rows.append({
            "DAG": format_dag_name(
                str(run.get("dag_id") or "")
            ),
            "Run ID": (
                run.get("dag_run_id")
                or run.get("run_id")
            ),
            "État": format_status(run.get("state")),
            "Début": format_datetime(run.get("start_date")),
            "Fin": format_datetime(run.get("end_date")),
            "Durée": format_duration(
                get_run_duration_seconds(run)
            ),
            "Type": (
                run.get("run_type")
                or run.get("triggering_user_name")
                or "Non disponible"
            )
        })

    return pd.DataFrame(rows)


# ============================================================================
# Détail d'une exécution
# ============================================================================

def render_run_details(
    dag_id: str,
    dag_run_id: str,
    run: dict[str, Any]
) -> None:
    """Affiche le détail d'une exécution sélectionnée."""

    st.divider()

    render_section_header(
        "🔍",
        "Détail de l'exécution",
        "Informations générales et tâches du DagRun sélectionné."
    )

    render_metric_cards([
        ("État", format_status(run.get("state"))),
        (
            "Durée",
            format_duration(get_run_duration_seconds(run))
        ),
        (
            "Début",
            format_datetime(run.get("start_date"))
        ),
        (
            "Fin",
            format_datetime(run.get("end_date"))
        )
    ])

    st.markdown(
        '<div class="checkit-run-reference">'
        f'<strong>DAG :</strong> <code>{dag_id}</code><br>'
        f'<strong>Run ID :</strong> <code>{dag_run_id}</code>'
        '</div>',
        unsafe_allow_html=True
    )

    if run.get("conf"):
        with st.expander("Configuration du run"):
            st.json(run.get("conf"))

    try:
        tasks = load_task_instances(
            dag_id,
            dag_run_id
        )

    except Exception as error:
        logger.warning(
            "Impossible de charger les tâches du run %s : %s",
            dag_run_id,
            error
        )

        st.error(
            "Les tâches de cette exécution ne sont pas disponibles."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    render_tasks_section(
        dag_id,
        dag_run_id,
        tasks
    )


# ============================================================================
# Tâches et logs
# ============================================================================

def render_tasks_section(
    dag_id: str,
    dag_run_id: str,
    tasks: list[dict[str, Any]]
) -> None:
    """Affiche les tâches d'une exécution."""

    render_section_header(
        "⚙️",
        "Tâches",
        "États, durées et tentatives des tâches du DagRun."
    )

    if not tasks:
        st.info(
            "Aucune tâche n'est disponible pour cette exécution."
        )
        return

    state_counts: dict[str, int] = {}

    for task in tasks:
        state = str(task.get("state") or "unknown").lower()
        state_counts[state] = state_counts.get(state, 0) + 1

    metrics = [
        (
            format_status(state),
            format_number(count)
        )
        for state, count in sorted(state_counts.items())
    ]

    render_metric_cards(
        metrics,
        columns_count=min(4, max(1, len(metrics)))
    )

    event = st.dataframe(
        prepare_tasks_dataframe(tasks),
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"tasks_{dag_id}_{dag_run_id}"
    )

    selected_rows = event.selection.rows

    if not selected_rows:
        render_selection_help(
            "Sélectionne une tâche pour consulter son journal."
        )
        return

    render_task_log_section(
        dag_id,
        dag_run_id,
        tasks[selected_rows[0]]
    )


def prepare_tasks_dataframe(
    tasks: list[dict[str, Any]]
) -> pd.DataFrame:
    """Prépare les tâches pour leur affichage."""

    rows = []

    for task in tasks:
        duration = task.get("duration")

        if duration is None:
            duration = calculate_duration_seconds(
                task.get("start_date"),
                task.get("end_date"),
                running=(
                    str(task.get("state") or "").lower()
                    not in TERMINAL_STATES
                )
            )

        rows.append({
            "Tâche": task.get("task_id"),
            "État": format_status(task.get("state")),
            "Tentative": (
                task.get("try_number")
                or task.get("task_try_number")
                or 0
            ),
            "Début": format_datetime(task.get("start_date")),
            "Fin": format_datetime(task.get("end_date")),
            "Durée": format_duration(duration),
            "Map index": task.get("map_index", -1),
            "Opérateur": task.get("operator")
        })

    return pd.DataFrame(rows)


def render_task_log_section(
    dag_id: str,
    dag_run_id: str,
    task: dict[str, Any]
) -> None:
    """Affiche le journal de la tâche sélectionnée."""

    task_id = str(task.get("task_id") or "")

    if not task_id:
        st.warning(
            "La tâche sélectionnée ne possède pas d'identifiant."
        )
        return

    try_number = int(
        task.get("try_number")
        or task.get("task_try_number")
        or 1
    )

    map_index = int(task.get("map_index", -1))

    st.divider()

    render_section_header(
        "📜",
        f"Journal de la tâche {task_id}",
        "Consultation du contenu produit par la tentative sélectionnée."
    )

    render_metric_cards([
        ("État", format_status(task.get("state"))),
        ("Tentative", format_number(try_number)),
        ("Map index", format_number(map_index))
    ], columns_count=3)

    with st.container(border=True):
        selected_try_number = st.number_input(
            "Tentative à consulter",
            min_value=1,
            max_value=max(1, try_number),
            value=max(1, try_number),
            step=1,
            key=f"log_try_{dag_id}_{dag_run_id}_{task_id}"
        )

    try:
        log_content = load_task_log(
            dag_id,
            dag_run_id,
            task_id,
            int(selected_try_number),
            map_index
        )

    except AirflowServiceError as error:
        logger.warning(
            "Impossible de charger le log de la tâche %s : %s",
            task_id,
            error
        )

        st.error(
            "Le journal de cette tâche n'est pas disponible."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    except Exception as error:
        logger.exception(
            "Erreur inattendue pendant la lecture du log %s.",
            task_id
        )

        st.error(
            "Une erreur est survenue pendant la lecture du journal."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    if not log_content.strip():
        st.info("Le journal de cette tentative est vide.")
        return

    st.code(
        log_content,
        language="text",
        line_numbers=True
    )

    st.download_button(
        "⬇️ Télécharger le journal",
        data=log_content,
        file_name=(
            f"{dag_id}_{dag_run_id}_{task_id}"
            f"_try_{selected_try_number}.log"
        ),
        mime="text/plain",
        width="stretch"
    )


# ============================================================================
# Échecs récents
# ============================================================================

def render_failures_section() -> None:
    """Affiche les dernières exécutions ayant échoué."""

    render_section_header(
        "🚨",
        "Échecs récents",
        "Dernières exécutions nécessitant une attention particulière."
    )

    with st.container(border=True):
        limit = st.selectbox(
            "Nombre maximal d'échecs",
            options=[5, 10, 20, 50],
            index=1,
            key="pipeline_failure_limit"
        )

    try:
        failures = load_recent_failures(int(limit))

    except Exception as error:
        logger.warning(
            "Impossible de charger les échecs récents : %s",
            error
        )

        st.error(
            "Les derniers échecs ne sont pas disponibles."
        )
        return

    if not failures:
        st.markdown(
            '<div class="checkit-success-card">'
            '✅ Aucun échec récent détecté. '
            'Le pipeline fonctionne normalement.'
            '</div>',
            unsafe_allow_html=True
        )
        return

    rows = []

    for failure in failures:
        failed_tasks = failure.get("failed_tasks") or []

        task_names = ", ".join(
            str(task.get("task_id"))
            for task in failed_tasks
            if task.get("task_id")
        )

        rows.append({
            "DAG": format_dag_name(
                str(failure.get("dag_id") or "")
            ),
            "Run ID": failure.get("dag_run_id"),
            "État": format_status(failure.get("state")),
            "Début": format_datetime(failure.get("start_date")),
            "Fin": format_datetime(failure.get("end_date")),
            "Durée": format_duration(
                failure.get("duration_seconds")
            ),
            "Tâches échouées": task_names or "Non disponible"
        })

    render_metric_cards([
        (
            "Échecs recensés",
            format_number(len(failures))
        ),
        (
            "DAGs concernés",
            format_number(
                len({
                    failure.get("dag_id")
                    for failure in failures
                    if failure.get("dag_id")
                })
            )
        )
    ], columns_count=2)

    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
        hide_index=True
    )

    with st.expander("Détail technique brut"):
        st.json(failures)


# ============================================================================
# Actualisation
# ============================================================================

def clear_pipeline_cache() -> None:
    """Supprime le cache utilisé par la page."""

    load_health_summary.clear()
    load_dag_overview.clear()
    load_run_summary.clear()
    load_dag_runs.clear()
    load_task_instances.clear()
    load_recent_failures.clear()
    load_task_log.clear()


# ============================================================================
# Page complète
# ============================================================================

def render_pipeline_page() -> None:
    """Affiche la page de supervision du pipeline."""

    render_pipeline_style()
    render_header()

    overview_tab, runs_tab, failures_tab = st.tabs([
        "📡 Vue générale",
        "🧩 Exécutions et tâches",
        "🚨 Incidents"
    ])

    with overview_tab:
        render_health_section()
        st.divider()
        render_dag_overview_section()
        st.divider()
        render_run_summary_section()

    with runs_tab:
        render_runs_section()

    with failures_tab:
        render_failures_section()

    render_refresh_section(
        button_label="🔄 Actualiser la supervision",
        button_key="refresh_pipeline_page",
        cache_message=(
            "Les données Airflow sont conservées "
            "en cache pendant 15 secondes."
        ),
        clear_cache=clear_pipeline_cache
    )