"""Service PostgreSQL du dashboard CheckIt.AI.

Ce module fournit les données nécessaires aux pages du dashboard :

- vérification de la connexion PostgreSQL ;
- indicateurs globaux de la base ;
- suivi des exécutions du pipeline ;
- statistiques sur les sources ;
- contrôle du contenu des tables ;
- consultation paginée des articles.

Toutes les requêtes sont en lecture seule.
Le chargement des données reste géré par les services PostgreSQL du pipeline.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor

from dashboard.services.dashboard_service_utils import (
    calculate_percentage,
    normalize_limit,
    normalize_offset
)
from src.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Configuration
# ============================================================================

DATABASE_SCHEMA = os.getenv(
    "CHECKIT_DATABASE_SCHEMA",
    "checkit"
).strip() or "checkit"

DATABASE_HOST = os.getenv(
    "CHECKIT_POSTGRES_HOST",
    os.getenv("POSTGRES_HOST", "localhost")
).strip() or "localhost"

DATABASE_PORT = int(
    os.getenv(
        "CHECKIT_POSTGRES_PORT",
        os.getenv("POSTGRES_PORT", "5432")
    )
)

DATABASE_NAME = os.getenv(
    "CHECKIT_POSTGRES_DATABASE",
    os.getenv("POSTGRES_DB", "checkit")
).strip() or "checkit"

DATABASE_USER = os.getenv(
    "CHECKIT_POSTGRES_USER",
    os.getenv("POSTGRES_USER", "checkit_et1")
).strip() or "checkit_et1"

DATABASE_PASSWORD = os.getenv(
    "CHECKIT_POSTGRES_PASSWORD",
    os.getenv("POSTGRES_PASSWORD", "")
)

DATABASE_CONNECT_TIMEOUT = int(
    os.getenv("CHECKIT_POSTGRES_CONNECT_TIMEOUT", "5")
)

ALLOWED_TABLES = {
    "sources",
    "pipeline_runs",
    "articles",
    "images",
    "article_labels",
    "article_features",
    "model_predictions"
}

ALLOWED_ARTICLE_SORT_COLUMNS = {
    "published_at",
    "extracted_at",
    "transformed_at",
    "created_at",
    "updated_at",
    "title",
    "language",
    "data_quality_status"
}

ALLOWED_SORT_DIRECTIONS = {"ASC", "DESC"}


# ============================================================================
# Connexion
# ============================================================================

def create_connection() -> Connection:
    """Crée une connexion PostgreSQL dédiée au dashboard."""

    connection = psycopg2.connect(
        host=DATABASE_HOST,
        port=DATABASE_PORT,
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        connect_timeout=DATABASE_CONNECT_TIMEOUT,
        application_name="checkit_dashboard"
    )

    connection.set_session(readonly=True, autocommit=True)

    with connection.cursor() as cursor:
        cursor.execute(
            f"SET search_path TO {DATABASE_SCHEMA}, public;"
        )

    return connection


@contextmanager
def get_connection() -> Iterator[Connection]:
    """Ouvre puis ferme automatiquement une connexion PostgreSQL."""

    connection: Connection | None = None

    try:
        connection = create_connection()
        yield connection

    except Exception:
        logger.exception(
            "Erreur pendant l'accès PostgreSQL du dashboard."
        )
        raise

    finally:
        if connection is not None and not connection.closed:
            connection.close()


def execute_query(
    query: str,
    parameters: Sequence[Any] | Mapping[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Exécute une requête SELECT et retourne une liste de dictionnaires."""

    normalized_query = query.strip().lower()

    if not (
        normalized_query.startswith("select")
        or normalized_query.startswith("with")
    ):
        raise ValueError(
            "Le service PostgreSQL du dashboard accepte "
            "uniquement les requêtes de lecture."
        )

    with get_connection() as connection:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute(query, parameters)
            return [dict(row) for row in cursor.fetchall()]


