import pytest
from streamlit.testing.v1 import AppTest

from ats_match.data import ROOT
from ats_match.domain import CandidateResult, Receipt
from ats_match.llm import LLMSettings


def test_preview_is_explicit_and_never_creates_fake_measurements(monkeypatch):
    monkeypatch.setattr("ats_match.llm.LLMSettings.from_env", lambda: LLMSettings())
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
    assert not at.exception
    assert any("Sample preview" in message.value for message in at.info)
    assert len(at.metric) == 2  # Only the clearly labeled sample evidence checks.
    with pytest.raises(KeyError):
        at.session_state["runs"]
    run_button = next(button for button in at.button if button.label == "Run LLM match")
    assert run_button.disabled


def test_live_action_updates_receipts_and_edited_inputs_cannot_reuse_results(
    monkeypatch, assessments
):
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-test")
    monkeypatch.setattr(
        "ats_match.llm.LLMSettings.from_env", lambda: LLMSettings(api_key="unit-test")
    )

    class FakeMatcher:
        def __init__(self, settings):
            pass

        def assess(self, job, resume):
            return CandidateResult(
                resume_id=resume.id,
                assessment=assessments[resume.id],
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
    next(button for button in at.button if button.label == "Run LLM match").click().run()
    assert not at.exception
    assert len(at.session_state["runs"]) == 1
    assert any(
        metric.label == "Reported API cost" and metric.value == "$0.003000" for metric in at.metric
    )
    next(text for text in at.text_input if text.label == "Role").input("Edited role").run()
    assert not at.exception
    assert any("Inputs changed" in message.value for message in at.info)
    assert len(at.session_state["runs"]) == 1
