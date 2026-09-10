"""Разбор текста на заголовки, абзацы и предложения.

Поддерживает две разметки: Markdown (`## Заголовок`, `1. пункт`, `` `имя` ``)
и Jira (`h2. Заголовок`, `# пункт`, `{{имя}}`). Разметка считается Jira, если вне
блоков кода есть хотя бы один заголовок вида `h2.`.
"""

import re
from dataclasses import dataclass, field

MD_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
JIRA_HEADING = re.compile(r"^h([1-6])\.\s+(.+?)\s*$")
BOLD_LINE = re.compile(r"^\s*(?:\*\*(.+?)\*\*|\*(\S.*?\S)\*|__(.+?)__)\s*:?\s*$")
BOLD_LABEL = re.compile(r"^\s*(?:\*\*(.+?)\*\*|__(.+?)__)\s*:\s+(\S.*)$")
SETEXT_UNDERLINE = re.compile(r"^\s{0,3}(=+|-+)\s*$")
BULLET_ITEM = re.compile(r"^\s*(?:[-*+•]|#+)\s+")
NUMBERED_ITEM = re.compile(r"^\s*(?:\d+[.)]|#+)\s+")
CODE_SPAN = re.compile(r"`[^`\n]+`|\{\{[^}\n]+\}\}")
URL = re.compile(r"https?://\S+")
MD_LINK = re.compile(r"\[([^\]\n]+)\]\([^)\n]*\)")
JIRA_LINK = re.compile(r"\[([^\]|\n]+)\|[^\]\n]*\]")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
JIRA_BLOCK = re.compile(r"^\s*\{(code|noformat)(?::[^}]*)?\}")
HTML_LINE = re.compile(r"^\s*<[a-zA-Z/][^>]*>(?:.*>)?\s*$")
TABLE_ROW = re.compile(r"^\s*\|")
QUOTED = re.compile(r"«[^«»\n]{1,40}»|\"[^\"\n]{1,40}\"|„[^“”„\n]{1,40}[“”]|“[^“”\n]{1,40}”")


@dataclass
class Paragraph:
    """Абзац или один пункт списка: номер первой строки и строки текста."""

    line: int
    lines: list[str]
    numbered: bool = False
    table: bool = False

    @property
    def text(self) -> str:
        return " ".join(s.strip() for s in self.lines)


@dataclass
class Section:
    """Раздел от заголовка до следующего заголовка того же или более высокого уровня.

    Абзацы вложенных подразделов входят в раздел.
    """

    title: str
    line: int
    level: int = 0
    paragraphs: list[Paragraph] = field(default_factory=list)


@dataclass
class Document:
    lines: list[str]
    jira: bool
    headings: list[tuple[int, str]]
    paragraphs: list[Paragraph]
    sections: list[Section]

    def prose_lines(self) -> list[tuple[int, str]]:
        """Строки абзацев и заголовков с номерами: без блоков кода и разметки."""
        result = [(p.line + i, s) for p in self.paragraphs for i, s in enumerate(p.lines)]
        result.extend((line, title) for line, title in self.headings)
        return sorted(result)


def normalize_title(title: str) -> str:
    """Заголовок в нижнем регистре без разметки и знаков препинания по краям."""
    title = re.sub(r"[*_`]", "", title)
    return title.strip(" :.!—-").lower()


def strip_code(text: str) -> str:
    """Имена кода в кавычках заменены на слово X, чтобы не мешать правилам."""
    return CODE_SPAN.sub("X", text)


def strip_urls(text: str) -> str:
    return URL.sub("X", text)


def strip_links(text: str) -> str:
    """Ссылки Markdown и Jira заменены на их видимый текст."""
    return JIRA_LINK.sub(r"\1", MD_LINK.sub(r"\1", text))


def strip_quoted(text: str) -> str:
    """Короткие слова в кавычках — упоминание, а не употребление: их правила о словах пропускают."""
    return QUOTED.sub("X", text)


def heading_of(line: str, jira: bool) -> tuple[int, str] | None:
    """Уровень и текст заголовка, если строка им является, иначе None."""
    m = JIRA_HEADING.match(line)
    if m:
        return int(m.group(1)), m.group(2)
    if not jira:
        m = MD_HEADING.match(line)
        if m:
            return len(m.group(1)), m.group(2)
    m = BOLD_LINE.match(line)
    if m:
        return 9, next(g for g in m.groups() if g)
    return None