def execute_scalar(
    query: str,
    parameters: Sequence[Any] | Mapping[str, Any] | None = None,
    default: Any = None
) -> Any:
    """Retourne la première valeur de la première ligne d'une requête."""

    rows = execute_query(query, parameters)

    if not rows:
        return default

    return next(iter(rows[0].values()), default)


# ============================================================================
# État de la connexion
# ============================================================================

def test_connection() -> dict[str, Any]:
    """Teste la connexion et retourne son contexte PostgreSQL."""

    rows = execute_query(
        """
        SELECT
            current_database() AS database,
            current_user AS database_user,
            current_schema() AS schema,
            version() AS version,
            CURRENT_TIMESTAMP AS checked_at;
        """
    )

    if not rows:
        raise RuntimeError(
            "PostgreSQL n'a retourné aucune information de connexion."
        )

    result = rows[0]

    return {
        "status": "success",
        "host": DATABASE_HOST,
        "port": DATABASE_PORT,
        **result
    }


def is_database_available() -> bool:
    """Indique si PostgreSQL est accessible."""

    try:
        return execute_scalar("SELECT TRUE;", default=False) is True

    except Exception as error:
        logger.warning(
            "PostgreSQL indisponible pour le dashboard : %s",
            error
        )
        return False


# ============================================================================
# Indicateurs globaux
# ============================================================================

def get_table_counts() -> dict[str, int]:
    """Retourne le nombre de lignes des principales tables."""

    rows = execute_query(
        f"""
        SELECT 'sources' AS table_name, COUNT(*) AS row_count
        FROM {DATABASE_SCHEMA}.sources

        UNION ALL

        SELECT 'pipeline_runs', COUNT(*)
        FROM {DATABASE_SCHEMA}.pipeline_runs

        UNION ALL

        SELECT 'articles', COUNT(*)
        FROM {DATABASE_SCHEMA}.articles

        UNION ALL

        SELECT 'images', COUNT(*)
        FROM {DATABASE_SCHEMA}.images

        UNION ALL

        SELECT 'article_labels', COUNT(*)
        FROM {DATABASE_SCHEMA}.article_labels

        UNION ALL

        SELECT 'article_features', COUNT(*)
        FROM {DATABASE_SCHEMA}.article_features

        UNION ALL

        SELECT 'model_predictions', COUNT(*)
        FROM {DATABASE_SCHEMA}.model_predictions;
        """
    )

    return {
        str(row["table_name"]): int(row["row_count"])
        for row in rows
    }


def get_database_overview() -> dict[str, Any]:
    """Construit les principaux KPI du dashboard."""

    counts = get_table_counts()
    article_count = counts.get("articles", 0)
    image_count = counts.get("images", 0)
    label_count = counts.get("article_labels", 0)
    feature_count = counts.get("article_features", 0)

    return {
        **counts,
        "image_coverage": calculate_percentage(
            image_count,
            article_count
        ),
        "label_coverage": calculate_percentage(
            label_count,
            article_count
        ),
        "feature_coverage": calculate_percentage(
            feature_count,
            article_count
        )
    }


def get_database_size() -> dict[str, Any]:
    """Retourne la taille occupée par la base PostgreSQL."""

    rows = execute_query(
        """
        SELECT
            pg_database_size(current_database()) AS size_bytes,
            pg_size_pretty(
                pg_database_size(current_database())
            ) AS formatted_size;
        """
    )

    return rows[0] if rows else {
        "size_bytes": 0,
        "formatted_size": "0 bytes"
    }



# ============================================================================
# Suivi des pipelines
# ============================================================================

