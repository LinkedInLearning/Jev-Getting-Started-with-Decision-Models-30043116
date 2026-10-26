# RoleMatch

Branch: `02_01b`.

A local applicant-review application for Video 4. It uses an LLM with structured outputs through OpenRouter or OpenAI. Jev is added during the recording.

For a short setup checklist, use [README_APP.md](README_APP.md). The [video guide](lessons/04-working-application/script.html) and [Codex prompt](prompts/video-04-codex-prompt.md) describe the lesson.

**No OpenAI or OpenRouter key?** Choose the [Jev-only prompt](prompts/video-04-jev-only-prompt.md). It asks Codex to replace the LLM integration, remove its key requirement, and use only `TYPESAFE_API_KEY`. Skip the LLM configuration and baseline steps below. The starter interface opens without an LLM key; Jev analysis becomes available after that integration is implemented.

## Start the application

Use Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone --branch 02_01b https://github.com/LinkedInLearning/Jev-Getting-Started-with-Decision-Models-30043116.git
cd Jev-Getting-Started-with-Decision-Models-30043116
cp .env.example .env
```

Add your OpenRouter key to `.env`:

```dotenv
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4.1-mini
OPENROUTER_API_KEY=your-own-key
```

Start the application:

```bash
uv sync --locked
uv run streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

For OpenAI directly, set `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4.1-mini`, and `OPENAI_API_KEY`.

Keys and model configuration stay in the local environment file. They do not appear in the main application interface.

## The recording workflow

1. Select **Python Backend Engineer** from the job dropdown.
2. Read or edit the job description on the left.
3. Upload the five PDFs from `output/pdf/resumes/` on the right.
4. Select **Analyze applications**.
5. Review evidence scores, then select an applicant to read the answers.
6. Expand **Analysis details** for source text, cost, speed, reference checks, and exports.

The other built-in roles are Backend Platform Engineer and API Integration Engineer. Each has a complete description and its own four matching criteria.

The job description is editable. **Matching criteria** contains the explicit questions used for evidence coverage. Update these when you change the requirements. Editing a description does not silently generate a different set of questions.

Only live results appear in the interface. There are no prefilled scores or simulated API measurements.

## Prepared applications

[Download all five resumes](output/pdf/applicant-resumes.zip), or use the individual PDFs in [output/pdf/resumes](output/pdf/resumes/).

| Applicant | Evidence to explore |
| --- | --- |
| Asha Mehta | Python APIs, production delivery, PostgreSQL, and pytest |
| Daniel Brooks | Python backend delivery with a different testing framework |
| Elena Torres | Adjacent data engineering experience |
| Marcus Reed | Unclear deployment claims and a skills-list mention of pytest |
| Sofia Khan | Production backend experience using TypeScript instead of Python |

Every person and application is fictional. Each PDF has a small training-material footer. Names and contact details are excluded from the model's assessment criteria.

The PDFs are ordinary, selectable-text documents. The app also accepts UTF-8 text, up to 10 files per run, 2 MB and 12 PDF pages per file. Scanned PDFs need OCR outside this application.

To rebuild the supplied PDFs:

```bash
uv run --with reportlab python scripts/build_application_pdfs.py
```

## Understanding results

**Evidence match** is the percentage of explicit criteria with direct project or work evidence. It is a coverage count, not a probability or hiring recommendation. Adjacent experience does not receive partial credit in this count.

For each criterion, the model returns `direct`, `related`, `not_stated`, or `unclear`, with original resume line IDs. A missing statement does not prove a lack of skill.

The app also asks whether production API delivery is documented and scores backend service delivery depth from 0 to 2 on a defined rubric. The rubric and supporting lines are inside **Analysis details**.

The **Analysis run** dropdown switches between saved runs for the same current job and applications. Selecting another applicant or opening analysis details does not make a new model request. Changing the job, criteria, or files requires a fresh analysis.

Run history lasts for the current browser session. Export an analysis to keep its frozen inputs, results, and request receipts.

## Measurement and evaluation

Each resume is one schema-constrained LLM request. All judgments are requested together. There are no hidden retries, narrative-generation calls, or alternate-model fallbacks.

- Use the provider's reported `usage.cost` when available.
- Otherwise estimate from returned tokens and a saved, matching price snapshot.
- Account for cached tokens only when a cache price is available.
- Keep generation cost when a response fails validation.
- Unknown cost remains unavailable. It is never treated as zero.

OpenRouter prices come from its public models API. Direct OpenAI estimates use optional dated rates from `.env`. Receipts retain actual model IDs, generation IDs, usage, latency, and price provenance.

Reference evaluation is available only for unchanged bundled PDFs against the original Python role. It reports 20 requirement labels and 10 additional checks separately. Edited roles and other uploads have no supplied reference labels.

A live five-PDF browser run on 26 October 2026 completed in 13.48 seconds and reported $0.0040656 in API cost. Requirement-label agreement was 18/20. Additional-check agreement was 8/10. The disagreements are preserved in the [baseline notes](lessons/04-working-application/llm-baseline.md).

These examples establish functional behavior. They do not establish production hiring accuracy or comparative Jev savings.

### Repeat the baseline

```bash
uv run python -m ats_match.benchmark --dataset applications --out runs/ats-applications-baseline.json --repeats 3
```

This sends 15 requests: five resumes for each of three repeats. `--dataset small` uses the earlier three short text examples.

The run file preserves frozen inputs, input hashes, prompt version, every answer or error, timing, usage, cost basis, and reference-label disagreements. `runs/`, `.env`, and local exports are ignored by Git.

## Add Jev during recording

Choose the [comparison prompt](prompts/video-04-codex-prompt.md) for side-by-side results, or the [Jev-only prompt](prompts/video-04-jev-only-prompt.md) to remove the LLM. The Jev-only path reports absolute Jev cost, time, and reference-label agreement without claiming comparative savings.

The `Matcher` protocol exposes `assess(job, resume) -> CandidateResult`.

| File | Responsibility |
| --- | --- |
| `ats_match/llm.py` | Current inference request, parsing, usage, and pricing |
| `ats_match/domain.py` | Shared job, resume, assessment, and receipt contract |
| `ats_match/prompts.py` | Instructions, questions, and strict response schema |
| `ats_match/workflow.py` | Matching loop, evaluation, and exports |
| `ats_match/data.py` | Job catalog, PDF extraction, and reference lookup |
| `app.py` | Job selection, uploads, answers, and collapsible analysis |

Add a second implementation at this boundary. During recording, use the [integration prompt](prompts/video-04-codex-prompt.md) to add **LLM structured output**, **Jev**, and **Compare both**. Keep both engines available, with the same job, files, questions, answer meanings, and scheduling.

Compare both should show paired answers for the same applicant, with a side-by-side measurement summary inside Analysis details. The [implementation brief](prompts/add-jev.md) specifies source selection, output compatibility, and complete cost accounting.

Measure all calls needed to produce the same answers and evidence. Include any extra extraction or fallback calls. Compare full-run time, median request time, complete cost, failures, and both reference-label groups.

## Checks

```bash
uv run ruff check .
uv run pytest -q
```

Tests cover job switching, real PDF extraction, upload errors, stale results, result history without extra model calls, evidence validation, failed requests, billing provenance, and reference evaluation. Automated tests make no paid API calls.

## References

- [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
- [OpenRouter models and pricing API](https://openrouter.ai/api/v1/models)
- [TypeSafe's Jack & Jill hiring case study](https://typesafe.ai/blog/jack-jill-jev-case-study), context for the future integration, not a performance claim for this application.
