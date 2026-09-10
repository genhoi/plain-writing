"""Правила проверки. Каждое правило — функция `check_*(doc) -> list[Finding]`."""

import re
from dataclasses import dataclass
from pathlib import Path

from .document import (
    Document,
    Paragraph,
    count_words,
    normalize_title,
    split_sentences,
    strip_code,
    strip_quoted,
    strip_urls,
)

DATA_DIR = Path(__file__).parent
MAX_SENTENCE_WORDS = 35
MAX_PARAGRAPH_SENTENCES = 8

FORBIDDEN_SECTIONS = (
    "не входит",
    "не вошло",
    "что не входит",
    "что не вошло",
    "что осталось за бортом",
    "за бортом",
    "что не сделано",
    "не сделано",
    "out of scope",
    "not in scope",
    "not included",
    "not done",
    "left out",
    "what's left",
)
TASK_SECTIONS = ("проблема", "что сделать", "как проверить")
MR_SECTIONS = ("зачем", "что изменилось", "проверки")


@dataclass(frozen=True)
class Finding:
    line: int
    rule: str
    message: str


def read_list(name: str) -> list[tuple[str, str]]:
    """Строки файла из каталога `lint/` без комментариев: (слово, замена или пустая строка)."""
    result = []
    for raw in (DATA_DIR / name).read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        word, _, replacement = raw.partition("\t")
        result.append((word.strip(), replacement.strip()))
    return result


def word_pattern(word: str) -> re.Pattern[str]:
    """Слово из списка с окончанием до трёх букв: «минимальн» найдёт «минимальный»."""
    return re.compile(r"(?<![\w-])" + re.escape(word) + r"[a-zа-яё]{0,3}(?![\w-])", re.IGNORECASE)


def _find_words(doc: Document, words: list[tuple[str, str]], rule: str, label: str) -> list[Finding]:
    findings = []
    for number, line in doc.prose_lines():
        clean = strip_quoted(strip_code(line))
        taken: list[tuple[int, int]] = []
        for word, replacement in sorted(words, key=lambda pair: -len(pair[0])):
            m = word_pattern(word).search(clean)
            if not m or any(m.start() < end and start < m.end() for start, end in taken):
                continue
            taken.append(m.span())
            hint = f", замена: {replacement}" if replacement else ""
            findings.append(Finding(number, rule, f"«{m.group(0)}»: {label}{hint}"))
    return findings


def check_sections(doc: Document) -> list[Finding]:
    """Разделы, о которых читатель не спрашивал: «Не входит» и подобные."""
    findings = []
    for line, title in doc.headings:
        name = normalize_title(title)
        if any(name.startswith(bad) for bad in FORBIDDEN_SECTIONS):
            findings.append(Finding(line, "sections", f"раздел «{title.strip()}»: убрать. Реальное ограничение идёт одним абзацем с причиной"))
    return findings


def check_jargon(doc: Document) -> list[Finding]:
    """Жаргон и кальки из `lint/jargon.txt`."""
    return _find_words(doc, read_list("jargon.txt"), "jargon", "жаргон")


def check_self_praise(doc: Document) -> list[Finding]:
    """Самооценка из `lint/self-praise.txt`."""
    return _find_words(doc, read_list("self-praise.txt"), "self-praise", "самооценка, пусть читатель оценит сам")


_EXPLANATION = re.compile(r"^(?:`|\}\})?\s*(?:[(:—–]|-\s|это\b|то есть\b)")
_BRANCH = re.compile(
    r"(?:\bветк[а-яё]{0,3}|\bbranch(?:es)?)\s+(`[^`]+`|\{\{[^}]+\}\}|[\w./-]*[-/][\w./-]*)"
    r"|(`[^`]+`)\s+branch\b",
    re.IGNORECASE,
)


def _explained(text: str, end: int) -> bool:
    return bool(_EXPLANATION.match(text[end:]))


