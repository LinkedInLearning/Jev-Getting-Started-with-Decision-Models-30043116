from io import BytesIO

import streamlit as st
from streamlit.testing.v1 import AppTest

from ats_match.data import ROOT, load_application_samples
from ats_match.domain import Assessment, CandidateResult, Receipt
from ats_match.llm import LLMSettings


def upload_files():
    files = []
    for path in sorted((ROOT / "output/pdf/resumes").glob("*.pdf")):
        item = BytesIO(path.read_bytes())
        item.name = path.name
        files.append(item)
    return files


def configured(monkeypatch):
    monkeypatch.setattr(
        "ats_match.llm.LLMSettings.from_env", lambda: LLMSettings(api_key="unit-test")
    )


def test_initial_screen_has_real_job_and_uploads_without_preview_or_fake_results(monkeypatch):
    monkeypatch.setattr("ats_match.llm.LLMSettings.from_env", lambda: LLMSettings())
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
    assert not at.exception
    assert not at.sidebar
    assert not at.metric
    description = next(x for x in at.text_area if x.label == "Job description")
    assert "What you will do" in description.value
    assert "Cedarline" in description.value
    assert not any("Sample preview" in x.value for x in at.info)
    assert next(x for x in at.button if x.label == "Analyze applications").disabled


def test_job_selection_loads_the_corresponding_description_and_criteria(monkeypatch):
    configured(monkeypatch)
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
    next(x for x in at.selectbox if x.label == "Job opening").set_value("backend-platform").run()
    assert not at.exception
    assert "Kubernetes" in next(x for x in at.text_area if x.label == "Job description").value
    assert (
        "Prometheus" in next(x for x in at.text_area if x.label == "Criteria, one per line").value
    )


def test_live_analysis_uses_uploaded_pdfs_and_preserves_results_without_extra_calls(monkeypatch):
    configured(monkeypatch)
    monkeypatch.setattr(st, "file_uploader", lambda *args, **kwargs: upload_files())
    _, reference_resumes, labels = load_application_samples()
    reference_by_text = {r.text: labels[r.id] for r in reference_resumes}
    calls = []

    class FakeMatcher:
        def __init__(self, settings):
            pass

        def assess(self, job, resume):
            calls.append(resume.id)
            expected = reference_by_text[resume.text]
            ref = [next(iter(resume.lines))]
            assessment = Assessment.model_validate(
                {
                    "matches": [
                        {
                            "requirement_id": key,
                            "status": value,
                            "evidence_line_ids": [] if value == "not_stated" else ref,
                        }
                        for key, value in expected["matches"].items()
                    ],
                    "production_api": {
                        "status": expected["production_api"],
                        "evidence_line_ids": []
                        if expected["production_api"] == "not_stated"
                        else ref,
                    },
                    "backend_depth": {
                        "level": expected["backend_depth"],
                        "evidence_line_ids": ref if expected["backend_depth"] else [],
                    },
                }
            )
            return CandidateResult(
                resume_id=resume.id,
                assessment=assessment,
                receipt=Receipt(
                    provider="openrouter",
                    requested_model="unit-test",
                    actual_model="unit-test",
                    latency_seconds=1,
                    input_tokens=100,
                    output_tokens=50,
                    cost_usd=0.001,
                    cost_basis="reported",
                ),
            )

        def close(self):
            pass

    monkeypatch.setattr("ats_match.llm.LLMMatcher", FakeMatcher)
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
    next(x for x in at.button if x.label == "Analyze applications").click().run()
    assert not at.exception
    assert len(calls) == 5
    assert len(at.session_state["application_runs"]) == 1
    assert any(x.label == "Total API cost" and x.value == "$0.005000" for x in at.metric)
    assert any("Reference agreement: 20/20 requirement labels" in x.value for x in at.markdown)
    assert any(x.label == "Analysis details" for x in at.expander)
    next(x for x in at.selectbox if x.label == "Applicant").set_value("U02").run()
    assert len(calls) == 5
    next(x for x in at.button if x.label == "Analyze applications").click().run()
    assert len(calls) == 10
    assert len(at.session_state["application_runs"]) == 2
    assert len(next(x for x in at.selectbox if x.label == "Analysis run").options) == 2
    editor = next(x for x in at.text_area if x.label == "Job description")
    editor.input(editor.value + "\nAdditional project context.").run()
    assert not at.exception
    assert any("changed" in x.value for x in at.info)
    assert len(calls) == 10


def test_invalid_upload_prevents_a_partial_analysis(monkeypatch):
    configured(monkeypatch)
    bad = BytesIO(b"Not a PDF")
    bad.name = "broken.pdf"
    monkeypatch.setattr(st, "file_uploader", lambda *args, **kwargs: upload_files()[:1] + [bad])
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
    assert not at.exception
    assert any("valid PDF" in x.value for x in at.error)
    assert next(x for x in at.button if x.label == "Analyze applications").disabled
