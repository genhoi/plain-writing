#!/usr/bin/env bash
# Положить ссылку на скилл в любой каталог скиллов: ~/.agents/skills, ~/.grok/skills и подобные.
# Использование: install/skills-dir.sh КАТАЛОГ [--copy]

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

[ $# -ge 1 ] || { echo "использование: $0 КАТАЛОГ [--copy]" >&2; exit 2; }
link_skill "$1" "${2:-}"
