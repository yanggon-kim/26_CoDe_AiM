#!/usr/bin/env python3
"""Figure 8 (Sec. VI-B/C, fig:e2e): end-to-end decoding on five systems, both platforms, as bars.

Systems (user, 2026-10-30): NPU only; NPU + X for X = stock AiM, P3-LLM-style, LP-Spec-style, CoDe, where PIM design X
runs every weight GEMM and attention and the NPU the element-wise work, except NPU + P3-LLM-style on the edge server,
which follows P3-LLM's own placement at batch 8 (linear layers on the NPU, attention on PIM; user 2026-11-10, option B;
ids isca.e2e.hbm2.p3own.*, evaluation cd0678a, dac_2x2 Sec. 2p). Rows: mobile platform (speculative loop of
Llama-2-7B, M = 8, L 1024, acceptance 0.7, 1.1B draft, NPU 42 GB/s, synthesised PU energy, reads priced) and edge
server (batch 8, gmean of five LLMs, W4A8, energy at the NPU's 55 W idle). Columns: (a) speed-up over NPU only, tok/s
printed on the bars; (b) tok/s per logic mm^2 normalised to LP-Spec-style (PIM designs only); (c) energy per token (mJ).
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
from svgchart import FL, FT, TEXTWIDTH, Fig, I, Panel, row, width

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
        out[p] = dict(tid=tid, tok=tok, sp=sp, pm=pm, en=en)
    return out


def check_prose_numbers(d):
    ph, hb = d["phone"], d["hbm2"]
    pt, ht = ph["tid"], hb["tid"]
    # eval-e2e-phone (operating point M = 8, Sec. V-D): CoDe 3.22x NPU only at 29.9 tok/s, LP-Spec-style 3.00x at 27.9,
    # P3-LLM-style 2.06x (two tokens per read: four passes over eight token rows), stock AiM 1.27x
    assert [r2(ph["sp"][s]) for s in ("stock", "p3", "lpspec", "code")] == [1.27, 2.06, 3.00, 3.22]
    assert round(ph["tok"]["code"], 1) == 29.9 and round(ph["tok"]["lpspec"], 1) == 27.9
    assert -(-8 // 2) == 4
    # guard only, not printed since 2026-11-12 (the paper never names a best M): each system's own best M (L 1024, 1.1B
    # draft, alpha 0.7): CoDe / LP-Spec-style 47.1 / 46.8 at M = 3, P3-LLM-style 43.8 and stock AiM 26.5 at M = 2, NPU only
    # 10.6 at M = 4
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
    # VI-B eval-e2e-lpspec: across M = 2-16 (alpha 0.7) CoDe decodes at least as fast as LP-Spec-style and returns
    # 1.75-2.28x its tok/s per logic mm^2 (evaluation/dac_sd8g3 Sec. 2l, b020aab; speed range and extreme M not printed)
    acc = "isca.acc.phone.a070.M2to16.core8_over_h2"
    assert pt[f"{acc}.speed.min_ge_1"] == 1 and pt[f"{acc}.speed.min"] >= 1
    assert r2(pt[f"{acc}.per_mm2.min"]) == 1.75 and r2(pt[f"{acc}.per_mm2.max"]) == 2.28
    assert pt[f"{acc}.per_mm2.min"] <= pt["isca.e2e.phone.M8.core8_over_h2.per_mm2"] <= pt[f"{acc}.per_mm2.max"]
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
    # ("NPU only overtakes CoDe from batch 16" cut 2026-11-12, user trim; npu_overtakes ids stay collected)
    # eval-e2e-per-mm2 (SAED14 x 10 areas, evaluation 35c9d06; Nangate45 history 1.99 / 1.79, 1.17 / 1.06, 1.69):
    # CoDe / LP-Spec-style 1.87x (mobile, M = 8), 1.80x (edge); CoDe / P3-LLM-style 1.11x, 1.05x (edge: own
    # placement, PIM logic only, no NPU area); Fig. 8b P3-LLM-style edge bar = p3own_over_h2.per_mm2 (1.72)
    assert r2(ph["pm"]["code"]) == 1.87 == r2(pt["isca.e2e.phone.M8.core8_over_h2.per_mm2"])
    assert abs(ph["pm"]["code"] - pt["isca.e2e.phone.M8.core8.per_mm2_norm_lp"]) < 1e-9
    assert all(abs(ph["pm"][s] - pt[f"isca.e2e.phone.M8.{KEY['phone'][s]}.per_mm2_norm_lp"]) < 1e-9 for s in ("stock", "p3"))
    assert r2(hb["pm"]["code"]) == 1.80 == r2(ht["isca.e2e.hbm2.core4_over_h2.per_mm2"])
    assert r2(pt["isca.e2e.phone.M8.core8_over_h3.per_mm2"]) == 1.11 and r2(ht["isca.e2e.hbm2.core4_over_p3own.per_mm2"]) == 1.05
    assert abs(hb["pm"]["p3"] - ht["isca.e2e.hbm2.p3own_over_h2.per_mm2"]) < 1e-9 and r2(hb["pm"]["p3"]) == 1.72
    assert abs(hb["pm"]["code"] / hb["pm"]["p3"] - ht["isca.e2e.hbm2.core4_over_p3own.per_mm2"]) < 1e-9
    assert r2(pt["isca.e2e.phone.M8.core8_over_h2.speed"]) == 1.07 and ht["isca.e2e.hbm2.core4_over_h2.speed"] == 1.0
    # eval-energy, mobile (M = 8): CoDe 106.0 mJ/token; NPU only 6.0x, stock AiM 1.93x, P3-LLM-style 1.38x, LP-Spec-style 1.12x
    # (SAED14 run-5 PU power, microarch d7cd004, evaluation 8db3979; Nangate45 history 105.8, 1.96 / 1.40 / 1.14)
    e = ph["en"]
    assert round(e["code"], 1) == 106.0
    assert round(e["npu"] / e["code"], 1) == 6.0
    for s, k, v in (("stock", "stock", 1.93), ("p3", "h3", 1.38), ("lpspec", "h2", 1.12)):
        q = pt[f"isca.e2e.phone.M8.{k}_over_core8.mJ"]
        assert r2(q) == v and abs(e[s] / e["code"] - q) < 1e-9, (s, q)
    assert min(e, key=e.get) == "code"
    # eval-energy, edge server at 55 W idle: NPU only 1.48x, P3-LLM-style 1.52x CoDe's; LP-Spec-style ties (1.00x);
    # gated NPU (0 W): P3-LLM-style 2.07x (2.08x before run 5) (larger than at 55 W: its NPU reads the linear weights over the pins), NPU only 2.46x
    assert r2(ht["isca.e2e.hbm2.npu_over_core4.mJ_55W"]) == 1.48 and r2(ht["isca.e2e.hbm2.p3own_over_core4.mJ_55W"]) == 1.52
    assert abs(hb["en"]["p3"] / hb["en"]["code"] - ht["isca.e2e.hbm2.p3own_over_core4.mJ_55W"]) < 1e-9
    assert r2(ht["isca.e2e.hbm2.h2_over_core4.mJ_55W"]) == 1.00
    assert r2(ht["isca.e2e.hbm2.p3own_over_core4.mJ_0W"]) == 2.07 > ht["isca.e2e.hbm2.p3own_over_core4.mJ_55W"] and r2(ht["isca.e2e.hbm2.npu_over_core4.mJ_0W"]) == 2.45
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
    # abstract / intro / conclusion: 1.07x faster on 0.574x the logic, 1.87x per mm2 (mobile); 1.41x, 1.05x, 1.52x (edge server)
    # Fig. 8 HBM2 bars equal the collected export figures/fig_e2e_hbm2.csv (evaluation cd0678a)
    with open(os.path.join(EVAL, "dac_2x2", "figures", "fig_e2e_hbm2.csv")) as fh:
        ex = {r["design"]: r for r in csv.DictReader(fh)}
    for s, k in (("npu", "npu"), ("stock", "stock"), ("p3", "p3_500"), ("lpspec", "h2"), ("code", "core4")):
        assert abs(float(ex[k]["tok_s"]) - hb["tok"][s]) < 1e-9 and abs(float(ex[k]["mJ_tok_55W"]) - hb["en"][s]) < 1e-9, s
    assert ex["p3_500"]["placement"] == "npu_lin_pim_attn" and ex["core4"]["placement"] == "pim_all"
    print("Secs. VI-B/C numbers hold: mobile M = 8 3.22 / 3.00 / 2.06 / 1.27x at 29.9 / 27.9 tok/s, 1.07x (also M = 16), "
          "M = 2-16 vs LP-Spec-style speed >= 1, per mm2 1.75-2.28x; "
          "edge 1.28 / 1.28 / 0.91 / 0.45x, 1.41x; per mm2 1.87 / 1.80, 1.11 / 1.05; energy 105.8 mJ, "
          "6.0 / 1.96 / 1.40 / 1.14x; edge 1.48 / 1.52x (gated 2.07 / 2.45x, weight I/O 76 % of the gap)")


def fmt(v):
    return f"{v:.0f}" if v >= 99.5 else f"{v:.1f}" if v >= 9.95 else f"{v:.2f}"


def main():
    d = load()
    check_prose_numbers(d)
    W, H = TEXTWIDTH, 113.6   # 0.8x of 142 pt (user trims 2026-11-12, 2026-11-13: 178 -> 142 -> 113.6 pt)
    fig = Fig(W, H)
    fig.o.append(DEFS)
    fig.legend_patches([(LABEL[s],) + colours(s) for s in SYS], 8.5)
    box_h, rows_y = 36.0, (22.0, 70.0)
    spec = {"phone": [dict(ylim=(0, 4.2), yticks=[0, 1, 2, 3]), dict(ylim=(0, 2.3), yticks=[0, 1, 2]),
                      dict(ylim=(0, 265), yticks=[0, 100, 200])],
            "hbm2": [dict(ylim=(0, 1.65), yticks=[0, 0.5, 1, 1.5]), dict(ylim=(0, 2.3), yticks=[0, 1, 2]),
                     dict(ylim=(0, 570), yticks=[0, 200, 400])]}
    titles = ["(a) Speed-up over NPU only", "(b) Tok/s per logic mm² ÷ LP-Spec-style", "(c) Energy per token"]
    ylabs = ["speed-up", "ratio", "mJ / token"]
    for (p, rlab), y0 in zip((("phone", ["Mobile", I("M") + " = 8"]), ("hbm2", ["Edge server", "batch 8"])), rows_y):
        axes = [dict(a, ylog=False) for a in spec[p]]
        lay = row(fig, axes, y0, y0 + box_h, left=20.0, gap=9.0)
        for i, s in enumerate(rlab):
            x = 3.0 + FL * 0.75 + i * (FL + 1.0)
            fig.text(x, y0 + box_h / 2, s, FL, "middle", f' transform="rotate(-90 {x:.2f} {y0 + box_h / 2:.2f})"')
        for k, ((x0, w, ylx), ax) in enumerate(zip(lay, axes)):
            pn = Panel(fig, x0, y0, w, box_h, (0, 1), [], ax["ylim"], False, ax["yticks"], xlog=False)
            pn.frame(titles[k] if p == "phone" else "", "", ylabs[k], ylx)
            if k < 2:   # the normalisation point
                fig.line(x0, pn.py(1.0), x0 + w, pn.py(1.0), "#000000", 0.6, ' stroke-dasharray="2.5 1.5"')
            syss = SYS if k != 1 else SYS[1:]
            vals = {0: d[p]["sp"], 1: d[p]["pm"], 2: d[p]["en"]}[k]
            labs = {0: d[p]["tok"], 1: d[p]["pm"], 2: d[p]["en"]}[k]
            n = len(syss)
            slot = w / (n + 0.3)
            bw = slot * 0.72
            top = ax["ylim"][1]
            for i, s in enumerate(syss):
                cx = x0 + slot * (i + 0.65)
                v = vals[s]
                fill, edge = colours(s)
                yv = pn.py(min(v, top))
                fig.o.append(f'<rect x="{cx - bw / 2:.2f}" y="{yv:.2f}" width="{bw:.2f}" height="{y0 + box_h - yv:.2f}" '
                             f'fill="{fill}" stroke="{edge}" stroke-width="{BAR_LW}"/>')
                if v > top:     # clipped bar: break mark, value inside the bar
                    yb = y0 + 7.0
                    fig.o.append(f'<rect x="{cx - bw / 2 - 1:.2f}" y="{yb:.2f}" width="{bw + 2:.2f}" height="2.2" fill="#FFFFFF"/>')
                    fig.text(cx, y0 + 16.5, fmt(labs[s]), FT, "middle")
                else:           # white ground under the value, so the dashed 1.0 line never crosses it
                    lw_ = width(fmt(labs[s]), FT)
                    fig.o.append(f'<rect x="{cx - lw_ / 2 - 0.6:.2f}" y="{yv - 1.6 - FT * 0.74:.2f}" width="{lw_ + 1.2:.2f}" '
                                 f'height="{FT * 0.74 + 0.6:.2f}" fill="#FFFFFF"/>')
                    fig.text(cx, yv - 1.6, fmt(labs[s]), FT, "middle")
            pn.finish()
    fig.write("fig_e2e", "scripts/make_fig_e2e.py")


if __name__ == "__main__":
    main()
