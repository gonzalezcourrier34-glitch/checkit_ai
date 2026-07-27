"""Utilitaires communs aux services du dashboard CheckIt.AI.

Ce module centralise les fonctions génériques partagées par les services
Airflow et PostgreSQL du dashboard.
"""

from __future__ import annotations


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