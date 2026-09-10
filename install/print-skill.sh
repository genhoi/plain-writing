#!/usr/bin/env bash
# Напечатать текст скилла без служебной шапки для вставки в системную инструкцию агента.
# Использование: install/print-skill.sh | pbcopy

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

awk 'NR == 1 && $0 == "---" { skip = 1; next } skip && $0 == "---" { skip = 0; next } skip { next } !started && !NF { next } { started = 1; print }' "$SKILL_FILE"
