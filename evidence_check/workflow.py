"""Run reference checks and measure both judgments and resulting application behavior."""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime
from statistics import median

from evidence_check.domain import Case, CaseResult, ReferencePack, Run, fingerprint
from evidence_check.engine import QUESTION_SPEC


def normalize_quote(text: str) -> str:
    table = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})
    return re.sub(r"\s+", " ", text.translate(table)).strip()


def precheck(pack: ReferencePack, case: Case) -> CaseResult | None:
    if not set(case.source_ids) <= set(pack.source_map):
        raise ValueError("Unknown source ID. Check the reference pack.")
    if not case.source_ids:
        return CaseResult(
            case_id=case.id,
            verdict="insufficient_evidence",
            evidence_id="none",
            validation="no_source",
        )
    if case.quote and not any(
        normalize_quote(case.quote) in normalize_quote(pack.source_map[key].text)
        for key in case.source_ids
    ):
        return CaseResult(
            case_id=case.id,
            verdict="insufficient_evidence",
            evidence_id="none",
            validation="quote_missing",
        )
    return None


def run_pack(pack: ReferencePack, verifier) -> Run:
    started_at = datetime.now(UTC).isoformat()
    started = time.perf_counter()
    results = []
    for case in pack.cases:
        item_started = time.perf_counter()
        result = precheck(pack, case)
        if result is None:
            try:
                judgment = verifier.assess(pack, case)
                result = CaseResult(
                    case_id=case.id,
                    verdict=judgment.verdict,
                    evidence_id=judgment.evidence_id,
                    judgment=judgment,
                    api_attempted=True,
                )
            except Exception as error:
                # Do not include provider payloads or credentials in exported failures.
                result = CaseResult(
                    case_id=case.id,
                    error=type(error).__name__,
                    api_attempted=True,
                )
        result.seconds = time.perf_counter() - item_started
        results.append(result)
    return Run(
        started_at=started_at,
        fingerprint=fingerprint(pack, verifier.model, QUESTION_SPEC),
        requested_model=verifier.model,
        seconds=time.perf_counter() - started,
        results=results,
    )


def outcome(result: CaseResult, confidence_floor: float) -> str:
    if result.error:
        return "review"
    if result.validation == "quote_missing":
        return "blocked"
    if result.validation != "ok" or result.verdict == "insufficient_evidence":
        return "review"
    judgment = result.judgment
    if not judgment or result.evidence_id == "none":
        return "review"
    if min(judgment.confidence, judgment.evidence_confidence) < confidence_floor:
        return "review"
    return "ready" if result.verdict == "supported" else "blocked"


def metrics(pack: ReferencePack, run: Run, confidence_floor: float) -> dict:
    by_id = {result.case_id: result for result in run.results}
    if set(by_id) != {case.id for case in pack.cases} or len(by_id) != len(run.results):
        raise ValueError("A result is required for every case exactly once.")
    matched = evidence_matched = validations_matched = released = bad_releases = reviews = 0
    semantic_total = semantic_matched = 0
    confusion = {
        label: {
            actual: 0 for actual in ("supported", "contradicted", "insufficient_evidence", "error")
        }
        for label in ("supported", "contradicted", "insufficient_evidence")
    }
    for case in pack.cases:
        result = by_id[case.id]
        agreed = result.error is None and result.verdict == case.expected
        matched += agreed
        if case.expected_validation != "ok":
            validations_matched += (
                result.error is None and result.validation == case.expected_validation
            )
        action = outcome(result, confidence_floor)
        released += action == "ready"
        bad_releases += action == "ready" and (
            not agreed or result.evidence_id not in case.expected_evidence
        )
        reviews += action == "review"
        if case.expected_validation == "ok":
            semantic_total += 1
            semantic_matched += agreed
            evidence_matched += (
                result.error is None and result.evidence_id in case.expected_evidence
            )
            confusion[case.expected][result.verdict if not result.error else "error"] += 1
    pairs = []
    for case in pack.cases:
        if not case.same_as:
            continue
        left, right = by_id[case.same_as], by_id[case.id]
        pairs.append(
            {
                "base": case.same_as,
                "variant": case.id,
                "consistent": not left.error
                and not right.error
                and left.verdict == right.verdict
                and left.evidence_id == right.evidence_id,
            }
        )
    api_results = [result for result in run.results if result.api_attempted]
    judgments = [result.judgment for result in api_results if result.judgment]
    input_complete = all(judgment.usage.input_tokens is not None for judgment in judgments) and len(
        judgments
    ) == len(api_results)
    output_complete = all(
        judgment.usage.output_tokens is not None for judgment in judgments
    ) and len(judgments) == len(api_results)
    cost_complete = all(
        judgment.usage.estimated_cost_usd is not None for judgment in judgments
    ) and len(judgments) == len(api_results)
    return {
        "total": len(pack.cases),
        "label_agreement": matched,
        "semantic_agreement": semantic_matched,
        "semantic_total": semantic_total,
        "evidence_agreement": evidence_matched,
        "evidence_total": semantic_total,
        "validation_agreement": validations_matched,
        "validation_total": len(pack.cases) - semantic_total,
        "released": released,
        "unexpected_releases": bad_releases,
        "reviews": reviews,
        "errors": sum(result.error is not None for result in run.results),
        "api_requests": len(api_results),
        "input_tokens": sum(judgment.usage.input_tokens or 0 for judgment in judgments),
        "output_tokens": sum(judgment.usage.output_tokens or 0 for judgment in judgments),
        "input_complete": input_complete,
        "output_complete": output_complete,
        "estimated_cost_usd": sum(judgment.usage.estimated_cost_usd or 0 for judgment in judgments),
        "known_cost_records": sum(
            judgment.usage.estimated_cost_usd is not None for judgment in judgments
        ),
        "cost_complete": cost_complete,
        "median_api_seconds": median([result.seconds for result in api_results])
        if api_results
        else None,
        "regressions": pairs,
        "confusion": confusion,
    }


def is_stale(pack: ReferencePack, model: str, run: Run) -> bool:
    return run.fingerprint != fingerprint(pack, model, QUESTION_SPEC)
