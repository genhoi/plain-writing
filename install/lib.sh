# Общие функции скриптов подключения. Подключается через `source`.

set -eu

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
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
  local target_dir; target_dir="$(cd "$1" && pwd -P)"
  case "$SKILL_DIR/" in
    "$target_dir/plain-writing/"*)
      echo "цель $target — это сам репозиторий или каталог внутри него, ставить некуда." >&2
      return 1 ;;
  esac
  if [ -L "$target" ] && [ ! -e "$target" ]; then
    rm "$target"
    echo "убрана битая ссылка: $target"
  fi
  local ours=""
  if [ -e "$target" ] && [ "$target" -ef "$SKILL_DIR" ]; then
    ours="link"
  elif [ -d "$target" ] && [ ! -L "$target" ] && diff -rq "$SKILL_DIR" "$target" >/dev/null 2>&1; then
    ours="copy"
  fi
  if [ "$mode" != "--copy" ]; then
    case "$ours" in
      link) echo "уже есть: $target -> $SKILL_DIR"; return 0 ;;
      copy) echo "уже есть: копия в $target"; return 0 ;;
    esac
    if [ -e "$target" ]; then
      echo "есть свой $target. Уберите его или запустите с --copy, чтобы заменить копией." >&2
      return 1
    fi
    ln -s "$SKILL_DIR" "$target"
    echo "ссылка: $target -> $SKILL_DIR"
    return 0
  fi
  if [ "$ours" = "copy" ]; then
    echo "уже есть: копия в $target"
    return 0
  fi
  rm -rf "$target"
  cp -R "$SKILL_DIR" "$target"
  echo "скопировано: $target"
}
