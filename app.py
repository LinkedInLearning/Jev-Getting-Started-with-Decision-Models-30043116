"""RoleMatch: an LLM baseline for the Jev course. Run: uv run streamlit run app.py."""

from __future__ import annotations

import base64
import html
import os
from dataclasses import replace

import streamlit as st
from pydantic import ValidationError

from ats_match.data import ROOT, load_samples, make_job, read_resume
from ats_match.domain import DEPTH_LEVELS, STATUS_LABELS, fingerprint
from ats_match.llm import LLMMatcher, LLMSettings
from ats_match.preview import preview_assessments
from ats_match.workflow import evaluate, results_csv, run_matching

st.set_page_config(page_title="RoleMatch | Resume evidence", page_icon="◈", layout="wide")


def styles():
    font = ROOT / "assets" / "app" / "host-grotesk.woff2"
    face = ""
    if font.exists():
        encoded = base64.b64encode(font.read_bytes()).decode()
        face = f"@font-face{{font-family:Host;src:url(data:font/woff2;base64,{encoded}) format('woff2');font-display:swap;}}"
    st.markdown(
        f"<style>{face}{(ROOT / 'ats_match' / 'style.css').read_text()}</style>",
        unsafe_allow_html=True,
    )


def badge(text, status="neutral"):
    return f'<span class="pill {html.escape(status)}">{html.escape(str(text))}</span>'


def money(value):
    return "Unavailable" if value is None else f"${value:.6f}"


def matrix(job, resumes, assessments, errors):
    headers = "".join(f'<th title="{html.escape(r.text)}">{r.id}</th>' for r in job.requirements)
    body = []
    for resume in resumes:
        assessment = assessments.get(resume.id)
        if assessment is None:
            cells = f'<td colspan="{len(job.requirements) + 1}">{badge("Request failed", "unclear")}</td>'
        else:
            by_id = {m.requirement_id: m for m in assessment.matches}
            direct = sum(m.status.value == "direct" for m in assessment.matches)
            cells = f'<td class="coverage">{direct}<span> / {len(job.requirements)}</span></td>'
            for r in job.requirements:
                m = by_id[r.id]
                short = {
                    "direct": "Direct",
                    "related": "Related",
                    "not_stated": "Not stated",
                    "unclear": "Unclear",
                }
                cells += f"<td>{badge(short[m.status.value], m.status.value)}</td>"
        body.append(f'<tr><td class="resume-name">{html.escape(resume.label)}</td>{cells}</tr>')
    st.markdown(
        '<div class="matrix-wrap"><table class="matrix"><thead><tr>'
        f"<th>Resume</th><th>Direct matches</th>{headers}</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>",
        unsafe_allow_html=True,
    )
    for req in job.requirements:
        st.caption(f"{req.id} · {req.text}")
    for label, error in errors.items():
        st.error(f"{label}: {error}")


def receipt_panel(run):
    summary = run.summary
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Run time", f"{summary['wall_seconds']:.2f}s")
    cost_label = {
        "reported": "Reported API cost",
        "estimated": "Estimated API cost",
        "unavailable": "API cost",
    }[summary["cost_basis"]]
    col2.metric(cost_label, money(summary["total_cost_usd"]))
    col3.metric(
        "Input tokens",
        f"{summary['input_tokens']:,}" if summary["input_tokens"] is not None else "Unavailable",
    )
    col4.metric(
        "Output tokens",
        f"{summary['output_tokens']:,}" if summary["output_tokens"] is not None else "Unavailable",
    )
    st.caption(
        f"{summary['succeeded']} completed · {summary['failed']} failed · "
        f"{summary['api_calls']} model requests · Median request {summary['median_call_seconds']:.2f}s"
    )
    if summary["total_cost_usd"] is None:
        st.caption("A complete cost was not available. Missing usage is never counted as free.")
    elif summary["cost_basis"] == "estimated":
        st.caption(
            "Cost is estimated from returned tokens and the saved price snapshot. It is not a billing receipt."
        )


