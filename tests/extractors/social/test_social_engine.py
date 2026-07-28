"""Tests du moteur générique des extracteurs sociaux."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pytest

from src.extractors.social import social_engine as module
from src.extractors.social.social_adapter import SocialAdapter, SocialItem
from src.extractors.social.social_context import SocialExtractionContext


# Fonctions simulées

def fake_iter_items(
    source: Mapping[str, Any],
    maximum_articles: int
) -> Iterable[SocialItem]:
    del source, maximum_articles
    return []


def fake_build_article(
    item: Any,
    identifier: str,
    source: Mapping[str, Any],
    context: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "item": item,
        "identifier": identifier,
        "source": source.get("source_id", ""),
        "context": dict(context)
    }


def build_adapter(
    validate_item: Any = None,
    build_article: Any = fake_build_article,
    iter_items: Any = fake_iter_items
) -> SocialAdapter:
    """Construit un adaptateur social minimal valide."""

    return SocialAdapter(
        source_id="reddit",
        default_name="Reddit",
        iter_items=iter_items,
        build_article=build_article,
        validate_item=validate_item
    )


def build_context(
    *,
    maximum_articles: int = 10,
    remove_duplicates: bool = True
) -> SocialExtractionContext:
    """Construit un contexte d'extraction social minimal."""

    return SocialExtractionContext(
        source={
            "source_id": "reddit",
            "name": "Reddit"
        },
        maximum_articles=maximum_articles,
        max_article_age_days=30,
        filters={
            "require_title": True
        },
        remove_duplicates=remove_duplicates
    )


# Initialisation

def test_social_extractor_normalizes_section_name() -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        section_name="  custom_social  ",
        sources_file=Path("sources.yaml")
    )

    assert extractor.section_name == "custom_social"


@pytest.mark.parametrize(
    "section_name",
    [
        "",
        "   ",
        None
    ]
)
def test_social_extractor_uses_default_section_name(
    section_name: Any
) -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        section_name=section_name,
        sources_file=Path("sources.yaml")
    )

    assert extractor.section_name == "social_sources"


def test_social_extractor_rejects_invalid_adapter() -> None:
    with pytest.raises(
        TypeError,
        match="adapter doit être une instance de SocialAdapter"
    ):
        module.SocialExtractor(
            adapter=object(),
            sources_file=Path("sources.yaml")
        )


def test_social_extractor_requires_sources_file() -> None:
    with pytest.raises(
        ValueError,
        match="Le fichier de configuration des sources est requis"
    ):
        module.SocialExtractor(
            adapter=build_adapter(),
            sources_file=None
        )


def test_social_extractor_rejects_unknown_attributes() -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        sources_file=Path("sources.yaml")
    )

    with pytest.raises(AttributeError):
        extractor.unknown_attribute = "value"


# Configuration

def test_load_source_loads_and_caches_configuration(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        sources_file=Path("sources.yaml")
    )
    received: list[tuple[Path, str]] = []

    def fake_load_validated_source(
        sources_file: Path,
        source_id: str
    ) -> dict[str, Any]:
        received.append((sources_file, source_id))
        return {
            "source_id": source_id,
            "enabled": True
        }

    monkeypatch.setattr(
        module,
        "load_validated_source",
        fake_load_validated_source
    )

    first = extractor.load_source()
    second = extractor.load_source()

    assert first == {
        "source_id": "reddit",
        "enabled": True
    }
    assert second == first
    assert second is not first
    assert received == [
        (Path("sources.yaml"), "reddit")
    ]


def test_load_source_force_reload_ignores_cache(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        sources_file=Path("sources.yaml")
    )
    calls = 0

    def fake_load_validated_source(
        sources_file: Path,
        source_id: str
    ) -> dict[str, Any]:
        nonlocal calls
        del sources_file, source_id
        calls += 1
        return {
            "version": calls
        }

    monkeypatch.setattr(
        module,
        "load_validated_source",
        fake_load_validated_source
    )

    first = extractor.load_source()
    second = extractor.load_source(force_reload=True)

    assert first == {
        "version": 1
    }
    assert second == {
        "version": 2
    }


