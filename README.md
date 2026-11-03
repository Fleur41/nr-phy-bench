# NR-PHY-Bench

**Where AI models break on 5G physical-layer engineering.**

AI models can *explain* 5G NR well. NR-PHY-Bench tests whether they can *compute* what a
radio engineer computes every day by following the 3GPP specifications step by step: the
Transport Block Size, LDPC code-block segmentation and rate matching for a scheduled PDSCH.

Every answer is a single integer, and every golden answer is produced by a Python reference
implementation of the spec, so grading is exact: no rubric and no LLM judge.

> **Results:** see [Results](#results). **Limitations:** see [Limitations](#limitations).
> This run covers only models with a free API tier, so frontier coverage is limited.

## Short description

NR-PHY-Bench is a 14-task eval in **5G NR physical-layer engineering** (3GPP TS 38.211,
38.212, 38.214 and 38.101-1). Each task asks a model to compute one integer that a radio
engineer derives by following the spec: the transport block size, LDPC base graph, filler
bits, rate-matching length E, or the limited-buffer redundancy-version start k0. **The gap:**
models can explain these procedures, but when they have to execute them they skip steps,
invent table limits or use simplified formulas from memory, and every slip gives a different
integer. **Key finding:** [FILL AFTER FINAL RUN, e.g. "Gemini 3.8 Flash scored X/Y, while the
open-weight models gemma-4-31b and gpt-oss-120b scored 0/Z: they never completed a single TBS
procedure correctly, even with every input given (L1)."]

## Video walkthrough

**[VIDEO LINK: add after upload, and check it opens in a private window without requesting access]**

The video (≤ 5 min) covers the problem, why models fail, how the eval works and the results.

---

## Domain and expertise

**Field:** telecommunications engineering, 5G NR physical layer (downlink shared channel).

**Expertise the eval draws on:** reading and applying 3GPP specifications the way a modem,
base-station or test-equipment engineer does: TBS determination (TS 38.214 §5.1.3.2), LDPC
base-graph selection, code-block segmentation and rate matching including LBRM (TS 38.212),
DM-RS overhead (TS 38.211) and carrier bandwidth to PRB mapping (TS 38.101-1). The author
holds a BSc in Telecommunication & Information Engineering and has prior eval-writing
experience (discriminative test cases, difficulty calibration, golden-answer verification).

### Why this domain

- **A real expert gap.** These calculations sit at the core of every 5G modem and base
  station scheduler. A single wrong rounding step changes the transport block size, and the
  receiver can no longer decode the data.
- **Exact, objective grading.** The spec defines exactly one correct integer for each task.
- **Long, unforgiving procedures.** TS 38.214 §5.1.3.2 alone chains quantisation, table
  lookups, a 156-RE cap, two rounding rules and a three-way branch on code rate and size.
  One slip anywhere gives a different number.
- **International.** 3GPP specifications are used by every 5G network in the world.

## What it tests and why it matters

**What it measures:** whether a model can *execute* a multi-step 3GPP procedure exactly and
end at the one integer the spec defines, not whether it can describe the procedure.

**Who it's for:** teams building AI assistants for telecom engineering (RAN, modem and
test-equipment vendors and operators), and model developers who want a hard, objectively
graded test of long procedural reasoning over technical standards.

**Why the gap matters in practice:** engineers increasingly ask AI models to size a
transport block, check a scheduler configuration or explain a link-budget number. If a
model returns a confident but wrong TBS or rate-matching length, the gNB and UE disagree on
the bit layout and the data cannot be decoded. The error is silent: the explanation sounds
right, only the number is wrong. An exact-integer benchmark exposes this directly.

14 tasks in five difficulty levels. Each task is built around a specific **trap**: a step
where a plausible mistake produces a different final integer. The trap for each task is
recorded in `tasks/tasks.json`.

| Level | What the model must do | Tasks |
|---|---|---|
| **L1: explicit inputs** | Apply the procedure when every formula input is given | 4 |
| **L2: derived inputs** | Derive n_PRB from the carrier bandwidth (TS 38.101-1) and the DM-RS overhead from the DM-RS configuration (TS 38.211), then compute the TBS | 3 |
| **L3: derived and chained** | As L2, then carry the result through LDPC base-graph selection, code-block segmentation or rate matching (TS 38.212) | 3 |
| **L4: limited buffer rate matching** | As L3, plus a second, hypothetical TBS (TBS_LBRM) to size the circular buffer, then the redundancy-version start position k0 | 2 |
| **L5: context rules** | Recognise which rules apply from *how* the PDSCH was scheduled (DCI format, RNTI, number of codewords), which overrides the UE's configured values, then compute the TBS (TS 38.214 §5.1.3.1–5.1.3.2, TS 38.211 §7.3.1.3) | 2 |

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
| `ctx-paging-tb-scaling` | L5 | Paging (DCI 1_0, P-RNTI): MCS table 1 although qam256 is configured, xOverhead assumed 0, and TB scaling S = 0.5 moves N_info below 3824 into the table branch (golden 3824; ignoring S gives 7552) |
| `ctx-2cw-7layer-tb2` | L5 | 7 layers = two codewords: transport block 2 is mapped to ceil(7/2) = 4 layers with its own I_MCS (7 layers gives 1147488, 3 layers 491800) |

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
| `reference/context.py` | TS 38.214 §5.1.3.1 (MCS table selection), §5.1.3.2 and Table 5.1.3.2-2 (xOverhead for P/SI/RA-RNTI, TB scaling S), TS 38.211 Table 7.3.1.3-1 (codeword-to-layer mapping) |

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
TBS_LBRM, N_cb, ...). Result: **14/14 golden answers confirmed**. py3gpp is an optional
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
git clone https://github.com/Fleur41/nr-phy-bench.git   # or unzip the submission
cd nr-phy-bench                                          # (the unzipped folder)
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
python -m src.analyze results/raw/*.jsonl --name analysis    # where each wrong answer leaves the spec
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

### Reproduce the scores without API keys

The raw responses from our run are included, so the published tables can be regenerated
offline in seconds:

```bash
python -m src.grade results/raw/*.jsonl --name check   # writes results/scores/check.{json,md}
```

### Runtime and cost

- **No API calls** (tests, task build, `--dry-run`, regrading the included raw outputs):
  under a minute in total, free.
- **Full run, per model** (14 tasks × 3 samples = 42 requests, sent one at a time): in our
  run a single response took a median of about 3 min (gpt-oss-120b on Groq), 5 min
  (gemma-4-31b) and 4 to 10 min (Gemini 3.8 Flash, high reasoning effort). That is roughly
  2 to 6 hours per model, plus waiting time for free-tier rate limits.
- **Daily caps:** Gemini 3.8 Flash on the free tier allows 20 requests per day, so its 42
  answers take 2 days or more.
- **Cost:** **$0** for this submission (free tiers only). On paid APIs, expect up to roughly
  30k output tokens per response for reasoning models, so at most about 1M output tokens
  per model for the full run; multiply by your provider's price.

## Results

### Models tested and settings

| Model (provider:model ID as passed to `--models`) | Type | Provider |
|---|---|---|
| `gemini:gemini-3.8-flash` | Frontier, proprietary | Google AI Studio (free tier) |
| `gemini:gemma-4-31b-it` | Open-weight | Google AI Studio (free tier) |
| `groq:openai/gpt-oss-120b` | Open-weight | Groq (free tier) |

- **Run dates:** 1 to [END DATE] November 2026 (the free-tier quota spread the run over several days).
- **Runs per task:** 3 samples per task per model (42 responses per model).
- **Reasoning effort:** `high` where the API accepts it.
- **Max output tokens:** 65,536 (falls back to 32,000 if a model rejects it). The settings
  actually used are stored with every response in `results/raw/*.jsonl` (`settings` field).
- **Temperature:** not set, so each provider's default is used (the same for every model).
  Variation between samples is reported rather than suppressed: 3 samples per task.
- **Prompt:** identical for every model; the full prompt for every task is in `tasks/tasks.json`
  and can be printed with `python -m src.run_eval --dry-run`.

### Scores

<!-- RESULTS:START -->
_Results will be added after the full run._
<!-- RESULTS:END -->

## Failure analysis

**Where the chain breaks (automatic).** `python -m src.analyze results/raw/*.jsonl` walks
each wrong response through the reference trace of its task (n_PRB → N_RE → N_info →
N_info′ → TBS → K′/K → G → TBS_LBRM → N_cb → answer) and reports the first golden
intermediate value that never appears in the model's working. It is a deterministic
heuristic (exact integer matching, no LLM judge); spot checks by hand agreed with it.
Full per-response table: `results/scores/analysis.md`.

First step where the working leaves the reference procedure (all 84 wrong answers):

| Model | Wrong | n_PRB | N_RE | N_info | K' |
|---|---|---|---|---|---|
| gemini:gemma-4-31b-it | 42 | 8 | 19 | 12 | 3 |
| groq:openai/gpt-oss-120b | 42 | 9 | 19 | 11 | 3 |

Most failures happen **early**: 55 of the 84 wrong answers (65%) already leave the spec at
the bandwidth lookup (n_PRB) or the resource-element count (N_RE), the first two steps of
the chain. The breaks land on the steps the tasks were designed to trap: all 6 wrong
answers on `tbs-156-cap` break at **N_RE** (the 156-RE cap), 4 of the 6 on the L3
`cfg-filler-bits-ld-trap` break at N_RE (the DM-RS symbol count) and the other 2 one step
earlier at n_PRB, and all 6 on `ldpc-filler-bits-bg2-large-tb` break at **K′** (code-block
segmentation, where the base-graph choice matters).

The patterns below are taken from the raw responses in `results/raw/` (task and sample are
given so each one can be checked).

**0. Misremembering the bandwidth table (both open models).** Deriving n_PRB from the
carrier is the first L2 step, and it is a table lookup (TS 38.101-1 Table 5.3.2-1). Gemma
computed "36 MHz / (12 × 30 kHz) = 100 RBs" for 40 MHz @ 30 kHz (spec: **106**;
`cfg-tbs-dmrs-type2-xoverhead`, sample 0). gpt-oss used 135 RBs for 50 MHz @ 30 kHz
(spec: **133**; `lbrm-k0-rv3-maxmimo8`, sample 2). Everything after that step is wrong too.

**1. Skipping the TBS quantisation entirely (gemma-4-31b).** TS 38.214 §5.1.3.2 turns
N_info into a TBS through quantisation, a table or formula branch and byte alignment. Gemma
often stops at N_info: "the TBS is the floor of N_info" gives **54789** on `tbs-156-cap`
(sample 2; golden 54296). That value is not even a multiple of 8, which no valid TBS can be.
Other samples invent formulas: TBS = S·v·N_info (40416), or rounding to a multiple of 1000
(804000 on `cfg-tbs-100mhz-256qam-4layer`). This happens on L1, where every input is given.

**2. Inventing table limits (gpt-oss-120b).** Table 5.1.3.2-1 only applies when
N_info ≤ 3824; larger values use a formula. gpt-oss instead treats the table as the upper
limit for every TBS and invents a "maximum entry": "the largest entry of the table … is
**38 240 bits** … the selected TBS is capped" (`tbs-256qam-xoverhead`, sample 0; golden
143400). The same invented cap appears on `cfg-tbs-156-cap-derived` and a different one
(61440) on `tbs-low-rate-segmentation`.

**3. Base-graph selection from memory, not from the spec (gpt-oss-120b).** TS 38.212 §7.2.2
selects **base graph 2** whenever the code rate R ≤ 0.25, regardless of the block size. On
`ldpc-filler-bits-bg2-large-tb` gpt-oss used a size-only rule ("A > 3824 → BG1", "B > 8424 →
BG1"), chose BG1 and got 216 / 280 filler bits instead of 96. This is the trap the task was
built around, and it was also the failure seen in the pilot.

**4. Getting the rate-matching split backwards (gpt-oss-120b).** When G is not divisible by
the number of code blocks, the spec gives the *last* blocks the larger length E. On
`cfg-ratematch-E-last-cb` gpt-oss stated that the last block "receives only the base
amount" (sample 1: 9059; golden 9088).

**5. Simplified k0 formula for limited-buffer rate matching (both open models).** TS 38.212
Table 5.4.2.1-2 defines k0 for rv = 3 with BG1 as ⌊56·N_cb / (66·Z_c)⌋·Z_c. Both open models
used ⌊rv·N_cb / 4⌋ instead, with wrong N_cb values as well: gemma 92160, gpt-oss 12288
(`lbrm-k0-rv3-maxmimo8`; golden 14592). Gemma's working shows it guessing ("N_cb^max =
122880 × something? No.").

**6. Gemini 3.8 Flash.** [FILL AFTER FINAL RUN: so far every Flash answer that came back
was correct, including the LBRM k0 task. Describe any failures here, or state plainly that
Flash solved the tasks it answered, and what that means for the gap (the gap is largest for
open-weight models that teams can deploy on-premises).]

**Why the models fail, in short:** the procedures are long, and each step has a plausible
shortcut that looks right in a textbook explanation (a table "maximum", a size-only base-graph
rule, an evenly spaced k0). Models that know *about* the spec take the shortcut. The exact
integer answer shows every such slip, where a free-text answer would hide it.

**Not counted as model failures:** API errors (429 quota, 5xx) and truncated outputs are
shown separately as "+N excl." and re-run; they never count as wrong.

## Prior work and sources

- **Built during the hackathon.** No code, tasks or data existed before the hackathon. No
  existing benchmark or dataset was used; all 14 tasks and their configurations were written
  for this eval.
- **3GPP specifications (the source of every rule and table):**
  - TS 38.214 (NR; Physical layer procedures for data), §5.1.3 (Release 18)
  - TS 38.212 (NR; Multiplexing and channel coding), §5.2.2, §5.3.2, §5.4.2.1, §7.2.2 (Release 18)
  - TS 38.211 (NR; Physical channels and modulation), §7.3.1.3, §7.4.1.1.2 (Release 18)
  - TS 38.101-1 (NR; UE radio transmission and reception, Part 1: FR1), Table 5.3.2-1 (Release 18)

  The specifications are freely available from [3gpp.org](https://www.3gpp.org/specifications).
  Only table values needed for the calculations are reproduced in `reference/`; no spec text
  or documents are included.
- **[py3gpp](https://pypi.org/project/py3gpp/)** (open source): used only as an independent
  cross-check of the golden answers and tables (`src/crosscheck.py`), not to produce them.
- **Tools:** the code was written with AI coding assistance (see [Author](#author)).

## Limitations

- **Limited frontier coverage.** This submission was built on free API tiers only. The one
  frontier model tested is **Gemini 3.8 Flash**. Gemini 3.1 Pro is not available on the
  free tier, and Claude and GPT models have no free API tier. The other models are
  open-weight. The harness already supports Anthropic and OpenAI, so anyone with keys can
  add them with one command.
- **Free-tier quotas.** The Gemini free tier allows **20 requests per day per model** (as of
  Nov 2026), so the 42 Gemini 3.8 Flash answers were collected over several days using the
  runner's resume feature. Failed attempts (for example 503 "high demand" errors) also
  count against that quota. Groq's per-minute token limits can block or cut off long reasoning
  outputs. Quota problems show up as `error` or `truncated` and are re-run, never counted as `wrong`.
- **Small task set.** 14 tasks × 3 samples gives a directional signal, not tight confidence
  intervals. The task generator makes it easy to add more configurations.
- **Scope.** Downlink PDSCH, FR1, single-symbol DM-RS, PDSCH mapping type A, single DL BWP
  spanning the carrier. Uplink transform precoding, mapping type B, FR2 and multi-TRP are not
  covered yet. The L3 rate-matching prompts state that limited-buffer rate matching is not
  configured. E does not depend on N_cb, so this assumption does not change the answer.
  L4 covers LBRM explicitly.
- **Hand-entered spec tables.** The spec tables were entered by hand from the 3GPP
  specifications. The TBS table, MCS index table 1 and the LDPC lifting sizes are also
  checked automatically against py3gpp (`python -m src.crosscheck`). The rest (MCS index
  table 2, N_RB, DM-RS, LBRM tables) and the L5 context rules in `reference/context.py`
  (MCS table selection, xOverhead and TB scaling for P-RNTI, codeword-to-layer mapping) were
  checked by the author against the spec text. Corrections only need a table
  edit and `python -m src.build_tasks`. Model responses can be regraded without rerunning
  the models, because the prompts contain no derived values.

## Repository layout

```
reference/     Python reference implementations (the source of all golden answers)
src/           build_tasks.py, run_eval.py, grade.py, analyze.py (step-level diagnosis), crosscheck.py (independent check via py3gpp)
tasks/         tasks.json (generated: prompts, golden answers, traps, reference traces)
results/raw/   raw model responses, one JSON line per task x model x sample
results/scores/ graded results (.json) and summary tables (.md)
results/pilot/ earlier exploratory runs (smaller task set, 32k output limit), kept for transparency
tests/         tests for the reference code, the grader and the analysis
```

## Author

BSc Telecommunication & Information Engineering, software engineering specialisation.
Built for the micro1 AI eval hackathon, 2026.

**AI assistance:** the code in this repository was written with the help of
[Claude Code](https://claude.com/claude-code) (Anthropic). The author chose the domain and
the tasks, checked the golden answers and spec tables against the 3GPP specifications, ran
the evaluations and reviewed every change. The golden answers are also confirmed
independently with py3gpp (`python -m src.crosscheck`).
