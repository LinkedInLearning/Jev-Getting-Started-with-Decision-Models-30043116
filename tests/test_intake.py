from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from invoice_intake.core import (
    Policy,
    Result,
    find_candidates,
    fingerprint,
    parse_judgment,
    route,
)
from invoice_intake.jev import check_invoice
from tests.conftest import answer_payload


def fake_factory(payload=None, exception=None):
    calls = []

    class Client:
        def __init__(self, **kwargs):
            self.options = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def system_one(self, **kwargs):
            calls.append({"options": self.options, **kwargs})
            if exception:
                raise exception
            return SimpleNamespace(model_dump=lambda **_: payload)

    return Client, calls


def result_for(text, **kwargs):
    candidates = find_candidates(text)
    payload = answer_payload(candidates, **kwargs)
    return Result(fingerprint(text), candidates, parse_judgment(payload, candidates))


def test_candidates_keep_exact_spans_and_duplicate_occurrences(invoices):
    text = invoices[3]["text"]
    candidates = find_candidates(text)
    assert len(candidates) == 4
    assert [c.value for c in candidates] == ["2400.00", "192.00", "192.00", "2400.00"]
    assert len({c.id for c in candidates}) == 4
    for candidate in candidates:
        assert text[candidate.start : candidate.end] == candidate.text
        assert text.splitlines()[candidate.line - 1] == candidate.source_line


@pytest.mark.parametrize("text", ["USD\nTotal $1.200,50", "USD\nTotal $12,34.56"])
def test_unsupported_number_formats_do_not_become_partial_values(text):
    assert not find_candidates(text)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Currency: USD\nTotal is unreadable",
        "Currency: EUR\nTotal €50.00",
        "Currency: CAD\nTotal $50.00",
        "Currency: SEK\nUSD reference rate\nTotal $50.00",
        "Total $50.00",
        "Currency: USD\nSubtotal $20.00\nCredit -$5.00",
        "Currency: USD\nTotal USD -50.00",
        "Currency: USD\nTotal ($50.00)",
        "Currency: USD\nTotal −$50.00",
        "Currency: USD\nTotal $" + "9" * 80 + ".00",
        "Currency: USD\n" + "Total $1.00\n" * 41,
        "Currency: USD\n" + "x" * 20_001,
    ],
)
def test_unsupported_inputs_go_to_review_without_calls(text):
    factory, calls = fake_factory()
    result = check_invoice(text, api_key="not-real", client_factory=factory)
    assert not calls
    assert not result.called_api
    assert route(result, Policy()).status == "Review required"


def test_missing_key_does_not_instantiate_client(invoices):
    factory, calls = fake_factory()
    result = check_invoice(invoices[0]["text"], client_factory=factory)
    assert not calls
    assert "TYPESAFE_API_KEY" in result.error


def test_one_request_batches_independent_questions_and_copies_selected_value(invoices):
    text = invoices[0]["text"]
    candidates = find_candidates(text)
    factory, calls = fake_factory(answer_payload(candidates, choice="amount_3"))
    result = check_invoice(text, api_key="not-real", client_factory=factory)
    assert len(calls) == 1
    assert set(calls[0]["questions"]) == {
        "payable_amount",
        "has_payable_total",
        "unresolved_amounts",
    }
    assert calls[0]["state"]["invoice_text"] == text
    assert calls[0]["options"]["retry"].max_retries == 0
    decision = route(result, Policy())
    assert decision.status == "Ready for draft"
    assert decision.candidate.text == "$2,592.00"
    assert decision.candidate.value == "2592.00"
    assert result.judgment.input_tokens == 300


@pytest.mark.parametrize("presence,unresolved", [(0.1, 0.01), (0.99, 0.99), (0.5, 0.5)])
def test_confident_subtotal_does_not_override_presence_or_conflict(presence, unresolved):
    result = result_for(
        "Currency: USD\nSubtotal: $500.00", presence=presence, unresolved=unresolved
    )
    assert result.judgment.confidence > 0.9
    assert route(result, Policy()).status == "Review required"


def test_missing_total_with_only_components_requires_review(invoices):
    result = result_for(invoices[2]["text"], choice="none", presence=0.02)
    assert route(result, Policy()).candidate is None


def test_explicit_pending_credit_requires_review(invoices):
    result = result_for(invoices[1]["text"], choice="amount_3", unresolved=0.98)
    assert route(result, Policy()).status == "Review required"


def test_resolved_credit_can_produce_source_backed_draft(invoices):
    result = result_for(invoices[3]["text"], choice="amount_4")
    assert (
        route(result, Policy()).candidate.source_line == "Final amount due after credit: $2,400.00"
    )


def test_policy_boundaries_reuse_the_same_judgments():
    result = result_for("Currency: USD\nTotal $50.00")
    answer = replace(
        result.judgment, confidence=0.85, has_payable_total=0.85, unresolved_amounts=0.15
    )
    result = replace(result, judgment=answer)
    assert route(result, Policy()).status == "Ready for draft"
    assert route(result, Policy(min_confidence=0.86)).status == "Review required"
    assert route(result, Policy(min_presence=0.86)).status == "Review required"
    assert route(result, Policy(max_unresolved=0.14)).status == "Review required"


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p["answers"].pop("has_payable_total"),
        lambda p: p["answers"]["payable_amount"].update(choice="invented"),
        lambda p: p["answers"]["payable_amount"]["probabilities"].update(invented=0.0),
        lambda p: p["answers"]["payable_amount"]["probabilities"].update(none=0.8),
        lambda p: p["answers"]["payable_amount"].update(confidence=0.2),
        lambda p: p["answers"]["has_payable_total"].update(noul=float("nan")),
        lambda p: p["answers"]["has_payable_total"].update(noul=1.1),
        lambda p: p["answers"]["has_payable_total"].update(noul=True),
        lambda p: p["answers"]["has_payable_total"].update(type="choice"),
        lambda p: p["usage"].update(input_tokens=-1),
        lambda p: p.update(model=""),
    ],
)
def test_malformed_responses_fail_closed(change):
    text = "Currency: USD\nTotal $50.00"
    payload = answer_payload(find_candidates(text))
    change(payload)
    factory, _ = fake_factory(payload)
    result = check_invoice(text, api_key="not-real", client_factory=factory)
    assert result.judgment is None
    assert "validated" in result.error
    assert route(result, Policy()).candidate is None


def test_api_failure_has_no_draft_no_secret_and_no_automatic_retry():
    factory, calls = fake_factory(exception=RuntimeError("secret-provider-detail"))
    result = check_invoice(
        "Currency: USD\nTotal $50.00", api_key="not-real", client_factory=factory
    )
    assert len(calls) == 1
    assert "secret-provider-detail" not in result.error
    assert result.called_api
    assert route(result, Policy()).candidate is None


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), True])
def test_invalid_policy_is_rejected(value):
    with pytest.raises(ValueError):
        Policy(min_confidence=value)