def test_reload_source_forces_reload(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        sources_file=Path("sources.yaml")
    )
    received: list[bool] = []

    def fake_load_source(
        self: module.SocialExtractor,
        force_reload: bool = False
    ) -> dict[str, Any]:
        del self
        received.append(force_reload)

        return {"enabled": True}

    monkeypatch.setattr(
        module.SocialExtractor,
        "load_source",
        fake_load_source
    )

    result = extractor.reload_source()

    assert result == {
        "enabled": True
    }
    assert received == [True]


def test_get_source_delegates_to_load_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        sources_file=Path("sources.yaml")
    )

    monkeypatch.setattr(
        module.SocialExtractor,
        "load_source",
        lambda self, force_reload=False: {
            "enabled": True
        }
    )

    assert extractor.get_source() == {
        "enabled": True
    }


def test_source_property_delegates_to_load_source(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        sources_file=Path("sources.yaml")
    )

    monkeypatch.setattr(
        module.SocialExtractor,
        "load_source",
        lambda self, force_reload=False: {
            "name": "Reddit"
        }
    )

    assert extractor.source == {
        "name": "Reddit"
    }


# Secrets

def test_secret_name_properties_normalize_values(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        sources_file=Path("sources.yaml")
    )

    monkeypatch.setattr(
        module.SocialExtractor,
        "load_source",
        lambda self, force_reload=False: {
            "client_id_secret_name": "  REDDIT_CLIENT_ID  ",
            "client_secret_secret_name": "  REDDIT_CLIENT_SECRET  "
        }
    )

    assert extractor.client_id_secret_name == "REDDIT_CLIENT_ID"
    assert extractor.client_secret_secret_name == "REDDIT_CLIENT_SECRET"


def test_client_id_resolves_secret(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        sources_file=Path("sources.yaml")
    )
    received: list[str] = []

    monkeypatch.setattr(
        module.SocialExtractor,
        "load_source",
        lambda self, force_reload=False: {
            "client_id_secret_name": "REDDIT_CLIENT_ID"
        }
    )

    def fake_get_secret(secret_name: str) -> str:
        received.append(secret_name)
        return "client-id"

    monkeypatch.setattr(
        module,
        "get_secret",
        fake_get_secret
    )

    assert extractor.client_id == "client-id"
    assert received == [
        "REDDIT_CLIENT_ID"
    ]


def test_client_secret_resolves_secret(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        sources_file=Path("sources.yaml")
    )
    received: list[str] = []

    monkeypatch.setattr(
        module.SocialExtractor,
        "load_source",
        lambda self, force_reload=False: {
            "client_secret_secret_name": "REDDIT_CLIENT_SECRET"
        }
    )

    def fake_get_secret(secret_name: str) -> str:
        received.append(secret_name)
        return "client-secret"

    monkeypatch.setattr(
        module,
        "get_secret",
        fake_get_secret
    )

    assert extractor.client_secret == "client-secret"
    assert received == [
        "REDDIT_CLIENT_SECRET"
    ]


