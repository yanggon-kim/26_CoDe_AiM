#!/usr/bin/env python3
"""Fig. sequence (Sec. IV-A) and Table cmds (Sec. IV-D): one weight row of Llama-2-7B's q_proj on the mobile platform,
M = 8, steady state, from stock AiM to CoDe one component at a time.

(a) Stock AiM sweeps the row eight times, one token each (simulated); (b) beat filling only, a MODEL composed from
stock's trace with each MAC slot shrunk to one 1.25 ns beat (8 sweeps; drawn with dashed lane outlines); (c) row reuse
only, simulated as CoDe's trace at D = 1, V = 8 (1 sweep; its drain-later block, TMOD + CASRDMAC16 + 8 RDMAC16 + TMOD,
sits inside the MAC stream and is drawn as token drain); (d) CoDe (V = 8, D = 4, 1 sweep). All on one ns axis; per
row a cmd lane (segments coloured by class: row-switch commands, MAC commands, token drain) and a PU lane (busy beats,
one CK each; one beat in four in (a) and (c), every beat in (b) and (d)). Per-row totals at the right; a span from
each shorter row's end to stock's end carries its ratio against stock (red for CoDe's 4.40x).

Source (read only): evaluation/dac_2x2 (collected at 7b4126a; context Sec. 2j, Sec. 5 rows 53-55):
raw/utrace_run_{stock,bfonly,rsonly,core8}.csv (one steady row sweep of the command log, channel 28; umac_trace @
microarch 86efbc6, middle rows @ 1a6d381), raw/utrace_sum.csv and utrace_sum_mid.csv (per-sweep totals),
raw/utrace_sum_split.csv (class split + weight-row rows), touched.csv (umac.trace.* weight-row ids and steps;
umac.kernel.phone.W2.*), raw/ukern_phone_sum.csv (whole q_proj GEMM, umac_kernel @ 7e5124b / 170254c), and the EV-58
pack's dac_table4.csv (GB KB, Table II).
A window starts at the previous sweep's last MAC16 and ends at this sweep's last MAC16 (the "run period"), so eight
windows tile 8 consecutive sweeps exactly; the K chunk's WRGB burst (once per 64 sweeps) is not in it.
Asserts every number Sec. IV prints from this trace. Writes figs/src/fig_sequence.html (then
python3 scripts/html2pdf.py fig_sequence) and tables/tab_cmds.tex.
"""
import csv
import os

from dac_data import EVAL, REPO, read
from svgchart import FL, FT, Fig, width

RAW = os.path.join(EVAL, "dac_2x2", "raw")
TOUCHED = os.path.join(EVAL, "dac_2x2", "touched.csv")
TCK = 1.25                      # ns, mobile CK (III-A), one PU beat
V, D, SWEEPS = 8, 4, 8
COL = {"row": "#CFE2F3", "mac": "#9A9A9A", "drain": "#000000", "beat": "#303030",
       "quarter": "#CBCBCB"}   # one busy beat in four, drawn as its average: 1/4 of #303030 over white
RED = "#E03127"
TRACES = ("stock", "bfonly", "rsonly", "core8")


def rows_of(name):
    return {r["row_id"]: r for r in csv.DictReader(open(os.path.join(RAW, name + ".csv")))}


