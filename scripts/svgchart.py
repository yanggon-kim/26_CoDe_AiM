"""Line charts as inline SVG at final size (Figs. 2, 6, 7), shared by make_fig_{roofline,phone,hbm2}.py.

Style (user, 2026-10-17; BTS ISCA'22 Fig. 1 and Centaur ISCA'20 Fig. 7(b) as style references only): every series one
thin solid line (LW pt) through small hollow markers at its data points, joined by straight segments that stop at the
marker outline; series told apart by colour plus marker shape (STYLE in dac_data.py, the palette Table II and Fig. 5
share); light gray thin gridlines at the major ticks; a thin black axis box; one legend row of line + marker samples
on top, shared by all panels. Text in Liberation Serif (TrueType, so Chrome embeds no Type 3 font) at 8-8.5 pt.
Units: 1 SVG user unit = 1 pt (1/72 in). \\textwidth = 516 TeX pt = 514 pt; \\columnwidth = 252 TeX pt = 251 pt.
Each figure script calls write_html(); scripts/html2pdf.py turns figs/src/<name>.html into figs/<name>.pdf + .png.
"""
import math
import os
import re

from PIL import ImageFont

from dac_data import REPO, STYLE

TEXTWIDTH, COLUMNWIDTH = 514.0, 251.0
FT, FL = 8.0, 8.5             # tick labels; axis labels, panel titles, legend, notes
LW = 0.75                     # every series line and marker outline
BOX_LW, GRID_LW, TICK_LW = 0.6, 0.4, 0.5
GRID = "#D0D0D0"
FONT = "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"
FONT_I = "/usr/share/fonts/truetype/liberation2/LiberationSerif-Italic.ttf"
HOST = dict(color="#000000", marker="circle", label="Host NPU")
SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_FONTS = {}


def width(markup, size):
    """Rendered width (pt) of a label in Liberation Serif; <tspan font-style="italic"> runs measured in italic."""
    total = 0.0
    for italic, run in re.findall(r'(<tspan font-style="italic">)?([^<]*)(?:</tspan>)?', markup):
        if not run:
            continue
        path = FONT_I if italic else FONT
        if path not in _FONTS:
            _FONTS[path] = ImageFont.truetype(path, 100)
        total += _FONTS[path].getlength(run.replace("&amp;", "&")) * size / 100
    return total


def I(s):
    return f'<tspan font-style="italic">{s}</tspan>'


def style(key):
    """key: 'host' or a STYLE key (stock / lpspec / p3 / code)."""
    return HOST if key == "host" else STYLE[key]


def dash(st):
    """Optional stroke-dasharray of a series style (a "dash" entry, e.g. "2.2 1.2"); solid by default."""
    return f' stroke-dasharray="{st["dash"]}"' if st.get("dash") else ""


def marker(cx, cy, shape, color):
    """Hollow marker; returns (svg, radius used to stop the joining segments)."""
    a = f'fill="none" stroke="{color}" stroke-width="{LW}"'
    if shape == "circle":
        r = 1.9
        return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" {a}/>', r
    if shape == "square":
        h = 1.7
        return f'<rect x="{cx - h:.2f}" y="{cy - h:.2f}" width="{2 * h}" height="{2 * h}" {a}/>', h * 1.15
    if shape in ("tri_up", "tri_down"):
        R, s = 2.45, (-1 if shape == "tri_up" else 1)
        pts = [(cx, cy + s * R), (cx - R * 0.866, cy - s * R / 2), (cx + R * 0.866, cy - s * R / 2)]
        return f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x, y in pts)}" {a}/>', R * 0.75
    if shape == "diamond":
        R = 2.4
        pts = [(cx, cy - R), (cx + R, cy), (cx, cy + R), (cx - R, cy)]
        return f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x, y in pts)}" {a}/>', R * 0.85
    raise ValueError(shape)


class Fig:
    def __init__(self, W, H):
        self.W, self.H, self.o = W, H, []

    def text(self, x, y, s, size=FL, anchor="start", extra=""):
        self.o.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}"{extra}>{s}</text>')

    def line(self, x1, y1, x2, y2, color="#000000", sw=LW, extra=""):
        self.o.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" '
                      f'stroke-width="{sw}"{extra}/>')

    def legend(self, keys, y, x_center=None, sample=16.0, gap=3.0, space=11.0, labels=None):
        """One row of line + marker samples, centred on x_center; keys in the order given."""
        labels = labels or {}
        items = [(k, labels.get(k, style(k)["label"])) for k in keys]
        tot = sum(sample + gap + width(lab, FL) for _, lab in items) + space * (len(items) - 1)
        x = (self.W / 2 if x_center is None else x_center) - tot / 2
        for k, lab in items:
            st = style(k)
            svg, r = marker(x + sample / 2, y - 2.9, st["marker"], st["color"])
            self.line(x, y - 2.9, x + sample / 2 - r, y - 2.9, st["color"], extra=dash(st))
            self.line(x + sample / 2 + r, y - 2.9, x + sample, y - 2.9, st["color"], extra=dash(st))
            self.o.append(svg)
            self.text(x + sample + gap, y, lab)
            x += sample + gap + width(lab, FL) + space
        return tot

    def write(self, name, note):
        W, H = self.W, self.H
        head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{name}</title>
