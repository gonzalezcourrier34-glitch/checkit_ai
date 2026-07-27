"""Service Airflow du dashboard CheckIt.AI.

Ce module permet au dashboard de communiquer avec Airflow afin de :

- vérifier la disponibilité de l'API ;
- consulter la santé des composants Airflow ;
- récupérer la liste et l'état des DAGs ;
- consulter les DagRuns et leurs tâches ;
- déclencher manuellement un DAG ;
- mettre un DAG en pause ou le réactiver ;
- récupérer les journaux d'une tâche.

Le service utilise uniquement l'API REST publique Airflow 3.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from urllib.parse import quote

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from dashboard.services.dashboard_service_utils import (
    calculate_percentage,
    normalize_limit,
    normalize_offset
)
from src.logger import get_logger

logger = get_logger(__name__)


# Configuration

AIRFLOW_BASE_URL = (
    os.getenv(
        "CHECKIT_AIRFLOW_URL",
        os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080")
    ).strip().rstrip("/")
    or "http://localhost:8080"
)

AIRFLOW_API_URL = f"{AIRFLOW_BASE_URL}/api/v2"
AIRFLOW_AUTH_URL = f"{AIRFLOW_BASE_URL}/auth/token"

AIRFLOW_USERNAME = os.getenv(
    "CHECKIT_AIRFLOW_USERNAME",
    os.getenv("AIRFLOW_USERNAME", "airflow")
).strip()

AIRFLOW_PASSWORD = os.getenv(
    "CHECKIT_AIRFLOW_PASSWORD",
    os.getenv("AIRFLOW_PASSWORD", "airflow")
)

AIRFLOW_ACCESS_TOKEN = os.getenv(
    "CHECKIT_AIRFLOW_TOKEN",
    os.getenv("AIRFLOW_ACCESS_TOKEN", "")
).strip()

AIRFLOW_REQUEST_TIMEOUT = float(
    os.getenv("CHECKIT_AIRFLOW_REQUEST_TIMEOUT", "10")
)

AIRFLOW_MAX_RETRIES = int(
    os.getenv("CHECKIT_AIRFLOW_MAX_RETRIES", "2")
)

AIRFLOW_VERIFY_SSL = (
    os.getenv("CHECKIT_AIRFLOW_VERIFY_SSL", "true")
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)

AIRFLOW_DEFAULT_PAGE_LIMIT = int(
    os.getenv("CHECKIT_AIRFLOW_PAGE_LIMIT", "100")
)

CHECKIT_DAG_IDS = {
    "checkit_master_pipeline",
    "checkit_extract_dag",
    "checkit_transform_dag",
    "checkit_load_dag",
    "checkit_quality_dag",
    "checkit_cleanup_dag",
    "checkit_database_setup",
    "test_checkit_postgres"
}

TERMINAL_DAG_RUN_STATES = {
    "success",
    "failed",
    "canceled"
}

FAILED_DAG_RUN_STATES = {
    "failed",
    "canceled"
}

FAILED_TASK_STATES = {
    "failed",
    "upstream_failed"
}


# Erreurs

class AirflowServiceError(RuntimeError):
    """Erreur produite pendant un appel à l'API Airflow."""


class AirflowAuthenticationError(AirflowServiceError):
    """Erreur d'authentification auprès d'Airflow."""


class AirflowNotFoundError(AirflowServiceError):
    """Ressource Airflow introuvable."""


# Session HTTP

_session: Session | None = None
_access_token: str | None = AIRFLOW_ACCESS_TOKEN or None
_token_lock = Lock()


def create_session() -> Session:
    """Crée une session HTTP réutilisable pour l'API Airflow."""

    retry_configuration = Retry(
        total=AIRFLOW_MAX_RETRIES,
        connect=AIRFLOW_MAX_RETRIES,
        read=AIRFLOW_MAX_RETRIES,
        status=AIRFLOW_MAX_RETRIES,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({
            "GET",
            "HEAD",
            "OPTIONS",
            "PUT",
            "DELETE"
        }),
        raise_on_status=False
    )

    adapter = HTTPAdapter(
        max_retries=retry_configuration,
        pool_connections=10,
        pool_maxsize=20
    )

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "CheckItAI-Dashboard/1.0"
    })
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def get_session() -> Session:
    """Retourne la session HTTP partagée du dashboard."""

    global _session

    if _session is None:
        _session = create_session()

    return _session


