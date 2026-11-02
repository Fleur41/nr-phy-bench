"""Tests for the L5 context rules (reference/context.py) and TB scaling in compute_tbs."""
from fractions import Fraction

from reference.context import (codeword_layers, effective_xoverhead, pdsch_mcs_table,
                               tb_scaling)
from reference.tbs import compute_tbs


def test_mcs_table_256qam_only_for_dci_1_1_c_rnti():
    assert pdsch_mcs_table("1_1", "C-RNTI", "qam256") == 2
    assert pdsch_mcs_table("1_0", "P-RNTI", "qam256") == 1   # paging ignores qam256
    assert pdsch_mcs_table("1_0", "C-RNTI", "qam256") == 1   # fallback DCI ignores it too
    assert pdsch_mcs_table("1_1", "C-RNTI", "qam64") == 1


def test_xoverhead_ignored_for_broadcast_rntis():
    for rnti in ("P-RNTI", "SI-RNTI", "RA-RNTI", "MsgB-RNTI"):
        assert effective_xoverhead(rnti, 6) == 0
    assert effective_xoverhead("C-RNTI", 6) == 6


def test_tb_scaling_table_5_1_3_2_2():
    assert tb_scaling("1_0", "P-RNTI", "00") == 1
    assert tb_scaling("1_0", "P-RNTI", "01") == Fraction(1, 2)
    assert tb_scaling("1_0", "RA-RNTI", "10") == Fraction(1, 4)
    assert tb_scaling("1_0", "SI-RNTI", "01") == 1          # SI-RNTI is not scaled
    assert tb_scaling("1_1", "C-RNTI", None) == 1


def test_codeword_to_layer_mapping_table_7_3_1_3_1():
    assert codeword_layers(4) == (4,)
    assert [codeword_layers(v) for v in (5, 6, 7, 8)] == [(2, 3), (3, 3), (3, 4), (4, 4)]


def test_scaling_moves_n_info_into_table_branch():
    # Paging task: S = 1/2 gives N_info = 3819.375 <= 3824 (step 3), TBS 3824.
    tbs, trace = compute_tbs(48, 12, 24, 9, 1, 1, 0, scaling=Fraction(1, 2), return_trace=True)
    assert trace["step"] == 3 and trace["N_info"] == 3819.375 and tbs == 3824
    # Without scaling the same allocation goes through step 4.
    assert compute_tbs(48, 12, 24, 9, 1, 1, 0) == 7552


def test_scaling_one_is_unchanged():
    assert compute_tbs(52, 14, 6, 20, 1, 2, 0, scaling=1) == compute_tbs(52, 14, 6, 20, 1, 2, 0)
