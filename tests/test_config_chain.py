"""Tests for configuration-derived inputs and rate matching."""
import itertools

from reference import nr_config as cfg
from reference.ldpc import circular_buffer_k0, rate_match_lengths


def test_n_rb_well_known():
    assert cfg.n_rb(30, 100) == 273
    assert cfg.n_rb(15, 20) == 106
    assert cfg.n_rb(30, 40) == 106


def test_type_a_ld_counts_from_slot_start():
    assert cfg.type_a_ld(2, 8) == 10
    assert cfg.dmrs_symbols_type_a(2, 8, 2) == 3   # l_d = 10, pos2 -> l0, 6, 9
    assert cfg.dmrs_symbols_type_a(0, 8, 2) == 2   # l_d = 8,  pos2 -> l0, 7


def test_dmrs_re_per_prb():
    assert cfg.dmrs_re_per_prb(1, 2, 1) == 12
    assert cfg.dmrs_re_per_prb(1, 1, 1) == 6
    assert cfg.dmrs_re_per_prb(2, 3, 2) == 24


def test_rate_matching_partitions_G():
    for G_sym, C, nl, qm in itertools.product((1000, 1001, 4096, 12345), (1, 3, 7, 104), (1, 2, 4), (2, 4, 6, 8)):
        G = G_sym * nl * qm
        E = rate_match_lengths(G, C, nl, qm)
        assert sum(E) == G
        assert E == sorted(E) and E[-1] - E[0] in (0, nl * qm)
        assert all(e % (nl * qm) == 0 for e in E)


def test_k0_without_lbrm():
    assert circular_buffer_k0(1, 384, 0) == 0
    assert circular_buffer_k0(1, 384, 2) == 33 * 384
    assert circular_buffer_k0(2, 352, 3) == 43 * 352


def test_n_prb_lbrm_table_boundaries():
    from reference.ldpc import n_prb_lbrm
    assert [n_prb_lbrm(x) for x in (24, 32, 33, 66, 67, 106, 107, 108, 133, 135, 136, 162, 163, 217, 218, 273)] == \
           [32, 32, 66, 66, 107, 107, 107, 135, 135, 135, 162, 162, 217, 217, 273, 273]


def test_lbrm_hand_worked():
    # 50 MHz @ 30 kHz (133 PRB) -> n_PRB,LBRM = 135; v = min(8, 4) = 4; 256QAM, R = 948/1024
    # N_info = 156*135*948/1024*8*4 = 623,902.5 -> TBS_LBRM = 622,760 (reference)
    # C = 53, N_ref = floor(622760 / (53 * 2/3)) = floor(17625.28) = 17625 < N = 66*384
    # k0(rv3) = floor(56 * 17625 / (66 * 384)) * 384 = 38 * 384 = 14592
    from reference.ldpc import circular_buffer_k0, n_cb_lbrm, tbs_lbrm
    assert tbs_lbrm(133, 8, 2) == 622760
    assert n_cb_lbrm(1, 384, 53, 622760) == 17625
    assert circular_buffer_k0(1, 384, 3, 17625) == 14592
