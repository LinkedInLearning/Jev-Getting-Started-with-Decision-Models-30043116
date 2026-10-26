"""Find exact source values and keep routing policy in ordinary code."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

AMOUNT = re.compile(
    r"(?<![\w.,])(?:USD\s*|\$\s*)(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{2})?(?![\d.,])", re.I
)
OTHER_CURRENCY = re.compile(
    r"\b(?:EUR|GBP|CAD|AUD|JPY|INR|CHF|SGD|NZD|HKD|CNY|RMB|AED)\b|[€£¥₹]", re.I
)
SIGNED_AMOUNT = re.compile(
    r"(?:[-−]\s*(?:USD\s*|\$)|(?:USD\s*|\$)\s*[-−]|\(\s*(?:USD\s*|\$))", re.I
)
MAX_TEXT = 20_000
MAX_CANDIDATES = 40
NONE = "none"


@dataclass(frozen=True)
class Candidate:
    id: str
    text: str
    value: str
    line: int
    source_line: str
    start: int
    end: int


@dataclass(frozen=True)
class Judgment:
    choice: str
    confidence: float
    probabilities: dict[str, float]
    has_payable_total: float
    unresolved_amounts: float
    model: str
    input_tokens: int | None
    output_tokens: int | None


@dataclass(frozen=True)
class Result:
    source_hash: str
    candidates: tuple[Candidate, ...]
    judgment: Judgment | None = None
    error: str | None = None
    latency_ms: float | None = None
    called_api: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Policy:
    min_confidence: float = 0.85
    min_presence: float = 0.85
    max_unresolved: float = 0.15

    def __post_init__(self):
        for value in (self.min_confidence, self.min_presence, self.max_unresolved):
            probability(value)


@dataclass(frozen=True)
class Route:
    status: str
    reasons: tuple[str, ...]
    candidate: Candidate | None = None


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def find_candidates(text: str) -> tuple[Candidate, ...]:
    if len(text) > MAX_TEXT:
        return ()
    found = []
    for index, match in enumerate(AMOUNT.finditer(text), 1):
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.end())
        line_end = len(text) if line_end == -1 else line_end
        number = re.sub(r"[^\d.]", "", match.group())
        if len(re.sub(r"\D", "", number)) > 15:
            continue
        found.append(
            Candidate(
                id=f"amount_{index}",
                text=match.group(),
                value=str(Decimal(number).quantize(Decimal("0.01"))),
                line=text.count("\n", 0, match.start()) + 1,
                source_line=text[line_start:line_end],
                start=match.start(),
                end=match.end(),
            )
        )
    return tuple(found)


def preflight(text: str, candidates: tuple[Candidate, ...]) -> str | None:
    if not text.strip():
        return "Add invoice text before checking the amount."
    if len(text) > MAX_TEXT:
        return f"The invoice exceeds the {MAX_TEXT:,}-character limit."
    if SIGNED_AMOUNT.search(text):
        return "Signed or parenthesized amounts need review. No positive total was inferred."
    if any(len(re.sub(r"\D", "", match.group())) > 15 for match in AMOUNT.finditer(text)):
        return "An amount exceeds the supported numeric range. Check the source."
    if not candidates:
        return "No supported amount was found. Check the source text."
    if len(candidates) > MAX_CANDIDATES:
        return "Too many amount candidates. Check a single invoice at a time."
    declared = re.findall(r"\bCurrency\s*:\s*([A-Z]{3})\b", text, re.I)
    if (
        not re.search(r"\bUSD\b", text, re.I)
        or OTHER_CURRENCY.search(text)
        or any(currency.upper() != "USD" for currency in declared)
    ):
        return "Confirm a single USD currency in the source. Other currencies need review."
    return None


def probability(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("Probability must be a number.")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Probability must be between zero and one.")
    return float(value)


def parse_judgment(payload: dict, candidates: tuple[Candidate, ...]) -> Judgment:
    """Validate the response contract before any field can reach a draft."""
    answers = payload["answers"]
    selection = answers["payable_amount"]
    presence = answers["has_payable_total"]
    ambiguity = answers["unresolved_amounts"]
    if selection["type"] != "choice" or any(
        answer["type"] != "noul" for answer in (presence, ambiguity)
    ):
        raise ValueError("Unexpected answer types.")
    expected = {c.id for c in candidates} | {NONE}
    if set(selection["probabilities"]) != expected or selection["choice"] not in expected:
        raise ValueError("The selected amount or options do not match the source candidates.")
    probabilities = {key: probability(p) for key, p in selection["probabilities"].items()}
    if abs(sum(probabilities.values()) - 1) > 0.01:
        raise ValueError("The choice probabilities do not sum to one.")
    choice = selection["choice"]
    if probabilities[choice] + 0.0001 < max(probabilities.values()):
        raise ValueError("The selected option is not the highest-probability option.")
    confidence = probability(selection["confidence"])
    n = len(probabilities)
    expected_confidence = (max(probabilities.values()) - 1 / n) / (1 - 1 / n)
    if abs(confidence - expected_confidence) > 0.02:
        raise ValueError("Choice confidence does not match its probability distribution.")
    model = payload["model"]
    if not isinstance(model, str) or not model.strip():
        raise ValueError("The response does not identify its model.")
    usage = payload.get("usage") or {}
    for key in ("input_tokens", "output_tokens"):
        value = usage.get(key)
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError("Invalid token usage.")
    return Judgment(
        choice=choice,
        confidence=confidence,
        probabilities=probabilities,
        has_payable_total=probability(presence["noul"]),
        unresolved_amounts=probability(ambiguity["noul"]),
        model=model,
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )


def route(result: Result, policy: Policy) -> Route:
    if result.error:
        return Route("Review required", (result.error,))
    answer = result.judgment
    if answer is None:
        return Route("Review required", ("No verified model response is available.",))
    reasons = []
    candidate = next((c for c in result.candidates if c.id == answer.choice), None)
    if candidate is None:
        reasons.append("No candidate was selected as the payable amount.")
    if answer.has_payable_total < policy.min_presence:
        reasons.append("The final amount due is not sufficiently supported by the source.")
    if answer.unresolved_amounts > policy.max_unresolved:
        reasons.append("A conflicting total or pending adjustment needs a person to check it.")
    if answer.confidence < policy.min_confidence:
        reasons.append("The amount selection falls below the confidence policy.")
    if reasons:
        return Route("Review required", tuple(reasons))
    return Route("Ready for draft", ("All three checks meet the current policy.",), candidate)
