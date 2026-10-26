"""Evidence Check web application."""

from __future__ import annotations

import base64
import html
import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from evidence_check.domain import load_pack
from evidence_check.engine import DEFAULT_MODEL, PRICE_SOURCE, QUESTION_SPEC, JevVerifier
from evidence_check.workflow import is_stale, metrics, outcome, run_pack

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env", override=True)
st.set_page_config(page_title="Evidence Check", page_icon="▣", layout="wide")

font = base64.b64encode((ROOT / "assets/app/host-grotesk.woff2").read_bytes()).decode()
css = (ROOT / "evidence_check/style.css").read_text()
st.markdown(
    f"<style>@font-face {{font-family: Host; src: url(data:font/woff2;base64,{font});}}{css}</style>",
    unsafe_allow_html=True,
)

pack = load_pack(ROOT / "data/reference_pack.json")
api_key = os.getenv("TYPESAFE_API_KEY", "").strip()
configured_model = os.getenv("TYPESAFE_MODEL", DEFAULT_MODEL)
connection = "API key configured" if api_key else "API key required"
dot_class = "dot connected" if api_key else "dot"
st.markdown(
    f'<div class="app-header"><div class="brand">Evidence Check</div><div class="connection"><span class="{dot_class}"></span>{connection}</div></div>',
    unsafe_allow_html=True,
)
st.title("Review claims before release")
st.write("Check whether product claims are supported by their cited sources.")
st.caption(
    f"{len(pack.cases)} labeled checks · {len(pack.sources)} source passages · TypeSafe only"
)

with st.expander("Run settings"):
    settings_left, settings_right = st.columns([1, 1])
    with settings_left:
        model = st.text_input("Jev model", value=configured_model)
        st.caption("A versioned model makes comparisons easier to reproduce.")
    with settings_right:
        floor = st.slider("Minimum confidence for a ready verdict", 0.0, 1.0, 0.8, 0.05)
        st.caption("Example policy. This changes the action, not the saved model answers.")
    st.caption("Changing the model requires a new run. Threshold changes do not call the API.")

if not api_key:
    st.info(
        "Add TYPESAFE_API_KEY to .env, then refresh. You can inspect every claim and source before running Jev."
    )

run_button, clear_button, _ = st.columns([1.25, 1, 3])
with run_button:
    execute = st.button(
        "Run all checks", type="primary", width="stretch", disabled=not api_key or not model.strip()
    )
with clear_button:
    if st.button("Clear results", width="stretch", disabled="run" not in st.session_state):
        st.session_state.pop("run", None)
        st.session_state.pop("previous_run", None)
        st.rerun()

if execute:
    verifier = JevVerifier(api_key, model.strip())
    try:
        with st.spinner("Checking claims against their sources..."):
            new_run = run_pack(pack, verifier)
        if st.session_state.get("run"):
            st.session_state["previous_run"] = st.session_state["run"]
        st.session_state["run"] = new_run
    finally:
        verifier.close()
    st.rerun()

run = st.session_state.get("run")
stale = bool(run and is_stale(pack, model.strip(), run))
if stale:
    st.warning(
        "These results use a different model or reference pack. Run the checks again before using the comparison."
    )

if run and not stale:
    summary = metrics(pack, run, floor)
    columns = st.columns(4)
    columns[0].metric("Verdict agreement", f"{summary['label_agreement']}/{summary['total']}")
    columns[1].metric(
        "Evidence ID agreement", f"{summary['evidence_agreement']}/{summary['evidence_total']}"
    )
    columns[2].metric("Unexpected ready verdicts", summary["unexpected_releases"])
    columns[3].metric("Sent to review", f"{summary['reviews']}/{summary['total']}")
    st.caption(
        "API failures count as failed checks. A valid source ID does not prove that its passage supports a claim."
    )
else:
    st.markdown(
        '<div class="empty">No current results. Expected labels are available below. Actual verdicts appear only after a live run.</div>',
        unsafe_allow_html=True,
    )

