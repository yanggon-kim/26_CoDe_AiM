#!/usr/bin/env python3
"""Fig. sequence (Sec. IV-A) and Table cmds (Sec. IV-D): one weight row of Llama-2-7B's q_proj on the mobile platform,
M = 8, steady state, as the simulator issues it.

(a) Stock AiM sweeps the row eight times, one token each; (b) CoDe (V = 8, D = 4) sweeps it once for all eight tokens.
Both on one ns axis; per design a cmd lane (segments coloured by class: row-switch commands, MAC commands, token
drain) and a PU lane (busy beats, one CK each; stock computes one beat in four, CoDe every beat). A red span marks the
window ratio; brackets (1) and (2) under CoDe's PU lane mark the two components (beat filling: MAC slots; row reuse:
row switches).

Source (read only): evaluation/dac_2x2/raw/utrace_run_stock.csv and utrace_run_core8.csv (one steady row sweep of the
command log, channel 28; umac_trace @ microarch 86efbc6, collected at evaluation 472414f, context Sec. 2j),
raw/utrace_sum.csv (per-sweep totals), raw/ukern_phone_sum.csv (whole q_proj GEMM, umac_kernel @ 7e5124b / 170254c),
touched.csv (umac.kernel.phone.W2.row_groups_per_fill), and the EV-58 pack's dac_table4.csv (GB KB, Table II).
A window starts at the previous sweep's last MAC16 and ends at this sweep's last MAC16 (utrace_sum "run period"), so
eight stock windows tile 8 consecutive sweeps exactly; the K chunk's WRGB burst (once per 64 sweeps) is not in it.
Asserts every number Sec. IV prints from this trace. Writes figs/src/fig_sequence.html (then
python3 scripts/html2pdf.py fig_sequence) and tables/tab_cmds.tex.
"""
import csv
import os

from dac_data import EVAL, REPO, read
from svgchart import FL, FT, Fig, I, width

RAW = os.path.join(EVAL, "dac_2x2", "raw")
TOUCHED = os.path.join(EVAL, "dac_2x2", "touched.csv")
TCK = 1.25                      # ns, mobile CK (III-A), one PU beat
V, D, SWEEPS = 8, 4, 8
COL = {"row": "#CFE2F3", "mac": "#9A9A9A", "drain": "#000000", "beat": "#303030",
       "quarter": "#CBCBCB"}   # one busy beat in four, drawn as its average: 1/4 of #303030 over white
RED = "#E03127"


def window(name):
    rows = list(csv.DictReader(open(os.path.join(RAW, f"utrace_run_{name}.csv"))))
    run = [r for r in rows if r["part"] == "run MAC16"]
    last = max(int(r["row_id"]) for r in run)
    win = [r for r in rows if int(r["row_id"]) < last]            # previous last MAC16 .. this sweep's last MAC16
    t0 = float(win[0]["t_ns"])
    period = float(rows[last]["t_ns"]) - t0
    cls = {"MAC": "mac", "run framing": "row", "per-token": "drain"}
    segs = [(float(r["t_ns"]) - t0, float(r["t_ns"]) - t0 + float(r["gap_next_ns"]), cls[r["cls"]]) for r in win]
    assert abs(segs[-1][1] - period) < 1e-9 and all(abs(a[1] - b[0]) < 1e-9 for a, b in zip(segs, segs[1:]))
    assert not any(r["cmd"] in ("WRGB", "CASWRGB", "REFab") for r in win)          # no GB fill, no refresh in the window
    macs = [float(r["t_ns"]) - t0 for r in win if r["cmd"] == "MAC16"]
    counts = {c: sum(1 for r in win if r["cmd"] == c) for c in ("MAC16", "TMOD", "PREA", "ACT16-1", "ACT16-2",
                                                                "WRMAC16", "RDMAC16", "CASRDMAC16")}
    return segs, macs, period, counts


def merge(segs):
    out = []
    for a, b, c in segs:
        if out and out[-1][2] == c:
            out[-1] = (out[-1][0], b, c)
        else:
            out.append((a, b, c))
    return out


