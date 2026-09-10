#!/usr/bin/env bash
# Подключить скилл к Claude Code: ссылка в ~/.claude/skills и строка в ~/.claude/CLAUDE.md.
# Использование: install/claude-code.sh [--copy]

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
link_skill "$CLAUDE_HOME/skills" "${1:-}"
ensure_line "$CLAUDE_HOME/CLAUDE.md" "skills/plain-writing/SKILL.md" \
  "Любой текст, который прочитают без нашего чата (задача в трекере, описание MR, комментарий в ревью, сообщение коллеге, отчёт мне), пишется по \`~/.claude/skills/plain-writing/SKILL.md\`."
