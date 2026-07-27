"""Utilitaires communs aux services du dashboard CheckIt.AI.

Ce module centralise les fonctions génériques partagées par les services
Airflow et PostgreSQL du dashboard.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


# Calculs

def calculate_percentage(
    value: int | float,
    total: int | float
) -> float:
    """Calcule un pourcentage arrondi à deux décimales."""

    if total <= 0:
        return 0.0

    return round(value * 100 / total, 2)


# Pagination

def normalize_limit(
    value: int,
    *,
    minimum: int = 1,
    maximum: int = 1000
) -> int:
    """Limite une valeur à l'intervalle de pagination autorisé."""

    if minimum > maximum:
        raise ValueError(
            "La limite minimale ne peut pas dépasser "
            "la limite maximale."
        )

    return max(
        minimum,
        min(int(value), maximum)
    )


def normalize_offset(value: int) -> int:
    """Retourne un offset positif ou nul."""

    return max(0, int(value))


# Dates

def parse_datetime(value: Any) -> datetime | None:
    """Convertit une date ISO en objet datetime."""

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


def calculate_duration_seconds(
    start_value: Any,
    end_value: Any = None,
    *,
    use_current_time: bool = False
) -> float | None:
    """Calcule une durée en secondes entre deux dates."""

    start_date = parse_datetime(start_value)

    if start_date is None:
        return None

    end_date = parse_datetime(end_value)

    if end_date is None:
        if not use_current_time:
            return None

        end_date = datetime.now(timezone.utc)

    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)

    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    return round(
        max(
            0.0,
            (end_date - start_date).total_seconds()
        ),
        3
    )