def test_secret_properties_return_empty_string_without_name(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    extractor = module.SocialExtractor(
        adapter=build_adapter(),
        sources_file=Path("sources.yaml")
    )

    monkeypatch.setattr(
        module.SocialExtractor,
        "load_source",
        lambda self, force_reload=False: {}
    )
    monkeypatch.setattr(
        module,
        "get_secret",
        lambda secret_name: pytest.fail("get_secret ne doit pas être appelé")
    )

    assert extractor.client_id == ""
    assert extractor.client_secret == ""


# Exécution

def test_extract_delegates_to_social_engine(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = build_adapter()
    extractor = module.SocialExtractor(
        adapter=adapter,
        sources_file=Path("sources.yaml")
    )
    source = {
        "enabled": True
    }
    expected = [
        {
            "title": "Article"
        }
    ]
    received: list[tuple[Mapping[str, Any], SocialAdapter]] = []

    def fake_extract_social_source(
        current_source: Mapping[str, Any],
        current_adapter: SocialAdapter
    ) -> list[dict[str, Any]]:
        received.append((current_source, current_adapter))
        return expected

    monkeypatch.setattr(
        module,
        "extract_social_source",
        fake_extract_social_source
    )

    result = extractor.extract(source)

    assert result == expected
    assert received == [
        (source, adapter)
    ]


def test_run_delegates_to_configured_extractor(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = build_adapter()
    extractor = module.SocialExtractor(
        adapter=adapter,
        sources_file=Path("sources.yaml")
    )
    expected = object()
    received: dict[str, Any] = {}

    def fake_execute_configured_extractor(**kwargs: Any) -> Any:
        received.update(kwargs)
        return expected

    monkeypatch.setattr(
        module,
        "execute_configured_extractor",
        fake_execute_configured_extractor
    )

    result = extractor.run()

    assert result is expected
    assert received == {
        "extractor_name": "Reddit",
        "source_type": module.SOURCE_TYPE_SOCIAL,
        "source_loader": extractor.reload_source,
        "extraction_function": extractor.extract
    }


# Validation spécifique

def test_validate_social_item_rejects_existing_reason() -> None:
    social_item = SocialItem(
        identifier="item-1",
        item={},
        rejection_reason="contenu_supprime"
    )

    result = module.validate_social_item(
        social_item,
        build_adapter(),
        build_context()
    )

    assert result == (
        False,
        "contenu_supprime"
    )


def test_validate_social_item_accepts_without_validator() -> None:
    result = module.validate_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(),
        build_context()
    )

    assert result == (
        True,
        ""
    )


def test_validate_social_item_calls_adapter_validator() -> None:
    received: list[tuple[Any, Mapping[str, Any], Mapping[str, Any]]] = []

    def fake_validate_item(
        item: Any,
        filters: Mapping[str, Any],
        source: Mapping[str, Any]
    ) -> tuple[bool, str]:
        received.append((item, filters, source))
        return False, "  contenu_invalide  "

    context = build_context()
    social_item = SocialItem(
        identifier="item-1",
        item={
            "title": "Publication"
        }
    )

    result = module.validate_social_item(
        social_item,
        build_adapter(validate_item=fake_validate_item),
        context
    )

    assert result == (
        False,
        "contenu_invalide"
    )
    assert received == [
        (
            social_item.item,
            context.filters,
            context.source
        )
    ]


def test_validate_social_item_handles_validator_exception() -> None:
    def failing_validator(
        item: Any,
        filters: Mapping[str, Any],
        source: Mapping[str, Any]
    ) -> tuple[bool, str]:
        del item, filters, source
        raise RuntimeError("boom")

    result = module.validate_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(validate_item=failing_validator),
        build_context()
    )

    assert result == (
        False,
        "validation_impossible"
    )


@pytest.mark.parametrize(
    "result",
    [
        None,
        True,
        (True,),
        (True, "", "extra"),
        ["true", ""]
    ]
)
def test_validate_social_item_rejects_invalid_result_shape(
    result: Any
) -> None:
    adapter = build_adapter(
        validate_item=lambda item, filters, source: result
    )

    assert module.validate_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        adapter,
        build_context()
    ) == (
        False,
        "validation_invalide"
    )


@pytest.mark.parametrize(
    "valid",
    [
        1,
        0,
        "true",
        None
    ]
)
def test_validate_social_item_requires_boolean_status(
    valid: Any
) -> None:
    adapter = build_adapter(
        validate_item=lambda item, filters, source: (
            valid,
            "raison"
        )
    )

    assert module.validate_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        adapter,
        build_context()
    ) == (
        False,
        "validation_invalide"
    )


# Construction

def test_build_social_article_normalizes_pipeline_fields() -> None:
    context = build_context()

    def custom_builder(
        item: Any,
        identifier: str,
        source: Mapping[str, Any],
        item_context: Mapping[str, Any]
    ) -> dict[str, Any]:
        del item, identifier, source, item_context
        return {
            "title": "Article",
            "source": "r/news"
        }

    result = module.build_social_article(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(build_article=custom_builder),
        context
    )

    assert result == {
        "title": "Article",
        "source": "reddit",
        "publisher": "r/news",
        "source_type": module.SOURCE_TYPE_SOCIAL,
        "source_name": "Reddit"
    }


