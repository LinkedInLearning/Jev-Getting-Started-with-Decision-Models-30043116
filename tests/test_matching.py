import json

import httpx
import pytest
from pydantic import ValidationError

from ats_match.data import make_job, read_resume
from ats_match.domain import (
    Assessment,
    CandidateResult,
    EvidenceStatus,
    PriceSnapshot,
    Receipt,
    validate_evidence,
)
from ats_match.llm import LLMMatcher, LLMSettings, fill_usage
from ats_match.prompts import SYSTEM_PROMPT
from ats_match.workflow import csv_safe, evaluate, results_csv, run_matching


def test_evidence_is_not_a_hiring_decision(workspace, assessments):
    job, resumes, _ = workspace
    assert assessments["C02"].matches[1].status == EvidenceStatus.NOT_STATED
    assert assessments["C03"].matches[1].status == EvidenceStatus.UNCLEAR
    for resume in resumes:
        validate_evidence(assessments[resume.id], job, resume)


def test_unknown_evidence_is_rejected(workspace, assessments):
    job, resumes, _ = workspace
    answer = assessments["C01"].model_copy(deep=True)
    answer.matches[0].evidence_line_ids = ["L99"]
    with pytest.raises(ValueError, match="unknown"):
        validate_evidence(answer, job, resumes[0])


@pytest.mark.parametrize(
    "failure", ["missing", "duplicate", "wrong_id", "empty_evidence", "false_evidence"]
)
def test_response_cannot_silently_drop_or_invent_requirements(workspace, assessments, failure):
    job, resumes, _ = workspace
    answer = assessments["C01"].model_copy(deep=True)
    if failure == "missing":
        answer.matches.pop()
    elif failure == "duplicate":
        answer.matches[1] = answer.matches[0]
    elif failure == "wrong_id":
        answer.matches[0].requirement_id = "R99"
    elif failure == "empty_evidence":
        answer.matches[0].evidence_line_ids = []
    else:
        answer.matches[0].status = EvidenceStatus.NOT_STATED
    with pytest.raises(ValueError):
        validate_evidence(answer, job, resumes[0])


def test_schema_refuses_non_finite_or_out_of_range_values(assessments):
    raw = assessments["C01"].model_dump(mode="json")
    raw["backend_depth"]["level"] = 97
    with pytest.raises(ValidationError):
        Assessment.model_validate(raw)


def receipt(**changes):
    return Receipt(
        requested_model="openai/gpt-4.1-mini", provider="openrouter", latency_seconds=1.2, **changes
    )


def price():
    return PriceSnapshot(
        model="openai/gpt-4.1-mini",
        input_per_million=0.4,
        output_per_million=1.6,
        cached_input_per_million=0.1,
        source="unit-test price",
        checked_at="2026-10-26T00:00:00Z",
    )


def test_reported_cost_overrides_estimates():
    result = fill_usage(
        receipt(),
        {
            "model": "openai/gpt-4.1-mini",
            "usage": {
                "prompt_tokens": 1000,
                "completion_tokens": 100,
                "cost": 0.00047,
            },
        },
        price(),
    )
    assert result.cost_usd == 0.00047
    assert result.cost_basis == "reported"


def test_estimate_accounts_for_cached_input():
    result = fill_usage(
        receipt(),
        {
            "model": "openai/gpt-4.1-mini",
            "usage": {
                "prompt_tokens": 1000,
                "completion_tokens": 100,
                "prompt_tokens_details": {"cached_tokens": 500},
            },
        },
        price(),
    )
    assert result.cost_usd == pytest.approx(0.00041)
    assert result.cost_basis == "estimated"


def test_missing_usage_or_different_model_does_not_become_free():
    assert fill_usage(receipt(), {"model": "openai/gpt-4.1-mini"}, price()).cost_usd is None
    changed = fill_usage(
        receipt(),
        {
            "model": "other/model",
            "usage": {
                "prompt_tokens": 1000,
                "completion_tokens": 100,
            },
        },
        price(),
    )
    assert changed.cost_usd is None


