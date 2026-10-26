from pathlib import Path

import pytest

from evidence_check.domain import Judgment, Usage, load_pack


@pytest.fixture
def pack():
    return load_pack(Path(__file__).parents[1] / "data/reference_pack.json")


def judgment(verdict="supported", evidence_id="identity", confidence=0.95, **usage):
    probabilities = {"supported": 0.0, "contradicted": 0.0, "insufficient_evidence": 0.0}
    probabilities[verdict] = 1.0
    return Judgment(
        verdict=verdict,
        confidence=confidence,
        probabilities=probabilities,
        evidence_id=evidence_id,
        evidence_confidence=confidence,
        evidence_probabilities={evidence_id: 1.0},
        model="jev-1.14.0",
        usage=Usage(input_tokens=100, output_tokens=20, estimated_cost_usd=0.0000042, **usage),
    )


class ReferenceVerifier:
    model = "jev-1.14.0"

    def __init__(self):
        self.calls = []

    def assess(self, pack, case):
        self.calls.append(case.id)
        return judgment(case.expected, case.expected_evidence[0])

    def close(self):
        pass


@pytest.fixture
def verifier():
    return ReferenceVerifier()
