"""Contrats communs aux extracteurs de réseaux sociaux."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from src.utils.extractor_utils import normalize_value

SocialIterator = Callable[[Mapping[str, Any], int], Iterable["SocialItem"]]
SocialArticleBuilder = Callable[[Any, str, Mapping[str, Any], Mapping[str, Any]], dict[str, Any]]
SocialItemValidator = Callable[[Any, Mapping[str, Any], Mapping[str, Any]], tuple[bool, str]]


@dataclass(slots=True)
class SocialItem:
    """Élément brut produit par un extracteur social."""

    identifier: str
    item: Any
    context: Mapping[str, Any] = field(default_factory=dict)
    rejection_reason: str = ""


@dataclass(frozen=True, slots=True)
class SocialAdapter:
    """Décrit les fonctions propres à une source sociale."""

    source_id: str
    default_name: str
    iter_items: SocialIterator
    build_article: SocialArticleBuilder
    validate_item: SocialItemValidator | None = None

    def __post_init__(self) -> None:
        """Normalise et valide l'adaptateur social."""

        source_id = normalize_value(self.source_id)
        default_name = normalize_value(self.default_name) or source_id

        if not source_id:
            raise ValueError("L'identifiant d'un SocialAdapter ne peut pas être vide.")
        if not callable(self.iter_items):
            raise TypeError("iter_items doit être une fonction appelable.")
        if not callable(self.build_article):
            raise TypeError("build_article doit être une fonction appelable.")
        if self.validate_item is not None and not callable(self.validate_item):
            raise TypeError("validate_item doit être une fonction appelable ou None.")

        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "default_name", default_name)