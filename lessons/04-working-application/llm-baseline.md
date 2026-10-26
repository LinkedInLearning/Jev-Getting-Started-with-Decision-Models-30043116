# Live LLM baseline

## Five PDF applications

The redesigned applicant-review workflow was checked on 26 October 2026 using five real PDF uploads, the built-in Python Backend Engineer description, OpenRouter, and `openai/gpt-4.1-mini`.

| Measurement | Observed result |
| --- | --- |
| Successful requests | 5 of 5 |
| Complete run time | 13.48 seconds |
| Median model request | 2.63 seconds |
| Provider-reported API cost | $0.0040656 |
| Input tokens | 7,440 |
| Output tokens | 681 |
| Requirement-label agreement | 18 of 20 |
| Additional evidence-check agreement | 8 of 10 |

Four judgments differed from the hand-labeled references:

- Marcus's conflicting deployment evidence was labeled not stated instead of unclear.
- Marcus's skills-list mention of pytest was labeled direct instead of related.
- Elena's data pipeline work received backend delivery depth 1 instead of 0.
- Marcus's production-delivery check was not stated instead of unclear.

These disagreements remain in the results. The prompt was not tuned to turn this small set into a perfect score.

The browser export was verified and saved locally as `runs/ats-applications-baseline.json`. Run ID: `0e99705d968e`. Prompt version: `ats-evidence-v1`.

## Earlier short-text check

Checked on 26 October 2026 with OpenRouter and `openai/gpt-4.1-mini`.

This is one run over the three bundled synthetic resumes. It is a functional check, not a production benchmark.

| Measurement | Observed result |
| --- | --- |
| Successful requests | 3 of 3 |
| Complete run time | 9.93 seconds |
| Median model request | 3.00 seconds |
| Provider-reported API cost | $0.0016804 |
| Input tokens | 2,673 |
| Output tokens | 382 |
| Requirement-label agreement | 12 of 12 |
| Additional evidence-check agreement | 5 of 6 |

The data-engineering resume received backend delivery depth 1. The reference label is 0 because no backend service project is documented.

All three production-delivery checks agreed with the reference labels.

The evidence references passed structural validation. That does not establish that every semantic judgment is correct.

The browser workflow was also run successfully. Its separate run took 7.64 seconds and reported $0.0016756 for three requests. Request times and generated output lengths can vary.

The full first-run receipt, frozen inputs, results, price snapshot, and evaluation are saved locally in `runs/llm-baseline.json`. That directory is ignored by Git.

Run ID: `91e702d1f097`. Prompt version: `ats-evidence-v1`.

Both evaluations report requirement labels separately from the production-delivery and backend-depth checks. Preserve both groups in the later Jev comparison.

No Jev calls have been made. Comparative savings are not measured yet.
