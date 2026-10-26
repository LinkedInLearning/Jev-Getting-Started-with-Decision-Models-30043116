# Evidence Check

Check product claims against cited source passages with Jev.

The app shows expected and actual verdicts, relevant source IDs, regression failures, and API usage.
It uses TypeSafe only. No OpenAI or OpenRouter account is required.

## Run

Requires Git, Python 3.12, and uv.

```bash
git clone --branch 02_03 --single-branch https://github.com/LinkedInLearning/Jev-Getting-Started-with-Decision-Models-30043116.git evidence-check
cd evidence-check
uv sync --locked
cp .env.example .env
uv run streamlit run app.py
```

Open http://localhost:8503.

On Windows, use `copy .env.example .env` instead of `cp`.

Add your key to the local `.env` file:

```dotenv
TYPESAFE_API_KEY=your_key_here
TYPESAFE_MODEL=jev-1.14.0
```

Refresh the app after saving the key.
Without a key, you can inspect the claims, expected labels, and source library.
Actual results remain empty until a live run.
Never commit `.env`.

Use separate clone folders to run this app alongside other applications.
This app uses port 8503 by default.

## Use the app

1. Click **Run all checks**.
2. Compare expected and actual verdicts in **Checks**.
3. Use **Inspect a check** to read its source passages.
4. Open **Analysis details** for the confusion matrix, regression pairs, usage, and JSON export.

The reference pack contains fictional product documentation.
It covers normal, boundary, negative, partial, missing, contradictory, and adversarial cases.

Jev answers two independent Choice questions in one request:

- Does the source support, contradict, or fail to establish the claim?
- Which supplied source most directly establishes its truth or falsity?

Expected labels are never sent to Jev.
Code checks missing sources and alleged verbatim quotes before making an API call.
A quote appearing in a source does not mean its context supports the claim.
A valid source ID is also not proof of support.

## Interpret the results

**Verdict agreement** includes all 12 workflow cases.
API failures count as failures, not missing rows.

**Evidence ID agreement** and **semantic verdict agreement** cover the 10 model cases.
They compare against independently written expected labels.
The two deterministic source prechecks have a separate agreement count.

**Unexpected ready verdicts** counts claims marked ready when their verdict or chosen evidence differs from the reference labels.
**Sent to review** includes insufficient evidence, conflicting judgments, low confidence, and API errors.
Ready is a local review status. The app does not publish content.

The confidence threshold is an example policy, not a calibrated guarantee.
Changing it reuses saved answers without another API request.
The two regression pairs preserve labels while changing the wording or option order.
Unchanged answers on a few fixtures do not prove general robustness.

## Usage and cost

The run receipt logs the resolved model, tokens, API requests, errors, and measured wall time.
Automatic retries are disabled so every attempted call is visible.
Estimated cost uses the published input-token price for recognized model versions.
Output tokens are free under that price schedule.
Unknown usage and failed requests make the total incomplete.
A failed request may still be billable.

Pricing source: [TypeSafe models](https://docs.typesafe.ai/models), checked 2026-10-26.
No sample performance or cost results are presented as live measurements.

## Change the reference pack

Edit `data/reference_pack.json`.
Each claim cites source IDs and includes an expected verdict and expected evidence IDs.
The special evidence value `none` means no supplied passage establishes the claim.
Unknown source IDs and changed labels on regression variants are rejected.
Changes to sources, questions, or the model invalidate previous results.

Review labels before running a comparison.
Keep a separate held-out set when revising questions or choosing thresholds.
Keep exact arithmetic, string checks, and execution rules in code.

## Checks

```bash
uv run pytest -q
uv run ruff check .
```

Automated checks use mocked API responses. They do not measure live model quality.

## References

- [Citation verification cookbook](https://docs.typesafe.ai/cookbooks/citation_check)
- [Choice questions](https://docs.typesafe.ai/primitives/choice)
- [Confidence](https://docs.typesafe.ai/confidence)
- [Python SDK](https://docs.typesafe.ai/sdk/python)
- [Known Jev 1.13 failure modes](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
