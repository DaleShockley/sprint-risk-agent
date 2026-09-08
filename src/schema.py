"""Structured output schema for risk verdicts.

Keeping this as a typed model (instead of trusting raw JSON from the
model) is what makes the agent's output checkable and testable.
"""

from typing import Literal

from pydantic import BaseModel

RiskCategory = Literal["stale", "blocked", "unowned", "at_risk_priority"]
Confidence = Literal["low", "medium", "high"]


class RiskVerdict(BaseModel):
    issue: int
    risk: RiskCategory
    confidence: Confidence
    reason: str
    recommended_action: str