def get_latest_pipeline_run() -> dict[str, Any] | None:
    """Retourne la dernière exécution enregistrée."""

    rows = execute_query(
        f"""
        SELECT
            id,
            dag_id,
            airflow_run_id,
            pipeline_name,
            pipeline_version,
            status,
            started_at,
            finished_at,
            duration_seconds,
            extraction_duration_seconds,
            transformation_duration_seconds,
            load_duration_seconds,
            extracted_count,
            transformed_count,
            valid_count,
            rejected_count,
            loaded_count,
            images_downloaded_count,
            images_valid_count,
            images_invalid_count,
            error_message,
            run_metadata
        FROM {DATABASE_SCHEMA}.pipeline_runs
        ORDER BY started_at DESC
        LIMIT 1;
        """
    )

    return rows[0] if rows else None


def get_pipeline_runs(limit: int = 50) -> list[dict[str, Any]]:
    """Retourne l'historique récent des exécutions."""

    safe_limit = normalize_limit(limit, maximum=500)

    return execute_query(
        f"""
        SELECT
            id,
            dag_id,
            airflow_run_id,
            status,
            started_at,
            finished_at,
            duration_seconds,
            extraction_duration_seconds,
            transformation_duration_seconds,
            load_duration_seconds,
            extracted_count,
            transformed_count,
            valid_count,
            rejected_count,
            loaded_count,
            images_valid_count,
            images_invalid_count,
            error_message
        FROM {DATABASE_SCHEMA}.pipeline_runs
        ORDER BY started_at DESC
        LIMIT %s;
        """,
        (safe_limit,)
    )


def get_pipeline_summary() -> dict[str, Any]:
    """Retourne les statistiques générales des exécutions."""

    rows = execute_query(
        f"""
        SELECT
            COUNT(*) AS total_runs,
            COUNT(*) FILTER (
                WHERE status = 'success'
            ) AS successful_runs,
            COUNT(*) FILTER (
                WHERE status = 'failed'
            ) AS failed_runs,
            COUNT(*) FILTER (
                WHERE status = 'running'
            ) AS running_runs,
            ROUND(
                AVG(duration_seconds)::NUMERIC,
                3
            ) AS average_duration_seconds,
            ROUND(
                MAX(duration_seconds)::NUMERIC,
                3
            ) AS maximum_duration_seconds,
            MAX(started_at) AS latest_started_at
        FROM {DATABASE_SCHEMA}.pipeline_runs;
        """
    )

    if not rows:
        return {}

    result = rows[0]
    total_runs = int(result.get("total_runs") or 0)
    successful_runs = int(result.get("successful_runs") or 0)

    result["success_rate"] = calculate_percentage(
        successful_runs,
        total_runs
    )

    return result


def get_latest_run_content() -> dict[str, Any]:
    """Compte les entités associées au dernier pipeline_run."""

    rows = execute_query(
        f"""
        WITH latest_run AS (
            SELECT id, status, started_at, finished_at
            FROM {DATABASE_SCHEMA}.pipeline_runs
            ORDER BY started_at DESC
            LIMIT 1
        )
        SELECT
            run.id AS pipeline_run_id,
            run.status,
            run.started_at,
            run.finished_at,
            COUNT(DISTINCT article.id) AS articles,
            COUNT(DISTINCT image.id) AS images,
            COUNT(DISTINCT label.id) AS labels,
            COUNT(DISTINCT feature.id) AS features,
            COUNT(DISTINCT prediction.id) AS predictions
        FROM latest_run AS run
        LEFT JOIN {DATABASE_SCHEMA}.articles AS article
            ON article.pipeline_run_id = run.id
        LEFT JOIN {DATABASE_SCHEMA}.images AS image
            ON image.article_id = article.id
        LEFT JOIN {DATABASE_SCHEMA}.article_labels AS label
            ON label.article_id = article.id
        LEFT JOIN {DATABASE_SCHEMA}.article_features AS feature
            ON feature.article_id = article.id
        LEFT JOIN {DATABASE_SCHEMA}.model_predictions AS prediction
            ON prediction.pipeline_run_id = run.id
        GROUP BY
            run.id,
            run.status,
            run.started_at,
            run.finished_at;
        """
    )

    return rows[0] if rows else {}


