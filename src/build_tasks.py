"""Generate tasks/tasks.json from task parameters.

Golden answers are never typed by hand: each one is computed by the
reference implementation in reference/. To add a task, add an entry
to TBS_TASKS or LDPC_TASKS and re-run:

    python -m src.build_tasks
"""
from __future__ import annotations

import json
from pathlib import Path

from reference import nr_config as cfg
from reference.ldpc import (circular_buffer_k0, n_cb_lbrm, rate_match_lengths, segment,
                             select_base_graph, tbs_lbrm)
from reference.tbs import MCS_TABLES, compute_tbs

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tasks" / "tasks.json"

ANSWER_FORMAT = (
    "Show your working, then end your response with a final line in exactly "
    "this format (digits only, no commas or units):\nFINAL ANSWER: <integer>"
)

MCS_TABLE_NAMES = {
    1: "TS 38.214 Table 5.1.3.1-1 (MCS index table 1, up to 64QAM)",
    2: "TS 38.214 Table 5.1.3.1-2 (MCS index table 2, up to 256QAM)",
}

# Each entry: id, trap (what the task is designed to catch), and parameters.
TBS_TASKS = [
    {
        "id": "tbs-156-cap",
        "trap": "N'_RE = 162 exceeds 156 and must be capped at 156 per PRB",
        "params": dict(n_prb=52, n_symb_sh=14, n_dmrs_prb=6, mcs_index=20,
                       mcs_table=1, num_layers=2, n_oh_prb=0),
    },
    {
        "id": "tbs-low-rate-segmentation",
        "trap": "R <= 1/4 in step 4: C uses 3816, not the 8424 branch",
        "params": dict(n_prb=273, n_symb_sh=13, n_dmrs_prb=12, mcs_index=2,
                       mcs_table=1, num_layers=4, n_oh_prb=0),
    },
    {
        "id": "tbs-256qam-xoverhead",
        "trap": "xOverhead = 6 must be subtracted; 256QAM table 2 must be used",
        "params": dict(n_prb=106, n_symb_sh=12, n_dmrs_prb=12, mcs_index=20,
                       mcs_table=2, num_layers=2, n_oh_prb=6),
    },
]

LDPC_TASKS = [
    {
        "id": "ldpc-filler-bits-bg2-large-tb",
        "trap": "Large TB but R <= 1/4 forces base graph 2 (K_cb = 3840), not BG1",
        "tbs": 59496,
        "mcs_index": 2,
        "mcs_table": 1,
    },
]


