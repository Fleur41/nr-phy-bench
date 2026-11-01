# NR-PHY-Bench

**Where AI models break on 5G physical-layer engineering.**

AI models can *explain* 5G NR well. NR-PHY-Bench tests whether they can *compute* what a
radio engineer computes every day by following the 3GPP specifications step by step: the
Transport Block Size, LDPC code-block segmentation and rate matching for a scheduled PDSCH.

Every answer is a single integer, and every golden answer is produced by a Python reference
implementation of the spec, so grading is exact: no rubric and no LLM judge.

> **Results:** see [Results](#results). **Limitations:** see [Limitations](#limitations).
> This run covers only models with a free API tier, so frontier coverage is limited.

---

## Why this domain

- **A real expert gap.** These calculations sit at the core of every 5G modem and base
  station scheduler. A single wrong rounding step changes the transport block size, and the
  receiver can no longer decode the data.
- **Exact, objective grading.** The spec defines exactly one correct integer for each task.
- **Long, unforgiving procedures.** TS 38.214 §5.1.3.2 alone chains quantisation, table
  lookups, a 156-RE cap, two rounding rules and a three-way branch on code rate and size.
  One slip anywhere gives a different number.
- **International.** 3GPP specifications are used by every 5G network in the world.

## What the tasks test

10 tasks in three difficulty levels. Each task is built around a specific **trap**: a step
where a plausible mistake produces a different final integer. The trap for each task is
recorded in `tasks/tasks.json`.

| Level | What the model must do | Tasks |
|---|---|---|
| **L1: explicit inputs** | Apply the procedure when every formula input is given | 4 |
| **L2: derived inputs** | Derive n_PRB from the carrier bandwidth (TS 38.101-1) and the DM-RS overhead from the DM-RS configuration (TS 38.211), then compute the TBS | 3 |
| **L3: derived and chained** | As L2, then carry the result through LDPC base-graph selection, code-block segmentation or rate matching (TS 38.212) | 3 |

| Task | Level | Trap |
|---|---|---|
| `tbs-156-cap` | L1 | N'_RE = 162 must be capped at 156 REs per PRB |
| `tbs-low-rate-segmentation` | L1 | Code rate ≤ 1/4: the code-block count uses 3816, not 8424 |
| `tbs-256qam-xoverhead` | L1 | xOverhead = 6 must be subtracted; the 256QAM MCS table must be used |
| `ldpc-filler-bits-bg2-large-tb` | L1 | A large TB with R ≤ 1/4 still uses **base graph 2** |
| `cfg-tbs-100mhz-256qam-4layer` | L2 | 100 MHz @ 30 kHz gives 273 PRBs; pos2 with l_d = 14 gives 3 DM-RS symbols |
| `cfg-tbs-dmrs-type2-xoverhead` | L2 | DM-RS type 2 uses 4 REs per CDM group, not 6 |
| `cfg-tbs-156-cap-derived` | L2 | The 156-RE cap, hidden behind derived inputs |
| `cfg-filler-bits-ld-trap` | L3 | For mapping type A, l_d counts from the slot start (S + L = 10, not L = 8) |
| `cfg-ratematch-E-xoverhead` | L3 | xOverhead affects the TBS only, not the rate-matching budget G |
| `cfg-ratematch-E-last-cb` | L3 | G is not divisible by C, so the last code blocks get the larger E |

## How grading works

- Each prompt asks the model to show its working and end with `FINAL ANSWER: <integer>`.
- `src/grade.py` reads the **last** `FINAL ANSWER` line. It accepts formatting variants
  such as `**54296**`, `1,081,512 bits` and `1 081 512`, and does an exact integer comparison.
- Every response gets one of five statuses, so formatting or infrastructure problems are
  never counted as wrong maths:

| Status | Meaning |
|---|---|
| `correct` | Parsed integer equals the golden answer |
| `wrong` | Parsed integer differs |
| `no_answer` | The model finished but gave no parseable final answer |
| `truncated` | The output hit the token limit before an answer (harness or quota limit) |
| `error` | The API call failed (for example a free-tier quota) |

Accuracy is `correct / total`. `truncated` and `error` are reported separately so readers
can tell model failures from infrastructure failures.

## Where the golden answers come from

Golden answers are **never typed by hand**. `src/build_tasks.py` computes every answer from
the reference implementations and writes it to `tasks/tasks.json`, together with a full
trace of intermediate values (N_RE, N_info, C, Z_c, G and so on) for checking.

| Reference module | Spec |
|---|---|
| `reference/tbs.py` | TS 38.214 §5.1.3.2, Tables 5.1.3.1-1, 5.1.3.1-2, 5.1.3.2-1 |
| `reference/ldpc.py` | TS 38.212 §5.2.2 (segmentation), §5.4.2.1 (rate matching), §7.2.2 (base graph), Table 5.3.2-1 (lifting sizes) |
| `reference/nr_config.py` | TS 38.101-1 Table 5.3.2-1 (N_RB), TS 38.211 §7.4.1.1.2 (DM-RS) |

The reference code uses exact rational arithmetic (`fractions.Fraction`). Spec boundaries
such as `R ≤ 0.67` and `R ≤ 1/4` are therefore evaluated exactly, without floating-point
error. The tests (`tests/`) include hand-worked examples and property checks: for example,
every TBS the procedure can produce must split evenly into LDPC code blocks, and the
rate-matching lengths must add up to exactly G.

## Quick start

Requires **Python 3.10+**.

```bash
git clone https://github.com/Fleur41/nr-phy-bench.git
cd nr-phy-bench
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m pytest -q                # verify the reference implementations
python -m src.build_tasks          # regenerate tasks/tasks.json from the reference code
python -m src.run_eval --dry-run   # print every prompt with its golden answer, no API calls
```

### Run against models

```bash
cp .env.example .env               # then add the key(s) for the providers you use
python -m src.run_eval --list-models gemini                  # model ids your key can use
python -m src.run_eval --models gemini:gemini-3.8-flash --samples 3 --tag flash
python -m src.grade results/raw/<file>.jsonl                 # or several files with --name
```

Supported providers (`provider:model`):

| Provider | Key in `.env` | Notes |
|---|---|---|
| `gemini` | `GEMINI_API_KEY` | Free tier at aistudio.google.com; also serves Gemma models |
| `groq` | `GROQ_API_KEY` | Free tier with tight per-minute token limits |
| `openrouter` | `OPENROUTER_API_KEY` | Free `:free` models |
| `anthropic` | `ANTHROPIC_API_KEY` | Paid |
| `openai` | `OPENAI_API_KEY` | Paid |

Every model gets the same prompt, `reasoning effort = high` where the provider supports it,
and a 65,536-token output limit (falling back to 32,000 for models with a lower maximum; the settings used are recorded with each response). Per-minute quota errors are retried automatically.

## Results

<!-- RESULTS:START -->
_Results will be added after the full run._
<!-- RESULTS:END -->

## Limitations

- **Limited frontier coverage.** This submission was built on free API tiers only. The one
  frontier model tested is **Gemini 3.8 Flash**. Gemini 3.1 Pro is not available on the
  free tier, and Claude and GPT models have no free API tier. The other models are
  open-weight. The harness already supports Anthropic and OpenAI, so anyone with keys can
  add them with one command.
- **Free-tier quotas.** Groq's per-minute token limits can block or cut off long reasoning
  outputs. These show up as `error` or `truncated`, never as `wrong`.
- **Small task set.** 10 tasks × 3 samples gives a directional signal, not tight confidence
  intervals. The task generator makes it easy to add more configurations.
- **Scope.** Downlink PDSCH, FR1, single-symbol DM-RS, PDSCH mapping type A, no
  limited-buffer rate matching. Uplink transform precoding, mapping type B, FR2 and
  multi-TRP are not covered yet.
- **Hand-entered spec tables.** The MCS, TBS, N_RB and DM-RS tables were entered by hand
  from the 3GPP specifications and checked by the author. Corrections only need a table
  edit and `python -m src.build_tasks`. Model responses can be regraded without rerunning
  the models, because the prompts contain no derived values.

## Repository layout

```
reference/     Python reference implementations (the source of all golden answers)
src/           build_tasks.py, run_eval.py, grade.py
tasks/         tasks.json (generated: prompts, golden answers, traps, reference traces)
results/raw/   raw model responses, one JSON line per task x model x sample
results/scores/ graded results (.json) and summary tables (.md)
results/pilot/ earlier exploratory runs (smaller task set, 32k output limit), kept for transparency
tests/         tests for the reference code and the grader
```

## Author

BSc Telecommunication & Information Engineering, software engineering specialisation.
Built for the micro1 AI eval hackathon, 2026.
