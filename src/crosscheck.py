"""Independent cross-check of the golden answers in tasks/tasks.json.

The golden answers come from reference/. This script recomputes them WITHOUT importing
reference/, so that a bug there cannot silently confirm itself:

- TBS (TS 38.214 5.1.3.2) and code-block segmentation (TS 38.212 5.2.2, 7.2.2: base
  graph, C, Z_c, K, filler bits) come from the open-source py3gpp library
  (nrTBS, nrDLSCHInfo, a Python port of the MATLAB 5G Toolbox functions).
- G, the rate-matching output lengths E (TS 38.212 5.4.2.1), LBRM N_cb and k0 are
  re-derived below from the spec formulas, written separately from reference/ldpc.py.

Limitation: the small spec tables used to derive inputs (MCS rows, N_RB, DM-RS symbol
count, n_PRB,LBRM) are typed in below. They were re-entered from the spec rather than
copied from reference/, but they are not checked against an external library.

Usage (optional dependency, not needed to run the eval):
    pip install -r requirements-crosscheck.txt
    python -m src.crosscheck
Exits non-zero if any golden answer or trace value disagrees.
"""
from __future__ import annotations

import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
from py3gpp.nrDLSCHInfo import nrDLSCHInfo
from py3gpp.nrTBS import nrTBS as _nrTBS

TASKS = Path(__file__).resolve().parent.parent / "tasks" / "tasks.json"

# TS 38.214 Table 5.1.3.1-1 (mcs_table 1) and 5.1.3.1-2 (mcs_table 2): (Qm, R x 1024).
# Only the rows the tasks use.
MCS = {
    1: {2: (2, 193), 15: (4, 616), 16: (4, 658), 19: (6, 517), 20: (6, 567)},
    2: {20: (8, 682.5), 24: (8, 841), 25: (8, 885), 27: (8, 948)},
}
MOD = {2: "QPSK", 4: "16QAM", 6: "64QAM", 8: "256QAM"}
# TS 38.101-1 Table 5.3.2-1: N_RB for (bandwidth MHz, SCS kHz). Only the entries used.
N_RB = {(20, 15): 106, (40, 30): 106, (50, 30): 133, (80, 30): 217, (100, 30): 273}
# TS 38.212 Table 5.4.2.1-1: (max BWP PRBs upper bound, n_PRB,LBRM)
N_PRB_LBRM = [(32, 32), (66, 66), (107, 107), (135, 135), (162, 162), (217, 217), (math.inf, 273)]
# TS 38.212 Table 5.4.2.1-2: k0 numerators (BG1 over 66*Zc, BG2 over 50*Zc)
K0_NUM = {1: (0, 17, 33, 56), 2: (0, 13, 25, 43)}


def nr_tbs(mod: str, layers: int, n_prb: int, re_per_prb: int, rate: float, x_oh: int = 0) -> int:
    return int(np.atleast_1d(_nrTBS(mod, layers, n_prb, re_per_prb, rate, x_oh))[0])


def dmrs_symbols_type_a(start: int, length: int, add_pos: int) -> int:
    """TS 38.211 Table 7.4.1.1.2-3, PDSCH mapping type A, single-symbol DM-RS.
    l_d is counted from the start of the slot (S + L)."""
    ld = start + length
    if ld < 8:
        return 1
    if ld < 10:
        return min(add_pos, 1) + 1
    if ld < 12:
        return min(add_pos, 2) + 1
    return add_pos + 1


