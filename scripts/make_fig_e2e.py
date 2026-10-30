#!/usr/bin/env python3
"""Figure 8 (Sec. VI-B/C, fig:e2e): end-to-end decoding on five systems, both platforms, as bars.

Systems (user, 2026-10-30): NPU only; NPU + X for X = stock AiM, P3-LLM-style, LP-Spec-style, CoDe, where PIM design X
runs every weight GEMM and attention and the NPU the element-wise work. Rows: mobile platform (speculative loop of
Llama-2-7B, M = 4, L 1024, acceptance 0.7, 1.1B draft, NPU 42 GB/s, synthesised PU energy, reads priced) and edge
server (batch 8, gmean of five LLMs, W4A8, energy at the NPU's 55 W idle). Columns: (a) speed-up over NPU only, tok/s
printed on the bars; (b) tok/s per logic mm^2 normalised to LP-Spec-style (PIM designs only); (c) energy per token (mJ).
Source (read only): the ISCA evaluation ids, evaluation f896213 / 77a9b9d:
  isca.e2e.phone.<npu|stock|h3|h2|core8>.*, isca.e2e.phone.core8_over_h2.{per_mm2,speed_M5,speed_Mge5.*},
  isca.e2e.phone.h3.best_M.d1b / best_tok_s.d1b and x.ev56.e2e.d1b.<d>.{best_M,tok_s} (evaluation/dac_sd8g3, Sec. 2f);
  isca.e2e.hbm2.<npu|stock|p3_500|h2|core4>.*, isca.e2e.hbm2.npu_overtakes.core4.* (evaluation/dac_2x2, Sec. 2p);
  the best-M rows also against evaluation/dac_sd8g3/raw/ev56_best.csv (L 1024, d1b, alpha 0.7).
Every number Secs. VI-B and VI-C print about Fig. 8 is asserted in check_prose_numbers(). Writes figs/src/fig_e2e.html;
then  python3 scripts/html2pdf.py fig_e2e  ->  figs/fig_e2e.pdf (+ .png preview).
"""
import csv
import os

from dac_data import PHONE_RAW, ids, r2
from svgchart import FL, FT, TEXTWIDTH, Fig, I, Panel, row, width

SYS = ["npu", "stock", "p3", "lpspec", "code"]
LABEL = {"npu": "NPU only", "stock": "NPU + stock AiM", "p3": "NPU + P3-LLM-style", "lpspec": "NPU + LP-Spec-style",
         "code": "NPU + CoDe"}
KEY = {"phone": {"npu": "npu", "stock": "stock", "p3": "h3", "lpspec": "h2", "code": "core8"},
       "hbm2": {"npu": "npu", "stock": "stock", "p3": "p3_500", "lpspec": "h2", "code": "core4"}}