def _is_item(line: str, jira: bool) -> tuple[bool, bool]:
    """Является ли строка пунктом списка и нумерован ли он."""
    if not jira and line.lstrip().startswith("#"):
        return False, False
    if NUMBERED_ITEM.match(line):
        return True, True
    return bool(BULLET_ITEM.match(line)), False


_ABBREVIATIONS = re.compile(
    r"\b(т\.е|т\.д|т\.п|т\.к|напр|см|стр|рис|табл|др|пр|руб|коп|тыс|млн|млрд|гг|г|ул|им|e\.g|i\.e|etc|vs|т)\.",
    re.IGNORECASE,
)
_SENTENCE_END = re.compile(r"(?<=[.!?])[»\"”)]*\s+(?=[^a-zа-яё\s])|(?<=;)\s+|(?<=[.!?])[»\"”)]*$|\s*\|\s*")


def split_sentences(text: str) -> list[str]:
    """Предложения абзаца. Точка после сокращения и перед строчной буквой границей не считается."""
    text = strip_code(text)
    text = _ABBREVIATIONS.sub(lambda m: m.group(0).replace(".", "·"), text)
    parts = [p.strip() for p in _SENTENCE_END.split(text)]
    return [p for p in parts if p]


_WORD = re.compile(r"[\w'’-]*[^\W_][\w'’-]*")


def count_words(sentence: str) -> int:
    return len(_WORD.findall(sentence))


def _code_block_end(line: str, opener: str | None) -> tuple[bool, str | None]:
    """Открывает или закрывает ли строка блок кода. Возвращает (граница, новый открывающий маркер)."""
    m = FENCE.match(line)
    if m:
        marker = m.group(1)
        if opener is None:
            return True, marker
        if marker[0] == opener[0] and len(marker) >= len(opener) and not line.strip()[len(marker):].strip():
            return True, None
        return False, opener
    if JIRA_BLOCK.match(line):
        return True, (None if opener == "{}" else "{}")
    return False, opener


def _prose_source(lines: list[str]) -> list[str | None]:
    """Строки вне блоков кода; внутри блока — None."""
    result: list[str | None] = []
    opener: str | None = None
    for line in lines:
        boundary, opener = _code_block_end(line, opener)
        if boundary:
            result.append(None)
            continue
        result.append(None if opener is not None else line)
    return result


def parse(text: str) -> Document:
    lines = text.lstrip("\ufeff").splitlines()
    prose = _prose_source(lines)
    jira = any(s is not None and JIRA_HEADING.match(s) for s in prose)
    headings: list[tuple[int, str]] = []
    paragraphs: list[Paragraph] = []
    root = Section("", 0)
    sections: list[Section] = [root]
    open_sections: list[Section] = [root]
    current: Paragraph | None = None

    def close() -> None:
        nonlocal current
        if current is not None:
            paragraphs.append(current)
            for section in open_sections:
                section.paragraphs.append(current)
            current = None

    def add_heading(number: int, level: int, title: str) -> None:
        close()
        headings.append((number, title))
        section = Section(title, number, level)
        sections.append(section)
        while open_sections[-1].level >= level and len(open_sections) > 1:
            open_sections.pop()
        open_sections.append(section)

    for number, line in enumerate(lines, start=1):
        line = prose[number - 1]
        if line is None or HTML_LINE.match(line):
            close()
            continue
        if not line.strip() or line.strip() in {"----", "***"}:
            close()
            continue
        if SETEXT_UNDERLINE.match(line):
            if current is not None and len(current.lines) == 1 and not current.numbered and not current.table:
                title = current.lines[0].strip()
                current = None
                add_heading(number - 1, 1 if line.strip().startswith("=") else 2, title)
            else:
                close()
            continue
        if TABLE_ROW.match(line):
            close()
            if not re.fullmatch(r"[\s|:-]+", line):
                current = Paragraph(number, [line], table=True)
                close()
            continue
        heading = heading_of(line, jira)
        if heading is not None:
            add_heading(number, *heading)
            continue
        m = BOLD_LABEL.match(line)
        if m:
            add_heading(number, 9, m.group(1) or m.group(2))
            current = Paragraph(number, [m.group(3)])
            continue
        item, numbered = _is_item(line, jira)
        if item:
            close()
            current = Paragraph(number, [line], numbered)
            continue
        if current is None:
            current = Paragraph(number, [line])
        else:
            current.lines.append(line)
    close()
    return Document(lines, jira, headings, paragraphs, sections)