def get_recent_pipeline_errors(
    limit: int = 20
) -> list[dict[str, Any]]:
    """Retourne les dernières exécutions ayant une erreur."""

    safe_limit = normalize_limit(limit, maximum=200)

    return execute_query(
        f"""
        SELECT
            id,
            dag_id,
            airflow_run_id,
            status,
            started_at,
            finished_at,
            error_message
        FROM {DATABASE_SCHEMA}.pipeline_runs
        WHERE
            status = 'failed'
            OR NULLIF(BTRIM(error_message), '') IS NOT NULL
        ORDER BY started_at DESC
        LIMIT %s;
        """,
        (safe_limit,)
    )


# ============================================================================
# Statistiques sur les sources
# ============================================================================

def get_sources_summary() -> list[dict[str, Any]]:
    """Retourne les volumes et dates de collecte par source."""

    return execute_query(
        f"""
        SELECT
            source.id,
            source.source_key,
            source.display_name,
            source.source_type,
            source.default_language,
            source.is_active,
            COUNT(article.id) AS article_count,
            COUNT(image.id) AS image_count,
            COUNT(label.id) AS label_count,
            MAX(article.extracted_at) AS latest_extraction
        FROM {DATABASE_SCHEMA}.sources AS source
        LEFT JOIN {DATABASE_SCHEMA}.articles AS article
            ON article.source_id = source.id
        LEFT JOIN {DATABASE_SCHEMA}.images AS image
            ON image.article_id = article.id
        LEFT JOIN {DATABASE_SCHEMA}.article_labels AS label
            ON label.article_id = article.id
        GROUP BY
            source.id,
            source.source_key,
            source.display_name,
            source.source_type,
            source.default_language,
            source.is_active
        ORDER BY article_count DESC, source.display_name;
        """
    )


def get_source_type_distribution() -> list[dict[str, Any]]:
    """Compte les articles par type de source."""

    return execute_query(
        f"""
        SELECT
            source.source_type,
            COUNT(article.id) AS article_count
        FROM {DATABASE_SCHEMA}.sources AS source
        LEFT JOIN {DATABASE_SCHEMA}.articles AS article
            ON article.source_id = source.id
        GROUP BY source.source_type
        ORDER BY article_count DESC;
        """
    )


# ============================================================================
# Qualité et contenu
# ============================================================================

def get_quality_summary() -> list[dict[str, Any]]:
    """Compte les articles par statut qualité."""

    return execute_query(
        f"""
        SELECT
            data_quality_status,
            COUNT(*) AS article_count
        FROM {DATABASE_SCHEMA}.articles
        GROUP BY data_quality_status
        ORDER BY article_count DESC;
        """
    )


def get_language_distribution(
    limit: int = 20
) -> list[dict[str, Any]]:
    """Retourne les principales langues des articles."""

    safe_limit = normalize_limit(limit, maximum=100)

    return execute_query(
        f"""
        SELECT
            COALESCE(NULLIF(language, ''), 'unknown') AS language,
            COUNT(*) AS article_count
        FROM {DATABASE_SCHEMA}.articles
        GROUP BY COALESCE(NULLIF(language, ''), 'unknown')
        ORDER BY article_count DESC
        LIMIT %s;
        """,
        (safe_limit,)
    )


def get_label_distribution() -> list[dict[str, Any]]:
    """Retourne la répartition des labels actifs."""

    return execute_query(
        f"""
        SELECT
            label,
            label_type,
            COUNT(*) AS label_count
        FROM {DATABASE_SCHEMA}.article_labels
        WHERE is_active = TRUE
        GROUP BY label, label_type
        ORDER BY label_count DESC, label;
        """
    )


