"""Tests unitaires de la normalisation des verdicts de fact-checking."""

from __future__ import annotations

from collections import UserDict
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, fields, is_dataclass
from typing import Any

import pytest

import src.article.fact_check_labels as module


# Constantes

def test_fact_check_labels_have_expected_values() -> None:
    assert module.FACT_CHECK_LABEL_TRUE == "true"
    assert module.FACT_CHECK_LABEL_FALSE == "false"
    assert module.FACT_CHECK_LABEL_NOT_CLASSIFIED == "not_classified"


def test_fact_check_labels_contains_all_standard_labels() -> None:
    assert module.FACT_CHECK_LABELS == {
        "true",
        "false",
        "not_classified"
    }


def test_reason_constants_have_expected_values() -> None:
    assert module.REASON_EXACT_MATCH == "exact_match"
    assert module.REASON_TRUE_MARKER == "true_marker"
    assert module.REASON_FALSE_MARKER == "false_marker"
    assert module.REASON_AMBIGUOUS == "ambiguous"
    assert module.REASON_EMPTY == "empty"
    assert module.REASON_UNKNOWN == "unknown"


def test_exact_label_sets_are_disjoint() -> None:
    assert module.TRUE_EXACT_LABELS.isdisjoint(
        module.FALSE_EXACT_LABELS
    )
    assert module.TRUE_EXACT_LABELS.isdisjoint(
        module.AMBIGUOUS_EXACT_LABELS
    )
    assert module.FALSE_EXACT_LABELS.isdisjoint(
        module.AMBIGUOUS_EXACT_LABELS
    )


def test_marker_collections_are_not_empty() -> None:
    assert module.TRUE_MARKERS
    assert module.FALSE_MARKERS
    assert module.AMBIGUOUS_MARKERS


def test_rating_prefixes_are_not_empty() -> None:
    assert module.RATING_PREFIXES


# Résultat de classification

def test_fact_check_label_result_is_frozen_dataclass_with_slots() -> None:
    assert is_dataclass(module.FactCheckLabelResult)
    assert module.FactCheckLabelResult.__dataclass_params__.frozen is True
    assert hasattr(module.FactCheckLabelResult, "__slots__")


def test_fact_check_label_result_has_expected_field_order() -> None:
    assert [
        field.name
        for field in fields(module.FactCheckLabelResult)
    ] == [
        "raw_value",
        "normalized_value",
        "label",
        "reason",
        "matched_value"
    ]


def test_fact_check_label_result_uses_empty_match_by_default() -> None:
    result = module.FactCheckLabelResult(
        raw_value="Verdict",
        normalized_value="verdict",
        label="not_classified",
        reason="unknown"
    )

    assert result.matched_value == ""


def test_fact_check_label_result_is_immutable() -> None:
    result = module.FactCheckLabelResult(
        raw_value="True",
        normalized_value="true",
        label="true",
        reason="exact_match"
    )

    with pytest.raises(FrozenInstanceError):
        result.label = "false"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("true", True),
        ("false", True),
        ("not_classified", False),
        ("unknown", False),
        ("", False)
    ]
)
def test_fact_check_label_result_is_classified(
    label: str,
    expected: bool
) -> None:
    result = module.FactCheckLabelResult(
        raw_value="",
        normalized_value="",
        label=label,
        reason=""
    )

    assert result.is_classified is expected


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("true", True),
        ("false", False),
        ("not_classified", False)
    ]
)
def test_fact_check_label_result_is_true(
    label: str,
    expected: bool
) -> None:
    result = module.FactCheckLabelResult(
        raw_value="",
        normalized_value="",
        label=label,
        reason=""
    )

    assert result.is_true is expected


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("true", False),
        ("false", True),
        ("not_classified", False)
    ]
)
def test_fact_check_label_result_is_false(
    label: str,
    expected: bool
) -> None:
    result = module.FactCheckLabelResult(
        raw_value="",
        normalized_value="",
        label=label,
        reason=""
    )

    assert result.is_false is expected


