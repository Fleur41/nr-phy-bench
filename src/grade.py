"""Grade raw model outputs against golden answers (exact integer match).

    python -m src.grade results/raw/<run>.jsonl

Each response is classified as:
  correct      - parsed integer equals the golden answer
  wrong        - parsed integer differs
  no_answer    - no parseable "FINAL ANSWER: <integer>" line (reported separately,
                 so formatting failures are never confused with wrong maths)
  error        - the API call itself failed
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks" / "tasks.json"

_FINAL_RE = re.compile(r"FINAL\s+ANSWER\s*[:=]\s*(.+)", re.IGNORECASE)
# Digit groups may be separated by commas, spaces or thin spaces: 1,081,512 / 1 081 512
_INT_RE = re.compile(r"-?\d{1,3}(?:[,   ]\d{3})+(?!\d)|-?\d+")


def extract_answer(text: str):
    """Return the integer on the LAST 'FINAL ANSWER:' line, or None."""
    if not text:
        return None
    matches = _FINAL_RE.findall(text)
    if not matches:
        return None
    line = matches[-1].replace("*", "").replace("`", "").replace("$", "")
    m = _INT_RE.search(line)
    if not m:
        return None
    return int(re.sub(r"[,   ]", "", m.group(0)))


def grade_file(raw_path: Path) -> tuple[list[dict], dict]:
    golden = {t["id"]: t["answer"] for t in json.loads(TASKS.read_text())}
    rows = []
    for line in raw_path.read_text().splitlines():
        rec = json.loads(line)
        if rec.get("error"):
            status, parsed = "error", None
        else:
            parsed = extract_answer(rec.get("response", ""))
            if parsed is None:
                status = "no_answer"
            else:
                status = "correct" if parsed == golden[rec["task_id"]] else "wrong"
        rows.append({
            "task_id": rec["task_id"], "model": rec["model"], "sample": rec.get("sample", 0),
            "expected": golden[rec["task_id"]], "parsed": parsed, "status": status,
        })

    summary = defaultdict(lambda: defaultdict(int))
    for r in rows:
        summary[r["model"]][r["status"]] += 1
        summary[r["model"]]["total"] += 1
    return rows, summary


def to_markdown(rows: list[dict], summary: dict) -> str:
    models = sorted(summary)
    task_ids = sorted({r["task_id"] for r in rows})
    out = ["| Model | Correct | Wrong | No answer | Error | Accuracy |",
           "|---|---|---|---|---|---|"]
    for m in models:
        s = summary[m]
        acc = s["correct"] / s["total"] if s["total"] else 0
        out.append(f"| {m} | {s['correct']} | {s['wrong']} | {s['no_answer']} | "
                   f"{s['error']} | {acc:.0%} |")
    out += ["", "| Task | Expected | " + " | ".join(models) + " |",
            "|---|---|" + "---|" * len(models)]
    for tid in task_ids:
        cells = []
        for m in models:
            rs = [r for r in rows if r["task_id"] == tid and r["model"] == m]
            cells.append(", ".join(
                "✅" if r["status"] == "correct" else f"❌ {r['parsed']}" if r["status"] == "wrong"
                else r["status"] for r in rs))
        expected = rows[[r["task_id"] for r in rows].index(tid)]["expected"]
        out.append(f"| {tid} | {expected} | " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", type=Path, help="results/raw/<run>.jsonl")
    args = ap.parse_args()

    rows, summary = grade_file(args.raw)
    stem = args.raw.stem
    scores_dir = ROOT / "results" / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    (scores_dir / f"{stem}.json").write_text(json.dumps(rows, indent=2) + "\n")
    md = to_markdown(rows, summary)
    (scores_dir / f"{stem}.md").write_text(md)
    print(md)
    print(f"Saved results/scores/{stem}.json and .md")


if __name__ == "__main__":
    main()
