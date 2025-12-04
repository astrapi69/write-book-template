# tests/test_replace_md_bullet_points.py

from scripts.replace_md_bullet_points import convert_bullets_in_text


def test_simple_dash_and_star_bullets():
    input_text = "- First item\n" "* Second item\n" "Normal line\n"

    expected = "• First item  \n" "• Second item  \n" "Normal line\n"

    assert convert_bullets_in_text(input_text) == expected


def test_multiline_bullet_item():
    input_text = (
        "- First item with continuation line\n"
        "  second line of the item\n"
        "Next normal line\n"
    )

    expected = (
        "• First item with continuation line  \n"
        "  second line of the item  \n"
        "Next normal line\n"
    )

    assert convert_bullets_in_text(input_text) == expected


def test_list_state_resets_for_non_indented_line():
    input_text = "- Point one\n" "Normal line\n" "  Not a follow-item, just indented\n"

    expected = "• Point one  \n" "Normal line\n" "  Not a follow-item, just indented\n"

    assert convert_bullets_in_text(input_text) == expected


def test_code_block_is_ignored():
    input_text = (
        "```python\n" "- this is not a bullet, but code\n" "```\n" "- actual bullet\n"
    )

    expected = (
        "```python\n" "- this is not a bullet, but code\n" "```\n" "• actual bullet  \n"
    )

    assert convert_bullets_in_text(input_text) == expected


def test_indented_follow_line_without_list_start_not_treated_as_bullet():
    input_text = (
        "Normal line\n"
        "  indented line without a list\n"
        "- List item\n"
        "  continuation line\n"
    )

    expected = (
        "Normal line\n"
        "  indented line without a list\n"
        "• List item  \n"
        "  continuation line  \n"
    )

    assert convert_bullets_in_text(input_text) == expected
