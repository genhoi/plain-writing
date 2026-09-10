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
    strip_links,
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
# Обязательные разделы: для каждого — имя в сообщении и допустимые заголовки.
TASK_SECTIONS = (("Проблема", ("проблема",)), ("Что сделать", ("что сделать",)), ("Как проверить", ("как проверить",)))
MR_SECTIONS = (("Зачем", ("зачем",)), ("Что изменилось", ("что изменилось",)), ("Проверки", ("проверки", "как проверено", "как проверял", "как проверить")))


@dataclass(frozen=True)
class Finding:
    line: int
    rule: str
    message: str


@dataclass(frozen=True)
class Entry:
    """Строка списка слов: слово, замена и слова, перед которыми оно не считается нарушением."""

    word: str
    replacement: str = ""
    exceptions: tuple[str, ...] = ()


def read_list(name: str) -> list[Entry]:
    """Строки файла из каталога `lint/` без комментариев. Поля разделены табуляцией."""
    result = []
    for raw in (DATA_DIR / name).read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        fields = [f.strip() for f in raw.split("\t")]
        word = fields[0]
        replacement = fields[1] if len(fields) > 1 else ""
        exceptions = tuple(w.strip() for w in fields[2].split(",") if w.strip()) if len(fields) > 2 else ()
        result.append(Entry(word, replacement, exceptions))
    return result


def word_pattern(entry: Entry) -> re.Pattern[str]:
    """Слово из списка с окончанием до трёх букв: «минимальн» найдёт «минимальный»."""
    pattern = r"(?<![\w-])" + re.escape(entry.word) + r"[a-zа-яё]{0,3}(?![\w-])"
    if entry.exceptions:
        pattern += r"(?!\s+(?:" + "|".join(re.escape(w) for w in entry.exceptions) + r"))"
    return re.compile(pattern, re.IGNORECASE)


def _line_of_offset(paragraph: Paragraph, offset: int) -> int:
    """Строка абзаца, на которую попадает смещение в склеенном тексте."""
    position = 0
    for index, line in enumerate(paragraph.lines):
        position += len(line.strip()) + 1
        if offset < position:
            return paragraph.line + index
    return paragraph.line + len(paragraph.lines) - 1


def _text_units(doc: Document) -> list[Paragraph]:
    """Абзацы и заголовки как единицы текста для правил о словах."""
    units = list(doc.paragraphs)
    units.extend(Paragraph(line, [title]) for line, title in doc.headings)
    return sorted(units, key=lambda p: p.line)


def _find_words(doc: Document, entries: list[Entry], rule: str, label: str) -> list[Finding]:
    findings = []
    for unit in _text_units(doc):
        clean = strip_quoted(strip_code(unit.text))
        taken: list[tuple[int, int]] = []
        for entry in sorted(entries, key=lambda e: -len(e.word)):
            for m in word_pattern(entry).finditer(clean):
                if any(m.start() < end and start < m.end() for start, end in taken):
                    continue
                taken.append(m.span())
                hint = f", замена: {entry.replacement}" if entry.replacement else ""
                findings.append(Finding(_line_of_offset(unit, m.start()), rule, f"«{m.group(0)}»: {label}{hint}"))
    return findings


def check_sections(doc: Document) -> list[Finding]:
    """Разделы, о которых читатель не спрашивал: «Не входит» и подобные."""
    findings = []
    for line, title in doc.headings:
        if normalize_title(title) in FORBIDDEN_SECTIONS:
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
    return [re.compile(entry.word) for entry in read_list("codes.txt")]


def check_codes(doc: Document) -> list[Finding]:
    """Внутренние коды и ветки без расшифровки в том же абзаце."""
    findings = []
    patterns = _code_patterns()
    for unit in _text_units(doc):
        text = strip_urls(strip_links(unit.text))
        explained_spans: list[tuple[int, int]] = []
        found: list[tuple[int, str, str]] = []
        for m in _BRANCH.finditer(text):
            name = m.group(1) or m.group(2)
            if _explained(text, m.end()):
                explained_spans.append(m.span())
            else:
                found.append((m.start(), name, "ветка: читатель не знает, что в ней. Сказать, что это, или убрать"))
        explained_codes = set()
        for pattern in patterns:
            for m in pattern.finditer(text):
                inside_branch = any(start <= m.start() and m.end() <= end for start, end in explained_spans)
                if inside_branch or _explained(text, m.end()):
                    explained_codes.add(m.group(0))
                else:
                    found.append((m.start(), m.group(0), "внутренний код без расшифровки: объяснить в том же абзаце или убрать"))
        seen = set()
        for offset, code, message in sorted(found):
            if code in explained_codes or code in seen:
                continue
            seen.add(code)
            findings.append(Finding(_line_of_offset(unit, offset), "codes", f"«{code}»: {message}"))
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
    """Предложение длиннее 35 слов, абзац длиннее 8 предложений. Строка таблицы абзацем не считается."""
    findings = []
    for paragraph in doc.paragraphs:
        sentences = split_sentences(paragraph.text)
        for index, sentence in enumerate(sentences):
            words = count_words(sentence)
            if words > MAX_SENTENCE_WORDS:
                findings.append(Finding(_line_of_sentence(paragraph, index), "length", f"предложение из {words} слов, предел {MAX_SENTENCE_WORDS}: разбить"))
        if len(sentences) > MAX_PARAGRAPH_SENTENCES and not paragraph.table:
            findings.append(Finding(paragraph.line, "length", f"абзац из {len(sentences)} предложений, предел {MAX_PARAGRAPH_SENTENCES}: разбить"))
    return findings


_CODE_NAME = re.compile(r"`[^`]+`|\{\{[^}]+\}\}")


def _required_sections(doc: Document, required, rule: str, kind: str) -> list[Finding]:
    findings = []
    present = [normalize_title(title) for _, title in doc.headings]
    for name, variants in required:
        if not any(title.startswith(v) for title in present for v in variants):
            findings.append(Finding(1, rule, f"нет раздела «{name}», он обязателен для {kind}"))
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