# Level 2/3 tasks: the model gets a realistic configuration, not the formula inputs.
# It must derive n_PRB, the DM-RS overhead and N_symb^sh itself (level 2), and
# for level 3 carry the result through LDPC segmentation or rate matching.
# Level 4 adds limited buffer rate matching (LBRM), which needs a second, hypothetical
# TBS (TBS_LBRM) and the circular-buffer start position k0 for a redundancy version.
# question: "tbs" | "filler_bits" | "E_first" | "E_last" | "k0"
CONFIG_TASKS = [
    {
        "id": "cfg-tbs-100mhz-256qam-4layer", "level": 2, "question": "tbs",
        "trap": "Derive n_PRB = 273 (100 MHz @ 30 kHz) and 3 DM-RS symbols for pos2 "
                "(l_d = 14) x 12 REs = 36 REs/PRB",
        "config": dict(bandwidth_mhz=100, scs_khz=30, start_symbol=2, length=12,
                       dmrs_type=1, cdm_groups_without_data=2, additional_position=2,
                       mcs_index=27, mcs_table=2, num_layers=4, xoverhead=0),
    },
    {
        "id": "cfg-tbs-dmrs-type2-xoverhead", "level": 2, "question": "tbs",
        "trap": "DM-RS type 2 has 4 REs per CDM group: 3 groups x 4 x 2 symbols = 24; "
                "xOverhead 12 also applies",
        "config": dict(bandwidth_mhz=40, scs_khz=30, start_symbol=1, length=13,
                       dmrs_type=2, cdm_groups_without_data=3, additional_position=1,
                       mcs_index=16, mcs_table=1, num_layers=2, xoverhead=12),
    },
    {
        "id": "cfg-tbs-156-cap-derived", "level": 2, "question": "tbs",
        "trap": "14 symbols with only 6 DM-RS REs gives N'_RE = 162, which must be "
                "capped at 156 (the cap is hidden behind derived inputs)",
        "config": dict(bandwidth_mhz=20, scs_khz=15, start_symbol=0, length=14,
                       dmrs_type=1, cdm_groups_without_data=1, additional_position=0,
                       mcs_index=19, mcs_table=1, num_layers=2, xoverhead=0),
    },
    {
        "id": "cfg-filler-bits-ld-trap", "level": 3, "question": "filler_bits",
        "trap": "Type A l_d counts from slot start: S=2, L=8 gives l_d = 10, so pos2 has "
                "3 DM-RS symbols (using l_d = L = 8 gives 2 and F = 32 instead of 136)",
        "config": dict(bandwidth_mhz=50, scs_khz=30, start_symbol=2, length=8,
                       dmrs_type=1, cdm_groups_without_data=2, additional_position=2,
                       mcs_index=15, mcs_table=1, num_layers=2, xoverhead=0),
    },
    {
        "id": "cfg-ratematch-E-xoverhead", "level": 3, "question": "E_first",
        "trap": "G uses the REs actually available; xOverhead only affects TBS. "
                "Applying xOverhead to G gives 12720 instead of 13992",
        "config": dict(bandwidth_mhz=40, scs_khz=30, start_symbol=1, length=13,
                       dmrs_type=2, cdm_groups_without_data=3, additional_position=1,
                       mcs_index=16, mcs_table=1, num_layers=2, xoverhead=12),
    },
    {
        "id": "cfg-ratematch-E-last-cb", "level": 3, "question": "E_last",
        "trap": "G/(NL*Qm) is not divisible by C: the last code blocks get the ceil "
                "size (9088), the first ones the floor size (9056)",
        "config": dict(bandwidth_mhz=100, scs_khz=30, start_symbol=2, length=12,
                       dmrs_type=1, cdm_groups_without_data=2, additional_position=2,
                       mcs_index=27, mcs_table=2, num_layers=4, xoverhead=0),
    },
    {
        "id": "lbrm-k0-rv3-maxmimo8", "level": 4, "question": "k0",
        "trap": "TBS_LBRM uses v = min(maxMIMO-Layers, 4) = 4, not 8, and n_PRB,LBRM = 135; "
                "N_cb = N_ref = 17625 < N, so k0 = 14592 (v = 8 or ignoring LBRM gives 21504)",
        "config": dict(bandwidth_mhz=50, scs_khz=30, start_symbol=2, length=12,
                       dmrs_type=1, cdm_groups_without_data=2, additional_position=1,
                       mcs_index=25, mcs_table=2, num_layers=4, xoverhead=0,
                       max_mimo_layers=8, rv=3),
    },
    {
        "id": "lbrm-k0-rv2-2layer", "level": 4, "question": "k0",
        "trap": "N_ref = floor(TBS_LBRM / (C x 2/3)) = 18297 < N = 25344 is not a multiple "
                "of Z_c, so k0 needs the floor: 8832 (ignoring LBRM gives 12672)",
        "config": dict(bandwidth_mhz=80, scs_khz=30, start_symbol=2, length=12,
                       dmrs_type=1, cdm_groups_without_data=2, additional_position=1,
                       mcs_index=24, mcs_table=2, num_layers=2, xoverhead=0,
                       max_mimo_layers=2, rv=2),
    },
]


