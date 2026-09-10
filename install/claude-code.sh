#!/usr/bin/env bash
# Подключить скилл к Claude Code: ссылка в ~/.claude/skills и строка в ~/.claude/CLAUDE.md.
# Использование: install/claude-code.sh [--copy]

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
link_skill "$CLAUDE_HOME/skills" "${1:-}"
path="$CLAUDE_HOME/skills/plain-writing/SKILL.md"
case "$path" in "$HOME"/*) path="~${path#"$HOME"}" ;; esac
ensure_line "$CLAUDE_HOME/CLAUDE.md" "plain-writing/SKILL.md\`. Перед публикацией" \
  "Любой текст, который прочитают без нашего чата (задача в трекере, описание MR, комментарий в ревью, сообщение коллеге, отчёт мне), пишется по \`$path\`. Перед публикацией перечитать как чужой."
