#!/usr/bin/env python3
"""Fig. mapping (Sec. IV-B, IV-C) and Table cmds (Sec. IV-D): a skinny GEMM on CoDe at M = 8, mobile platform.

(a) The skinny GEMM X (M = 8 tokens x K) . W (K x N) = Y (M x N), each token row in its own blue shade (light token 1
to dark token 8); red boxes mark one bank's work in one row sweep: the 8 tokens' K chunk (in the GB), one matrix
column of W over that chunk (one bank's 2 KB DRAM row = one output's weights), and that output's 8 sums.
(b) One weight row of one bank (Llama-2-7B q_proj, steady state). Both lanes start at the same x; lane length is
proportional to time with two drawing allowances (the paper needs only the ~4x impression): the drain slivers are
widened to stay visible, and CoDe's tile-MAC block is widened to hold its label (drawn ratio asserted near 4.40x).
Stock AiM: 8 units RS | MAC x64 | D, one per token; CoDe: RS | tile MAC x64 | D (burst drain), one row sweep. A red
double arrow "speedup" spans CoDe's end to stock's end (no ratio printed). The zoom shows one tile MAC: one column
read, 8 beats, two column periods, x64. Table: MAC beats / row opens / column reads / MAC time per weight row.
MAC time is counted in column periods, not MAC slots: CoDe's MAC slot is 10 ns (Table I), stock AiM's 5 ns.

Source (read only): evaluation/dac_2x2 (collected at 7b4126a; context Sec. 2j, Sec. 5 rows 53-55):
raw/utrace_run_{stock,core8}.csv (one steady row sweep of the command log, channel 28; umac_trace @ microarch 86efbc6),
raw/utrace_sum.csv (per-sweep totals), raw/utrace_sum_split.csv (class split + weight-row rows), touched.csv
(umac.trace.* weight-row ids; umac.kernel.phone.W2.*), raw/ukern_phone_sum.csv (whole q_proj GEMM, umac_kernel @
7e5124b / 170254c), and the EV-58 pack's dac_table4.csv (GB KB, Table III).
A window starts at the previous sweep's last MAC16 and ends at this sweep's last MAC16 (the "run period"), so eight
windows tile 8 consecutive sweeps exactly; the K chunk's WRGB burst (once per 64 sweeps) is not in it.
Asserts every number Sec. IV prints from this trace. Writes figs/src/fig_mapping.html (then
python3 scripts/html2pdf.py fig_mapping) and tables/tab_cmds.tex.
"""
import csv
import os

from dac_data import EVAL, REPO, read
from svgchart import Fig, width

RAW = os.path.join(EVAL, "dac_2x2", "raw")
TOUCHED = os.path.join(EVAL, "dac_2x2", "touched.csv")
TCK, TCOL = 1.25, 5.0           # ns, mobile CK (one PU beat) and column period (Table III)
V, D, SWEEPS, COLS = 8, 4, 8, 64
TRACES = ("stock", "core8")
INK, GRAY_RS, GRAY_D, RULE, NOTE = "#000000", "#A6A6A6", "#FFFFFF", "#BFBFBF", "#404040"
TINT, EDGE, RED = "#CFE2F3", "#2B5FA8", "#E03127"


