"""The app calls this workflow. Provider changes should not change its inputs or policy."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from statistics import median
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from ats_match.domain import CandidateResult, Job, Resume, StrictModel, coverage, fingerprint
from ats_match.prompts import PROMPT_VERSION


class Matcher(Protocol):
    def assess(self, job: Job, resume: Resume) -> CandidateResult: ...


class Run(StrictModel):
    id: str
    started_at: str
    prompt_version: str
    input_hash: str
    job: Job
    resumes: list[Resume]
    results: list[CandidateResult]
    wall_seconds: float

    @property
    def summary(self) -> dict:
        receipts = [r.receipt for r in self.results]
        costs = [r.cost_usd for r in receipts]
        return {
            "resumes": len(self.results),
            "succeeded": sum(r.assessment is not None for r in self.results),
            "failed": sum(r.assessment is None for r in self.results),
            "api_calls": sum(r.receipt.latency_seconds > 0 for r in self.results),
            "wall_seconds": self.wall_seconds,
            "median_call_seconds": median(r.latency_seconds for r in receipts) if receipts else 0,
            "input_tokens": (
                sum(r.input_tokens for r in receipts)
                if all(r.input_tokens is not None for r in receipts)
                else None
            ),
            "output_tokens": (
                sum(r.output_tokens for r in receipts)
                if all(r.output_tokens is not None for r in receipts)
                else None
            ),
            "known_cost_usd": sum(c for c in costs if c is not None),
            "total_cost_usd": sum(costs) if all(c is not None for c in costs) else None,
            "cost_basis": (
                "reported"
                if all(r.cost_basis == "reported" for r in receipts)
                else "estimated"
                if all(c is not None for c in costs)
                else "unavailable"
            ),
        }


def run_matching(job: Job, resumes: list[Resume], matcher: Matcher, progress=None) -> Run:
    started_at = datetime.now(UTC).isoformat()
    started = perf_counter()
    results = []
    for i, resume in enumerate(resumes):
        results.append(matcher.assess(job, resume))
        if progress:
            progress(i + 1, len(resumes), resume.label)
    return Run(
        id=uuid4().hex[:12],
        started_at=started_at,
        prompt_version=PROMPT_VERSION,
        input_hash=fingerprint(job, resumes),
        job=job,
        resumes=resumes,
        results=results,
        wall_seconds=perf_counter() - started,
    )


def evaluate(
    run: Run, reference_job: Job, reference_resumes: list[Resume], labels: dict
) -> dict | None:
    reference = {r.id: r for r in reference_resumes}
    if run.job != reference_job:
        return None
    if any(reference.get(r.id) != r for r in run.resumes):
        return None
    correct = 0
    total = len(run.resumes) * len(run.job.requirements)
    errors = []
    for result in run.results:
        expected = labels[result.resume_id]["matches"]
        actual = (
            {m.requirement_id: m.status.value for m in result.assessment.matches}
            if result.assessment
            else {}
        )
        for req_id, label in expected.items():
            if actual.get(req_id) == label:
                correct += 1
            else:
                errors.append(
                    {
                        "resume_id": result.resume_id,
                        "requirement_id": req_id,
                        "expected": label,
                        "actual": actual.get(req_id, "request_failed"),
                    }
                )
    return {
        "correct": correct,
        "total": total,
        "agreement": correct / total if total else None,
        "disagreements": errors,
    }


def results_csv(run: Run) -> str:
    out = io.StringIO()
    fields = [
        "resume",
        "requirement_id",
        "requirement",
        "evidence_status",
        "source_lines",
        "model",
        "error",
    ]
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    by_id = {r.id: r for r in run.resumes}
    requirements = {r.id: r.text for r in run.job.requirements}
    for result in run.results:
        receipt = result.receipt
        common = {
            "resume": by_id[result.resume_id].label,
            "model": receipt.actual_model or receipt.requested_model,
            "error": result.error or "",
        }
        if result.assessment:
            for match in result.assessment.matches:
                row = {
                    **common,
                    "requirement_id": match.requirement_id,
                    "requirement": requirements[match.requirement_id],
                    "evidence_status": match.status.value,
                    "source_lines": "; ".join(match.evidence_line_ids),
                }
                writer.writerow({k: csv_safe(v) for k, v in row.items()})
        else:
            writer.writerow({k: csv_safe(v) for k, v in common.items()})
    return out.getvalue()


def csv_safe(value):
    """Keep uploaded filenames and requirement text from becoming spreadsheet formulas."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def table_rows(run: Run) -> list[dict]:
    rows = []
    by_id = {r.id: r for r in run.resumes}
    for result in run.results:
        row = {"Resume": by_id[result.resume_id].label}
        if result.assessment:
            counts = coverage(result.assessment)
            row["Direct evidence"] = f"{counts['direct']} / {len(run.job.requirements)}"
            for m in result.assessment.matches:
                row[m.requirement_id] = m.status.value
            row["Production API"] = result.assessment.production_api.status
            row["Backend depth"] = str(result.assessment.backend_depth.level)
        else:
            row["Direct evidence"] = "Run failed"
        rows.append(row)
    return rows
