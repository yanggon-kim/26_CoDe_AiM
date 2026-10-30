#!/usr/bin/env python3
"""Figure 7 (Sec. VI-A, fig:gemm): GEMM speed and area efficiency against M, both platforms, four PIM designs + the NPU.

Rows: mobile platform (LPDDR5-6400, INT8, gmean of six Llama FC shapes) and edge server (HBM2, W4A8, gmean of the 25 FC
shapes of five LLMs). Columns: (a) GEMM speed-up over stock AiM, with the NPU's GEMM as a line; (b) GEMM throughput
(GOPS) per logic mm^2 (four dies / 16 pseudo-channels). Level = kernel + drain on both platforms (user, 2026-10-30).
Source (read only): the ISCA evaluation ids, evaluation f896213 / 77a9b9d:
  isca.gemm.phone.M<M>.<stock|h3|h2|core8|npu>.*  (evaluation/dac_sd8g3/touched.csv, context Sec. 2f)
  isca.gemm.hbm2.M<M>.<stock|p3_500|h2|core4|npu>.*  (evaluation/dac_2x2/touched.csv, context Sec. 2p)
Plotted: M = 1, 2, 4, 8, 16, 32, 64 (powers of two; user, 2026-10-30), out of the collected grid 1-6, 8, 12, 16, 24,
32, 48, 64. Every range Sec. VI-A prints is taken over the plotted M only and asserted in check_prose_numbers(); the
mechanism claims ("beyond M = 2", "CoDe = LP-Spec-style up to M = D") are asserted over the whole collected grid. Writes figs/src/fig_gemm.html; then
  python3 scripts/html2pdf.py fig_gemm  ->  figs/fig_gemm.pdf (+ .png preview).
"""
from dac_data import KEY, ids, r2
from svgchart import FL, TEXTWIDTH, I, Fig, Panel, lin_ticks, row

MS = [1, 2, 4, 8, 16, 32, 64]                                 # plotted, and the M every printed range spans
MS_ALL = [1, 2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 48, 64]        # collected grid
DESIGNS = ["stock", "p3", "lpspec", "code"]
TOPIC = {"phone": "dac_sd8g3", "hbm2": "dac_2x2"}
D = 4


def load():
    out = {}
    for p, t in TOPIC.items():
        tid = ids(t)
        g = lambda M, d, c: tid[f"isca.gemm.{p}.M{M}.{d}.{c}"]  # noqa: E731
        sp = {d: [(M, 1.0 if d == "stock" else g(M, KEY[p][d], "speedup_vs_stock")) for M in MS_ALL] for d in DESIGNS}
        pm = {d: [(M, g(M, KEY[p][d], "per_mm2")) for M in MS_ALL] for d in DESIGNS}
        npu = [(M, g(M, "npu", "speedup_vs_stock")) for M in MS_ALL]
        # the ids agree with themselves: speed-up = GOPS ratio, the stored per-mm2 ratios = the per-mm2 values' ratio
        for M in MS_ALL:
            for d in ("p3", "lpspec", "code"):
                assert abs(g(M, KEY[p][d], "gops") / g(M, "stock", "gops") - g(M, KEY[p][d], "speedup_vs_stock")) < 1e-9
            c = KEY[p]["code"]
            for r in ("lpspec", "p3", "stock"):
                assert abs(g(M, c, "per_mm2") / g(M, KEY[p][r], "per_mm2") - tid[f"isca.gemm.{p}.M{M}.{c}_over_{KEY[p][r]}.per_mm2"]) < 1e-9
        out[p] = dict(sp=sp, pm=pm, npu=npu)
    return out