TOPIC = {"phone": "dac_sd8g3", "hbm2": "dac_2x2"}
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
        g = lambda s, c: tid[f"isca.e2e.{p}.{KEY[p][s]}.{c}"]  # noqa: E731
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
    # eval-e2e-phone: CoDe 4.37x NPU only at 46.4 tok/s, LP-Spec-style 4.34x at 46.1, P3-LLM-style 2.96x, stock AiM 1.81x
    assert [r2(ph["sp"][s]) for s in ("stock", "p3", "lpspec", "code")] == [1.81, 2.96, 4.34, 4.37]
    assert round(ph["tok"]["code"], 1) == 46.4 and round(ph["tok"]["lpspec"], 1) == 46.1
    # best M of each system (L 1024, 1.1B draft, alpha 0.7): CoDe / LP-Spec-style 47.1 / 46.8 at M = 3, P3-LLM-style 43.8 at
    # M = 2, stock AiM 26.5 at M = 2, NPU only 10.6 at M = 4 (= the M = 4 bar)
    with open(os.path.join(PHONE_RAW, "ev56_best.csv")) as fh:
        best = {r["mapping"]: (int(r["best_M"]), float(r["tok_s"])) for r in csv.DictReader(fh)
                if r["row_id"].startswith("npu42/1024/d1b/") and r["alpha"] == "0.7"}
    want = {"all_core": (3, 47.1), "all_h2": (3, 46.8), "all_h3": (2, 43.8), "all_stock": (2, 26.5), "all_npu": (4, 10.6)}
    for m, (bm, ts) in want.items():
        assert best[m][0] == bm and round(best[m][1], 1) == ts, (m, best[m])
        if m != "all_h3":
            assert pt[f"x.ev56.e2e.d1b.{m}.best_M"] == bm and abs(pt[f"x.ev56.e2e.d1b.{m}.tok_s"] - best[m][1]) < 1e-9
    assert pt["isca.e2e.phone.h3.best_M.d1b"] == 2 and abs(pt["isca.e2e.phone.h3.best_tok_s.d1b"] - best["all_h3"][1]) < 1e-9
    assert abs(best["all_npu"][1] - ph["tok"]["npu"]) < 1e-9
    # eval-e2e-phone setting (user, 2026-10-30): a chain round yields (1 - a^M) / (1 - a) tokens on average (checked
    # against ev56_chain's T_round x tok/s), below 1 / (1 - 0.7) = 3.3; M = 4 is NPU only's best M and within 2 % of
    # the best of NPU + CoDe (1.5 %) and NPU + LP-Spec-style (1.7 %)
    with open(os.path.join(PHONE_RAW, "ev56_chain.csv")) as fh:
        cr = {r["row_id"]: r for r in csv.DictReader(fh)}
    for M in range(2, 17):
        r = cr[f"npu42/1024/d1b/all_core/{M}/0.7"]
        n = float(r["tok_s"]) * float(r["T_round_us"]) * 1e-6
        assert abs(n - (1 - 0.7 ** M) / (1 - 0.7)) < 1e-6 and n < 1 / (1 - 0.7), (M, n)
    assert round(1 / (1 - 0.7), 1) == 3.3
    assert best["all_npu"][0] == 4
    gap = {s: 1 - ph["tok"][s] / best[m][1] for m, s in (("all_core", "code"), ("all_h2", "lpspec"))}
    assert (round(100 * gap["code"], 1), round(100 * gap["lpspec"], 1)) == (1.5, 1.7) and max(gap.values()) < 0.02, gap
    # VI-D eval-vsweep-choice: the loop's best M with an EAGLE head is 4 (L 1024, alpha 0.7)
    with open(os.path.join(PHONE_RAW, "ev56_best.csv")) as fh:
        assert next(int(r["best_M"]) for r in csv.DictReader(fh) if r["row_id"] == "npu42/1024/eagle/all_core/0.7") == 4
    assert best["all_core"][1] > best["all_h2"][1] > best["all_h3"][1] > best["all_stock"][1] > best["all_npu"][1]
    # past M = 4 CoDe's loop leads LP-Spec-style: 1.07x at M = 8 and at M = 16 (powers of two, as Fig. 7; no claim at
    # LP-Spec-style's partial-tile dip M = 5). Read from the collected ev56_chain rows (L 1024, 1.1B draft, alpha 0.7);
    # the M >= 5 band agrees with the collected ids isca.e2e.phone.core8_over_h2.speed_Mge5.*
    with open(os.path.join(PHONE_RAW, "ev56_chain.csv")) as fh:
        ch = {r["row_id"]: float(r["tok_s"]) for r in csv.DictReader(fh)}
    lead = {M: ch[f"npu42/1024/d1b/all_core/{M}/0.7"] / ch[f"npu42/1024/d1b/all_h2/{M}/0.7"] for M in range(4, 17)}
    assert abs(lead[4] - pt["isca.e2e.phone.core8_over_h2.speed"]) < 1e-9
    assert abs(min(lead[M] for M in range(5, 17)) - pt["isca.e2e.phone.core8_over_h2.speed_Mge5.min"]) < 1e-9
    assert abs(max(lead[M] for M in range(5, 17)) - pt["isca.e2e.phone.core8_over_h2.speed_Mge5.max"]) < 1e-9
    assert r2(lead[8]) == 1.07 == r2(lead[16]), (lead[8], lead[16])
    # eval-e2e-server: CoDe = LP-Spec-style 1.28x NPU only (456 tok/s); stock 0.45x, P3-LLM-style 0.76x; CoDe 1.68x P3
    assert [r2(hb["sp"][s]) for s in ("stock", "p3", "lpspec", "code")] == [0.45, 0.76, 1.28, 1.28]
    assert hb["tok"]["code"] == hb["tok"]["lpspec"] and round(hb["tok"]["code"]) == 456
    assert all(hb["sp"][s] < 1 for s in ("stock", "p3"))
    assert r2(ht["isca.e2e.hbm2.core4_over_p3_500.speed"]) == 1.68
    # NPU only overtakes CoDe from batch 16 on the gmean (CoDe last ahead at 12)
    assert ht["isca.e2e.hbm2.npu_overtakes.core4.gmean.first_npu_M"] == 16 and ht["isca.e2e.hbm2.npu_overtakes.core4.gmean.last_pim_M"] == 12
    # eval-e2e-phone setting: batch 8 = the largest power of two at which CoDe still leads NPU only
    lead_b = ht["isca.e2e.hbm2.npu_overtakes.core4.gmean.last_pim_M"]
    assert max(2 ** k for k in range(8) if 2 ** k <= lead_b) == 8 < ht["isca.e2e.hbm2.npu_overtakes.core4.gmean.first_npu_M"]
    # eval-e2e-per-mm2: CoDe / LP-Spec-style 1.87x (mobile), 1.79x (edge); CoDe / P3-LLM-style 1.10x, 1.26x
    assert r2(ph["pm"]["code"]) == 1.87 == r2(pt["isca.e2e.phone.core8_over_h2.per_mm2"])
    assert r2(hb["pm"]["code"]) == 1.79 == r2(ht["isca.e2e.hbm2.core4_over_h2.per_mm2"])
    assert r2(pt["isca.e2e.phone.core8_over_h3.per_mm2"]) == 1.10 and r2(ht["isca.e2e.hbm2.core4_over_p3_500.per_mm2"]) == 1.26
    assert r2(pt["isca.e2e.phone.core8_over_h2.speed"]) == 1.01 and ht["isca.e2e.hbm2.core4_over_h2.speed"] == 1.0
    # eval-energy, mobile: CoDe 70.5 mJ/token; NPU only 7.9x, stock AiM 1.80x, P3-LLM-style 1.28x, LP-Spec-style 1.04x CoDe's
    e = ph["en"]
    assert round(e["code"], 1) == 70.5
    assert round(e["npu"] / e["code"], 1) == 7.9
    assert r2(pt["isca.e2e.phone.stock_over_core8.mJ"]) == 1.80 and abs(e["stock"] / e["code"] - pt["isca.e2e.phone.stock_over_core8.mJ"]) < 1e-9
    assert r2(pt["isca.e2e.phone.h3_over_core8.mJ"]) == 1.28 and r2(pt["isca.e2e.phone.h2_over_core8.mJ"]) == 1.04
    assert min(e, key=e.get) == "code"
    # eval-energy, edge server at 55 W idle: NPU only 1.48x, P3-LLM-style 1.64x CoDe's; LP-Spec-style ties (1.00x);
    # gated NPU (0 W): P3-LLM-style 1.46x, NPU only 2.46x
    assert r2(ht["isca.e2e.hbm2.npu_over_core4.mJ_55W"]) == 1.48 and r2(ht["isca.e2e.hbm2.p3_500_over_core4.mJ_55W"]) == 1.64
    assert r2(ht["isca.e2e.hbm2.h2_over_core4.mJ_55W"]) == 1.00
    assert r2(ht["isca.e2e.hbm2.p3_500_over_core4.mJ_0W"]) == 1.46 and r2(ht["isca.e2e.hbm2.npu_over_core4.mJ_0W"]) == 2.46
    assert abs(hb["en"]["npu"] / hb["en"]["code"] - ht["isca.e2e.hbm2.npu_over_core4.mJ_55W"]) < 1e-9
    assert min(hb["en"], key=hb["en"].get) == "code"
    # abstract / intro / conclusion: 1.87x per mm2 at matched speed (mobile); 1.68x, 1.26x, 1.64x (edge server)
    print("Secs. VI-B/C numbers hold: mobile 4.37 / 4.34 / 2.96 / 1.81x, best M 47.1 / 46.8 / 43.8 / 26.5 / 10.6, M = 8 / 16 1.07x; "
          "edge 1.28 / 1.28 / 0.76 / 0.45x, 1.68x, NPU from batch 16; per mm2 1.87 / 1.79, 1.10 / 1.26; energy 70.5 mJ, "
          "7.9 / 1.80 / 1.28 / 1.04x; edge 1.48 / 1.64x (gated 1.46 / 2.46x)")