def test_fact_check_label_result_to_dict_returns_serializable_data() -> None:
    result = module.FactCheckLabelResult(
        raw_value="Verdict: faux",
        normalized_value="faux",
        label="false",
        reason="exact_match",
        matched_value="faux"
    )

    assert result.to_dict() == {
        "raw_value": "Verdict: faux",
        "normalized_value": "faux",
        "label": "false",
        "reason": "exact_match",
        "matched_value": "faux",
        "is_classified": True
    }


# Normalisation des préfixes

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Verdict", "verdict"),
        ("Fact-check", "fact check"),
        ("NOTRE ÉVALUATION", "notre evaluation"),
        ("  Our   Rating  ", "our rating"),
        ("Résultat", "resultat")
    ]
)
def test_normalize_prefix_returns_expected_value(
    value: str,
    expected: str
) -> None:
    assert module.normalize_prefix(value) == expected


def test_normalize_prefix_removes_accents() -> None:
    assert module.normalize_prefix("Évaluation") == "evaluation"


def test_normalize_prefix_replaces_hyphens_with_spaces() -> None:
    assert module.normalize_prefix("fact-check") == "fact check"


def test_normalize_prefix_collapses_whitespace() -> None:
    assert module.normalize_prefix("our   rating") == "our rating"


# Suppression des préfixes

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("verdict false", "false"),
        ("rating true", "true"),
        ("our rating mostly false", "mostly false"),
        ("notre evaluation plutot vrai", "plutot vrai"),
        ("fact check fake", "fake"),
        ("classification misleading", "misleading")
    ]
)
def test_remove_rating_prefix_removes_known_prefix(
    value: str,
    expected: str
) -> None:
    assert module.remove_rating_prefix(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "verdict",
        "rating",
        "fact check",
        "notre evaluation"
    ]
)
def test_remove_rating_prefix_returns_empty_for_prefix_only(
    value: str
) -> None:
    assert module.remove_rating_prefix(value) == ""


def test_remove_rating_prefix_preserves_unknown_prefix() -> None:
    assert module.remove_rating_prefix(
        "decision false"
    ) == "decision false"


def test_remove_rating_prefix_strips_outer_whitespace() -> None:
    assert module.remove_rating_prefix(
        "  verdict false  "
    ) == "false"


def test_remove_rating_prefix_prioritizes_longest_prefix(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "RATING_PREFIXES",
        (
            "rating",
            "our rating"
        )
    )

    assert module.remove_rating_prefix(
        "our rating false"
    ) == "false"


def test_remove_rating_prefix_strips_separators_after_prefix() -> None:
    assert module.remove_rating_prefix(
        "verdict - false"
    ) == "false"


# Normalisation du verdict

