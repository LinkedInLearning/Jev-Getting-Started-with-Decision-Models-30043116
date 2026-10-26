from __future__ import annotations

import json
from functools import partial

import httpx2
from typesafe_sdk import TypeSafeClient

from invoice_intake.core import Policy, find_candidates, route
from invoice_intake.jev import check_invoice
from tests.conftest import answer_payload


def test_official_sdk_serializes_questions_and_reads_response_without_network():
    text = "Currency: USD\nSubtotal $40.00\nTax $10.00\nTotal due $50.00"
    payload = answer_payload(find_candidates(text), choice="amount_3")
    captured = []

    def handle(request):
        captured.append(json.loads(request.content))
        assert request.url.path == "/v1/systemone"
        assert request.headers["Authorization"] == "Bearer not-real"
        return httpx2.Response(200, json=payload)

    factory = partial(TypeSafeClient, transport=httpx2.MockTransport(handle))
    result = check_invoice(text, api_key="not-real", client_factory=factory)
    assert len(captured) == 1
    assert captured[0]["questions"]["payable_amount"]["type"] == "choice"
    assert captured[0]["questions"]["has_payable_total"]["type"] == "noul"
    assert captured[0]["questions"]["unresolved_amounts"]["type"] == "noul"
    assert route(result, Policy()).candidate.value == "50.00"


def test_sdk_http_error_does_not_retry_or_create_a_draft():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx2.Response(429, json={"error": "Rate limited"})

    factory = partial(TypeSafeClient, transport=httpx2.MockTransport(handle))
    result = check_invoice(
        "Currency: USD\nTotal due $50.00", api_key="not-real", client_factory=factory
    )
    assert len(calls) == 1
    assert result.judgment is None
    assert route(result, Policy()).status == "Review required"
