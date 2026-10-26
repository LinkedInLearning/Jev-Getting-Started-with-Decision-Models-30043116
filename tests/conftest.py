import json
from pathlib import Path

import pytest

from ats_match.data import load_samples
from ats_match.domain import Assessment, validate_evidence


@pytest.fixture
def workspace():
    return load_samples()


@pytest.fixture
def assessments(workspace):
    job, resumes, _ = workspace
    raw = json.loads((Path(__file__).parent / "fixtures/assessments.json").read_text())
    result = {}
    for resume in resumes:
        answer = Assessment.model_validate(raw["assessments"][resume.id])
        validate_evidence(answer, job, resume)
        result[resume.id] = answer
    return result