# Authentification

def request_access_token(force_refresh: bool = False) -> str:
    """Obtient un jeton JWT auprès du gestionnaire d'authentification."""

    global _access_token

    if _access_token and not force_refresh:
        return _access_token

    with _token_lock:
        if _access_token and not force_refresh:
            return _access_token

        if not AIRFLOW_USERNAME:
            raise AirflowAuthenticationError(
                "Aucun utilisateur Airflow n'est configuré."
            )

        try:
            response = get_session().post(
                AIRFLOW_AUTH_URL,
                json={
                    "username": AIRFLOW_USERNAME,
                    "password": AIRFLOW_PASSWORD
                },
                timeout=AIRFLOW_REQUEST_TIMEOUT,
                verify=AIRFLOW_VERIFY_SSL
            )

        except requests.RequestException as error:
            raise AirflowAuthenticationError(
                "Impossible de contacter le service "
                "d'authentification Airflow."
            ) from error

        if not response.ok:
            raise AirflowAuthenticationError(
                build_error_message(
                    response,
                    "Authentification Airflow refusée"
                )
            )

        payload = parse_json_response(response)
        token = (
            payload.get("access_token")
            or payload.get("token")
            or payload.get("jwt")
        )

        if not token:
            raise AirflowAuthenticationError(
                "Airflow n'a retourné aucun jeton d'accès."
            )

        _access_token = str(token)
        return _access_token


def clear_access_token() -> None:
    """Supprime le jeton mémorisé afin de forcer son renouvellement."""

    global _access_token
    _access_token = AIRFLOW_ACCESS_TOKEN or None


def get_auth_headers() -> dict[str, str]:
    """Construit les en-têtes d'authentification Airflow."""

    return {
        "Authorization": f"Bearer {request_access_token()}"
    }


# Appels API

def airflow_request(
    method: str,
    endpoint: str,
    *,
    parameters: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    authenticated: bool = True,
    retry_authentication: bool = True
) -> dict[str, Any]:
    """Exécute un appel vers l'API REST Airflow."""

    normalized_endpoint = endpoint.strip()

    if not normalized_endpoint.startswith("/"):
        normalized_endpoint = f"/{normalized_endpoint}"

    url = f"{AIRFLOW_API_URL}{normalized_endpoint}"
    headers = get_auth_headers() if authenticated else {}

    try:
        response = get_session().request(
            method=method.upper(),
            url=url,
            params=parameters,
            json=payload,
            headers=headers,
            timeout=AIRFLOW_REQUEST_TIMEOUT,
            verify=AIRFLOW_VERIFY_SSL
        )

    except requests.Timeout as error:
        raise AirflowServiceError(
            f"Délai d'attente dépassé pour Airflow : {url}"
        ) from error

    except requests.RequestException as error:
        raise AirflowServiceError(
            f"Impossible de contacter Airflow : {url}"
        ) from error

    if (
        response.status_code == 401
        and authenticated
        and retry_authentication
        and not AIRFLOW_ACCESS_TOKEN
    ):
        request_access_token(force_refresh=True)

        return airflow_request(
            method,
            endpoint,
            parameters=parameters,
            payload=payload,
            authenticated=True,
            retry_authentication=False
        )

    if response.status_code == 404:
        raise AirflowNotFoundError(
            build_error_message(
                response,
                "Ressource Airflow introuvable"
            )
        )

    if not response.ok:
        raise AirflowServiceError(
            build_error_message(
                response,
                "Erreur retournée par Airflow"
            )
        )

    return parse_json_response(response)


