"""Validated contracts returned by the decision layer."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ContentCategory(str, Enum):
    GENERAL = "general"
    QUESTION_ANSWERING = "question_answering"
    CODING = "coding"
    DATA_ANALYSIS = "data_analysis"
    CREATIVE = "creative"
    TRANSACTIONAL = "transactional"
    SENSITIVE = "sensitive"
    UNSUPPORTED = "unsupported"


class RequestRoute(str, Enum):
    DIRECT_RESPONSE = "direct_response"
    KNOWLEDGE_AGENT = "knowledge_agent"
    CODE_AGENT = "code_agent"
    DATA_AGENT = "data_agent"
    CREATIVE_AGENT = "creative_agent"
    ACTION_AGENT = "action_agent"
    HUMAN_REVIEW = "human_review"
    REJECT = "reject"


class AgentAction(str, Enum):
    RESPOND = "respond"
    ASK_CLARIFYING_QUESTION = "ask_clarifying_question"
    RETRIEVE_CONTEXT = "retrieve_context"
    USE_TOOL = "use_tool"
    DELEGATE = "delegate"
    REQUEST_APPROVAL = "request_approval"
    ESCALATE = "escalate"
    REFUSE = "refuse"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Decision(BaseModel):
    """A single, auditable decision for an incoming request."""

    model_config = ConfigDict(extra="forbid")

    category: ContentCategory
    route: RequestRoute
    next_action: AgentAction
    risk: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1, max_length=500)
    required_capabilities: list[str] = Field(max_length=10)

