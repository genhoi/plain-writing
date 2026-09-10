"""Командная строка: `python -m lint [--kind task|mr|text] [файл ...]`.

Без файлов читает stdin. Печатает `файл:строка: правило: замечание`.
Код возврата 1, если замечания есть, иначе 0.
"""

import argparse
import sys
from pathlib import Path

from . import KINDS, check


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lint", description="Проверка текста по правилам skill/SKILL.md.")
    parser.add_argument("--kind", choices=KINDS, default="text", help="форма текста: task, mr или text (по умолчанию)")
    parser.add_argument("files", nargs="*", help="файлы для проверки; без файлов читается stdin")
    args = parser.parse_args(argv)

    sources = [(name, Path(name).read_text(encoding="utf-8")) for name in args.files] or [("<stdin>", sys.stdin.read())]
    total = 0
    for name, text in sources:
        for finding in check(text, args.kind):
            print(f"{name}:{finding.line}: {finding.rule}: {finding.message}")
            total += 1
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