def _mix(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


TOK = [_mix("#CDDCF3", "#14366E", k / 7) for k in range(8)]     # token k's shade, light (1) to dark (8)
TOKT = [INK if k < 3 else "#FFFFFF" for k in range(8)]           # text on each shade


def rows_of(name):
    return {r["row_id"]: r for r in csv.DictReader(open(os.path.join(RAW, name + ".csv")))}


def window(name):
    rows = list(csv.DictReader(open(os.path.join(RAW, f"utrace_run_{name}.csv"))))
    run = [r for r in rows if r["part"] == "run MAC16"]
    last = max(int(r["row_id"]) for r in run if r["cmd"] == "MAC16")
    win = [r for r in rows if int(r["row_id"]) < last]            # previous last MAC16 .. this sweep's last MAC16
    t0 = float(win[0]["t_ns"])
    period = float(rows[last]["t_ns"]) - t0
    assert not any(r["cmd"] in ("WRGB", "CASWRGB", "REFab") for r in win)          # no GB fill, no refresh in the window
    macs = [float(r["t_ns"]) - t0 for r in win if r["cmd"] == "MAC16"]
    counts = {c: sum(1 for r in win if r["cmd"] == c) for c in ("MAC16", "TMOD", "PREA", "ACT16-1", "ACT16-2",
                                                                "WRMAC16", "RDMAC16")}
    return macs, period, counts


def checks():
    s = rows_of("utrace_sum")
    sp = rows_of("utrace_sum_split")
    tid = {r["id"]: float(r["value"]) for r in csv.DictReader(open(TOUCHED))}
    w = {t: window(t) for t in TRACES}
    sweeps = {"stock": SWEEPS, "core8": 1}
    row_ns, split = {}, {}
    for t in TRACES:
        macs, p, n = w[t]
        assert p == float(s[f"{t}/period"]["ns_per_run"])
        row_ns[t] = sweeps[t] * p
        assert row_ns[t] == float(sp[f"{t}/wrow"]["ns_per_run"]) == tid[f"umac.trace.{t}.wrow_ns"]
        assert int(sp[f"{t}/wrow"]["count_per_run"]) == sweeps[t]
        split[t] = {c: float(sp[f"{t}/full_{c}"]["ns_per_run"]) for c in ("mac", "row", "drain")}
        assert abs(sum(split[t].values()) - p) < 1e-9
        # 64 MAC commands (column reads) and one row switch (one ACT16 pair) per row sweep in both designs
        assert n["MAC16"] == COLS and (n["PREA"], n["ACT16-1"], n["ACT16-2"], n["WRMAC16"]) == (1, 1, 1, 1)
        assert n["TMOD"] == 2
    disp = {"stock": f"{row_ns['stock']:,.0f}", "core8": f"{row_ns['core8']:.2f}"}
    assert disp == {"stock": "3,250", "core8": "738.75"}
    speedup = row_ns["stock"] / row_ns["core8"]
    assert abs(speedup - tid["umac.trace.core8.speedup_vs_stock"]) < 1e-12 and f"{speedup:.2f}" == "4.40"
    # the table of panel (b), per weight row
    tab = {}
    for t in TRACES:
        macs, p, n = w[t]
        beats_per_mac = 1 if t == "stock" else V                     # useful beats per MAC command
        slot = macs[2] - macs[1]
        assert all(abs((b - a) - slot) < 1e-9 for a, b in zip(macs[1:], macs[2:]))
        assert slot == float(s[f"{t}/t_slot"]["ns_per_run"]) == {"stock": TCOL, "core8": TCOL * V / D}[t]
        useful = sweeps[t] * float(s[f"{t}/useful"]["ns_per_run"])
        mac_time = sweeps[t] * float(sp[f"{t}/exp_mac_slots"]["ns_per_run"])
        tab[t] = dict(beats=sweeps[t] * n["MAC16"] * beats_per_mac, opens=sweeps[t] * n["ACT16-1"],
                      reads=sweeps[t] * n["MAC16"], periods=mac_time / TCOL)
        assert useful == tab[t]["beats"] * TCK                       # every counted beat is a useful 1.25 ns beat
        assert mac_time == sweeps[t] * n["MAC16"] * slot             # MAC time = MAC commands x MAC slot
    assert tab["stock"] == dict(beats=512, opens=8, reads=512, periods=512.0)
    assert tab["core8"] == dict(beats=512, opens=1, reads=64, periods=128.0)
    assert tab["stock"]["beats"] == tab["core8"]["beats"] == V * COLS                     # printed as "8 x 64"
    # slot factor (IV-C): useful beats / beats the MAC time holds: 1/4 stock AiM, 1 CoDe
    assert [tab[t]["beats"] / (tab[t]["periods"] * D) for t in TRACES] == [0.25, 1.0]
    # zoom: one tile MAC holds its column V / D = 2 column periods, D = 4 beats each
    assert V / D == 2 and TCOL / TCK == D
    # token drain per token: one RDMAC16 per token per sweep (stock), V in CoDe's burst drain
    assert w["stock"][2]["RDMAC16"] == 1 and w["core8"][2]["RDMAC16"] == V
    # the K chunk's WRGB burst: 512 WRGB per burst (V tokens x 64), once per 64 row sweeps
    assert int(s["core8_gbfill/WRGB"]["count_per_run"]) == 512 and int(s["stock_gbfill/WRGB"]["count_per_run"]) == 64
    assert tid["umac.kernel.phone.W2.row_groups_per_fill"] == 64 and tid["umac.kernel.phone.W2.k_chunks"] == 2
    # GB (IV-D) and panel (a): one K chunk of 4096 / 2 = 2,048 INT8 inputs = 2 KB per token = 64 WRGB of 32 B = one
    # 2 KB DRAM row of weights; V tokens -> 16 KB
    k_chunk_B = 4096 // int(tid["umac.kernel.phone.W2.k_chunks"])
    assert k_chunk_B == 2048 and k_chunk_B // COLS == 32 and 512 * 32 == V * k_chunk_B == 16 * 1024
    gb = {(r["substrate"][:5], r["design"]): int(r["GB_KB"]) for r in read("dac_table4.csv")}
    assert gb[("phone", "core8")] == 16                                                          # Table III
    # whole q_proj GEMM (umac_kernel W2, channel 28): CoDe 4.32x stock AiM (guard only, not printed)
    k = rows_of("ukern_phone_sum")
    assert k["W2/core"]["workload_label"].startswith("Llama-2-7B q_proj") and k["W2/core"]["channel"] == "28"
    assert f"{float(k['W2/core']['speedup_vs_stock']):.2f}" == "4.32"
    print(f"mapping: weight row stock {disp['stock']} ns, CoDe {disp['core8']} ns, {speedup:.2f}x; table "
          + " | ".join(f"{t} " + "/".join(f"{v:g}" for v in tab[t].values()) for t in TRACES)
          + "; GB 16 KB; q_proj 4.32x")
    return row_ns, split, tab


class S:
    """Minimal SVG builder at 1 user unit = 1 pt."""

    def __init__(self):
        self.o = []

    def t(self, x, y, s, size=8.0, anchor="start", fill=INK, bold=False, extra=""):
        st = f' style="fill:{fill}"' if fill != INK else ""
        b = ' font-weight="bold"' if bold else ""
        self.o.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}"{b}{st}{extra}>{s}</text>')

    def r(self, x, y, w, h, fill="none", stroke=INK, sw=0.5, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.o.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" '
                      f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def l(self, x1, y1, x2, y2, stroke=INK, sw=0.5, dash=None, extra=""):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.o.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" '
                      f'stroke-width="{sw}"{d}{extra}/>')

    def bracket(self, x0, x1, y, label, color=INK, size=8.0):
        """A bracket open upward under a span, its label below."""
        self.o.append(f'<path d="M{x0:.2f} {y:.2f} v3 H{x1:.2f} v-3" fill="none" stroke="{color}" stroke-width="0.6"/>')
        self.t((x0 + x1) / 2, y + 3 + size + 1.5, label, size, "middle", color)

    def tri(self, x, y, color=RED, h=4.6):
        """Down-pointing triangle (the column read mark), top edge at y, centred on x."""
        self.o.append(f'<polygon points="{x - h * 0.6:.2f},{y:.2f} {x + h * 0.6:.2f},{y:.2f} {x:.2f},{y + h:.2f}" '
                      f'fill="{color}"/>')


