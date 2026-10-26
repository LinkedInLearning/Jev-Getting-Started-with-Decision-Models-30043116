import json

import httpx2
import pytest
from typesafe_sdk import RetryPolicy, TypeSafeClient

from evidence_check.engine import JevVerifier


def response_payload():
    return {
        "model": "jev-1.14.0",
        "usage": {"input_tokens": 1000, "output_tokens": 40},
        "answers": {
            "relation": {
                "type": "choice",
                "choice": "supported",
                "confidence": 0.95,
                "probabilities": {
                    "supported": 0.97,
                    "contradicted": 0.01,
                    "insufficient_evidence": 0.02,
                },
            },
            "evidence": {
                "type": "choice",
                "choice": "identity",
                "confidence": 0.95,
                "probabilities": {"identity": 0.97, "automation": 0.01, "none": 0.02},
            },
        },
    }


def client_for(payload, captured):
    def handle(request):
        captured.append(json.loads(request.content))
        assert request.url.path == "/v1/systemone"
        return httpx2.Response(200, json=payload)

    return TypeSafeClient(
        api_key="local-test-key",
        transport=httpx2.MockTransport(handle),
        retry=RetryPolicy(max_retries=0),
    )


def test_real_sdk_contract_and_input_only_cost(pack):
    captured = []
    client = client_for(response_payload(), captured)
    try:
        result = JevVerifier("local-test-key", client=client).assess(pack, pack.cases[0])
    finally:
        client.close()
    assert result.verdict == "supported"
    assert result.evidence_id == "identity"
    assert result.usage.estimated_cost_usd == pytest.approx(0.000042)
    assert result.usage.input_tokens == 1000
    assert captured[0]["state"] == pack.state_for(pack.cases[0])
    assert set(captured[0]["questions"]) == {"relation", "evidence"}


@pytest.mark.parametrize("failure", ["unknown_id", "bad_sum", "wrong_choice", "missing_answer"])
def test_invalid_model_contracts_are_rejected(pack, failure):
    payload = response_payload()
    if failure == "unknown_id":
        payload["answers"]["evidence"]["choice"] = "invented"
    elif failure == "bad_sum":
        payload["answers"]["relation"]["probabilities"]["supported"] = 0.4
    elif failure == "wrong_choice":
        payload["answers"]["relation"]["choice"] = "contradicted"
    elif failure == "missing_answer":
        del payload["answers"]["evidence"]
    client = client_for(payload, [])
    try:
        with pytest.raises(ValueError):
            JevVerifier("local-test-key", client=client).assess(pack, pack.cases[0])
    finally:
        client.close()


def test_unknown_model_price_is_not_zero(pack):
    payload = response_payload()
    payload["model"] = "a-future-model"
    client = client_for(payload, [])
    try:
        result = JevVerifier("local-test-key", client=client).assess(pack, pack.cases[0])
    finally:
        client.close()
    assert result.usage.estimated_cost_usd is None
    assert result.usage.price_source is None


def test_missing_output_count_stays_unknown_while_input_cost_remains_known(pack):
    payload = response_payload()
    payload["usage"]["output_tokens"] = None
    client = client_for(payload, [])
    try:
        result = JevVerifier("local-test-key", client=client).assess(pack, pack.cases[0])
    finally:
        client.close()
    assert result.usage.output_tokens is None
    assert result.usage.estimated_cost_usd == pytest.approx(0.000042)


def test_missing_key_is_an_explicit_setup_error():
    with pytest.raises(ValueError, match="TYPESAFE_API_KEY"):
        JevVerifier(" ")