@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "   "
    ]
)
def test_normalize_fact_check_text_returns_empty_for_missing_value(
    value: Any
) -> None:
    assert module.normalize_fact_check_text(value) == ""


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("VRAI", "vrai"),
        ("Évaluation : FAUX", "faux"),
        ("Verdict: Trompeur!", "trompeur"),
        ("Rating — Mostly True", "mostly true"),
        ("Fact-check: AI-generated image", "ai generated image"),
        ("Correct & Verified", "correct and verified"),
        ("  Plusieurs   espaces  ", "plusieurs espaces"),
        ("[FAUX]", "faux"),
        ("« Vrai »", "« vrai »")
    ]
)
def test_normalize_fact_check_text_returns_expected_value(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_fact_check_text(value) == expected


def test_normalize_fact_check_text_calls_clean_text(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Any] = []

    def fake_clean_text(value: Any) -> str:
        calls.append(value)
        return "VERDICT: TRUE"

    monkeypatch.setattr(
        module,
        "clean_text",
        fake_clean_text
    )

    result = module.normalize_fact_check_text("raw")

    assert result == "true"
    assert calls == ["raw"]


def test_normalize_fact_check_text_removes_accents() -> None:
    assert module.normalize_fact_check_text(
        "Vérifiée"
    ) == "verifiee"


def test_normalize_fact_check_text_normalizes_typographic_apostrophe() -> None:
    assert module.normalize_fact_check_text(
        "N’A JAMAIS DIT"
    ) == "n'a jamais dit"


def test_normalize_fact_check_text_replaces_punctuation_with_spaces() -> None:
    assert module.normalize_fact_check_text(
        "false,true"
    ) == "false true"


def test_normalize_fact_check_text_does_not_merge_words() -> None:
    assert module.normalize_fact_check_text(
        "not/true"
    ) == "not true"


def test_normalize_fact_check_text_removes_rating_prefix(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[str] = []

    def fake_remove_rating_prefix(value: str) -> str:
        captured.append(value)
        return "normalized-result"

    monkeypatch.setattr(
        module,
        "remove_rating_prefix",
        fake_remove_rating_prefix
    )

    result = module.normalize_fact_check_text(
        "Verdict: False"
    )

    assert result == "normalized-result"
    assert captured == ["verdict false"]


# Recherche des marqueurs

@pytest.mark.parametrize(
    ("value", "marker", "expected"),
    [
        ("the claim is true", "true", True),
        ("true", "true", True),
        ("this is true.", "true", True),
        ("untrue", "true", False),
        ("truthful", "true", False),
        ("falsehood", "false", False),
        ("mostly false", "mostly false", True),
        ("", "true", False),
        ("true", "", False)
    ]
)
def test_contains_marker_returns_expected_value(
    value: str,
    marker: str,
    expected: bool
) -> None:
    assert module.contains_marker(value, marker) is expected


def test_contains_marker_escapes_regular_expression_characters() -> None:
    assert module.contains_marker(
        "rating a+b",
        "a+b"
    ) is True


def test_contains_marker_accepts_apostrophe_inside_marker() -> None:
    assert module.contains_marker(
        "it isn't true",
        "isn't true"
    ) is True


def test_find_first_marker_returns_empty_when_nothing_matches() -> None:
    assert module.find_first_marker(
        "verdict inconnu",
        (
            "true",
            "false"
        )
    ) == ""


def test_find_first_marker_returns_matching_marker() -> None:
    assert module.find_first_marker(
        "this claim is false",
        (
            "true",
            "false"
        )
    ) == "false"


def test_find_first_marker_prioritizes_longest_marker() -> None:
    result = module.find_first_marker(
        "the claim is mostly false",
        (
            "false",
            "mostly false"
        )
    )

    assert result == "mostly false"


def test_find_first_marker_calls_contains_marker_in_length_order(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def fake_contains_marker(value: str, marker: str) -> bool:
        calls.append(marker)
        return marker == "medium marker"

    monkeypatch.setattr(
        module,
        "contains_marker",
        fake_contains_marker
    )

    result = module.find_first_marker(
        "value",
        (
            "short",
            "the longest marker",
            "medium marker"
        )
    )

    assert result == "medium marker"
    assert calls == [
        "the longest marker",
        "medium marker"
    ]


# Construction d'un résultat non classifié

def test_build_not_classified_result_returns_expected_result() -> None:
    result = module.build_not_classified_result(
        raw_value="Mixed",
        normalized_value="mixed",
        reason="ambiguous",
        matched_value="mixed"
    )

    assert result == module.FactCheckLabelResult(
        raw_value="Mixed",
        normalized_value="mixed",
        label="not_classified",
        reason="ambiguous",
        matched_value="mixed"
    )


def test_build_not_classified_result_uses_empty_match_by_default() -> None:
    result = module.build_not_classified_result(
        raw_value="Unknown",
        normalized_value="unknown-value",
        reason="unknown"
    )

    assert result.matched_value == ""


# Correspondances exactes

@pytest.mark.parametrize(
    "value",
    [
        "true",
        "correct",
        "accurate",
        "verified",
        "mostly true",
        "vrai",
        "vraie",
        "exacte",
        "plutôt vrai",
        "globalement vraie",
        "verdadero"
    ]
)
def test_classify_fact_check_label_classifies_exact_true_values(
    value: str
) -> None:
    result = module.classify_fact_check_label(value)

    assert result.label == module.FACT_CHECK_LABEL_TRUE
    assert result.reason == module.REASON_EXACT_MATCH
    assert result.matched_value == result.normalized_value
    assert result.is_true is True


@pytest.mark.parametrize(
    "value",
    [
        "false",
        "fake",
        "incorrect",
        "misleading",
        "mostly false",
        "partially false",
        "faux",
        "fausse",
        "trompeuse",
        "plutôt faux",
        "désinformation",
        "image générée par IA",
        "falso"
    ]
)
def test_classify_fact_check_label_classifies_exact_false_values(
    value: str
) -> None:
    result = module.classify_fact_check_label(value)

    assert result.label == module.FACT_CHECK_LABEL_FALSE
    assert result.reason == module.REASON_EXACT_MATCH
    assert result.matched_value == result.normalized_value
    assert result.is_false is True


@pytest.mark.parametrize(
    "value",
    [
        "mixed",
        "half true",
        "needs context",
        "out of context",
        "satire",
        "unverified",
        "uncertain",
        "no evidence",
        "mitigé",
        "à nuancer",
        "hors contexte",
        "partiellement vrai",
        "preuves insuffisantes",
        "impossible à vérifier"
    ]
)
def test_classify_fact_check_label_keeps_exact_ambiguous_values_unclassified(
    value: str
) -> None:
    result = module.classify_fact_check_label(value)

    assert result.label == module.FACT_CHECK_LABEL_NOT_CLASSIFIED
    assert result.reason == module.REASON_AMBIGUOUS
    assert result.matched_value == result.normalized_value
    assert result.is_classified is False


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        " ",
        "Verdict:",
        "Rating"
    ]
)
def test_classify_fact_check_label_returns_empty_reason_for_empty_value(
    value: Any
) -> None:
    result = module.classify_fact_check_label(value)

    assert result.label == module.FACT_CHECK_LABEL_NOT_CLASSIFIED
    assert result.reason == module.REASON_EMPTY
    assert result.normalized_value == ""
    assert result.matched_value == ""


# Correspondances par marqueur

@pytest.mark.parametrize(
    ("value", "marker"),
    [
        (
            "The report concludes that the claim is false.",
            "the claim is false"
        ),
        (
            "This photograph was generated by AI.",
            "generated by ai"
        ),
        (
            "The statement is misleading according to investigators.",
            "misleading"
        ),
        (
            "Cette affirmation est en grande partie fausse.",
            "en grande partie fausse"
        ),
        (
            "Il n'a jamais dit cette phrase.",
            "n'a jamais dit"
        )
    ]
)
def test_classify_fact_check_label_detects_false_marker(
    value: str,
    marker: str
) -> None:
    result = module.classify_fact_check_label(value)

    assert result.label == module.FACT_CHECK_LABEL_FALSE
    assert result.reason == module.REASON_FALSE_MARKER
    assert result.matched_value == marker


@pytest.mark.parametrize(
    ("value", "marker"),
    [
        (
            "The evidence supports this claim.",
            "evidence supports"
        ),
        (
            "Investigators confirmed the story as true.",
            "confirmed"
        ),
        (
            "This is an authentic image.",
            "authentic image"
        ),
        (
            "L'affirmation est globalement vraie.",
            "globalement vraie"
        ),
        (
            "Le document a été vérifié par plusieurs experts.",
            "verifie"
        )
    ]
)
def test_classify_fact_check_label_detects_true_marker(
    value: str,
    marker: str
) -> None:
    result = module.classify_fact_check_label(value)

    assert result.label == module.FACT_CHECK_LABEL_TRUE
    assert result.reason == module.REASON_TRUE_MARKER
    assert result.matched_value == marker


@pytest.mark.parametrize(
    ("value", "marker"),
    [
        (
            "This claim is partly true but needs context.",
            "needs context"
        ),
        (
            "There is not enough evidence to verify this claim.",
            "not enough evidence"
        ),
        (
            "This image is satire, not a real event.",
            "satire"
        ),
        (
            "Cette publication est hors contexte et trompeuse.",
            "hors contexte"
        ),
        (
            "Cette affirmation est partiellement vraie.",
            "partiellement vraie"
        )
    ]
)
def test_classify_fact_check_label_prioritizes_ambiguous_marker(
    value: str,
    marker: str
) -> None:
    result = module.classify_fact_check_label(value)

    assert result.label == module.FACT_CHECK_LABEL_NOT_CLASSIFIED
    assert result.reason == module.REASON_AMBIGUOUS
    assert result.matched_value == marker


def test_classify_fact_check_label_prioritizes_false_before_true() -> None:
    result = module.classify_fact_check_label(
        "The claim is not true."
    )

    assert result.label == module.FACT_CHECK_LABEL_FALSE
    assert result.reason == module.REASON_FALSE_MARKER
    assert result.matched_value == "is not true"


def test_classify_fact_check_label_does_not_detect_true_inside_untrue() -> None:
    result = module.classify_fact_check_label(
        "The statement is untrue."
    )

    assert result.label == module.FACT_CHECK_LABEL_FALSE
    assert result.matched_value == "untrue"


def test_classify_fact_check_label_returns_unknown_for_unmatched_value() -> None:
    result = module.classify_fact_check_label(
        "Verdict spécial sans correspondance"
    )

    assert result == module.FactCheckLabelResult(
        raw_value="Verdict spécial sans correspondance",
        normalized_value="special sans correspondance",
        label=module.FACT_CHECK_LABEL_NOT_CLASSIFIED,
        reason=module.REASON_UNKNOWN,
        matched_value=""
    )


# Utilisation des fonctions internes

def test_classify_fact_check_label_calls_clean_text_for_raw_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Any] = []

    def fake_clean_text(value: Any) -> str:
        calls.append(value)
        return "raw cleaned"

    monkeypatch.setattr(
        module,
        "clean_text",
        fake_clean_text
    )
    monkeypatch.setattr(
        module,
        "normalize_fact_check_text",
        lambda value: ""
    )

    result = module.classify_fact_check_label("raw")

    assert result.raw_value == "raw cleaned"
    assert calls == ["raw"]


