# Application details

For installation and startup, see [README.md](README.md).

## Jobs and applications

RoleMatch includes Python Backend Engineer, Backend Platform Engineer, and API Integration Engineer roles.
Each has an editable description and four explicit matching criteria.

Update **Matching criteria** when you change the job requirements.
Editing the description does not automatically change the questions.

Upload up to 10 PDF or UTF-8 text files per run.
Each file can be up to 2 MB and 12 PDF pages.
Scanned PDFs require OCR before upload.

The [five sample PDFs](output/pdf/resumes/) are fictional applications for the Python role.
They include direct evidence, adjacent experience, missing statements, and unclear claims.
Names and contact details are excluded from the assessment criteria.

To rebuild the PDFs and download bundle:

```bash
uv run --with reportlab python scripts/build_application_pdfs.py
```

## Answers and evidence

Each requirement receives one label:

| Label | Meaning |
| --- | --- |
| Direct | Project or work evidence supports the requirement. |
| Related | Evidence is relevant but does not directly meet the requirement. |
| Not stated | The resume does not state supporting evidence. |
| Unclear | The available evidence is ambiguous or conflicting. |

Answers reference original resume line IDs.
A missing statement does not prove a lack of skill.

**Evidence match** is the percentage of criteria with direct evidence.
Related evidence does not receive partial credit in this count.
The percentage is not a probability or hiring recommendation.

The app also checks production API delivery and scores backend service delivery depth from 0 to 2.
The scoring rubric and source lines appear inside **Analysis details**.

## Saved results

The **Analysis run** menu switches between completed runs for the current inputs.
Selecting an applicant or opening analysis details does not make another model request.
Changing the job, criteria, or files requires a new analysis.

Run history lasts for the current browser session.
Use **Export analysis** to retain the inputs, answers, and request receipts.
Only live analysis results appear in the interface.

## Cost and timing

Each resume uses one schema-constrained LLM request.
All judgments are requested together.
There are no automatic retries or alternate-model fallbacks.

The app uses provider-reported cost when available.
Otherwise, it estimates cost from returned tokens and a matching saved price.
Unknown cost remains unavailable.
Failed validation retains any known generation cost.

OpenRouter pricing comes from its public models API.
Direct OpenAI estimates require optional dated rates in `.env`.
Receipts retain model IDs, generation IDs, usage, latency, and price provenance.

Reference checks are available for unchanged sample PDFs against the original Python role.
They report agreement on 20 requirement labels and 10 additional checks separately.
Other uploads and edited jobs have no supplied reference labels.

## Benchmark

```bash
uv run python -m ats_match.benchmark --dataset applications --out runs/ats-applications.json --repeats 3
```

This makes 15 requests: five resumes for each of three repeats.
Use `--dataset small` for the three smaller text fixtures.

The JSON output retains inputs, hashes, answers, errors, usage, timing, and reference disagreements.
The `runs/` directory, `.env`, and local exports are ignored by Git.

## Engine integration

Use the [Jev-only prompt](prompts/jev-only.md) to replace the LLM.
Use the [comparison prompt](prompts/compare-engines.md) to retain both engines.

The `Matcher` protocol exposes `assess(job, resume) -> CandidateResult`.
Both integrations preserve the existing questions, source evidence, and scoring meanings.

| File | Responsibility |
| --- | --- |
| `ats_match/llm.py` | Inference requests, parsing, usage, and pricing |
| `ats_match/domain.py` | Shared job, resume, assessment, and receipt types |
| `ats_match/prompts.py` | Instructions, questions, and response schema |
| `ats_match/workflow.py` | Matching, evaluation, and exports |
| `ats_match/data.py` | Job catalog, PDF extraction, and reference lookup |
| `app.py` | Job selection, uploads, answers, and analysis |

## Checks

```bash
uv run ruff check .
uv run pytest -q
```

Tests cover uploads, PDF extraction, job switching, result history, evidence validation, billing, and reference checks.
Automated tests make no paid API calls.
