"""An explicit UI preview, never a substitute for an LLM or a benchmark result."""

import json

from ats_match.data import ROOT
from ats_match.domain import Assessment, validate_evidence


def preview_assessments(job, resumes):
    raw = json.loads((ROOT / "data" / "preview_assessments.json").read_text())
    result = {}
    for resume in resumes:
        assessment = Assessment.model_validate(raw["assessments"][resume.id])
        validate_evidence(assessment, job, resume)
        result[resume.id] = assessment
    return result
