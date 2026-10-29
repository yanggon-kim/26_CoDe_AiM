#!/usr/bin/env python3
"""Fig. breakdown (Sec. III-B): stock AiM's GEMM time by component, M = 8, one channel, normalized to 100 %.

Four horizontal stacked bars: mobile one tile (K 2048 x N 64, INT8, channel 28), mobile q_proj of Llama-2-7B
(4096 x 4096), edge-server one tile (K 4096 x N 256, W4A8, channel 30), edge-server q_proj of Llama-3.1-8B; the absolute
GEMM time is printed at each bar's end. Segments: MAC useful beats, MAC idle beats, row switch, token load, token drain,
refresh. The "other" class (MAC16 stall + time before the first command + residual, at most 0.015 % of a bar) is left
out of the bars; III-B's paragraph says so.

Source (read only): evaluation/dac_2x2/figures/tab_umac_kernel_stock.csv (stock rows of umac_kernel, microarch 170254c,
collected at evaluation 472414f, context Sec. 2j; phone rows re-collected after the JEDEC refresh fix, evaluation
c2ad6f9, Sec. 2p: the phone bars gain a refresh segment) and evaluation/dac_2x2/touched.csv (umac.kernel.* ids: GB fill
amortization). Asserts every share the figure draws and every number the III-B prose prints from this kernel.
Writes figs/src/fig_breakdown.html; scripts/html2pdf.py fig_breakdown turns it into figs/fig_breakdown.pdf.
"""
import csv
import os

from dac_data import EVAL
from svgchart import BOX_LW, COLUMNWIDTH, FL, FT, GRID, GRID_LW, TICK_LW, Fig, width

CSV = os.path.join(EVAL, "dac_2x2", "figures", "tab_umac_kernel_stock.csv")
TOUCHED = os.path.join(EVAL, "dac_2x2", "touched.csv")
BARS = [("phone", "W1", "Mobile, one tile"), ("phone", "W2", "Mobile, q_proj"),
        ("hbm2", "W1", "Server, one tile"), ("hbm2", "W2", "Server, q_proj")]
# (legend label, CSV component prefix, fill): MAC slot in a luminance ramp (useful dark -> idle white), the row-switch
# commands in one tint, the token load / drain commands and refresh in greys
SEGS = [("MAC useful", "MAC useful beats", "#303030"),
        ("MAC idle", "MAC idle beats", "#FFFFFF"),
        ("row switch", "row switch", "#CFE2F3"),
        ("token load", "token load", "#B0B0B0"),
        ("token drain", "token drain", "#E3E3E3"),
        ("refresh", "refresh", "#7A7A7A")]
# shares the figure draws (%, 2 dp; the brief's check table = context Sec. 2j)
WANT = {("phone", "W1"): (14.07, 42.22, 8.59, 28.25, 0.70, 6.16),
        ("phone", "W2"): (17.98, 53.95, 19.53, 0.56, 0.84, 7.13),
        ("hbm2", "W1"): (14.24, 42.72, 10.22, 28.48, 0.71, 3.62),
        ("hbm2", "W2"): (19.14, 57.42, 13.81, 2.39, 0.99, 6.25)}
TOTAL_US = {("phone", "W1"): "4.55", ("phone", "W2"): "456", ("hbm2", "W1"): "7.19", ("hbm2", "W2"): "85.6"}


def load():
    data = {}
    for r in csv.DictReader(open(CSV)):
        assert r["design"] == "stock AiM", r["design"]
        d = data.setdefault((r["platform"], r["workload"]), {"comp": {}, "row": r})
        d["comp"][r["component"]] = (float(r["ns"]), float(r["share_pct"]), r["level"])
    return data


def seg(d, prefix):
    hits = [v for k, v in d["comp"].items() if k.startswith(prefix) and v[2] == "bar"]
    assert len(hits) == 1, (prefix, hits)
    return hits[0]


