"""Tests for the agent loop, using a mocked Anthropic client.

No API key required -- these check that we parse and validate the
model's response correctly, and that a tool-use turn gets handled
before the final answer.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.agent import run_agent


def _text_response(payload):
    return SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text=json.dumps(payload))],
    )


def _tool_use_response(name, tool_input, tool_id="call_1"):
    return SimpleNamespace(
        stop_reason="tool_use",
        content=[SimpleNamespace(type="tool_use", name=name, input=tool_input, id=tool_id)],
    )


@patch("src.agent.anthropic.Anthropic")
def test_run_agent_parses_final_verdicts(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _text_response(
        [
            {
                "issue": 7,
                "risk": "stale",
                "confidence": "high",
                "reason": "No activity in 20 days.",
                "recommended_action": "Ping assignee.",
            }
        ]
    )

    verdicts = run_agent("octocat/hello-world")

    assert len(verdicts) == 1
    assert verdicts[0].issue == 7
    assert verdicts[0].risk == "stale"


@patch("src.agent.get_issue_detail")
@patch("src.agent.anthropic.Anthropic")
def test_run_agent_executes_tool_call_before_finishing(mock_anthropic_cls, mock_get_detail):
    mock_get_detail.return_value = {"number": 3, "labels": ["blocked"]}
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.side_effect = [
        _tool_use_response("get_issue_detail", {"repo": "octocat/hello-world", "issue_number": 3}),
        _text_response(
            [
                {
                    "issue": 3,
                    "risk": "blocked",
                    "confidence": "medium",
                    "reason": "Labeled blocked.",
                    "recommended_action": "Follow up.",
                }
            ]
        ),
    ]

    verdicts = run_agent("octocat/hello-world")

    mock_get_detail.assert_called_once_with(repo="octocat/hello-world", issue_number=3)
    assert verdicts[0].risk == "blocked"