def test_classify_fact_check_label_normalizes_cleaned_raw_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[Any] = []

    monkeypatch.setattr(
        module,
        "clean_text",
        lambda value: "cleaned raw"
    )

    def fake_normalize_fact_check_text(value: Any) -> str:
        captured.append(value)
        return "true"

    monkeypatch.setattr(
        module,
        "normalize_fact_check_text",
        fake_normalize_fact_check_text
    )

    result = module.classify_fact_check_label("raw")

    assert result.label == module.FACT_CHECK_LABEL_TRUE
    assert captured == ["cleaned raw"]


def test_classify_fact_check_label_checks_marker_groups_in_expected_order(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, Any]] = []

    monkeypatch.setattr(
        module,
        "clean_text",
        lambda value: "custom verdict"
    )
    monkeypatch.setattr(
        module,
        "normalize_fact_check_text",
        lambda value: "custom verdict"
    )

    def fake_find_first_marker(
        value: str,
        markers: Any
    ) -> str:
        calls.append(
            (
                value,
                markers
            )
        )
        return ""

    monkeypatch.setattr(
        module,
        "find_first_marker",
        fake_find_first_marker
    )

    result = module.classify_fact_check_label("raw")

    assert result.reason == module.REASON_UNKNOWN
    assert calls == [
        (
            "custom verdict",
            module.AMBIGUOUS_MARKERS
        ),
        (
            "custom verdict",
            module.FALSE_MARKERS
        ),
        (
            "custom verdict",
            module.TRUE_MARKERS
        )
    ]


