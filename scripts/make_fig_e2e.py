#!/usr/bin/env python3
"""Figure 8 (Sec. VI-B/C, fig:e2e): end-to-end decoding on five systems, both platforms, as bars.

Systems (user, 2026-10-30): NPU only; NPU + X for X = stock AiM, P3-LLM-style, LP-Spec-style, CoDe, where PIM design X
runs every weight GEMM and attention and the NPU the element-wise work, except NPU + P3-LLM-style on the edge server,
which follows P3-LLM's own placement at batch 8 (linear layers on the NPU, attention on PIM; user 2026-11-10, option B;
ids isca.e2e.hbm2.p3own.*, evaluation cd0678a, dac_2x2 Sec. 2p). Rows: mobile platform (speculative loop of
Llama-2-7B, M = 8, L 1024, acceptance 0.7, 1.1B draft, NPU 42 GB/s, synthesised PU energy, reads priced) and edge
server (batch 8, gmean of five LLMs, W4A8, energy at the NPU's 55 W idle). Columns (user-approved breakdowns, 2026-11-11): (a) time per token stacked by
layer class (linear layers, attention, NPU element-wise work, NPU<->PIM hand-offs), normalised to NPU only = 1, with tok/s
and the speed-up over NPU only printed on each bar; (b) tok/s per logic mm^2 normalised to LP-Spec-style (PIM designs only,
system fills as before); (c) energy per token stacked by component (PIM, NPU, DRAM reads over the pins, DRAM standby, idle
NPU at 55 W on the edge server), totals printed. Breakdown ids (evaluation 81820a2, row 113):
  isca.e2e.phone.M8.<d>.T.<linear|attention|npu_elem|other>_norm, isca.e2e.hbm2.<d>.T.<...>_norm (sd8g3 Sec. 2f, 2x2 Sec. 2r);
  isca.e2e.phone.M8.<d>.Eg.<pim|npu|dram|standby>; hyb.esplit.hbm2.b8.<d>.g55.<pim|pim_standby|npu_dyn|reads|static|other>.
Source (read only): the ISCA evaluation ids, evaluation f896213 / 77a9b9d / bf36b5f / 7cf79d5:
  isca.e2e.phone.M8.<npu|stock|h3|h2|core8>.* and isca.e2e.phone.M8.<ratio>.* (the mobile operating point, M = 8),
  isca.e2e.phone.h3.best_M.d1b / best_tok_s.d1b and x.ev56.e2e.d1b.<d>.{best_M,tok_s} (evaluation/dac_sd8g3, Sec. 2f);
  isca.e2e.hbm2.<npu|stock|p3own|h2|core4>.*, isca.e2e.hbm2.npu_overtakes.core4.* (evaluation/dac_2x2, Sec. 2p; the all-PIM
  P3-LLM-style cell isca.e2e.hbm2.p3_500.* is history, guarded below, never printed);
  the best-M rows also against evaluation/dac_sd8g3/raw/ev56_best.csv (L 1024, d1b, alpha 0.7).
Every number Secs. VI-B and VI-C print about Fig. 8 is asserted in check_prose_numbers(). Writes figs/src/fig_e2e.html;
then  python3 scripts/html2pdf.py fig_e2e  ->  figs/fig_e2e.pdf (+ .png preview).
"""
import csv
import os

from dac_data import EVAL, PHONE_RAW, ids, r2
from svgchart import FL, FT, TEXTWIDTH, Fig, I, Panel, width, ylabels_width

SYS = ["npu", "stock", "p3", "lpspec", "code"]
LABEL = {"npu": "NPU only", "stock": "NPU + stock AiM", "p3": "NPU + P3-LLM-style", "lpspec": "NPU + LP-Spec-style",
         "code": "NPU + CoDe"}
KEY = {"phone": {"npu": "npu", "stock": "stock", "p3": "h3", "lpspec": "h2", "code": "core8"},
       "hbm2": {"npu": "npu", "stock": "stock", "p3": "p3own", "lpspec": "h2", "code": "core4"}}
