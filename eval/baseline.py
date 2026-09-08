"""A dumb, rule-based baseline for comparison against the agent.

No LLM calls -- just threshold checks on the same fields the agent has
access to. The point of scoring both against the same labeled set is
to see exactly where the agent earns its keep (usually: cases that
need reading the comment thread, not just the metadata).
"""

from datetime import datetime, timezone

STALE_DAYS = 14
PRIORITY_IDLE_DAYS = 7
PRIORITY_LABELS = {"priority: high", "priority: critical", "p0", "p1"}


def _days_since(timestamp: str) -> int:
    updated = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - updated).days


def classify(issue: dict, comments: list[dict]) -> str | None:
    """Returns a risk category, or None if the issue looks healthy.

    Deliberately shallow: it never reads `comments` -- that's the gap
    the agent is meant to close.
    """
    labels = {label.lower() for label in issue.get("labels", [])}
    days_idle = _days_since(issue["updated_at"])

    if "blocked" in labels:
        return "blocked"
    if not issue.get("assignee"):
        return "unowned"
    if labels & PRIORITY_LABELS and days_idle >= PRIORITY_IDLE_DAYS:
        return "at_risk_priority"
    if days_idle >= STALE_DAYS:
        return "stale"
    return None
