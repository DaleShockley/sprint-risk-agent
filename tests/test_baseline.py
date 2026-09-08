"""Regression tests for the rule-based baseline.

Uses dates computed relative to "now" (not fixed strings) so these
stay correct no matter when the suite runs -- unlike the demo
eval/labeled_issues.json, which uses fixed dates and is meant to be
refreshed periodically against a real repo.
"""

from datetime import datetime, timedelta, timezone

from eval.baseline import classify


def _iso(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def test_classify_flags_blocked_label_regardless_of_recency():
    issue = {"labels": ["blocked"], "assignee": "alice", "updated_at": _iso(1)}
    assert classify(issue, []) == "blocked"


def test_classify_flags_unowned_when_no_assignee():
    issue = {"labels": [], "assignee": None, "updated_at": _iso(1)}
    assert classify(issue, []) == "unowned"


def test_classify_flags_stale_after_threshold():
    issue = {"labels": [], "assignee": "alice", "updated_at": _iso(20)}
    assert classify(issue, []) == "stale"


def test_classify_flags_at_risk_priority_when_idle_a_week():
    issue = {"labels": ["priority: high"], "assignee": "alice", "updated_at": _iso(10)}
    assert classify(issue, []) == "at_risk_priority"


def test_classify_returns_none_when_healthy():
    issue = {"labels": [], "assignee": "alice", "updated_at": _iso(1)}
    assert classify(issue, []) is None


def test_classify_ignores_comments_by_design():
    # documents the known gap the agent is meant to close
    issue = {"labels": ["blocked"], "assignee": "alice", "updated_at": _iso(1)}
    comments = [{"author": "alice", "body": "actually this got resolved yesterday"}]
    assert classify(issue, comments) == "blocked"
  