# Level 5 tasks: context rules. The procedure is the same TBS procedure, but HOW the PDSCH
# was scheduled (DCI format, RNTI, number of codewords) changes which inputs apply,
# overriding values that are configured for the UE. The model must recognise that.
CONTEXT_TASKS = [
    {
        "id": "ctx-paging-tb-scaling", "level": 5, "question": "tbs",
        "trap": "Paging (DCI 1_0, P-RNTI): MCS table 1 must be used although qam256 is "
                "configured; xOverhead is assumed 0 for P-RNTI; S = 0.5 from the TB scaling "
                "field moves N_info (3819.375) below 3824 into the table branch. Ignoring S "
                "gives 7552, using the 256QAM table 6912, applying xOverhead 3624, all three "
                "mistakes 13064",
        "context": dict(dci_format="1_0", rnti="P-RNTI", tb_scaling_field="01",
                        configured_mcs_table="qam256", configured_xoverhead=6,
                        n_prb=48, n_symb_sh=12, n_dmrs_prb=24, mcs_index=9, total_layers=1,
                        codeword=0),
    },
    {
        "id": "ctx-2cw-7layer-tb2", "level": 5, "question": "tbs",
        "trap": "7 layers means two codewords; codeword 1 (TB 2) is mapped to ceil(7/2) = 4 "
                "layers (TS 38.211 Table 7.3.1.3-1) and uses its own I_MCS = 17 (256QAM table). "
                "7 layers gives 1147488, the 3 layers of codeword 0 gives 491800, TB 1's "
                "I_MCS 852696; double-symbol DM-RS takes 24 REs/PRB (12 gives 704904)",
        "context": dict(dci_format="1_1", rnti="C-RNTI", tb_scaling_field=None,
                        configured_mcs_table="qam256", configured_xoverhead=0,
                        bandwidth_mhz=100, scs_khz=30, start_symbol=1, length=13,
                        dmrs_type=1, dmrs_symbols=2, cdm_groups_without_data=2,
                        mcs_index_tb1=22, mcs_index_tb2=17, total_layers=7, codeword=1),
    },
]


def solve_context(c: dict) -> dict:
    """Apply the context rules, then the ordinary TBS procedure."""
    from reference import context as ctx

    mcs_table = ctx.pdsch_mcs_table(c["dci_format"], c["rnti"], c["configured_mcs_table"])
    x_oh = ctx.effective_xoverhead(c["rnti"], c["configured_xoverhead"])
    S = ctx.tb_scaling(c["dci_format"], c["rnti"], c["tb_scaling_field"])
    layers = ctx.codeword_layers(c["total_layers"])[c["codeword"]]
    if "n_prb" in c:
        n_prb, n_symb, n_dmrs = c["n_prb"], c["n_symb_sh"], c["n_dmrs_prb"]
        mcs_index = c["mcs_index"]
    else:
        n_prb = cfg.n_rb(c["scs_khz"], c["bandwidth_mhz"])
        n_symb = c["length"]
        n_dmrs = cfg.dmrs_re_per_prb(c["dmrs_type"], c["cdm_groups_without_data"],
                                     c["dmrs_symbols"])
        mcs_index = c[f"mcs_index_tb{c['codeword'] + 1}"]
    tbs, trace = compute_tbs(n_prb, n_symb, n_dmrs, mcs_index, mcs_table, layers, x_oh,
                             scaling=S, return_trace=True)
    return {"mcs_table": mcs_table, "N_oh_PRB": x_oh, "S": float(S), "layers": layers,
            "n_PRB": n_prb, "N_DMRS_PRB": n_dmrs, "I_MCS": mcs_index,
            "tbs_trace": trace, "tbs": tbs}


