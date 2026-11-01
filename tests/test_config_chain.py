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
