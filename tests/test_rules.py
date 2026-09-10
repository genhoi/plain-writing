"""Каждое правило: текст, на котором оно срабатывает, и текст, на котором молчит."""

import pytest

from lint import check
from lint.rules import read_list
from tests.conftest import rules

CLEAN = "Заказ на 3000 ₽ со скидкой 300 ₽ возвращается за 900 ₽ за позицию. Так считает `RefundCalculator`."


def test_clean_text_has_no_findings():
    assert check(CLEAN) == []


# 1. Разделы, которых не должно быть.

@pytest.mark.parametrize(
    "heading",
    ["## Не входит", "h2. Что осталось за бортом", "**Что не сделано**", "## Out of scope", "### Not included", "*Не вошло*"],
)
def test_sections_forbidden_heading(heading):
    findings = check(f"{heading}\n\nПеренос старых заказов.\n")
    assert [f.rule for f in findings] == ["sections"]
    assert findings[0].line == 1


@pytest.mark.parametrize("heading", ["## Проблема", "h2. Ограничение", "**Как проверить**", "## Не входит в стоимость доставки", "## Не входит НДС в эту сумму"])
def test_sections_allowed_heading(heading):
    text = f"{heading}\n\nПосле оплаты строка закрыта.\n"
    assert "sections" not in rules(check(text))


def test_sections_setext_heading():
    findings = check("Не входит\n---\n\nПеренос старых заказов.\n")
    assert [(f.rule, f.line) for f in findings] == [("sections", 1)]


def test_sections_mention_in_prose_is_fine():
    assert "sections" not in rules(check("Раздела «Не входит» в задаче нет.\n"))


# 2. Жаргон из lint/jargon.txt.

@pytest.mark.parametrize("entry", read_list("jargon.txt"), ids=lambda e: e.word)
def test_jargon_each_entry_triggers(entry):
    findings = check(f"Здесь {entry.word} и больше ничего.\n")
    assert [f.rule for f in findings] == ["jargon"]
    assert entry.replacement in findings[0].message


def test_jargon_repeated_word_reported_twice():
    findings = check("Сначала спайк на день, потом второй спайк.\n")
    assert [f.rule for f in findings] == ["jargon", "jargon"]


def test_jargon_phrase_across_wrapped_lines():
    assert "self-praise" in rules(check("Изменение очень\nполезно всем.\n"))
    assert check("Слово «минимальный\nфикс» заменить.\n") == []


def test_jargon_matches_word_forms():
    assert "jargon" in rules(check("Запись идемпотентная, повторный вызов ничего не меняет.\n"))


def test_jargon_ignores_code_names():
    assert "jargon" not in rules(check("Флаг `fail-closed` в `config/payment.php` включён.\n"))


def test_jargon_ignores_longer_words():
    assert "jargon" not in rules(check("Префикс и фиксация суммы остаются.\n"))


# 3. Внутренние коды и ветки.

def test_codes_unexplained_key():
    findings = check("Проверка из SHOP-388 сохраняется.\n")
    assert [f.rule for f in findings] == ["codes"]
    assert "SHOP-388" in findings[0].message


def test_codes_explained_in_same_paragraph():
    text = "Проверку из SHOP-388 (заказ с неснятой строкой предоплаты пропускается) оставить.\n"
    assert "codes" not in rules(check(text))


def test_codes_explained_with_colon():
    assert "codes" not in rules(check("SHOP-388: заказ с неснятой строкой предоплаты пропускается.\n"))


def test_codes_explanation_in_other_paragraph_does_not_count():
    text = "SHOP-388 (пропуск смешанных заказов) остаётся.\n\nПроверка из SHOP-388 идёт первой.\n"
    findings = check(text)
    assert [f.line for f in findings if f.rule == "codes"] == [3]


def test_codes_mr_number():
    assert "codes" in rules(check("Сделано в MR !120 без таблицы требований.\n"))


def test_codes_patterns_come_from_file():
    assert [e.word for e in read_list("codes.txt")], "lint/codes.txt пуст"


def test_codes_standards_are_not_codes():
    text = "Кодировка UTF-8, хеш SHA-256, дата в ISO-8601, ключ AES-256, протокол TLS-1.3.\n"
    assert check(text) == []


def test_codes_in_headings_are_checked():
    assert [f.rule for f in check("## Проверка SHOP-388\n\nТекст.\n")] == ["codes"]


def test_codes_explained_after_link():
    text = "Проверку из [SHOP-388](https://tracker.local/SHOP-388) (заказ пропускается) оставить.\n"
    assert check(text) == []
    assert check("Проверку из [SHOP-388|https://tracker.local/SHOP-388] (заказ пропускается) оставить.\n") == []