def window(name):
    rows = list(csv.DictReader(open(os.path.join(RAW, f"utrace_run_{name}.csv"))))
    run = [r for r in rows if r["part"] == "run MAC16"]
    last = max(int(r["row_id"]) for r in run if r["cmd"] == "MAC16")
    win = [r for r in rows if int(r["row_id"]) < last]            # previous last MAC16 .. this sweep's last MAC16
    t0 = float(win[0]["t_ns"])
    period = float(rows[last]["t_ns"]) - t0

    def cls(r):
        # a TMOD inside the MAC stream belongs to the drain-later block (row reuse only): the split's drain class
        if r["cmd"] == "TMOD" and r["part"] == "run MAC16":
            return "drain"
        return {"MAC": "mac", "run framing": "row", "per-token": "drain"}[r["cls"]]
    segs = [(float(r["t_ns"]) - t0, float(r["t_ns"]) - t0 + float(r["gap_next_ns"]), cls(r)) for r in win]
    assert abs(segs[-1][1] - period) < 1e-9 and all(abs(a[1] - b[0]) < 1e-9 for a, b in zip(segs, segs[1:]))
    assert not any(r["cmd"] in ("WRGB", "CASWRGB", "REFab") for r in win)          # no GB fill, no refresh in the window
    macs = [float(r["t_ns"]) - t0 for r in win if r["cmd"] == "MAC16"]
    counts = {c: sum(1 for r in win if r["cmd"] == c) for c in ("MAC16", "TMOD", "PREA", "ACT16-1", "ACT16-2",
                                                                "WRMAC16", "RDMAC16", "CASRDMAC16")}
    counts["dl_TMOD"] = sum(1 for r in win if r["cmd"] == "TMOD" and r["part"] == "run MAC16")
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
    s = rows_of("utrace_sum")
    m = rows_of("utrace_sum_mid")
    sp = {**rows_of("utrace_sum_split"), **{k: v for k, v in m.items() if "/full_" in k or "/exp_" in k
                                            or k.endswith("/wrow") or k.endswith("/speedup")}}
    tid = {r["id"]: float(r["value"]) for r in csv.DictReader(open(TOUCHED))}
    w = {t: window(t) for t in TRACES}
    sweeps = {"stock": SWEEPS, "bfonly": SWEEPS, "rsonly": 1, "core8": 1}
    per = {"stock": s["stock/period"], "bfonly": m["bfonly/period"], "rsonly": m["rsonly/period"],
           "core8": s["core8/period"]}
    row_ns = {}
    for t in TRACES:
        segs, macs, p, n = w[t]
        assert p == float(per[t]["ns_per_run"])
        row_ns[t] = sweeps[t] * p
        assert row_ns[t] == float(sp[f"{t}/wrow"]["ns_per_run"]) == tid[f"umac.trace.{t}.wrow_ns"]
        assert int(sp[f"{t}/wrow"]["count_per_run"]) == sweeps[t]
        # class split of the drawn window = the collected split (gap attributed to the command before it)
        tot = {c: sum(b - a for a, b, k in segs if k == c) for c in ("mac", "row", "drain")}
        for c, key in (("mac", "full_mac"), ("row", "full_row"), ("drain", "full_drain")):
            assert abs(tot[c] - float(sp[f"{t}/{key}"]["ns_per_run"])) < 1e-9, (t, c, tot[c])
        # 64 MAC commands per sweep in every design; one row switch per sweep
        assert n["MAC16"] == 64
        assert (n["PREA"], n["ACT16-1"], n["ACT16-2"], n["WRMAC16"]) == (1, 1, 1, 1)
        assert n["TMOD"] == 2 + n["dl_TMOD"] and n["dl_TMOD"] == (2 if t == "rsonly" else 0)
    disp = {t: v for t, v in zip(TRACES, ("3,250", "1,360", "2,629.375", "738.75"))}
    assert f"{row_ns['stock']:,.0f}" == disp["stock"] and f"{row_ns['bfonly']:,.0f}" == disp["bfonly"]
    assert f"{row_ns['rsonly']:,.3f}" == disp["rsonly"] and f"{row_ns['core8']:.2f}" == disp["core8"]
    # MAC commands per weight row: 512 / 512 / 64 / 64; row switches 8 / 8 / 1 / 1
    assert [sweeps[t] * w[t][3]["MAC16"] for t in TRACES] == [512, 512, 64, 64] and list(sweeps.values()) == [8, 8, 1, 1]
    # step ratios (both orders) and the total
    r = lambda a, b: row_ns[a] / row_ns[b]  # noqa: E731
    steps = {"a_b": r("stock", "bfonly"), "b_d": r("bfonly", "core8"), "a_c": r("stock", "rsonly"),
             "c_d": r("rsonly", "core8"), "a_d": r("stock", "core8")}
    for k, i in (("a_b", "bfonly.step_stock_to_bf"), ("b_d", "bfonly.step_bf_to_core"),
                 ("a_c", "rsonly.step_stock_to_rs"), ("c_d", "rsonly.step_rs_to_core"),
                 ("a_d", "core8.speedup_vs_stock")):
        assert abs(steps[k] - tid["umac.trace." + i]) < 1e-12
    shown = {k: f"{v:.2f}" for k, v in steps.items()}
    assert shown == {"a_b": "2.39", "b_d": "1.84", "a_c": "1.24", "c_d": "3.56", "a_d": "4.40"}
    # MAC slot spacing: 5 ns (stock, one column period), 1.25 ns (beat filling only: one beat, faster than a column
    # period, hence a model), 40 ns (row reuse only: V t_col at D = 1), 10 ns (CoDe: V / D column periods)
    assert float(s["stock/t_slot"]["ns_per_run"]) == 5.0 and float(m["bfonly/t_slot"]["ns_per_run"]) == TCK
    assert float(m["rsonly/t_slot"]["ns_per_run"]) == V * 5.0 and float(s["core8/t_slot"]["ns_per_run"]) == 5.0 * V / D
    for t, sl in (("stock", 5.0), ("bfonly", TCK), ("rsonly", 40.0), ("core8", 10.0)):
        gaps = [b - a for a, b in zip(w[t][1][1:], w[t][1][2:])]
        odd = [g for g in gaps if abs(g - sl) > 1e-9]
        # row reuse only: one MAC gap holds the drain-later block (1 cycle + 61.25 ns)
        assert odd == ([0.625 + 61.25] if t == "rsonly" else []), (t, odd)
    # MAC slots over the weight row (exposed split): stock 2,560 -> beat filling only 640 (8 sweeps); row reuse only
    # keeps 2,560 (the idle beats), CoDe 640; useful beats 640 ns in all four
    slots = {t: sweeps[t] * float(sp[f"{t}/exp_mac_slots"]["ns_per_run"]) for t in TRACES}
    assert slots == {"stock": 2560.0, "bfonly": 640.0, "rsonly": 2560.0, "core8": 640.0}
    useful = {t: sweeps[t] * float((m if t in ("bfonly", "rsonly") else s)[f"{t}/useful"]["ns_per_run"])
              for t in TRACES}
    assert set(useful.values()) == {640.0}
    # row switch: 86.875 ns per sweep in every design (row reuse only: without its drain-later TMOD pair)
    for t in TRACES:
        assert float(sp[f"{t}/full_row"]["ns_per_run"]) == 86.875
    # row reuse only: drain-later block (TMOD + CASRDMAC16 + 8 RDMAC16 + TMOD) inside the MAC stream, 61.25 ns
    blocks = [(a, b) for a, b, c in merge(w["rsonly"][0]) if c == "drain"]
    assert len(blocks) == 1 and abs(blocks[0][1] - blocks[0][0] - 61.25) < 1e-9
    assert float(m["rsonly/drain_block"]["ns_per_run"]) == 61.25 and w["rsonly"][3]["RDMAC16"] == V
    macs_rs = w["rsonly"][1]
    assert macs_rs[1] < blocks[0][0] < macs_rs[-1]                                  # inside the MAC stream
    # token drain stays per token: one RDMAC16 per token per sweep
    assert w["stock"][3]["RDMAC16"] == w["bfonly"][3]["RDMAC16"] == 1 and w["core8"][3]["RDMAC16"] == V
    # the composed cell of Table IV (section 12's rule) vs the window: 166.25 vs 170.0 ns per sweep, 2.3 %
    assert tid["umac.trace.bfonly.period_ns"] == 170.0 and tid["umac.trace.bfonly.s12_rule_ns"] == 166.25
    assert f"{tid['umac.trace.bfonly.s12_optimism_pct']:.1f}" == "2.3"
    # the K chunk's WRGB burst: 512 WRGB per burst (V tokens x 64), once per 64 row sweeps
    assert int(s["core8_gbfill/WRGB"]["count_per_run"]) == 512 and int(s["stock_gbfill/WRGB"]["count_per_run"]) == 64
    assert tid["umac.kernel.phone.W2.row_groups_per_fill"] == 64 and tid["umac.kernel.phone.W2.k_chunks"] == 2
    # GB (IV-D): one K chunk of 4096 / 2 = 2,048 INT8 inputs = 2 KB per token = 64 WRGB of 32 B; V tokens -> 16 KB
    k_chunk_B = 4096 // int(tid["umac.kernel.phone.W2.k_chunks"])
    assert k_chunk_B == 2048 and k_chunk_B // 64 == 32 and 512 * 32 == V * k_chunk_B == 16 * 1024
    gb = {(r["substrate"][:5], r["design"]): int(r["GB_KB"]) for r in read("dac_table4.csv")}
    assert gb[("phone", "core8")] == 16                                                          # Table II
    # whole q_proj GEMM (umac_kernel W2, channel 28): CoDe 4.31x stock AiM
    k = rows_of("ukern_phone_sum")
    assert k["W2/core"]["workload_label"].startswith("Llama-2-7B q_proj") and k["W2/core"]["channel"] == "28"
    assert f"{float(k['W2/core']['speedup_vs_stock']):.2f}" == "4.31"
    print("sequence: weight row " + " / ".join(f"{t} {disp[t]} ns" for t in TRACES)
          + f"; steps a->b {shown['a_b']} b->d {shown['b_d']}, a->c {shown['a_c']} c->d {shown['c_d']}, "
          f"total {shown['a_d']}; MAC cmds 512/512/64/64; row switches 8/8/1/1; MAC slots 2,560 -> 640 (b), "
          f"2,560 kept (c); drain block 61.25 ns; s12 rule 2.3 %; GB 16 KB; q_proj 4.31x")
    return w, row_ns, disp, shown


