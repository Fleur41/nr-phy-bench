"""Generate tasks/tasks.json from task parameters.

Golden answers are never typed by hand: each one is computed by the
reference implementation in reference/. To add a task, add an entry
to TBS_TASKS or LDPC_TASKS and re-run:

    python -m src.build_tasks
"""
from __future__ import annotations

import json
from pathlib import Path

from reference.ldpc import segment, select_base_graph
from reference.tbs import MCS_TABLES, compute_tbs

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tasks" / "tasks.json"

ANSWER_FORMAT = (
    "Show your working, then end your response with a final line in exactly "
    "this format (digits only, no commas or units):\nFINAL ANSWER: <integer>"
)

MCS_TABLE_NAMES = {
    1: "TS 38.214 Table 5.1.3.1-1 (MCS index table 1, up to 64QAM)",
    2: "TS 38.214 Table 5.1.3.1-2 (MCS index table 2, up to 256QAM)",
}

# Each entry: id, trap (what the task is designed to catch), and parameters.
TBS_TASKS = [
    {
        "id": "tbs-156-cap",
        "trap": "N'_RE = 162 exceeds 156 and must be capped at 156 per PRB",
        "params": dict(n_prb=52, n_symb_sh=14, n_dmrs_prb=6, mcs_index=20,
                       mcs_table=1, num_layers=2, n_oh_prb=0),
    },
    {
        "id": "tbs-low-rate-segmentation",
        "trap": "R <= 1/4 in step 4: C uses 3816, not the 8424 branch",
        "params": dict(n_prb=273, n_symb_sh=13, n_dmrs_prb=12, mcs_index=2,
                       mcs_table=1, num_layers=4, n_oh_prb=0),
    },
    {
        "id": "tbs-256qam-xoverhead",
        "trap": "xOverhead = 6 must be subtracted; 256QAM table 2 must be used",
        "params": dict(n_prb=106, n_symb_sh=12, n_dmrs_prb=12, mcs_index=20,
                       mcs_table=2, num_layers=2, n_oh_prb=6),
    },
]

LDPC_TASKS = [
    {
        "id": "ldpc-filler-bits-bg2-large-tb",
        "trap": "Large TB but R <= 1/4 forces base graph 2 (K_cb = 3840), not BG1",
        "tbs": 59496,
        "mcs_index": 2,
        "mcs_table": 1,
    },
]


def tbs_prompt(p: dict) -> str:
    return (
        "You are a 5G NR physical-layer engineer. Following 3GPP TS 38.214 "
        "Section 5.1.3.2 exactly, compute the Transport Block Size (TBS) in bits "
        "for this PDSCH transmission:\n"
        f"- MCS index table: {MCS_TABLE_NAMES[p['mcs_table']]}\n"
        f"- MCS index I_MCS = {p['mcs_index']}\n"
        f"- Allocated PRBs n_PRB = {p['n_prb']}\n"
        f"- PDSCH symbols in the slot N_symb^sh = {p['n_symb_sh']}\n"
        f"- DM-RS REs per PRB N_DMRS^PRB = {p['n_dmrs_prb']} "
        "(already includes the overhead of DM-RS CDM groups without data)\n"
        f"- xOverhead N_oh^PRB = {p['n_oh_prb']}\n"
        f"- Number of layers v = {p['num_layers']}\n"
        "- Single codeword, scaling factor S = 1 (not a P-RNTI/RA-RNTI transmission)\n\n"
        + ANSWER_FORMAT
    )


def ldpc_prompt(t: dict) -> str:
    qm, r1024 = MCS_TABLES[t["mcs_table"]][t["mcs_index"]]
    return (
        "You are a 5G NR physical-layer engineer. A PDSCH transport block of "
        f"A = {t['tbs']} bits is scheduled with I_MCS = {t['mcs_index']} from "
        f"{MCS_TABLE_NAMES[t['mcs_table']]}, i.e. target code rate "
        f"R = {r1024}/1024 and Q_m = {qm}.\n\n"
        "Following 3GPP TS 38.212 (LDPC base graph selection in Section 7.2.2, "
        "transport-block CRC attachment, and code block segmentation in "
        "Section 5.2.2), determine the number of filler bits F = K - K' inserted "
        "into EACH code block.\n\n"
        + ANSWER_FORMAT
    )


def build() -> list[dict]:
    tasks = []
    for t in TBS_TASKS:
        tbs, trace = compute_tbs(**t["params"], return_trace=True)
        tasks.append({
            "id": t["id"], "category": "tbs", "spec": "TS 38.214 5.1.3.2",
            "trap": t["trap"], "params": t["params"], "prompt": tbs_prompt(t["params"]),
            "answer": tbs, "reference_trace": trace,
        })
    for t in LDPC_TASKS:
        _, r1024 = MCS_TABLES[t["mcs_table"]][t["mcs_index"]]
        bg = select_base_graph(t["tbs"], r1024 / 1024)
        seg = segment(t["tbs"], bg)
        tasks.append({
            "id": t["id"], "category": "ldpc", "spec": "TS 38.212 5.2.2, 7.2.2",
            "trap": t["trap"],
            "params": {k: t[k] for k in ("tbs", "mcs_index", "mcs_table")},
            "prompt": ldpc_prompt(t), "answer": seg["filler_bits"],
            "reference_trace": {"base_graph": bg, **seg},
        })
    return tasks


def main() -> None:
    tasks = build()
    OUT.write_text(json.dumps(tasks, indent=2, default=str) + "\n")
    for t in tasks:
        print(f"{t['id']:35s} answer={t['answer']}")
    print(f"Wrote {len(tasks)} tasks to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
