Sprint Risk Agent — Project Spec

The problem
Every TPM spends hours each week scanning a backlog for issues that are quietly going sideways: no update in two weeks, no assignee, marked "blocked" with no comment explaining why, high priority but zero recent activity. This project builds an agent that does that scan and writes the status digest a human would actually send.
Why this project, specifically
Most "AI portfolio projects" are a chatbot wrapped around an API call. This one isn't, and that's the point. It has to show three things a reviewer will actually check:

Real tool use. The agent calls functions to fetch data and decide what to look at next, it isn't just fed a wall of text in one prompt.
Structured, checkable output. Risk flags come back as typed data, not prose you have to trust.
Evaluation. There's a small labeled test set and a script that scores the agent against it, plus a comparison against a dumb baseline. This is the part almost nobody includes, and it's the part that signals you understand AI work has to be measured, not just demoed.
Architecture
Agent loop (Claude via the Anthropic SDK, tool-calling mode):

list_issues(repo, state="open") — pulls open issues via the GitHub REST API.
get_issue_detail(issue_number) — fetches labels, assignee, milestone, last-updated timestamp.
get_issue_comments(issue_number) — pulls comment thread, used to check for unresolved blockers.
Agent reasons over each issue and emits a structured verdict:

{
  "issue": 482,
  "risk": "blocked",
  "confidence": "high",
  "reason": "Labeled blocked 9 days ago, no comment since, no linked PR.",
  "recommended_action": "Ping assignee or reassign."
}

A formatting step turns the list of verdicts into a digest (markdown or Slack-style text) grouped by risk type.

Risk categories to start with: stale (no activity in N days), blocked (label or comment language, no resolution), unowned (no assignee), at_risk_priority (high priority, low recent activity).
Tech stack
Python 3.11+
Anthropic SDK for the agent loop and tool calling
requests (or PyGithub) for the GitHub REST API
pydantic for the structured verdict schema
pytest for unit tests on the tools and the formatting layer
A flat JSON file as the eval set (20-30 hand-labeled issues with the "correct" risk verdict)
GitHub Actions for CI (lint + tests on every push)
Eval harness (the part that matters most)
Build a labeled set: pull ~25 real closed/old issues from a public repo, hand-label what risk category each should have gotten.
Score the agent's verdicts against your labels: accuracy per category, plus a confusion matrix if you want to go further.
Build one naive baseline (e.g., a rule-based script: flag anything untouched for 14+ days as stale, anything unassigned as unowned) and score it the same way.
Report both numbers side by side in the README. The agent doesn't need to crush the baseline — an honest table showing where it's better and where it isn't is more credible than a claim that it's perfect.
Repo structure
sprint-risk-agent/
├── README.md
├── src/
│   ├── github_client.py      # tool functions: list_issues, get_issue_detail, get_issue_comments
│   ├── agent.py               # the tool-calling loop + prompt
│   ├── schema.py               # pydantic models for verdicts
│   └── digest.py                # formats verdicts into a readable report
├── eval/
│   ├── labeled_issues.json
│   ├── baseline.py
│   └── score.py
├── tests/
│   └── test_github_client.py, test_digest.py, ...
├── .github/workflows/ci.yml
└── requirements.txt
Milestones
Data layer — GitHub client + tool functions, tested against a real public repo.
Agent loop — tool-calling wired up, produces structured verdicts for a handful of issues.
Digest formatting — verdicts become a readable report (this is the "demo-able" milestone).
Eval harness — labeled set, scoring script, baseline comparison.
Polish — README with architecture diagram, sample digest output, eval results table, a short GIF or screenshot, CI badge.
README outline (for the finished repo)
One-paragraph problem statement (the pain, not the tech)
Sample output (a real digest, so a reviewer sees the payoff in 10 seconds)
Architecture diagram (agent loop + tools)
Eval results table (agent vs. baseline)
How to run it locally
What you'd build next (scope this honestly, it reads as self-aware rather than incomplete)
Stretch goals (only after the above works)
Slack webhook output instead of/alongside markdown
Scheduled runs (cron or GitHub Action) so it posts a digest automatically
Multi-repo support
A second baseline: plain zero-shot prompting (no tools, just a big text dump) scored against the tool-using agent, to make the "why tool use matters" case explicit

# sprint-risk-agent
Sprint Risk Agent