def test_build_social_article_preserves_existing_source_name() -> None:
    def custom_builder(
        item: Any,
        identifier: str,
        source: Mapping[str, Any],
        item_context: Mapping[str, Any]
    ) -> dict[str, Any]:
        del item, identifier, source, item_context
        return {
            "title": "Article",
            "source_name": "Nom personnalisé"
        }

    result = module.build_social_article(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(build_article=custom_builder),
        build_context()
    )

    assert result is not None
    assert result["source_name"] == "Nom personnalisé"


def test_build_social_article_does_not_duplicate_matching_publisher() -> None:
    def custom_builder(
        item: Any,
        identifier: str,
        source: Mapping[str, Any],
        item_context: Mapping[str, Any]
    ) -> dict[str, Any]:
        del item, identifier, source, item_context
        return {
            "title": "Article",
            "source": "Reddit"
        }

    result = module.build_social_article(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(build_article=custom_builder),
        build_context()
    )

    assert result is not None
    assert "publisher" not in result
    assert result["source"] == "reddit"


def test_build_social_article_handles_builder_exception() -> None:
    def failing_builder(
        item: Any,
        identifier: str,
        source: Mapping[str, Any],
        item_context: Mapping[str, Any]
    ) -> dict[str, Any]:
        del item, identifier, source, item_context
        raise RuntimeError("boom")

    result = module.build_social_article(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(build_article=failing_builder),
        build_context()
    )

    assert result is None


@pytest.mark.parametrize(
    "article",
    [
        None,
        {},
        [],
        "invalid"
    ]
)
def test_build_social_article_rejects_invalid_article(
    article: Any
) -> None:
    adapter = build_adapter(
        build_article=lambda item, identifier, source, context: article
    )

    result = module.build_social_article(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        adapter,
        build_context()
    )

    assert result is None


# Traitement

def test_process_social_item_rejects_invalid_social_item(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context()

    monkeypatch.setattr(
        module,
        "validate_social_item",
        lambda social_item, adapter, current_context: (
            False,
            "contenu_invalide"
        )
    )

    module.process_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(),
        context
    )

    assert context.processed_count == 1
    assert context.rejection_stats == Counter(
        {
            "contenu_invalide": 1
        }
    )


def test_process_social_item_rejects_invalid_construction(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context()

    monkeypatch.setattr(
        module,
        "validate_social_item",
        lambda social_item, adapter, current_context: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "build_social_article",
        lambda social_item, adapter, current_context: None
    )

    module.process_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(),
        context
    )

    assert context.rejection_stats == Counter(
        {
            "construction_invalide": 1
        }
    )


def test_process_social_item_rejects_invalid_age(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context()

    monkeypatch.setattr(
        module,
        "validate_social_item",
        lambda social_item, adapter, current_context: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "build_social_article",
        lambda social_item, adapter, current_context: {
            "title": "Article"
        }
    )
    monkeypatch.setattr(
        module,
        "validate_article_age",
        lambda article, maximum_age: (
            False,
            "article_trop_ancien"
        )
    )

    module.process_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(),
        context
    )

    assert context.rejection_stats == Counter(
        {
            "article_trop_ancien": 1
        }
    )


def test_process_social_item_handles_article_validation_exception(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context()

    monkeypatch.setattr(
        module,
        "validate_social_item",
        lambda social_item, adapter, current_context: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "build_social_article",
        lambda social_item, adapter, current_context: {
            "title": "Article"
        }
    )
    monkeypatch.setattr(
        module,
        "validate_article_age",
        lambda article, maximum_age: (
            True,
            ""
        )
    )

    def failing_validate_article(
        article: Mapping[str, Any],
        filters: Mapping[str, Any]
    ) -> tuple[bool, str]:
        del article, filters
        raise RuntimeError("boom")

    monkeypatch.setattr(
        module,
        "validate_article",
        failing_validate_article
    )

    module.process_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(),
        context
    )

    assert context.rejection_stats == Counter(
        {
            "validation_article_impossible": 1
        }
    )