def parse_json_response(response: Response) -> dict[str, Any]:
    """Convertit une réponse Airflow en dictionnaire."""

    if not response.content:
        return {}

    try:
        payload = response.json()

    except ValueError as error:
        raise AirflowServiceError(
            "Airflow a retourné une réponse JSON invalide."
        ) from error

    if isinstance(payload, dict):
        return payload

    return {"items": payload}


def build_error_message(
    response: Response,
    prefix: str
) -> str:
    """Construit un message lisible à partir d'une erreur HTTP."""

    detail = ""

    try:
        payload = response.json()

        if isinstance(payload, dict):
            detail = str(
                payload.get("detail")
                or payload.get("message")
                or payload.get("title")
                or ""
            )

    except ValueError:
        detail = response.text.strip()

    suffix = f" : {detail}" if detail else ""

    return (
        f"{prefix} "
        f"({response.status_code} {response.reason})"
        f"{suffix}"
    )


def encode_path_value(value: str) -> str:
    """Protège une valeur insérée dans le chemin d'une URL."""

    return quote(str(value), safe="")


def build_dag_path(
    dag_id: str,
    *parts: str
) -> str:
    """Construit un chemin API Airflow sécurisé pour un DAG."""

    encoded_parts = [
        encode_path_value(part)
        for part in parts
    ]

    path = f"/dags/{encode_path_value(dag_id)}"

    if encoded_parts:
        path = f"{path}/{'/'.join(encoded_parts)}"

    return path


def get_collection(
    payload: dict[str, Any],
    *possible_keys: str
) -> list[dict[str, Any]]:
    """Extrait une collection depuis une réponse Airflow."""

    for key in possible_keys:
        value = payload.get(key)

        if isinstance(value, list):
            return [
                item
                for item in value
                if isinstance(item, dict)
            ]

    items = payload.get("items")

    if isinstance(items, list):
        return [
            item
            for item in items
            if isinstance(item, dict)
        ]

    return []


# Disponibilité et santé

def get_airflow_version() -> dict[str, Any]:
    """Retourne la version exposée par Airflow."""

    return airflow_request(
        "GET",
        "/version",
        authenticated=False
    )


def get_airflow_health() -> dict[str, Any]:
    """Retourne l'état de santé des composants Airflow."""

    return airflow_request(
        "GET",
        "/monitor/health",
        authenticated=False
    )


def is_airflow_available() -> bool:
    """Indique si l'API Airflow répond correctement."""

    try:
        get_airflow_version()
        return True

    except Exception as error:
        logger.warning(
            "API Airflow indisponible : %s",
            error
        )
        return False


def get_health_summary() -> dict[str, Any]:
    """Construit un résumé exploitable par le dashboard."""

    health = get_airflow_health()
    components: dict[str, dict[str, Any]] = {}
    healthy_count = 0
    unhealthy_count = 0
    unknown_count = 0

    for component_name, component_value in health.items():
        if not isinstance(component_value, dict):
            continue

        status = str(
            component_value.get("status") or "unknown"
        ).lower()

        components[component_name] = {
            **component_value,
            "status": status
        }

        if status == "healthy":
            healthy_count += 1
        elif status == "unhealthy":
            unhealthy_count += 1
        else:
            unknown_count += 1

    global_status = (
        "healthy"
        if components and unhealthy_count == 0
        else "unhealthy"
    )

    if not components:
        global_status = "unknown"

    return {
        "status": global_status,
        "components": components,
        "healthy_count": healthy_count,
        "unhealthy_count": unhealthy_count,
        "unknown_count": unknown_count,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }


def test_connection() -> dict[str, Any]:
    """Teste Airflow et retourne sa version et son état de santé."""

    version = get_airflow_version()
    health = get_health_summary()

    return {
        "status": "success",
        "base_url": AIRFLOW_BASE_URL,
        "version": (
            version.get("version")
            or version.get("git_version")
            or "unknown"
        ),
        "health": health,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }


# DAGs

