
Github client · PY
"""GitHub API client — tool functions for the Sprint Risk Agent.
 
Each function here is a "tool" the agent will call later. They return
plain dicts/lists so they're easy to pass back to the agent as tool
results, and easy to unit test without touching the network.
"""
 
import os
import time
from typing import Any
 
import requests
 
GITHUB_API = "https://api.github.com"
 
 
class GitHubClientError(Exception):
    """Raised when the GitHub API returns something we can't recover from."""
 
 
def _headers() -> dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers
 
 
def _get(url: str, params: dict[str, Any] | None = None) -> requests.Response:
    resp = requests.get(url, headers=_headers(), params=params, timeout=15)
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
        wait = max(reset - int(time.time()), 1)
        raise GitHubClientError(f"Rate limited. Resets in {wait}s.")
    if resp.status_code == 404:
        raise GitHubClientError(f"Not found: {url}")
    resp.raise_for_status()
    return resp
 
 
def list_issues(repo: str, state: str = "open", limit: int = 50) -> list[dict[str, Any]]:
    """List issues for `repo` (format "owner/name"). Excludes pull requests.
 
    Returns a lightweight list: number, title, labels, assignee, milestone, updated_at.
    """
    issues: list[dict[str, Any]] = []
    page = 1
    while len(issues) < limit:
        resp = _get(
            f"{GITHUB_API}/repos/{repo}/issues",
            params={"state": state, "per_page": 100, "page": page},
        )
        batch = resp.json()
        if not batch:
            break
        for item in batch:
            if "pull_request" in item:  # GitHub's issues endpoint includes PRs; skip them
                continue
            issues.append(
                {
                    "number": item["number"],
                    "title": item["title"],
                    "labels": [label["name"] for label in item["labels"]],
                    "assignee": item["assignee"]["login"] if item["assignee"] else None,
                    "milestone": item["milestone"]["title"] if item["milestone"] else None,
                    "updated_at": item["updated_at"],
                }
            )
            if len(issues) >= limit:
                break
        page += 1
    return issues
 
 
def get_issue_detail(repo: str, issue_number: int) -> dict[str, Any]:
    """Full detail for a single issue."""
    item = _get(f"{GITHUB_API}/repos/{repo}/issues/{issue_number}").json()
    return {
        "number": item["number"],
        "title": item["title"],
        "body": item.get("body") or "",
        "state": item["state"],
        "labels": [label["name"] for label in item["labels"]],
        "assignee": item["assignee"]["login"] if item["assignee"] else None,
        "milestone": item["milestone"]["title"] if item["milestone"] else None,
        "created_at": item["created_at"],
        "updated_at": item["updated_at"],
        "comments_count": item["comments"],
    }
 
 
def get_issue_comments(repo: str, issue_number: int) -> list[dict[str, Any]]:
    """All comments on an issue, oldest first."""
    resp = _get(f"{GITHUB_API}/repos/{repo}/issues/{issue_number}/comments")
    return [
        {
            "author": comment["user"]["login"],
            "body": comment["body"],
            "created_at": comment["created_at"],
        }
        for comment in resp.json()
    ]
 


Unable to open file. (×2)
