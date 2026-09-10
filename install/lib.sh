# Общие функции скриптов подключения. Подключается через `source`.

set -eu

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_DIR="$REPO/skill"
SKILL_FILE="$SKILL_DIR/SKILL.md"

# Добавить строку в файл, если в нём ещё нет строки с указанной подстрокой.
# ensure_line ФАЙЛ ПОДСТРОКА ТЕКСТ
ensure_line() {
  local file="$1" marker="$2" text="$3"
  mkdir -p "$(dirname "$file")"
  if [ -f "$file" ] && grep -qF -- "$marker" "$file"; then
    echo "уже есть: $file"
    return 0
  fi
  if [ -s "$file" ] && [ "$(tail -c 1 "$file")" != "" ]; then
    printf '\n' >> "$file"
  fi
  printf '%s\n' "$text" >> "$file"
  echo "добавлено: $file"
}

# Символьная ссылка на каталог скилла (или копия при флаге --copy).
# link_skill КАТАЛОГ_СКИЛЛОВ [--copy]
link_skill() {
  local target="$1/plain-writing" mode="${2:-}"
  mkdir -p "$1"
  if [ -L "$target" ] && [ "$(readlink -f "$target")" = "$SKILL_DIR" ]; then
    echo "уже есть: $target -> $SKILL_DIR"
    return 0
  fi
  if [ -e "$target" ] && [ "$mode" != "--copy" ]; then
    echo "есть свой $target. Уберите его или запустите с --copy, чтобы заменить копией." >&2
    return 1
  fi
  if [ "$mode" = "--copy" ]; then
    rm -rf "$target"
    cp -r "$SKILL_DIR" "$target"
    echo "скопировано: $target"
  else
    ln -s "$SKILL_DIR" "$target"
    echo "ссылка: $target -> $SKILL_DIR"
  fi
}
