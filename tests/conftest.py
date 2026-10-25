import pytest

from ats_match.data import load_samples
from ats_match.preview import preview_assessments


@pytest.fixture
def workspace():
    return load_samples()


@pytest.fixture
def assessments(workspace):
    job, resumes, _ = workspace
    return preview_assessments(job, resumes)
