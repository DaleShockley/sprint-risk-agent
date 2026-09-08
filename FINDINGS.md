# Findings

## What I built

Sprint Risk Agent scans open GitHub issues and flags the ones quietly going sideways: stale, blocked, unowned, or high priority but going cold. I built it in five stages: a GitHub API client, an agent loop that gives Claude tool access to that client, a schema that forces the model's output into a checkable structure, a digest formatter, and an eval harness that scores the agent against a hand-labeled set of issues and a rule-based baseline.

I used Claude the whole way through, working step by step rather than asking for the whole repo at once. Each piece got built, tested, and verified before moving to the next.

## What I learned

The biggest shift for me was realizing that "AI agent" isn't just a chatbot with extra steps. The agent here doesn't get handed a wall of issue data and asked to guess. It calls specific functions (list issues, get one issue's detail, get its comments) and decides what to look at based on what it finds. That's the actual mechanism behind what people mean when they say "tool use" or "agentic," and it's a lot more concrete than I expected going in.

The second thing was the eval harness, and honestly it's the part I almost skipped. It felt like extra work for a portfolio project nobody would scrutinize that closely. But building a rule-based baseline and scoring it against the same labeled issues as the agent turned out to be the most interesting part of the whole thing. The baseline hit 75% by just checking labels and dates. It missed two cases on purpose built into the eval set: an issue still tagged "blocked" that was actually resolved in the comments, and an issue with an assignee who'd said in a comment they were out for three weeks. Those are exactly the cases where reading the comment thread matters, and they're the clearest argument I have for why the agent's tool access earns its place instead of just being a rule engine wearing an LLM costume.

## Debugging note

Most of the actual friction wasn't in the code, it was in getting files onto GitHub correctly through the web UI. Twice, a file's real content got replaced with placeholder text that matched the filename (requirements.txt held the literal text "Requirements · TXT" instead of the package list, and the same thing happened to github\_client.py). Neither showed up until CI actually tried to install dependencies or import the file, so the fix was always a full-content replace rather than a small edit.

The other one was more of a real gotcha: the CI workflow ran `pytest tests/ -v` directly, which doesn't add the repo root to Python's import path. Locally I'd been running `python -m pytest`, which does add it, so everything worked on my end and broke in CI. The fix was one word (`python -m pytest` instead of `pytest`), but it's a good example of why "works on my machine" and "works in CI" aren't the same claim, and why testing the actual pipeline matters as much as testing the code.  
