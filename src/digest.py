"""Formats risk verdicts into a human-readable digest.

Deliberately separate from the agent loop -- this is a pure function
over data, so it's easy to test and easy to swap output formats
(markdown today, Slack blocks later) without touching the agent.
"""

from collections import defaultdict
from datetime import datetime, timezone

from src.schema import RiskVerdict

_CATEGORY_ORDER = ["blocked", "at_risk_priority", "stale", "unowned"]
_CATEGORY_LABELS = {
    "blocked": "Blocked",
    "at_risk_priority": "High priority, going quiet",
    "stale": "Stale",
    "unowned": "Unowned",
}


def format_digest(
    repo: str,
    verdicts: list[RiskVerdict],
    issue_titles: dict[int, str] | None = None,
) -> str:
    """Builds a markdown digest grouped by risk category, most severe first."""
    issue_titles = issue_titles or {}

    if not verdicts:
        return f"# Sprint Risk Digest — {repo}\n\nNo issues flagged. Backlog looks healthy.\n"

    grouped: dict[str, list[RiskVerdict]] = defaultdict(list)
    for verdict in verdicts:
        grouped[verdict.risk].append(verdict)

    lines = [
        f"# Sprint Risk Digest — {repo}",
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        f"**{len(verdicts)} issue(s) flagged.**",
        "",
    ]

    for category in _CATEGORY_ORDER:
        items = grouped.get(category, [])
        if not items:
            continue
        lines.append(f"## {_CATEGORY_LABELS[category]} ({len(items)})")
        lines.append("")
        for verdict in sorted(items, key=lambda v: v.issue):
            title = issue_titles.get(verdict.issue)
            heading = f"#{verdict.issue} — {title}" if title else f"#{verdict.issue}"
            lines.append(f"- **{heading}** _(confidence: {verdict.confidence})_")
            lines.append(f"  {verdict.reason}")
            lines.append(f"  → {verdict.recommended_action}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
