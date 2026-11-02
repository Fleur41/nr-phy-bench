"""Context rules: WHICH TBS rules apply, given how the PDSCH was scheduled.

These are the conditions an engineer must check before running the TBS procedure.
They are short in the spec, but easy to miss because they override the UE's
configured values.

Sources:
  - TS 38.214 Section 5.1.3.1: MCS index table selection. Table 5.1.3.1-2 (256QAM) is
    used only when mcs-Table = qam256 AND the PDSCH is scheduled by DCI format 1_1
    (CRC scrambled by C-RNTI). DCI format 1_0 (e.g. P-RNTI, SI-RNTI, RA-RNTI) uses
    Table 5.1.3.1-1 even when qam256 is configured.
  - TS 38.214 Section 5.1.3.2: "If the PDSCH is scheduled by PDCCH with a CRC scrambled
    by SI-RNTI, RA-RNTI, MsgB-RNTI or P-RNTI, N_oh^PRB is assumed to be 0."
  - TS 38.214 Table 5.1.3.2-2: TB scaling field -> scaling factor S, applied for DCI
    format 1_0 with CRC scrambled by P-RNTI, RA-RNTI or MsgB-RNTI.
  - TS 38.211 Table 7.3.1.3-1: codeword-to-layer mapping. With more than 4 layers there
    are two codewords; codeword 0 gets floor(v/2) layers and codeword 1 gets ceil(v/2).

EXPERT CHECK: the conditions above are paraphrased from the spec and must be verified
against the spec text before the final submission.
"""
from __future__ import annotations

from fractions import Fraction

# TS 38.214 Table 5.1.3.2-2
TB_SCALING = {"00": Fraction(1), "01": Fraction(1, 2), "10": Fraction(1, 4)}

SCALED_RNTIS = {"P-RNTI", "RA-RNTI", "MsgB-RNTI"}
NO_XOVERHEAD_RNTIS = {"SI-RNTI", "RA-RNTI", "MsgB-RNTI", "P-RNTI"}


def pdsch_mcs_table(dci_format: str, rnti: str, configured: str) -> int:
    """1 = Table 5.1.3.1-1 (qam64), 2 = Table 5.1.3.1-2 (qam256)."""
    return 2 if configured == "qam256" and dci_format == "1_1" and rnti == "C-RNTI" else 1


def effective_xoverhead(rnti: str, configured: int) -> int:
    return 0 if rnti in NO_XOVERHEAD_RNTIS else configured


def tb_scaling(dci_format: str, rnti: str, field: str | None) -> Fraction:
    if dci_format == "1_0" and rnti in SCALED_RNTIS and field is not None:
        return TB_SCALING[field]
    return Fraction(1)


def codeword_layers(total_layers: int) -> tuple[int, ...]:
    """Layers per codeword (TS 38.211 Table 7.3.1.3-1)."""
    if total_layers <= 4:
        return (total_layers,)
    return (total_layers // 2, total_layers - total_layers // 2)
