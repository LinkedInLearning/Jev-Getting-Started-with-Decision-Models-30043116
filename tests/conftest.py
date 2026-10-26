from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def invoices():
    return json.loads((Path(__file__).parents[1] / "data/invoices.json").read_text())


def answer_payload(candidates, choice=None, top_probability=0.98, presence=0.99, unresolved=0.01):
    options = [c.id for c in candidates] + ["none"]
    choice = choice or options[0]
    probabilities = {key: (1 - top_probability) / (len(options) - 1) for key in options}
    probabilities[choice] = top_probability
    n = len(options)
    return {
        "model": "jev-test",
        "answers": {
            "payable_amount": {
                "type": "choice",
                "choice": choice,
                "confidence": (top_probability - 1 / n) / (1 - 1 / n),
                "probabilities": probabilities,
            },
            "has_payable_total": {"type": "noul", "noul": presence},
            "unresolved_amounts": {"type": "noul", "noul": unresolved},
        },
        "usage": {"input_tokens": 300, "output_tokens": 60},
    }
