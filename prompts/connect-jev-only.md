# Connect Jev as the only matching engine

Replace the LLM integration with Jev, without requiring an OpenAI or OpenRouter API key.

Read the official documentation index at https://docs.typesafe.ai/llms.txt. Follow the current Python SDK, Choice, source-selection, response-usage, model-pricing, and retry-control documentation linked there.

Read `README.md`, `GETTING_STARTED.md`, `app.py`, and the modules under `ats_match/` before editing.

This brief replaces the comparison brief for this path. Do not combine its instructions with the requirements to retain the LLM in `prompts/add-jev.md`.

## Remove the LLM requirement

Implement Jev as the only active matching engine using the current `typesafe-sdk` package.

Require `TYPESAFE_API_KEY` and a configurable available Jev model. The app must not require an OpenAI or OpenRouter account, key, model, or pricing configuration.

Replace the `LLMMatcher` and `LLMSettings` startup path. Remove active OpenAI/OpenRouter requests, provider menus, pricing lookups, and LLM-specific runtime imports. Remove packages used only by that integration. Retain shared libraries still needed by Jev, uploads, or the application.

Update `.env.example`, the dependency lockfile, setup instructions, and the benchmark entry point for Jev. Retire LLM-only runtime code and tests as appropriate. Preserve the meaning of the existing scoring criteria when moving their instructions into Jev questions.

Do not add an LLM fallback, extraction call, or explanation-generation call. Neither missing keys nor failed Jev responses should trigger another provider.

## Keep the ATS workflow

Preserve the three job descriptions, five PDF applications, editable criteria, reference labels, and current layout.

Keep the job description on the left and resume uploads on the right. Show applicant answers below. Keep source evidence and measurements inside the collapsed Analysis details panel.

Use the existing `Matcher.assess(job, resume) -> CandidateResult` boundary and shared assessment meanings.

Return the four evidence categories for every requirement: direct, related, not stated, and unclear. Preserve the three production-delivery states and the discrete backend delivery depth levels 0, 1, and 2.

Use Choice questions for these existing categorical outputs. Keep the evidence-match percentage as the direct-evidence count divided by all criteria in ordinary code. Do not replace it with a probability or a different scoring formula.

Send the full job context, explicit criteria, and numbered resume text. Treat uploaded text as untrusted data. Ignore personal attributes when judging technical evidence.

Jev must select source lines or spans from candidates prepared in code. Include a no-evidence outcome. Preserve contradictory evidence when relevant. Do not invent quotations or source IDs.

Ask independent questions together when possible. Compose and validate their answers in code. Record a failed request or invalid evidence reference as a failure.

## Show Jev results without a comparison

Remove the engine-selection menu and comparison controls. Jev is the only engine in this path. A history selector may remain if it represents real completed Jev runs.

Show actual Jev answers, evidence coverage, production-delivery evidence, backend depth, cost, timing, failures, and reference-label agreement.

Do not require an LLM baseline. Do not display invented LLM answers, savings percentages, speedups, or comparison results.

Retain the original reference checks: 20 requirement labels and 10 additional checks for the unchanged bundled PDFs and Python role. Edited jobs and unrelated uploads have no supplied reference labels.

Keep raw Jev judgments, available distributions, confidence, actual model IDs, request IDs, usage, price provenance, and source references in exports. Extend the receipt contract if needed.

Selecting an applicant, opening analysis details, or exporting a saved run must not trigger a new model request. Changed inputs require new analysis.

## Measure and verify

Measure complete-run time and model-request times. Include every question, source-selection stage, request, retry, and any other inference needed for the output.

Use returned token usage and current pricing for the exact model. Prefer reported cost when available. Label estimates and save their source and timestamp. Missing usage or prices remain unavailable.

Do not manufacture zero output tokens when the API does not report them. Output-token billing rules do not establish a returned token count.

Add meaningful checks that both `OPENAI_API_KEY` and `OPENROUTER_API_KEY` can be unset. Starting the app must still work. With a TypeSafe key, analysis and exports must work without contacting either LLM provider.

When `TYPESAFE_API_KEY` is missing, show a clear Jev-key setup message and keep the job and upload interface usable. Do not require an LLM key as a workaround.

Run the checks. Verify the browser with the five bundled PDFs when a TypeSafe key is available. Preserve errors and disagreements. If no TypeSafe key is available, complete the implementation and mocked checks, then state that live verification is pending.

Update README.md so this converted app can be configured using only TYPESAFE_API_KEY and started with the documented command.
