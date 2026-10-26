# Connect Jev without an LLM

Choose this prompt if you do not have an OpenAI or OpenRouter API key, or want Jev as the only matching engine.

You still need a TypeSafe API key for Jev. Copy the prompt below into Codex.

```text
Read https://docs.typesafe.ai/llms.txt and its Python SDK documentation.

Follow prompts/connect-jev-only.md to replace the LLM matching engine with Jev.

I do not have an OpenAI or OpenRouter API key. Require only TYPESAFE_API_KEY. Remove LLM provider configuration, runtime calls, and dependencies used only by the LLM integration. Do not add an LLM fallback or comparison mode.

Preserve the job descriptions, PDF uploads, criteria, scoring rules, and source evidence. Show Jev answers and actual cost, time, failures, and reference agreement in the collapsed analysis.

Verify the app starts and analyzes with OPENAI_API_KEY and OPENROUTER_API_KEY unset. Update the setup instructions and run the checks. Keep keys in .env.
```

For side-by-side results, choose the [comparison prompt](compare-engines.md) instead. That path needs keys for both engines.
