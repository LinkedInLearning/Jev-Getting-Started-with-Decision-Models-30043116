from datetime import UTC, datetime

import pytest

from evidence_check.workflow import is_stale, metrics, outcome, run_pack
from tests.conftest import judgment


def test_code_prechecks_skip_calls_and_keep_all_cases(pack, verifier):
    run = run_pack(pack, verifier)
    assert len(run.results) == 12
    assert len(verifier.calls) == 10
    assert "C09" not in verifier.calls and "C10" not in verifier.calls
    summary = metrics(pack, run, 0.8)
    assert summary["label_agreement"] == 12
    assert summary["semantic_agreement"] == summary["semantic_total"] == 10
    assert summary["evidence_agreement"] == summary["evidence_total"] == 10
    assert summary["validation_agreement"] == summary["validation_total"] == 2
    assert all(pair["consistent"] for pair in summary["regressions"])


def test_api_failures_remain_in_the_agreement_denominator(pack, verifier):
    original = verifier.assess

    def fail_one(pack, case):
        if case.id == "C01":
            raise TimeoutError("This payload must not be exported.")
        return original(pack, case)

    verifier.assess = fail_one
    run = run_pack(pack, verifier)
    summary = metrics(pack, run, 0.8)
    assert summary["total"] == 12 and summary["label_agreement"] == 11
    assert summary["semantic_total"] == 10 and summary["semantic_agreement"] == 9
    assert summary["errors"] == 1 and summary["api_requests"] == 10
    assert summary["cost_complete"] is False
    assert summary["input_complete"] is False and summary["output_complete"] is False
    assert run.results[0].error == "TimeoutError"
    assert "payload" not in run.model_dump_json()
    assert outcome(run.results[0], 0.8) == "review"
    assert summary["confusion"]["supported"]["error"] == 1


def test_wrong_confident_verdict_is_a_failure_not_a_valid_response_success(pack, verifier):
    original = verifier.assess

    def wrong_one(pack, case):
        if case.id == "C05":
            return judgment("supported", "deployment")
        return original(pack, case)

    verifier.assess = wrong_one
    summary = metrics(pack, run_pack(pack, verifier), 0.8)
    assert summary["label_agreement"] == 11
    assert summary["evidence_agreement"] == 10
    assert summary["unexpected_releases"] == 1
    assert summary["confusion"]["contradicted"]["supported"] == 1


def test_existing_but_wrong_source_id_fails_evidence_agreement(pack, verifier):
    original = verifier.assess

    def wrong_source(pack, case):
        if case.id == "C01":
            return judgment("supported", "automation")
        return original(pack, case)

    verifier.assess = wrong_source
    summary = metrics(pack, run_pack(pack, verifier), 0.8)
    assert summary["label_agreement"] == 12
    assert summary["evidence_agreement"] == 9
    assert summary["unexpected_releases"] == 1


def test_threshold_changes_reuse_answers_and_can_only_change_policy(pack, verifier):
    run = run_pack(pack, verifier)
    original_calls = list(verifier.calls)
    before = metrics(pack, run, 0.8)
    after = metrics(pack, run, 0.99)
    assert after["released"] < before["released"]
    assert after["label_agreement"] == before["label_agreement"]
    assert verifier.calls == original_calls
    assert not is_stale(pack, verifier.model, run)


def test_changed_source_or_model_invalidates_results(pack, verifier):
    run = run_pack(pack, verifier)
    assert is_stale(pack, "another-model", run)
    changed = pack.model_copy(deep=True)
    changed.sources[0].text = "SAML is no longer offered."
    assert is_stale(changed, verifier.model, run)


def test_a_changed_regression_variant_is_visible_even_when_other_cases_pass(pack, verifier):
    run = run_pack(pack, verifier)
    variant = run.results[2]
    variant.verdict = "contradicted"
    variant.judgment = judgment("contradicted", "identity")
    summary = metrics(pack, run, 0.8)
    assert summary["label_agreement"] == 11
    assert summary["regressions"][1]["consistent"] is False


def test_unknown_output_counts_do_not_create_a_complete_token_total(pack, verifier):
    run = run_pack(pack, verifier)
    run.results[0].judgment.usage.output_tokens = None
    summary = metrics(pack, run, 0.8)
    assert summary["input_complete"] is True
    assert summary["output_complete"] is False
    assert summary["cost_complete"] is True


def test_missing_results_cannot_disappear_from_denominator(pack, verifier):
    run = run_pack(pack, verifier)
    run.results.pop()
    with pytest.raises(ValueError, match="every case"):
        metrics(pack, run, 0.8)


def test_all_failed_calls_have_no_observed_cost_records(pack, verifier):
    def fail_all(pack, case):
        raise ConnectionError("offline")

    verifier.assess = fail_all
    before = datetime.now(UTC)
    run = run_pack(pack, verifier)
    after = datetime.now(UTC)
    summary = metrics(pack, run, 0.8)
    assert summary["known_cost_records"] == 0
    assert not summary["cost_complete"]
    assert summary["label_agreement"] == 2
    assert summary["errors"] == 10
    assert before <= datetime.fromisoformat(run.started_at) <= after