def get_dags(
    *,
    limit: int = AIRFLOW_DEFAULT_PAGE_LIMIT,
    offset: int = 0,
    only_active: bool = False,
    checkit_only: bool = False
) -> list[dict[str, Any]]:
    """Retourne les DAGs connus par Airflow."""

    safe_limit = normalize_limit(limit)
    safe_offset = normalize_offset(offset)

    payload = airflow_request(
        "GET",
        "/dags",
        parameters={
            "limit": safe_limit,
            "offset": safe_offset,
            "only_active": str(only_active).lower()
        }
    )

    dags = get_collection(payload, "dags")

    if checkit_only:
        dags = [
            dag
            for dag in dags
            if str(dag.get("dag_id")) in CHECKIT_DAG_IDS
            or str(dag.get("dag_id", "")).startswith("checkit_")
        ]

    return dags


def get_dag(dag_id: str) -> dict[str, Any]:
    """Retourne les informations d'un DAG."""

    return airflow_request(
        "GET",
        build_dag_path(dag_id)
    )


def get_checkit_dags() -> list[dict[str, Any]]:
    """Retourne uniquement les DAGs du projet CheckIt.AI."""

    return get_dags(
        limit=500,
        only_active=False,
        checkit_only=True
    )


def set_dag_paused(
    dag_id: str,
    is_paused: bool
) -> dict[str, Any]:
    """Met un DAG en pause ou le réactive."""

    return airflow_request(
        "PATCH",
        build_dag_path(dag_id),
        payload={
            "is_paused": bool(is_paused)
        }
    )


def pause_dag(dag_id: str) -> dict[str, Any]:
    """Met un DAG en pause."""

    return set_dag_paused(dag_id, True)


def unpause_dag(dag_id: str) -> dict[str, Any]:
    """Réactive un DAG."""

    return set_dag_paused(dag_id, False)


# Exécutions des DAGs

def get_dag_runs(
    dag_id: str = "~",
    *,
    limit: int = 50,
    offset: int = 0,
    order_by: str = "-start_date"
) -> list[dict[str, Any]]:
    """Retourne les exécutions d'un DAG ou de tous les DAGs."""

    safe_limit = normalize_limit(limit)
    safe_offset = normalize_offset(offset)
    encoded_dag_id = (
        "~"
        if dag_id == "~"
        else encode_path_value(dag_id)
    )

    payload = airflow_request(
        "GET",
        build_dag_path(dag_id, "dagRuns"),
        parameters={
            "limit": safe_limit,
            "offset": safe_offset,
            "order_by": order_by
        }
    )

    return get_collection(
        payload,
        "dag_runs",
        "dagRuns"
    )


def get_dag_run(
    dag_id: str,
    dag_run_id: str
) -> dict[str, Any]:
    """Retourne une exécution précise d'un DAG."""

    return airflow_request(
        "GET",
        build_dag_path(
            dag_id,
            "dagRuns",
            dag_run_id
        )
    )


def get_latest_dag_run(
    dag_id: str
) -> dict[str, Any] | None:
    """Retourne la dernière exécution connue d'un DAG."""

    runs = get_dag_runs(
        dag_id,
        limit=1,
        order_by="-start_date"
    )

    return runs[0] if runs else None


def trigger_dag(
    dag_id: str,
    *,
    configuration: dict[str, Any] | None = None,
    dag_run_id: str | None = None,
    logical_date: str | None = None,
    note: str | None = None
) -> dict[str, Any]:
    """Déclenche manuellement un DAG Airflow."""

    # Airflow exige la présence du champ logical_date,
    # même pour un déclenchement manuel sans date imposée.
    payload: dict[str, Any] = {
        "conf": configuration or {},
        "logical_date": logical_date
    }

    if dag_run_id:
        payload["dag_run_id"] = dag_run_id

    if note:
        payload["note"] = note

    result = airflow_request(
        "POST",
        build_dag_path(dag_id, "dagRuns"),
        payload=payload
    )

    logger.info(
        "DAG Airflow déclenché depuis le dashboard : %s, run=%s.",
        dag_id,
        result.get("dag_run_id")
    )

    return result


