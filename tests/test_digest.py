from src.digest import format_digest
from src.schema import RiskVerdict


def _verdict(**overrides):
    base = dict(issue=1, risk="stale", confidence="medium", reason="r", recommended_action="a")
    base.update(overrides)
    return RiskVerdict(**base)


def test_format_digest_empty():
    output = format_digest("octocat/hello-world", [])
    assert "No issues flagged" in output


def test_format_digest_groups_by_category_in_severity_order():
    verdicts = [
        _verdict(issue=1, risk="stale"),
        _verdict(issue=2, risk="blocked"),
    ]
    output = format_digest("octocat/hello-world", verdicts)
    # blocked is more severe than stale, should be listed first
    assert output.index("Blocked") < output.index("Stale")
    assert "#1" in output
    assert "#2" in output


def test_format_digest_includes_titles_when_provided():
    verdicts = [_verdict(issue=5, risk="unowned")]
    output = format_digest(
        "octocat/hello-world", verdicts, issue_titles={5: "Fix login bug"}
    )
    assert "#5 — Fix login bug" in output