def context_prompt(t: dict) -> str:
    c = t["context"]
    if t["id"] == "ctx-paging-tb-scaling":
        body = (
            "A UE in RRC_CONNECTED decodes a paging message on PDSCH:\n"
            f"- The PDSCH is scheduled by DCI format {c['dci_format']} with "
            f"CRC scrambled by {c['rnti']}; the DCI field 'TB scaling' = '{c['tb_scaling_field']}'\n"
            "- For its unicast traffic the UE is configured with PDSCH-Config mcs-Table = "
            f"{c['configured_mcs_table']} and PDSCH-ServingCellConfig xOverhead = "
            f"xOh{c['configured_xoverhead']}\n"
            f"- I_MCS = {c['mcs_index']}, {c['total_layers']} layer, single codeword\n"
            f"- Allocated PRBs n_PRB = {c['n_prb']}, PDSCH symbols N_symb^sh = "
            f"{c['n_symb_sh']} (mapping type A)\n"
            f"- DM-RS REs per PRB N_DMRS^PRB = {c['n_dmrs_prb']} (already includes the "
            "DM-RS CDM groups without data)\n"
            "- No PT-RS, CSI-RS, SSB, or rate-matching resources overlap the PDSCH\n\n"
            "Compute the Transport Block Size (TBS) in bits of this paging PDSCH, following "
            "TS 38.214 Sections 5.1.3.1 and 5.1.3.2.\n\n"
        )
    else:
        body = (
            "A UE is scheduled with a single-user MIMO PDSCH:\n"
            f"- FR1 carrier, channel bandwidth {c['bandwidth_mhz']} MHz, subcarrier spacing "
            f"{c['scs_khz']} kHz; the PDSCH is allocated over the full maximum transmission "
            "bandwidth of the carrier (TS 38.101-1)\n"
            f"- Scheduled by DCI format 1_1 with CRC scrambled by {c['rnti']}; PDSCH-Config "
            f"mcs-Table = {c['configured_mcs_table']}; xOverhead is not configured\n"
            f"- {c['total_layers']} layers in total, two transport blocks: transport block 1 "
            f"has I_MCS = {c['mcs_index_tb1']}, transport block 2 has I_MCS = "
            f"{c['mcs_index_tb2']}\n"
            f"- PDSCH mapping type A, dmrs-TypeA-Position = pos2, start symbol S = "
            f"{c['start_symbol']}, length L = {c['length']} symbols\n"
            f"- DM-RS: dmrs-Type = type{c['dmrs_type']}, double-symbol front-loaded DM-RS "
            "(maxLength = len2, 2 DM-RS symbols), dmrs-AdditionalPosition = pos0, number "
            f"of DM-RS CDM groups without data = {c['cdm_groups_without_data']}\n"
            "- No PT-RS, CSI-RS, SSB, or rate-matching resources overlap the PDSCH\n\n"
            "Compute the Transport Block Size (TBS) in bits of transport block 2 "
            "(codeword 1), following TS 38.211 Section 7.3.1.3 and TS 38.214 Sections "
            "5.1.3.1 and 5.1.3.2.\n\n"
        )
    return "You are a 5G NR physical-layer engineer. " + body + ANSWER_FORMAT


def solve_config(c: dict) -> dict:
    """Full reference chain from configuration to every quantity we can ask about."""
    n_prb = cfg.n_rb(c["scs_khz"], c["bandwidth_mhz"])
    n_dmrs_sym = cfg.dmrs_symbols_type_a(c["start_symbol"], c["length"], c["additional_position"])
    n_dmrs_prb = cfg.dmrs_re_per_prb(c["dmrs_type"], c["cdm_groups_without_data"], n_dmrs_sym)
    tbs, trace = compute_tbs(n_prb, c["length"], n_dmrs_prb, c["mcs_index"], c["mcs_table"],
                             c["num_layers"], c["xoverhead"], return_trace=True)
    qm, r1024 = MCS_TABLES[c["mcs_table"]][c["mcs_index"]]
    bg = select_base_graph(tbs, r1024 / 1024)
    seg = segment(tbs, bg)
    G = cfg.data_re_actual(n_prb, c["length"], n_dmrs_prb) * qm * c["num_layers"]
    E = rate_match_lengths(G, seg["C"], c["num_layers"], qm)
    lbrm = {}
    if "max_mimo_layers" in c:
        # A single BWP spanning the carrier, so the max BWP size is n_PRB.
        t_lbrm = tbs_lbrm(n_prb, c["max_mimo_layers"], c["mcs_table"])
        n_cb = n_cb_lbrm(bg, seg["Zc"], seg["C"], t_lbrm)
        lbrm = {"TBS_LBRM": t_lbrm, "N_cb": n_cb,
                "k0": circular_buffer_k0(bg, seg["Zc"], c["rv"], n_cb)}
    return {
        "n_PRB": n_prb, "l_d": cfg.type_a_ld(c["start_symbol"], c["length"]),
        "dmrs_symbols": n_dmrs_sym, "N_DMRS_PRB": n_dmrs_prb, "tbs_trace": trace,
        "tbs": tbs, "base_graph": bg, "segmentation": seg, "filler_bits": seg["filler_bits"],
        "G": G, "E_first": E[0], "E_last": E[-1], **lbrm,
    }