def test_codes_inside_explained_branch_are_explained():
    assert check("Ветка `SHOP-410-payment` (перенос стадии оплаты) ждёт ревью.\n") == []


@pytest.mark.parametrize(
    "text",
    ["Это вырез из ветки `feature/refund-fix` без переноса.\n", "Merged from the `hotfix-12` branch.\n", "Ветка {{shop-410-payment}} ещё живёт.\n"],
)
def test_codes_branch_without_explanation(text):
    findings = check(text)
    assert "codes" in rules(findings)
    assert "ветка" in findings[0].message


def test_codes_branch_with_explanation():
    text = "Ветка `feature/refund-fix` (пересчёт скидки при возврате) ждёт ревью.\n"
    assert "codes" not in rules(check(text))


def test_codes_ignore_urls_and_plain_words():
    text = "Смотреть https://tracker.local/browse/NP-12 и слово ветка без имени.\n"
    assert "codes" not in rules(check(text))


# 4. Самооценка из lint/self-praise.txt.

@pytest.mark.parametrize("entry", read_list("self-praise.txt"), ids=lambda e: e.word)
def test_self_praise_each_entry_triggers(entry):
    findings = check(f"Получился {entry.word} вариант.\n")
    assert [f.rule for f in findings] == ["self-praise"]


def test_self_praise_exceptions_from_list():
    assert check("Минимальная сумма заказа 600 ₽, минимальный порог 100 ₽.\n") == []
    assert "self-praise" in rules(check("Сделал минимальный вырез.\n"))


def test_self_praise_matches_word_forms():
    assert "self-praise" in rules(check("Сделал минимальные правки.\n"))


def test_self_praise_ignores_negation_and_code():
    assert "self-praise" not in rules(check("Поле `min_amount` и нечестная сумма.\n"))


# 5. Длина.

def test_length_long_sentence():
    text = " ".join(["слово"] * 36) + ".\n"
    findings = check(text)
    assert [f.rule for f in findings] == ["length"]
    assert "36" in findings[0].message


def test_length_sentence_of_35_words_passes():
    assert check(" ".join(["слово"] * 35) + ".\n") == []


def test_length_semicolon_splits_sentences():
    text = "; ".join([" ".join(["слово"] * 20)] * 2) + ".\n"
    assert check(text) == []


def test_length_code_names_count_as_one_word():
    text = " ".join(["слово"] * 34) + " `UPDATE ... WHERE id = :id AND processed_at IS NULL`.\n"
    assert check(text) == []


def test_length_long_paragraph():
    text = " ".join(["Строка закрыта."] * 9) + "\n"
    findings = check(text)
    assert [f.rule for f in findings] == ["length"]
    assert "9 предложений" in findings[0].message


def test_length_list_items_are_separate_paragraphs():
    text = "\n".join(["- Строка закрыта. Сумма записана."] * 6) + "\n"
    assert check(text) == []


def test_length_abbreviations_do_not_split():
    from lint.document import split_sentences

    assert len(split_sentences("Сумма, т.е. 600 ₽, записана. См. Таблицу.")) == 2
    assert len(split_sentences("Вернули 100 руб. 200 руб. ждут, т.к. 2019 г. закрыт. Итого.")) == 2
    text = " ".join(["слово"] * 33) + " т.е. 600 рублей записаны.\n"
    assert [f.rule for f in check(text)] == ["length"]


def test_length_quote_after_period_does_not_glue_sentences():
    text = " ".join(["Строка закрыта «словом»."] * 3) + "\n"
    assert check(text) == []


def test_length_wide_table_row_is_not_a_paragraph():
    row = "| " + " | ".join(["a"] * 10) + " |\n"
    assert check(row + "|" + "---|" * 10 + "\n" + row) == []


def test_length_reports_line_of_sentence():
    text = "Первая строка.\nВторая строка.\n" + " ".join(["Слово"] * 40) + ".\n"
    assert [f.line for f in check(text)] == [3]


# 6. Форма задачи.

TASK = """## Проблема

Скидка вычитается из первой позиции целиком.

## Что сделать

1. `RefundCalculator::calculate()`: делить скидку пропорционально цене.
2. Таблица `refund_item`: добавить колонку `discount_share`.

## Как проверить

- Тест на три позиции по 1000 ₽.
"""

TASK_JIRA = TASK.replace("## Проблема", "h2. Проблема").replace("## Что сделать", "h2. Что сделать").replace("## Как проверить", "h2. Как проверить").replace("1. `RefundCalculator::calculate()`", "# {{RefundCalculator::calculate()}}").replace("2. Таблица `refund_item`", "# Таблица {{refund_item}}")


@pytest.mark.parametrize("text", [TASK, TASK_JIRA])
def test_task_form_passes(text):
    assert check(text, kind="task") == []


