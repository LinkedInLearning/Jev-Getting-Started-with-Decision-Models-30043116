"""RoleMatch applicant review. Run: uv run streamlit run app.py."""

from __future__ import annotations

import base64
import html
from datetime import datetime

import streamlit as st
from pydantic import ValidationError

from ats_match.data import ROOT, application_reference, load_openings, make_job, read_resume
from ats_match.domain import DEPTH_LEVELS, STATUS_LABELS, fingerprint
from ats_match.llm import LLMMatcher, LLMSettings
from ats_match.workflow import evaluate, results_csv, run_matching

st.set_page_config(page_title="Applications | RoleMatch", page_icon="▦", layout="wide")


def styles():
    encoded = base64.b64encode((ROOT / "assets/app/host-grotesk.woff2").read_bytes()).decode()
    st.html(
        "<style>@font-face{font-family:Host;src:url(data:font/woff2;base64,"
        + encoded
        + ") format('woff2');font-display:swap;}"
        + (ROOT / "ats_match/style.css").read_text()
        + "</style>"
    )


def badge(text, status="neutral"):
    return f'<span class="status {html.escape(status)}">{html.escape(str(text))}</span>'


def money(value):
    return "Unavailable" if value is None else f"${value:.6f}"


def applicant_name(resume):
    return resume.label.replace("_", " ").replace("-", " ")


def candidate_table(run):
    names = {r.id: applicant_name(r) for r in run.resumes}
    rows = []
    production = {"yes": "Described", "not_stated": "Not stated", "unclear": "Unclear"}
    for result in run.results:
        name = html.escape(names[result.resume_id])
        if result.assessment is None:
            rows.append(
                f'<tr><td class="candidate-name">{name}</td><td colspan="3">{badge("Analysis failed", "unclear")}</td></tr>'
            )
            continue
        answer = result.assessment
        direct = sum(m.status.value == "direct" for m in answer.matches)
        percentage = round(100 * direct / len(run.job.requirements))
        meter = f'<div class="score"><strong>{percentage}%</strong><progress value="{percentage}" max="100" aria-label="Criteria with direct evidence">{percentage}%</progress><small>{direct} of {len(run.job.requirements)} criteria</small></div>'
        state = answer.production_api.status
        rows.append(
            f'<tr><td class="candidate-name">{name}</td>'
            f"<td>{meter}</td><td>{badge(production[state], 'direct' if state == 'yes' else state)}</td>"
            f'<td><strong>{answer.backend_depth.level}</strong><span class="out-of"> / 2</span></td></tr>'
        )
    st.html(
        '<div class="table-scroll"><table class="candidate-table"><thead><tr>'
        "<th>Applicant</th><th>Evidence match</th><th>Production API delivery</th><th>Backend delivery depth</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
    )


def answers(job, assessment):
    by_id = {m.requirement_id: m for m in assessment.matches}
    for requirement in job.requirements:
        answer = by_id[requirement.id]
        st.html(
            '<div class="answer-row"><span>'
            + html.escape(requirement.text)
            + "</span>"
            + badge(STATUS_LABELS[answer.status.value], answer.status.value)
            + "</div>"
        )


