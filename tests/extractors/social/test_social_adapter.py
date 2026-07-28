"""Tests des contrats communs aux extracteurs sociaux."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import pytest

from src.extractors.social import social_adapter as module


# Fonctions simulées

def fake_iter_items(
    source: Mapping[str, Any],
    maximum_items: int
) -> Iterable[module.SocialItem]:
    del source, maximum_items
    return []


def fake_build_article(
    item: Any,
    identifier: str,
    context: Mapping[str, Any],
    source: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "item": item,
        "identifier": identifier,
        "context": dict(context),
        "source": dict(source)
    }


def fake_validate_item(
    item: Any,
    context: Mapping[str, Any],
    source: Mapping[str, Any]
) -> tuple[bool, str]:
    del item, context, source
    return True, ""


# SocialItem

def test_social_item_stores_required_values() -> None:
    item = object()
    context = {
        "community": "news"
    }

    social_item = module.SocialItem(
        identifier="abc123",
        item=item,
        context=context,
        rejection_reason="contenu supprimé"
    )

    assert social_item.identifier == "abc123"
    assert social_item.item is item
    assert social_item.context == context
    assert social_item.rejection_reason == "contenu supprimé"


def test_social_item_uses_empty_defaults() -> None:
    social_item = module.SocialItem(
        identifier="abc123",
        item={"title": "Publication"}
    )

    assert social_item.context == {}
    assert social_item.rejection_reason == ""


def test_social_item_context_default_is_independent() -> None:
    first = module.SocialItem(
        identifier="first",
        item={}
    )
    second = module.SocialItem(
        identifier="second",
        item={}
    )

    assert first.context == {}
    assert second.context == {}
    assert first.context is not second.context


def test_social_item_is_mutable() -> None:
    social_item = module.SocialItem(
        identifier="initial",
        item={}
    )

    social_item.identifier = "updated"
    social_item.rejection_reason = "invalide"

    assert social_item.identifier == "updated"
    assert social_item.rejection_reason == "invalide"


def test_social_item_rejects_unknown_attributes() -> None:
    social_item = module.SocialItem(
        identifier="abc123",
        item={}
    )

    with pytest.raises(AttributeError):
        social_item.unknown_attribute = "value"


# SocialAdapter

def test_social_adapter_stores_valid_configuration() -> None:
    adapter = module.SocialAdapter(
        source_id="reddit",
        default_name="Reddit",
        iter_items=fake_iter_items,
        build_article=fake_build_article,
        validate_item=fake_validate_item
    )

    assert adapter.source_id == "reddit"
    assert adapter.default_name == "Reddit"
    assert adapter.iter_items is fake_iter_items
    assert adapter.build_article is fake_build_article
    assert adapter.validate_item is fake_validate_item


def test_social_adapter_normalizes_source_id_and_default_name() -> None:
    adapter = module.SocialAdapter(
        source_id="  reddit  ",
        default_name="  Reddit News  ",
        iter_items=fake_iter_items,
        build_article=fake_build_article
    )

    assert adapter.source_id == "reddit"
    assert adapter.default_name == "Reddit News"


@pytest.mark.parametrize(
    "default_name",
    [
        "",
        "   ",
        None
    ]
)
def test_social_adapter_uses_source_id_as_default_name(
    default_name: Any
) -> None:
    adapter = module.SocialAdapter(
        source_id="reddit",
        default_name=default_name,
        iter_items=fake_iter_items,
        build_article=fake_build_article
    )

    assert adapter.default_name == "reddit"


@pytest.mark.parametrize(
    "source_id",
    [
        "",
        "   ",
        None
    ]
)
def test_social_adapter_rejects_empty_source_id(
    source_id: Any
) -> None:
    with pytest.raises(
        ValueError,
        match="L'identifiant d'un SocialAdapter ne peut pas être vide"
    ):
        module.SocialAdapter(
            source_id=source_id,
            default_name="Reddit",
            iter_items=fake_iter_items,
            build_article=fake_build_article
        )


@pytest.mark.parametrize(
    "iter_items",
    [
        None,
        "not-callable",
        42,
        {}
    ]
)
def test_social_adapter_rejects_invalid_iter_items(
    iter_items: Any
) -> None:
    with pytest.raises(
        TypeError,
        match="iter_items doit être une fonction appelable"
    ):
        module.SocialAdapter(
            source_id="reddit",
            default_name="Reddit",
            iter_items=iter_items,
            build_article=fake_build_article
        )


@pytest.mark.parametrize(
    "build_article",
    [
        None,
        "not-callable",
        42,
        []
    ]
)
def test_social_adapter_rejects_invalid_build_article(
    build_article: Any
) -> None:
    with pytest.raises(
        TypeError,
        match="build_article doit être une fonction appelable"
    ):
        module.SocialAdapter(
            source_id="reddit",
            default_name="Reddit",
            iter_items=fake_iter_items,
            build_article=build_article
        )


@pytest.mark.parametrize(
    "validate_item",
    [
        "not-callable",
        42,
        [],
        {}
    ]
)
def test_social_adapter_rejects_invalid_validate_item(
    validate_item: Any
) -> None:
    with pytest.raises(
        TypeError,
        match="validate_item doit être une fonction appelable ou None"
    ):
        module.SocialAdapter(
            source_id="reddit",
            default_name="Reddit",
            iter_items=fake_iter_items,
            build_article=fake_build_article,
            validate_item=validate_item
        )


def test_social_adapter_accepts_none_validator() -> None:
    adapter = module.SocialAdapter(
        source_id="reddit",
        default_name="Reddit",
        iter_items=fake_iter_items,
        build_article=fake_build_article,
        validate_item=None
    )

    assert adapter.validate_item is None


def test_social_adapter_is_frozen() -> None:
    adapter = module.SocialAdapter(
        source_id="reddit",
        default_name="Reddit",
        iter_items=fake_iter_items,
        build_article=fake_build_article
    )

    with pytest.raises(AttributeError):
        adapter.source_id = "mastodon"


def test_social_adapter_rejects_unknown_attributes() -> None:
    adapter = module.SocialAdapter(
        source_id="reddit",
        default_name="Reddit",
        iter_items=fake_iter_items,
        build_article=fake_build_article
    )

    with pytest.raises((AttributeError, TypeError)):
        adapter.unknown_attribute = "value"