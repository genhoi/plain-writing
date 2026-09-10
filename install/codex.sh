#!/usr/bin/env bash
# Подключить скилл к Codex: строка в ~/.codex/AGENTS.md со ссылкой на SKILL.md.
# Использование: install/codex.sh

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
ensure_line "$CODEX_HOME/AGENTS.md" "skill/SKILL.md\`. Прочитай файл перед тем, как писать такой текст." \
  "Любой текст, который прочитают без нашего чата (задача в трекере, описание MR, комментарий в ревью, сообщение коллеге, отчёт мне), пишется по правилам из \`$SKILL_FILE\`. Прочитай файл перед тем, как писать такой текст."
