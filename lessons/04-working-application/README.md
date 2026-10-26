# Connect Jev to a Working Application

Target duration: 4:50.

Status: the LLM starter is implemented on branch `02_01b`. The Jev integration is reserved for recording.

## Learning objective

Replace a working LLM matching step while preserving the application behavior and evaluation inputs.

## Demonstration

Use RoleMatch, a Python/Streamlit applicant-review application.

Select the Python Backend Engineer opening. Show the editable job description on the left. Upload the five PDFs from `output/pdf/resumes/` on the right.

Read the evidence scores and an applicant's answers. Expand Analysis details for source lines, cost, speed, and exports.

The starter evaluates every job requirement, checks documented production API delivery, and assesses backend delivery depth with one LLM request per resume.

During recording, add a new inference implementation at `Matcher.assess(job, resume)`. Keep the job, resumes, criteria, and application code fixed.

Read [GETTING_STARTED.md](../../GETTING_STARTED.md). Start with `uv run streamlit run app.py`.

Learners can follow [README_APP.md](../../README_APP.md) for the clone, branch, setup, and run commands.

Capture the LLM baseline with `uv run python -m ats_match.benchmark --dataset applications --out runs/ats-applications-baseline.json --repeats 3`.

During recording, add the LLM/Jev selector alongside the second engine. Compare actual latency, cost with its source, failed requests, requirement-label agreement, and additional evidence-check agreement. No comparative savings are assumed.

## Learner checkpoint

Inspect a requirement label beside its original resume evidence. Distinguish not stated from unclear.

## Recording plan

Show the finished app, inspect the LLM call, add the new engine with Codex, and rerun the same examples. Prepare both implementations before recording.

The [recording guide](script.html) contains the timed flow, short spoken pointers, and learner check.

Paste the [short Codex prompt](../../prompts/video-04-codex-prompt.md) during recording. It points to the official documentation and the [detailed integration brief](../../prompts/add-jev.md).

The requested ending state adds LLM structured output, Jev, and Compare both. The same applicant's answers appear side by side, with measured costs and timing in the collapsed analysis.

## Optional path without an LLM key

Learners with only a TypeSafe key can choose the [Jev-only prompt](../../prompts/video-04-jev-only-prompt.md).

It replaces the LLM integration, removes its runtime and key requirements, and uses Jev as the only matching engine. These learners skip the LLM baseline and comparison steps. They still inspect real answers, source evidence, Jev cost, and timing.

The starter interface can be opened without either LLM key. Jev analysis needs the optional integration to be implemented first.