def get_image_quality_summary() -> list[dict[str, Any]]:
    """Retourne les statuts de validation des images."""

    return execute_query(
        f"""
        SELECT
            validation_status,
            is_valid,
            COUNT(*) AS image_count
        FROM {DATABASE_SCHEMA}.images
        GROUP BY validation_status, is_valid
        ORDER BY image_count DESC;
        """
    )


def get_feature_distribution() -> list[dict[str, Any]]:
    """Retourne les volumes de features par famille."""

    return execute_query(
        f"""
        SELECT
            feature_group,
            feature_name,
            feature_type,
            COUNT(*) AS feature_count
        FROM {DATABASE_SCHEMA}.article_features
        GROUP BY
            feature_group,
            feature_name,
            feature_type
        ORDER BY feature_count DESC, feature_name;
        """
    )


def get_daily_article_counts(
    days: int = 30
) -> list[dict[str, Any]]:
    """Retourne le nombre d'articles collectés par jour."""

    safe_days = normalize_limit(days, maximum=3650)

    return execute_query(
        f"""
        SELECT
            DATE(extracted_at) AS extraction_date,
            COUNT(*) AS article_count
        FROM {DATABASE_SCHEMA}.articles
        WHERE extracted_at >= CURRENT_DATE - %s
        GROUP BY DATE(extracted_at)
        ORDER BY extraction_date;
        """,
        (safe_days,)
    )


def get_data_completeness() -> dict[str, Any]:
    """Mesure la présence des principaux champs métier."""

    rows = execute_query(
        f"""
        SELECT
            COUNT(*) AS total_articles,
            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(content), '') IS NOT NULL
            ) AS with_content,
            COUNT(*) FILTER (
                WHERE published_at IS NOT NULL
            ) AS with_publication_date,
            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(author), '') IS NOT NULL
            ) AS with_author,
            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(canonical_url), '') IS NOT NULL
            ) AS with_url,
            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(language), '') IS NOT NULL
            ) AS with_language,
            COUNT(*) FILTER (
                WHERE EXISTS (
                    SELECT 1
                    FROM {DATABASE_SCHEMA}.images AS image
                    WHERE image.article_id = articles.id
                )
            ) AS with_image,
            COUNT(*) FILTER (
                WHERE EXISTS (
                    SELECT 1
                    FROM {DATABASE_SCHEMA}.article_labels AS label
                    WHERE label.article_id = articles.id
                      AND label.is_active = TRUE
                )
            ) AS with_label,
            COUNT(*) FILTER (
                WHERE EXISTS (
                    SELECT 1
                    FROM {DATABASE_SCHEMA}.article_features AS feature
                    WHERE feature.article_id = articles.id
                )
            ) AS with_feature
        FROM {DATABASE_SCHEMA}.articles;
        """
    )

    if not rows:
        return {}

    result = rows[0]
    total = int(result.get("total_articles") or 0)

    for field in (
        "with_content",
        "with_publication_date",
        "with_author",
        "with_url",
        "with_language",
        "with_image",
        "with_label",
        "with_feature"
    ):
        result[f"{field}_rate"] = calculate_percentage(
            int(result.get(field) or 0),
            total
        )

    return result


# ============================================================================
# Consultation des articles
# ============================================================================

