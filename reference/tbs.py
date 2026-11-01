"""Reference implementation of NR PDSCH/PUSCH Transport Block Size (TBS).

Source: 3GPP TS 38.214, Section 5.1.3.2 (TBS determination) and
Tables 5.1.3.1-1 / 5.1.3.1-2 (MCS index tables).

This file produces the golden answers for TBS tasks. Every step is
kept separate and returned in a trace so a human expert can check
each intermediate value against the spec.
"""
from __future__ import annotations

import math
from fractions import Fraction

# TS 38.214 Table 5.1.3.1-1: MCS index table 1 for PDSCH (up to 64QAM).
# index -> (modulation order Qm, target code rate R x 1024)
MCS_TABLE_1 = {
    0: (2, 120), 1: (2, 157), 2: (2, 193), 3: (2, 251), 4: (2, 308),
    5: (2, 379), 6: (2, 449), 7: (2, 526), 8: (2, 602), 9: (2, 679),
    10: (4, 340), 11: (4, 378), 12: (4, 434), 13: (4, 490), 14: (4, 553),
    15: (4, 616), 16: (4, 658), 17: (6, 438), 18: (6, 466), 19: (6, 517),
    20: (6, 567), 21: (6, 616), 22: (6, 666), 23: (6, 719), 24: (6, 772),
    25: (6, 822), 26: (6, 873), 27: (6, 910), 28: (6, 948),
}

# TS 38.214 Table 5.1.3.1-2: MCS index table 2 for PDSCH (up to 256QAM).
MCS_TABLE_2 = {
    0: (2, 120), 1: (2, 193), 2: (2, 308), 3: (2, 449), 4: (2, 602),
    5: (4, 378), 6: (4, 434), 7: (4, 490), 8: (4, 553), 9: (4, 616),
    10: (4, 658), 11: (6, 466), 12: (6, 517), 13: (6, 567), 14: (6, 616),
    15: (6, 666), 16: (6, 719), 17: (6, 772), 18: (6, 822), 19: (6, 873),
    20: (8, Fraction(1365, 2)), 21: (8, 711), 22: (8, 754), 23: (8, 797),
    24: (8, 841), 25: (8, 885), 26: (8, Fraction(1833, 2)), 27: (8, 948),
}

MCS_TABLES = {1: MCS_TABLE_1, 2: MCS_TABLE_2}

# TS 38.214 Table 5.1.3.2-1: TBS for N_info <= 3824.
TBS_TABLE = [
    24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144,
    152, 160, 168, 176, 184, 192, 208, 224, 240, 256, 272, 288, 304, 320,
    336, 352, 368, 384, 408, 432, 456, 480, 504, 528, 552, 576, 608, 640,
    672, 704, 736, 768, 808, 848, 888, 928, 984, 1032, 1064, 1128, 1160,
    1192, 1224, 1256, 1288, 1320, 1352, 1416, 1480, 1544, 1608, 1672, 1736,
    1800, 1864, 1928, 2024, 2088, 2152, 2216, 2280, 2408, 2472, 2536, 2600,
    2664, 2728, 2792, 2856, 2976, 3104, 3240, 3368, 3496, 3624, 3752, 3824,
]


def _round_half_up(x: Fraction) -> int:
    """Spec says 'ties in the round function are broken towards the next largest integer'."""
    return math.floor(x + Fraction(1, 2))


def compute_tbs(
    n_prb: int,
    n_symb_sh: int,
    n_dmrs_prb: int,
    mcs_index: int,
    mcs_table: int = 1,
    num_layers: int = 1,
    n_oh_prb: int = 0,
    return_trace: bool = False,
):
    """Compute TBS per TS 38.214 5.1.3.2.

    n_prb       : number of allocated PRBs
    n_symb_sh   : number of PDSCH/PUSCH symbols in the slot
    n_dmrs_prb  : DM-RS REs per PRB in the allocation (incl. CDM-group overhead)
    mcs_index   : I_MCS
    mcs_table   : 1 (64QAM) or 2 (256QAM)
    num_layers  : v
    n_oh_prb    : xOverhead (0, 6, 12 or 18)
    """
    qm, r1024 = MCS_TABLES[mcs_table][mcs_index]
    R = Fraction(r1024) / 1024  # exact arithmetic, no float rounding surprises

    # Step 1: number of REs
    n_re_prime = 12 * n_symb_sh - n_dmrs_prb - n_oh_prb
    n_re = min(156, n_re_prime) * n_prb

    # Step 2: intermediate number of information bits
    n_info = n_re * R * qm * num_layers

    trace = {
        "Qm": qm, "R": float(R), "N_RE_prime": n_re_prime, "N_RE": n_re,
        "N_info": float(n_info),
    }

    if n_info <= 3824:
        # Step 3
        n = max(3, math.floor(math.log2(n_info)) - 6)
        n_info_q = max(24, (2 ** n) * math.floor(n_info / (2 ** n)))
        tbs = next(t for t in TBS_TABLE if t >= n_info_q)
        trace.update(step=3, n=n, N_info_prime=n_info_q)
    else:
        # Step 4
        n = math.floor(math.log2(n_info - 24)) - 5
        n_info_q = max(3840, (2 ** n) * _round_half_up((n_info - 24) / (2 ** n)))
        if R <= Fraction(1, 4):
            c = math.ceil(Fraction(n_info_q + 24, 3816))
        elif n_info_q > 8424:
            c = math.ceil(Fraction(n_info_q + 24, 8424))
        else:
            c = 1
        tbs = 8 * c * math.ceil(Fraction(n_info_q + 24, 8 * c)) - 24
        trace.update(step=4, n=n, N_info_prime=n_info_q, C=c)

    trace["TBS"] = tbs
    return (tbs, trace) if return_trace else tbs