def I(s):
    return f'<tspan font-style="italic">{s}</tspan>'


def draw(row_ns, split, tab):
    W = 252.0
    g = S()
    # ---------------- (a) the skinny GEMM, M = 8; one bank's work in one row sweep in red ----------------
    g.t(1, 8.5, f"(a) skinny GEMM, {I('M')} = 8", 8.5, bold=True)
    top, rh = 25.0, 6.0
    X0, XW = 12.0, 74.0
    W0, WW = 106.0, 58.0
    Y0, YW = 186.0, 58.0
    H = 8 * rh                      # X and Y rows; W's height (K) drawn equal to X's height
    nc = 20.0                       # the output this bank holds: matrix column of W and Y
    g.t(X0, top - 4, f"X: {I('M')} = 8 tokens &#215; {I('K')}")
    g.t(W0, top - 4, f"W: {I('K')} &#215; {I('N')}")
    g.t(Y0, top - 4, f"Y: {I('M')} = 8 &#215; {I('N')}")
    for k in range(8):
        g.r(X0, top + k * rh, XW, rh, TOK[k], "#FFFFFF", 0.4)
        g.t(X0 - 2.5, top + k * rh + rh - 0.4, f"{k + 1}", 8.0, "end", TOK[max(k, 3)])
    g.r(X0, top, XW, H, "none", INK, 0.6)
    g.r(X0, top, XW / 2, H, "none", RED, 1.2)
    g.t((X0 + XW + W0) / 2, top + H / 2 + 3.5, "&#215;", 10.0, "middle")
    g.r(W0, top, WW, H, "#FFFFFF", INK, 0.6)
    g.l(W0, top + H / 2, W0 + WW, top + H / 2, RULE, 0.5, "2 1.5")
    g.r(W0 + nc, top, 5, H / 2, "#E8E8E8", "none", 0)
    for i in range(1, 8):
        g.l(W0 + nc, top + i * H / 16, W0 + nc + 5, top + i * H / 16, "#808080", 0.3)
    g.r(W0 + nc, top, 5, H / 2, "none", RED, 1.2)
    g.t((W0 + WW + Y0) / 2, top + H / 2 + 3.0, "=", 10.0, "middle")
    g.r(Y0, top, YW, H, "#FFFFFF", INK, 0.6)
    for k in range(8):
        g.r(Y0 + nc, top + k * rh, 5, rh, TOK[k], "none", 0)
        if k:
            g.l(Y0, top + k * rh, Y0 + nc, top + k * rh, RULE, 0.35)
            g.l(Y0 + nc + 5, top + k * rh, Y0 + YW, top + k * rh, RULE, 0.35)
    g.r(Y0 + nc, top, 5, H, "none", RED, 1.2)
    ya = top + H + 10.0
    tags = [(X0, f"8 tokens &#215; {I('K')} chunk (GB)"), (W0, "one bank's row (2 KB)"), (Y0, "8 sums")]
    for (x, s), nxt in zip(tags, [W0, Y0, W]):
        assert x + width(s.replace("&#215;", "x"), 8.0) < nxt - 4, s                 # tags do not touch
        g.t(x, ya, s, 8.0, fill=RED)

    # ---------------- (b) one weight row of one bank: stock AiM against CoDe ----------------
    yb = ya + 15.0
    g.t(1, yb, "(b) one weight row of one bank", 8.5, bold=True)
    lx, lend = 41.0, 250.0
    assert width("stock AiM", 8.0) * 1.06 + 1 < lx - 3                         # bold lane label fits left of the lane
    T = row_ns["stock"]
    sx = (lend - lx) / T                                                        # pt per ns
    lh = 14.0
    # stock AiM: 8 units RS | MAC x64 | D, widths from the per-sweep split; the D sliver widened to stay visible
    ys = yb + 15.0
    uw = (lend - lx) / SWEEPS
    rs_w = split["stock"]["row"] * sx
    d_w = max(split["stock"]["drain"] * sx, 2.5)
    mac_w = uw - rs_w - d_w
    assert abs(uw - (split["stock"]["row"] + split["stock"]["mac"] + split["stock"]["drain"]) * sx) < 1e-9
    assert mac_w > width("&#215;64".replace("&#215;", "x"), 8.0) + 3
    g.t(1, ys + lh / 2 + 3.0, "stock AiM", 8.0, bold=True)
    for k in range(SWEEPS):
        x = lx + k * uw
        g.r(x, ys, rs_w, lh, GRAY_RS, INK, 0.5)
        g.r(x + rs_w, ys, mac_w, lh, TOK[k], INK, 0.5)
        g.t(x + rs_w + mac_w / 2, ys + lh / 2 + 2.8, "&#215;64", 8.0, "middle", TOKT[k])
        g.r(x + rs_w + mac_w, ys, d_w, lh, GRAY_D, INK, 0.5)
        g.t(x + rs_w + mac_w / 2, ys - 2.5, f"{k + 1}", 8.0, "middle")
    # RS and D named on token 1's unit, below the lane, with short leaders
    yl = ys + lh + 9.0
    rs_c, d_c = lx + rs_w / 2, lx + rs_w + mac_w + d_w / 2
    g.l(rs_c, ys + lh, rs_c, yl - 6.2, INK, 0.4)
    g.l(d_c, ys + lh, d_c, yl - 6.2, INK, 0.4)
    g.t(rs_c, yl, "RS", 8.0, "middle")
    g.t(d_c, yl, "D", 8.0, "middle")
    assert rs_c + width("RS", 8.0) / 2 + 3 < d_c - width("D", 8.0) / 2
    yk = yl + 3.5
    g.bracket(lx, lend, yk, "8 row sweeps, one per token")
    # CoDe: RS | tile MAC x64 | D (burst drain), one row sweep; the block widened to hold its label
    yc = yk + 3 + 9.5 + 14.0
    g.t(lx, yc - 3.0, "1 row sweep, tokens 1&#8211;8", 8.0, fill=EDGE)
    g.t(1, yc + lh / 2 + 3.0, "CoDe", 8.0, fill=EDGE, bold=True)
    c_rs = split["core8"]["row"] * sx
    c_d = max(split["core8"]["drain"] * sx, 3.0)
    c_mac = max(split["core8"]["mac"] * sx, width("tile MAC &#215;64".replace("&#215;", "x"), 8.0) + 3.0)
    cend = lx + c_rs + c_mac + c_d
    drawn = (lend - lx) / (cend - lx)
    assert 3.5 < drawn <= row_ns["stock"] / row_ns["core8"], drawn                 # about 4:1, never above 4.40
    g.r(lx, yc, c_rs, lh, GRAY_RS, INK, 0.5)
    g.r(lx + c_rs, yc, c_mac, lh, TINT, EDGE, 0.7)
    g.t(lx + c_rs + c_mac / 2, yc + lh / 2 + 2.8, "tile MAC &#215;64", 8.0, "middle", EDGE)
    g.r(lx + c_rs + c_mac, yc, c_d, lh, TINT, EDGE, 0.5)
    # speedup: from CoDe's end to stock AiM's end
    ay = yc + lh / 2
    g.l(cend, yc - 1.5, cend, yc + lh + 1.5, "#808080", 0.5, "2 1.5")
    g.l(lend, ys + lh, lend, yc + lh + 1.5, "#808080", 0.5, "2 1.5")
    g.l(cend + 1.0, ay, lend - 1.0, ay, RED, 0.9, extra=' marker-start="url(#ar)" marker-end="url(#ar)"')
    g.t((cend + lend) / 2, ay - 3.0, "speedup", 8.5, "middle", RED, True)
    assert lx + width("1 row sweep, tokens 1-8", 8.0) + 4 < (cend + lend) / 2 - width("speedup", 8.5) * 0.55
    # RS and D named on CoDe's unit: RS to the left (clear of the zoom's left edge line), D straight below
    yl2 = yc + lh + 9.0
    crs_c, cd_c = lx + c_rs / 2, lx + c_rs + c_mac + c_d / 2
    g.l(crs_c, yc + lh, lx - 5.5, yl2 - 5.0, INK, 0.4)
    g.t(lx - 6.0, yl2, "RS", 8.0, "end")
    g.l(cd_c, yc + lh, cd_c, yl2 - 6.2, INK, 0.4)
    g.t(cd_c, yl2, "D", 8.0, "middle")
    # zoom of the whole tile-MAC block: one tile MAC = one column read, 8 beats over two column periods, x64
    zx, zy, zw, zh = lx, yl2 + 6.0, 199.0, 47.0
    g.l(lx + c_rs, yc + lh, zx, zy, EDGE, 0.5, "2 1.5")
    g.l(lx + c_rs + c_mac, yc + lh, zx + zw, zy, EDGE, 0.5, "2 1.5")
    g.r(zx, zy, zw, zh, "#FFFFFF", EDGE, 0.7)
    head1, head2 = "tile MAC: one column read (", "), 8 beats"
    g.t(zx + 5, zy + 10.0, head1, 8.0, fill=EDGE)
    xt = zx + 5 + width(head1, 8.0)
    g.tri(xt + 3.0, zy + 4.6, RED, 4.6)
    g.t(xt + 6.0, zy + 10.0, head2, 8.0, fill=EDGE)
    pitch = 19.0
    assert 4 * pitch - 2 > width("column period (4 CK)", 8.0)
    bx0, by = zx + 14.0, zy + 15.0
    g.tri(bx0 - 6.5, by + 3.7, RED, 4.6)
    g.r(bx0 - 2.5, by - 2.0, 8 * pitch + 3.0, 16.0, "none", EDGE, 0.5, "2 1.2")
    for k in range(8):
        g.r(bx0 + k * pitch, by, pitch - 2.0, 12.0, TOK[k], INK, 0.5)
        g.t(bx0 + k * pitch + (pitch - 2.0) / 2, by + 8.9, f"{k + 1}", 8.0, "middle", TOKT[k], True)
    g.bracket(bx0, bx0 + 4 * pitch - 2.0, by + 16.5, "column period (4 CK)", EDGE)
    g.bracket(bx0 + 4 * pitch, bx0 + 8 * pitch - 2.0, by + 16.5, "column period (4 CK)", EDGE)
    gx = bx0 + 8 * pitch + 6.0
    g.t(gx, by + 9.5, "&#215;64", 9.0, fill=EDGE, bold=True)
    assert gx + width("x64", 9.0) * 1.06 < zx + zw - 3
    assert by + 16.5 + 3 + 9.5 + 2.0 < zy + zh
    # the count table: equal MAC beats; what each lever removes
    ty = zy + zh + 12.0
    cols = [(76.0, "MAC beats"), (126.0, "row opens"), (176.0, "column reads"), (225.0, "MAC time")]
    for (c0, h0), (c1, h1) in zip(cols, cols[1:]):
        assert c0 + width(h0, 8.0) / 2 + 4 < c1 - width(h1, 8.0) / 2
    for cx, h in cols:
        g.t(cx, ty, h, 8.0, "middle", NOTE)
    g.l(1, ty + 3.0, W - 1, ty + 3.0, RULE, 0.6)
    tcol = f"{I('t')}<tspan font-size=\"6\" baseline-shift=\"sub\">col</tspan>"
    rows = [("stock AiM", INK, tab["stock"]), ("CoDe", EDGE, tab["core8"])]
    for i, (name, c, v) in enumerate(rows):
        yy = ty + 13.0 + i * 10.5
        g.t(1, yy, name, 8.0, fill=c, bold=True)
        vals = (f"{V} &#215; {COLS}", f"{v['opens']}", f"{v['reads']}", f"{v['periods']:g} {tcol}")
        for (cx, _), s in zip(cols, vals):
            g.t(cx, yy, s, 8.0, "middle", c)
    yr = ty + 13.0 + 10.5 + 4.0
    g.l(1, yr, W - 1, yr, RULE, 0.6)
    Hh = round(yr + 1.5, 1)
    fig = Fig(W, Hh)
    marker = ('<marker id="ar" viewBox="0 0 6 6" refX="5.5" refY="3" markerWidth="4.5" markerHeight="4.5" '
              f'orient="auto-start-reverse"><path d="M0,0 L6,3 L0,6 z" fill="{RED}"/></marker>')
    fig.o = ["<defs>" + marker + "</defs>"] + g.o
    fig.write("fig_mapping", "scripts/make_fig_mapping.py from evaluation/dac_2x2/raw/utrace_run_{stock,core8}.csv")
    print(f"drawn lane ratio {drawn:.2f} (data {row_ns['stock'] / row_ns['core8']:.2f})")


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
        fh.write("% generated by scripts/make_fig_mapping.py (counts checked on the V = 8 trace, evaluation/dac_2x2 "
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
