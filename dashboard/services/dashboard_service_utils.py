"""Utilitaires communs aux services du dashboard CheckIt.AI.

Ce module centralise les fonctions génériques utilisées par plusieurs
services du dashboard :

- calcul des pourcentages ;
- sécurisation des limites de pagination ;
- sécurisation des offsets de pagination.

Les fonctions métier propres à Airflow ou PostgreSQL restent dans leurs
services respectifs.
"""

from __future__ import annotations


# ============================================================================
# Calculs
# ============================================================================

def calculate_percentage(
    value: int | float,
    total: int | float
) -> float:
    """Calcule un pourcentage arrondi à deux décimales."""

    if total <= 0:
        return 0.0

    return round(value * 100 / total, 2)


# ============================================================================
# Pagination
# ============================================================================

def normalize_limit(
    value: int,
    *,
    minimum: int = 1,
    maximum: int = 1000
) -> int:
    """Ramène une limite de pagination dans l'intervalle autorisé."""

    if minimum > maximum:
        raise ValueError(
            "La limite minimale ne peut pas dépasser la limite maximale."
        )

    return max(minimum, min(int(value), maximum))


def normalize_offset(value: int) -> int:
    """Retourne un offset de pagination positif ou nul."""

    return max(0, int(value))