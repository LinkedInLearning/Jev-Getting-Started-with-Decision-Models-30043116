"""Run a reproducible LLM baseline over the bundled synthetic examples."""

import argparse
import json
from pathlib import Path

from ats_match.data import load_application_samples, load_samples
from ats_match.llm import LLMMatcher, LLMSettings
from ats_match.workflow import evaluate, run_matching


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("runs/llm-baseline.json"))
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--dataset", choices=["applications", "small"], default="applications")
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error("Use 1 to 10 repeats.")
    settings = LLMSettings.from_env()
    if not settings.api_key:
        parser.error("Configure the provider API key in .env before running a live benchmark.")
    job, resumes, labels = (
        load_application_samples() if args.dataset == "applications" else load_samples()
    )
    matcher = LLMMatcher(settings)
    runs = []
    try:
        for _ in range(args.repeats):
            run = run_matching(job, resumes, matcher)
            quality = evaluate(run, job, resumes, labels)
            runs.append(
                {"run": run.model_dump(mode="json"), "summary": run.summary, "evaluation": quality}
            )
            print(json.dumps({"run_id": run.id, **run.summary, "evaluation": quality}, indent=2))
    finally:
        matcher.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"runs": runs}, indent=2))
    print(f"Saved {len(runs)} live run(s) to {args.out}")
    return int(any(r["summary"]["failed"] for r in runs))


if __name__ == "__main__":
    raise SystemExit(main())
