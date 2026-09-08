from unittest.mock import MagicMock, patch

from src.github_client import get_issue_comments, get_issue_detail, list_issues


def _mock_response(json_data, status=200, headers=None):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data
    resp.headers = headers or {}
    resp.text = ""
    resp.raise_for_status = MagicMock()
    return resp


@patch("src.github_client.requests.get")
def test_list_issues_skips_pull_requests(mock_get):
    mock_get.side_effect = [
        _mock_response(
            [
                {
                    "number": 1,
                    "title": "Real issue",
                    "labels": [],
                    "assignee": None,
                    "milestone": None,
                    "updated_at": "2026-01-01T00:00:00Z",
                },
                {
                    "number": 2,
                    "title": "A PR",
                    "labels": [],
                    "assignee": None,
                    "milestone": None,
                    "updated_at": "2026-01-02T00:00:00Z",
                    "pull_request": {},
                },
            ]
        ),
        _mock_response([]),
    ]
    issues = list_issues("octocat/hello-world")
    assert len(issues) == 1
    assert issues[0]["number"] == 1


@patch("src.github_client.requests.get")
def test_get_issue_detail_shapes_fields(mock_get):
    mock_get.return_value = _mock_response(
        {
            "number": 42,
            "title": "Something broke",
            "body": "details",
            "state": "open",
            "labels": [{"name": "blocked"}],
            "assignee": {"login": "dale"},
            "milestone": {"title": "v1"},
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-05T00:00:00Z",
            "comments": 3,
        }
    )
    detail = get_issue_detail("octocat/hello-world", 42)
    assert detail["assignee"] == "dale"
    assert detail["labels"] == ["blocked"]
    assert detail["comments_count"] == 3


@patch("src.github_client.requests.get")
def test_get_issue_comments(mock_get):
    mock_get.return_value = _mock_response(
        [
            {
                "user": {"login": "dale"},
                "body": "still blocked",
                "created_at": "2026-01-06T00:00:00Z",
            }
        ]
    )
    comments = get_issue_comments("octocat/hello-world", 42)
    assert comments[0]["author"] == "dale"
    assert comments[0]["body"] == "still blocked"
