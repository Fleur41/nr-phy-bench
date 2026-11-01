"""Reference implementation of NR LDPC base-graph selection and code-block segmentation.

Sources:
  - TS 38.212 Section 7.2.2  (LDPC base graph selection, DL-SCH)
  - TS 38.212 Section 6.2.2  (same rule for UL-SCH)
  - TS 38.212 Section 5.2.2  (code block segmentation and CRC attachment)
  - TS 38.212 Table 5.3.2-1  (LDPC lifting sizes Zc)
"""
from __future__ import annotations

import math
from fractions import Fraction

# Table 5.3.2-1: all lifting sizes Z = a * 2^j <= 384
LIFTING_SIZES = sorted(
    a * 2 ** j
    for a in (2, 3, 5, 7, 9, 11, 13, 15)
    for j in range(8)
    if a * 2 ** j <= 384
)


def select_base_graph(tbs: int, code_rate) -> int:
    """Return 1 or 2. tbs = A (payload without CRC), code_rate = R."""
    # Fraction(str(x)) turns float 0.67 into exactly 67/100 (Fraction(0.67) would not).
    R = Fraction(str(code_rate)) if isinstance(code_rate, float) else Fraction(code_rate)
    if tbs <= 292 or (tbs <= 3824 and R <= Fraction(67, 100)) or R <= Fraction(1, 4):
        return 2
    return 1


def segment(tbs: int, base_graph: int) -> dict:
    """Code block segmentation per TS 38.212 5.2.2.

    Input is the TBS (A). The TB CRC is added first: 24 bits if A > 3824, else 16.
    Returns C, K' (bits per CB incl. CB CRC, before filler), Kb, Zc, K, and filler bits F.
    """
    tb_crc = 24 if tbs > 3824 else 16
    B = tbs + tb_crc
    k_cb = 8448 if base_graph == 1 else 3840

    if B <= k_cb:
        L, C, B_prime = 0, 1, B
    else:
        L = 24
        C = math.ceil(B / (k_cb - L))
        B_prime = B + C * L

    k_prime = B_prime // C  # spec guarantees divisibility for valid TBS values

    if base_graph == 1:
        kb = 22
    elif B > 640:
        kb = 10
    elif B > 560:
        kb = 9
    elif B > 192:
        kb = 8
    else:
        kb = 6

    zc = min(z for z in LIFTING_SIZES if kb * z >= k_prime)
    K = (22 if base_graph == 1 else 10) * zc

    return {
        "A": tbs, "TB_CRC": tb_crc, "B": B, "L": L, "C": C, "B_prime": B_prime,
        "K_prime": k_prime, "Kb": kb, "Zc": zc, "K": K, "filler_bits": K - k_prime,
    }


def rate_match_lengths(G: int, C: int, num_layers: int, qm: int) -> list[int]:
    """E_r for every code block, TS 38.212 5.4.2.1 (all C code blocks scheduled, C' = C).

    The first C' - mod(G/(NL*Qm), C') blocks get the floor size, the rest the ceil size.
    """
    unit = num_layers * qm
    assert G % unit == 0
    symbols = G // unit
    n_small = C - symbols % C
    small = unit * (symbols // C)
    large = unit * -(-symbols // C)
    return [small if j < n_small else large for j in range(C)]


# TS 38.212 Table 5.4.2.1-1: n_PRB,LBRM from the maximum number of PRBs across all
# configured DL BWPs of the carrier. (upper bound of range, n_PRB_LBRM)
_N_PRB_LBRM = [(32, 32), (66, 66), (107, 107), (135, 135), (162, 162), (217, 217), (10**9, 273)]

R_LBRM = Fraction(2, 3)


def n_prb_lbrm(max_bwp_prbs: int) -> int:
    """Table 5.4.2.1-1: <33 -> 32, 33..66 -> 66, 67..107 -> 107, 108..135 -> 135,
    136..162 -> 162, 163..217 -> 217, >217 -> 273."""
    for upper, value in _N_PRB_LBRM:
        if max_bwp_prbs <= upper:
            return value
    raise ValueError(max_bwp_prbs)


def tbs_lbrm(max_bwp_prbs: int, max_layers: int, mcs_table: int) -> int:
    """TBS_LBRM per TS 38.212 5.4.2.1 (DL-SCH): TBS procedure of TS 38.214 5.1.3.2 with
    v = min(maxMIMO-Layers, 4), the highest modulation order of the configured MCS table,
    R = 948/1024, and N_RE = 156 * n_PRB,LBRM."""
    from reference.tbs import compute_tbs

    highest_mcs = {1: 28, 2: 27}[mcs_table]  # both rows have R x 1024 = 948
    # 13 symbols with no DM-RS gives N'_RE = 156, so N_RE = 156 * n_PRB_LBRM exactly.
    return compute_tbs(n_prb_lbrm(max_bwp_prbs), 13, 0, highest_mcs, mcs_table,
                       min(max_layers, 4), 0)


def n_cb_lbrm(base_graph: int, zc: int, C: int, tbs_lbrm_bits: int) -> int:
    """N_cb = min(N, N_ref), N_ref = floor(TBS_LBRM / (C * R_LBRM))."""
    n = (66 if base_graph == 1 else 50) * zc
    n_ref = math.floor(Fraction(tbs_lbrm_bits) / (C * R_LBRM))
    return min(n, n_ref)


# TS 38.212 Table 5.4.2.1-2: k0 numerators (BG1 over 66*Zc, BG2 over 50*Zc)
_K0_NUM = {1: (0, 17, 33, 56), 2: (0, 13, 25, 43)}


def circular_buffer_k0(base_graph: int, zc: int, rv: int, n_cb: int | None = None) -> int:
    """Starting position k0 in the circular buffer. Without limited-buffer rate
    matching, N_cb = N = 66*Zc (BG1) or 50*Zc (BG2)."""
    n = (66 if base_graph == 1 else 50) * zc
    n_cb = n if n_cb is None else n_cb
    return (_K0_NUM[base_graph][rv] * n_cb // n) * zc
