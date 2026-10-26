# Compare the LLM and Jev

Choose this prompt if you have an LLM provider key and want side-by-side answers, costs, and timing.

No OpenAI or OpenRouter key? Choose the [Jev-only prompt](jev-only.md) instead. That path removes the LLM requirement and needs only a TypeSafe key.

Copy the prompt below into Codex.

```text
Read https://docs.typesafe.ai/llms.txt and its Python SDK documentation.

Follow prompts/add-jev.md to add Jev as a second matching engine in this ATS.

Keep the LLM engine available. Add an engine menu with LLM structured output, Jev, and Compare both.

Compare both must use the same job, resumes, criteria, and scoring rules. Show both engines' answers side by side. Show actual cost, time, failures, and reference-label agreement in the collapsible analysis.

Preserve source evidence. Run the checks and update the setup instructions. Keep API keys in .env.
```
