"""Примеры из skill/reference/: «до» даёт замечания, «после» проходит."""

from lint import check
from tests.conftest import rules


def test_task_after_is_clean(reference):
    assert check((reference / "task-after.md").read_text(encoding="utf-8"), kind="task") == []


def test_task_before_breaks_at_least_three_rules(reference):
    findings = check((reference / "task-before.md").read_text(encoding="utf-8"), kind="task")
    assert len(rules(findings)) >= 3
    assert {"sections", "jargon", "codes", "task-form"} <= rules(findings)


def test_mr_after_is_clean(reference):
    assert check((reference / "mr-after.md").read_text(encoding="utf-8"), kind="mr") == []


def test_mr_before_breaks_at_least_three_rules(reference):
    findings = check((reference / "mr-before.md").read_text(encoding="utf-8"), kind="mr")
    assert len(rules(findings)) >= 3
    assert {"sections", "jargon", "self-praise", "codes", "mr-form"} <= rules(findings)
