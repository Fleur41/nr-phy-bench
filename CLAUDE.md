# NR-PHY-Bench — project context for Claude Code

## What this is
Submission for the **micro1 AI eval hackathon** (international, cash prizes, goal: top 3).
Deadline: **Nov 9, 2026, 11:15 AM Nairobi time (EAT)**.

**NR-PHY-Bench: Where Frontier AI Models Break on 5G Physical-Layer Engineering.**
An eval of 5–10 expert tasks where models must *calculate* (not explain) 3GPP 5G NR
physical-layer quantities, step by step per the spec. Every answer is a number,
graded exactly against a Python reference implementation.

## Owner
BSc Telecommunication & Information Engineering, software engineering specialisation,
prior eval-writing experience at Turing (discriminative test cases, difficulty calibration,
golden-answer verification). The owner is the domain expert who verifies golden answers
against the spec, runs the eval with their own API keys, records the video, and makes all git commits.

## Working rules
- Claude creates/edits files; **the user commits and pushes themselves**. Tell them when to commit and suggest a message. Do not run `git commit`/`git push`.
- Python only (local Python is 3.9.6, so keep code 3.9-compatible). No frontend.
- Use exact arithmetic (`fractions.Fraction`) in reference code: spec boundaries such as R <= 0.67 and R <= 1/4 matter.
- Judges check: reproducibility from README alone, no false passes / false fails in grading.

## Layout
- `reference/` — golden-answer calculators (`tbs.py`: TS 38.214 §5.1.3.2; `ldpc.py`: TS 38.212 §5.2.2, §7.2.2)
- `tests/` — sanity tests for the reference code (`python -m pytest -q`)
- `tasks/tasks.json` — the eval tasks (prompt, golden answer, spec reference)
- `src/run_eval.py` — queries models (Anthropic, OpenAI, Google), saves raw outputs to `results/`
- `src/grade.py` — exact numeric grading
- Deliverables: README.md, requirements.txt, .env.example, results/, video ≤5 min (YouTube/Loom, not in zip)

## Plan
1. ✅ Skeleton + reference calculators + tests
2. Pilot: 3–4 tasks against models. If models ace them, switch to backup "RF-LinkBench" (link budgets / dB traps)
3. Write 5–10 final tasks, calibrate difficulty
4. run_eval.py + grade.py, full run, results table
5. README, video script, final zip
