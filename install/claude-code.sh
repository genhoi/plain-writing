#!/usr/bin/env bash
# Подключить скилл к Claude Code: ссылка в ~/.claude/skills и строка в ~/.claude/CLAUDE.md.
# Использование: install/claude-code.sh [--copy]

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
link_skill "$CLAUDE_HOME/skills" "${1:-}"
# Скилл загружается инструментом Skill, а не чтением файла: только такие скиллы Claude Code
# возвращает в контекст после его сжатия.
if [ -f "$CLAUDE_HOME/CLAUDE.md" ] && grep -qF -- "plain-writing/SKILL.md\`. Перед публикацией" "$CLAUDE_HOME/CLAUDE.md"; then
  echo "в $CLAUDE_HOME/CLAUDE.md строка ведёт к файлу SKILL.md: после сжатия контекста правила теряются." >&2
  echo "Замените её строкой «…пишется по скиллу plain-writing. Загружать его инструментом Skill…»." >&2
fi
ensure_line "$CLAUDE_HOME/CLAUDE.md" "plain-writing" \
  "Любой текст, который прочитают без нашего чата (задача в трекере, описание MR, комментарий в ревью, сообщение коллеге, отчёт мне), пишется по скиллу plain-writing. Загружать его инструментом Skill, а не читать файл: так правила вернутся в контекст после его сжатия. Перед публикацией перечитать как чужой."
