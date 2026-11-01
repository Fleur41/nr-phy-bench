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
- Python only, 3.10+ required (current SDKs need it). Local venv: `/opt/homebrew/bin/python3.11 -m venv .venv`. No frontend.
- Use exact arithmetic (`fractions.Fraction`) in reference code: spec boundaries such as R <= 0.67 and R <= 1/4 matter.
- Judges check: reproducibility from README alone, no false passes / false fails in grading.

## Layout
- `reference/` — golden-answer calculators (`tbs.py`: TS 38.214 §5.1.3.2; `ldpc.py`: TS 38.212 §5.2.2, §5.4.2.1, §7.2.2; `nr_config.py`: N_RB from TS 38.101-1, DM-RS overhead from TS 38.211 §7.4.1.1.2)
- `src/build_tasks.py` — generates `tasks/tasks.json`; levels: L1 explicit inputs, L2 derived from config, L3 derived + chained (LDPC / rate matching)
- `tests/` — sanity tests for the reference code (`python -m pytest -q`)
- `tasks/tasks.json` — the eval tasks (prompt, golden answer, spec reference)
- `src/run_eval.py` — queries models (Anthropic, OpenAI, plus free OpenAI-compatible: Gemini, OpenRouter, Groq), saves raw outputs to `results/`
- `src/grade.py` — exact numeric grading
- Deliverables: README.md, requirements.txt, .env.example, results/, video ≤5 min (YouTube/Loom, not in zip)

## Plan
1. ✅ Skeleton + reference calculators + tests
2. ✅ Pilot (Nov 1): Gemini 3.8 Flash 4/4 on L1, gpt-oss-120b failed (fell for BG1 trap). Decision: keep NR-PHY-Bench, add harder L2/L3 tasks
   - Free models in use: Gemini (free tier; 3.1 Pro not available free), Groq (TPM limits too tight), GitHub Models (retired 2026-07-30, removed). Paid Anthropic/OpenAI optional
3. 🔄 12 tasks (4 L1, 3 L2, 3 L3, 2 L4 LBRM). Gemini 3.8 Flash solved L1-L3 in early samples, so L4 (LBRM k0) was added. Owner must verify tables in reference/nr_config.py and ldpc.py (Table 5.4.2.1-1)
   - Final runs (resumable with --out): results/raw/gemini-3.8-flash_L1-L2.jsonl, gemini-3.8-flash_L3-L4.jsonl, gemma-4-31b.jsonl, gpt-oss-120b.jsonl. Settings: effort high, 65k max tokens, 900s timeout. Exploratory runs in results/pilot/. Avoid >2 concurrent processes per free Gemini key (stalls)
   - QUOTA: Gemini 3.8 Flash free tier = 20 requests/day/model (resets ~08:00 EAT). Flash quota used up on Nov 1 with 4/36 done. Resume L3-L4 file first on Nov 2, then L1-L2; expected done Nov 3
4. run_eval.py + grade.py, full run, results table
5. README, video script, final zip