def checks():
    s = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(RAW, "utrace_sum.csv")))}
    st, st_mac, st_p, st_n = window("stock")
    co, co_mac, co_p, co_n = window("core8")
    assert st_p == float(s["stock/period"]["ns_per_run"]) == 406.25
    assert co_p == float(s["core8/period"]["ns_per_run"]) == 738.75
    stock_ns, code_ns = SWEEPS * st_p, co_p
    ratio = stock_ns / code_ns
    assert f"{stock_ns:,.0f}" == "3,250" and f"{code_ns:.2f}" == "738.75" and f"{ratio:.2f}" == "4.40"
    # MAC commands: 64 per sweep in both; stock sweeps 8 times -> 512, CoDe once -> 64 (one tile MAC per column)
    assert st_n["MAC16"] == 64 == co_n["MAC16"] == int(s["stock/c"]["count_per_run"]) == int(s["core8/c"]["count_per_run"])
    assert SWEEPS * st_n["MAC16"] == 512 and co_n["MAC16"] == 64
    # MAC slot spacing: one column period (5 ns) in stock, V/D = 2 periods (10 ns) in CoDe
    assert float(s["stock/t_slot"]["ns_per_run"]) == 5.0 and float(s["core8/t_slot"]["ns_per_run"]) == 5.0 * V / D
    assert all(abs(b - a - 10.0) < 1e-9 for a, b in zip(co_mac[1:], co_mac[2:]))
    # MAC slots: 8 x 320 = 2,560 ns (stock) -> 640 ns (CoDe): beat filling, slot factor 1/4 -> 1
    m_st, m_co = SWEEPS * float(s["stock/mac_slots"]["ns_per_run"]), float(s["core8/mac_slots"]["ns_per_run"])
    assert (m_st, m_co) == (2560.0, 640.0) and m_st / m_co == 4
    assert float(s["core8/useful"]["ns_per_run"]) == m_co == co_n["MAC16"] * V * TCK          # every CoDe beat useful
    assert SWEEPS * float(s["stock/useful"]["ns_per_run"]) == m_co                                 # same useful work
    # row switches: one TMOD pair + PREA + ACT16 pair + WRMAC16 per sweep; 8 (stock) -> 1 (CoDe): row reuse
    for n in (st_n, co_n):
        assert (n["TMOD"], n["PREA"], n["ACT16-1"], n["ACT16-2"], n["WRMAC16"]) == (2, 1, 1, 1, 1)
    assert float(s["stock/framing"]["ns_per_run"]) == float(s["core8/framing"]["ns_per_run"]) == 86.875
    # token drain stays per token: one RDMAC16 per token per sweep in both (CoDe: one burst of V reads)
    assert st_n["RDMAC16"] == 1 and co_n["RDMAC16"] == V and st_n["CASRDMAC16"] == co_n["CASRDMAC16"] == 1
    assert int(s["stock/drain"]["count_per_run"]) == 1 and int(s["core8/drain"]["count_per_run"]) == V
    # the K chunk's WRGB burst: 512 WRGB per burst (V tokens x 64), once per 64 row sweeps
    assert int(s["core8_gbfill/WRGB"]["count_per_run"]) == 512 and int(s["stock_gbfill/WRGB"]["count_per_run"]) == 64
    tid = {r["id"]: float(r["value"]) for r in csv.DictReader(open(TOUCHED))}
    assert tid["umac.kernel.phone.W2.row_groups_per_fill"] == 64 and tid["umac.kernel.phone.W2.k_chunks"] == 2
    # GB (IV-D): one K chunk of 4096 / 2 = 2,048 INT8 inputs = 2 KB per token = 64 WRGB of 32 B; V tokens -> 16 KB
    k_chunk_B = 4096 // int(tid["umac.kernel.phone.W2.k_chunks"])
    assert k_chunk_B == 2048 and k_chunk_B // 64 == 32 and 512 * 32 == V * k_chunk_B == 16 * 1024
    gb = {(r["substrate"][:5], r["design"]): int(r["GB_KB"]) for r in read("dac_table4.csv")}
    assert gb[("phone", "core8")] == 16                                                          # Table II
    # whole q_proj GEMM (umac_kernel W2, channel 28): CoDe 4.31x stock AiM
    k = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(RAW, "ukern_phone_sum.csv")))}
    assert k["W2/core"]["workload_label"].startswith("Llama-2-7B q_proj") and k["W2/core"]["channel"] == "28"
    assert f"{float(k['W2/core']['speedup_vs_stock']):.2f}" == "4.31"
    print(f"sequence: stock {stock_ns:,.0f} ns (8 x {st_p}), CoDe {code_ns} ns, {ratio:.2f}x; MAC cmds 512 -> 64; "
          f"MAC slots {m_st:,.0f} -> {m_co:.0f} ns; row switches 8 -> 1; GB 16 KB = 512 x 32 B; q_proj 4.31x")
    return st, st_mac, st_p, co, co_mac, co_p, ratio