def checks(data):
    tid = {r["id"]: float(r["value"]) for r in csv.DictReader(open(TOUCHED))}
    for key, want in WANT.items():
        d = data[key]
        shares = tuple(round(seg(d, p)[1], 2) for _, p, _ in SEGS)
        assert shares == want, (key, shares)
        other = seg(d, "other")[1]
        assert other < 0.015, (key, other)                       # left out of the bars
        bar = [v for v in d["comp"].values() if v[2] == "bar"]
        tot = float(d["row"]["total_ns"])
        assert abs(sum(v[0] for v in bar) - tot) / tot < 1e-5, key      # the 7 bar classes sum to the total
        assert f"{tot / 1000:.3g}" == TOTAL_US[key], (key, tot)                 # 3 significant digits, in us
        # U is the useful share of the time; U_MAC = 1/4; f_MAC = the MAC-slot share (useful + idle)
        r = d["row"]
        assert abs(float(r["U"]) * 100 - seg(d, "MAC useful")[1]) < 1e-3, key
        assert float(r["U_MAC"]) == 0.25, key
        assert abs(float(r["f_MAC"]) * 100 - seg(d, "MAC useful")[1] - seg(d, "MAC idle")[1]) < 1e-3, key
        # idle beats = 3 x useful beats (a stock slot serves one token: one beat of four)
        assert abs(seg(d, "MAC idle")[0] - 3 * seg(d, "MAC useful")[0]) < 1e-6, key
    sh = {k: {p: seg(data[k], p)[1] for _, p, _ in SEGS} for k in WANT}
    nonmac = {k: 100 - sh[k]["MAC useful beats"] - sh[k]["MAC idle beats"] for k in WANT}
    # III-B prose (each value printed once):
    # Time breakdown: useful 14.1-19.1 %, idle 42.2-57.4 %, non-MAC commands 23.4-43.7 % across the four bars
    assert (round(min(v["MAC useful beats"] for v in sh.values()), 1), round(max(v["MAC useful beats"] for v in sh.values()), 1)) == (14.1, 19.1)
    assert (round(min(v["MAC idle beats"] for v in sh.values()), 1), round(max(v["MAC idle beats"] for v in sh.values()), 1)) == (42.2, 57.4)
    assert (round(min(nonmac.values()), 1), round(max(nonmac.values()), 1)) == (23.4, 43.7), nonmac
    # Idle beats: the largest segment of every bar
    assert all(max(v, key=v.get) == "MAC idle beats" for v in sh.values())
    # Idle beats: q_proj idle shares 53.9 % (mobile) and 57.4 % (edge server)
    assert round(sh[("phone", "W2")]["MAC idle beats"], 1) == 53.9 and round(sh[("hbm2", "W2")]["MAC idle beats"], 1) == 57.4
    # III-B mot-rowswitch-cost (q_proj shares only): row switch 19.5 % / 13.8 %, the largest non-MAC class on both
    # platforms; on the mobile platform above the useful beats' 18.0 %; edge useful 19.1 %
    PQ, HQ = ("phone", "W2"), ("hbm2", "W2")
    assert round(sh[PQ]["row switch"], 1) == 19.5 and round(sh[HQ]["row switch"], 1) == 13.8
    assert round(sh[PQ]["MAC useful beats"], 1) == 18.0 and round(sh[HQ]["MAC useful beats"], 1) == 19.1
    assert sh[PQ]["row switch"] > sh[PQ]["MAC useful beats"]
    for k in (PQ, HQ):
        assert sh[k]["row switch"] > max(sh[k]["token load"] + sh[k]["token drain"], sh[k]["refresh"]), k
    # mobile row-switch parts: the two TMODs 8.1 %, the ACT16 pair 8.5 % (8.545: not 8.6), together most of the 19.5 %
    part = {n: v[1] for n, v in data[PQ]["comp"].items() if v[2].startswith("part of row switch")}
    tmod, act = [next(v for n, v in part.items() if n.startswith(x)) for x in ("TMOD", "ACT16 pair")]
    assert (round(tmod, 1), round(act, 1)) == (8.1, 8.5) and tmod + act > sh[PQ]["row switch"] / 2
    assert abs(sum(part.values()) - sh[PQ]["row switch"]) < 1e-2                 # the four parts make the row switch
    # token load / drain at most 2.4 % / 1.0 % of q_proj; refresh 7.1 % / 6.2 % of q_proj
    assert (round(max(sh[k]["token load"] for k in (PQ, HQ)), 1), round(max(sh[k]["token drain"] for k in (PQ, HQ)), 1)) == (2.4, 1.0)
    assert round(sh[HQ]["refresh"], 1) == 6.2   # 6.245 %: 6.2, not 6.3 (no double rounding)
    assert round(sh[PQ]["refresh"], 1) == 7.1
    # edge server: all non-MAC commands together 23.4 % > useful 19.1 %
    assert round(nonmac[HQ], 1) == 23.4 and nonmac[HQ] > sh[HQ]["MAC useful beats"]
    # VI-C eval-vsweep-robust: the mobile one tile's token load 28.3 % of stock AiM's time (M = 8; one fill, one sweep);
    # guard only: edge one tile 28.5 %, q_proj 0.6 % (no longer printed)
    assert [round(sh[k]["token load"], 1) for k in WANT] == [28.3, 0.6, 28.5, 2.4]
    assert round(max(v["token drain"] for v in sh.values()), 1) == 1.0
    # one GB fill serves 64 row sweeps (mobile q_proj), 16 (server q_proj), 1 (one tile)
    for p, w, n in (("phone", "W2", 64), ("hbm2", "W2", 16), ("phone", "W1", 1), ("hbm2", "W1", 1)):
        assert tid[f"umac.kernel.{p}.{w}.row_groups_per_fill"] == n, (p, w)
    # channels and shapes the paragraph names
    for (p, w), (shape, ch) in {("phone", "W1"): ("2048x64", "28"), ("phone", "W2"): ("4096x4096", "28"),
                                ("hbm2", "W1"): ("4096x256", "30"), ("hbm2", "W2"): ("4096x4096", "30")}.items():
        assert (data[(p, w)]["row"]["shape"], data[(p, w)]["row"]["channel"]) == (shape, ch), (p, w)
    print("breakdown: useful 14.1-19.1 %, idle 42.2-57.4 %, non-MAC 23.4-43.7 %; q_proj row switch 19.5 / 13.8 %, "
          "useful 18.0 / 19.1 %, TMOD 8.1 %, ACT16 8.5 %, load / drain <= 2.4 / 1.0 %, q_proj refresh 7.1 / 6.2 %, "
          "edge non-MAC 23.4 %; mobile one-tile token load 28.3 %")