TOPIC = {"phone": "dac_sd8g3", "hbm2": "dac_2x2"}
PFX = {"phone": "isca.e2e.phone.M8", "hbm2": "isca.e2e.hbm2"}   # mobile operating point M = 8, edge batch 8
EKEY = {"phone": "mJ_tok", "hbm2": "mJ_tok_55W"}


# Palette (user, 2026-10-30; skill 02 F5 / 11 G6, as Fig. 3 and Mesorasi Fig. 18): the four reference systems in the
# white / gray ramp, the two lightest told apart by a thin black diagonal hatch; CoDe alone in Fig. 3's blue tint;
# every bar a thin black edge.
EDGE, BAR_LW = "#000000", 0.5
FILL = {"npu": "#FFFFFF", "stock": "#BFBFBF", "p3": "url(#hatch_p3)", "lpspec": "#808080", "code": "#CFE2F3"}
DEFS = ('<defs><pattern id="hatch_p3" patternUnits="userSpaceOnUse" width="2.6" height="2.6" '
        'patternTransform="rotate(45)"><rect width="2.6" height="2.6" fill="#E8E8E8"/>'
        '<line x1="0" y1="0" x2="0" y2="2.6" stroke="#000000" stroke-width="0.45"/></pattern></defs>')


# Breakdown stacks (11 G6): classes, not designs, carry the stack shades, on one luminance ramp with a hatch where the gray
# ramp runs out; CoDe's bar keeps its identity by a heavier outline and its x label on Fig. 3's tint.
TCLS = ["linear", "attention", "npu_elem", "other"]
TLAB = {"linear": "Linear layers", "attention": "Attention", "npu_elem": "NPU element-wise", "other": "NPU–PIM hand-offs"}
ECLS = ["pim", "npu", "dram", "standby", "idle"]
ELAB = {"pim": "PIM", "npu": "NPU", "dram": "DRAM reads", "standby": "DRAM standby", "idle": "Idle NPU at 55 W"}
SHADE = {"linear": "#595959", "attention": "#A6A6A6", "npu_elem": "#E6E6E6", "other": "url(#hatch_cls)",
         "pim": "#595959", "npu": "#A6A6A6", "dram": "#E6E6E6", "standby": "url(#hatch_cls)", "idle": "#FFFFFF"}
DEFS += ('<defs><pattern id="hatch_cls" patternUnits="userSpaceOnUse" width="2.6" height="2.6" '
         'patternTransform="rotate(45)"><rect width="2.6" height="2.6" fill="#FFFFFF"/>'
         '<line x1="0" y1="0" x2="0" y2="2.6" stroke="#000000" stroke-width="0.45"/></pattern></defs>')
XLAB = {"npu": ["NPU", "only"], "stock": ["Stock", "AiM"], "p3": ["P3-", "LLM-", "style"], "lpspec": ["LP-", "Spec-", "style"],
        "code": ["CoDe"]}
SEG_LW, CODE_LW, FX = 0.35, 1.1, 7.5


def colours(s):
    return FILL[s], EDGE


def load():
    out = {}
    for p, t in TOPIC.items():
        tid = ids(t)
        g = lambda s, c: tid[f"{PFX[p]}.{KEY[p][s]}.{c}"]  # noqa: E731
        tok = {s: g(s, "tok_s") for s in SYS}
        sp = {s: tok[s] / tok["npu"] for s in SYS}
        for s in SYS[1:]:
            assert abs(sp[s] - g(s, "speedup_vs_npu")) < 1e-9, (p, s)
        pm = {s: g(s, "tok_s_per_mm2") / g("lpspec", "tok_s_per_mm2") for s in SYS[1:]}
        en = {s: g(s, EKEY[p]) for s in SYS}
        # (a) time per token by layer class, NPU only = 1 (row 113)
        T = {s: {c: g(s, f"T.{c}_norm") for c in TCLS} for s in SYS}
        for s in SYS:
            assert abs(sum(T[s].values()) - g(s, "T.total_norm")) < 1e-9, (p, s)
            assert abs(g(s, "T.total_norm") - tok["npu"] / tok[s]) < 1e-9, (p, s)
        # (c) energy per token by component; the edge PIM group's standby part (pim_standby) is drawn as DRAM standby, as
        # on the phone, and the KV-append term (other, 0.005 mJ) joins the NPU group
        E = {}
        for s in SYS:
            if p == "phone":
                E[s] = dict(pim=g(s, "Eg.pim"), npu=g(s, "Eg.npu"), dram=g(s, "Eg.dram"), standby=g(s, "Eg.standby"), idle=0.0)
            else:
                h = lambda c: tid[f"hyb.esplit.hbm2.b8.{KEY[p][s]}.g55.{c}"]  # noqa: E731
                assert h("other") < 0.01
                E[s] = dict(pim=h("pim") - h("pim_standby"), npu=h("npu_dyn") + h("other"), dram=h("reads"),
                            standby=h("pim_standby"), idle=h("static"))
            assert abs(sum(E[s].values()) - en[s]) < 1e-9 * en[s], (p, s)
        out[p] = dict(tid=tid, tok=tok, sp=sp, pm=pm, en=en, T=T, E=E)
    return out


