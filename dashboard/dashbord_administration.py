"""Page d'administration du dashboard CheckIt.AI.

Cette page permet de :

- contrôler la connexion à PostgreSQL et Airflow ;
- consulter l'état technique des services ;
- déclencher manuellement les DAGs CheckIt.AI ;
- mettre les DAGs en pause ou les réactiver ;
- consulter un aperçu des tables PostgreSQL ;
- afficher les informations utiles à la maintenance.

Les actions sensibles nécessitent une confirmation explicite.
"""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

from dashboard.services.dashboard_airflow_service import (
    AirflowServiceError,
    get_checkit_dags,
    get_health_summary,
    get_latest_dag_run,
    pause_dag,
    test_connection as test_airflow_connection,
    trigger_dag,
    unpause_dag
)
from dashboard.services.dahsboard_postgres_service import (
    ALLOWED_TABLES,
    get_database_size,
    get_table_counts,
    get_table_preview,
    test_connection as test_postgres_connection
)
from dashboard.dashboard_ui_utils import (
    format_dag_name,
    format_datetime,
    format_number,
    format_status,
    render_information_block,
    render_metric_cards,
    render_refresh_section,
    render_section_header,
    rows_to_dataframe
)
from src.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Configuration
# ============================================================================

DANGEROUS_DAGS = {
    "checkit_cleanup_dag",
    "checkit_database_setup"
}

DEFAULT_TABLE = "articles"
DEFAULT_PREVIEW_LIMIT = 50


# ============================================================================
# Cache
# ============================================================================

@st.cache_data(ttl=15, show_spinner=False)
def load_postgres_connection() -> dict[str, Any]:
    """Teste la connexion PostgreSQL."""

    return test_postgres_connection()


@st.cache_data(ttl=15, show_spinner=False)
def load_airflow_connection() -> dict[str, Any]:
    """Teste la connexion Airflow."""

    return test_airflow_connection()


@st.cache_data(ttl=15, show_spinner=False)
def load_airflow_health() -> dict[str, Any]:
    """Charge l'état des composants Airflow."""

    return get_health_summary()


@st.cache_data(ttl=15, show_spinner=False)
def load_checkit_dags() -> list[dict[str, Any]]:
    """Charge les DAGs appartenant au projet CheckIt.AI."""

    return get_checkit_dags()


@st.cache_data(ttl=15, show_spinner=False)
def load_latest_dag_run(
    dag_id: str
) -> dict[str, Any] | None:
    """Charge la dernière exécution d'un DAG."""

    return get_latest_dag_run(dag_id)


@st.cache_data(ttl=30, show_spinner=False)
def load_database_information() -> dict[str, Any]:
    """Charge les principales informations PostgreSQL."""

    return {
        "size": get_database_size(),
        "counts": get_table_counts()
    }


@st.cache_data(ttl=30, show_spinner=False)
def load_table_preview(
    table_name: str,
    limit: int
) -> list[dict[str, Any]]:
    """Charge un aperçu d'une table PostgreSQL."""

    return get_table_preview(
        table_name,
        limit=limit
    )


# ============================================================================
# Style
# ============================================================================