checks_tab, sources_tab = st.tabs(["Checks", "Source library"])
with checks_tab:
    results = {item.case_id: item for item in run.results} if run and not stale else {}
    rows = []
    for case in pack.cases:
        result = results.get(case.id)
        rows.append(
            {
                "ID": case.id,
                "Check": case.title,
                "Expected": case.expected.replace("_", " "),
                "Actual": "API error"
                if result and result.error
                else result.verdict.replace("_", " ")
                if result and result.verdict
                else "Not run",
                "Evidence": result.evidence_id if result else "Not run",
                "Agreement": "Fail"
                if result
                and (
                    result.error
                    or result.verdict != case.expected
                    or result.evidence_id not in case.expected_evidence
                    or result.validation != case.expected_validation
                )
                else "Pass"
                if result
                else "Pending",
                "Action": outcome(result, floor).title() if result else "Pending",
            }
        )
    st.dataframe(rows, hide_index=True, width="stretch", height=460)
    selected_id = st.selectbox(
        "Inspect a check",
        [case.id for case in pack.cases],
        format_func=lambda key: next(
            f"{case.id} · {case.title}" for case in pack.cases if case.id == key
        ),
    )
    case = next(case for case in pack.cases if case.id == selected_id)
    result = results.get(case.id)
    st.markdown(f'<div class="claim">{html.escape(case.claim)}</div>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Cited sources")
        if not case.source_ids:
            st.caption(
                "No source was supplied. Code sends this check to review without an API call."
            )
        for source_id in case.source_ids:
            source = pack.source_map[source_id]
            st.markdown(
                f'<div class="source"><strong>{html.escape(source.id)} · {html.escape(source.title)}</strong>{html.escape(source.text)}</div>',
                unsafe_allow_html=True,
            )
        if case.quote:
            st.caption("Alleged verbatim quote")
            st.write(case.quote)
    with right:
        st.subheader("Expected and actual")
        expected_column, actual_column = st.columns(2)
        expected_column.markdown(
            f'<div class="result"><span>Expected verdict</span><strong>{case.expected.replace("_", " ").title()}</strong><br>Source: {html.escape(" or ".join(case.expected_evidence))}</div>',
            unsafe_allow_html=True,
        )
        actual_label = (
            "API error"
            if result and result.error
            else result.verdict.replace("_", " ").title()
            if result and result.verdict
            else "Not run"
        )
        actual_column.markdown(
            f'<div class="result"><span>Actual verdict</span><strong>{actual_label}</strong><br>Source: {html.escape(result.evidence_id or "none") if result else "Not run"}</div>',
            unsafe_allow_html=True,
        )
        st.caption(case.note)
        if result:
            action = outcome(result, floor)
            st.markdown(
                f'<div class="badge {action}">{action.title()}</div>', unsafe_allow_html=True
            )
            if result.error:
                st.error(
                    f"Request failed ({result.error}). No judgment was returned. This check counts as a failure."
                )
            elif result.validation != "ok":
                st.write(
                    "No cited source was supplied."
                    if result.validation == "no_source"
                    else "The alleged verbatim quote was not found in the cited source."
                )
                st.caption("Deterministic source check. No model call and no model confidence.")
            elif result.judgment:
                st.caption(
                    f"Verdict confidence {result.judgment.confidence:.2f} · Evidence confidence {result.judgment.evidence_confidence:.2f}"
                )
                st.bar_chart(
                    {
                        label.replace("_", " ").title(): value
                        for label, value in result.judgment.probabilities.items()
                    },
                    horizontal=True,
                    color="#546c5e",
                    height=190,
                )
        with st.expander("Question and expected labels"):
            st.write(QUESTION_SPEC["relation"]["instructions"])
            st.json(QUESTION_SPEC["relation"]["criteria"])
            st.caption("Expected labels are test data. They are never included in the API request.")
            if case.reverse_options:
                st.write("This case reverses the order of both Choice option lists.")

with sources_tab:
    st.caption(pack.description)
    for source in pack.sources:
        st.markdown(
            f'<div class="source"><strong>{html.escape(source.id)} · {html.escape(source.title)}</strong>{html.escape(source.text)}</div>',
            unsafe_allow_html=True,
        )

if run and not stale:
    with st.expander("Analysis details"):
        st.subheader("Run receipt")
        columns = st.columns(4)
        columns[0].metric("Wall time", f"{run.seconds:.2f} s")
        columns[1].metric("API requests", summary["api_requests"])
        columns[2].metric("API errors", summary["errors"])
        cost_prefix = "" if summary["cost_complete"] else "Observed "
        cost_display = (
            f"{cost_prefix}${summary['estimated_cost_usd']:.6f}"
            if summary["known_cost_records"]
            else "Unavailable"
        )
        columns[3].metric("Estimated API cost", cost_display)
        input_usage = (
            f"{summary['input_tokens']:,}"
            if summary["input_complete"]
            else f"{summary['input_tokens']:,} observed, incomplete"
        )
        output_usage = (
            f"{summary['output_tokens']:,}"
            if summary["output_complete"]
            else "Unavailable for the full run"
        )
        st.caption(
            f"Input tokens: {input_usage}. Output tokens: {output_usage}. Automatic retries are disabled."
        )
        st.caption(
            f"Pricing estimate: {PRICE_SOURCE}. Output tokens are free. This is not an invoice."
        )
        if (
            not summary["input_complete"]
            or not summary["output_complete"]
            or not summary["cost_complete"]
        ):
            st.warning(
                "Some requests lack usage or a known price. Observed totals are incomplete. Failed requests may still be billable."
            )
        models = sorted({result.judgment.model for result in run.results if result.judgment})
        st.caption(
            f"Started {run.started_at}. Resolved models: {', '.join(models) or 'none returned'}. Live results, no replay cache."
        )
        st.subheader("What the checks measure")
        st.write(
            f"Semantic verdict agreement: {summary['semantic_agreement']}/{summary['semantic_total']}. Source precheck agreement: {summary['validation_agreement']}/{summary['validation_total']}."
        )
        st.caption(
            "The main verdict total includes code checks. Semantic agreement excludes those two prechecks. Evidence ID agreement compares against labeled relevant passages, not ID existence alone."
        )
        st.dataframe(
            [
                {"Expected": expected, **actuals}
                for expected, actuals in summary["confusion"].items()
            ],
            hide_index=True,
            width="stretch",
        )
        st.subheader("Regression pairs")
        st.dataframe(summary["regressions"], hide_index=True, width="stretch")
        st.caption(
            "Changed answers are a regression signal. Consistency on a few cases does not prove robustness. Keep the original expected labels."
        )
        previous = st.session_state.get("previous_run")
        if previous and previous.fingerprint == run.fingerprint:
            old = {item.case_id: item for item in previous.results}
            changed = [
                item.case_id
                for item in run.results
                if (item.verdict, item.evidence_id, item.error)
                != (
                    old[item.case_id].verdict,
                    old[item.case_id].evidence_id,
                    old[item.case_id].error,
                )
            ]
            st.write(f"Changed since the previous identical run: {', '.join(changed) or 'none'}.")
        st.download_button(
            "Download run JSON",
            json.dumps(
                {
                    "reference_pack": pack.model_dump(),
                    "run": run.model_dump(),
                    "policy_confidence_floor": floor,
                    "metrics": summary,
                },
                indent=2,
            ),
            file_name="evidence-check-results.json",
            mime="application/json",
        )

st.markdown(
    '<div class="app-footer">Evidence Check · Source-based judgments for human review. Ready is a local status, no content is published.</div>',
    unsafe_allow_html=True,
)
