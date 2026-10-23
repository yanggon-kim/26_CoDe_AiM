#!/usr/bin/env python3
"""Figure 5 (Sec. VI-A): the phone, CoDe vs LP-Spec-style (stock AiM as the reference), INT8, LPDDR5-6400.

(a) speculative-verify decode step of Llama-2-7B at L = 1024: tokens per second (M rows per step) with the 8 Gen 3
    NPU (42 GB/s) as the host line; (b) GEMM throughput per logic mm^2 (geomean of six Llama FC shapes);
(c) attention layer per logic mm^2 (geomean of three head configurations, L = 1024); (d) decode step per logic mm^2
(L = 1024). Logic area summed over the four dies. Reads dac_fig5_phone.csv of the EV-58 pack (scripts/dac_data.py);
the prose ranges (over every L) are asserted in make_tables.py. Plotted points (user, 2026-10-17): M = 1, 2, 4, ..., 64
(16 for the attention layer); the prose's crossovers come from the full M grid.
Writes figs/src/fig_phone.html (inline SVG at the text width, scripts/svgchart.py); then
  python3 scripts/html2pdf.py fig_phone  ->  figs/fig_phone.pdf (+ .png preview).
"""
from dac_data import KEY, f, r2, read
from svgchart import FL, I, TEXTWIDTH, Fig, Panel, lin_ticks, log_ticks, loglerp, row

DESIGNS = ["stock", "lpspec", "code"]


def series(rows, level, design, col, L=None, wl=None):
    pts = []
    for r in rows:
        if not r["level"].startswith(level) or r["design"] != KEY["phone"][design]:
            continue
        if L is not None and r["L"] != L:
            continue
        if wl is not None and r["workload"] != wl:
            continue
        pts.append((int(r["M"]), f(r[col]), f(r["t_npu_us"])))
    pts.sort()
    return pts


POW2 = [1, 2, 4, 8, 16, 32, 64]


def main():
    rows = read("dac_fig5_phone.csv")
    gm = "gmean over 3 head configs"
    spec = [("decode", "throughput", "1024", None, "(a) Decode step", "tok/s"),
            ("GEMM", "per_logic_mm2", None, None, "(b) GEMM, per mm²", "GOPS / mm²"),
            ("attention", "per_logic_mm2", "1024", gm, "(c) Attention layer, per mm²", "tok/s / mm²"),
            ("decode", "per_logic_mm2", "1024", None, "(d) Decode step, per mm²", "tok/s / mm²")]
    data, axes = [], []
    for lev, col, L, wl, title, ylab in spec:
        xm = 16 if lev == "attention" else 64
        ser = {d: [(m, v) for m, v, _ in series(rows, lev, d, col, L, wl) if m in POW2] for d in DESIGNS}
        for d in DESIGNS:
            assert [m for m, _ in ser[d]] == [m for m in POW2 if m <= xm], (lev, d)
        npu = None
        if lev == "decode" and col == "throughput":
            npu = [(m, m * 1e6 / t) for m, _, t in series(rows, lev, "stock", col, L, wl) if m in POW2]
            axes.append(dict(ylim=(4, 2500), ylog=True, yticks=log_ticks(4, 2500)))
        else:
            ylim, yt = lin_ticks(max(v for d in DESIGNS for _, v in ser[d]))
            axes.append(dict(ylim=ylim, ylog=False, yticks=yt))
        data.append((lev, L, wl, title, ylab, xm, ser, npu))
    fig = Fig(TEXTWIDTH, 126.0)
    top, bottom = 21.0, 126.0 - 19.3
    fig.legend(["host", "stock", "lpspec", "code"], 7.0, labels={"host": "Host NPU (42 GB/s)"})
    for (x0, w, ylx), ax, (lev, L, wl, title, ylab, xm, ser, npu) in zip(row(fig, axes, top, bottom), axes, data):
        pn = Panel(fig, x0, top, w, bottom - top, (1, xm), [t for t in (1, 4, 16, 64) if t <= xm], ax["ylim"],
                   ax["ylog"], ax["yticks"])
        pn.frame(title, "token rows " + I("M"), ylab, ylx)
        if npu:
            pn.series("host", npu)
        for d in sorted(DESIGNS, key=lambda d: d != "code"):     # CoDe beneath the rivals
            pn.series(d, ser[d])
        if npu:
            # CoDe's last M ahead of the NPU at L = 1024 (the prose prints 24-28 over L 128-1024), from the full grid
            c = series(rows, lev, "code", "t_us", L, wl)
            win = max(m for m, t, tn in c if t < tn)
            assert win == 24, win
            # the plotted points agree: CoDe ahead of the NPU at M = 16, behind at M = 32
            cd, hn = dict(ser["code"]), dict(npu)
            assert cd[16] > hn[16] and cd[32] < hn[32]
            # the leader ends on the drawn NPU segment at M = 24, within 0.5 % of the NPU's own value there
            tn24 = dict((m, tn) for m, _, tn in c)[win]
            yv = loglerp(npu, win)
            assert abs(yv / (win * 1e6 / tn24) - 1) < 5e-3
            pn.note(1.3, 1100, ["CoDe ahead", "to " + I("M") + f" = {win}"], "start", to=(win, yv),
                    attach=(pn.px(1.3) + 40, pn.py(1100) + FL * 0.8))
        pn.finish()
    # the per-mm^2 lead at M = 5 (decode step, L = 1024) that the prose bounds (1.86-2.84 over every L)
    d5 = {d: dict((m, v) for m, v, _ in series(rows, "decode", d, "per_logic_mm2", "1024")) for d in DESIGNS}
    assert 2.83 <= r2(d5["code"][5] / d5["lpspec"][5]) <= 2.84
    fig.write("fig_phone", "scripts/make_fig_phone.py")


if __name__ == "__main__":
    main()
