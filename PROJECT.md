# Jev: Getting Started with Decision Models

LinkedIn Learning course project, course ID `30043116`.

Repository: https://github.com/LinkedInLearning/Jev-Getting-Started-with-Decision-Models-30043116

## Start here

- [Current six-video course plan](planning/course-plan.html)
- [Earlier five-video draft](planning/jev-course-outline-2026-10-20.html)
- [Title research and source references](planning/jev-title-recommendation-2026-10-20.html)
- [Lesson scripts](lessons/README.md)
- [Exercise files](exercise-files/README.md)
- [Visual assets](assets/README.md)

## Course format

Six videos, each under five minutes, following the outline supplied on 23 October 2026.

Planned running time: 27 minutes 20 seconds.

Video one uses at most eight Google Slides. The remaining five videos are hands-on.

Videos four through six use ATS matching, selected on 26 October 2026.

Learners start with an LLM-powered resume evidence workbench, then add Jev during recording and compare the same task.

| Video | Title | Target duration | Script location |
| --- | --- | --- | --- |
| 1 | What Is Jev? An introduction to decision models | 4:30 | `lessons/01-what-jev-does/` |
| 2 | Ask Jev your first questions | 4:30 | `lessons/02-first-question/` |
| 3 | Choose the Right Question Type | 4:30 | `lessons/03-question-types/` |
| 4 | Connect Jev to a working application | 4:50 | `lessons/04-working-application/` |
| 5 | Handle uncertainty in your decisions | 4:30 | `lessons/05-uncertainty/` |
| 6 | Test your Jev decision workflow | 4:30 | `lessons/06-testing/` |

## Current status

RoleMatch is the LLM-only starter on branch `02_01b`. Its main screen has an editable job description on the left and resume uploads on the right. Results appear below, with supporting evidence and measurements in a collapsed analysis panel.

It compares resumes against explicit job requirements, displays original source lines, and records model usage, cost provenance, latency, failures, and sample-label agreement.

Run `uv sync --locked`, configure the local `.env`, and use `uv run streamlit run app.py`.

Read [GETTING_STARTED.md](GETTING_STARTED.md) for setup, the inference boundary, and the baseline benchmark command.

The learner quickstart is [README_APP.md](README_APP.md). Video 4 has a [timed recording guide](lessons/04-working-application/script.html), a [short Codex prompt](prompts/video-04-codex-prompt.md), and a [Jev implementation brief](prompts/add-jev.md) for paired outputs and measurements.

Three built-in job openings and five fictional one-page PDF resumes are ready for recording. The PDFs are in `output/pdf/resumes/`, with a ZIP bundle in `output/pdf/applicant-resumes.zip`. The interface has no prefilled or simulated results.

Live OpenRouter and browser checks passed on 26 October 2026. The five-PDF run cost $0.0040656, with 13.48 seconds total time and a 2.63-second median request. Requirement-label agreement was 18 of 20. Additional evidence-check agreement was 8 of 10. See the [baseline notes](lessons/04-working-application/llm-baseline.md) for preserved disagreements and the earlier short-text check.

This branch contains no Jev implementation. Comparative savings remain to be measured after the decision-model integration is added.

The [eight-slide introduction](https://docs.google.com/presentation/d/1pnz2Du74DxdTHrVW-zysbOstVhugFgjZTW6EZ6uoOa4/edit) includes the official white TypeSafe mark, original editable diagrams, and a comparison table.

It follows the supplied blue LinkedIn Learning template. The two launch slides follow the cover. Sources and teaching context are in the speaker notes.

## Repository conventions

Keep the publisher's README, license, notice, and contribution files intact during initial setup.

The upstream README describes `CHAPTER#_MOVIE#` exercise branches, with optional `b` and `e` suffixes.

Planned application snapshots are `02_01b` and `02_01e`.

Planned uncertainty snapshots are `02_02b` and `02_02e`.

Planned evaluation snapshots are `02_03b` and `02_03e`.

`02_01b` contains the LLM starter. Create the ending and later exercise snapshots after those implementations are checked.

Only `main` existed on the remote when this project was cloned on 23 October 2026.

The planning work began on `codex/course-setup`. The current app branch is `02_01b`.

## Research scope

The YouTube research covers five video pages, their descriptions, and available chapter outlines.

Full transcripts were unavailable. Do not describe those videos as fully watched or transcribed.

The updated plan also uses the existing Jev Field Lab, its Streamlit presets, and the public launch research from `/Users/harshit/playground/jev_test`.

Social and blog screenshots were removed from the deck and course asset folders following review on 24 October 2026. Reference captures are retained in the private, ignored `.tmp/` directory.

Check current TypeSafe documentation before implementing SDK calls or recording API examples.

Start with https://docs.typesafe.ai/llms.txt.