CONFIG_QUESTIONS = {
    "tbs": ("the Transport Block Size (TBS) in bits, following TS 38.214 Section 5.1.3.2",
            "TS 38.214 5.1.3.2"),
    "filler_bits": ("the number of filler bits F = K - K' inserted into EACH code block, "
                    "following TS 38.212 (base graph selection Section 7.2.2, code block "
                    "segmentation Section 5.2.2) applied to the TBS from TS 38.214 Section 5.1.3.2",
                    "TS 38.214 5.1.3.2; TS 38.212 5.2.2, 7.2.2"),
    "E_first": ("the rate-matching output sequence length E (in bits) of the FIRST code "
                "block (r = 0), following TS 38.212 Section 5.4.2.1",
                "TS 38.214 5.1.3.2; TS 38.212 5.2.2, 5.4.2.1, 7.2.2"),
    "E_last": ("the rate-matching output sequence length E (in bits) of the LAST code "
               "block (r = C-1), following TS 38.212 Section 5.4.2.1",
               "TS 38.214 5.1.3.2; TS 38.212 5.2.2, 5.4.2.1, 7.2.2"),
    "k0": ("the starting position k0 (in bits) in the circular buffer for the redundancy "
           "version given above, for the first code block, following TS 38.212 Section "
           "5.4.2.1 (including the limited-buffer circular buffer size N_cb)",
           "TS 38.214 5.1.3.2; TS 38.212 5.2.2, 5.4.2.1 (LBRM), 7.2.2"),
}


def config_prompt(t: dict) -> str:
    c = t["config"]
    rm = ""
    if t["question"] == "k0":
        rm = (f"- Redundancy version rv_id = {c['rv']}\n"
              "- Limited buffer rate matching applies (I_LBRM = 1). The UE has a single DL BWP "
              "spanning the full carrier, PDSCH-ServingCellConfig maxMIMO-Layers = "
              f"{c['max_mimo_layers']}, and the configured mcs-Table is "
              f"{'qam256' if c['mcs_table'] == 2 else 'qam64'}\n")
    elif t["question"].startswith("E_"):
        rm = ("- All code blocks of the transport block are scheduled (no CBG-based "
              "transmission); limited buffer rate matching is not configured\n")
    return (
        "You are a 5G NR physical-layer engineer. A UE is scheduled with the following "
        "PDSCH (single codeword, scaling factor S = 1):\n"
        f"- FR1 carrier, channel bandwidth {c['bandwidth_mhz']} MHz, subcarrier spacing "
        f"{c['scs_khz']} kHz; the PDSCH is allocated over the full maximum transmission "
        "bandwidth of the carrier (TS 38.101-1)\n"
        f"- PDSCH mapping type A, dmrs-TypeA-Position = pos2, start symbol S = "
        f"{c['start_symbol']}, length L = {c['length']} symbols\n"
        f"- DM-RS: dmrs-Type = type{c['dmrs_type']}, single-symbol DM-RS (maxLength = len1), "
        f"dmrs-AdditionalPosition = pos{c['additional_position']}, number of DM-RS CDM groups "
        f"without data = {c['cdm_groups_without_data']}\n"
        f"- {MCS_TABLE_NAMES[c['mcs_table']]}, I_MCS = {c['mcs_index']}, "
        f"{c['num_layers']} layers\n"
        f"- xOverhead (higher-layer parameter) = {c['xoverhead']}\n"
        "- No PT-RS, CSI-RS, SSB, or rate-matching resources overlap the PDSCH\n"
        + rm +
        f"\nCompute {CONFIG_QUESTIONS[t['question']][0]}.\n\n" + ANSWER_FORMAT
    )


