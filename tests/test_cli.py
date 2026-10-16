"""Командная строка: файлы, stdin, код возврата."""

import subprocess
import sys

from tests.conftest import ROOT


def run(*args, stdin=None):
    return subprocess.run([sys.executable, "-m", "lint", *args], cwd=ROOT, input=stdin, capture_output=True, text=True, encoding="utf-8")


def test_clean_file_exits_zero(reference):
    result = run("--kind", "task", str(reference / "task-after.md"))
    assert result.returncode == 0
    assert result.stdout == ""


def test_file_with_findings_exits_one(reference):
    result = run("--kind", "task", str(reference / "task-before.md"))
    assert result.returncode == 1
    lines = result.stdout.splitlines()
    assert len(lines) >= 3
    assert all(line.startswith(str(reference / "task-before.md") + ":") for line in lines)
    assert any(": jargon: " in line for line in lines)


def test_stdin():
    result = run(stdin="Сделал минимальный фикс.\n")
    assert result.returncode == 1
    assert result.stdout.splitlines() == [
        "<stdin>:1: jargon: «фикс»: жаргон, замена: исправление",
        "<stdin>:1: self-praise: «минимальный»: самооценка, пусть читатель оценит сам",
    ]


def test_several_files(reference):
    result = run(str(reference / "task-after.md"), str(reference / "mr-before.md"))
    assert result.returncode == 1
    assert "mr-before.md:" in result.stdout
    assert "task-after.md:" not in result.stdout


def test_missing_file_exits_two():
    result = run("nosuch.md")
    assert result.returncode == 2
    assert "nosuch.md" in result.stderr
    assert "Traceback" not in result.stderr


def test_bom_file(tmp_path):
    path = tmp_path / "task.md"
    path.write_text("\ufeff## Проблема\n\nТекст.\n\n## Что сделать\n\n1. `X`: y.\n\n## Как проверить\n\n- вернуть заказ.\n", encoding="utf-8")
    assert run("--kind", "task", str(path)).returncode == 0