def circled(fig, x, y, n, r=4.6):
    fig.o.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="#FFFFFF" stroke="{RED}" stroke-width="0.6"/>')
    fig.text(x, y + 2.8, str(n), FT, "middle", f' style="fill:{RED}"')


def draw(st, st_mac, st_p, co, co_mac, co_p, ratio):
    W = 252.0
    lab_w = 19.0
    x0, x1 = lab_w + 3.0, W - 4.0
    T = SWEEPS * st_p
    sx = lambda t: x0 + (x1 - x0) * t / T   # noqa: E731
    lane_h, lane_gap = 8.0, 2.0
    # legend: cmd classes on the first row, PU states on the second
    y_leg = 1.0 + FL
    legend = [("cmd:", [("row switch", COL["row"]), ("MAC", COL["mac"]), ("token drain", COL["drain"])]),
              ("PU:", [("busy beat", COL["beat"]), ("one beat in four busy", COL["quarter"])])]
    sw, gap, space = 7.0, 2.5, 8.0
    fig_rows = []
    # unit geometry: header (FL + 2), cmd lane, PU lane
    y_a = y_leg + FL + 2.0 + 6.0
    y_b = y_a + FL + 3.0 + 2 * lane_h + lane_gap + 9.0
    y_axis = y_b + FL + 3.0 + 2 * lane_h + lane_gap + 15.0
    H = y_axis + FT + 3.0 + FL + 1.5
    fig = Fig(W, round(H + 0.5))
    for r, (head, items) in enumerate(legend):
        yy = y_leg + r * (FL + 2.0)
        fig.text(lab_w, yy, head, FL, "end", ' style="fill:#404040"')
        x = x0
        for lab, col in items:
            fig.o.append(f'<rect x="{x:.2f}" y="{yy - sw + 0.6:.2f}" width="{sw}" height="{sw - 0.6:.2f}" fill="{col}" '
                         f'stroke="#000000" stroke-width="0.5"/>')
            fig.text(x + sw + gap, yy, lab, FL)
            x += sw + gap + width(lab, FL) + space

    def unit(y, title, sub, segs_per, macs_per, period, reps, beats_per_mac):
        fig.text(0.5, y + FL, f'<tspan font-weight="bold">{title}</tspan> {sub}', FL)
        yc = y + FL + 3.0
        yp = yc + lane_h + lane_gap
        fig.text(lab_w, yc + lane_h - 1.5, "cmd", FT, "end", ' style="fill:#404040"')
        fig.text(lab_w, yp + lane_h - 1.5, "PU", FT, "end", ' style="fill:#404040"')
        for k in range(reps):
            off = k * period
            for a, b, c in merge(segs_per):
                fig.o.append(f'<rect x="{sx(off + a):.3f}" y="{yc:.2f}" width="{sx(off + b) - sx(off + a):.3f}" '
                             f'height="{lane_h}" fill="{COL[c]}" stroke="none"/>')
            # a beat is 1.25 ns, under 0.1 pt: stock's one-in-four pattern is drawn as its average over each MAC
            # slot (5 ns), CoDe's back-to-back beats as one solid run per tile MAC (10 ns)
            slot = macs_per[2] - macs_per[1]          # MAC16 spacing in the sweep: 5 ns stock, 10 ns CoDe
            fill = COL["beat"] if beats_per_mac * TCK == slot else COL["quarter"]
            assert (beats_per_mac * TCK) / slot in (1.0, 0.25)
            for t in macs_per:
                a, b = off + t, off + t + slot
                fig.o.append(f'<rect x="{sx(a):.3f}" y="{yp:.2f}" width="{sx(b) - sx(a) + 0.02:.3f}" height="{lane_h}" '
                             f'fill="{fill}" stroke="none"/>')
        end = reps * period
        for yy in (yc, yp):
            fig.o.append(f'<rect x="{x0:.2f}" y="{yy:.2f}" width="{sx(end) - x0:.2f}" height="{lane_h}" fill="none" '
                         f'stroke="#000000" stroke-width="0.5"/>')
        for k in range(1, reps):                 # sweep boundaries
            fig.line(sx(k * period), yc - 1.5, sx(k * period), yp + lane_h + 1.5, "#000000", 0.4)
        return yc, yp, sx(end)

    yc_a, yp_a, end_a = unit(y_a, "(a) Stock AiM:", "8 row sweeps, 512 MAC commands", st, st_mac, st_p, SWEEPS, 1)
    fig.text(x1, y_a + FL, "3,250 ns", FL, "end")
    yc_b, yp_b, end_b = unit(y_b, "(b) CoDe:", "1 row sweep, 64 tile MAC commands", co, co_mac, co_p, 1, V)
    # window ends: dashed rules down to the axis
    for xe in (end_a, end_b):
        fig.line(xe, yc_a - 1.5 if xe == end_a else yc_b - 1.5, xe, y_axis, "#000000", 0.5,
                 ' stroke-dasharray="1.6,1.2"')
    fig.text(x1, y_b + FL, "738.75 ns", FL, "end")
    # the ratio: a red span from CoDe's end to stock's end, label centred on it
    yr = yc_b + lane_h / 2
    lab = f"{ratio:.2f}&#215; shorter"
    xm, lw = (end_b + end_a) / 2, width(lab, FL) + 4.0
    fig.line(end_b + 1.0, yr, xm - lw / 2, yr, RED, 0.7, ' marker-start="url(#ar)"')
    fig.line(xm + lw / 2, yr, end_a - 1.0, yr, RED, 0.7, ' marker-end="url(#ar)"')
    fig.text(xm, yr + FL * 0.34, lab, FL, "middle", f' style="fill:{RED}"')
    # brackets under CoDe's PU lane: (2) row switch [0, first MAC of the sweep), (1) the sweep's MAC slots
    first = co_mac[1]
    yb = yp_b + lane_h + 2.5
    for n, a, b in ((2, 0.0, first), (1, first, co_p)):
        xa, xb = sx(a) + 0.4, sx(b) - 0.4
        fig.o.append(f'<polyline points="{xa:.2f},{yb:.2f} {xa:.2f},{yb + 2.5:.2f} {xb:.2f},{yb + 2.5:.2f} '
                     f'{xb:.2f},{yb:.2f}" fill="none" stroke="#000000" stroke-width="0.5"/>')
        circled(fig, (xa + xb) / 2, yb + 2.5 + 5.2, n)
    kx = end_b + 8.0
    for n, yy, txt in ((1, yp_b + lane_h / 2, "beat filling: MAC slots 2,560 &#8594; 640 ns"),
                       (2, yp_b + lane_h / 2 + 11.0, "row reuse: row switches 8 &#8594; 1")):
        circled(fig, kx, yy, n)
        fig.text(kx + 7.0, yy + FT * 0.34, txt, FT)
    # time axis
    fig.line(x0, y_axis, x1, y_axis, "#000000", 0.6)
    for t in range(0, 3001, 500):
        fig.line(sx(t), y_axis, sx(t), y_axis + 2.5, "#000000", 0.5)
        fig.text(sx(t), y_axis + FT + 3.0, f"{t:,}", FT, "middle")
    fig.text((x0 + x1) / 2, y_axis + FT + 3.0 + FL + 0.5, "time (ns)", FL, "middle")
    fig.o.insert(0, '<defs><marker id="ar" viewBox="0 0 6 6" refX="5.5" refY="3" markerWidth="4" markerHeight="4" '
                    f'orient="auto-start-reverse"><path d="M0,0 L6,3 L0,6 z" fill="{RED}"/></marker></defs>')
    fig.write("fig_sequence", "scripts/make_fig_sequence.py from evaluation/dac_2x2/raw/utrace_run_{stock,core8}.csv")


