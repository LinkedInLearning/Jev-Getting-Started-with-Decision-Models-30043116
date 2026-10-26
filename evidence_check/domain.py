"""Validated reference data and results."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Verdict = Literal["supported", "contradicted", "insufficient_evidence"]
Validation = Literal["ok", "no_source", "quote_missing"]


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1)
    title: str
    category: str
    claim: str = Field(min_length=1)
    source_ids: list[str]
    quote: str | None = None
    expected: Verdict
    expected_evidence: list[str]
    expected_validation: Validation = "ok"
    reverse_options: bool = False
    same_as: str | None = None
    note: str


class ReferencePack(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    description: str
    sources: list[Source]
    cases: list[Case]

    @model_validator(mode="after")
    def validate_references(self) -> ReferencePack:
        source_ids = [source.id for source in self.sources]
        case_ids = [case.id for case in self.cases]
        if len(source_ids) != len(set(source_ids)) or len(case_ids) != len(set(case_ids)):
            raise ValueError("Source IDs and case IDs must be unique.")
        if "none" in source_ids:
            raise ValueError("The source ID none is reserved.")
        for case in self.cases:
            if len(case.source_ids) != len(set(case.source_ids)):
                raise ValueError(f"{case.id}: duplicate cited source ID.")
            if not set(case.source_ids) <= set(source_ids):
                raise ValueError(f"{case.id}: unknown cited source ID.")
            if not case.expected_evidence:
                raise ValueError(f"{case.id}: expected evidence must include an ID or none.")
            if not set(case.expected_evidence) <= set(case.source_ids) | {"none"}:
                raise ValueError(f"{case.id}: expected evidence must be a cited source or none.")
            if case.same_as and case.same_as not in case_ids:
                raise ValueError(f"{case.id}: unknown regression pair.")
            if case.same_as:
                original = next(item for item in self.cases if item.id == case.same_as)
                if (
                    case.expected != original.expected
                    or case.expected_evidence != original.expected_evidence
                ):
                    raise ValueError(
                        f"{case.id}: regression variants must retain the original labels."
                    )
        return self

    @property
    def source_map(self) -> dict[str, Source]:
        return {source.id: source for source in self.sources}

    def state_for(self, case: Case) -> dict:
        """Never send expected labels, notes, or scenario names to the model."""
        return {
            "claim": case.claim,
            "sources": [self.source_map[key].model_dump() for key in case.source_ids],
        }


class Usage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    price_source: str | None = None


class Judgment(BaseModel):
    verdict: Verdict
    confidence: float = Field(ge=0, le=1)
    probabilities: dict[str, float]
    evidence_id: str
    evidence_confidence: float = Field(ge=0, le=1)
    evidence_probabilities: dict[str, float]
    model: str
    usage: Usage


class CaseResult(BaseModel):
    case_id: str
    verdict: Verdict | None = None
    evidence_id: str | None = None
    validation: Validation = "ok"
    judgment: Judgment | None = None
    error: str | None = None
    seconds: float = 0
    api_attempted: bool = False


class Run(BaseModel):
    fingerprint: str
    requested_model: str
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    seconds: float
    results: list[CaseResult]


def load_pack(path: Path) -> ReferencePack:
    return ReferencePack.model_validate_json(path.read_text())


def fingerprint(pack: ReferencePack, model: str, question: dict) -> str:
    payload = {"pack": pack.model_dump(), "model": model, "question": question}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