<!-- GENERATED by {note}; do not edit by hand. {W:g} x {H:g} pt, 1 user unit = 1 pt.
     Build: python3 scripts/html2pdf.py {name}  ->  figs/{name}.pdf (+ .png preview). -->
<style>
  html, body {{ margin: 0; padding: 0; background: #FFFFFF; }}
  svg {{ display: block; }}
  text {{ font-family: "Liberation Serif", "Times New Roman", serif; fill: #000000; }}
</style>
</head>
<body>
<svg xmlns="http://www.w3.org/2000/svg" width="{W:g}pt" height="{H:g}pt" viewBox="0 0 {W:g} {H:g}">
"""
        out = os.path.join(REPO, "figs", "src", name + ".html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(head + "\n".join(self.o) + "\n</svg>\n</body>\n</html>\n")
        print("wrote", out, f"({W:g} x {H:g} pt)")


def log_ticks(lo, hi):
    return [10 ** k for k in range(math.ceil(math.log10(lo) - 1e-9), math.floor(math.log10(hi) + 1e-9) + 1)]


def ylabels_width(ticks, ylog):
    return max(width(fmt_y(t, ylog), FT) for t in ticks)


def fmt_y(t, ylog):
    if ylog:
        return "10" + str(round(math.log10(t))).translate(SUP)
    return f"{t:g}"


class Panel:
    """One plot box: x log2 (M), y log10 or linear. x0, y0 = top-left corner of the box."""

    def __init__(self, fig, x0, y0, w, h, xlim, xticks, ylim, ylog, yticks=None, xlog=True):
        self.f, self.x0, self.y0, self.w, self.h = fig, x0, y0, w, h
        self.xlog = xlog
        self.xlim, self.xticks, self.ylim, self.ylog = xlim, xticks, ylim, ylog
        self.yticks = yticks if yticks is not None else (log_ticks(*ylim) if ylog else None)

    def px(self, x):
        if not self.xlog:
            a, b = self.xlim
            return self.x0 + (x - a) / (b - a) * self.w
        a, b = (math.log2(v) for v in self.xlim)
        return self.x0 + (math.log2(x) - a) / (b - a) * self.w

    def py(self, y):
        if self.ylog:
            a, b = (math.log10(v) for v in self.ylim)
            t = (math.log10(y) - a) / (b - a)
        else:
            a, b = self.ylim
            t = (y - a) / (b - a)
        return self.y0 + self.h - t * self.h

    def frame(self, title, xlabel, ylabel, ylab_x):
        f, x0, y0, w, h = self.f, self.x0, self.y0, self.w, self.h
        for t in self.xticks:            # gridlines first, beneath the data
            if self.xlim[0] < t < self.xlim[1]:
                f.line(self.px(t), y0, self.px(t), y0 + h, GRID, GRID_LW)
        for t in self.yticks:
            if self.ylim[0] < t < self.ylim[1]:
                f.line(x0, self.py(t), x0 + w, self.py(t), GRID, GRID_LW)
        self._box = (title, xlabel, ylabel, ylab_x)

    def finish(self):
        """Axis box, ticks and labels, drawn over the data."""
        title, xlabel, ylabel, ylab_x = self._box
        f, x0, y0, w, h = self.f, self.x0, self.y0, self.w, self.h
        for t in self.xticks:
            x = self.px(t)
            f.line(x, y0 + h, x, y0 + h - 2.5, sw=TICK_LW)
            f.line(x, y0, x, y0 + 2.5, sw=TICK_LW)
            f.text(x, y0 + h + FT + 1.0, f"{t:g}", FT, "middle")
        for t in self.yticks:
            y = self.py(t)
            f.line(x0, y, x0 + 2.5, y, sw=TICK_LW)
            f.line(x0 + w, y, x0 + w - 2.5, y, sw=TICK_LW)
            f.text(x0 - 2.0, y + FT * 0.34, fmt_y(t, self.ylog), FT, "end")
        if self.ylog:                    # minor ticks at 2..9 x each decade
            k0 = math.floor(math.log10(self.ylim[0]))
            for k in range(k0, math.ceil(math.log10(self.ylim[1]))):
                for s in range(2, 10):
                    v = s * 10 ** k
                    if self.ylim[0] < v < self.ylim[1]:
                        y = self.py(v)
                        f.line(x0, y, x0 + 1.5, y, sw=TICK_LW)
                        f.line(x0 + w, y, x0 + w - 1.5, y, sw=TICK_LW)
        f.o.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{w:.2f}" height="{h:.2f}" fill="none" stroke="#000000" '
                   f'stroke-width="{BOX_LW}"/>')
        f.text(x0 + w / 2, y0 - 3.0, title, FL, "middle")
        f.text(x0 + w / 2, y0 + h + FT + 1.0 + FL + 0.5, xlabel, FL, "middle")
        yc = y0 + h / 2
        f.text(ylab_x, yc, ylabel, FL, "middle", f' transform="rotate(-90 {ylab_x:.2f} {yc:.2f})"')

    def series(self, key, pts, knees=()):
        """pts: [(M, value)] each drawn with a marker; knees: extra unmarked vertices (an analytic roof's ridge)."""
        st = style(key)
        verts = sorted([(m, v, True) for m, v in pts] + [(m, v, False) for m, v in knees])
        xy = [(self.px(m), self.py(v), mk) for m, v, mk in verts]
        svgs, radii = [], []
        for x, y, mk in xy:
            if mk:
                s, r = marker(x, y, st["marker"], st["color"])
                svgs.append(s)
                radii.append(r + 0.25)
            else:
                radii.append(0.0)
        for (xa, ya, _), ra, (xb, yb, _), rb in zip(xy, radii, xy[1:], radii[1:]):
            d = math.hypot(xb - xa, yb - ya)
            if d <= ra + rb + 0.3:
                continue
            ux, uy = (xb - xa) / d, (yb - ya) / d
            self.f.line(xa + ux * ra, ya + uy * ra, xb - ux * rb, yb - uy * rb, st["color"], LW,
                        ' stroke-linecap="butt"' + dash(st))
        self.f.o.extend(svgs)

    def note(self, x, y, lines, anchor="start", to=None, attach=None):
        """Text lines at data (x, y) with an optional leader from attach (pt offset) to data point `to`."""
        f = self.f
        px, py = self.px(x), self.py(y)
        if to is not None:
            ax, ay = attach if attach else (px, py)
            f.line(ax, ay, self.px(to[0]), self.py(to[1]), sw=0.5)
        for i, s in enumerate(lines):
            wd = width(s, FL)
            xl = px - (wd if anchor == "end" else 0)
            f.o.append(f'<rect x="{xl - 0.8:.2f}" y="{py + i * (FL + 1) - FL * 0.78:.2f}" width="{wd + 1.6:.2f}" '
                       f'height="{FL + 0.6:.2f}" fill="#FFFFFF"/>')
            f.text(px, py + i * (FL + 1), s, FL, anchor)


def row(fig, specs, top, bottom, left=0.5, right=0.5, gap=4.0):
    """Lay panels side by side. specs: dicts with ylim, ylog, yticks (or None). Returns [(x0, w, ylab_x)].

    Each panel's left decoration = rotated y label (FL) + its widest tick label; the plot boxes share the rest."""
    deco = []
    for s in specs:
        ticks = s.get("yticks") or log_ticks(*s["ylim"])
        deco.append(FL + 1.5 + ylabels_width(ticks, s["ylog"]) + 2.0)
    free = fig.W - left - right - sum(deco) - gap * (len(specs) - 1) - 3.0   # 3 pt: last x tick label overhang
    w = free / len(specs)
    out, x = [], left
    for d in deco:
        out.append((x + d, w, x + FL * 0.75))
        x += d + w + gap
    return out


def lin_ticks(vmax, n=(2, 4)):
    """Ticks 0, step, ... for a linear axis from 0: the step (1, 2, 2.5, 5 x 10^k) giving n[0]..n[1] steps to vmax."""
    k = 10 ** math.floor(math.log10(vmax))
    for s in (0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10):
        step = s * k
        if n[0] <= vmax / step <= n[1]:
            break
    top = vmax * 1.08
    return (0, top), [step * i for i in range(int(top / step + 1e-9) + 1)]


def loglerp(pts, m):
    """Value of the drawn (straight on log-log axes) segment at M = m between two plotted points."""
    (m0, v0), (m1, v1) = [(a, b) for a, b in pts if a <= m][-1], [(a, b) for a, b in pts if a >= m][0]
    if m0 == m1:
        return v0
    t = (math.log2(m) - math.log2(m0)) / (math.log2(m1) - math.log2(m0))
    return v0 * (v1 / v0) ** t