def render_administration_style() -> None:
    """Applique le style visuel de la page Administration."""

    st.markdown(
        """
        <style>
            .checkit-admin-header {
                padding: 1.35rem 1.5rem;
                margin-bottom: 1.25rem;
                border: 1px solid rgba(128, 132, 149, 0.18);
                border-radius: 1.1rem;
                background:
                    radial-gradient(
                        circle at top right,
                        rgba(255, 155, 72, 0.18),
                        transparent 38%
                    ),
                    rgba(128, 132, 149, 0.045);
            }

            .checkit-admin-eyebrow {
                margin-bottom: 0.45rem;
                color: #8d91a4;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.11em;
                text-transform: uppercase;
            }

            .checkit-admin-title {
                margin: 0;
                font-size: 2rem;
                font-weight: 780;
                line-height: 1.15;
            }

            .checkit-admin-description {
                max-width: 54rem;
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
                background: rgba(255, 155, 72, 0.14);
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

            .checkit-info-card {
                padding: 0.9rem 1rem;
                border: 1px solid rgba(128, 132, 149, 0.18);
                border-radius: 0.8rem;
                background: rgba(128, 132, 149, 0.04);
            }

            .checkit-info-row {
                padding: 0.55rem 0;
                border-bottom: 1px solid rgba(128, 132, 149, 0.12);
            }

            .checkit-info-row:last-child {
                border-bottom: none;
            }

            .checkit-info-label {
                color: #8d91a4;
                font-size: 0.68rem;
                font-weight: 700;
                letter-spacing: 0.05em;
                text-transform: uppercase;
            }

            .checkit-info-value {
                margin-top: 0.18rem;
                font-size: 0.84rem;
                line-height: 1.35;
                word-break: break-word;
            }

            .checkit-danger-card {
                padding: 0.9rem 1rem;
                margin-bottom: 0.85rem;
                border: 1px solid rgba(255, 93, 93, 0.26);
                border-radius: 0.8rem;
                background: rgba(255, 93, 93, 0.08);
                color: #ff7c7c;
                font-size: 0.82rem;
                line-height: 1.45;
            }

            .checkit-safe-card {
                padding: 0.9rem 1rem;
                margin-bottom: 0.85rem;
                border: 1px solid rgba(49, 199, 106, 0.24);
                border-radius: 0.8rem;
                background: rgba(49, 199, 106, 0.08);
                color: #54d889;
                font-size: 0.82rem;
                line-height: 1.45;
            }

            .checkit-maintenance-card {
                height: 100%;
                padding: 1rem;
                border: 1px solid rgba(128, 132, 149, 0.18);
                border-radius: 0.9rem;
                background: rgba(128, 132, 149, 0.04);
            }

            .checkit-maintenance-title {
                margin-bottom: 0.45rem;
                font-size: 0.98rem;
                font-weight: 720;
            }

            .checkit-maintenance-text {
                color: #9a9eae;
                font-size: 0.8rem;
                line-height: 1.5;
            }

            .checkit-footer-note {
                margin-top: 0.6rem;
                color: #85899b;
                font-size: 0.72rem;
                text-align: center;
            }

            div[data-testid="stMetric"] {
                padding: 0.15rem 0;
            }

            div[data-testid="stMetricLabel"] {
                color: #9296a8;
                font-size: 0.78rem;
            }

            div[data-testid="stMetricValue"] {
                font-size: 1.3rem;
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
            div[data-testid="stTextArea"] label,
            div[data-testid="stNumberInput"] label,
            div[data-testid="stCheckbox"] label {
                color: #8d91a4;
                font-size: 0.77rem;
                font-weight: 600;
            }

            div[data-testid="stButton"] button,
            div[data-testid="stFormSubmitButton"] button {
                min-height: 2.6rem;
                border-radius: 0.75rem;
                font-weight: 650;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================================
# En-tête
# ============================================================================

def render_header() -> None:
    """Affiche le titre et la description de la page."""

    st.markdown(
        '<div class="checkit-admin-header">'
        '<div class="checkit-admin-eyebrow">'
        'Console technique'
        '</div>'
        '<div class="checkit-admin-title">'
        '🛠️ Administration CheckIt.AI'
        '</div>'
        '<div class="checkit-admin-description">'
        'Contrôle des services, pilotage des DAGs Airflow et '
        'consultation technique de la base PostgreSQL.'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================================
# État des services
# ============================================================================

def render_services_section() -> None:
    """Affiche les contrôles PostgreSQL et Airflow."""

    render_section_header(
        "🔌",
        "État des services",
        "Disponibilité des composants techniques de la plateforme."
    )

    postgres_column, airflow_column = st.columns(2)

    with postgres_column:
        with st.container(border=True):
            render_postgres_status()

    with airflow_column:
        with st.container(border=True):
            render_airflow_status()


def render_postgres_status() -> None:
    """Affiche l'état de PostgreSQL."""

    st.subheader("🐘 PostgreSQL")

    try:
        connection = load_postgres_connection()
        information = load_database_information()
        database_size = information.get("size", {})

        st.success("PostgreSQL est accessible.")

        render_metric_cards([
            (
                "Base",
                str(connection.get("database") or "Inconnue")
            ),
            (
                "Taille",
                str(
                    database_size.get("formatted_size")
                    or "Inconnue"
                )
            )
        ], columns_count=2)

        render_information_block([
            (
                "Utilisateur",
                connection.get("database_user", "inconnu")
            ),
            (
                "Schéma",
                connection.get("schema", "inconnu")
            )
        ])

        with st.expander("Informations PostgreSQL"):
            st.json(connection)

    except Exception as error:
        logger.warning(
            "Connexion PostgreSQL impossible depuis "
            "la page d'administration : %s",
            error
        )

        st.error("PostgreSQL est indisponible.")

        with st.expander("Détail technique"):
            st.code(str(error))


def render_airflow_status() -> None:
    """Affiche l'état d'Airflow."""

    st.subheader("🌬️ Airflow")

    try:
        connection = load_airflow_connection()
        health = load_airflow_health()
        global_status = health.get("status", "unknown")

        if global_status == "healthy":
            st.success("Airflow est opérationnel.")
        elif global_status == "unhealthy":
            st.error("Un composant Airflow est indisponible.")
        else:
            st.warning(
                "L'état global d'Airflow n'a pas pu être déterminé."
            )

        render_metric_cards([
            (
                "Version",
                str(connection.get("version") or "Inconnue")
            ),
            (
                "État",
                format_status(global_status)
            )
        ], columns_count=2)

        render_information_block([
            (
                "Adresse",
                connection.get("base_url", "inconnue")
            )
        ])

        with st.expander("Composants Airflow"):
            render_airflow_components(
                health.get("components", {})
            )

    except Exception as error:
        logger.warning(
            "Connexion Airflow impossible depuis "
            "la page d'administration : %s",
            error
        )

        st.error("Airflow est indisponible.")

        with st.expander("Détail technique"):
            st.code(str(error))


def render_airflow_components(
    components: dict[str, dict[str, Any]]
) -> None:
    """Affiche l'état individuel des composants Airflow."""

    if not components:
        st.info(
            "Aucune information sur les composants "
            "Airflow n'est disponible."
        )
        return

    rows = []

    for component_name, component in components.items():
        rows.append({
            "Composant": component_name.replace("_", " ").capitalize(),
            "État": format_status(component.get("status")),
            "Dernier battement": format_datetime(
                component.get("latest_heartbeat")
                or component.get("latest_scheduler_heartbeat")
                or component.get("last_heartbeat")
            )
        })

    st.dataframe(
        rows_to_dataframe(rows),
        width="stretch",
        hide_index=True
    )


# ============================================================================
# Contrôle des DAGs
# ============================================================================

def render_dag_control_section() -> None:
    """Affiche les commandes permettant de gérer les DAGs."""

    render_section_header(
        "⚙️",
        "Contrôle des DAGs",
        "Déclenchement manuel et gestion de la planification Airflow."
    )

    try:
        dags = load_checkit_dags()

    except Exception as error:
        logger.warning(
            "Impossible de charger les DAGs CheckIt.AI : %s",
            error
        )

        st.error(
            "La liste des DAGs Airflow n'est pas disponible."
        )
        return

    if not dags:
        st.info(
            "Aucun DAG CheckIt.AI n'a été trouvé dans Airflow."
        )
        return

    dag_ids = sorted(
        str(dag.get("dag_id"))
        for dag in dags
        if dag.get("dag_id")
    )

    with st.container(border=True):
        selected_dag_id = st.selectbox(
            "DAG à administrer",
            options=dag_ids,
            format_func=lambda dag_id: format_dag_name(
                dag_id,
                include_id=True
            ),
            key="administration_dag"
        )

    selected_dag = next(
        (
            dag
            for dag in dags
            if dag.get("dag_id") == selected_dag_id
        ),
        {}
    )

    render_selected_dag_status(
        selected_dag_id,
        selected_dag
    )

    trigger_column, schedule_column = st.columns(2)

    with trigger_column:
        with st.container(border=True):
            render_dag_trigger_form(selected_dag_id)

    with schedule_column:
        with st.container(border=True):
            render_dag_pause_controls(
                selected_dag_id,
                selected_dag
            )


def render_selected_dag_status(
    dag_id: str,
    dag: dict[str, Any]
) -> None:
    """Affiche l'état du DAG sélectionné."""

    latest_run = load_latest_dag_run(dag_id)
    is_paused = bool(dag.get("is_paused"))

    render_metric_cards([
        (
            "DAG",
            format_dag_name(dag_id)
        ),
        (
            "Planification",
            "🟠 En pause" if is_paused else "🟢 Actif"
        ),
        (
            "Dernier run",
            format_status(
                latest_run.get("state")
                if latest_run
                else "unknown"
            )
        )
    ], columns_count=3)

    if latest_run:
        with st.expander("Dernière exécution"):
            render_information_block([
                (
                    "Run ID",
                    latest_run.get("dag_run_id", "inconnu")
                ),
                (
                    "Début",
                    format_datetime(latest_run.get("start_date"))
                ),
                (
                    "Fin",
                    format_datetime(latest_run.get("end_date"))
                )
            ])

            st.json(latest_run)


def render_dag_trigger_form(dag_id: str) -> None:
    """Affiche le formulaire de déclenchement d'un DAG."""

    st.subheader("▶️ Déclencher")

    is_dangerous = dag_id in DANGEROUS_DAGS

    if is_dangerous:
        st.markdown(
            '<div class="checkit-danger-card">'
            '⚠️ Ce DAG peut modifier ou supprimer des données. '
            'Une confirmation explicite est obligatoire.'
            '</div>',
            unsafe_allow_html=True
        )

    with st.form(
        "trigger_dag_form",
        clear_on_submit=False
    ):
        configuration_text = st.text_area(
            "Configuration JSON",
            value="{}",
            height=140,
            help=(
                "Configuration transmise au DAG dans le champ conf. "
                "Laisser {} lorsqu'aucun paramètre n'est nécessaire."
            )
        )

        confirmation = st.checkbox(
            (
                "Je confirme vouloir exécuter cette action"
                if is_dangerous
                else "Je confirme le déclenchement du DAG"
            )
        )

        submitted = st.form_submit_button(
            "▶️ Déclencher le DAG",
            width="stretch",
            type="primary"
        )

    if not submitted:
        return

    if not confirmation:
        st.warning(
            "Tu dois confirmer l'exécution avant "
            "de déclencher le DAG."
        )
        return

    configuration = parse_configuration(
        configuration_text
    )

    if configuration is None:
        return

    trigger_selected_dag(
        dag_id,
        configuration
    )


def parse_configuration(
    configuration_text: str
) -> dict[str, Any] | None:
    """Valide la configuration JSON saisie par l'utilisateur."""

    normalized_text = configuration_text.strip() or "{}"

    try:
        configuration = json.loads(normalized_text)

    except json.JSONDecodeError as error:
        st.error(
            "La configuration saisie n'est pas un JSON valide."
        )

        st.code(str(error))
        return None

    if not isinstance(configuration, dict):
        st.error(
            "La configuration doit être un objet JSON."
        )
        return None

    return configuration


def trigger_selected_dag(
    dag_id: str,
    configuration: dict[str, Any]
) -> None:
    """Déclenche le DAG sélectionné."""

    try:
        with st.spinner(
            f"Déclenchement du DAG {dag_id}..."
        ):
            result = trigger_dag(
                dag_id,
                configuration=configuration
            )

        st.success(
            f"Le DAG `{dag_id}` a été déclenché."
        )

        run_id = result.get("dag_run_id")

        if run_id:
            st.write(f"**Run ID :** `{run_id}`")

        with st.expander("Réponse Airflow"):
            st.json(result)

        clear_administration_cache()

    except AirflowServiceError as error:
        logger.warning(
            "Échec du déclenchement du DAG %s : %s",
            dag_id,
            error
        )

        st.error(
            "Airflow a refusé ou n'a pas pu exécuter le DAG."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

    except Exception as error:
        logger.exception(
            "Erreur inattendue pendant le déclenchement "
            "du DAG %s.",
            dag_id
        )

        st.error(
            "Une erreur inattendue est survenue pendant "
            "le déclenchement."
        )

        with st.expander("Détail technique"):
            st.code(str(error))


def render_dag_pause_controls(
    dag_id: str,
    dag: dict[str, Any]
) -> None:
    """Affiche les commandes de pause d'un DAG."""

    st.subheader("⏯️ Planification")

    is_paused = bool(dag.get("is_paused"))

    if is_paused:
        st.markdown(
            '<div class="checkit-danger-card">'
            'Le DAG est actuellement en pause. '
            'Il ne sera pas déclenché automatiquement.'
            '</div>',
            unsafe_allow_html=True
        )

        if st.button(
            "🟢 Réactiver le DAG",
            width="stretch",
            key=f"unpause_{dag_id}"
        ):
            update_dag_pause_state(
                dag_id,
                is_paused=False
            )

        return

    st.markdown(
        '<div class="checkit-safe-card">'
        'Le DAG est actif et peut être planifié '
        'ou déclenché normalement.'
        '</div>',
        unsafe_allow_html=True
    )

    confirmation = st.checkbox(
        "Je confirme vouloir mettre ce DAG en pause",
        key=f"pause_confirmation_{dag_id}"
    )

    if st.button(
        "🟠 Mettre le DAG en pause",
        width="stretch",
        disabled=not confirmation,
        key=f"pause_{dag_id}"
    ):
        update_dag_pause_state(
            dag_id,
            is_paused=True
        )


def update_dag_pause_state(
    dag_id: str,
    *,
    is_paused: bool
) -> None:
    """Modifie l'état de pause d'un DAG."""

    try:
        with st.spinner(
            "Mise à jour du DAG..."
        ):
            if is_paused:
                result = pause_dag(dag_id)
            else:
                result = unpause_dag(dag_id)

        action = (
            "mis en pause"
            if is_paused
            else "réactivé"
        )

        st.success(
            f"Le DAG `{dag_id}` a été {action}."
        )

        with st.expander("Réponse Airflow"):
            st.json(result)

        clear_administration_cache()
        st.rerun()

    except Exception as error:
        logger.warning(
            "Impossible de modifier l'état du DAG %s : %s",
            dag_id,
            error
        )

        st.error(
            "L'état du DAG n'a pas pu être modifié."
        )

        with st.expander("Détail technique"):
            st.code(str(error))


# ============================================================================
# Consultation PostgreSQL
# ============================================================================

def render_database_section() -> None:
    """Affiche les informations et aperçus PostgreSQL."""

    render_section_header(
        "🗄️",
        "Consultation PostgreSQL",
        "Volumes des tables et aperçu sécurisé des données stockées."
    )

    try:
        database_information = load_database_information()

    except Exception as error:
        logger.warning(
            "Impossible de charger les informations PostgreSQL : %s",
            error
        )

        st.error(
            "Les informations PostgreSQL ne sont pas disponibles."
        )
        return

    render_table_counts(
        database_information.get("counts", {})
    )

    st.divider()
    render_table_browser()


def render_table_counts(
    counts: dict[str, int]
) -> None:
    """Affiche le nombre de lignes des tables."""

    render_section_header(
        "📦",
        "Contenu des tables",
        "Nombre de lignes actuellement présentes dans chaque table."
    )

    if not counts:
        st.info(
            "Aucune statistique de table n'est disponible."
        )
        return

    metrics = [
        (
            table_name.replace("_", " ").capitalize(),
            format_number(counts[table_name])
        )
        for table_name in sorted(counts)
    ]

    render_metric_cards(
        metrics,
        columns_count=min(4, max(1, len(metrics)))
    )


def render_table_browser() -> None:
    """Affiche un aperçu sécurisé d'une table autorisée."""

    render_section_header(
        "🔎",
        "Explorateur de tables",
        "Aperçu en lecture seule des tables autorisées."
    )

    table_names = sorted(ALLOWED_TABLES)

    with st.container(border=True):
        first_column, second_column = st.columns([3, 1])

        with first_column:
            selected_table = st.selectbox(
                "Table",
                options=table_names,
                index=(
                    table_names.index(DEFAULT_TABLE)
                    if DEFAULT_TABLE in table_names
                    else 0
                ),
                key="administration_table"
            )

        with second_column:
            limit = st.number_input(
                "Nombre de lignes",
                min_value=10,
                max_value=500,
                value=DEFAULT_PREVIEW_LIMIT,
                step=10,
                key="administration_table_limit"
            )

    try:
        rows = load_table_preview(
            selected_table,
            int(limit)
        )

    except Exception as error:
        logger.warning(
            "Impossible de consulter la table %s : %s",
            selected_table,
            error
        )

        st.error(
            f"La table `{selected_table}` n'a pas pu être consultée."
        )

        with st.expander("Détail technique"):
            st.code(str(error))

        return

    dataframe = rows_to_dataframe(rows)

    if dataframe.empty:
        st.info(
            f"La table `{selected_table}` est vide."
        )
        return

    st.dataframe(
        dataframe,
        width="stretch",
        hide_index=True
    )

    st.caption(
        f"{len(dataframe)} ligne(s) affichée(s). "
        "Consultation strictement limitée à la lecture."
    )


# ============================================================================
# Maintenance
# ============================================================================

def render_maintenance_section() -> None:
    """Affiche les informations relatives à la maintenance."""

    render_section_header(
        "🧹",
        "Maintenance",
        "Opérations techniques encadrées par les DAGs Airflow."
    )

    st.info(
        "Le dashboard ne supprime directement aucune donnée. "
        "Les opérations sensibles passent par Airflow afin de conserver "
        "les validations, les journaux et la traçabilité."
    )

    first_column, second_column = st.columns(2)

    with first_column:
        st.markdown(
            '<div class="checkit-maintenance-card">'
            '<div class="checkit-maintenance-title">'
            '🧹 Nettoyage des lots'
            '</div>'
            '<div class="checkit-maintenance-text">'
            'Le DAG <code>checkit_cleanup_dag</code> gère le nettoyage '
            'contrôlé des fichiers intermédiaires.<br><br>'
            'Son déclenchement nécessite une confirmation explicite '
            'depuis la section de contrôle des DAGs.'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    with second_column:
        st.markdown(
            '<div class="checkit-maintenance-card">'
            '<div class="checkit-maintenance-title">'
            '🗄️ Initialisation PostgreSQL'
            '</div>'
            '<div class="checkit-maintenance-text">'
            'Le DAG <code>checkit_database_setup</code> prépare la '
            'structure PostgreSQL utilisée par CheckIt.AI.<br><br>'
            'Cette opération doit rester exceptionnelle sur une base '
            'contenant déjà des données.'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )


# ============================================================================
# Actualisation
# ============================================================================

def clear_administration_cache() -> None:
    """Supprime le cache utilisé par la page."""

    load_postgres_connection.clear()
    load_airflow_connection.clear()
    load_airflow_health.clear()
    load_checkit_dags.clear()
    load_latest_dag_run.clear()
    load_database_information.clear()
    load_table_preview.clear()


# ============================================================================
# Page complète
# ============================================================================

def render_administration_page() -> None:
    """Affiche la page d'administration complète."""

    render_administration_style()
    render_header()

    services_tab, dags_tab, database_tab, maintenance_tab = st.tabs([
        "🔌 Services",
        "⚙️ DAGs",
        "🗄️ PostgreSQL",
        "🧹 Maintenance"
    ])

    with services_tab:
        render_services_section()

    with dags_tab:
        render_dag_control_section()

    with database_tab:
        render_database_section()

    with maintenance_tab:
        render_maintenance_section()

    render_refresh_section(
        button_label="🔄 Actualiser l'administration",
        button_key="refresh_administration_page",
        cache_message=(
            "Les informations techniques sont conservées "
            "en cache entre 15 et 30 secondes."
        ),
        clear_cache=clear_administration_cache
    )