def analysis_details(run, selected):
    result = next(r for r in run.results if r.resume_id == selected.id)
    summary = run.summary
    with st.expander("Analysis details"):
        if result.assessment:
            st.markdown("#### Supporting evidence")
            for requirement in run.job.requirements:
                answer = next(
                    m for m in result.assessment.matches if m.requirement_id == requirement.id
                )
                st.markdown(f"**{requirement.text}**")
                if answer.evidence_line_ids:
                    for line in answer.evidence_line_ids:
                        st.html(
                            f'<div class="source-line"><span>{line}</span>{html.escape(selected.lines[line])}</div>'
                        )
                else:
                    st.caption("No supporting evidence is stated in this resume.")
            st.caption(
                f"Backend delivery depth {result.assessment.backend_depth.level}: {DEPTH_LEVELS[result.assessment.backend_depth.level]}"
            )
            extra_sources = list(
                dict.fromkeys(
                    result.assessment.production_api.evidence_line_ids
                    + result.assessment.backend_depth.evidence_line_ids
                )
            )
            for line in extra_sources:
                st.html(
                    f'<div class="source-line"><span>{line}</span>{html.escape(selected.lines[line])}</div>'
                )
        st.markdown("#### Cost and speed")
        cols = st.columns(4)
        cols[0].metric("Total API cost", money(summary["total_cost_usd"]))
        cols[1].metric("Total time", f"{summary['wall_seconds']:.2f}s")
        cols[2].metric(
            "Input tokens",
            f"{summary['input_tokens']:,}"
            if summary["input_tokens"] is not None
            else "Unavailable",
        )
        cols[3].metric(
            "Output tokens",
            f"{summary['output_tokens']:,}"
            if summary["output_tokens"] is not None
            else "Unavailable",
        )
        st.caption(
            f"{summary['api_calls']} requests · {summary['failed']} failed · Median request {summary['median_call_seconds']:.2f}s · Cost basis: {summary['cost_basis']}"
        )
        if summary["cost_basis"] == "estimated":
            st.caption(
                "Cost uses returned token counts and a saved price snapshot. It is an estimate."
            )
        elif summary["total_cost_usd"] is None:
            st.caption(
                "Complete billing data was unavailable. Missing costs are not counted as zero."
            )
        st.markdown("#### Matching engine")
        st.write(
            f"LLM with structured outputs · {result.receipt.provider} · {result.receipt.actual_model or result.receipt.requested_model}"
        )
        st.caption(f"Run {run.id} · Input snapshot {run.input_hash[:12]} · {run.prompt_version}")
        reference = application_reference(run.job, run.resumes)
        if reference:
            quality = evaluate(run, *reference)
            extra = quality["additional_checks"]
            st.write(
                f"Reference agreement: {quality['correct']}/{quality['total']} requirement labels · {extra['correct']}/{extra['total']} additional checks"
            )
            st.caption(
                "Reference labels apply only to the unchanged fictional applications. This small set is not a production accuracy estimate."
            )
            disagreements = quality["disagreements"] + extra["disagreements"]
            if disagreements:
                st.json(disagreements)
        a, b = st.columns(2)
        a.download_button(
            "Export results",
            results_csv(run),
            "applicant-evidence.csv",
            "text/csv",
            use_container_width=True,
        )
        b.download_button(
            "Export analysis",
            run.model_dump_json(indent=2),
            f"analysis-{run.id}.json",
            "application/json",
            use_container_width=True,
        )
        with st.expander("Request receipts"):
            st.json([r.receipt.model_dump(mode="json") for r in run.results])


styles()
st.html(
    '<header class="app-header"><div class="brand"><span class="brand-icon">▦</span>RoleMatch</div><span class="workspace-name">Applications</span></header>'
)
st.title("Review applications")
st.write("Match applicant experience to the requirements of an open role.")

try:
    settings = LLMSettings.from_env()
except (ValueError, ValidationError):
    st.error("The matching service configuration is invalid. Check the local .env settings.")
    st.stop()

openings = load_openings()
opening_by_id = {o.id: o for o in openings}
left, right = st.columns([1, 1], gap="large")
with left:
    st.markdown("### Job description")
    opening_id = st.selectbox(
        "Job opening",
        options=list(opening_by_id),
        format_func=lambda oid: opening_by_id[oid].job.title,
    )
    opening = opening_by_id[opening_id]
    st.caption(f"{opening.department} · {opening.location} · {opening.employment_type}")
    description = st.text_area(
        "Job description",
        value=opening.job.description,
        height=375,
        key=f"description_{opening_id}",
        label_visibility="collapsed",
    )
    with st.expander("Matching criteria"):
        st.caption(
            "Evidence match uses these criteria. Update them when you change the job requirements."
        )
        title = st.text_input("Job title", value=opening.job.title, key=f"title_{opening_id}")
        requirement_text = st.text_area(
            "Criteria, one per line",
            value="\n".join(r.text for r in opening.job.requirements),
            height=145,
            key=f"criteria_{opening_id}",
        )
