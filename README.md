# Ledger Intake

Capture a supplier invoice total from its source text.
Jev selects an exact amount candidate.
Code sends the result to a draft or a review queue.

## Run

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
git clone --branch 02_02 --single-branch https://github.com/LinkedInLearning/Jev-Getting-Started-with-Decision-Models-30043116.git jev-invoice-intake
cd jev-invoice-intake
uv sync --locked
cp .env.example .env
```

Add your TypeSafe key to `TYPESAFE_API_KEY` in `.env`.
Get a key from the [TypeSafe console](https://console.typesafe.ai/).
Keep the key on your machine.

```bash
uv run streamlit run app.py --server.port 8502
```

Open [localhost:8502](http://localhost:8502).
No OpenAI or OpenRouter key is needed.
Without a TypeSafe key, the interface still shows invoices and extracted values.
Model judgments appear only after a real successful request.

## Use

1. Select a fictional supplier invoice or edit its text.
2. Click **Check invoice**.
3. Inspect the selected amount and its original source line.
4. Review the separate Choice and Noul judgments.
5. Adjust the review policy without making another API call.

The initial policy values are illustrative, not validated operating thresholds.
A confident selection can still be wrong.
Missing evidence and unresolved adjustments independently block a draft.

This app supports text invoices with an explicit USD currency.
It copies found amounts and never generates a new total.
It creates an exportable draft only, with no payment action.
It does not run OCR or accept PDF uploads.
Token usage and request time come from the real request.
Billed cost is unavailable when the provider does not return it.

## Structure

- `invoice_intake/core.py`: candidate extraction, response validation, and review policy.
- `invoice_intake/jev.py`: one Jev request with three independent questions.
- `data/invoices.json`: fictional invoices with clear, unresolved, and missing totals.
- `tests/`: policy, failure, API contract, and interface checks.

```bash
uv run pytest -q
uv run ruff check .
```

## References

- [Pre-parsed value extraction](https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook)
- [Confidence](https://docs.typesafe.ai/confidence)
- [Choice](https://docs.typesafe.ai/primitives/choice)
- [Noul](https://docs.typesafe.ai/primitives/noul)
- [Python SDK](https://docs.typesafe.ai/sdk/python)