def get_articles(
    *,
    limit: int = 50,
    offset: int = 0,
    source_key: str | None = None,
    language: str | None = None,
    label: str | None = None,
    quality_status: str | None = None,
    search: str | None = None,
    sort_by: str = "extracted_at",
    sort_direction: str = "DESC"
) -> list[dict[str, Any]]:
    """Retourne une page d'articles avec filtres facultatifs."""

    safe_limit = normalize_limit(limit, maximum=500)
    safe_offset = normalize_offset(offset)
    safe_sort = (
        sort_by
        if sort_by in ALLOWED_ARTICLE_SORT_COLUMNS
        else "extracted_at"
    )
    safe_direction = sort_direction.strip().upper()

    if safe_direction not in ALLOWED_SORT_DIRECTIONS:
        safe_direction = "DESC"

    conditions = ["TRUE"]
    parameters: list[Any] = []

    if source_key:
        conditions.append("source.source_key = %s")
        parameters.append(source_key)

    if language:
        conditions.append("article.language = %s")
        parameters.append(language)

    if label:
        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM checkit.article_labels AS filtered_label
                WHERE filtered_label.article_id = article.id
                  AND filtered_label.label = %s
                  AND filtered_label.is_active = TRUE
            )
            """
        )
        parameters.append(label)

    if quality_status:
        conditions.append("article.data_quality_status = %s")
        parameters.append(quality_status)

    if search:
        conditions.append(
            """
            (
                article.title ILIKE %s
                OR article.content ILIKE %s
                OR article.author ILIKE %s
            )
            """
        )
        search_pattern = f"%{search.strip()}%"
        parameters.extend([
            search_pattern,
            search_pattern,
            search_pattern
        ])

    parameters.extend([safe_limit, safe_offset])

    return execute_query(
        f"""
        SELECT
            article.id,
            source.source_key,
            source.display_name AS source_name,
            article.title,
            article.author,
            article.language,
            article.category,
            article.dataset_role,
            article.data_quality_status,
            article.published_at,
            article.extracted_at,
            article.canonical_url,
            EXISTS (
                SELECT 1
                FROM {DATABASE_SCHEMA}.images AS image
                WHERE image.article_id = article.id
            ) AS has_image,
            EXISTS (
                SELECT 1
                FROM {DATABASE_SCHEMA}.article_labels AS article_label
                WHERE article_label.article_id = article.id
                  AND article_label.is_active = TRUE
            ) AS has_label
        FROM {DATABASE_SCHEMA}.articles AS article
        JOIN {DATABASE_SCHEMA}.sources AS source
            ON source.id = article.source_id
        WHERE {" AND ".join(conditions)}
        ORDER BY article.{safe_sort} {safe_direction} NULLS LAST
        LIMIT %s
        OFFSET %s;
        """,
        parameters
    )


def count_articles(
    *,
    source_key: str | None = None,
    language: str | None = None,
    quality_status: str | None = None
) -> int:
    """Compte les articles correspondant aux filtres principaux."""

    conditions = ["TRUE"]
    parameters: list[Any] = []

    if source_key:
        conditions.append("source.source_key = %s")
        parameters.append(source_key)

    if language:
        conditions.append("article.language = %s")
        parameters.append(language)

    if quality_status:
        conditions.append("article.data_quality_status = %s")
        parameters.append(quality_status)

    result = execute_scalar(
        f"""
        SELECT COUNT(*)
        FROM {DATABASE_SCHEMA}.articles AS article
        JOIN {DATABASE_SCHEMA}.sources AS source
            ON source.id = article.source_id
        WHERE {" AND ".join(conditions)};
        """,
        parameters,
        default=0
    )

    return int(result or 0)


def get_article_details(
    article_id: str
) -> dict[str, Any] | None:
    """Retourne un article avec son image, ses labels et ses features."""

    articles = execute_query(
        f"""
        SELECT
            article.*,
            source.source_key,
            source.display_name AS source_name,
            source.source_type
        FROM {DATABASE_SCHEMA}.articles AS article
        JOIN {DATABASE_SCHEMA}.sources AS source
            ON source.id = article.source_id
        WHERE article.id = %s
        LIMIT 1;
        """,
        (article_id,)
    )

    if not articles:
        return None

    article = articles[0]

    article["images"] = execute_query(
        f"""
        SELECT *
        FROM {DATABASE_SCHEMA}.images
        WHERE article_id = %s
        ORDER BY is_primary DESC, image_position;
        """,
        (article_id,)
    )

    article["labels"] = execute_query(
        f"""
        SELECT *
        FROM {DATABASE_SCHEMA}.article_labels
        WHERE article_id = %s
        ORDER BY is_active DESC, labeled_at DESC;
        """,
        (article_id,)
    )

    article["features"] = execute_query(
        f"""
        SELECT *
        FROM {DATABASE_SCHEMA}.article_features
        WHERE article_id = %s
        ORDER BY feature_group, feature_name;
        """,
        (article_id,)
    )

    article["predictions"] = execute_query(
        f"""
        SELECT *
        FROM {DATABASE_SCHEMA}.model_predictions
        WHERE article_id = %s
        ORDER BY predicted_at DESC;
        """,
        (article_id,)
    )

    return article


# ============================================================================
# Consultation générique contrôlée
# ============================================================================

def get_table_preview(
    table_name: str,
    limit: int = 100
) -> list[dict[str, Any]]:
    """Retourne un aperçu sécurisé d'une table autorisée."""

    if table_name not in ALLOWED_TABLES:
        raise ValueError(
            f"Table non autorisée : {table_name!r}."
        )

    safe_limit = normalize_limit(limit, maximum=500)

    return execute_query(
        f"""
        SELECT *
        FROM {DATABASE_SCHEMA}.{table_name}
        LIMIT %s;
        """,
        (safe_limit,)
    )
