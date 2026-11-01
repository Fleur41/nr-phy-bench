"""Sanity tests for the reference calculators.

Run with:  python -m pytest -q
"""
import itertools

from reference.ldpc import LIFTING_SIZES, segment, select_base_graph
from reference.tbs import MCS_TABLES, TBS_TABLE, compute_tbs


def test_table_sizes():
    assert len(TBS_TABLE) == 93
    assert TBS_TABLE == sorted(TBS_TABLE)
    assert len(LIFTING_SIZES) == 51


def test_tbs_small_hand_worked():
    # 1 PRB, 12 symbols, 12 DMRS REs, MCS 0 (table 1): N_info ~= 30.9 -> TBS 24
    assert compute_tbs(1, 12, 12, 0) == 24


def test_tbs_peak_100mhz_4layer_256qam():
    # 273 PRB, 12 symb, 12 DMRS REs, MCS 27 table 2, 4 layers.
    # Hand-worked: N_info=1067566.5, n=15, N'_info=1081344, C=129 -> 1081512
    tbs, trace = compute_tbs(273, 12, 12, 27, mcs_table=2, num_layers=4, return_trace=True)
    assert trace["N_info_prime"] == 1081344
    assert trace["C"] == 129
    assert tbs == 1081512


def test_tbs_invariants_and_segmentation_divisibility():
    """For every TBS the spec can produce, segmentation must split evenly into code blocks."""
    for table, mcs_map in MCS_TABLES.items():
        for mcs, n_prb, layers in itertools.product(mcs_map, (1, 5, 24, 51, 106, 273), (1, 2, 4)):
            tbs = compute_tbs(n_prb, 12, 12, mcs, mcs_table=table, num_layers=layers)
            assert tbs % 8 == 0
            qm, r1024 = mcs_map[mcs]
            bg = select_base_graph(tbs, r1024 / 1024)
            seg = segment(tbs, bg)
            assert seg["B_prime"] % seg["C"] == 0, (table, mcs, n_prb, layers, seg)
            assert seg["K"] >= seg["K_prime"]


def test_base_graph_rules():
    assert select_base_graph(292, 0.9) == 2       # small TB
    assert select_base_graph(3824, 0.67) == 2     # medium TB, R <= 0.67
    assert select_base_graph(3824, 0.68) == 1
    assert select_base_graph(100000, 0.25) == 2   # low rate
    assert select_base_graph(100000, 0.26) == 1


def test_segmentation_bg1_large():
    # A=1081512, BG1: B=1081536, C=ceil(B/8424)=129, B'=B+129*24
    seg = segment(1081512, 1)
    assert seg["C"] == 129
    assert seg["K_prime"] == (1081536 + 129 * 24) // 129
    assert seg["Zc"] == 384 and seg["K"] == 8448
