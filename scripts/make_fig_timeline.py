#!/usr/bin/env python3
"""Figure (Sec. III-B): one weight column of one bank, M tokens, PU depth D, time in column periods T.

A schematic (no measured data): four designs, each with three lanes (cmd / bank / PU).
  Stock AiM    : one command + one column read + one PU beat (T/D wide) per token; time M*T.
  LP-Spec-style: ceil(M/4) reads, one command each; 4 parallel ALU lanes, each busy a full T; 4x multipliers.
  P3-LLM-style : p = min(D, 2) tokens per read (tCCD_S = T/2 caps the command spacing); one command per token
                 at offsets k/p inside the read; time ceil(M/p)*T.
  CoDe         : one command + one read per tile of V tokens; beats T/D wide back to back; the column is held
                 for max(1, m/D) periods (m = tokens in the tile).
Asserts the counts the figure prints at D = 4, M = 8, V = 8:
  stock 8T / 8 cmd / 8 rd; LP-Spec 2T / 2 / 2; P3 4T / 8 / 4; CoDe 2T / 1 / 1.
Layout (skill F10): one column (252 pt), four stacked units (stock, area family, faster-PU family, CoDe), each a header row (name left, summary right) over its
cmd / bank / PU lanes on the shared 0T..8T grid; one time axis at the bottom. Rivals in white / grays, CoDe in the
one tint (#CFE2F3 fill, #2B5FA8 stroke).
Writes figs/src/fig_timeline.html (one inline SVG at final size); then
  python3 scripts/html2pdf.py fig_timeline   ->  figs/fig_timeline.pdf (+ .png preview).
"""
import math
import os
import re

from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
D, M, V, LPSPEC_ALUS = 4, 8, 8, 4

GRAY_READ = "#E8E8E8"
GRAY_BEAT = "#808080"
GRAY_ALU = "#A6A6A6"
GRID = "#BFBFBF"
TINT, TINT_EDGE = "#CFE2F3", "#2B5FA8"


def model(design):
    """Return dict: cmds (times), reads [(t0, t1)], beats [(t0, t1, lane)], T total, mult (x stock)."""
    cmds, reads, beats = [], [], []
    if design == "stock":
        for k in range(M):
            cmds.append(k)
            reads.append((k, k + 1))
            beats.append((k, k + 1 / D, 0))
        mult = 1
    elif design == "p3":
        p = min(D, 2)
        for j in range(math.ceil(M / p)):
            reads.append((j, j + 1))
            for k in range(p):
                if j * p + k < M:
                    t = j + k / p
                    cmds.append(t)
                    beats.append((t, t + 1 / D, 0))
        mult = 1
    elif design == "lpspec":
        for j in range(math.ceil(M / LPSPEC_ALUS)):
            cmds.append(j)
            reads.append((j, j + 1))
            for lane in range(LPSPEC_ALUS):
                if j * LPSPEC_ALUS + lane < M:
                    beats.append((j, j + 1, lane))
        mult = LPSPEC_ALUS
    elif design == "core":
        t = 0.0
        for start in range(0, M, V):
            m = min(V, M - start)
            held = max(1.0, m / D)
            cmds.append(t)
            reads.append((t, t + held))
            for k in range(m):
                beats.append((t + k / D, t + (k + 1) / D, 0))
            t += held
        mult = 1
    total = max(max(r[1] for r in reads), max(b[1] for b in beats))
    return dict(cmds=cmds, reads=reads, beats=beats, T=total, mult=mult)


ROWS = [("stock", "Stock AiM"), ("lpspec", "LP-Spec-style"), ("p3", "P3-LLM-style"), ("core", "CoDe")]   # area family first
EXPECT = {"stock": (8, 8, 8), "p3": (4, 8, 4), "lpspec": (2, 2, 2), "core": (2, 1, 1)}

# ---- geometry (pt; 1 SVG unit = 1 pt; \columnwidth = 252 pt) ----
W = 252
FS, FN = 8, 8.5            # body text, design names
X0, PER_T = 22.0, 28.125   # grid origin and width of one column period T (8T = 225 pt)
HEAD_H, LANE_H, NOTE_H, UNIT_GAP = 11.0, 10.0, 10.0, 4.0
I = lambda s: f'<tspan font-style="italic">{s}</tspan>'                       # a variable
SUB = lambda s: f'<tspan dy="1.8" font-size="6">{s}</tspan><tspan dy="-1.8"> </tspan>'
FONT = "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"   # the face the PDF embeds


