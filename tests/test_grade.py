"""The grader must never produce a false pass or false fail on formatting alone."""
from src.grade import extract_answer


def test_plain():
    assert extract_answer("work...\nFINAL ANSWER: 54296") == 54296


def test_formatting_variants():
    assert extract_answer("FINAL ANSWER: **54296**") == 54296
    assert extract_answer("Final Answer: 1,081,512 bits") == 1081512
    assert extract_answer("FINAL ANSWER: `96`") == 96
    assert extract_answer("FINAL ANSWER = 1 081 512") == 1081512


def test_uses_last_final_answer():
    # A model that changes its mind is graded on its last stated answer.
    assert extract_answer("FINAL ANSWER: 59432\nWait, R <= 1/4...\nFINAL ANSWER: 59496") == 59496


def test_no_answer():
    assert extract_answer("The TBS is 54296.") is None
    assert extract_answer("FINAL ANSWER: cannot determine") is None
    assert extract_answer("") is None


def test_accuracy_excludes_infrastructure_failures():
    from src.grade import accuracy_cell
    rows = [{"status": s} for s in ("correct", "wrong", "no_answer", "error", "truncated")]
    assert accuracy_cell(rows) == "1/3 (33%) +2 excl."
    assert accuracy_cell([{"status": "error"}]) == "n/a +1 excl."
    assert accuracy_cell([{"status": "correct"}]) == "1/1 (100%)"