# Journalisation

def test_classify_fact_check_label_logs_exact_ambiguous_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    messages: list[tuple[Any, ...]] = []

    monkeypatch.setattr(
        module.logger,
        "debug",
        lambda *args: messages.append(args)
    )

    result = module.classify_fact_check_label("mixed")

    assert result.reason == module.REASON_AMBIGUOUS
    assert messages == [
        (
            "Verdict AMBIGUOUS : %r",
            "mixed"
        )
    ]


def test_classify_fact_check_label_logs_exact_false_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    messages: list[tuple[Any, ...]] = []

    monkeypatch.setattr(
        module.logger,
        "debug",
        lambda *args: messages.append(args)
    )

    result = module.classify_fact_check_label("false")

    assert result.label == module.FACT_CHECK_LABEL_FALSE
    assert messages == [
        (
            "Verdict EXACT FALSE : %r",
            "false"
        )
    ]


def test_classify_fact_check_label_logs_exact_true_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    messages: list[tuple[Any, ...]] = []

    monkeypatch.setattr(
        module.logger,
        "debug",
        lambda *args: messages.append(args)
    )

    result = module.classify_fact_check_label("true")

    assert result.label == module.FACT_CHECK_LABEL_TRUE
    assert messages == [
        (
            "Verdict EXACT TRUE : %r",
            "true"
        )
    ]