def text_width(markup, size=FS):
    """Approximate rendered width (pt) of a label: tags stripped, measured in Liberation Serif at `size`."""
    plain = re.sub(r"<[^>]+>", "", markup).replace("&#8592;", "<-").replace("&#215;", "x")
    return ImageFont.truetype(FONT, 100).getlength(plain) * size / 100


def main():
    res = {d: model(d) for d, _ in ROWS}
    for d, (t, c, r) in EXPECT.items():
        got = (res[d]["T"], len(res[d]["cmds"]), len(res[d]["reads"]))
        assert got == (t, c, r), (d, got)
    print("checks: stock 8T/8/8, P3 4T/8/4, LP-Spec 2T/2/2, CoDe 2T/1/1 at D = 4, M = 8, V = 8")

    o = []
    X = lambda t: X0 + t * PER_T

    def rect(x, y, w, h, fill, stroke, sw=0.5):
        o.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}"/>')

    def text(x, y, s, size=FS, anchor="start", color="#000000", extra=""):
        fill = "" if color == "#000000" else f' fill="{color}"'
        o.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}"{fill}{extra}>{s}</text>')

    def note(x, y, s, color="#000000"):
        rect(x - 1, y - 6.3, text_width(s) + 2, 8.2, "#FFFFFF", "none", 0)
        text(x, y, s, FS, "start", color)

    def hline(x0, x1, y, color=GRID, sw=0.4):
        o.append(f'<line x1="{x0:.2f}" y1="{y:.2f}" x2="{x1:.2f}" y2="{y:.2f}" stroke="{color}" stroke-width="{sw}"/>')

    def span(x0, x1, y, color="#000000"):   # double-headed bracket between two events
        m = "ab" if color == TINT_EDGE else "ah"
        o.append(f'<line x1="{x0:.2f}" y1="{y:.2f}" x2="{x1:.2f}" y2="{y:.2f}" stroke="{color}" stroke-width="0.6" '
                 f'marker-start="url(#{m})" marker-end="url(#{m})"/>')

    y = 0.5
    for d, name in ROWS:
        r, ours = res[d], d == "core"
        accent = TINT_EDGE if ours else "#000000"
        # header row: name left, summary right
        base = y + 8.2
        text(0, base, name, FN, "start", accent, ' font-weight="bold"')
        summary = f"{r['T']:g}{I('T')}, {len(r['cmds'])} cmd, {len(r['reads'])} rd, {r['mult']}&#215; mult."
        text(W - 0.5, base, summary, FS, "end", accent, ' font-weight="bold"' if ours else "")
        y += HEAD_H
        y_end = y + 3 * LANE_H + (NOTE_H if d == "stock" else 0)
        for k in range(M + 1):   # dotted grid at every period, inside this unit's lanes only
            o.append(f'<line x1="{X(k):.2f}" y1="{y:.2f}" x2="{X(k):.2f}" y2="{y_end:.2f}" stroke="{GRID}" '
                     f'stroke-width="0.4" stroke-dasharray="0.8,1.2"/>')
        y_cmd, y_bank, y_pu = y, y + LANE_H, y + 2 * LANE_H
        for yy, lab in ((y_cmd, "cmd"), (y_bank, "bank"), (y_pu, "PU")):
            text(X0 - 3, yy + 7.2, lab, FS, "end", "#404040")
            hline(X0, X(M), yy)
        hline(X0, X(M), y_pu + LANE_H)
        # commands: a stem with a downward head
        for t in r["cmds"]:
            x = X(t)
            o.append(f'<line x1="{x:.2f}" y1="{y_cmd + 2.6:.2f}" x2="{x:.2f}" y2="{y_cmd + LANE_H - 1.2:.2f}" '
                     f'stroke="#000000" stroke-width="0.9"/>')
            o.append(f'<path d="M{x - 2:.2f},{y_cmd + 1.2:.2f} L{x + 2:.2f},{y_cmd + 1.2:.2f} L{x:.2f},{y_cmd + 4.2:.2f} z" '
                     f'fill="#000000"/>')
        # column reads
        for (t0, t1) in r["reads"]:
            fc, ec = (TINT, TINT_EDGE) if ours else (GRAY_READ, "#000000")
            rect(X(t0) + 0.6, y_bank + 1.3, X(t1) - X(t0) - 1.2, LANE_H - 2.6, fc, ec)
            if ours:
                text((X(t0) + X(t1)) / 2, y_bank + 7.3, "column held", FS, "middle")
        # PU beats
        if d == "lpspec":
            sub = (LANE_H - 2) / LPSPEC_ALUS
            for (t0, t1, lane) in r["beats"]:
                rect(X(t0) + 0.6, y_pu + 1 + lane * sub + 0.15, X(t1) - X(t0) - 1.2, sub - 0.3, GRAY_ALU, "#000000", 0.4)
        else:
            for (t0, t1, _) in r["beats"]:
                fc, ec = (TINT_EDGE, TINT_EDGE) if ours else (GRAY_BEAT, "#000000")
                rect(X(t0) + 0.3, y_pu + 1.3, X(t1) - X(t0) - 0.6, LANE_H - 2.6, fc, ec, 0.4)
        # end-of-design rule
        o.append(f'<line x1="{X(r["T"]):.2f}" y1="{y_cmd:.2f}" x2="{X(r["T"]):.2f}" y2="{y_pu + LANE_H:.2f}" '
                 f'stroke="#000000" stroke-width="0.8" stroke-dasharray="2,1.5"/>')
        # in-lane notes
        if d == "stock":
            yb = y_pu + LANE_H + 3.5
            span(X(0), X(1), yb)
            note(X(1) + 3, yb + 2.8, f"{I('T')} = one column period; the PU computes {I('T')}/{I('D')} of it")
        elif d == "p3":
            span(X(3.0) + 0.5, X(3.5) - 0.5, y_cmd + 6.5)
            note(X(4) + 2.5, y_cmd + 7.2, f"&#8592; command spacing {I('t')}{SUB('CCD_S')}= {I('T')}/2")
        elif d == "lpspec":
            note(X(2) + 4, y_bank + 7.3, "4 ALUs, each busy a full " + I("T"))
            note(X(2) + 4, y_pu + 7.3, "(one read feeds 4 tokens)")
        elif d == "core":
            span(X(0.5), X(0.75), y_cmd + 5.0, TINT_EDGE)
            note(X(0.75) + 3, y_cmd + 7.2, f"beat = {I('T')}/{I('D')} = 1 CK", TINT_EDGE)
            note(X(2) + 4, y_pu + 7.3, f"8 beats of one held column, {I('D')} = 4 per {I('T')}", TINT_EDGE)
        y = y_pu + LANE_H + (NOTE_H if d == "stock" else 0) + UNIT_GAP
    # time axis
    ya = y - UNIT_GAP + 2
    o.append(f'<line x1="{X(0):.2f}" y1="{ya:.2f}" x2="{X(M):.2f}" y2="{ya:.2f}" stroke="#000000" stroke-width="0.6"/>')
    for k in range(M + 1):
        o.append(f'<line x1="{X(k):.2f}" y1="{ya:.2f}" x2="{X(k):.2f}" y2="{ya + 2:.2f}" stroke="#000000" '
                 f'stroke-width="0.6"/>')
        text(X(k), ya + 9.5, f"{k}{I('T')}", FS, "middle")
    H = math.ceil(ya + 11.5)

    head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>fig_timeline</title>
<!-- GENERATED by scripts/make_fig_timeline.py; do not edit by hand. One column ({W} x {H} pt), 1 user unit = 1 pt.
     Build: python3 scripts/html2pdf.py fig_timeline  ->  figs/fig_timeline.pdf (+ .png preview). -->
<style>
  html, body {{ margin: 0; padding: 0; background: #FFFFFF; }}
  svg {{ display: block; }}
  text {{ font-family: "Liberation Serif", "Nimbus Roman", "Times New Roman", serif; }}
</style>
</head>
<body>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}">
<defs>
  <marker id="ah" viewBox="0 0 6 6" refX="6" refY="3" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
    <path d="M0,0 L6,3 L0,6 z" fill="#000000"/></marker>
  <marker id="ab" viewBox="0 0 6 6" refX="6" refY="3" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
    <path d="M0,0 L6,3 L0,6 z" fill="{TINT_EDGE}"/></marker>
</defs>
"""
    out = os.path.join(REPO, "figs", "src", "fig_timeline.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(o) + "\n</svg>\n</body>\n</html>\n")
    print("wrote", out, f"({W} x {H} pt)")


if __name__ == "__main__":
    main()
