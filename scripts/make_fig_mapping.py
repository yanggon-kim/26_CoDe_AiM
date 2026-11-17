#!/usr/bin/env python3
"""Fig. mapping (Sec. IV-B, IV-C) and Table cmds (Sec. IV-D): a skinny GEMM on CoDe at M = 8, mobile platform.

(a) The skinny GEMM X (M = 8 tokens x K) . W (K x N) = Y (M x N), each token row in its own blue shade (light token 1
to dark token 8), one curly brace "8" over X's token rows (rows drawn 4.2 pt, 0.7x the former 6 pt; 2026-11-15); red boxes mark one bank's work in one row sweep: the 8 tokens' K chunk (in the GB), one matrix
column of W over that chunk (one bank's 2 KB DRAM row = one output's weights), and that output's 8 sums.
(b) One weight row of one bank (Llama-2-7B q_proj, steady state). Both lanes start at the same x; lane length is
proportional to time with two drawing allowances (the paper needs only the impression of the gap): RS and D boxes are
widened to hold their 7 pt labels (CoDe's as wide as stock AiM's), and CoDe's tile-MAC block is widened to hold its
label (drawn ratio asserted in 2.5..4.40, about 3:1). Lane names sit above the lanes (left-aligned).
Stock AiM: 8 units RS | MAC x64 | D, one per token; CoDe: RS | tile MAC x64 | D (burst drain), one row sweep. A red
double arrow "speedup" spans CoDe's end to stock's end (no ratio printed). Bold labels name the paper's two root causes
(red, Sec. III-B: row switching overhead under the stock lane, left-aligned, idle beats in the stock zoom) and two designs (green,
Sec. IV-B row reuse under the tile MAC, IV-C beat filling in the CoDe zoom; user 2026-11-16, replacing the zoom
headers and the column-read triangle). The zoom shows one tile MAC: one column read, 8 beats, two column periods. Table: MAC beats / row opens / column reads / MAC time per weight row.
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
TINT, RED = "#CFE2F3", "#E03127"
GREEN = "#1A8F3C"                # speedup and the CoDe highlights (user 2026-11-16)
HL = 1.3                         # red / green highlight stroke, as thick as (a)'s bold boxes (user 2026-11-16)
FACE_R, FACE_SW = 4.2, 0.9       # faces enlarged from r 3.0 / 0.6 pt strokes (user 2026-11-16)


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

    def face(self, cx, cy, color, smile, r=FACE_R):
        """A line-drawn face (no emoji glyph, so the PDF needs no extra font); the 3 pt design scaled by r / 3."""
        k = r / 3.0
        m = 0.9 if smile else -0.9                                             # mouth curvature
        my = cy + (0.9 if smile else 1.7) * k
        self.o.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="#FFFFFF" stroke="{color}" stroke-width="{FACE_SW}"/>'
                      f'<circle cx="{cx - 1.05 * k:.2f}" cy="{cy - 0.8 * k:.2f}" r="{0.42 * k:.2f}" fill="{color}"/>'
                      f'<circle cx="{cx + 1.05 * k:.2f}" cy="{cy - 0.8 * k:.2f}" r="{0.42 * k:.2f}" fill="{color}"/>'
                      f'<path d="M{cx - 1.4 * k:.2f} {my:.2f} Q{cx:.2f} {my + m * 1.4 * k:.2f} {cx + 1.4 * k:.2f} {my:.2f}" '
                      f'fill="none" stroke="{color}" stroke-width="{FACE_SW}" stroke-linecap="round"/>')


def I(s):
    return f'<tspan font-style="italic">{s}</tspan>'


def SUB(base, s, size, tail=""):
    """Italic base with an upright subscript at 0.7 em, lowered 0.22 em by dy (Chrome's baseline-shift="sub" drops
    too far); the tail (text after the subscript) is lifted back to the baseline (user 2026-11-17)."""
    k, d = 0.7 * size, 0.22 * size
    back = f'<tspan dy="{-d:.2f}">{tail}</tspan>' if tail else ""
    return f'{I(base)}<tspan font-size="{k:.2f}" dy="{d:.2f}">{s}</tspan>{back}'


def draw(row_ns, split, tab):
    W = 240.0                       # ACM sigconf \columnwidth in pt (IEEEtran was 252)
    g = S()
    # ---------------- (a) the skinny GEMM, M = 8; one bank's work in one row sweep in bold black outlines ----------------
    g.t(1, 8.5, f"(a) skinny GEMM, {I('M')} = 8", 8.5, bold=True)
    top, rh = 25.0, 4.2             # row height 0.7 x the former 6.0 pt (user 2026-11-15: shorter panel (a))
    X0, XW = 12.0, 70.0
    W0, WW = 98.0, 56.0
    Y0, YW = 178.0, 56.0
    H = 8 * rh                      # X and Y rows; W's height (K) drawn equal to X's height
    nc = 20.0                       # the output this bank holds: matrix column of W and Y
    g.t(X0, top - 4, f"X: {I('M')} = 8 tokens &#215; {I('K')}")
    g.t(W0, top - 4, f"W: {I('K')} &#215; {I('N')}")
    g.t(Y0, top - 4, f"Y: {I('M')} = 8 &#215; {I('N')}")
    for k in range(8):
        g.r(X0, top + k * rh, XW, rh, TOK[k], "#FFFFFF", 0.4)
    g.r(X0, top, XW, H, "none", INK, 0.6)
    # one curly brace over the eight token rows with a single "8" (user 2026-11-15: replaces the row numbers 1..8)
    bxr, bxm, bxl, q, ym = X0 - 1.5, X0 - 3.5, X0 - 5.5, 2.5, top + H / 2
    g.o.append(f'<path d="M{bxr:.2f} {top:.2f} Q{bxm:.2f} {top:.2f} {bxm:.2f} {top + q:.2f} L{bxm:.2f} {ym - q:.2f} '
               f'Q{bxm:.2f} {ym:.2f} {bxl:.2f} {ym:.2f} Q{bxm:.2f} {ym:.2f} {bxm:.2f} {ym + q:.2f} '
               f'L{bxm:.2f} {top + H - q:.2f} Q{bxm:.2f} {top + H:.2f} {bxr:.2f} {top + H:.2f}" fill="none" '
               f'stroke="{INK}" stroke-width="0.6"/>')
    assert bxl - 0.8 - width("8", 8.5) > 0                                      # the "8" stays on the canvas
    g.t(bxl - 0.8, ym + 3.0, "8", 8.5, "end")
    g.r(X0, top, XW / 2, H, "none", INK, 1.3)
    g.t((X0 + XW + W0) / 2, top + H / 2 + 3.5, "&#215;", 10.0, "middle")
    g.r(W0, top, WW, H, "#FFFFFF", INK, 0.6)
    g.l(W0, top + H / 2, W0 + WW, top + H / 2, RULE, 0.5, "2 1.5")
    g.r(W0 + nc, top, 5, H / 2, "#E8E8E8", "none", 0)
    for i in range(1, 8):
        g.l(W0 + nc, top + i * H / 16, W0 + nc + 5, top + i * H / 16, "#808080", 0.3)
    g.r(W0 + nc, top, 5, H / 2, "none", INK, 1.3)
    g.t((W0 + WW + Y0) / 2, top + H / 2 + 3.0, "=", 10.0, "middle")
    g.r(Y0, top, YW, H, "#FFFFFF", INK, 0.6)
    for k in range(8):
        g.r(Y0 + nc, top + k * rh, 5, rh, TOK[k], "none", 0)
        if k:
            g.l(Y0, top + k * rh, Y0 + nc, top + k * rh, RULE, 0.35)
            g.l(Y0 + nc + 5, top + k * rh, Y0 + YW, top + k * rh, RULE, 0.35)
    g.r(Y0 + nc, top, 5, H, "none", INK, 1.3)
    ya = top + H + 10.0
    tags = [(X0, f"8 tokens &#215; {I('K')} chunk (GB)"), (W0, "one bank's row (2 KB)"), (Y0, "8 sums")]
    for (x, s), nxt in zip(tags, [W0, Y0, W]):
        assert x + width(s.replace("&#215;", "x"), 8.0) < nxt - 4, s                 # tags do not touch
        g.t(x, ya, s, 8.0)

    # ---------------- (b) one weight row of one bank: stock AiM against CoDe ----------------
    # Lane names sit above their lanes, so the lanes span the width and each stock unit gets about 30 pt. RS and D
    # carry their labels inside at 7 pt and stock AiM's "x64" sits at 6.5 pt: the user's explicit decision (2026-10-29).
    # panel (b) drawn at 0.8 of its former height (user 2026-11-15): lanes 11 pt, CoDe's name on the line of the stock
    # bracket's label (that label right-aligned), "speedup" set inside its arrow, and a tighter zoom box and table
    yb = ya + 11.0                  # 1 pt tighter (user 2026-11-17: one more body line under Fig. 1 on p. 1)
    g.t(1, yb, "(b) one weight row of one bank", 8.5, bold=True)
    i_under = len(g.o)              # the stock zoom's dashed lines go here, under every later box and label
    lx, lend = 1.5, W - 1.5
    T = row_ns["stock"]
    sx = (lend - lx) / T                                                        # pt per ns
    lh = 11.0
    # stock AiM: 8 adjacent units RS | MAC x64 | D; the lane length is the data (3,250 ns), and RS and D are widened
    # to hold their labels, the MAC block taking the rest of each unit
    yn = yb + 10.0                                                              # lane name
    LB = 8.0                                                                    # root-cause / design labels, bold
    ys = yn + 14.0                                  # lane top (token numbers and the face between; user 2026-11-16:
                                                    # "Root cause 1" moved under the stock lane)
    uw = (lend - lx) / SWEEPS
    rs_w = max(split["stock"]["row"] * sx, width("RS", 7.0) + 1.8)          # 0.9 pt pad a side (ACM column)
    d_w = max(split["stock"]["drain"] * sx, width("D", 7.0) + 1.8)
    mac_w = uw - rs_w - d_w
    assert abs(uw * SWEEPS - (split["stock"]["row"] + split["stock"]["mac"] + split["stock"]["drain"]) * SWEEPS * sx) < 1e-9
    # unit floor 29 pt since the ACM column (240 pt; 30 pt on IEEEtran's 252); the label fit is the binding check
    assert uw > 29 and mac_w > width("x64", 6.5) + 2.4, (uw, mac_w)
    # list bullets before the two lane names, in each name's colour (user 2026-11-16)
    bul = width("\u2022", 8.0) + 2.0                                          # bullet + 2 pt gap
    g.t(lx, yn, "&#8226;", 8.0, bold=True)
    nrm = '<tspan font-weight="normal">'
    slab = "8 separate GEMV row sweeps for tokens 1&#8211;8"
    g.t(lx + bul, yn, f"stock AiM:{nrm} {slab}</tspan>", 8.0, bold=True)
    assert lx + bul + width("stock AiM: ", 8.0) * 1.06 + width(slab.replace("&#8211;", "-"), 8.0) < W - 1
    for k in range(SWEEPS):
        x = lx + k * uw
        g.r(x, ys, rs_w, lh, GRAY_RS, INK, 0.5)
        g.t(x + rs_w / 2, ys + lh / 2 + 2.5, "RS", 7.0, "middle")
        g.r(x + rs_w, ys, mac_w, lh, TOK[k], INK, 0.5)
        g.t(x + rs_w + mac_w / 2, ys + lh / 2 + 2.3, "&#215;64", 6.5, "middle", TOKT[k])
        g.r(x + rs_w + mac_w, ys, d_w, lh, GRAY_D, INK, 0.5)
        g.t(x + rs_w + mac_w + d_w / 2, ys + lh / 2 + 2.5, "D", 7.0, "middle")
        g.t(x + rs_w + mac_w / 2, ys - 2.5, f"{k + 1}", 8.0, "middle")
    # red highlights (user 2026-11-16): each D | RS pair between consecutive tokens, D of token 1 .. RS of token 8,
    # is the time CoDe removes; a small sad face between the token labels 7 and 8
    for k in range(SWEEPS - 1):
        x0, x1 = lx + k * uw + rs_w + mac_w, lx + (k + 1) * uw + rs_w
        g.r(x0 - HL / 2, ys - HL / 2, x1 - x0 + HL, lh + HL, "none", RED, HL)
    fx = lx + 6.5 * uw + rs_w + mac_w / 2
    fy = ys - 2.3 - FACE_R - FACE_SW / 2                                       # face bottom 2.3 pt above the lane
    assert fx - FACE_R - FACE_SW / 2 > lx + 6 * uw + rs_w + mac_w / 2 + width("7", 8.0) / 2 + 2  # clear of "7"
    assert fx + FACE_R + FACE_SW / 2 < lx + 7 * uw + rs_w + mac_w / 2 - width("8", 8.0) / 2 - 2  # clear of "8"
    assert fy - FACE_R - FACE_SW / 2 > yn + 2.0                                 # under the lane name's descenders
    assert yn + 2.0 < ys - 2.5 - 5.8                                            # name clear of the token numbers
    g.face(fx, fy, RED, False)
    # root cause 1 under the stock lane, above CoDe's lane name, its start on the left edge of the first red box
    # (token 1's D | token 2's RS; user 2026-11-16); its end clear of the stock zoom's dashed lines, checked below
    rc1 = "Root cause 1: row switching overhead"
    w_rc1 = width(rc1, LB) * 1.06
    x_rc1 = lx + rs_w + mac_w - HL / 2                                          # first red box's left edge
    yr1 = ys + lh + 8.5                                                         # cap top 2.9 pt below the lane
    g.t(x_rc1, yr1, rc1, LB, "start", RED, True)
    bl_y = yr1 + 9.5                                                            # CoDe's lane name
    # CoDe: RS | tile MAC x64 | D (burst drain), one row sweep; RS and D as wide as stock AiM's, the tile-MAC block
    # widened to hold its label, so the drawn lanes keep about 3:1 of the 4.40x
    yc = bl_y + 3.0
    g.t(lx, yc - 3.0, "&#8226;", 8.0, bold=True)                              # black, like stock AiM's (user 2026-11-16)
    sub = "1 GEMM sweep for tokens 1&#8211;8"
    g.t(lx + bul, yc - 3.0, f"CoDe:{nrm} {sub}</tspan>", 8.0, bold=True)
    c_rs, c_d = rs_w, d_w
    c_mac = max(split["core8"]["mac"] * sx, width("tile MAC &#215;64".replace("&#215;", "x"), 8.0) + 3.0)
    cend = lx + c_rs + c_mac + c_d
    drawn = (lend - lx) / (cend - lx)
    assert 2.5 < drawn <= row_ns["stock"] / row_ns["core8"], drawn                 # about 3:1, never above 4.40
    g.r(lx, yc, c_rs, lh, GRAY_RS, INK, 0.5)
    g.t(lx + c_rs / 2, yc + lh / 2 + 2.5, "RS", 7.0, "middle")
    g.r(lx + c_rs, yc, c_mac, lh, TINT, INK, 0.7)   # black edge and text like the zoom frame (user 2026-11-16)
    g.t(lx + c_rs + c_mac / 2, yc + lh / 2 + 2.8, "tile MAC &#215;64", 8.0, "middle", INK)
    g.r(lx + c_rs + c_mac, yc, c_d, lh, GRAY_D, INK, 0.5)
    g.t(lx + c_rs + c_mac + c_d / 2, yc + lh / 2 + 2.5, "D", 7.0, "middle")
    g.r(lx - HL / 2, yc - HL / 2, c_rs + HL, lh + HL, "none", GREEN, HL)          # green: what CoDe pays once
    g.r(lx + c_rs + c_mac - HL / 2, yc - HL / 2, c_d + HL, lh + HL, "none", GREEN, HL)
    # speedup: from CoDe's end to stock AiM's end, the label inside a break in the arrow
    ay = yc + lh / 2
    g.l(cend, yc, cend, yc + lh + 1.5, "#808080", 0.5, "2 1.5")
    g.l(lend, ys + lh, lend, yc + lh + 1.5, "#808080", 0.5, "2 1.5")
    # the stock zoom's dashed lines (drawn later, from token 8's x64 block to the right zoom box) cross the arrow row;
    # "speedup" ends 1.5 pt left of the first line and the enlarged smiling face starts right of it
    # design 1 under the tile-MAC block, between the CoDe lane and the time axis (canvas taller by its line)
    GAP_Z = 3.0
    yd1 = yc + lh + 7.5
    yt = yd1 + 3.2
    m8z, zy_ = lx + 7 * uw + rs_w, yt + 3.5 + GAP_Z
    zx2_ = 1.0 + (8 * 15.0 - 2.0 + 7.0) + 3.5
    xds = [xa + (xb - xa) * (ay - (ys + lh)) / (zy_ - (ys + lh)) for xa, xb in ((m8z, zx2_), (m8z + mac_w, W - 1.0))]
    x_dash = m8z + (zx2_ - m8z) * (yr1 + 2.0 - (ys + lh)) / (zy_ - (ys + lh))     # left dashed line at rc1's foot
    assert x_rc1 + w_rc1 < x_dash - 3.0, (x_rc1 + w_rc1, x_dash)                       # rc1 clear of the dashed lines
    wt = width("speedup", 8.5) * 1.06
    tx = xds[0] - 1.5 - wt / 2                                                  # "speedup", a smiling face on its right
    fcx = tx + wt / 2 + 3.5 + FACE_R
    lb, rb = tx - wt / 2 - 3.0, fcx + FACE_R + 2.5
    g.l(cend + 1.0, ay, lb, ay, GREEN, 0.9, extra=' marker-start="url(#ar)"')
    g.l(rb, ay, lend - 1.0, ay, GREEN, 0.9, extra=' marker-end="url(#ar)"')
    fh = FACE_R + FACE_SW / 2 + 0.3
    g.r(lb, ay - fh, rb - lb, 2 * fh, "#FFFFFF", "none", 0)                  # white backing under the dashed line
    g.t(tx, ay + 3.0, "speedup", 8.5, "middle", GREEN, True)
    g.face(fcx, ay, GREEN, True)
    assert lb - (cend + 1.0) > 12 and lend - 1.0 - rb > 12                       # both arrow halves visible
    for xd in xds:
        assert abs(xd - fcx) > FACE_R + FACE_SW / 2 + 1.0, (xd, fcx)          # smiling face clear of both lines
    # time axis under the CoDe lane and its "Design 1" label (user 2026-11-16): the lanes' horizontal direction is time
    d1 = "Design 1: row reuse"
    w_d1, xd1 = width(d1, LB) * 1.06, lx + c_rs + c_mac / 2
    assert xd1 - w_d1 / 2 > 1.0
    xe = W - 1.0 - width("time", 8.0) - 2.5                                     # 1.3 pt line, 8 pt label (user 2026-11-16)
    g.l(lx, yt, xe, yt, INK, 1.3, extra=' marker-end="url(#ak)"')
    g.t(xe + 2.0, yt + 2.8, "time", 8.0)
    # two zooms at 6.5 pt (user 2026-11-16): left, CoDe's tile MAC (one column read, 8 beats, all filled); right,
    # stock AiM's MAC of token 8 (one column read, 1 beat of 4 filled, 3 idle); the zoom boxes keep the former
    # bottom edge relative to the time axis
    zs, p, bh = 6.5, 15.0, 9.5                                                  # zoom font, beat pitch, beat height
    zy, zh = yt + 3.5 + GAP_Z, 38.0                                            # 1 pt shorter (2026-11-17)
    zc = 6.3                                                                    # bracket label 6.5 -> 6.3 pt to fit t_CK
    ck = SUB("t", "CK", zc, ")")                                                # t_CK as in the caption (2026-11-17)
    assert 4 * p - 2 > width("column period (4 t)", zc) + width("CK", 0.7 * zc)   # label within its bracket
    zx1, zw1 = 1.0, 8 * p - 2.0 + 7.0
    zx2 = zx1 + zw1 + 3.5
    assert abs(zy - zy_) < 1e-9 and abs(zx2 - zx2_) < 1e-9                       # the face check used these
    zw2 = W - 1.0 - zx2
    by = zy + 11.5

    def head(x, y, s, c):                                                       # bold zoom header at LB
        g.t(x, y, s, LB, fill=c, bold=True)
        return x + width(s, LB) * 1.06

    def beats(x0, n, fills, c):
        g.r(x0 - 1.6, by - 1.6, n * p - 2.0 + 3.2, bh + 3.2, "none", c, 0.5, "2 1.2")   # the one column read
        for k, f in enumerate(fills):
            g.r(x0 + k * p, by, p - 2.0, bh, TOK[f] if f is not None else "#FFFFFF", INK, 0.5)
            if f is not None:
                g.t(x0 + k * p + (p - 2.0) / 2, by + 7.0, f"{f + 1}", zs, "middle", TOKT[f], True)
        for j in range(n // 4):
            g.bracket(x0 + 4 * j * p, x0 + (4 * j + 4) * p - 2.0, by + bh + 2.0, f"column period (4 {ck}", c, zc)

    def hl(x0, k0, k1, c):                                                      # highlight beats k0..k1
        g.r(x0 + k0 * p - HL / 2, by - HL / 2, (k1 - k0 + 1) * p - 2.0 + HL, bh + HL, "none", c, HL)

    # left: CoDe's tile MAC
    g.l(lx + c_rs, yc + lh, zx1, zy, INK, 0.5, "2 1.5")
    g.l(lx + c_rs + c_mac, yc + lh, zx1 + zw1, zy, INK, 0.5, "2 1.5")
    g.r(zx1, zy, zw1, zh, "#FFFFFF", INK, 0.7)
    assert head(zx1 + 3.0, zy + 8.0, "Design 2: beat filling", GREEN) < zx1 + zw1 - 2
    # design 1 drawn after the left zoom's dashed lines, on a white backing where they pass under it
    g.r(xd1 - w_d1 / 2 - 0.5, yd1 - 6.0, w_d1 + 1.0, 8.0, "#FFFFFF", "none", 0)
    g.t(xd1, yd1, d1, LB, "middle", GREEN, True)
    b1 = zx1 + 3.5
    beats(b1, 8, list(range(8)), INK)
    hl(b1, 1, 3, GREEN)
    hl(b1, 5, 7, GREEN)
    # right: stock AiM's MAC of token 8; its dashed lines from that token's x64 block, drawn under everything
    m8 = lx + 7 * uw + rs_w
    g.o.insert(i_under, f'<line x1="{m8:.2f}" y1="{ys + lh:.2f}" x2="{zx2:.2f}" y2="{zy:.2f}" stroke="{INK}" '
                        f'stroke-width="0.5" stroke-dasharray="2 1.5"/>'
                        f'<line x1="{m8 + mac_w:.2f}" y1="{ys + lh:.2f}" x2="{zx2 + zw2:.2f}" y2="{zy:.2f}" '
                        f'stroke="{INK}" stroke-width="0.5" stroke-dasharray="2 1.5"/>')
    g.r(zx2, zy, zw2, zh, "#FFFFFF", INK, 0.7)
    assert head(zx2 + 3.0, zy + 8.0, "Root cause 2: idle beats", RED) < zx2 + zw2 - 2
    b2 = zx2 + 3.5
    beats(b2, 4, [7, None, None, None], INK)
    hl(b2, 1, 3, RED)
    assert by + bh + 2.0 + 3 + zs + 1.5 + 1.5 < zy + zh
    # the count table: equal MAC beats; what each lever removes
    ty = zy + zh + 8.5                                                          # 0.5 pt tighter (2026-11-17)
    cols = [(74.0, "MAC beats"), (121.0, "row opens"), (168.0, "column reads"), (214.0, "MAC time")]
    for (c0, h0), (c1, h1) in zip(cols, cols[1:]):
        assert c0 + width(h0, 8.0) / 2 + 4 < c1 - width(h1, 8.0) / 2
    for cx, h in cols:
        g.t(cx, ty, h, 8.0, "middle", NOTE)
    g.l(1, ty + 3.0, W - 1, ty + 3.0, RULE, 0.6)
    tcol = SUB("t", "col", 8.0)
    rows = [("stock AiM", INK, tab["stock"]), ("CoDe", INK, tab["core8"])]
    for i, (name, c, v) in enumerate(rows):
        yy = ty + 11.5 + i * 9.5
        g.t(1, yy, name, 8.0, fill=c, bold=True)
        vals = (f"{V} &#215; {COLS}", f"{v['opens']}", f"{v['reads']}", f"{v['periods']:g} {tcol}")
        for (cx, _), s in zip(cols, vals):
            g.t(cx, yy, s, 8.0, "middle", c)
    yr = ty + 11.5 + 9.5 + 3.5
    g.l(1, yr, W - 1, yr, RULE, 0.6)
    Hh = round(yr + 1.0, 1)
    print(f"panel (b) height {Hh - ya:.1f} pt (from (a)'s tag line)")
    fig = Fig(W, Hh)
    marker = ('<marker id="ar" viewBox="0 0 6 6" refX="5.5" refY="3" markerWidth="4.5" markerHeight="4.5" '
              f'orient="auto-start-reverse"><path d="M0,0 L6,3 L0,6 z" fill="{GREEN}"/></marker>'
              '<marker id="ak" viewBox="0 0 6 6" refX="5.5" refY="3" markerWidth="4" markerHeight="4" '
              f'orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="{INK}"/></marker>')
    fig.o = ["<defs>" + marker + "</defs>"] + g.o
    fig.write("fig_mapping", "scripts/make_fig_mapping.py from evaluation/dac_2x2/raw/utrace_run_{stock,core8}.csv. "
              "Text below 8 pt is the user's explicit decision (2026-10-29): panel (b)'s RS and D labels inside their "
              "boxes at 7 pt and stock AiM's x64 at 6.5 pt (subscripts at 0.7 em); the two zoom boxes at 6.5 pt "
              "(user 2026-11-16)")
    print(f"drawn lane ratio {drawn:.2f} (data {row_ns['stock'] / row_ns['core8']:.2f})")


def table():
    """Table cmds (WRGB row dropped, user 2026-11-12; prose keeps WRGB): CoDe's commands, count per token against stock AiM (symbolic in V; the V = 8 trace checks it)."""
    rows = [
        (r"\emph{tile MAC} (col, $V$)", r"One column read at the stock MAC timing; $V$ beats on it", "column", r"$1/V$", "1"),
        (r"\emph{burst drain}", r"A tile's $V$ sums out in one burst", "row sweep", "1", "1"),
        ("row switch", r"TMOD$\times$2, PREA, ACT16 pair, WRMAC16; unchanged", "row sweep", r"$1/V$", "1"),
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