def tbs_prompt(p: dict) -> str:
    return (
        "You are a 5G NR physical-layer engineer. Following 3GPP TS 38.214 "
        "Section 5.1.3.2 exactly, compute the Transport Block Size (TBS) in bits "
        "for this PDSCH transmission:\n"
        f"- MCS index table: {MCS_TABLE_NAMES[p['mcs_table']]}\n"
        f"- MCS index I_MCS = {p['mcs_index']}\n"
        f"- Allocated PRBs n_PRB = {p['n_prb']}\n"
        f"- PDSCH symbols in the slot N_symb^sh = {p['n_symb_sh']}\n"
        f"- DM-RS REs per PRB N_DMRS^PRB = {p['n_dmrs_prb']} "
        "(already includes the overhead of DM-RS CDM groups without data)\n"
        f"- xOverhead N_oh^PRB = {p['n_oh_prb']}\n"
        f"- Number of layers v = {p['num_layers']}\n"
        "- Single codeword, scaling factor S = 1 (not a P-RNTI/RA-RNTI transmission)\n\n"
        + ANSWER_FORMAT
    )


def ldpc_prompt(t: dict) -> str:
    qm, r1024 = MCS_TABLES[t["mcs_table"]][t["mcs_index"]]
    return (
        "You are a 5G NR physical-layer engineer. A PDSCH transport block of "
        f"A = {t['tbs']} bits is scheduled with I_MCS = {t['mcs_index']} from "
        f"{MCS_TABLE_NAMES[t['mcs_table']]}, i.e. target code rate "
        f"R = {r1024}/1024 and Q_m = {qm}.\n\n"
        "Following 3GPP TS 38.212 (LDPC base graph selection in Section 7.2.2, "
        "transport-block CRC attachment, and code block segmentation in "
        "Section 5.2.2), determine the number of filler bits F = K - K' inserted "
        "into EACH code block.\n\n"
        + ANSWER_FORMAT
    )


def build() -> list[dict]:
    tasks = []
    for t in TBS_TASKS:
        tbs, trace = compute_tbs(**t["params"], return_trace=True)
        tasks.append({
            "id": t["id"], "level": 1, "category": "tbs", "spec": "TS 38.214 5.1.3.2",
            "trap": t["trap"], "params": t["params"], "prompt": tbs_prompt(t["params"]),
            "answer": tbs, "reference_trace": trace,
        })
    for t in LDPC_TASKS:
        _, r1024 = MCS_TABLES[t["mcs_table"]][t["mcs_index"]]
        bg = select_base_graph(t["tbs"], r1024 / 1024)
        seg = segment(t["tbs"], bg)
        tasks.append({
            "id": t["id"], "level": 1, "category": "ldpc", "spec": "TS 38.212 5.2.2, 7.2.2",
            "trap": t["trap"],
            "params": {k: t[k] for k in ("tbs", "mcs_index", "mcs_table")},
            "prompt": ldpc_prompt(t), "answer": seg["filler_bits"],
            "reference_trace": {"base_graph": bg, **seg},
        })
    for t in CONFIG_TASKS:
        sol = solve_config(t["config"])
        tasks.append({
            "id": t["id"], "level": t["level"], "category": f"config-{t['question']}",
            "spec": CONFIG_QUESTIONS[t["question"]][1], "trap": t["trap"],
            "params": t["config"], "prompt": config_prompt(t),
            "answer": sol[t["question"]], "reference_trace": sol,
        })
    for t in CONTEXT_TASKS:
        sol = solve_context(t["context"])
        tasks.append({
            "id": t["id"], "level": t["level"], "category": "context-tbs",
            "spec": "TS 38.214 5.1.3.1, 5.1.3.2; TS 38.211 7.3.1.3", "trap": t["trap"],
            "params": t["context"], "prompt": context_prompt(t),
            "answer": sol[t["question"]], "reference_trace": sol,
        })
    return tasks


def main() -> None:
    tasks = build()
    OUT.write_text(json.dumps(tasks, indent=2, default=str) + "\n")
    for t in tasks:
        print(f"L{t['level']} {t['id']:35s} answer={t['answer']}")
    print(f"Wrote {len(tasks)} tasks to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
