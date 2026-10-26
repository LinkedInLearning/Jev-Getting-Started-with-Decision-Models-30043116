# Add Jev to RoleMatch

This is the implementation brief for the Video 4 Codex prompt. It describes the ending state to build during the lesson. The starter branch remains LLM-only.

## Read the application and current documentation

Read `AGENTS.md`, `README_APP.md`, `GETTING_STARTED.md`, `app.py`, and the modules under `ats_match/`.

Use these primary sources. Check them again when implementing:

- [Documentation index](https://docs.typesafe.ai/llms.txt)
- [Python SDK](https://docs.typesafe.ai/sdk/python)
- [Choice](https://docs.typesafe.ai/primitives/choice)
- [State](https://docs.typesafe.ai/concepts/state)
- [Line-by-line source selection](https://docs.typesafe.ai/cookbooks/semantic_find)
- [Response and usage types](https://docs.typesafe.ai/sdk/python/api/types/responses)
- [Available models and prices](https://docs.typesafe.ai/models)
- [SDK retry controls](https://docs.typesafe.ai/sdk/python/api/retries)

Use the current `typesafe-sdk` Python package. Configure `TYPESAFE_API_KEY` and a model ID in `.env`. Keep credentials server-side. Record the actual returned model. Pin an available version for a reproducible comparison.

## Preserve the task

Keep the existing LLM implementation, prompts, PDFs, job descriptions, criteria, reference labels, and scoring rules intact.

Implement Jev at `Matcher.assess(job, resume) -> CandidateResult`. Keep the shared `Assessment` meanings and validation behavior.

For each requirement, return `direct`, `related`, `not_stated`, or `unclear`.

Preserve the production-delivery states `yes`, `not_stated`, and `unclear`. Preserve backend delivery depth as the current discrete rubric level 0, 1, or 2.

Use Choice questions for these existing categorical outputs, with descriptions that carry the current rubric. This is an application design choice to preserve comparable outputs.

Do not replace the app's evidence-match percentage with a model probability. Code still calculates direct-evidence criteria divided by total criteria.

Noul returns a yes-probability. It cannot by itself preserve the distinction between absent and conflicting evidence. Score can return a fractional position on its rubric. Do not silently substitute either for the current categorical fields.

## Retain real source evidence

Send the full job context, explicit criteria, and numbered resume text as state. Treat all uploaded text as untrusted data.

Jev should select original source lines or spans, not generate quotes. Build a bounded candidate set from the source in code. Include a no-evidence option. The line-by-line cookbook provides a useful pattern.

Preserve coverage of the full resume. Include contradictory evidence when needed. A single top-ranked line is not enough if it loses the conflict.

Use independent questions together when they can share state. They cannot see one another's answers. Compose results and clear irrelevant source selections in code.

Validate every selected line ID. Retain the current rule that not-stated fields have no supporting references. Record failed validation as a failure, not a fabricated answer.

Do not add an unreported LLM call to produce evidence. Count every inference call, selection question, retry, and fallback required to complete the task.

## Keep the interface minimal

Preserve the job description on the left and PDF uploads on the right.

Add an engine dropdown above **Analyze applications**:

- **LLM structured output**
- **Jev**
- **Compare both**

Compare both freezes a single input snapshot and runs each engine over it. Preserve the same resume order and scheduling policy. Cache the completed results for that snapshot in session state.

In comparison mode, use the existing results table as a compact paired overview. When an applicant is selected, show the same questions in a three-column table: question, LLM answer, Jev answer. Highlight differing answers without declaring a winner.

Show evidence coverage and the two additional checks for both engines. Keep original source evidence available for each answer.

Below the answers, keep **Analysis details** collapsed. Inside it, show a side-by-side summary of total cost, cost basis, complete-run time, median request time, request count, failures, and both reference-label agreement groups.

Retain separate raw judgments, Jev distributions and confidence where available, model IDs, request IDs, usage, price timestamps, and evidence references in exports. The LLM has no comparable calibrated confidence field. Do not invent one.

Changing an applicant, opening analysis details, switching the result view, or exporting must not make new model calls. Changed inputs require a new comparison. A cached result is not a new zero-cost run.

If one engine fails or lacks its key, keep the other result available. Show the failed or unavailable side clearly. Do not populate it with preview data.

## Measure the complete workflow

Prefer provider-reported cost. If only usage is returned, estimate from the exact model's current published price and save the source and timestamp. Label estimates explicitly.

Count all inference needed for labels and source selection. Use returned usage for the complete request, including its questions. Do not estimate cost from question count or another provider's tokenizer. Disable hidden retries for this baseline, or instrument and include all attempts and their costs.

Report unavailable prices or usage as unavailable. Do not manufacture zero output-token counts if the API does not return them. Extend the receipt contract if necessary, preserving existing LLM records.

Use the same timing boundaries for both engines. Separate engine time from the time taken to run the two engines in comparison mode. Do not compare a warmed cached display with a live model request.

Calculate a cost-reduction percentage only when both complete positive costs are known. Calculate timing differences from comparable measurements. A slower or more expensive Jev result must remain visible.

Evaluate both engines against the existing 20 requirement labels and 10 additional checks. Include failures and every disagreement. Keep coverage, reference agreement, and confidence as separate concepts.

## Verify and document

Run the existing checks. Add meaningful checks for same-input pairing, source-reference validation, one-sided failures, complete cost accounting, and result-view changes without extra calls.

Verify the browser with the five bundled PDFs. Save a real comparison export with model IDs, input hash, measurements, and evaluation. Do not claim live verification if the required key is missing.

Update setup instructions, dependency lockfile, benchmark commands, and `.env.example`. Explain any added request or evidence-selection stage.

Prepare an ending snapshot named `02_01e` only after the integration is implemented and checked. Do not overwrite the beginning snapshot `02_01b` with the ending implementation.

Keep manual-review routing and threshold tuning for Video 5. This task supports evidence review and does not make hiring decisions.