def test_task_form_not_checked_without_kind():
    assert check("Просто абзац.\n") == []


def test_task_form_missing_sections():
    findings = check("## Проблема\n\nСкидка вычитается целиком.\n", kind="task")
    messages = [f.message for f in findings]
    assert all(f.rule == "task-form" for f in findings)
    assert any("Что сделать" in m for m in messages)
    assert any("Как проверить" in m for m in messages)
    assert not any("Проблема" in m for m in messages)


def test_task_form_requires_numbered_list():
    text = TASK.replace("1. `RefundCalculator", "- `RefundCalculator").replace("2. Таблица", "- Таблица")
    findings = check(text, kind="task")
    assert [f.rule for f in findings] == ["task-form"]
    assert "нумерованного списка" in findings[0].message


def test_task_form_subheading_keeps_items():
    text = TASK.replace("## Что сделать\n", "## Что сделать\n\n### Бэкенд\n")
    assert check(text, kind="task") == []
    broken = text.replace("2. Таблица `refund_item`: добавить колонку `discount_share`.", "2. Добавить колонку.")
    assert [f.rule for f in check(broken, kind="task")] == ["task-form"]


def test_task_form_bold_label_sections():
    text = "**Проблема**: скидка вычитается целиком.\n\n**Что сделать**:\n\n1. `RefundCalculator`: делить.\n\n**Как проверить**: тест.\n"
    assert check(text, kind="task") == []


def test_task_form_item_without_code_name():
    text = TASK.replace("2. Таблица `refund_item`: добавить колонку `discount_share`.", "2. Добавить колонку для доли скидки.")
    findings = check(text, kind="task")
    assert [(f.rule, f.line) for f in findings] == [("task-form", 8)]


# 7. Форма MR.

MR = """## Зачем

Скидка вычитается из первой позиции целиком.

## Что изменилось

Скидка делится пропорционально цене в `RefundCalculator`.

## Проверки

- Тест на три позиции по 1000 ₽.
"""


def test_mr_form_passes():
    assert check(MR, kind="mr") == []


def test_mr_form_accepts_how_verified():
    assert check(MR.replace("## Проверки", "## Как проверено"), kind="mr") == []


def test_mr_form_missing_section():
    findings = check(MR.replace("## Проверки", "## Тесты"), kind="mr")
    assert [f.rule for f in findings] == ["mr-form"]
    assert "Проверки" in findings[0].message


def test_mr_form_not_applied_to_task():
    assert "mr-form" not in rules(check(TASK, kind="task"))


def test_unknown_kind_rejected():
    with pytest.raises(KeyError):
        check(MR, kind="letter")


# Разметка: что правила пропускают.

def test_fenced_code_and_html_are_not_checked():
    text = "<p>минимальный фикс</p>\n\n```\nСделал минимальный фикс в SHOP-1.\n```\n\nАбзац.\n"
    assert check(text) == []


def test_quoted_word_is_a_mention():
    assert check("Слово «спайк», слово \"честно\" и слово “бэкофф” заменить.\n") == []


def test_quoted_sentence_is_still_checked():
    assert "jargon" in rules(check("Он написал: «сделаем спайк на день, потом решим, что дальше, и обсудим с командой».\n"))


def test_table_cells_are_separate_sentences():
    cell = " ".join(["слово"] * 20)
    assert check(f"| a | b |\n|---|---|\n| {cell} | {cell} |\n") == []


def test_code_in_backticks_explained_after_closing_quote():
    assert "codes" not in rules(check("Ключ `NP-12` (префикс проекта и номер) в тексте.\n"))


def test_fence_closes_only_with_matching_marker():
    text = "````\nминимальный фикс\n```\nещё код\n````\n\nПосле спайка.\n"
    findings = check(text)
    assert [(f.rule, f.line) for f in findings] == [("jargon", 7)]
    text = "```\nминимальный фикс\n~~~\n```\n\nТекст.\n"
    assert check(text) == []


def test_jira_code_block_is_not_prose():
    text = "h2. Проблема\n\n{code:java}\nидемпотентный ключ SHOP-1\n{code}\n\n{noformat}\nfail-closed\n{noformat}\n"
    assert check(text) == []


def test_jira_heading_inside_fence_does_not_switch_markup():
    text = TASK + "\n```\nh2. Пример\n```\n"
    assert check(text, kind="task") == []


def test_autolink_line_is_checked():
    assert "self-praise" in rules(check("<https://tracker.local/x> там минимальный фикс\n"))


def test_html_line_inside_paragraph_keeps_line_numbers():
    text = "Первая строка.\n<br>\nСделал минимальный фикс.\n"
    assert [f.line for f in check(text)] == [3, 3]


def test_bom_does_not_hide_first_heading():
    assert check("\ufeff## Не входит\n\nТекст.\n") != []