def inspector(job, resume, assessment):
    for requirement in job.requirements:
        match = next(m for m in assessment.matches if m.requirement_id == requirement.id)
        st.markdown(
            '<div class="requirement-row"><div><span class="req-id">'
            + html.escape(requirement.id)
            + "</span><strong>"
            + html.escape(requirement.text)
            + "</strong></div>"
            + badge(STATUS_LABELS[match.status.value], match.status.value)
            + "</div>",
            unsafe_allow_html=True,
        )
        if match.evidence_line_ids:
            for line in match.evidence_line_ids:
                st.markdown(
                    f'<div class="evidence"><span>{line}</span>{html.escape(resume.lines[line])}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No supporting evidence is stated in this resume.")
    st.markdown("#### Additional evidence checks")
    a, b = st.columns(2)
    production = {"yes": "Described", "not_stated": "Not stated", "unclear": "Unclear"}
    a.metric("Production API delivery", production[assessment.production_api.status])
    b.metric("Backend delivery depth", f"{assessment.backend_depth.level} / 2")
    st.caption(DEPTH_LEVELS[assessment.backend_depth.level])
    with st.expander("Read the full resume"):
        for line, text in resume.lines.items():
            st.write(f"{line} · {text}")


styles()
sample_job, sample_resumes, labels = load_samples()
try:
    settings = LLMSettings.from_env()
except (ValueError, ValidationError):
    st.error(
        "The local .env settings are invalid. Check provider, token limits, and non-negative prices."
    )
    st.stop()

with st.sidebar:
    st.markdown('<div class="wordmark"><span>◈</span> RoleMatch</div>', unsafe_allow_html=True)
    st.write("Resume evidence workbench")
    st.divider()
    st.markdown("### Matching engine")
    st.write("LLM baseline")
    provider = st.selectbox(
        "Provider", ["openrouter", "openai"], index=0 if settings.provider == "openrouter" else 1
    )
    default_model = (
        settings.model
        if provider == settings.provider
        else ("openai/gpt-4.1-mini" if provider == "openrouter" else "gpt-4.1-mini")
    )
    model = st.text_input("Model", value=default_model, key=f"model_{provider}").strip()
    key_name = "OPENROUTER_API_KEY" if provider == "openrouter" else "OPENAI_API_KEY"
    api_key = os.getenv(key_name, "").strip()
    configured = bool(api_key and model)
    st.markdown(
        badge(
            "API key configured" if configured else "API key needed",
            "direct" if configured else "related",
        ),
        unsafe_allow_html=True,
    )
    if not configured:
        st.caption(f"Add {key_name} to .env in the repository root.")
    if st.button("Reload configuration", use_container_width=True):
        st.rerun()
    st.divider()
    st.markdown("### Evidence, not assumptions")
    st.caption(
        "Not stated means the resume does not document it. Review the source text before drawing conclusions."
    )
    st.caption("Sample resumes are synthetic. Matching results support recruiter review.")

st.title("Match resume evidence to a role.")
st.write("Compare job requirements, inspect the source text, and measure the cost of each run.")
workbench, history, recording = st.tabs(["Matching workbench", "Run history", "Recording notes"])

with workbench:
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("### Job requirements")
            title = st.text_input("Role", value=sample_job.title)
            with st.expander("Edit job description and criteria"):
                description = st.text_area(
                    "Job description", value=sample_job.description, height=150
                )
                requirement_text = st.text_area(
                    "Requirements, one per line",
                    value="\n".join(r.text for r in sample_job.requirements),
                    height=145,
                    help="Use 1 to 8 explicit, job-related requirements. IDs follow their order.",
                )
            display_requirements = [
                line.strip().removeprefix("- ").strip()
                for line in requirement_text.splitlines()
                if line.strip()
            ]
            for i, line in enumerate(display_requirements, 1):
                st.markdown(f"**R{i:02d}**  {line}")
    with right:
        with st.container(border=True):
            st.markdown("### Resumes")
            source = st.radio(
                "Resume source", ["Course samples", "Upload resumes"], horizontal=True
            )
            resumes = []
            if source == "Course samples":
                selected = st.multiselect(
                    "Select resumes",
                    options=[r.id for r in sample_resumes],
                    default=[r.id for r in sample_resumes],
                    format_func=lambda rid: next(r.label for r in sample_resumes if r.id == rid),
                )
                resumes = [r for r in sample_resumes if r.id in selected]
                st.caption(
                    "Three synthetic examples: documented delivery, adjacent experience, and conflicting evidence."
                )
            else:
                uploads = st.file_uploader(
                    "Upload resumes",
                    type=["pdf", "txt"],
                    accept_multiple_files=True,
                    help="Text-based PDFs or UTF-8 text. Up to 10 resumes, 2 MB each.",
                )
                if len(uploads) > 10:
                    st.error("Choose at most 10 resumes for one run.")
                else:
                    for i, upload in enumerate(uploads, 1):
                        try:
                            resumes.append(read_resume(upload.name, upload.getvalue(), i))
                        except (ValueError, ValidationError) as exc:
                            st.error(f"{upload.name}: {exc}")
                st.caption("Resume text is sent to the selected LLM provider when you run a match.")
            st.caption(f"{len(resumes)} resumes selected. One model request per resume.")

    try:
        job = make_job(title, description, requirement_text)
    except (ValidationError, ValueError):
        st.error(
            "Enter a role, a job description, and 1 to 8 requirements of at least 3 characters each."
        )
        job = None
    run_clicked = st.button(
        "Run LLM match",
        type="primary",
        use_container_width=True,
        disabled=not (configured and resumes and job),
    )
    if run_clicked:
        active_settings = replace(settings, provider=provider, model=model, api_key=api_key)
        if active_settings.manual_price and active_settings.manual_price.model != model:
            active_settings.manual_price = None
        matcher = LLMMatcher(active_settings)
        progress = st.progress(0, text="Starting the matching run...")
        try:
            run = run_matching(
                job,
                resumes,
                matcher,
                progress=lambda done, total, name: progress.progress(
                    done / total, text=f"Reviewed {done}/{total}: {name}"
                ),
            )
        finally:
            matcher.close()
            progress.empty()
        st.session_state["last_run"] = run
        st.session_state.setdefault("runs", []).append(run)

    current_run = st.session_state.get("last_run")
    active_run = (
        current_run
        if job and current_run and current_run.input_hash == fingerprint(job, resumes)
        else None
    )
    assessments = {}
    errors = {}
    preview = False
    if active_run:
        assessments = {r.resume_id: r.assessment for r in active_run.results if r.assessment}
        resume_by_id = {r.id: r for r in resumes}
        errors = {resume_by_id[r.resume_id].label: r.error for r in active_run.results if r.error}
    elif job == sample_job and resumes and all(r in sample_resumes for r in resumes):
        assessments = preview_assessments(job, resumes)
        preview = True

    st.markdown("### Evidence comparison")
    if preview:
        st.info(
            "Sample preview: hand-authored labels. Run the LLM for live results and measurements."
        )
    elif current_run and not active_run:
        st.info(
            "Inputs changed. Run the match again to evaluate this version. Your previous result is in Run history."
        )
    if active_run:
        receipt_panel(active_run)
    if assessments or errors:
        matrix(job, resumes, assessments, errors)
        st.caption(
            "Direct matches count explicit evidence across the listed requirements. They are not a hiring score."
        )
        if assessments:
            st.markdown("### Inspect the evidence")
            selected_resume = st.selectbox(
                "Resume to inspect",
                options=[r.id for r in resumes if r.id in assessments],
                format_func=lambda rid: next(r.label for r in resumes if r.id == rid),
            )
            resume = next(r for r in resumes if r.id == selected_resume)
            inspector(job, resume, assessments[selected_resume])
    elif not preview:
        st.caption("Select resumes and run the LLM to build an evidence comparison.")
    if active_run:
        quality = evaluate(active_run, sample_job, sample_resumes, labels)
        with st.expander("Run receipt and sample evaluation"):
            if quality:
                st.write(
                    f"Sample requirement-label agreement: {quality['correct']} / {quality['total']}"
                )
                extra = quality["additional_checks"]
                st.write(
                    f"Additional evidence-check agreement: {extra['correct']} / {extra['total']}"
                )
                st.caption(
                    "Additional checks cover production API delivery and backend delivery depth. Compared with the hand-labeled synthetic examples. Failed requests count as disagreements. This small set is not a production accuracy estimate."
                )
                if quality["disagreements"]:
                    st.json(quality["disagreements"])
                if extra["disagreements"]:
                    st.json(extra["disagreements"])
            else:
                st.caption("No reference labels are available for these edited or uploaded inputs.")
            st.json([r.receipt.model_dump(mode="json") for r in active_run.results])
        a, b = st.columns(2)
        a.download_button(
            "Download evidence CSV",
            results_csv(active_run),
            "resume-evidence.csv",
            "text/csv",
            use_container_width=True,
        )
        b.download_button(
            "Download complete run JSON",
            active_run.model_dump_json(indent=2),
            f"llm-run-{active_run.id}.json",
            "application/json",
            use_container_width=True,
            help="Includes job text, resume text, answers, model IDs, and measurements.",
        )

with history:
    st.markdown("### Run history")
    runs = st.session_state.get("runs", [])
    if not runs:
        st.write("Your live LLM runs will appear here.")
        st.caption("The sample preview never creates a run or records a cost.")
    for run in reversed(runs):
        with st.expander(
            f"{run.started_at[:19]} UTC | {run.job.title} | {len(run.resumes)} resumes"
        ):
            receipt_panel(run)
            st.caption(
                f"Run {run.id} · Input snapshot {run.input_hash[:12]} · {run.prompt_version}"
            )
            st.download_button(
                "Download this run",
                run.model_dump_json(indent=2),
                f"llm-run-{run.id}.json",
                "application/json",
                key=f"history_{run.id}",
            )

with recording:
    st.markdown("### The LLM starter")
    st.write(
        "This branch contains one working LLM implementation. The matching interface, sample inputs, application logic, and measurements are separate."
    )
    st.markdown(
        "1. Show the three sample resumes and four requirements.\n2. Run the LLM and inspect one answer against its source lines.\n3. Open `ats_match/llm.py` to explain the current inference step.\n4. Save a live run as the baseline before changing the engine."
    )
    st.markdown("### A fair comparison")
    st.write(
        "Keep the job, resume text, criteria, and reference labels fixed. Compare model-request time, full-run time, reported or estimated cost, failed requests, and label agreement."
    )
    st.caption(
        "The baseline uses compact schema-constrained JSON. It does not generate a narrative for every resume."
    )
    st.code(
        "uv run python -m ats_match.benchmark --out runs/llm-baseline.json --repeats 3",
        language="bash",
    )