with right:
    st.markdown("### Applicants")
    st.write("Upload resumes to review for this role.")
    uploads = st.file_uploader(
        "Upload resumes",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="Up to 10 PDF or text files. Maximum 2 MB and 12 pages per file.",
    )
    resumes = []
    upload_errors = []
    if len(uploads) > 10:
        upload_errors.append("Upload at most 10 resumes at a time.")
    else:
        for i, upload in enumerate(uploads, 1):
            try:
                resumes.append(read_resume(upload.name, upload.getvalue(), i))
            except (ValueError, ValidationError) as exc:
                upload_errors.append(f"{upload.name}: {exc}")
    for error in upload_errors:
        st.error(error)
    if resumes:
        st.caption(
            f"{len(resumes)} application{'s' if len(resumes) != 1 else ''} ready for analysis."
        )
    else:
        st.html(
            '<div class="upload-note"><strong>PDF or text resumes</strong><p>Add up to 10 applications. Each file can be up to 2 MB.</p></div>'
        )
    st.caption("Resume text is sent to the configured AI provider when you analyze applications.")

try:
    job = make_job(title, description, requirement_text)
except (ValidationError, ValueError):
    st.error("Enter a job title, a complete description, and 1 to 8 matching criteria.")
    job = None

if not settings.api_key:
    st.warning("The matching service needs an API key. Add it to the local .env file.")

if st.button(
    "Analyze applications",
    type="primary",
    disabled=not (settings.api_key and job and resumes and not upload_errors),
    use_container_width=False,
):
    matcher = LLMMatcher(settings)
    progress = st.progress(0, text="Reading applications...")
    try:
        run = run_matching(
            job,
            resumes,
            matcher,
            progress=lambda done, total, name: progress.progress(
                done / total, text=f"Analyzing application {done} of {total}"
            ),
        )
    finally:
        matcher.close()
        progress.empty()
    st.session_state.setdefault("application_runs", []).append(run)

st.divider()
st.markdown("### Results")
all_runs = st.session_state.get("application_runs", [])
active_hash = fingerprint(job, resumes) if job else None
matching_runs = [run for run in all_runs if run.input_hash == active_hash]
if not matching_runs:
    if all_runs and resumes:
        st.info("The job or applications changed. Analyze again to refresh the results.")
    else:
        st.html(
            '<div class="empty-results"><strong>Your applicant review will appear here.</strong><p>Select a role, upload resumes, then analyze the applications.</p></div>'
        )
else:
    by_run = {run.id: run for run in reversed(matching_runs)}

    def run_name(rid):
        item = by_run[rid]
        time = datetime.fromisoformat(item.started_at).strftime("%H:%M:%S UTC")
        return f"LLM structured output · {len(item.resumes)} applicants · {time}"

    run_id = st.selectbox(
        "Analysis run", list(by_run), format_func=run_name, key=f"run_{active_hash}"
    )
    active_run = by_run[run_id]
    summary = active_run.summary
    cost_kind = {
        "reported": "Reported API cost",
        "estimated": "Estimated API cost",
        "unavailable": "API cost",
    }[summary["cost_basis"]]
    st.html(
        '<div class="result-summary"><span><strong>'
        + str(summary["succeeded"])
        + "</strong> applications analyzed</span><span>"
        + f"{summary['wall_seconds']:.2f}s total"
        + "</span><span>"
        + html.escape(cost_kind + ": " + money(summary["total_cost_usd"]))
        + "</span></div>"
    )
    candidate_table(active_run)
    st.caption(
        "Evidence match counts criteria with direct supporting evidence. It is not a hiring recommendation."
    )
    for result in active_run.results:
        if result.error:
            resume = next(r for r in active_run.resumes if r.id == result.resume_id)
            st.error(f"{applicant_name(resume)}: {result.error}")
    completed = [r for r in active_run.results if r.assessment]
    if completed:
        st.markdown("### Applicant details")
        by_id = {r.id: r for r in active_run.resumes}
        selected_id = st.selectbox(
            "Applicant",
            [r.resume_id for r in completed],
            format_func=lambda rid: applicant_name(by_id[rid]),
            key=f"applicant_{active_run.id}",
        )
        selected = by_id[selected_id]
        assessment = next(r.assessment for r in completed if r.resume_id == selected_id)
        answers(active_run.job, assessment)
        analysis_details(active_run, selected)
    else:
        analysis_details(active_run, active_run.resumes[0])

st.html(
    '<footer class="app-footer">Review the source evidence before making a hiring decision.</footer>'
)