def table():
    """Table cmds: CoDe's commands, count per token against stock AiM (symbolic in V; the V = 8 trace checks it)."""
    rows = [
        (r"tile MAC (col, $V$)", r"One column read at the stock MAC timing; $V$ beats on it", "column", r"$1/V$", "1"),
        ("burst drain", r"A tile's $V$ sums out in one burst", "row sweep", "1", "1"),
        ("row switch", r"TMOD$\times$2, PREA, ACT16 pair, WRMAC16; unchanged", "row sweep", r"$1/V$", "1"),
        ("WRGB", "GB fill; unchanged", "32\\,B of input", "1", "1"),
    ]
    out = os.path.join(REPO, "tables", "tab_cmds.tex")
    with open(out, "w") as fh:
        fh.write("% generated by scripts/make_fig_sequence.py (counts checked on the V = 8 trace, evaluation/dac_2x2 "
                 "Sec. 2j); do not edit\n")
        fh.write("\\begin{tabular}{@{}l>{\\raggedright\\arraybackslash}p{3.2cm}lcc@{}}\n\\toprule\n"
                 "Command & Action & Unit & CoDe & Stock \\\\\n\\midrule\n")
        for r in rows:
            fh.write(" & ".join(r) + " \\\\\n")
        fh.write("\\bottomrule\n\\end{tabular}\n")
    print("wrote", out)


def main():
    draw(*checks())
    table()


if __name__ == "__main__":
    main()