def check_prose_numbers(data):
    """The numbers eval-gemm-summary / -speed / -per-mm2 print: ranges over the plotted M (MS) only; the mechanism
    claims over the whole collected grid (MS_ALL). No claim rests on a rival's partial-tile dip (M = 3, 5, ...)."""
    sp = {p: {d: dict(data[p]["sp"][d]) for d in DESIGNS} for p in data}
    pm = {p: {d: dict(data[p]["pm"][d]) for d in DESIGNS} for p in data}
    ratio = lambda p, a, b, M: pm[p][a][M] / pm[p][b][M]  # noqa: E731
    rng = lambda xs: (r2(min(xs)), r2(max(xs)))  # noqa: E731
    for p in data:
        # every design but stock AiM runs the same speed up to M = 2 (one column read serves every token)
        for M in (1, 2):
            v = [sp[p][d][M] for d in ("p3", "lpspec", "code")]
            assert max(v) - min(v) < 0.01 * max(v), (p, M, v)
        # CoDe outruns P3-LLM-style beyond M = 2, at every collected M
        assert all(sp[p]["code"][M] > 1.2 * sp[p]["p3"][M] for M in MS_ALL if M >= 3)
        # CoDe = LP-Spec-style up to M = D on both platforms; on the edge server at every M (V = D)
        assert all(abs(sp[p]["code"][M] / sp[p]["lpspec"][M] - 1) < 1e-9 for M in MS_ALL if M <= D)
    assert all(abs(sp["hbm2"]["code"][M] / sp["hbm2"]["lpspec"][M] - 1) < 1e-9 for M in MS_ALL)
    # "1.96-1.97x at M = 2"; "at M = 4 CoDe 3.74x / 3.82x, P3-LLM-style 1.95x on both"
    v2 = [sp[p][d][2] for p in data for d in ("p3", "lpspec", "code")]
    assert (r2(min(v2)), r2(max(v2))) == (1.96, 1.97), v2
    assert r2(sp["phone"]["code"][4]) == 3.74 and r2(sp["hbm2"]["code"][4]) == 3.82
    assert r2(sp["phone"]["p3"][4]) == 1.95 == r2(sp["hbm2"]["p3"][4])
    # mobile: CoDe's eight-token tile halves LP-Spec-style's row sweeps from M = 8: 1.11x its speed
    s8 = [sp["phone"]["code"][M] / sp["phone"]["lpspec"][M] for M in MS if M >= 8]
    assert {r2(x) for x in s8} == {1.11}, s8
    assert all(sp["phone"]["code"][M] > sp["phone"]["lpspec"][M] for M in MS_ALL if M > D)
    # per logic mm2 against LP-Spec-style: mobile 1.86x up to M = 4, 2.07x from M = 8; edge server 1.79x at every M
    assert {r2(ratio("phone", "code", "lpspec", M)) for M in MS if M <= 4} == {1.86}
    assert {r2(ratio("phone", "code", "lpspec", M)) for M in MS if M >= 8} == {2.07}
    assert {r2(ratio("hbm2", "code", "lpspec", M)) for M in MS_ALL} == {1.79}
    # area: CoDe's logic is 0.539x (mobile) and 0.56x (edge) LP-Spec-style's: per-mm2 ratio = speed ratio / area ratio
    for p, a in (("phone", 0.539), ("hbm2", 0.56)):
        ar = sp[p]["code"][1] / pm[p]["code"][1] * pm[p]["lpspec"][1] / sp[p]["lpspec"][1]
        assert round(ar, 3 if p == "phone" else 2) == a, (p, ar)
    # per logic mm2 against P3-LLM-style: mobile 1.43x at M = 4, 1.59x from M = 8; edge 1.46-1.47x from M = 4;
    # P3-LLM-style leads at M <= 2 on both (CoDe 0.75x)
    assert r2(ratio("phone", "code", "p3", 4)) == 1.43
    assert {r2(ratio("phone", "code", "p3", M)) for M in MS if M >= 8} == {1.59}
    h = [ratio("hbm2", "code", "p3", M) for M in MS if M >= 4]
    assert rng(h) == (1.46, 1.47), h
    low = [ratio(p, "code", "p3", M) for p in data for M in (1, 2)]
    assert {r2(x) for x in low} == {0.75}, low
    assert all(ratio(p, "code", "p3", M) > 1 for p in data for M in MS_ALL if M >= 3)
    print("Sec. VI-A numbers hold (M = 1, 2, 4, ..., 64): M = 2 1.96-1.97x; M = 4 3.74 / 3.82 vs 1.95; mobile M >= 8 "
          "1.11x LP speed; per mm2 vs LP 1.86 / 2.07 mobile, 1.79 edge; vs P3 1.43, 1.59 mobile, 1.46-1.47 edge, "
          "0.75 at M <= 2")


def clip(pts, top):
    """Plotted NPU points up to the frame's top, plus the unmarked vertex where the drawn line meets it (log-x, lin-y)."""
    import math
    keep = [(m, v) for m, v in pts if v <= top]
    nxt = [(m, v) for m, v in pts if v > top]
    if not nxt:
        return keep, []
    (m0, v0), (m1, v1) = keep[-1], nxt[0]
    t = (top - v0) / (v1 - v0)
    return keep, [(2 ** (math.log2(m0) + t * (math.log2(m1) - math.log2(m0))), top)]


def main():
    data = load()
    check_prose_numbers(data)
    W, H = TEXTWIDTH, 195.0
    fig = Fig(W, H)
    fig.legend(["stock", "p3", "lpspec", "code", "host"], 8.5, labels={"host": "NPU"})
    box_h, rows_y = 58.0, (24.0, 115.0)
    sp_ticks = [0, 1, 2, 3, 4, 5]
    for (p, rlab, xlab), y0 in zip((("phone", "Mobile platform", "token rows " + I("M")),
                                    ("hbm2", "Edge server", "batch " + I("M"))), rows_y):
        d = data[p]
        pm_lim, pm_t = lin_ticks(max(v for s in d["pm"].values() for m, v in s if m in MS))
        axes = [dict(ylim=(0, 5.0), ylog=False, yticks=sp_ticks), dict(ylim=pm_lim, ylog=False, yticks=pm_t)]
        lay = row(fig, axes, y0, y0 + box_h, left=12.0, gap=10.0)
        fig.text(4.0 + FL * 0.75, y0 + box_h / 2, rlab, FL, "middle",
                 f' transform="rotate(-90 {4.0 + FL * 0.75:.2f} {y0 + box_h / 2:.2f})"')
        for k, ((x0, w, ylx), ax) in enumerate(zip(lay, axes)):
            title = ("(a) GEMM speed-up over stock AiM", "(b) GEMM throughput per logic mm²")[k] if p == "phone" else ""
            pn = Panel(fig, x0, y0, w, box_h, (1, 64), MS, ax["ylim"], False, ax["yticks"])
            pn.frame(title, xlab, ("speed-up", "GOPS / mm²")[k], ylx)
            key = ("sp", "pm")[k]
            if k == 0:
                pts, knee = clip([(m, v) for m, v in d["npu"] if m in MS], 5.0)
                pn.series("host", pts, knees=knee)
            for des in sorted(DESIGNS, key=lambda x: x != "code"):     # CoDe beneath the rivals
                pn.series(des, [(m, v) for m, v in d[key][des] if m in MS])
            pn.finish()
    fig.write("fig_gemm", "scripts/make_fig_gemm.py")


if __name__ == "__main__":
    main()