def test_live_adapter_uses_one_schema_constrained_request(workspace, assessments):
    job, resumes, _ = workspace
    posts = []

    def handler(request):
        assert request.method == "POST"
        payload = json.loads(request.content)
        posts.append(payload)
        assert payload["response_format"]["type"] == "json_schema"
        assert payload["response_format"]["json_schema"]["strict"] is True
        assert payload["provider"]["allow_fallbacks"] is False
        assert payload["messages"][0]["content"] == SYSTEM_PROMPT
        state = json.loads(payload["messages"][1]["content"])
        assert state["resume_lines"]["L02"] == resumes[0].lines["L02"]
        return httpx.Response(
            200,
            json={
                "model": "openai/gpt-4.1-mini",
                "id": "test-generation",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": assessments["C01"].model_dump_json(),
                        },
                    }
                ],
                "usage": {"prompt_tokens": 300, "completion_tokens": 100, "cost": 0.0002},
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        matcher = LLMMatcher(LLMSettings(api_key="unit-test", manual_price=price()), client=client)
        result = matcher.assess(job, resumes[0])
    assert len(posts) == 1
    assert result.error is None
    assert result.receipt.cost_usd == 0.0002
    assert result.assessment == assessments["C01"]


@pytest.mark.parametrize(
    "variant", ["truncated", "refused", "invalid_json", "bad_evidence", "http_error"]
)
def test_failed_generation_is_recorded_without_fabricated_fallback(workspace, assessments, variant):
    job, resumes, _ = workspace

    def handler(request):
        if variant == "http_error":
            return httpx.Response(429, json={"error": {"message": "key=SECRET_SHOULD_NOT_ESCAPE"}})
        answer = assessments["C01"].model_copy(deep=True)
        if variant == "bad_evidence":
            answer.matches[0].evidence_line_ids = ["L99"]
        return httpx.Response(
            200,
            json={
                "model": "openai/gpt-4.1-mini",
                "choices": [
                    {
                        "finish_reason": "length" if variant == "truncated" else "stop",
                        "message": {
                            "content": None
                            if variant == "refused"
                            else "not json"
                            if variant == "invalid_json"
                            else answer.model_dump_json()
                        },
                    }
                ],
                "usage": {"prompt_tokens": 300, "completion_tokens": 100, "cost": 0.0002},
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        matcher = LLMMatcher(LLMSettings(api_key="unit-test", manual_price=price()), client=client)
        result = matcher.assess(job, resumes[0])
    assert result.assessment is None
    assert result.error
    assert "SECRET" not in result.error
    if variant != "http_error":
        assert result.receipt.cost_usd == 0.0002


def test_absent_api_key_never_calls_the_network(workspace):
    job, resumes, _ = workspace

    def handler(request):
        pytest.fail("No network request should be made without an API key")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = LLMMatcher(LLMSettings(), client=client).assess(job, resumes[0])
    assert result.error
    assert result.receipt.latency_seconds == 0
    assert result.receipt.cost_usd is None


def test_partial_failures_count_against_quality_and_keep_cost_unknown(workspace, assessments):
    job, resumes, labels = workspace

    class FakeMatcher:
        def assess(self, job, resume):
            if resume.id == "C02":
                return CandidateResult(resume_id=resume.id, error="timeout", receipt=receipt())
            return CandidateResult(
                resume_id=resume.id,
                assessment=assessments[resume.id],
                receipt=receipt(
                    cost_usd=0.001, cost_basis="reported", input_tokens=100, output_tokens=50
                ),
            )

    run = run_matching(job, resumes, FakeMatcher())
    assert run.summary["failed"] == 1
    assert run.summary["total_cost_usd"] is None
    assert run.summary["known_cost_usd"] == 0.002
    assert evaluate(run, job, resumes, labels)["agreement"] == pytest.approx(8 / 12)
    assert "timeout" in results_csv(run)
    edited = [resumes[0].model_copy(update={"text": resumes[0].text + "\nExtra detail"})]
    run.resumes = edited
    assert evaluate(run, job, resumes, labels) is None


def test_input_boundaries():
    with pytest.raises(ValueError):
        read_resume("fake.pdf", b"Not a PDF", 1)
    with pytest.raises(ValueError):
        read_resume("resume.txt", b"\xff\xfe\xff", 1)
    with pytest.raises(ValueError):
        read_resume("resume.docm", b"anything", 1)
    with pytest.raises(ValueError):
        read_resume("resume.txt", b"x" * (2 * 1024 * 1024 + 1), 1)
    with pytest.raises(ValidationError):
        make_job("Role", "A sufficiently long role description.", "a")
    parsed = read_resume("resume.txt", b"Built a Python API.\nDeployed it to production.", 1)
    assert parsed.lines == {"L01": "Built a Python API.", "L02": "Deployed it to production."}


def test_exported_user_text_is_not_a_spreadsheet_formula():
    assert csv_safe('=HYPERLINK("example")').startswith("'")
    assert csv_safe("  @SUM(1,2)").startswith("'")
    assert csv_safe("Python API experience") == "Python API experience"