def test_process_social_item_rejects_invalid_article(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context()

    monkeypatch.setattr(
        module,
        "validate_social_item",
        lambda social_item, adapter, current_context: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "build_social_article",
        lambda social_item, adapter, current_context: {
            "title": "Article"
        }
    )
    monkeypatch.setattr(
        module,
        "validate_article_age",
        lambda article, maximum_age: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "validate_article",
        lambda article, filters: (
            False,
            "titre_invalide"
        )
    )

    module.process_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(),
        context
    )

    assert context.rejection_stats == Counter(
        {
            "titre_invalide": 1
        }
    )


def test_process_social_item_rejects_duplicate(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context(remove_duplicates=True)

    monkeypatch.setattr(
        module,
        "validate_social_item",
        lambda social_item, adapter, current_context: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "build_social_article",
        lambda social_item, adapter, current_context: {
            "title": "Article"
        }
    )
    monkeypatch.setattr(
        module,
        "validate_article_age",
        lambda article, maximum_age: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "validate_article",
        lambda article, filters: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "is_duplicate_article",
        lambda article, seen_keys: True
    )

    module.process_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(),
        context
    )

    assert context.articles == []
    assert context.rejection_stats == Counter(
        {
            "doublon": 1
        }
    )


def test_process_social_item_registers_and_adds_valid_article(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context(remove_duplicates=True)
    article = {
        "title": "Article"
    }
    registered: list[tuple[dict[str, Any], set[str]]] = []

    monkeypatch.setattr(
        module,
        "validate_social_item",
        lambda social_item, adapter, current_context: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "build_social_article",
        lambda social_item, adapter, current_context: article
    )
    monkeypatch.setattr(
        module,
        "validate_article_age",
        lambda current_article, maximum_age: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "validate_article",
        lambda current_article, filters: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "is_duplicate_article",
        lambda current_article, seen_keys: False
    )

    def fake_register_article(
        current_article: dict[str, Any],
        seen_keys: set[str]
    ) -> None:
        registered.append((current_article, seen_keys))

    monkeypatch.setattr(
        module,
        "register_article",
        fake_register_article
    )

    module.process_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(),
        context
    )

    assert context.articles == [article]
    assert registered == [
        (article, context.seen_keys)
    ]