def fmt(v):
    return f"{v:.0f}" if v >= 99.5 else f"{v:.1f}" if v >= 9.95 else f"{v:.2f}"


def main():
    d = load()
    check_prose_numbers(d)
    W, H = TEXTWIDTH, 178.0
    fig = Fig(W, H)
    fig.o.append(DEFS)
    fig.legend_patches([(LABEL[s],) + colours(s) for s in SYS], 8.5)
    box_h, rows_y = 62.0, (24.0, 104.0)
    spec = {"phone": [dict(ylim=(0, 5.6), yticks=[0, 1, 2, 3, 4, 5]), dict(ylim=(0, 2.3), yticks=[0, 0.5, 1, 1.5, 2]),
                      dict(ylim=(0, 165), yticks=[0, 50, 100, 150])],
            "hbm2": [dict(ylim=(0, 1.65), yticks=[0, 0.5, 1, 1.5]), dict(ylim=(0, 2.3), yticks=[0, 0.5, 1, 1.5, 2]),
                     dict(ylim=(0, 470), yticks=[0, 100, 200, 300, 400])]}
    titles = ["(a) Speed-up over NPU only", "(b) Tok/s per logic mm², normalized", "(c) Energy per token"]
    ylabs = ["speed-up", "÷ LP-Spec-style", "mJ / token"]
    for (p, rlab), y0 in zip((("phone", ["Mobile", I("M") + " = 4"]), ("hbm2", ["Edge server", "batch 8"])), rows_y):
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
                    yb = y0 + 9.0
                    fig.o.append(f'<rect x="{cx - bw / 2 - 1:.2f}" y="{yb:.2f}" width="{bw + 2:.2f}" height="2.2" fill="#FFFFFF"/>')
                    fig.text(cx, y0 + 19.5, fmt(labs[s]), FT, "middle")
                else:           # white ground under the value, so the dashed 1.0 line never crosses it
                    lw_ = width(fmt(labs[s]), FT)
                    fig.o.append(f'<rect x="{cx - lw_ / 2 - 0.6:.2f}" y="{yv - 1.6 - FT * 0.74:.2f}" width="{lw_ + 1.2:.2f}" '
                                 f'height="{FT * 0.74 + 0.6:.2f}" fill="#FFFFFF"/>')
                    fig.text(cx, yv - 1.6, fmt(labs[s]), FT, "middle")
            pn.finish()
    fig.write("fig_e2e", "scripts/make_fig_e2e.py")


if __name__ == "__main__":
    main()
