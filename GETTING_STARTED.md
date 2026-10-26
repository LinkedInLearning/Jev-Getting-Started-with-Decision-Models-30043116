# RoleMatch: the LLM starter

Branch: `02_01b`.

A local resume-to-job evidence matching app for Video 4.

The app uses an LLM through OpenRouter or OpenAI. This branch has no Jev implementation or TypeSafe SDK dependency.

## Run it

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

Then start the app:

```bash
uv sync --locked
uv run streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

For OpenAI directly, use `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4.1-mini`, and `OPENAI_API_KEY` instead.

The default model is a compact general LLM with strict JSON output. Choose any supported structured-output model in the sidebar. Changing models does not change the rubric.

## What to try

1. Review the role and its four explicit technical requirements.
2. Run the three synthetic resumes with **Run LLM match**.
3. Open one resume to compare each label with the exact source lines.
4. Check the request time, tokens, cost, and sample label agreement.
5. Download the evidence CSV or complete run JSON.

The initial sample preview is hand-authored interface data. It makes no model calls and has no API measurements. It is clearly labeled and never saved as a benchmark run.

You can also upload UTF-8 text or text-based PDF resumes. Up to ten files are accepted, at most 2 MB and 12 PDF pages per file. Scanned PDFs need OCR outside this starter.

The model evaluates documented technical evidence. Results support recruiter review. A missing statement is not evidence that a person lacks a skill. Personal attributes are excluded from the task and output.

## The matching task

Each resume is one request. That request asks for all judgments together:

| Judgment | Defined output |
| --- | --- |
| Each job requirement | `direct`, `related`, `not_stated`, or `unclear`, with resume line IDs |
| Production API delivery described | `yes`, `not_stated`, or `unclear`, with line IDs |
| Backend service delivery depth | Level 0, 1, or 2 on the documented rubric |

The app displays original source lines. It does not ask the model to invent explanations or quotations.

Strict JSON parsing checks the result. Local validation requires every requirement exactly once and rejects unknown evidence IDs. These checks establish the response structure and source references; a reviewer still checks whether the labels match the evidence.

## Where to add the decision model during recording

| File | Responsibility |
| --- | --- |
| `ats_match/llm.py` | Current LLM request, response parsing, usage, and price handling |
| `ats_match/domain.py` | Shared job, resume, assessment, and receipt contract |
| `ats_match/prompts.py` | Current LLM instructions, questions, and strict JSON schema |
| `ats_match/workflow.py` | Model-independent matching loop, coverage counts, evaluation, and exports |
| `app.py` | Input and results interface |
| `data/sample_workspace.json` | Synthetic inputs and hand-labeled reference answers |

The `Matcher` protocol exposes `assess(job, resume) -> CandidateResult`.

Add a new implementation later while keeping the same job criteria, inputs, and application behavior. The baseline does not manufacture LLM probabilities or treat a model's self-reported certainty as calibrated confidence.

## Record the baseline

```bash
uv run python -m ats_match.benchmark --out runs/llm-baseline.json --repeats 3
```

This sends nine requests: three resumes for each of three repeats.

The run file contains the frozen inputs, SHA-256 input hash, prompt version, requested and returned models, every result or error, elapsed times, usage, pricing provenance, and reference-label disagreements.

`runs/`, `.env`, and exports are ignored by Git. UI history lasts for the current Streamlit session. Download a run to retain it.

### Cost accounting

- Prefer OpenRouter's returned `usage.cost`, labeled **Reported API cost**.
- Otherwise estimate from returned input/output tokens and a saved model-price snapshot.
- Account for cached input only when its price is available.
- If price or usage is missing, show **Unavailable**, never a fabricated zero.
- Preserve generation cost even when the output fails validation.
- A failed or interrupted request can have unreported billing. Its unknown cost makes the total unavailable.
- The default does not retry silently or switch to a different LLM.

OpenRouter pricing comes from its public models API when a live run starts. Direct OpenAI calls need optional dated rates configured in `.env` to estimate cost. Receipts retain the source and timestamp. Billing-reported costs take precedence.

### A fair later comparison

Use the same frozen resumes, job requirements, evidence rules, reference labels, and request scheduling for both engines.

Compare median request time, complete-run time, total cost with its basis, failures, and reference-label agreement. Report the costs of all inference calls that the new implementation needs. Do not compare an LLM generating long narratives with a decision model performing a smaller task.

The evaluator reports twelve requirement labels and six additional evidence checks separately. The additional checks cover production API delivery and backend delivery depth.

These synthetic examples are a tiny teaching set, not a production hiring validation dataset. Agreement is hidden for edited or uploaded inputs without reference labels. Failures count as disagreements in both groups.

There are no projected Jev savings in this starter. Measure the second implementation during the next stage.

### Live verification

The OpenRouter integration and browser flow were checked on 26 October 2026. The first three-resume run cost $0.0016804, as reported by the provider, with a 3.00-second median request time.

Requirement-label agreement was 12 of 12. Additional evidence-check agreement was 5 of 6. Read the [saved baseline notes](lessons/04-working-application/llm-baseline.md) for the observed disagreement and measurement limits.

## Checks

```bash
uv run ruff check .
uv run pytest -q
```

Tests cover malformed responses, missing requirements, invented evidence references, failed requests, cached-token estimates, unknown costs, partial-batch quality, upload boundaries, and the Streamlit flow. They make no paid API calls.

## References

- [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
- [OpenRouter models and pricing API](https://openrouter.ai/api/v1/models)
- [TypeSafe's Jack & Jill hiring case study](https://typesafe.ai/blog/jack-jill-jev-case-study), context for the future integration, not a performance claim for this app.