def draw(w, row_ns, disp, shown):
    W = 252.0
    lab_w = 19.0
    x0, x1 = lab_w + 3.0, W - 4.0
    T = row_ns["stock"]
    sx = lambda t: x0 + (x1 - x0) * t / T   # noqa: E731
    lane_h, lane_gap, unit_gap = 8.0, 2.0, 6.0
    y_leg = 1.0 + FL
    legend = [("cmd:", [("row switch", COL["row"]), ("MAC", COL["mac"]), ("token drain", COL["drain"])]),
              ("PU:", [("busy beat", COL["beat"]), ("one beat in four busy", COL["quarter"])])]
    sw, gap, space = 7.0, 2.5, 8.0
    spec = [("stock", "(a) Stock AiM:", "8 row sweeps, 512 MAC commands", SWEEPS, 1, None),
            ("bfonly", "(b) Beat filling only, model:", "8 sweeps, 512 MAC commands", SWEEPS, 1, "a_b"),
            ("rsonly", "(c) Row reuse only:", "1 sweep, 64 tile MACs at <tspan font-style=\"italic\">D</tspan> = 1",
             1, V, "a_c"),
            ("core8", "(d) CoDe:", "1 sweep, 64 tile MAC commands", 1, V, "a_d")]
    unit_h = FL + 3.0 + 2 * lane_h + lane_gap
    y_top = y_leg + FL + 2.0 + 5.0
    y_axis = y_top + 4 * unit_h + 3 * unit_gap + 5.0
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

    for i, (t, title, sub, reps, beats_per_mac, step) in enumerate(spec):
        segs_per, macs_per, period, _ = w[t]
        y = y_top + i * (unit_h + unit_gap)
        total = f"{disp[t]} ns"
        assert 0.5 + width(title + " " + sub.replace('<tspan font-style="italic">D</tspan>', "D"), FL) + 1.5 \
            + width(total, FL) < x1, t                                               # header fits its row
        fig.text(0.5, y + FL, f'<tspan font-weight="bold">{title}</tspan> {sub}', FL)
        fig.text(x1, y + FL, total, FL, "end")
        yc = y + FL + 3.0
        yp = yc + lane_h + lane_gap
        fig.text(lab_w, yc + lane_h - 1.5, "cmd", FT, "end", ' style="fill:#404040"')
        fig.text(lab_w, yp + lane_h - 1.5, "PU", FT, "end", ' style="fill:#404040"')
        slot = macs_per[2] - macs_per[1]
        fill = COL["beat"] if beats_per_mac * TCK == slot else COL["quarter"]
        assert (beats_per_mac * TCK) / slot in (1.0, 0.25)
        for k in range(reps):
            off = k * period
            for a, b, c in merge(segs_per):
                fig.o.append(f'<rect x="{sx(off + a):.3f}" y="{yc:.2f}" width="{sx(off + b) - sx(off + a):.3f}" '
                             f'height="{lane_h}" fill="{COL[c]}" stroke="none"/>')
            # a beat is 1.25 ns, under 0.1 pt: a one-in-four pattern is drawn as its average over each MAC slot
            for tm in macs_per:
                a, b = off + tm, off + tm + slot
                fig.o.append(f'<rect x="{sx(a):.3f}" y="{yp:.2f}" width="{sx(b) - sx(a) + 0.02:.3f}" height="{lane_h}" '
                             f'fill="{fill}" stroke="none"/>')
        end = sx(reps * period)
        dash = ' stroke-dasharray="2,1.2"' if t == "bfonly" else ""       # the model's lanes: dashed outline
        for yy in (yc, yp):
            fig.o.append(f'<rect x="{x0:.2f}" y="{yy:.2f}" width="{end - x0:.2f}" height="{lane_h}" fill="none" '
                         f'stroke="#000000" stroke-width="{0.6 if dash else 0.5}"{dash}/>')
        for k in range(1, reps):                 # sweep boundaries
            fig.line(sx(k * period), yc - 1.5, sx(k * period), yp + lane_h + 1.5, "#000000", 0.4)
        if step:
            # span from this row's end to stock's end, the ratio against stock on it
            xs = sx(T)
            fig.line(xs, yc - 1.0, xs, yp + lane_h + 1.0, "#000000", 0.5, ' stroke-dasharray="1.6,1.2"')
            col = RED if step == "a_d" else "#000000"
            lab = f"{shown[step]}&#215;" + (" shorter" if step == "a_d" else "")
            yr = yc + lane_h / 2
            xm, lw = (end + xs) / 2, width(lab.replace("&#215;", "x"), FL) + 4.0
            assert xs - end > lw + 10.0, t                                            # label + two arrowheads fit
            mk = "ar" if step == "a_d" else "ak"
            fig.line(end + 1.0, yr, xm - lw / 2, yr, col, 0.7, f' marker-start="url(#{mk})"')
            fig.line(xm + lw / 2, yr, xs - 1.0, yr, col, 0.7, f' marker-end="url(#{mk})"')
            fig.text(xm, yr + FL * 0.34, lab, FL, "middle", f' style="fill:{col}"')
    # time axis
    fig.line(x0, y_axis, x1, y_axis, "#000000", 0.6)
    for tk in range(0, 3001, 500):
        fig.line(sx(tk), y_axis, sx(tk), y_axis + 2.5, "#000000", 0.5)
        fig.text(sx(tk), y_axis + FT + 3.0, f"{tk:,}", FT, "middle")
    fig.text((x0 + x1) / 2, y_axis + FT + 3.0 + FL + 0.5, "time (ns)", FL, "middle")
    marker = ('<marker id="{0}" viewBox="0 0 6 6" refX="5.5" refY="3" markerWidth="4" markerHeight="4" '
              'orient="auto-start-reverse"><path d="M0,0 L6,3 L0,6 z" fill="{1}"/></marker>')
    fig.o.insert(0, "<defs>" + marker.format("ar", RED) + marker.format("ak", "#000000") + "</defs>")
    fig.write("fig_sequence", "scripts/make_fig_sequence.py from evaluation/dac_2x2/raw/utrace_run_{stock,bfonly,"
                              "rsonly,core8}.csv")


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