def _code_patterns() -> list[re.Pattern[str]]:
    return [re.compile(word) for word, _ in read_list("codes.txt")]


def check_codes(doc: Document) -> list[Finding]:
    """Внутренние коды и ветки без расшифровки в том же абзаце."""
    findings = []
    patterns = _code_patterns()
    for paragraph in doc.paragraphs:
        text = strip_urls(paragraph.text)
        explained_codes = set()
        found: list[tuple[str, str]] = []
        for pattern in patterns:
            for m in pattern.finditer(text):
                if _explained(text, m.end()):
                    explained_codes.add(m.group(0))
                else:
                    found.append((m.group(0), "внутренний код без расшифровки: объяснить в том же абзаце или убрать"))
        for m in _BRANCH.finditer(text):
            name = m.group(1) or m.group(2)
            if not _explained(text, m.end()):
                found.append((name, "ветка: читатель не знает, что в ней. Сказать, что это, или убрать"))
        seen = set()
        for code, message in found:
            if code in explained_codes or code in seen:
                continue
            seen.add(code)
            findings.append(Finding(paragraph.line, "codes", f"«{code}»: {message}"))
    return findings


def _line_of_sentence(paragraph: Paragraph, index: int) -> int:
    """Строка, на которой начинается предложение с данным номером внутри абзаца."""
    count = 0
    for offset, line in enumerate(paragraph.lines):
        count += len(split_sentences(line))
        if count > index:
            return paragraph.line + offset
    return paragraph.line


def check_length(doc: Document) -> list[Finding]:
    """Предложение длиннее 35 слов, абзац длиннее 8 предложений."""
    findings = []
    for paragraph in doc.paragraphs:
        sentences = split_sentences(paragraph.text)
        for index, sentence in enumerate(sentences):
            words = count_words(sentence)
            if words > MAX_SENTENCE_WORDS:
                findings.append(Finding(_line_of_sentence(paragraph, index), "length", f"предложение из {words} слов, предел {MAX_SENTENCE_WORDS}: разбить"))
        if len(sentences) > MAX_PARAGRAPH_SENTENCES:
            findings.append(Finding(paragraph.line, "length", f"абзац из {len(sentences)} предложений, предел {MAX_PARAGRAPH_SENTENCES}: разбить"))
    return findings


_CODE_NAME = re.compile(r"`[^`]+`|\{\{[^}]+\}\}")


def _required_sections(doc: Document, required: tuple[str, ...], rule: str, kind: str) -> list[Finding]:
    findings = []
    present = [normalize_title(title) for _, title in doc.headings]
    for name in required:
        if not any(title.startswith(name) for title in present):
            findings.append(Finding(1, rule, f"нет раздела «{name.capitalize()}», он обязателен для {kind}"))
    return findings


def check_task_form(doc: Document) -> list[Finding]:
    """Форма задачи: разделы «Проблема», «Что сделать», «Как проверить»; в «Что сделать» нумерованные пункты с именем кода."""
    findings = _required_sections(doc, TASK_SECTIONS, "task-form", "задачи")
    for section in doc.sections:
        if not normalize_title(section.title).startswith("что сделать"):
            continue
        items = [p for p in section.paragraphs if p.numbered]
        if not items:
            findings.append(Finding(section.line, "task-form", "в «Что сделать» нет нумерованного списка"))
        for item in items:
            if not _CODE_NAME.search(item.text):
                findings.append(Finding(item.line, "task-form", "пункт не называет класс, таблицу или метод в обратных кавычках"))
    return findings


def check_mr_form(doc: Document) -> list[Finding]:
    """Форма описания MR: разделы «Зачем», «Что изменилось», «Проверки»."""
    return _required_sections(doc, MR_SECTIONS, "mr-form", "описания MR")


ALWAYS = (check_sections, check_jargon, check_codes, check_self_praise, check_length)
BY_KIND = {"task": (check_task_form,), "mr": (check_mr_form,), "text": ()}