def test_classify_fact_check_label_logs_unknown_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    messages: list[tuple[Any, ...]] = []

    monkeypatch.setattr(
        module.logger,
        "debug",
        lambda *args: messages.append(args)
    )

    result = module.classify_fact_check_label("special verdict")

    assert result.reason == module.REASON_UNKNOWN
    assert messages == [
        (
            "Verdict inconnu | brut=%r | normalisé=%r",
            "special verdict",
            "special verdict"
        )
    ]


# Récupération simple du label

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("true", "true"),
        ("false", "false"),
        ("mixed", "not_classified"),
        ("unknown verdict", "not_classified")
    ]
)
def test_get_fact_check_label_returns_expected_label(
    value: Any,
    expected: str
) -> None:
    assert module.get_fact_check_label(value) == expected


def test_get_fact_check_label_uses_classification_result(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[Any] = []

    def fake_classify_fact_check_label(
        value: Any
    ) -> module.FactCheckLabelResult:
        captured.append(value)
        return module.FactCheckLabelResult(
            raw_value="",
            normalized_value="",
            label="false",
            reason="test"
        )

    monkeypatch.setattr(
        module,
        "classify_fact_check_label",
        fake_classify_fact_check_label
    )

    assert module.get_fact_check_label("raw") == "false"
    assert captured == ["raw"]


# Validation des labels standards

@pytest.mark.parametrize(
    "value",
    [
        "true",
        "TRUE",
        "false",
        "False",
        "not_classified",
        "Not_Classified",
        "not classified"
    ]
)
def test_is_valid_fact_check_label_accepts_standard_labels(
    value: Any
) -> None:
    assert module.is_valid_fact_check_label(value) is True


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "fake",
        "real",
        "mixed",
        "unknown",
        1,
        0
    ]
)
def test_is_valid_fact_check_label_rejects_non_standard_labels(
    value: Any
) -> None:
    assert module.is_valid_fact_check_label(value) is False


def test_is_valid_fact_check_label_uses_normalized_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "normalize_fact_check_text",
        lambda value: "true"
    )

    assert module.is_valid_fact_check_label("anything") is True


# Normalisation des anciens labels

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("true", "true"),
        ("real", "true"),
        ("réel", "true"),
        ("vrai", "true"),
        ("1", "true"),
        (1, "true"),
        ("false", "false"),
        ("fake", "false"),
        ("faux", "false"),
        ("0", "false"),
        (0, "false"),
        ("not classified", "not_classified"),
        ("not_classified", "not_classified"),
        ("unknown", "not_classified"),
        ("unclassified", "not_classified"),
        ("non classé", "not_classified"),
        ("non classée", "not_classified"),
        ("", "not_classified"),
        (None, "not_classified")
    ]
)
def test_normalize_existing_fact_check_label_maps_known_values(
    value: Any,
    expected: str
) -> None:
    assert module.normalize_existing_fact_check_label(value) == expected


def test_normalize_existing_fact_check_label_uses_classifier_for_other_value(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Any] = []

    monkeypatch.setattr(
        module,
        "normalize_fact_check_text",
        lambda value: "custom verdict"
    )

    def fake_get_fact_check_label(value: Any) -> str:
        calls.append(value)
        return "false"

    monkeypatch.setattr(
        module,
        "get_fact_check_label",
        fake_get_fact_check_label
    )

    result = module.normalize_existing_fact_check_label("raw")

    assert result == "false"
    assert calls == ["raw"]


def test_normalize_existing_fact_check_label_evaluates_default_argument_eagerly(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Any] = []

    monkeypatch.setattr(
        module,
        "normalize_fact_check_text",
        lambda value: "true"
    )

    def fake_get_fact_check_label(value: Any) -> str:
        calls.append(value)
        return "false"

    monkeypatch.setattr(
        module,
        "get_fact_check_label",
        fake_get_fact_check_label
    )

    result = module.normalize_existing_fact_check_label("true")

    assert result == "true"
    assert calls == ["true"]


# Enrichissement d'un article

