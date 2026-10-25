"""The common contract for a matching engine. There is no provider code here."""

from __future__ import annotations

import hashlib
import json
import math
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class EvidenceStatus(StrEnum):
    DIRECT = "direct"
    RELATED = "related"
    NOT_STATED = "not_stated"
    UNCLEAR = "unclear"


STATUS_LABELS = {
    "direct": "Direct evidence",
    "related": "Related evidence",
    "not_stated": "Not stated",
    "unclear": "Unclear",
}

DEPTH_LEVELS = [
    "No backend project contribution is documented.",
    "Contributed to backend projects; ownership of production delivery is not documented.",
    "Owned implementation and production delivery of a backend service.",
]


class Requirement(StrictModel):
    id: str
    text: str = Field(min_length=3, max_length=800)


class Job(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=20, max_length=20_000)
    requirements: list[Requirement] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [r.id for r in self.requirements]
        if len(set(ids)) != len(ids):
            raise ValueError("Requirement IDs must be unique.")
        return self


class Resume(StrictModel):
    id: str
    label: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=20, max_length=25_000)

    @property
    def lines(self) -> dict[str, str]:
        return {
            f"L{i:02d}": line.strip()
            for i, line in enumerate((x for x in self.text.splitlines() if x.strip()), 1)
        }


class RequirementMatch(StrictModel):
    requirement_id: str
    status: EvidenceStatus
    evidence_line_ids: list[str] = Field(max_length=6)


class ProductionEvidence(StrictModel):
    status: Literal["yes", "not_stated", "unclear"]
    evidence_line_ids: list[str] = Field(max_length=6)


class DepthEvidence(StrictModel):
    level: int = Field(strict=True, ge=0, le=2)
    evidence_line_ids: list[str] = Field(max_length=6)


class Assessment(StrictModel):
    matches: list[RequirementMatch]
    production_api: ProductionEvidence
    backend_depth: DepthEvidence


class PriceSnapshot(StrictModel):
    model: str
    input_per_million: float = Field(ge=0)
    output_per_million: float = Field(ge=0)
    cached_input_per_million: float | None = Field(default=None, ge=0)
    source: str
    checked_at: str


class Receipt(StrictModel):
    requested_model: str
    actual_model: str | None = None
    provider: str
    request_id: str | None = None
    latency_seconds: float = Field(ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    cached_input_tokens: int | None = Field(default=None, ge=0)
    reasoning_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    cost_basis: Literal["reported", "estimated", "unavailable"] = "unavailable"
    price: PriceSnapshot | None = None


class CandidateResult(StrictModel):
    resume_id: str
    assessment: Assessment | None = None
    receipt: Receipt
    error: str | None = None


def fingerprint(job: Job, resumes: list[Resume]) -> str:
    data = {"job": job.model_dump(), "resumes": [r.model_dump() for r in resumes]}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def validate_evidence(assessment: Assessment, job: Job, resume: Resume) -> None:
    """Validate coverage and source references, without claiming to verify semantics."""
    expected = {r.id for r in job.requirements}
    ids = [m.requirement_id for m in assessment.matches]
    if len(ids) != len(expected) or set(ids) != expected:
        raise ValueError("The response must answer every requirement exactly once.")
    for match in assessment.matches:
        if match.status in (EvidenceStatus.DIRECT, EvidenceStatus.RELATED):
            if not match.evidence_line_ids:
                raise ValueError("Direct and related matches must reference resume lines.")
        if match.status == EvidenceStatus.NOT_STATED and match.evidence_line_ids:
            raise ValueError("A not-stated result cannot cite supporting evidence.")
    if (
        assessment.production_api.status == "yes"
        and not assessment.production_api.evidence_line_ids
    ):
        raise ValueError("Production API evidence needs a source reference.")
    if (
        assessment.production_api.status == "not_stated"
        and assessment.production_api.evidence_line_ids
    ):
        raise ValueError("Not-stated production experience cannot cite supporting evidence.")
    if assessment.backend_depth.level > 0 and not assessment.backend_depth.evidence_line_ids:
        raise ValueError("Backend project experience needs a source reference.")
    sources = [m.evidence_line_ids for m in assessment.matches]
    sources += [
        assessment.production_api.evidence_line_ids,
        assessment.backend_depth.evidence_line_ids,
    ]
    for group in sources:
        if len(group) != len(set(group)) or any(line not in resume.lines for line in group):
            raise ValueError("The response references unknown or duplicate resume lines.")


def coverage(assessment: Assessment) -> dict[str, int]:
    """Counts are application arithmetic, independent of any model."""
    return {
        status.value: sum(m.status == status for m in assessment.matches)
        for status in EvidenceStatus
    }


def finite_number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) and value >= 0 else None