def trigger_checkit_pipeline(
    *,
    configuration: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Déclenche le pipeline maître CheckIt.AI."""

    return trigger_dag(
        "checkit_master_pipeline",
        configuration=configuration
    )


def get_running_dag_runs(
    dag_id: str = "~",
    limit: int = 100
) -> list[dict[str, Any]]:
    """Retourne les exécutions actuellement non terminées."""

    return [
        run
        for run in get_dag_runs(dag_id, limit=limit)
        if str(run.get("state", "")).lower()
        not in TERMINAL_DAG_RUN_STATES
    ]


def get_failed_dag_runs(
    dag_id: str = "~",
    limit: int = 100
) -> list[dict[str, Any]]:
    """Retourne les exécutions récemment échouées."""

    return [
        run
        for run in get_dag_runs(dag_id, limit=limit)
        if str(run.get("state", "")).lower()
        in FAILED_DAG_RUN_STATES
    ]


# Tâches

def get_task_instances(
    dag_id: str,
    dag_run_id: str,
    *,
    limit: int = 500,
    offset: int = 0
) -> list[dict[str, Any]]:
    """Retourne les tâches d'une exécution Airflow."""

    safe_limit = normalize_limit(limit)
    safe_offset = normalize_offset(offset)
    payload = airflow_request(
        "GET",
        build_dag_path(
            dag_id,
            "dagRuns",
            dag_run_id,
            "taskInstances"
        ),
        parameters={
            "limit": safe_limit,
            "offset": safe_offset
        }
    )

    return get_collection(
        payload,
        "task_instances",
        "taskInstances"
    )


def get_task_instance(
    dag_id: str,
    dag_run_id: str,
    task_id: str,
    map_index: int = -1
) -> dict[str, Any]:
    """Retourne une tâche précise d'un DagRun."""

    return airflow_request(
        "GET",
        build_dag_path(
            dag_id,
            "dagRuns",
            dag_run_id,
            "taskInstances",
            task_id
        ),
        parameters={
            "map_index": int(map_index)
        }
    )


def get_failed_task_instances(
    dag_id: str,
    dag_run_id: str
) -> list[dict[str, Any]]:
    """Retourne les tâches échouées d'une exécution."""

    return [
        task
        for task in get_task_instances(dag_id, dag_run_id)
        if str(task.get("state", "")).lower()
        in FAILED_TASK_STATES
    ]


def get_task_state_summary(
    dag_id: str,
    dag_run_id: str
) -> dict[str, int]:
    """Compte les tâches d'une exécution par état."""

    summary: dict[str, int] = {}

    for task in get_task_instances(dag_id, dag_run_id):
        state = str(task.get("state") or "unknown").lower()
        summary[state] = summary.get(state, 0) + 1

    return summary


# Logs

def get_task_log(
    dag_id: str,
    dag_run_id: str,
    task_id: str,
    *,
    task_try_number: int = 1,
    map_index: int = -1,
    full_content: bool = True
) -> str:
    """Retourne le journal d'une tentative de tâche."""

    payload = airflow_request(
        "GET",
        build_dag_path(
            dag_id,
            "dagRuns",
            dag_run_id,
            "taskInstances",
            task_id,
            "logs",
            str(int(task_try_number))
        ),
        parameters={
            "map_index": int(map_index),
            "full_content": str(bool(full_content)).lower()
        }
    )

    content = (
        payload.get("content")
        or payload.get("log")
        or payload.get("message")
        or ""
    )

    if isinstance(content, list):
        return "\n".join(str(line) for line in content)

    return str(content)


# Statistiques du dashboard

def get_dag_run_summary(
    *,
    dag_id: str = "~",
    limit: int = 200
) -> dict[str, Any]:
    """Calcule les principaux indicateurs des DagRuns."""

    runs = get_dag_runs(dag_id, limit=limit)
    state_counts: dict[str, int] = {}
    durations: list[float] = []

    for run in runs:
        state = str(run.get("state") or "unknown").lower()
        state_counts[state] = state_counts.get(state, 0) + 1

        duration = get_run_duration_seconds(run)

        if duration is not None:
            durations.append(duration)

    total_runs = len(runs)
    successful_runs = state_counts.get("success", 0)
    failed_runs = sum(
        state_counts.get(state, 0)
        for state in FAILED_DAG_RUN_STATES
    )

    return {
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "running_runs": state_counts.get("running", 0),
        "queued_runs": state_counts.get("queued", 0),
        "state_counts": state_counts,
        "success_rate": calculate_percentage(
            successful_runs,
            total_runs
        ),
        "average_duration_seconds": (
            round(sum(durations) / len(durations), 3)
            if durations
            else 0.0
        ),
        "maximum_duration_seconds": (
            round(max(durations), 3)
            if durations
            else 0.0
        )
    }


def get_checkit_dag_overview() -> list[dict[str, Any]]:
    """Construit une ligne de synthèse pour chaque DAG CheckIt.AI."""

    overview: list[dict[str, Any]] = []

    for dag in get_checkit_dags():
        dag_id = str(dag.get("dag_id") or "")
        latest_run = get_latest_dag_run(dag_id)

        overview.append({
            "dag_id": dag_id,
            "description": dag.get("description"),
            "is_paused": bool(dag.get("is_paused")),
            "is_active": dag.get("is_active"),
            "file_token": dag.get("file_token"),
            "last_state": (
                latest_run.get("state")
                if latest_run
                else None
            ),
            "last_run_id": (
                latest_run.get("dag_run_id")
                if latest_run
                else None
            ),
            "last_start_date": (
                latest_run.get("start_date")
                if latest_run
                else None
            ),
            "last_end_date": (
                latest_run.get("end_date")
                if latest_run
                else None
            ),
            "last_duration_seconds": (
                get_run_duration_seconds(latest_run)
                if latest_run
                else None
            )
        })

    return sorted(
        overview,
        key=lambda item: item["dag_id"]
    )


def get_recent_failures(
    limit: int = 20
) -> list[dict[str, Any]]:
    """Retourne les derniers DagRuns ou tâches ayant échoué."""

    failures: list[dict[str, Any]] = []

    for run in get_failed_dag_runs("~", limit=max(limit, 50)):
        dag_id = str(run.get("dag_id") or "")
        dag_run_id = str(run.get("dag_run_id") or "")

        failure = {
            "dag_id": dag_id,
            "dag_run_id": dag_run_id,
            "state": run.get("state"),
            "start_date": run.get("start_date"),
            "end_date": run.get("end_date"),
            "duration_seconds": get_run_duration_seconds(run),
            "failed_tasks": []
        }

        if dag_id and dag_run_id:
            try:
                failure["failed_tasks"] = get_failed_task_instances(
                    dag_id,
                    dag_run_id
                )

            except AirflowServiceError as error:
                logger.warning(
                    "Impossible de récupérer les tâches du run %s : %s",
                    dag_run_id,
                    error
                )

        failures.append(failure)

        if len(failures) >= limit:
            break

    return failures


# Utilitaires

def parse_datetime(value: Any) -> datetime | None:
    """Convertit une date Airflow ISO en datetime."""

    if not value:
        return None

    if isinstance(value, datetime):
        return value

    normalized_value = str(value).strip()

    if normalized_value.endswith("Z"):
        normalized_value = f"{normalized_value[:-1]}+00:00"

    try:
        return datetime.fromisoformat(normalized_value)

    except ValueError:
        return None


def get_run_duration_seconds(
    run: dict[str, Any] | None
) -> float | None:
    """Calcule la durée d'un DagRun."""

    if not run:
        return None

    direct_duration = run.get("duration")

    if direct_duration is not None:
        try:
            return round(float(direct_duration), 3)

        except (TypeError, ValueError):
            pass

    start_date = parse_datetime(
        run.get("start_date")
        or run.get("queued_at")
        or run.get("logical_date")
    )

    end_date = parse_datetime(
        run.get("end_date")
    )

    if start_date is None:
        return None

    if end_date is None:
        state = str(run.get("state") or "").lower()

        if state not in TERMINAL_DAG_RUN_STATES:
            end_date = datetime.now(timezone.utc)
        else:
            return None

    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)

    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    return round(
        max(0.0, (end_date - start_date).total_seconds()),
        3
    )