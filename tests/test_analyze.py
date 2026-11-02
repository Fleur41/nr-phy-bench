"""Tests for the step-level diagnosis in src/analyze.py."""
import json
from pathlib import Path

from src.analyze import first_break, numbers_in, steps

TASKS = {t["id"]: t for t in json.loads(
    (Path(__file__).resolve().parent.parent / "tasks" / "tasks.json").read_text())}


def test_numbers_in_normalises_separators_and_latex():
    found = numbers_in(r"N = 54\,296 bits, 1,081,512 and 1 081 512, N_info = 3819.375, 8\;112")
    assert {54296, 1081512, 3819, 8112} <= found


def test_steps_follow_procedure_order_and_end_with_answer():
    names = [n for n, _ in steps(TASKS["cfg-ratematch-E-last-cb"])]
    assert names[0] == "n_PRB" and names[-1] == "answer"
    assert names.index("N_RE") < names.index("N_info") < names.index("G")


def test_first_break_finds_the_156_cap_trap():
    t = TASKS["tbs-156-cap"]  # golden N_RE = 156 * 52 = 8112; the trap gives 162 * 52 = 8424
    assert first_break(t, "N_RE = 162 x 52 = 8424 ... FINAL ANSWER: 1") == "N_RE"


def test_first_break_answer_when_all_steps_present():
    t = TASKS["tbs-156-cap"]
    tr = t["reference_trace"]
    text = f"N_RE = {tr['N_RE']}, N_info = {tr['N_info']}, N' = {tr['N_info_prime']}. FINAL ANSWER: 99"
    assert first_break(t, text) == "answer"
