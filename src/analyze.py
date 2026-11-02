"""Where does the chain break? Step-level diagnosis of wrong answers.

Every task in tasks/tasks.json carries the reference trace: the intermediate values of
the spec procedure (n_PRB, N_RE, N_info, N_info', TBS, K', K, G, TBS_LBRM, N_cb, ...).
For each WRONG response, this script walks the trace in procedure order and reports the
first intermediate value that does not appear anywhere in the model's working. That is
the step where the model left the spec (or the first one it skipped).

It is a deterministic heuristic, not a judge:
- a value "appears" if the exact integer occurs in the response (thousands separators,
  LaTeX spacing like 54\\,296 and decimals are normalised; N_info is matched on its
  integer part);
- values below 100 are skipped as steps (too likely to occur by coincidence);
- if every intermediate value appears but the final answer is wrong, the break is
  reported at the final step.

Usage:
    python -m src.analyze results/raw/*.jsonl            # prints and saves a summary
    python -m src.analyze results/raw/*.jsonl --name final
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from src.grade import extract_answer

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks" / "tasks.json"
SCORES = ROOT / "results" / "scores"

MIN_STEP_VALUE = 100


def steps(task: dict) -> list[tuple[str, int]]:
    """(step name, golden integer) in procedure order, ending with the asked quantity."""
    tr, cat = task["reference_trace"], task["category"]
    tbs_tr = tr.get("tbs_trace", tr)
    out: list[tuple[str, int]] = []
    if cat.startswith("config") or cat.startswith("context"):
        out.append(("n_PRB", tr.get("n_PRB")))
    if cat != "ldpc":
        out += [("N_RE", tbs_tr.get("N_RE")),
                ("N_info", math.floor(tbs_tr["N_info"]) if "N_info" in tbs_tr else None),
                ("N_info'", tbs_tr.get("N_info_prime")),
                ("TBS", tbs_tr.get("TBS"))]
    seg = tr.get("segmentation", tr if cat == "ldpc" else {})
    if cat in ("ldpc", "config-filler_bits"):
        out += [("K'", seg.get("K_prime")), ("K", seg.get("K"))]
    if cat in ("config-E_first", "config-E_last"):
        out += [("G", tr.get("G"))]
    if cat == "config-k0":
        out += [("TBS_LBRM", tr.get("TBS_LBRM")), ("N_cb", tr.get("N_cb"))]
    out = [(n, v) for n, v in out if v is not None and v >= MIN_STEP_VALUE]
    final = ("answer", task["answer"])
    if out and out[-1][1] == task["answer"]:
        out[-1] = final  # e.g. the TBS task: TBS is the answer
    elif not out or out[-1] != final:
        out.append(final)
    return out


_LATEX_SPACES = re.compile(r"\\[,;:! ]|\{,\}|~")
_NUMBER = re.compile(r"\d+(?:[,    ]\d{3})*(?:\.\d+)?")


def numbers_in(text: str) -> set[int]:
    text = _LATEX_SPACES.sub("", text)
    found = set()
    for m in _NUMBER.finditer(text):
        s = re.sub(r"[,    ]", "", m.group())
        found.add(int(float(s)) if "." in s else int(s))
    return found


def first_break(task: dict, response: str) -> str:
    present = numbers_in(response)
    for name, value in steps(task):
        if value not in present:
            return name
    return "answer"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--name", default="analysis")
    args = ap.parse_args()

    tasks = {t["id"]: t for t in json.loads(TASKS.read_text())}
    rows = []
    records = [json.loads(ln) for f in args.files for ln in Path(f).read_text().splitlines() if ln.strip()]
    for rec in records:
        task = tasks.get(rec["task_id"])
        text = rec.get("response") or ""
        if task is None or rec.get("error") or not text:
            continue
        parsed = extract_answer(text)
        if parsed is None or parsed == task["answer"]:
            continue
        rows.append({"model": rec["model"], "task_id": rec["task_id"], "level": task["level"],
                     "sample": rec["sample"], "parsed": parsed, "expected": task["answer"],
                     "first_break": first_break(task, text)})

    by_model: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        by_model[r["model"]][r["first_break"]] += 1
    order = ["n_PRB", "N_RE", "N_info", "N_info'", "K'", "K", "G", "TBS_LBRM", "N_cb", "answer"]
    cols = [c for c in order if any(c in cnt for cnt in by_model.values())]
    md = ["First step where the working leaves the reference procedure (wrong answers only).",
          "", "| Model | Wrong | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
    for m in sorted(by_model):
        cnt = by_model[m]
        md.append(f"| {m} | {sum(cnt.values())} | " + " | ".join(str(cnt.get(c, 0)) for c in cols) + " |")
    md += ["", "| Task | Level | Model | Sample | Answer | Expected | First break |",
           "|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["level"], r["task_id"], r["model"], r["sample"])):
        md.append(f"| {r['task_id']} | L{r['level']} | {r['model']} | {r['sample']} | "
                  f"{r['parsed']} | {r['expected']} | {r['first_break']} |")
    md += ["", "`answer` = every reference intermediate value appears in the working, only the "
           "last step is wrong. Heuristic: see `src/analyze.py`."]
    text = "\n".join(md) + "\n"
    print(text)
    SCORES.mkdir(parents=True, exist_ok=True)
    (SCORES / f"{args.name}.json").write_text(json.dumps(rows, indent=2) + "\n")
    (SCORES / f"{args.name}.md").write_text(text)
    print(f"Saved results/scores/{args.name}.json and .md")


if __name__ == "__main__":
    main()
