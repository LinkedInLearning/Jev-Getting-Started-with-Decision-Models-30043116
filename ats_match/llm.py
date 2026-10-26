"""Structured-output LLM matching, response validation, and usage accounting."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import perf_counter

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from ats_match.data import ROOT
from ats_match.domain import (
    Assessment,
    CandidateResult,
    Job,
    PriceSnapshot,
    Receipt,
    Resume,
    finite_number,
    validate_evidence,
)
from ats_match.prompts import messages_for, response_schema


@dataclass
class LLMSettings:
    provider: str = "openrouter"
    model: str = "openai/gpt-4.1-mini"
    api_key: str = field(default="", repr=False)
    timeout: float = 60.0
    max_output_tokens: int = 1800
    manual_price: PriceSnapshot | None = None

    @property
    def endpoint(self) -> str:
        return {
            "openrouter": "https://openrouter.ai/api/v1/chat/completions",
            "openai": "https://api.openai.com/v1/chat/completions",
        }[self.provider]

    @classmethod
    def from_env(cls) -> LLMSettings:
        # A local file takes precedence, so adding a key does not require a server restart.
        load_dotenv(ROOT / ".env", override=True)
        provider = os.getenv("LLM_PROVIDER", "openrouter").strip()
        if provider not in ("openrouter", "openai"):
            raise ValueError("LLM_PROVIDER must be openrouter or openai.")
        model = os.getenv("LLM_MODEL") or (
            "openai/gpt-4.1-mini" if provider == "openrouter" else "gpt-4.1-mini"
        )
        key_name = "OPENROUTER_API_KEY" if provider == "openrouter" else "OPENAI_API_KEY"
        price = None
        input_rate = os.getenv("LLM_INPUT_USD_PER_MILLION", "").strip()
        output_rate = os.getenv("LLM_OUTPUT_USD_PER_MILLION", "").strip()
        if input_rate and output_rate:
            cache = os.getenv("LLM_CACHED_INPUT_USD_PER_MILLION", "").strip()
            price = PriceSnapshot(
                model=model,
                input_per_million=float(input_rate),
                output_per_million=float(output_rate),
                cached_input_per_million=float(cache) if cache else None,
                source=os.getenv("LLM_PRICE_SOURCE") or "Local configured rates",
                checked_at=datetime.now(UTC).isoformat(),
            )
        return cls(
            provider=provider,
            model=model,
            api_key=os.getenv(key_name, "").strip(),
            timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
            max_output_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1800")),
            manual_price=price,
        )


def fetch_openrouter_price(model: str, client: httpx.Client) -> PriceSnapshot | None:
    """Fetch public rates. An unavailable quote is not a zero-dollar price."""
    try:
        response = client.get("https://openrouter.ai/api/v1/models", timeout=10)
        response.raise_for_status()
        match = next((m for m in response.json()["data"] if m["id"] == model), None)
        if match is None:
            return None
        rates = match["pricing"]
        return PriceSnapshot(
            model=model,
            input_per_million=float(rates["prompt"]) * 1_000_000,
            output_per_million=float(rates["completion"]) * 1_000_000,
            cached_input_per_million=(
                float(rates["input_cache_read"]) * 1_000_000
                if rates.get("input_cache_read") is not None
                else None
            ),
            source="https://openrouter.ai/api/v1/models",
            checked_at=datetime.now(UTC).isoformat(),
        )
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None


def _token_count(usage: dict, key: str) -> int | None:
    value = usage.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def fill_usage(receipt: Receipt, body: dict, price: PriceSnapshot | None) -> Receipt:
    usage = body.get("usage") or {}
    receipt.actual_model = body.get("model")
    receipt.request_id = body.get("id")
    receipt.input_tokens = _token_count(usage, "prompt_tokens")
    receipt.output_tokens = _token_count(usage, "completion_tokens")
    receipt.cached_input_tokens = _token_count(
        usage.get("prompt_tokens_details") or {}, "cached_tokens"
    )
    receipt.reasoning_tokens = _token_count(
        usage.get("completion_tokens_details") or {}, "reasoning_tokens"
    )
    reported = finite_number(usage.get("cost"))
    if reported is not None:
        receipt.cost_usd = reported
        receipt.cost_basis = "reported"
    elif (
        price is not None and receipt.input_tokens is not None and receipt.output_tokens is not None
    ):
        # Never estimate a fallback/versioned model with a different model's rates.
        actual = receipt.actual_model or receipt.requested_model
        known_aliases = {price.model, price.model.removeprefix("openai/")}
        if actual in known_aliases:
            cached = min(receipt.cached_input_tokens or 0, receipt.input_tokens)
            if cached == 0 or price.cached_input_per_million is not None:
                receipt.cost_usd = (
                    (receipt.input_tokens - cached) * price.input_per_million
                    + cached * (price.cached_input_per_million or 0)
                    + receipt.output_tokens * price.output_per_million
                ) / 1_000_000
                receipt.cost_basis = "estimated"
    receipt.price = price
    return receipt


def _friendly_http_error(status: int) -> str:
    if status == 401:
        return "The provider rejected the API key. Check your local .env file."
    if status in (402, 403):
        return "The provider blocked this request. Check account credits, budgets, and access."
    if status == 429:
        return "The provider rate-limited the request. Wait before running it again."
    if status == 400:
        return "The provider rejected the model or JSON schema. Choose a model with structured-output support."
    return f"The provider returned HTTP {status}. Try again after checking the provider status."


class LLMMatcher:
    """One strict JSON request per resume. No hidden retries, reasoning calls, or fallback models."""

    def __init__(self, settings: LLMSettings, *, client: httpx.Client | None = None):
        self.settings = settings
        self.client = client or httpx.Client(timeout=settings.timeout, follow_redirects=False)
        self._owns_client = client is None
        self._price_loaded = False
        self.price = settings.manual_price

    def close(self):
        if self._owns_client:
            self.client.close()

    def assess(self, job: Job, resume: Resume) -> CandidateResult:
        settings = self.settings
        receipt = Receipt(
            requested_model=settings.model,
            provider=settings.provider,
            latency_seconds=0,
        )
        if not settings.api_key:
            key_name = (
                "OPENROUTER_API_KEY" if settings.provider == "openrouter" else "OPENAI_API_KEY"
            )
            return CandidateResult(
                resume_id=resume.id,
                receipt=receipt,
                error=f"Add {key_name} to the local .env file, then run the match again.",
            )
        if not self._price_loaded:
            if self.price is None and settings.provider == "openrouter":
                self.price = fetch_openrouter_price(settings.model, self.client)
            self._price_loaded = True

        payload = {
            "model": settings.model,
            "messages": messages_for(job, resume),
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "resume_evidence",
                    "strict": True,
                    "schema": response_schema(job, resume),
                },
            },
        }
        # GPT-4.1 supports temperature. Other configurable models can use their defaults.
        if "gpt-4" in settings.model:
            payload["temperature"] = 0
        if settings.provider == "openrouter":
            payload.update(
                {
                    "max_tokens": settings.max_output_tokens,
                    "provider": {"require_parameters": True, "allow_fallbacks": False},
                }
            )
        else:
            payload["max_completion_tokens"] = settings.max_output_tokens
        started = perf_counter()
        try:
            response = self.client.post(
                settings.endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.api_key}",
                    "Content-Type": "application/json",
                },
            )
            receipt.latency_seconds = perf_counter() - started
            if response.is_error:
                return CandidateResult(
                    resume_id=resume.id,
                    receipt=receipt,
                    error=_friendly_http_error(response.status_code),
                )
            body = response.json()
            receipt = fill_usage(receipt, body, self.price)
            if body.get("error"):
                return CandidateResult(
                    resume_id=resume.id,
                    receipt=receipt,
                    error="The provider returned a generation error. Inspect its dashboard.",
                )
            choice = body["choices"][0]
            if choice.get("finish_reason") != "stop":
                return CandidateResult(
                    resume_id=resume.id,
                    receipt=receipt,
                    error="The response was interrupted, refused, or exceeded the output limit.",
                )
            content = choice["message"].get("content")
            if not isinstance(content, str):
                raise ValueError("The model did not return a JSON object.")
            assessment = Assessment.model_validate_json(content)
            validate_evidence(assessment, job, resume)
            return CandidateResult(resume_id=resume.id, assessment=assessment, receipt=receipt)
        except httpx.TimeoutException:
            error = "The model request timed out. No result was substituted."
        except httpx.HTTPError:
            error = "The model request could not reach the provider. Check your connection."
        except (ValueError, KeyError, IndexError, TypeError, ValidationError, json.JSONDecodeError):
            error = "The response failed schema or evidence-reference validation. Run again or inspect the provider trace."
        receipt.latency_seconds = perf_counter() - started
        return CandidateResult(resume_id=resume.id, receipt=receipt, error=error)
