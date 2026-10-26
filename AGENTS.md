# Jev course project

## Context

- This is the LinkedIn Learning course repository for Jev: Getting Started with Decision Models, course ID 30043116.
- Read PROJECT.md and planning/course-plan.html for the current scope.
- Follow the six-video outline supplied on 23 October 2026. Keep each recording under five minutes.
- Video one uses at most eight Google Slides. Videos two through six are hands-on.
- Video two covers the official playground and one Choice question only.
- Keep planning HTML in one continuous column, with short bullets and no decorative labels.
- Videos two and three introduce primitives with small examples. The user selected ATS matching for videos four through six on 26 October 2026.
- The ATS starter is on branch `02_01b`. It uses an LLM only. Add Jev during the recording, not in this starter.
- Learners choose the comparison prompt or the optional Jev-only prompt. The Jev-only implementation removes LLM runtime and key requirements. It needs only a TypeSafe key and does not show comparative savings.
- The official repository title supersedes the earlier working title in the research document.

## Teaching and writing

- Never use em dashes.
- Never add eyebrow text or decorative kicker labels above headings.
- Write scripts in short, speakable sentences, with one idea per line and visible spacing.
- Use plain English and a conversational teaching tone.
- Prefer compact HTML for reviews, plans, and complete scripts. Markdown is suitable for repository documentation.
- Use concrete examples and honest claims. Do not promise perfect accuracy, universal cost savings, or that Jev replaces reasoning models.
- Distinguish model judgments from application actions and explain uncertainty in context.

## Implementation

- Read live TypeSafe documentation before writing SDK integrations. Start at https://docs.typesafe.ai/llms.txt.
- Keep secrets out of source control and browser code.
- Use synthetic resumes and job descriptions for course demonstrations.
- Maintain the publisher's license, notice, contribution policy, and exercise branch convention.
- The teaching app is RoleMatch, a Python/Streamlit resume evidence workbench. Read GETTING_STARTED.md for actual setup and run commands.
- Keep its main screen minimal: editable job on the left, multi-file uploads on the right, answers below, and detailed analysis collapsed. Do not put course notes or model configuration in the main workflow.
- Use the five fictional PDFs in output/pdf/resumes/ for recording. The built-in job catalog is in data/job_openings.json. No prefilled result scores appear in the interface.
- Keep the job, resume text, requirement definitions, reference labels, and scheduling fixed when comparing inference engines.
- Record actual usage, cost provenance, latency, failures, and reference-label agreement. Missing usage or prices are unavailable, not zero.
- Keep inference inside the `Matcher.assess(job, resume)` boundary. Application counts and exports stay in ordinary code.
- Matching results support recruiter review. Do not infer missing skills from absent resume statements or use personal attributes for assessment.
- Codex writes the application; the application calls Jev. Preserve that distinction in the teaching.
- Keep uncertainty and workflow testing as separate lessons.
- Verify actual exercise behavior once implementation exists. Documentation-only setup does not require application tests.

## Research provenance

- Existing video research is based on titles, descriptions, and available chapters.
- Full transcripts were not available. Preserve that limitation in derived research claims.