def check_prose_numbers(d):
    ph, hb = d["phone"], d["hbm2"]
    pt, ht = ph["tid"], hb["tid"]
    # eval-e2e-phone (operating point M = 8, Sec. V-D): CoDe 3.22x NPU only at 29.9 tok/s, LP-Spec-style 3.00x at 27.9,
    # P3-LLM-style 2.06x (two tokens per read: four passes over eight token rows), stock AiM 1.27x
    assert [r2(ph["sp"][s]) for s in ("stock", "p3", "lpspec", "code")] == [1.27, 2.06, 3.00, 3.22]
    assert round(ph["tok"]["code"], 1) == 29.9 and round(ph["tok"]["lpspec"], 1) == 27.9
    assert -(-8 // 2) == 4
    # best M of each system (L 1024, 1.1B draft, alpha 0.7): CoDe / LP-Spec-style 47.1 / 46.8 at M = 3, P3-LLM-style 43.8 at
    # M = 2, stock AiM 26.5 at M = 2, NPU only 10.6 at M = 4
    with open(os.path.join(PHONE_RAW, "ev56_best.csv")) as fh:
        best = {r["mapping"]: (int(r["best_M"]), float(r["tok_s"])) for r in csv.DictReader(fh)
                if r["row_id"].startswith("npu42/1024/d1b/") and r["alpha"] == "0.7"}
    want = {"all_core": (3, 47.1), "all_h2": (3, 46.8), "all_h3": (2, 43.8), "all_stock": (2, 26.5), "all_npu": (4, 10.6)}
    for m, (bm, ts) in want.items():
        assert best[m][0] == bm and round(best[m][1], 1) == ts, (m, best[m])
        if m != "all_h3":
            assert pt[f"x.ev56.e2e.d1b.{m}.best_M"] == bm and abs(pt[f"x.ev56.e2e.d1b.{m}.tok_s"] - best[m][1]) < 1e-9
    assert pt["isca.e2e.phone.h3.best_M.d1b"] == 2 and abs(pt["isca.e2e.phone.h3.best_tok_s.d1b"] - best["all_h3"][1]) < 1e-9
    assert abs(best["all_npu"][1] - pt["isca.e2e.phone.npu.tok_s"]) < 1e-9
    # VI-D eval-vsweep-choice: the loop's best M with an EAGLE head is 4 (L 1024, alpha 0.7; guard only)
    with open(os.path.join(PHONE_RAW, "ev56_best.csv")) as fh:
        assert next(int(r["best_M"]) for r in csv.DictReader(fh) if r["row_id"] == "npu42/1024/eagle/all_core/0.7") == 4
    assert best["all_core"][1] > best["all_h2"][1] > best["all_h3"][1] > best["all_stock"][1] > best["all_npu"][1]
    # abstract / intro / VI-B eval-lpspec-variants / conclusion: CoDe decodes 1.07x faster than the per-bank LP-Spec-style
    # at M = 8, also at M = 16; recomputed from the collected ev56_chain rows (L 1024, 1.1B draft, alpha 0.7)
    with open(os.path.join(PHONE_RAW, "ev56_chain.csv")) as fh:
        ch = {r["row_id"]: float(r["tok_s"]) for r in csv.DictReader(fh)}
    lead = {M: ch[f"npu42/1024/d1b/all_core/{M}/0.7"] / ch[f"npu42/1024/d1b/all_h2/{M}/0.7"] for M in (8, 16)}
    assert abs(lead[8] - pt["isca.e2e.phone.M8.core8_over_h2.speed"]) < 1e-9
    assert abs(ph["tok"]["code"] / ph["tok"]["lpspec"] - lead[8]) < 1e-9
    assert r2(lead[8]) == 1.07 == r2(lead[16]), (lead[8], lead[16])
    # eval-e2e-server: CoDe = LP-Spec-style 1.28x NPU only (456 tok/s); stock 0.45x, P3-LLM-style 0.91x at P3-LLM's own
    # placement (linear layers on the NPU, attention on PIM); CoDe 1.41x P3 (all-PIM cell 0.76x / 1.68x: history only)
    assert [r2(hb["sp"][s]) for s in ("stock", "p3", "lpspec", "code")] == [0.45, 0.91, 1.28, 1.28]
    assert hb["tok"]["code"] == hb["tok"]["lpspec"] and round(hb["tok"]["code"]) == 456
    assert all(hb["sp"][s] < 1 for s in ("stock", "p3"))
    assert r2(ht["isca.e2e.hbm2.core4_over_p3own.speed"]) == 1.41
    assert abs(hb["tok"]["code"] / hb["tok"]["p3"] - ht["isca.e2e.hbm2.core4_over_p3own.speed"]) < 1e-9
    assert r2(ht["isca.e2e.hbm2.core4_over_p3_500.speed"]) == 1.68 and r2(ht["isca.e2e.hbm2.p3_500.speedup_vs_npu"]) == 0.76  # history
    # NPU only overtakes CoDe from batch 16 on the gmean (CoDe last ahead at 12)
    assert ht["isca.e2e.hbm2.npu_overtakes.core4.gmean.first_npu_M"] == 16 and ht["isca.e2e.hbm2.npu_overtakes.core4.gmean.last_pim_M"] == 12
    # eval-e2e-phone setting: batch 8 = the largest power of two at which CoDe still leads NPU only
    lead_b = ht["isca.e2e.hbm2.npu_overtakes.core4.gmean.last_pim_M"]
    assert max(2 ** k for k in range(8) if 2 ** k <= lead_b) == 8 < ht["isca.e2e.hbm2.npu_overtakes.core4.gmean.first_npu_M"]
    # eval-e2e-per-mm2: CoDe / LP-Spec-style 1.99x (mobile, M = 8), 1.79x (edge); CoDe / P3-LLM-style 1.17x, 1.06x (edge: own
    # placement, PIM logic only, no NPU area); Fig. 8b P3-LLM-style edge bar = p3own_over_h2.per_mm2 (1.69)
    assert r2(ph["pm"]["code"]) == 1.99 == r2(pt["isca.e2e.phone.M8.core8_over_h2.per_mm2"])
    assert abs(ph["pm"]["code"] - pt["isca.e2e.phone.M8.core8.per_mm2_norm_lp"]) < 1e-9
    assert all(abs(ph["pm"][s] - pt[f"isca.e2e.phone.M8.{KEY['phone'][s]}.per_mm2_norm_lp"]) < 1e-9 for s in ("stock", "p3"))
    assert r2(hb["pm"]["code"]) == 1.79 == r2(ht["isca.e2e.hbm2.core4_over_h2.per_mm2"])
    assert r2(pt["isca.e2e.phone.M8.core8_over_h3.per_mm2"]) == 1.17 and r2(ht["isca.e2e.hbm2.core4_over_p3own.per_mm2"]) == 1.06
    assert abs(hb["pm"]["p3"] - ht["isca.e2e.hbm2.p3own_over_h2.per_mm2"]) < 1e-9 and r2(hb["pm"]["p3"]) == 1.69
    assert abs(hb["pm"]["code"] / hb["pm"]["p3"] - ht["isca.e2e.hbm2.core4_over_p3own.per_mm2"]) < 1e-9
    assert r2(pt["isca.e2e.phone.M8.core8_over_h2.speed"]) == 1.07 and ht["isca.e2e.hbm2.core4_over_h2.speed"] == 1.0
    # eval-energy, mobile (M = 8): CoDe 105.8 mJ/token; NPU only 6.0x, stock AiM 1.96x, P3-LLM-style 1.40x, LP-Spec-style 1.14x
    e = ph["en"]
    assert round(e["code"], 1) == 105.8
    assert round(e["npu"] / e["code"], 1) == 6.0
    for s, k, v in (("stock", "stock", 1.96), ("p3", "h3", 1.40), ("lpspec", "h2", 1.14)):
        q = pt[f"isca.e2e.phone.M8.{k}_over_core8.mJ"]
        assert r2(q) == v and abs(e[s] / e["code"] - q) < 1e-9, (s, q)
    assert min(e, key=e.get) == "code"
    # eval-energy, edge server at 55 W idle: NPU only 1.48x, P3-LLM-style 1.52x CoDe's; LP-Spec-style ties (1.00x);
    # gated NPU (0 W): P3-LLM-style 2.08x (larger than at 55 W: its NPU reads the linear weights over the pins), NPU only 2.46x
    assert r2(ht["isca.e2e.hbm2.npu_over_core4.mJ_55W"]) == 1.48 and r2(ht["isca.e2e.hbm2.p3own_over_core4.mJ_55W"]) == 1.52
    assert abs(hb["en"]["p3"] / hb["en"]["code"] - ht["isca.e2e.hbm2.p3own_over_core4.mJ_55W"]) < 1e-9
    assert r2(ht["isca.e2e.hbm2.h2_over_core4.mJ_55W"]) == 1.00
    assert r2(ht["isca.e2e.hbm2.p3own_over_core4.mJ_0W"]) == 2.08 > ht["isca.e2e.hbm2.p3own_over_core4.mJ_55W"] and r2(ht["isca.e2e.hbm2.npu_over_core4.mJ_0W"]) == 2.46
    assert abs(hb["en"]["npu"] / hb["en"]["code"] - ht["isca.e2e.hbm2.npu_over_core4.mJ_55W"]) < 1e-9
    # gated-NPU cause (evaluation 860384d, 2x2 §2r/§8): P3-LLM-style's linear-weight reads over the HBM pins are 76 % of
    # the 0 W gap (26.41 mJ/token); context: linear placement 0.788 of the gap, P3-LLM-style's NPU MACs 0.0149 of its energy
    assert round(100 * ht["hyb.esplit.hbm2.b8.gap_share.weight_io"]) == 76
    assert ht["hyb.esplit.hbm2.b8.gap_share.weight_io"] < ht["hyb.esplit.hbm2.b8.gap_share.linear_placement"] < 1
    # Fig. 8c edge bars in the text (AI-review item 3, 2026-11-08): CoDe 145 mJ per token, stock AiM 2.73x CoDe's
    assert round(hb["en"]["code"]) == 145
    assert r2(ht["isca.e2e.hbm2.stock_over_core4.mJ_55W"]) == 2.73
    assert abs(hb["en"]["stock"] / hb["en"]["code"] - ht["isca.e2e.hbm2.stock_over_core4.mJ_55W"]) < 1e-9
    assert min(hb["en"], key=hb["en"].get) == "code"
    # Fig. 8a/8c breakdowns (evaluation 81820a2, row 113; sd8g3 Sec. 2f, 2x2 Sec. 2r)
    # eval-e2e-phone: CoDe's linear-layer time 0.93x and attention time 0.70x LP-Spec-style's; element-wise work and hand-offs
    # take the same time in every NPU + PIM system; hand-offs 27 % of CoDe's time per token
    T = ph["T"]
    q_lin, q_att = pt["isca.e2e.phone.M8.core8_over_h2.T_linear"], pt["isca.e2e.phone.M8.core8_over_h2.T_attention"]
    assert abs(T["code"]["linear"] / T["lpspec"]["linear"] - q_lin) < 1e-9 and r2(q_lin) == 0.93
    assert abs(T["code"]["attention"] / T["lpspec"]["attention"] - q_att) < 1e-9 and r2(q_att) == 0.70
    for c in ("npu_elem", "other"):
        assert max(T[s][c] for s in SYS[1:]) - min(T[s][c] for s in SYS[1:]) < 1e-12, c
    assert round(100 * pt["isca.e2e.phone.M8.core8.T.other_share"]) == 27
    assert abs(T["code"]["other"] / sum(T["code"].values()) - pt["isca.e2e.phone.M8.core8.T.other_share"]) < 1e-9
    assert T["npu"]["npu_elem"] == 0 == T["npu"]["other"]     # NPU only: no element-wise term by model, no hand-offs
    # eval-e2e-server: CoDe and LP-Spec-style split their time identically; CoDe spends 0.70x P3-LLM-style's time on the
    # linear layers (P3-LLM-style's NPU), 0.69x on attention
    assert ht["x.recon.isca.e2e.hbm2.T.core4_minus_h2_maxabs"] == 0 and hb["T"]["code"] == hb["T"]["lpspec"]
    for c, v in (("linear", 0.70), ("attention", 0.69)):
        q = ht[f"isca.e2e.hbm2.core4_over_p3own.T_{c}"]
        assert abs(hb["T"]["code"][c] / hb["T"]["p3"][c] - q) < 1e-9 and r2(q) == v, (c, q)
    # eval-energy, mobile: NPU only spends 46 % of its energy on DRAM reads, the NPU + PIM systems none; CoDe's PIM energy
    # (PU + bank reads) 0.79x LP-Spec-style's, 0.66x P3-LLM-style's
    E = ph["E"]
    assert round(100 * pt["isca.e2e.phone.M8.npu.Eg.dram"] / e["npu"]) == 46 and E["npu"]["dram"] == pt["isca.e2e.phone.M8.npu.Eg.dram"]
    assert all(E[s]["dram"] == 0 for s in SYS[1:])
    for k, s, v in (("h2", "lpspec", 0.79), ("h3", "p3", 0.66)):
        q = pt[f"isca.e2e.phone.M8.core8_over_{k}.Eg_pim"]
        assert abs(E["code"]["pim"] / E[s]["pim"] - q) < 1e-9 and r2(q) == v, (s, q)
    # eval-energy, edge at 55 W: the idle NPU takes 83 % of CoDe's energy per token
    assert round(100 * ht["hyb.esplit.hbm2.b8.core4.g55share.static"]) == 83
    assert abs(hb["E"]["code"]["idle"] / hb["en"]["code"] - ht["hyb.esplit.hbm2.b8.core4.g55share.static"]) < 1e-9
    # abstract / intro / conclusion: 1.07x faster on 0.539x the logic, 1.99x per mm2 (mobile); 1.41x, 1.06x, 1.52x (edge server)
    # Fig. 8 HBM2 bars equal the collected export figures/fig_e2e_hbm2.csv (evaluation cd0678a)
    with open(os.path.join(EVAL, "dac_2x2", "figures", "fig_e2e_hbm2.csv")) as fh:
        ex = {r["design"]: r for r in csv.DictReader(fh)}
    for s, k in (("npu", "npu"), ("stock", "stock"), ("p3", "p3_500"), ("lpspec", "h2"), ("code", "core4")):
        assert abs(float(ex[k]["tok_s"]) - hb["tok"][s]) < 1e-9 and abs(float(ex[k]["mJ_tok_55W"]) - hb["en"][s]) < 1e-9, s
    assert ex["p3_500"]["placement"] == "npu_lin_pim_attn" and ex["core4"]["placement"] == "pim_all"
    print("Secs. VI-B/C numbers hold: mobile M = 8 3.22 / 3.00 / 2.06 / 1.27x at 29.9 / 27.9 tok/s, 1.07x (also M = 16), "
          "best M 47.1 / 46.8 / 43.8 / 26.5 / 10.6; "
          "edge 1.28 / 1.28 / 0.91 / 0.45x, 1.41x, NPU from batch 16; per mm2 1.99 / 1.79, 1.17 / 1.06; energy 105.8 mJ, "
          "6.0 / 1.96 / 1.40 / 1.14x; edge 1.48 / 1.52x (gated 2.08 / 2.46x, weight I/O 76 % of the gap); "
          "breakdowns 0.93 / 0.70x, hand-offs 27 %, edge 0.70 / 0.69x P3, DRAM 46 %, PIM 0.79 / 0.66x, idle NPU 83 %")


def fmt(v):
    return f"{v:.0f}" if v >= 99.5 else f"{v:.1f}" if v >= 9.95 else f"{v:.2f}"


def label_ground(fig, cx, y, txt, size):
    """Text centred at cx on a white ground, so a gridline or the dashed 1.0 line never crosses it."""
    lw_ = width(txt, size)
    fig.o.append(f'<rect x="{cx - lw_ / 2 - 0.6:.2f}" y="{y - size * 0.74:.2f}" width="{lw_ + 1.2:.2f}" '
                 f'height="{size * 0.74 + 0.6:.2f}" fill="#FFFFFF"/>')
    fig.text(cx, y, txt, size, "middle")


def main():
    d = load()
    check_prose_numbers(d)
    W, H = TEXTWIDTH, 198.0
    fig = Fig(W, H)
    fig.o.append(DEFS)
    # legends once: (a)'s four layer classes, (c)'s five energy components
    for y, head, cls, lab in ((9.0, "(a)", TCLS, TLAB), (20.5, "(c)", ECLS, ELAB)):
        items = [(lab[c], SHADE[c], EDGE) for c in cls]
        tot = sum(9.0 + 3.0 + width(lab[c], FL) for c in cls) + 11.0 * (len(cls) - 1)
        x0 = W / 2 - tot / 2 + (width(head, FL) + 5.0) / 2
        fig.text(x0 - 5.0, y, head, FL, "end")
        fig.legend_patches(items, y, x_center=x0 + tot / 2)
    box_h, rows_y = 60.0, (36.0, 107.0)
    spec = {"phone": [dict(ylim=(0, 1.4), yticks=[0, 0.5, 1]), dict(ylim=(0, 2.3), yticks=[0, 0.5, 1, 1.5, 2]),
                      dict(ylim=(0, 265), yticks=[0, 50, 100, 150, 200, 250])],
            "hbm2": [dict(ylim=(0, 3.2), yticks=[0, 1, 2, 3]), dict(ylim=(0, 2.3), yticks=[0, 0.5, 1, 1.5, 2]),
                     dict(ylim=(0, 470), yticks=[0, 100, 200, 300, 400])]}
    titles = ["(a) Time per token, normalized", "(b) Tok/s per logic mm², normalized", "(c) Energy per token"]
    ylabs = ["÷ NPU only", "÷ LP-Spec-style", "mJ / token"]
    # one panel geometry for both rows, so the bottom row's x labels name the top row's bars too
    left, gap, slots = 17.0, 8.0, [len(SYS) + 0.2, len(SYS) - 1 + 0.2, len(SYS) + 0.2]
    deco = [FL + 1.5 + max(ylabels_width(spec[p][k]["yticks"], False) for p in spec) + 2.0 for k in range(3)]
    free = W - left - 0.5 - sum(deco) - 2 * gap
    lay, x = [], left
    for k in range(3):
        w = free * slots[k] / sum(slots)
        lay.append((x + deco[k], w, x + FL * 0.75))
        x += deco[k] + w + gap
    for (p, rlab), y0 in zip((("phone", "Mobile, " + I("M") + " = 8"), ("hbm2", "Edge, batch 8")), rows_y):
        xr = 3.0 + FL * 0.75
        fig.text(xr, y0 + box_h / 2, rlab, FL, "middle", f' transform="rotate(-90 {xr:.2f} {y0 + box_h / 2:.2f})"')
        for k, ((x0, w, ylx), ax) in enumerate(zip(lay, spec[p])):
            pn = Panel(fig, x0, y0, w, box_h, (0, 1), [], ax["ylim"], False, ax["yticks"], xlog=False)
            pn.frame(titles[k] if p == "phone" else "", "", ylabs[k], ylx)
            if k < 2:   # the normalisation point
                fig.line(x0, pn.py(1.0), x0 + w, pn.py(1.0), "#000000", 0.6, ' stroke-dasharray="2.5 1.5"')
            syss = SYS if k != 1 else SYS[1:]
            slot = w / slots[k]
            bw = slot * 0.70
            top, base = ax["ylim"][1], y0 + box_h
            for i, s in enumerate(syss):
                cx = x0 + slot * (i + 0.6)
                xl = cx - bw / 2
                lw = CODE_LW if s == "code" else BAR_LW
                if k == 1:      # (b) unchanged: one bar per system in its own fill
                    v = d[p]["pm"][s]
                    yv = pn.py(v)
                    fig.o.append(f'<rect x="{xl:.2f}" y="{yv:.2f}" width="{bw:.2f}" height="{base - yv:.2f}" '
                                 f'fill="{FILL[s]}" stroke="{EDGE}" stroke-width="{BAR_LW}"/>')
                    label_ground(fig, cx, yv - 1.6, fmt(v), FT)
                    continue
                parts = [(c, d[p]["T"][s][c]) for c in TCLS] if k == 0 else [(c, d[p]["E"][s][c]) for c in ECLS]
                v = sum(val for _, val in parts)
                acc = 0.0
                for c, val in parts:            # segments bottom to top, clipped at the axis top
                    lo, hi = min(acc, top), min(acc + val, top)
                    acc += val
                    if hi - lo <= 0:
                        continue
                    fig.o.append(f'<rect x="{xl:.2f}" y="{pn.py(hi):.2f}" width="{bw:.2f}" height="{pn.py(lo) - pn.py(hi):.2f}" '
                                 f'fill="{SHADE[c]}" stroke="{EDGE}" stroke-width="{SEG_LW}"/>')
                yv = pn.py(min(v, top))
                fig.o.append(f'<rect x="{xl:.2f}" y="{yv:.2f}" width="{bw:.2f}" height="{base - yv:.2f}" fill="none" '
                             f'stroke="{EDGE}" stroke-width="{lw}"/>')
                if v > top:     # clipped bar: break mark, total inside the bar
                    yb = y0 + 9.0
                    fig.o.append(f'<rect x="{xl - 1.5:.2f}" y="{yb:.2f}" width="{bw + 3:.2f}" height="2.2" fill="#FFFFFF"/>')
                    label_ground(fig, cx, y0 + 19.5, fmt(v), FT)
                elif k == 0:    # tok/s on top, speed-up over NPU only under it
                    if s == "npu":
                        label_ground(fig, cx, yv - 1.6, fmt(d[p]["tok"][s]), FT)
                    else:
                        label_ground(fig, cx, yv - 1.6, f"{d[p]['sp'][s]:.2f}×", FT)
                        label_ground(fig, cx, yv - 2.6 - FT, fmt(d[p]["tok"][s]), FT)
                else:
                    label_ground(fig, cx, yv - 1.6, fmt(v), FT)
                if p == "hbm2":   # system names under the bottom row
                    for j, ln in enumerate(XLAB[s]):
                        yt = base + FX + 1.5 + j * (FX + 0.8)
                        if s == "code":
                            tw = width(ln, FX)
                            fig.o.append(f'<rect x="{cx - tw / 2 - 1.2:.2f}" y="{yt - FX * 0.78:.2f}" width="{tw + 2.4:.2f}" '
                                         f'height="{FX + 0.4:.2f}" fill="{FILL["code"]}"/>')
                        fig.text(cx, yt, ln, FX, "middle")
            if k == 1 and p == "hbm2":
                for i, s in enumerate(syss):
                    cx = x0 + slot * (i + 0.6)
                    for j, ln in enumerate(XLAB[s]):
                        yt = base + FX + 1.5 + j * (FX + 0.8)
                        if s == "code":
                            tw = width(ln, FX)
                            fig.o.append(f'<rect x="{cx - tw / 2 - 1.2:.2f}" y="{yt - FX * 0.78:.2f}" width="{tw + 2.4:.2f}" '
                                         f'height="{FX + 0.4:.2f}" fill="{FILL["code"]}"/>')
                        fig.text(cx, yt, ln, FX, "middle")
            pn.finish()
    fig.write("fig_e2e", "scripts/make_fig_e2e.py")


if __name__ == "__main__":
    main()