# ============================================================================
# Complétude des données
# ============================================================================

def get_data_completeness_by_source() -> list[dict[str, Any]]:
    """Retourne la complétude des articles pour chaque source."""

    query = """
        SELECT
            s.source_key,
            COALESCE(s.display_name, s.source_key, 'unknown') AS display_name,
            COALESCE(s.source_type, 'unknown') AS source_type,
            COUNT(*) AS article_count,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(a.content), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS content_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE a.published_at IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS publication_date_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(a.author), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS author_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(
                        BTRIM(
                            COALESCE(
                                a.canonical_url,
                                a.original_url
                            )
                        ),
                        ''
                    ) IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS url_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(a.language), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS language_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE EXISTS (
                        SELECT 1
                        FROM checkit.images i
                        WHERE i.article_id = a.id
                        AND i.is_valid IS TRUE
                    )
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS image_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE EXISTS (
                        SELECT 1
                        FROM checkit.article_labels al
                        WHERE al.article_id = a.id
                    )
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS label_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE EXISTS (
                        SELECT 1
                        FROM checkit.article_features af
                        WHERE af.article_id = a.id
                    )
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS feature_rate

        FROM checkit.articles a

        LEFT JOIN checkit.sources s
            ON s.id = a.source_id

        GROUP BY
            s.source_key,
            s.display_name,
            s.source_type

        ORDER BY
            article_count DESC,
            s.source_key
    """

    return execute_query(query)

def get_data_completeness_by_source_type() -> list[dict[str, Any]]:
    """Retourne la complétude des articles par type de source."""

    query = """
        SELECT
            COALESCE(s.source_type, 'unknown') AS source_type,
            COUNT(*) AS article_count,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(a.content), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS content_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE a.published_at IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS publication_date_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(a.author), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS author_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(
                        BTRIM(
                            COALESCE(
                                a.canonical_url,
                                a.original_url
                            )
                        ),
                        ''
                    ) IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS url_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(a.language), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS language_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE EXISTS (
                        SELECT 1
                        FROM checkit.images i
                        WHERE i.article_id = a.id
                        AND i.is_valid IS TRUE
                    )
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS image_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE EXISTS (
                        SELECT 1
                        FROM checkit.article_labels al
                        WHERE al.article_id = a.id
                    )
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS label_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE EXISTS (
                        SELECT 1
                        FROM checkit.article_features af
                        WHERE af.article_id = a.id
                    )
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS feature_rate

        FROM checkit.articles a

        LEFT JOIN checkit.sources s
            ON s.id = a.source_id

        GROUP BY
            COALESCE(s.source_type, 'unknown')

        ORDER BY
            article_count DESC,
            source_type
    """

    return execute_query(query)

