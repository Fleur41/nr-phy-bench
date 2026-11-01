"""Grade raw model outputs against golden answers (exact integer match).

    python -m src.grade results/raw/<run>.jsonl

Each response is classified as:
  correct      - parsed integer equals the golden answer
  wrong        - parsed integer differs
  no_answer    - no parseable "FINAL ANSWER: <integer>" line (reported separately,
                 so formatting failures are never confused with wrong maths)
  truncated    - no answer because the output hit the token limit (a harness or
                 quota limit, not a model mistake; such runs should be re-run)
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
# stop/finish reasons meaning "ran out of output tokens" across providers
TRUNCATION_REASONS = {"length", "max_tokens", "incomplete"}

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


def grade_file(*raw_paths: Path) -> tuple[list[dict], dict]:
    tasks = json.loads(TASKS.read_text())
    golden = {t["id"]: t["answer"] for t in tasks}
    level = {t["id"]: t.get("level", 1) for t in tasks}
    rows = []
    lines = [ln for p in raw_paths for ln in p.read_text().splitlines() if ln.strip()]
    for line in lines:
        rec = json.loads(line)
        if rec.get("error"):
            status, parsed = "error", None
        else:
            parsed = extract_answer(rec.get("response", ""))
            if parsed is None:
                cut_off = rec.get("stop_reason") in TRUNCATION_REASONS
                status = "truncated" if cut_off else "no_answer"
            else:
                status = "correct" if parsed == golden[rec["task_id"]] else "wrong"
        rows.append({
            "task_id": rec["task_id"], "level": level[rec["task_id"]],
            "model": rec["model"], "sample": rec.get("sample", 0),
            "expected": golden[rec["task_id"]], "parsed": parsed, "status": status,
        })

    summary = defaultdict(lambda: defaultdict(int))
    for r in rows:
        summary[r["model"]][r["status"]] += 1
        summary[r["model"]]["total"] += 1
    return rows, summary


def to_markdown(rows: list[dict], summary: dict) -> str:
    models = sorted(summary)
    task_ids = sorted({r["task_id"] for r in rows},
                      key=lambda t: (next(r["level"] for r in rows if r["task_id"] == t), t))
    levels = sorted({r["level"] for r in rows})
    out = ["| Model | Correct | Wrong | No answer | Truncated | Error | Accuracy |",
           "|---|---|---|---|---|---|---|"]
    for m in models:
        s = summary[m]
        acc = s["correct"] / s["total"] if s["total"] else 0
        out.append(f"| {m} | {s['correct']} | {s['wrong']} | {s['no_answer']} | "
                   f"{s['truncated']} | {s['error']} | {acc:.0%} |")
    names = {1: "L1 explicit", 2: "L2 derived", 3: "L3 chained", 4: "L4 LBRM"}
    out += ["", "| Model | " + " | ".join(names.get(lv, f"L{lv}") for lv in levels) + " |",
            "|---|" + "---|" * len(levels)]
    for m in models:
        cells = []
        for lv in levels:
            rs = [r for r in rows if r["model"] == m and r["level"] == lv]
            ok = sum(r["status"] == "correct" for r in rs)
            cells.append(f"{ok}/{len(rs)} ({ok / len(rs):.0%})" if rs else "-")
        out.append(f"| {m} | " + " | ".join(cells) + " |")
    out += ["", "| Task | Level | Expected | " + " | ".join(models) + " |",
            "|---|---|---|" + "---|" * len(models)]
    for tid in task_ids:
        cells = []
        for m in models:
            rs = [r for r in rows if r["task_id"] == tid and r["model"] == m]
            cells.append(", ".join(
                "✅" if r["status"] == "correct" else f"❌ {r['parsed']}" if r["status"] == "wrong"
                else r["status"] for r in rs))
        first = next(r for r in rows if r["task_id"] == tid)
        out.append(f"| {tid} | L{first['level']} | {first['expected']} | " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", type=Path, nargs="+", help="one or more results/raw/<run>.jsonl")
    ap.add_argument("--name", help="report name (default: the single input file's name)")
    ap.add_argument("--readme", action="store_true",
                    help="also write the summary tables into README.md between the RESULTS markers")
    args = ap.parse_args()

    rows, summary = grade_file(*args.raw)
    stem = args.name or (args.raw[0].stem if len(args.raw) == 1 else "combined")
    scores_dir = ROOT / "results" / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    (scores_dir / f"{stem}.json").write_text(json.dumps(rows, indent=2) + "\n")
    md = to_markdown(rows, summary)
    (scores_dir / f"{stem}.md").write_text(md)
    print(md)
    print(f"Saved results/scores/{stem}.json and .md")
    if args.readme:
        update_readme(md, [p.name for p in args.raw])


def update_readme(md: str, sources: list[str]) -> None:
    readme = ROOT / "README.md"
    text = readme.read_text()
    start, end = "<!-- RESULTS:START -->", "<!-- RESULTS:END -->"
    if start not in text or end not in text:
        raise SystemExit("README.md has no RESULTS markers")
    block = (f"{start}\n_Generated by `python -m src.grade ... --readme` from "
             f"{', '.join(f'`results/raw/{s}`' for s in sorted(sources))}._\n\n{md}{end}")
    before, rest = text.split(start, 1)
    after = rest.split(end, 1)[1]
    readme.write_text(before + block + after)
    print("Updated README.md results section")


if __name__ == "__main__":
    main()
