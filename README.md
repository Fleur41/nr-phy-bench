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

12 tasks in four difficulty levels. Each task is built around a specific **trap**: a step
where a plausible mistake produces a different final integer. The trap for each task is
recorded in `tasks/tasks.json`.

| Level | What the model must do | Tasks |
|---|---|---|
| **L1: explicit inputs** | Apply the procedure when every formula input is given | 4 |
| **L2: derived inputs** | Derive n_PRB from the carrier bandwidth (TS 38.101-1) and the DM-RS overhead from the DM-RS configuration (TS 38.211), then compute the TBS | 3 |
| **L3: derived and chained** | As L2, then carry the result through LDPC base-graph selection, code-block segmentation or rate matching (TS 38.212) | 3 |
| **L4: limited buffer rate matching** | As L3, plus a second, hypothetical TBS (TBS_LBRM) to size the circular buffer, then the redundancy-version start position k0 | 2 |

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
| `lbrm-k0-rv3-maxmimo8` | L4 | TBS_LBRM uses v = min(maxMIMO-Layers, 4) = 4, not 8, and n_PRB,LBRM = 135 |
| `lbrm-k0-rv2-2layer` | L4 | N_ref = 18297 is not a multiple of Z_c, so k0 needs the floor; ignoring LBRM gives 12672 |

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

Accuracy is `correct / (correct + wrong + no_answer)`. A missing or unparseable answer
counts against the model, but `truncated` and `error` are infrastructure failures, so they
are left out of the denominator and shown as "+N excl." in every table. They are re-run
with `--out` rather than scored.

## Where the golden answers come from

Golden answers are **never typed by hand**. `src/build_tasks.py` computes every answer from
the reference implementations and writes it to `tasks/tasks.json`, together with a full
trace of intermediate values (N_RE, N_info, C, Z_c, G and so on) for checking.

| Reference module | Spec |
|---|---|
| `reference/tbs.py` | TS 38.214 §5.1.3.2, Tables 5.1.3.1-1, 5.1.3.1-2, 5.1.3.2-1 |
| `reference/ldpc.py` | TS 38.212 §5.2.2 (segmentation), §5.4.2.1 (rate matching, LBRM, k0), §7.2.2 (base graph), Tables 5.3.2-1 (lifting sizes), 5.4.2.1-1 (n_PRB,LBRM), 5.4.2.1-2 (k0) |
| `reference/nr_config.py` | TS 38.101-1 Table 5.3.2-1 (N_RB), TS 38.211 §7.4.1.1.2 (DM-RS) |

The reference code uses exact rational arithmetic (`fractions.Fraction`). Spec boundaries
such as `R ≤ 0.67` and `R ≤ 1/4` are therefore evaluated exactly, without floating-point
error. The tests (`tests/`) include hand-worked examples and property checks: for example,
every TBS the procedure can produce must split evenly into LDPC code blocks, and the
rate-matching lengths must add up to exactly G.

**Independent cross-check.** `src/crosscheck.py` recomputes every golden answer *without*
importing `reference/`. TBS and code-block segmentation come from the open-source
[py3gpp](https://pypi.org/project/py3gpp/) library (`nrTBS`, `nrDLSCHInfo`, a Python port
of the MATLAB 5G Toolbox functions). G, the rate-matching lengths E, and LBRM N_cb / k0 are
re-derived from the TS 38.212 formulas, written separately from `reference/ldpc.py`. It
also compares every intermediate value in the reference trace (C, filler bits, G,
TBS_LBRM, N_cb, ...). Result: **12/12 golden answers confirmed**. py3gpp is an optional
dependency, so the eval itself does not need it:

```bash
pip install -r requirements-crosscheck.txt
python -m src.crosscheck           # exits non-zero on any disagreement
```

It also compares the spec tables in `reference/` with py3gpp's own copies: TBS Table
5.1.3.2-1, MCS index table 1 and the LDPC lifting sizes all match. The remaining small
tables (MCS index table 2, N_RB, DM-RS symbol positions, n_PRB,LBRM, k0) have no py3gpp
equivalent, so they were checked by hand against the spec documents.

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
python -m src.run_eval --models gemini:gemini-3.8-flash --samples 3 --out results/raw/flash.jsonl
python -m src.grade results/raw/*.jsonl --name final         # grade one or many files
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
and a 65,536-token output limit (falling back to 32,000 for models with a lower maximum; the settings used are recorded with each response).

Free tiers are slow and sometimes unreliable, so the runner:
- retries per-minute quota errors (429), timeouts, dropped connections and 5xx errors with bounded retries,
- stops any single request after 15 minutes,
- **resumes** with `--out`: if the file exists, finished answers are kept and only missing or failed
  ones (`error`, `truncated`) are re-run. An interrupted run is never wasted, and failures caused by
  the infrastructure are retried instead of being counted against the model.

On a **daily-capped** free tier (Gemini 3.8 Flash: 20 requests/day), every failed attempt
also uses up quota. During one demand spike, 503 retries used up a full day's quota with no
answers. For those models, use:

```bash
python -m src.run_eval --models gemini:gemini-3.8-flash --samples 3 --out results/raw/flash.jsonl \
  --transient-wait 600 --stop-after-quota-failures 2
```

`--transient-wait 600` spaces 5xx retries 10 minutes apart. `--stop-after-quota-failures 2`
stops the model after two samples in a row fail with 429; rerun the same command the next
day to continue.

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
- **Free-tier quotas.** The Gemini free tier allows **20 requests per day per model** (as of
  Nov 2026), so the 36 Gemini 3.8 Flash answers were collected over several days using the
  runner's resume feature. Groq's per-minute token limits can block or cut off long reasoning
  outputs. Quota problems show up as `error` or `truncated` and are re-run, never counted as `wrong`.
- **Small task set.** 12 tasks × 3 samples gives a directional signal, not tight confidence
  intervals. The task generator makes it easy to add more configurations.
- **Scope.** Downlink PDSCH, FR1, single-symbol DM-RS, PDSCH mapping type A, no
  limited-buffer rate matching. Uplink transform precoding, mapping type B, FR2 and
  multi-TRP are not covered yet. The L3 rate-matching prompts state that limited
  buffer rate matching is not configured. This is a stated assumption: E does not depend on N_cb, so it
  does not change the answer. L4 covers LBRM explicitly.
- **Hand-entered spec tables.** The MCS, TBS, N_RB and DM-RS tables were entered by hand
  from the 3GPP specifications and checked by the author. Corrections only need a table
  edit and `python -m src.build_tasks`. Model responses can be regraded without rerunning
  the models, because the prompts contain no derived values.

## Repository layout

```
reference/     Python reference implementations (the source of all golden answers)
src/           build_tasks.py, run_eval.py, grade.py, crosscheck.py (independent check via py3gpp)
tasks/         tasks.json (generated: prompts, golden answers, traps, reference traces)
results/raw/   raw model responses, one JSON line per task x model x sample
results/scores/ graded results (.json) and summary tables (.md)
results/pilot/ earlier exploratory runs (smaller task set, 32k output limit), kept for transparency
tests/         tests for the reference code and the grader
```

## Author

BSc Telecommunication & Information Engineering, software engineering specialisation.
Built for the micro1 AI eval hackathon, 2026.

**AI assistance:** the code in this repository was written with the help of
[Claude Code](https://claude.com/claude-code) (Anthropic). The author chose the domain and
the tasks, checked the golden answers and spec tables against the 3GPP specifications, ran
the evaluations and reviewed every change. The golden answers are also confirmed
independently with py3gpp (`python -m src.crosscheck`).