def test_process_social_item_skips_deduplication_when_disabled(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context(remove_duplicates=False)
    article = {
        "title": "Article"
    }

    monkeypatch.setattr(
        module,
        "validate_social_item",
        lambda social_item, adapter, current_context: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "build_social_article",
        lambda social_item, adapter, current_context: article
    )
    monkeypatch.setattr(
        module,
        "validate_article_age",
        lambda current_article, maximum_age: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "validate_article",
        lambda current_article, filters: (
            True,
            ""
        )
    )
    monkeypatch.setattr(
        module,
        "is_duplicate_article",
        lambda article, seen_keys: pytest.fail(
            "La déduplication ne doit pas être appelée"
        )
    )
    monkeypatch.setattr(
        module,
        "register_article",
        lambda article, seen_keys: pytest.fail(
            "L'enregistrement ne doit pas être appelé"
        )
    )

    module.process_social_item(
        SocialItem(
            identifier="item-1",
            item={}
        ),
        build_adapter(),
        context
    )

    assert context.articles == [article]


# Extraction globale

def test_extract_social_source_rejects_invalid_adapter() -> None:
    assert module.extract_social_source(
        {
            "enabled": True
        },
        object()
    ) == []


def test_extract_social_source_returns_empty_without_context(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "create_extraction_context",
        lambda source, adapter: None
    )

    result = module.extract_social_source(
        {
            "enabled": True
        },
        build_adapter()
    )

    assert result == []


def test_extract_social_source_processes_valid_items(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context(maximum_articles=2)
    items = [
        SocialItem(
            identifier="item-1",
            item={}
        ),
        SocialItem(
            identifier="item-2",
            item={}
        )
    ]
    processed: list[str] = []

    adapter = build_adapter(
        iter_items=lambda source, maximum_articles: items
    )

    monkeypatch.setattr(
        module,
        "create_extraction_context",
        lambda source, current_adapter: context
    )

    def fake_process_social_item(
        social_item: SocialItem,
        current_adapter: SocialAdapter,
        current_context: SocialExtractionContext
    ) -> None:
        del current_adapter
        processed.append(social_item.identifier)
        current_context.processed_count += 1
        current_context.add_article(
            {
                "id": social_item.identifier
            }
        )

    monkeypatch.setattr(
        module,
        "process_social_item",
        fake_process_social_item
    )
    monkeypatch.setattr(
        module,
        "log_extraction_summary",
        lambda **kwargs: None
    )

    result = module.extract_social_source(
        {
            "enabled": True
        },
        adapter
    )

    assert result == [
        {
            "id": "item-1"
        },
        {
            "id": "item-2"
        }
    ]
    assert processed == [
        "item-1",
        "item-2"
    ]


def test_extract_social_source_handles_iterator_initialization_error(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context(maximum_articles=2)

    def failing_iter_items(
        source: Mapping[str, Any],
        maximum_articles: int
    ) -> Iterable[SocialItem]:
        del source, maximum_articles
        raise RuntimeError("boom")

    monkeypatch.setattr(
        module,
        "create_extraction_context",
        lambda source, adapter: context
    )
    monkeypatch.setattr(
        module,
        "log_extraction_summary",
        lambda **kwargs: None
    )

    result = module.extract_social_source(
        {
            "enabled": True
        },
        build_adapter(iter_items=failing_iter_items)
    )

    assert result == []
    assert context.rejection_stats == Counter(
        {
            "initialisation_impossible": 1
        }
    )


def test_extract_social_source_rejects_invalid_social_item(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context(maximum_articles=1)
    adapter = build_adapter(
        iter_items=lambda source, maximum_articles: [
            {
                "invalid": True
            }
        ]
    )

    monkeypatch.setattr(
        module,
        "create_extraction_context",
        lambda source, current_adapter: context
    )
    monkeypatch.setattr(
        module,
        "log_extraction_summary",
        lambda **kwargs: None
    )

    result = module.extract_social_source(
        {
            "enabled": True
        },
        adapter
    )

    assert result == []
    assert context.processed_count == 1
    assert context.rejection_stats == Counter(
        {
            "element_social_invalide": 1
        }
    )


def test_extract_social_source_handles_processing_exception(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context(maximum_articles=1)
    adapter = build_adapter(
        iter_items=lambda source, maximum_articles: [
            SocialItem(
                identifier="item-1",
                item={}
            )
        ]
    )

    monkeypatch.setattr(
        module,
        "create_extraction_context",
        lambda source, current_adapter: context
    )
    monkeypatch.setattr(
        module,
        "process_social_item",
        lambda social_item, current_adapter, current_context: (
            (_ for _ in ()).throw(RuntimeError("boom"))
        )
    )
    monkeypatch.setattr(
        module,
        "log_extraction_summary",
        lambda **kwargs: None
    )

    result = module.extract_social_source(
        {
            "enabled": True
        },
        adapter
    )

    assert result == []
    assert context.rejection_stats == Counter(
        {
            "erreur_inattendue": 1
        }
    )


def test_extract_social_source_logs_summary(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    context = build_context(maximum_articles=2)
    context.articles.append(
        {
            "title": "Article"
        }
    )
    context.processed_count = 3
    context.rejection_stats.update(
        {
            "doublon": 2
        }
    )
    received: list[dict[str, Any]] = []

    monkeypatch.setattr(
        module,
        "create_extraction_context",
        lambda source, adapter: context
    )
    monkeypatch.setattr(
        module,
        "log_extraction_summary",
        lambda **kwargs: received.append(kwargs)
    )

    result = module.extract_social_source(
        {
            "enabled": True
        },
        build_adapter()
    )

    assert result == context.articles
    assert received == [
        {
            "source_name": "Reddit",
            "extracted_count": 1,
            "processed_count": 3,
            "rejection_stats": context.rejection_stats
        }
    ]