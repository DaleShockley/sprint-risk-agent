"""Agent loop for the Sprint Risk Agent.

Wires Claude up with three tools (list_issues, get_issue_detail,
get_issue_comments) via the Anthropic tool-calling API. Claude decides
which issues to look at more closely and returns a structured risk
verdict for each one it flags.
"""

import json
from typing import Any

import anthropic

from src.github_client import get_issue_comments, get_issue_detail, list_issues
from src.schema import RiskVerdict

MODEL = "claude-sonnet-4-5"  # swap for whatever model your key has access to

SYSTEM_PROMPT = """You are a sprint risk analyst for a software team's GitHub repo.

Your job: review open issues and flag the ones that are quietly at risk,
using these categories:
- stale: no activity in 14+ days
- blocked: labeled or discussed as blocked, with no recent resolution
- unowned: no assignee
- at_risk_priority: high-priority label but little recent activity

For each issue you flag, ground the reason in specific data you pulled
(dates, labels, comment content) -- never guess. If an issue looks
healthy, don't report it at all.

Use the tools to gather real data before judging. Don't rely on the
issue title alone -- check labels, assignee, last update, and comments
when relevant.

When you're done, respond with ONLY a JSON array of verdicts, one
object per flagged issue, matching this shape:
[{"issue": <number>, "risk": "<category>", "confidence": "<low|medium|high>",
  "reason": "<short factual reason>", "recommended_action": "<short suggestion>"}]

No prose before or after the JSON.
"""

TOOLS = [
    {
        "name": "list_issues",
        "description": "List open issues in a repo (owner/name), lightweight fields only.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "e.g. 'octocat/hello-world'"},
                "limit": {"type": "integer", "default": 50},
            },
            "required": ["repo"],
        },
    },
    {
        "name": "get_issue_detail",
        "description": "Full detail for one issue: labels, assignee, milestone, timestamps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "issue_number": {"type": "integer"},
            },
            "required": ["repo", "issue_number"],
        },
    },
    {
        "name": "get_issue_comments",
        "description": "All comments on an issue, oldest first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "issue_number": {"type": "integer"},
            },
            "required": ["repo", "issue_number"],
        },
    },
]

def _dispatch(name: str, **kwargs: Any) -> Any:
    # Looked up at call time (not module load) so tests can patch the
    # individual functions (e.g. @patch("src.agent.get_issue_detail")).
    funcs = {
        "list_issues": list_issues,
        "get_issue_detail": get_issue_detail,
        "get_issue_comments": get_issue_comments,
    }
    return funcs[name](**kwargs)


def run_agent(repo: str, max_turns: int = 8) -> list[RiskVerdict]:
    """Runs the tool-calling loop and returns validated risk verdicts."""
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": f"Analyze open issues in {repo} for risk."}
    ]

    for _ in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            return _parse_verdicts(response)

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            try:
                result = _dispatch(block.name, **block.input)
            except Exception as exc:  # surface tool errors to the model instead of crashing
                result = {"error": str(exc)}
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(f"Agent didn't finish within {max_turns} turns.")


def _parse_verdicts(response: Any) -> list[RiskVerdict]:
    text = "".join(block.text for block in response.content if block.type == "text")
    raw = json.loads(text)
    return [RiskVerdict.model_validate(v) for v in raw]


if __name__ == "__main__":
    import sys

    repo_arg = sys.argv[1] if len(sys.argv) > 1 else "octocat/hello-world"
    for verdict in run_agent(repo_arg):
        print(f"#{verdict.issue} [{verdict.risk}/{verdict.confidence}] "
              f"{verdict.reason} -> {verdict.recommended_action}")
