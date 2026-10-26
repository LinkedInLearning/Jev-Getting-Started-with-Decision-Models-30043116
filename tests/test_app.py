from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from evidence_check.domain import load_pack
from evidence_check.workflow import run_pack
from tests.conftest import ReferenceVerifier

APP = Path(__file__).parents[1] / "app.py"


@pytest.fixture(autouse=True)
def isolate_local_credentials(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_MODEL", raising=False)


def test_no_key_screen_has_sources_and_expected_labels_but_no_actual_results(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert app.title[0].value == "Review claims before release"
    assert app.button[0].label == "Run all checks" and app.button[0].disabled
    assert len(app.metric) == 0
    assert set(app.dataframe[0].value["Actual"]) == {"Not run"}
    assert app.selectbox[0].label == "Inspect a check"


def test_saved_results_show_failures_without_another_api_call(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    pack = load_pack(APP.parent / "data/reference_pack.json")
    run = run_pack(pack, ReferenceVerifier())
    run.results[4].verdict = "supported"
    app = AppTest.from_file(str(APP), default_timeout=30)
    app.session_state["run"] = run
    app.run()
    assert not app.exception
    assert app.metric[0].value == "11/12"
    assert app.metric[1].value == "10/10"
    assert app.metric[2].value == "1"
    app.slider[0].set_value(1.0).run()
    assert not app.exception
    assert app.metric[0].value == "11/12"
    assert app.metric[2].value == "0"


def test_changed_model_hides_stale_results(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    pack = load_pack(APP.parent / "data/reference_pack.json")
    app = AppTest.from_file(str(APP), default_timeout=30)
    app.session_state["run"] = run_pack(pack, ReferenceVerifier())
    app.run()
    app.text_input[0].set_value("jev-latest").run()
    assert not app.exception
    assert len(app.metric) == 0
    assert set(app.dataframe[0].value["Actual"]) == {"Not run"}
    assert any("different model" in warning.value for warning in app.warning)


def test_failed_run_cost_is_unavailable_not_zero(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    pack = load_pack(APP.parent / "data/reference_pack.json")
    verifier = ReferenceVerifier()

    def fail_all(pack, case):
        raise ConnectionError("offline")

    verifier.assess = fail_all
    app = AppTest.from_file(str(APP), default_timeout=30)
    app.session_state["run"] = run_pack(pack, verifier)
    app.run()
    assert not app.exception
    cost_metric = next(metric for metric in app.metric if metric.label == "Estimated API cost")
    assert cost_metric.value == "Unavailable"


def test_completed_run_can_be_cleared_immediately_without_another_model_call(monkeypatch):
    verifier = ReferenceVerifier()
    monkeypatch.setenv("TYPESAFE_API_KEY", "local-test-key")
    monkeypatch.setattr("evidence_check.engine.JevVerifier", lambda api_key, model: verifier)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert app.button[1].label == "Clear results" and app.button[1].disabled
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "12/12"
    assert len(verifier.calls) == 10
    clear = next(button for button in app.button if button.label == "Clear results")
    assert not clear.disabled
    clear.click().run()
    assert not app.exception
    assert not app.metric
    assert set(app.dataframe[0].value["Actual"]) == {"Not run"}
    assert len(verifier.calls) == 10