def get_image_completeness() -> dict[str, Any]:
    """Retourne la complétude technique des images enregistrées."""

    query = """
        SELECT
            COUNT(*) AS total_images,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(remote_url), '') IS NOT NULL
            ) AS with_remote_url,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(local_path), '') IS NOT NULL
            ) AS with_local_path,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(file_name), '') IS NOT NULL
            ) AS with_file_name,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(file_extension), '') IS NOT NULL
            ) AS with_file_extension,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(file_format), '') IS NOT NULL
            ) AS with_file_format,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(mime_type), '') IS NOT NULL
            ) AS with_mime_type,

            COUNT(*) FILTER (
                WHERE width IS NOT NULL
            ) AS with_width,

            COUNT(*) FILTER (
                WHERE height IS NOT NULL
            ) AS with_height,

            COUNT(*) FILTER (
                WHERE size_bytes IS NOT NULL
            ) AS with_size_bytes,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(file_hash), '') IS NOT NULL
            ) AS with_file_hash,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(perceptual_hash), '') IS NOT NULL
            ) AS with_perceptual_hash,

            COUNT(*) FILTER (
                WHERE download_duration_ms IS NOT NULL
            ) AS with_download_duration,

            COUNT(*) FILTER (
                WHERE blur_score IS NOT NULL
            ) AS with_blur_score,

            COUNT(*) FILTER (
                WHERE brightness_score IS NOT NULL
            ) AS with_brightness_score,

            COUNT(*) FILTER (
                WHERE entropy_score IS NOT NULL
            ) AS with_entropy_score,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(remote_url), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_remote_url_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(local_path), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_local_path_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(file_name), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_file_name_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(file_extension), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_file_extension_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(file_format), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_file_format_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(mime_type), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_mime_type_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE width IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_width_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE height IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_height_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE size_bytes IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_size_bytes_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(file_hash), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_file_hash_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(perceptual_hash), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_perceptual_hash_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE download_duration_ms IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_download_duration_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE blur_score IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_blur_score_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE brightness_score IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_brightness_score_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE entropy_score IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_entropy_score_rate

        FROM checkit.images
    """

    rows = execute_query(query)
    return rows[0] if rows else {}


def get_metadata_completeness() -> dict[str, Any]:
    """Retourne la complétude des métadonnées éditoriales."""

    query = """
        SELECT
            COUNT(*) AS total_articles,

            COUNT(*) FILTER (
                WHERE source_id IS NOT NULL
            ) AS with_source,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(title), '') IS NOT NULL
            ) AS with_title,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(content), '') IS NOT NULL
            ) AS with_content,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(author), '') IS NOT NULL
            ) AS with_author,

            COUNT(*) FILTER (
                WHERE published_at IS NOT NULL
            ) AS with_publication_date,

            COUNT(*) FILTER (
                WHERE NULLIF(
                    BTRIM(
                        COALESCE(
                            canonical_url,
                            original_url
                        )
                    ),
                    ''
                ) IS NOT NULL
            ) AS with_url,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(language), '') IS NOT NULL
            ) AS with_language,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(category), '') IS NOT NULL
            ) AS with_category,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(dataset_role), '') IS NOT NULL
            ) AS with_role,

            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(data_quality_status), '') IS NOT NULL
            ) AS with_quality_status,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE source_id IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_source_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(title), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_title_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(content), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_content_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(author), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_author_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE published_at IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_publication_date_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(
                        BTRIM(
                            COALESCE(
                                canonical_url,
                                original_url
                            )
                        ),
                        ''
                    ) IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_url_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(language), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_language_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(category), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_category_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(dataset_role), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_role_rate,

            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE NULLIF(BTRIM(data_quality_status), '') IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS with_quality_status_rate

        FROM checkit.articles
    """

    rows = execute_query(query)
    return rows[0] if rows else {}