def test_enrich_article_with_fact_check_label_adds_classification_fields(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    article = {
        "id": "article-001",
        "title": "Titre"
    }
    result_value = module.FactCheckLabelResult(
        raw_value="Verdict: false",
        normalized_value="false",
        label="false",
        reason="exact_match",
        matched_value="false"
    )

    monkeypatch.setattr(
        module,
        "classify_fact_check_label",
        lambda value: result_value
    )

    result = module.enrich_article_with_fact_check_label(
        article,
        "Verdict: false"
    )

    assert result == {
        "id": "article-001",
        "title": "Titre",
        "label": "false",
        "fact_check_rating": "Verdict: false",
        "fact_check_rating_normalized": "false",
        "fact_check_label_reason": "exact_match",
        "fact_check_label_match": "false"
    }


def test_enrich_article_with_fact_check_label_returns_copy(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    article = {
        "id": "article-001"
    }

    monkeypatch.setattr(
        module,
        "classify_fact_check_label",
        lambda value: module.FactCheckLabelResult(
            raw_value="true",
            normalized_value="true",
            label="true",
            reason="exact_match",
            matched_value="true"
        )
    )

    result = module.enrich_article_with_fact_check_label(
        article,
        "true"
    )

    assert result is not article
    assert article == {
        "id": "article-001"
    }


def test_enrich_article_with_fact_check_label_overwrites_existing_label_by_default(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    article = {
        "label": "true"
    }

    monkeypatch.setattr(
        module,
        "classify_fact_check_label",
        lambda value: module.FactCheckLabelResult(
            raw_value="false",
            normalized_value="false",
            label="false",
            reason="exact_match",
            matched_value="false"
        )
    )

    result = module.enrich_article_with_fact_check_label(
        article,
        "false"
    )

    assert result["label"] == "false"


def test_enrich_article_with_fact_check_label_preserves_existing_label_when_requested(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    article = {
        "label": "true"
    }

    monkeypatch.setattr(
        module,
        "classify_fact_check_label",
        lambda value: module.FactCheckLabelResult(
            raw_value="false",
            normalized_value="false",
            label="false",
            reason="exact_match",
            matched_value="false"
        )
    )

    result = module.enrich_article_with_fact_check_label(
        article,
        "false",
        overwrite_label=False
    )

    assert result["label"] == "true"
    assert result["fact_check_rating"] == "false"
    assert result["fact_check_rating_normalized"] == "false"


@pytest.mark.parametrize(
    "existing_label",
    [
        None,
        "",
        False,
        0
    ]
)
def test_enrich_article_with_fact_check_label_fills_empty_existing_label(
    monkeypatch: pytest.MonkeyPatch,
    existing_label: Any
) -> None:
    article = {
        "label": existing_label
    }

    monkeypatch.setattr(
        module,
        "classify_fact_check_label",
        lambda value: module.FactCheckLabelResult(
            raw_value="true",
            normalized_value="true",
            label="true",
            reason="exact_match",
            matched_value="true"
        )
    )

    result = module.enrich_article_with_fact_check_label(
        article,
        "true",
        overwrite_label=False
    )

    assert result["label"] == "true"


def test_enrich_article_with_fact_check_label_accepts_custom_mapping(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    article: Mapping[str, Any] = UserDict(
        {
            "id": "article-001"
        }
    )

    monkeypatch.setattr(
        module,
        "classify_fact_check_label",
        lambda value: module.FactCheckLabelResult(
            raw_value="true",
            normalized_value="true",
            label="true",
            reason="exact_match",
            matched_value="true"
        )
    )

    result = module.enrich_article_with_fact_check_label(
        article,
        "true"
    )

    assert result["id"] == "article-001"
    assert result["label"] == "true"
    assert isinstance(result, dict)


def test_enrich_article_with_fact_check_label_passes_raw_rating_to_classifier(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Any] = []
    raw_rating = {
        "rating": "false"
    }

    def fake_classify_fact_check_label(
        value: Any
    ) -> module.FactCheckLabelResult:
        calls.append(value)
        return module.FactCheckLabelResult(
            raw_value="false",
            normalized_value="false",
            label="false",
            reason="exact_match",
            matched_value="false"
        )

    monkeypatch.setattr(
        module,
        "classify_fact_check_label",
        fake_classify_fact_check_label
    )

    module.enrich_article_with_fact_check_label(
        {},
        raw_rating
    )

    assert calls == [raw_rating]