def recompute(params: dict) -> dict:
    """Recompute every quantity the task family can ask for."""
    qm, r1024 = MCS[params["mcs_table"]][params["mcs_index"]]
    rate = r1024 / 1024

    if "tbs" in params:  # pure LDPC task: TBS given
        info = nrDLSCHInfo(params["tbs"], rate)
        return {"filler_bits": int(info["F"]), "C": int(info["C"])}

    if "n_prb" in params:  # L1: explicit inputs
        n_prb, n_symb = params["n_prb"], params["n_symb_sh"]
        n_dmrs, x_oh = params["n_dmrs_prb"], params["n_oh_prb"]
    else:  # L2+: derive from the configuration
        n_prb = N_RB[(params["bandwidth_mhz"], params["scs_khz"])]
        n_symb = params["length"]
        re_per_cdm_group = 6 if params["dmrs_type"] == 1 else 4
        n_dmrs = re_per_cdm_group * params["cdm_groups_without_data"] * dmrs_symbols_type_a(
            params["start_symbol"], params["length"], params["additional_position"])
        x_oh = params["xoverhead"]

    layers = params["num_layers"]
    re_per_prb = 12 * n_symb - n_dmrs
    tbs = nr_tbs(MOD[qm], layers, n_prb, re_per_prb, rate, x_oh)
    info = nrDLSCHInfo(tbs, rate)
    C, zc, bg, n = int(info["C"]), int(info["Zc"]), int(info["BGN"]), int(info["N"])

    # TS 38.212 5.4.2.1: G counts the REs actually available (xOverhead only affects TBS)
    G = n_prb * re_per_prb * qm * layers
    q = G // (layers * qm)
    out = {
        "tbs": tbs, "C": C, "filler_bits": int(info["F"]), "G": G,
        "E_first": layers * qm * (q // C),
        "E_last": layers * qm * math.ceil(Fraction(q, C)),
    }

    if "rv" in params:  # limited-buffer rate matching
        n_prb_lbrm = next(v for upper, v in N_PRB_LBRM if n_prb <= upper)
        lbrm_qm = 8 if params["mcs_table"] == 2 else 6
        tbs_lbrm = nr_tbs(MOD[lbrm_qm], min(params["max_mimo_layers"], 4), n_prb_lbrm, 156, 948 / 1024)
        n_ref = math.floor(Fraction(tbs_lbrm) / (C * Fraction(2, 3)))
        n_cb = min(n, n_ref)
        den = 66 if bg == 1 else 50
        out.update(TBS_LBRM=tbs_lbrm, N_cb=n_cb,
                   k0=(K0_NUM[bg][params["rv"]] * n_cb // (den * zc)) * zc)
    return out


def asked_quantity(category: str) -> str:
    """Which recomputed quantity a task's answer is, from its category
    (tbs, ldpc, config-tbs, config-filler_bits, config-E_first, config-E_last, config-k0)."""
    name = category.removeprefix("config-")
    return {"ldpc": "filler_bits"}.get(name, name)


def trace_value(trace: dict, key: str):
    """Find `key` in a task's reference trace (top level or nested)."""
    aliases = {"tbs": ("tbs", "TBS"), "C": ("C",), "filler_bits": ("filler_bits",)}
    for k in aliases.get(key, (key,)):
        if k in trace:
            return trace[k]
        for sub in trace.values():
            if isinstance(sub, dict) and k in sub:
                return sub[k]
    return None


def main() -> int:
    tasks = json.loads(TASKS.read_text())
    failures = 0
    for task in tasks:
        got = recompute(task["params"])
        diffs = {k: (v, trace_value(task["reference_trace"], k)) for k, v in got.items()
                 if trace_value(task["reference_trace"], k) not in (None, v)}
        # The golden answer must equal the recomputed value of the quantity asked for
        answer_ok = got.get(asked_quantity(task["category"])) == task["answer"]
        ok = answer_ok and not diffs
        failures += not ok
        detail = ", ".join(f"{k}={v}" for k, v in got.items())
        print(f"{'OK      ' if ok else 'MISMATCH'} {task['id']:32s} "
              f"{asked_quantity(task['category'])}={task['answer']:<8} [{detail}]")
        if diffs:
            print(f"         differs from reference trace (crosscheck, reference): {diffs}")
    print(f"\n{len(tasks) - failures}/{len(tasks)} golden answers independently confirmed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
