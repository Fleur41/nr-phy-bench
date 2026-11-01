"""Derive TBS inputs from a realistic NR configuration.

Real engineers are not handed n_PRB or N_DMRS^PRB: they derive them from the
carrier and the DM-RS configuration. These helpers do that derivation.

Sources:
  - TS 38.101-1 Table 5.3.2-1   (maximum transmission bandwidth N_RB, FR1)
  - TS 38.211 Section 7.4.1.1.2 and Table 7.4.1.1.2-3 (PDSCH DM-RS positions,
    single-symbol DM-RS)
  - TS 38.211 Tables 7.4.1.1.2-1 / -2 (DM-RS type 1: 6 REs per CDM group per
    symbol; type 2: 4 REs per CDM group per symbol)

EXPERT CHECK: every table below was entered by hand and must be verified
against the spec before the final submission.
"""
from __future__ import annotations

# TS 38.101-1 Table 5.3.2-1: N_RB for FR1, keyed by (SCS kHz, bandwidth MHz).
# Only the commonly deployed bandwidths are listed.
N_RB_FR1 = {
    (15, 5): 25, (15, 10): 52, (15, 15): 79, (15, 20): 106, (15, 25): 133,
    (15, 30): 160, (15, 40): 216, (15, 50): 270,
    (30, 5): 11, (30, 10): 24, (30, 15): 38, (30, 20): 51, (30, 25): 65,
    (30, 30): 78, (30, 40): 106, (30, 50): 133, (30, 60): 162, (30, 70): 189,
    (30, 80): 217, (30, 90): 245, (30, 100): 273,
    (60, 10): 11, (60, 15): 18, (60, 20): 24, (60, 25): 31, (60, 30): 38,
    (60, 40): 51, (60, 50): 65, (60, 60): 79, (60, 70): 93, (60, 80): 107,
    (60, 90): 121, (60, 100): 135,
}

# TS 38.211 Table 7.4.1.1.2-3, PDSCH mapping type A, single-symbol DM-RS.
# l_d -> number of DM-RS symbols for dmrs-AdditionalPosition pos0..pos3.
# (Only the count is needed for the RE overhead; positions are not.)
_TYPE_A_DMRS_SYMBOLS = {
    3: (1, 1, 1, 1), 4: (1, 1, 1, 1), 5: (1, 1, 1, 1), 6: (1, 1, 1, 1),
    7: (1, 1, 1, 1), 8: (1, 2, 2, 2), 9: (1, 2, 2, 2), 10: (1, 2, 3, 3),
    11: (1, 2, 3, 3), 12: (1, 2, 3, 4), 13: (1, 2, 3, 4), 14: (1, 2, 3, 4),
}

RE_PER_CDM_GROUP = {1: 6, 2: 4}  # per PRB per DM-RS symbol


def n_rb(scs_khz: int, bandwidth_mhz: int) -> int:
    return N_RB_FR1[(scs_khz, bandwidth_mhz)]


def type_a_ld(start_symbol: int, length: int) -> int:
    """For mapping type A, l_d counts from the FIRST SYMBOL OF THE SLOT to the
    last PDSCH symbol (TS 38.211 7.4.1.1.2), not just the PDSCH length."""
    return start_symbol + length


def dmrs_symbols_type_a(start_symbol: int, length: int, additional_position: int) -> int:
    return _TYPE_A_DMRS_SYMBOLS[type_a_ld(start_symbol, length)][additional_position]


def dmrs_re_per_prb(dmrs_type: int, cdm_groups_without_data: int, n_dmrs_symbols: int) -> int:
    """N_DMRS^PRB as used in TS 38.214 5.1.3.2: REs per PRB taken by DM-RS,
    including the CDM groups left empty (no data) per cdm_groups_without_data."""
    return RE_PER_CDM_GROUP[dmrs_type] * cdm_groups_without_data * n_dmrs_symbols


def data_re_actual(n_prb: int, n_symb_sh: int, n_dmrs_prb: int) -> int:
    """REs actually carrying PDSCH data (no PT-RS / CSI-RS / reserved REs).
    Unlike N_RE for TBS: no 156 cap and no xOverhead."""
    return (12 * n_symb_sh - n_dmrs_prb) * n_prb
