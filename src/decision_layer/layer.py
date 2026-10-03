"""GPT-6 Luna powered decision layer."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from .models import AgentAction, ContentCategory, Decision, RequestRoute

SYSTEM_INSTRUCTIONS = """You are a decision layer for an agentic application.
Analyze the incoming request and return only the structured decision requested by
the supplied schema.

Apply these rules:
- Classify the request by its primary intent.
- Route it to the narrowest capable handler.
- Select exactly one immediate next action, not a multi-step plan.
- Prefer asking a clarifying question when essential information is missing.
- Use request_approval before consequential external actions.
- Use human_review or escalate for high-risk ambiguity.
- Use reject/refuse only when the request cannot be safely or validly handled.
- Keep rationale short and do not include hidden chain-of-thought; state only the
  decisive factors.
"""


class DecisionLayerError(RuntimeError):
    """Raised when a valid decision cannot be produced."""


class DecisionLayer:
    """Classify, route, and choose an agent's next action in one model call.

    The SDK automatically reads ``OPENAI_API_KEY``. A client can be injected for
    tests or for applications that already manage an OpenAI client.
    """

    def __init__(
        self,
        *,
        client: Any | None = None,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        self._client = client or OpenAI()
        self.model = model or os.getenv("OPENAI_DECISION_MODEL", "gpt-6-luna")
        self.reasoning_effort = reasoning_effort or os.getenv(
            "OPENAI_DECISION_REASONING_EFFORT", "low"
        )

    def decide(
        self,
        request: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> Decision:
        """Return classification, route, and next action for ``request``."""
        if not request or not request.strip():
            raise ValueError("request must not be empty")

        input_items: list[dict[str, str]] = []
        if context:
            context_lines = "\n".join(
                f"- {key}: {value}" for key, value in sorted(context.items())
            )
            input_items.append(
                {
                    "role": "developer",
                    "content": f"Available application context:\n{context_lines}",
                }
            )
        input_items.append({"role": "user", "content": request})

        try:
            response = self._client.responses.create(
                model=self.model,
                instructions=SYSTEM_INSTRUCTIONS,
                input=input_items,
                reasoning={"effort": self.reasoning_effort},
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "agent_decision",
                        "strict": True,
                        "schema": Decision.model_json_schema(),
                    }
                },
            )
            output_text = response.output_text
            if not output_text:
                raise DecisionLayerError("OpenAI returned no decision output")
            return Decision.model_validate_json(output_text)
        except DecisionLayerError:
            raise
        except (ValidationError, ValueError, TypeError) as exc:
            raise DecisionLayerError("OpenAI returned an invalid decision") from exc
        except Exception as exc:
            raise DecisionLayerError("Decision request failed") from exc

    def classify_content(self, request: str, **kwargs: Any) -> ContentCategory:
        """Convenience accessor for content classification."""
        return self.decide(request, **kwargs).category

    def route_request(self, request: str, **kwargs: Any) -> RequestRoute:
        """Convenience accessor for request routing."""
        return self.decide(request, **kwargs).route

    def select_next_action(self, request: str, **kwargs: Any) -> AgentAction:
        """Convenience accessor for the immediate agent action."""
        return self.decide(request, **kwargs).next_action

