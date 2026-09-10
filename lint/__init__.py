"""Проверка текста для людей по правилам `skill/SKILL.md`.

    from lint import check
    findings = check(text, kind="task")
"""

from .document import parse
from .rules import ALWAYS, BY_KIND, Finding

KINDS = tuple(BY_KIND)


def check(text: str, kind: str = "text") -> list[Finding]:
    """Замечания к тексту, отсортированные по строке. `kind`: text, task или mr."""
    doc = parse(text)
    findings: list[Finding] = []
    for rule in ALWAYS + BY_KIND[kind]:
        findings.extend(rule(doc))
    return sorted(findings, key=lambda f: (f.line, f.rule, f.message))


__all__ = ["Finding", "KINDS", "check"]
