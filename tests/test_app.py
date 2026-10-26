from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from invoice_intake.core import Result, find_candidates, fingerprint, parse_judgment
from tests.conftest import answer_payload

ROOT = Path(__file__).parents[1]


def test_initial_screen_is_usable_without_a_key(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
    assert not app.exception
    assert app.text_area[0].value.startswith("NORTHLINE")
    assert len(app.selectbox[0].options) == 5
    assert not app.metric
    assert app.dataframe
    assert any("TYPESAFE_API_KEY" in notice.value for notice in app.info)
    app.button[0].click().run()
    assert not app.exception
    assert app.warning[0].value == "Review required"
    assert not app.metric


def test_sample_change_replaces_source(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
    app.selectbox[0].select(app.selectbox[0].options[1]).run()
    assert app.text_area[0].value.startswith("CEDAR")
    assert not app.exception


def test_policy_changes_do_not_rerun_model_and_edited_source_hides_stale_result(monkeypatch):
    calls = []

    def check(text, **_):
        calls.append(text)
        candidates = find_candidates(text)
        payload = answer_payload(candidates, choice="amount_3", top_probability=0.90)
        return Result(
            fingerprint(text),
            candidates,
            parse_judgment(payload, candidates),
            latency_ms=10,
            called_api=True,
        )

    monkeypatch.setattr("invoice_intake.jev.check_invoice", check)
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()
    app.button[0].click().run()
    assert not app.exception
    assert len(calls) == 1
    assert app.success[0].value == "Ready for draft"
    app.slider[0].set_value(0.95).run()
    assert len(calls) == 1
    assert app.warning[0].value == "Review required"
    app.text_area[0].input(app.text_area[0].value + "\nUpdated source").run()
    assert len(calls) == 1
    assert not app.metric
    assert any("source changed" in notice.value for notice in app.info)
    assert not app.exception
