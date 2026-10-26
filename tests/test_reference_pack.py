import pytest
from pydantic import ValidationError

from evidence_check.domain import ReferencePack
from evidence_check.engine import questions_for
from evidence_check.workflow import normalize_quote, precheck


def test_reference_pack_covers_distinct_failure_modes(pack):
    assert len(pack.cases) == 12
    assert {case.category for case in pack.cases} >= {
        "Normal",
        "Boundary",
        "Negative",
        "Missing",
        "Ambiguous",
        "Contradictory",
        "Adversarial",
        "Regression",
    }
    assert len(pack.sources) == 8


def test_unknown_source_ids_are_rejected(pack):
    payload = pack.model_dump()
    payload["cases"][0]["source_ids"] = ["invented"]
    with pytest.raises(ValidationError, match="unknown cited source ID"):
        ReferencePack.model_validate(payload)


def test_expected_evidence_must_refer_to_a_cited_source(pack):
    payload = pack.model_dump()
    payload["cases"][0]["expected_evidence"] = ["phone"]
    with pytest.raises(ValidationError, match="expected evidence"):
        ReferencePack.model_validate(payload)


def test_metamorphic_labels_must_stay_fixed(pack):
    payload = pack.model_dump()
    payload["cases"][1]["expected"] = "contradicted"
    with pytest.raises(ValidationError, match="retain the original labels"):
        ReferencePack.model_validate(payload)


def test_expected_labels_and_explanations_are_not_model_inputs(pack):
    state = pack.state_for(pack.cases[0])
    assert set(state) == {"claim", "sources"}
    assert set(state["sources"][0]) == {"id", "title", "text"}
    assert "expected" not in str(state)
    assert "A direct statement" not in str(state)


def test_option_order_changes_but_meaning_and_labels_are_preserved(pack):
    original, variant = pack.cases[0], pack.cases[2]
    first, reordered = questions_for(pack, original), questions_for(pack, variant)
    for key in ("relation", "evidence"):
        assert first[key].instructions == reordered[key].instructions
        assert dict(first[key].criteria) == dict(reordered[key].criteria)
        assert list(first[key].criteria) == list(reversed(list(reordered[key].criteria)))
    assert pack.state_for(original) == pack.state_for(variant)


def test_quote_presence_does_not_establish_semantic_support(pack):
    contradicted = pack.cases[4]
    assert contradicted.expected == "contradicted"
    assert precheck(pack, contradicted) is None


def test_missing_quote_is_blocked_without_model_confidence(pack):
    result = precheck(pack, pack.cases[9])
    assert result.validation == "quote_missing"
    assert result.judgment is None
    assert result.api_attempted is False


def test_normalization_keeps_negation_and_collapses_whitespace():
    assert normalize_quote("  “Not  available”\n today ") == '"Not available" today'
