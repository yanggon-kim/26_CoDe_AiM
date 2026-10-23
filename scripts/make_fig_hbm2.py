#!/usr/bin/env python3
"""Figure 6 (Sec. VI-B): the edge server, CoDe (V = 4) vs P3-LLM-style (stock AiM as the reference), HBM2, W4A8.

Batched decode step, geometric mean over five LLMs (L = 4K): (a) tokens per second (M requests, one token each) with
P3-LLM's NPU as the host line; (b) the same per logic mm^2 (16 pseudo-channels). Reads dac_fig6_hbm2.csv of the
EV-58 pack (scripts/dac_data.py); the prose bands are asserted in make_tables.py. Plotted points (user, 2026-10-17):
M = 1, 2, 4, ..., 64; the prose's crossovers come from the full M grid.
Writes figs/src/fig_hbm2.html (inline SVG at the column width, scripts/svgchart.py); then
  python3 scripts/html2pdf.py fig_hbm2  ->  figs/fig_hbm2.pdf (+ .png preview).
"""
from dac_data import KEY, f, r2, read
from svgchart import COLUMNWIDTH, I, Fig, Panel, lin_ticks, row

DESIGNS = ["stock", "p3", "code"]
POW2 = [1, 2, 4, 8, 16, 32, 64]


def main():
    rows = [r for r in read("dac_fig6_hbm2.csv") if r["model"].startswith("gmean")]
    ser = {}
    for d in DESIGNS:
        p = sorted((int(r["M"]), f(r["tok_s"]), f(r["tok_s_per_logic_mm2"]), f(r["T_npu_us"]))
                   for r in rows if r["design"] == KEY["hbm2"][d])
        ser[d] = p
    # geomean ratios at M = 8 agree with the bands the prose prints (1.68 speed, 1.26 per mm^2)
    c8 = dict((m, (t, a)) for m, t, a, _ in ser["code"])[8]
    p8 = dict((m, (t, a)) for m, t, a, _ in ser["p3"])[8]
    assert r2(c8[0] / p8[0]) == 1.68 and r2(c8[1] / p8[1]) == 1.26
    pts = {d: [x for x in ser[d] if x[0] in POW2] for d in DESIGNS}
    for d in DESIGNS:
        assert [x[0] for x in pts[d]] == POW2, d
    npu = [(m, m * 1e6 / tn) for m, _, _, tn in pts["code"]]
    axes = []
    for k in (1, 2):
        vmax = max([x[k] for d in DESIGNS for x in pts[d]] + ([v for _, v in npu] if k == 1 else []))
        ylim, yt = lin_ticks(vmax)
        axes.append(dict(ylim=ylim, ylog=False, yticks=yt))
    fig = Fig(COLUMNWIDTH, 117.0)
    top, bottom = 21.0, 117.0 - 19.3
    fig.legend(["host", "stock", "p3", "code"], 7.0, sample=13.0, gap=2.0, space=6.0)
    for (x0, w, ylx), ax, (k, title, ylab) in zip(row(fig, axes, top, bottom, gap=3.0), axes,
                                                  ((1, "(a) Batch step", "tok/s"), (2, "(b) Per logic mm\u00b2", "tok/s / mm\u00b2"))):
        pn = Panel(fig, x0, top, w, bottom - top, (1, 64), [1, 4, 16, 64], ax["ylim"], False, ax["yticks"])
        pn.frame(title, "batch " + I("M"), ylab, ylx)
        if k == 1:
            pn.series("host", npu)
        for d in sorted(DESIGNS, key=lambda d: d != "code"):     # CoDe beneath the rivals
            pn.series(d, [(x[0], x[k]) for x in pts[d]])
        pn.finish()
    fig.write("fig_hbm2", "scripts/make_fig_hbm2.py")


if __name__ == "__main__":
    main()
