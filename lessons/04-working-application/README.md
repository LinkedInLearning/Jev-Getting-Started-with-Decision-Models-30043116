# Connect Jev to a Working Application

Target duration: 4:50.

Status: the LLM starter is implemented on branch `02_01b`. The Jev integration is reserved for recording.

## Learning objective

Replace a working LLM matching step while preserving the application behavior and evaluation inputs.

## Demonstration

Use RoleMatch, a Python/Streamlit resume-to-job evidence workbench.

The starter evaluates every job requirement, checks documented production API delivery, and assesses backend delivery depth with one LLM request per resume.

During recording, add a new inference implementation at `Matcher.assess(job, resume)`. Keep the job, resumes, criteria, and application code fixed.

Read [GETTING_STARTED.md](../../GETTING_STARTED.md). Start with `uv run streamlit run app.py`.

Capture the LLM baseline with `uv run python -m ats_match.benchmark --out runs/llm-baseline.json --repeats 3`.

Compare actual latency, cost with its source, failed requests, and requirement-label agreement. No comparative savings are assumed.

## Learner checkpoint

Inspect a requirement label beside its original resume evidence. Distinguish not stated from unclear.

## Recording plan

Show the finished app, inspect the LLM call, add the new engine with Codex, and rerun the same examples. Prepare both implementations before recording.

Add the complete teaching script as `script.html` in this directory.
