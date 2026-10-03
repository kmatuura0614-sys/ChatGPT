from types import SimpleNamespace

import pytest

from decision_layer import (
    AgentAction,
    ContentCategory,
    DecisionLayer,
    DecisionLayerError,
    RequestRoute,
)


VALID_DECISION = """{
  "category": "coding",
  "route": "code_agent",
  "next_action": "retrieve_context",
  "risk": "low",
  "confidence": 0.94,
  "rationale": "The request requires a repository change.",
  "required_capabilities": ["repository_access"]
}"""


class FakeResponses:
    def __init__(self, output_text=VALID_DECISION, error=None):
        self.output_text = output_text
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(output_text=self.output_text)


def make_layer(responses=None):
    responses = responses or FakeResponses()
    client = SimpleNamespace(responses=responses)
    return DecisionLayer(client=client), responses


def test_decide_returns_validated_decision_and_uses_luna():
    layer, responses = make_layer()

    decision = layer.decide("Please fix the failing tests.")

    assert decision.category is ContentCategory.CODING
    assert decision.route is RequestRoute.CODE_AGENT
    assert decision.next_action is AgentAction.RETRIEVE_CONTEXT
    call = responses.calls[0]
    assert call["model"] == "gpt-6-luna"
    assert call["text"]["format"]["strict"] is True
    assert "api_key" not in call


def test_context_is_passed_as_developer_input():
    layer, responses = make_layer()

    layer.decide("Deploy it", context={"approval_required": True, "env": "prod"})

    assert responses.calls[0]["input"][0]["role"] == "developer"
    assert "approval_required: True" in responses.calls[0]["input"][0]["content"]


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        ("classify_content", ContentCategory.CODING),
        ("route_request", RequestRoute.CODE_AGENT),
        ("select_next_action", AgentAction.RETRIEVE_CONTEXT),
    ],
)
def test_convenience_accessors(method, expected):
    layer, _ = make_layer()
    assert getattr(layer, method)("Update the implementation") is expected


def test_empty_request_is_rejected_without_api_call():
    layer, responses = make_layer()
    with pytest.raises(ValueError, match="must not be empty"):
        layer.decide("  ")
    assert responses.calls == []


def test_invalid_model_output_is_wrapped():
    layer, _ = make_layer(FakeResponses(output_text='{"category": "unknown"}'))
    with pytest.raises(DecisionLayerError, match="invalid decision"):
        layer.decide("Hello")


def test_api_error_is_wrapped_without_leaking_details():
    layer, _ = make_layer(FakeResponses(error=RuntimeError("secret upstream detail")))
    with pytest.raises(DecisionLayerError, match="Decision request failed") as exc:
        layer.decide("Hello")
    assert "secret" not in str(exc.value)

