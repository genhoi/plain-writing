"""Правила проверки. Каждое правило — функция `check_*(doc) -> list[Finding]`."""

import re
from dataclasses import dataclass
from pathlib import Path

from .document import (
    CODE_SPAN,
    JIRA_LINK,
    MD_LINK,
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


# Строка-ссылка на задачи: «Closes NP-12», «Задача: NP-12, NP-13».
_TRAILER = re.compile(
    r"^\s*(?:[-*]\s+)?(?:closes|fixes|resolves|related to|relates to|refs?|see also|part of"
    r"|задач[аи]|связан[а-яё]*(?: с)?|см\.)\s*:?\s+(.+)$",
    re.IGNORECASE,
)
_PARENTHESES = re.compile(r"\(([^()\n]{1,80})\)")
_REFERENCE_FILLER = re.compile(r"[\s,;]+|\b(?:и|and)\b")


def _explained(text: str, end: int) -> bool:
    return bool(_EXPLANATION.match(text[end:]))


def _code_patterns() -> list[re.Pattern[str]]:
    return [re.compile(entry.word) for entry in read_list("codes.txt")]


def _mask(pattern: re.Pattern[str], text: str, keep=lambda m: False) -> str:
    """Совпадения заменены на «X» той же длины, чтобы смещения не сдвигались."""
    return pattern.sub(lambda m: m.group(0) if keep(m) else "X" * len(m.group(0)), text)


def _reference_spans(text: str, patterns: list[re.Pattern[str]]) -> list[tuple[int, int]]:
    """Места, где коды стоят указателем: в скобках после утверждения или в строке «Closes NP-12».

    Указатель — это коды через запятую и не больше двух слов-подписей: «(NP-12)»,
    «(задача NP-12)», «(sms-gateway !730)». Предложение понятно и без него.
    """
    spans = []
    candidates = [(m.start(1), m.group(1)) for m in _PARENTHESES.finditer(text)]
    trailer = _TRAILER.match(text)
    if trailer:
        candidates.append((trailer.start(1), trailer.group(1)))
    for start, inner in candidates:
        rest = inner
        found = False
        for pattern in patterns:
            rest, n = pattern.subn(" ", rest)
            found = found or n > 0
        if found and len(_REFERENCE_FILLER.sub(" ", rest).split()) <= 2:
            spans.append((start, start + len(inner)))
    return spans


def check_codes(doc: Document) -> list[Finding]:
    """Внутренние коды и ветки без расшифровки в том же абзаце.

    Код, по которому можно перейти (ссылка), код-указатель (в скобках или в строке
    «Closes NP-12») и код внутри имени файла или пути не считаются.
    """
    findings = []
    patterns = _code_patterns()
    for unit in _text_units(doc):
        text = strip_urls(_mask(JIRA_LINK, _mask(MD_LINK, unit.text)))
        references = _reference_spans(text, patterns)
        # Код внутри пути или имени в обратных кавычках — часть имени, а не код: `docs/NP-12/plan.md`.
        code_text = _mask(CODE_SPAN, text, keep=lambda m: "/" not in m.group(0))
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
            for m in pattern.finditer(code_text):
                if any(start <= m.start() and m.end() <= end for start, end in references):
                    continue
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


def _required_sections(doc: Document, required, rule: str, kind: str) -> list[Finding]:
    findings = []
    present = [normalize_title(title) for _, title in doc.headings]
    for name, variants in required:
        if not any(title.startswith(v) for title in present for v in variants):
            findings.append(Finding(1, rule, f"нет раздела «{name}», он обязателен для {kind}"))
    return findings


# Что в «Как проверить» читается как код, а не как шаг на стенде: тесты, классы, методы.
_TESTS_WORD = re.compile(r"(?<![\w-])(?:юнит|unit)(?![\w])|(?<!\w)тест[а-яё]{0,3}(?![\w-])", re.IGNORECASE)
_CLASS_NAME = re.compile(r"[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+|::|\w\(\)")


def _code_in_check(paragraph: Paragraph) -> str | None:
    """Первое имя класса, метода или упоминание тестов в пункте «Как проверить»."""
    for span in CODE_SPAN.finditer(paragraph.text):
        if _CLASS_NAME.search(span.group(0)):
            return span.group(0)
    m = _TESTS_WORD.search(strip_quoted(strip_code(paragraph.text)))
    return m.group(0) if m else None


def check_task_form(doc: Document) -> list[Finding]:
    """Форма задачи: разделы «Проблема», «Что сделать», «Как проверить».

    В «Что сделать» нумерованные пункты. В «Как проверить» шаги для тестировщика, без классов,
    методов и тестов: тесты описываются в MR.
    """
    findings = _required_sections(doc, TASK_SECTIONS, "task-form", "задачи")
    for section in doc.sections:
        title = normalize_title(section.title)
        if title.startswith("как проверить"):
            for paragraph in section.paragraphs:
                name = _code_in_check(paragraph)
                if name:
                    findings.append(Finding(paragraph.line, "task-form", f"«{name}» в «Как проверить»: раздел читает тестировщик, нужны шаги на стенде и ожидаемый результат, тесты — в описание MR"))
            continue
        if not title.startswith("что сделать"):
            continue
        items = [p for p in section.paragraphs if p.numbered]
        if not items:
            findings.append(Finding(section.line, "task-form", "в «Что сделать» нет нумерованного списка"))
    return findings


def check_mr_form(doc: Document) -> list[Finding]:
    """Форма описания MR: разделы «Зачем», «Что изменилось», «Проверки»."""
    return _required_sections(doc, MR_SECTIONS, "mr-form", "описания MR")


ALWAYS = (check_sections, check_jargon, check_codes, check_self_praise, check_length)
BY_KIND = {"task": (check_task_form,), "mr": (check_mr_form,), "text": ()}