def draw(data):
    W = COLUMNWIDTH
    lab_w = max(width(b[2], FT) for b in BARS) + 4.0
    tot_w = max(width(TOTAL_US[k] + " µs", FT) for k in TOTAL_US) + 4.0
    x0, x1 = lab_w + 1.0, W - tot_w - 1.0
    # legend: two rows of three swatches, centred over the plot box
    sw, gap, space = 7.0, 2.5, 9.0
    rows = [SEGS[:3], SEGS[3:]]
    col_w = [max(sw + gap + width(rows[r][c][0], FL) for r in range(2)) for c in range(3)]
    leg_w = sum(col_w) + space * 2
    leg_x = (x0 + x1) / 2 - leg_w / 2
    top = 1.0 + FL
    bar_h, pitch, divider = 10.0, 14.0, 6.0
    y_box = top + FL + 1.0 + 6.0
    ys, y = [], y_box + 4.0
    for i in range(len(BARS)):
        if i == 2:
            y += divider
        ys.append(y)
        y += pitch
    y_bot = y - pitch + bar_h + 4.0
    H = y_bot + FT + 2.0 + FL + 2.0
    fig = Fig(W, round(H + 0.5))
    for r, items in enumerate(rows):
        x = leg_x
        for c, (lab, _, col) in enumerate(items):
            yy = top + r * (FL + 1.0)
            fig.o.append(f'<rect x="{x:.2f}" y="{yy - sw + 0.6:.2f}" width="{sw}" height="{sw - 0.6:.2f}" fill="{col}" '
                         f'stroke="#000000" stroke-width="0.5"/>')
            fig.text(x + sw + gap, yy, lab, FL)
            x += col_w[c] + space
    sx = lambda pct: x0 + (x1 - x0) * pct / 100.0   # noqa: E731
    for t in (25, 50, 75):
        fig.line(sx(t), y_box, sx(t), y_bot, GRID, GRID_LW)
    ym = (ys[1] + bar_h + ys[2]) / 2
    fig.line(x0, ym, x1, ym, "#000000", 0.5)
    for (p, w, lab), yb in zip(BARS, ys):
        d = data[(p, w)]
        acc = 0.0
        for _, prefix, col in SEGS:
            s = seg(d, prefix)[1]
            if s <= 0:
                continue
            fig.o.append(f'<rect x="{sx(acc):.2f}" y="{yb:.2f}" width="{sx(acc + s) - sx(acc):.3f}" height="{bar_h}" '
                         f'fill="{col}" stroke="#000000" stroke-width="0.4"/>')
            acc += s
        fig.text(x0 - 3.0, yb + bar_h / 2 + FT * 0.34, lab, FT, "end")
        fig.text(x1 + 3.0, yb + bar_h / 2 + FT * 0.34, TOTAL_US[(p, w)] + " µs", FT, "start")
    for t in (0, 25, 50, 75, 100):
        fig.line(sx(t), y_bot, sx(t), y_bot - 2.5, sw=TICK_LW)
        fig.line(sx(t), y_box, sx(t), y_box + 2.5, sw=TICK_LW)
        fig.text(sx(t), y_bot + FT + 1.0, f"{t}", FT, "middle")
    fig.o.append(f'<rect x="{x0:.2f}" y="{y_box:.2f}" width="{x1 - x0:.2f}" height="{y_bot - y_box:.2f}" fill="none" '
                 f'stroke="#000000" stroke-width="{BOX_LW}"/>')
    fig.text((x0 + x1) / 2, y_bot + FT + 2.0 + FL, "share of the GEMM time (%)", FL, "middle")
    fig.write("fig_breakdown", "scripts/make_fig_breakdown.py from evaluation/dac_2x2/figures/tab_umac_kernel_stock.csv")


def main():
    data = load()
    checks(data)
    draw(data)


if __name__ == "__main__":
    main()
