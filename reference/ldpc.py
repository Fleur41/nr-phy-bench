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
