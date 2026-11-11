#!/usr/bin/env python3
"""Figure 10 (Sec. VII-A): speed-up over stock AiM against the logic each design adds over stock AiM, at M = 8.

(a) mobile platform (mm^2 per die), (b) edge server (mm^2 per pseudo-channel). x = dA_mm2, y = S_kernel_M8 (the Fig. 7
GEMM geometric mean at M = 8). CoDe: stock -> D = 1 -> 2 -> 3 -> 4, every point simulated. LP-Spec-style: a dashed
segment from stock to its four ALUs; one to three ALUs are priced but not simulated, so they carry no marker. The
eight-token LP-Spec-style (phone only) is one marker. Faint iso-lines of constant mm^2 per +1x of speed-up are guides.
No shared LP-Spec-style and no P3-LLM-style (brief, 2026-11-11).
Sources (read only): evaluation/dac_2x2/figures/fig_area_speedup.csv (the paper file of rows 114-115, evaluation 8949a24)
and the touched ids stor.* / aps.* (dac_2x2 Sec. 2u), pupow / budget (dac_sd8g3, dac_2x2), dacp_table4 (Table IV areas).
Internal records say CoRe / LP-Spec-like; the paper says CoDe / LP-Spec-style.
Every number Secs. I, III-D and VII-A print from rows 114-115 is asserted below.
Writes figs/src/fig_storage.html; then python3 scripts/html2pdf.py fig_storage -> figs/fig_storage.pdf (+ .png preview).
"""
import csv
import math
import os

from dac_data import EVAL, HBM2_RAW, PHONE_RAW, STYLE, ids
from svgchart import COLUMNWIDTH, FL, FT, I, LW, Fig, Panel, marker, row, width

CODE, GRAY, ISO = STYLE["code"]["color"], "#606060", "#A8A8A8"
STYLE.update({
    "st_code": dict(color=CODE, marker="diamond", label="CoDe, " + I("D") + " = 1 to 4"),
    "st_lp": dict(color=GRAY, marker="tri_up", label="LP-Spec-style, 1 to 4 ALUs", dash="2.4 1.4"),
    "st_lp8": dict(color=GRAY, marker="square", label="Eight-token LP-Spec-style"),
    "st_stock": dict(color="#000000", marker="circle", label="Stock AiM"),
})
ISO_K = {"phone": (0.15, 0.6), "hbm2": (0.1, 0.35)}      # mm^2 per +1x guides (brief)
ISO_AT = {0.6: 1.25, 0.35: 0.62}                          # gentle guides: label below the line at this x


def r(x, n):
    return round(float(x) + 1e-12, n)


def load():
    with open(os.path.join(EVAL, "dac_2x2", "figures", "fig_area_speedup.csv")) as fh:
        rows = list(csv.DictReader(fh))
    d = {}
    for x in rows:
        d[(x["platform"], x["series"], x["point"])] = x
    return d


def checks(d):
    t = ids("dac_2x2")
    s = ids("dac_sd8g3")
    f = lambda p, se, pt, c: float(d[(p, se, pt)][c])   # noqa: E731
    # the figure file equals the ids (design points), so the plotted points are the printed ones
    for p, core in (("phone", "core8"), ("hbm2", "core4")):
        assert abs(f(p, "CoRe", "D4", "dA_mm2") - t[f"aps.{p}.{core}.dA"]) < 1e-12
        assert abs(f(p, "CoRe", "D4", "S_kernel_M8") - t[f"aps.{p}.{core}.kernel_M8.S"]) < 1e-12
        assert abs(f(p, "LP-Spec-like", "A4", "dA_mm2") - t[f"aps.{p}.h2.dA"]) < 1e-12
        assert [d[(p, "LP-Spec-like", a)]["simulated_S"] for a in ("A1", "A2", "A3", "A4")] == ["no", "no", "no", "yes"]
        assert f(p, "LP-Spec-like", "A4", "S_kernel_M8") <= f(p, "CoRe", "D4", "S_kernel_M8") + 1e-12
    # VII-A P1: mm^2 per +1x on GEMMs of M = 8 (kernel): LP-Spec-style 0.608 vs CoDe 0.145 per die, 4.2x;
    # HBM2 0.337 vs 0.107 per pCH, 3.2x; end to end 4.1x and 3.2x
    assert (r(t["aps.phone.h2.kernel_M8.mm2_per_x"], 3), r(t["aps.phone.core8.kernel_M8.mm2_per_x"], 3)) == (0.608, 0.145)
    assert (r(t["aps.hbm2.h2.kernel_M8.mm2_per_x"], 3), r(t["aps.hbm2.core4.kernel_M8.mm2_per_x"], 3)) == (0.337, 0.107)
    assert r(t["aps.phone.h2.kernel_M8.ratio_to_core"], 1) == 4.2 and r(t["aps.hbm2.h2.kernel_M8.ratio_to_core"], 1) == 3.2
    assert r(t["aps.phone.h2.e2e_M8.ratio_to_core"], 1) == 4.1 and r(t["aps.hbm2.h2.e2e_M8.ratio_to_core"], 1) == 3.2
    for p, core in (("phone", "core8"), ("hbm2", "core4")):
        for lv in ("kernel_M8", "e2e_M8"):
            q = t[f"aps.{p}.h2.{lv}.mm2_per_x"] / t[f"aps.{p}.{core}.{lv}.mm2_per_x"]
            assert abs(q - t[f"aps.{p}.h2.{lv}.ratio_to_core"]) < 1e-9
        a = f(p, "CoRe", "D4", "dA_mm2") / (f(p, "CoRe", "D4", "S_kernel_M8") - 1)
        assert abs(a - t[f"aps.{p}.{core}.kernel_M8.mm2_per_x"]) < 1e-12
    # P1: arithmetic 86 % of LP-Spec-style's added logic, storage 91 % of CoDe's (mobile)
    assert round(100 * t["aps.phone.h2.arith_share"]) == 86 and round(100 * t["aps.phone.core8.storage_share"]) == 91
    # P2: the tile 0.457 mm^2 per die for 1.24x; D 1 -> 4 adds 0.002 mm^2, speed-up 4.17x (mobile, GEMMs at M = 8)
    assert r(t["aps.marg.phone.stock_d1.dA"], 3) == 0.457 and r(f("phone", "CoRe", "D1", "S_kernel_M8"), 2) == 1.24
    assert r(t["aps.marg.phone.d1_d4.dA"], 3) == 0.002 and r(t["aps.phone.core8.kernel_M8.S"], 2) == 4.17
    assert t["aps.marg.phone.stock_d1.dA_arith"] == 0 and t["aps.marg.phone.d1_d4.dA_storage"] == 0
    # P2: about 0.54 mm^2 per die per 32-wide ALU, 0.48 of it arithmetic (multipliers and adder trees); the eight-token
    # LP-Spec-style at CoDe's speed costs 4.2x CoDe's mm^2 per +1x
    assert r(t["aps.phone.lp_alu.step_dA.min"], 2) == r(t["aps.phone.lp_alu.step_dA.max"], 2) == 0.54
    assert r(t["aps.phone.lp_alu.step_arith"], 2) == 0.48
    assert r(t["aps.phone.h2a8.kernel_M8.ratio_to_core"], 1) == 4.2
    assert abs(t["aps.phone.h2a8.kernel_M8.S"] - t["aps.phone.core8.kernel_M8.S"]) < 1e-12
    # P2: peak power stays below LP-Spec-style's on both platforms (0.92x / 0.87x are printed in VI-C only)
    assert s["pupow.phone.gate.core8.over_h2"] < 1 and t["pupow.hbm2.gate.core4.over_h2"] < 1
    assert r(s["pupow.phone.gate.core8.over_h2"], 2) == 0.92 and r(t["pupow.hbm2.gate.core4.over_h2"], 2) == 0.87
    # P3: the per-mm^2 lead over LP-Spec-style holds until storage costs 8.3x (mobile) / 17.2x (edge server) our estimate;
    # at 3x, CoDe still returns 1.41x / 1.36x
    assert r(t["stor.phone.be.all.lp"], 1) == 8.3 and r(t["stor.hbm2.be.all.lp"], 1) == 17.2
    assert r(t["stor.phone.all.s3.per_mm2_vs_lp"], 2) == 1.41 and r(t["stor.hbm2.all.s3.per_mm2_vs_lp"], 2) == 1.36
    # III-D: the wider-PU family (our LP-Spec-style model) adds about 1.7 mm^2 per die over stock AiM = Table IV 2.610 - 0.947
    assert r(t["aps.phone.h2.dA"], 1) == 1.7
    t4 = {x["design"]: float(x["logic_mm2"]) for x in csv.DictReader(open(os.path.join(PHONE_RAW, "dacp_table4.csv")))}
    assert abs(t4["h2"] - t4["stock"] - t["aps.phone.h2.dA"]) < 1e-6, t4
    assert (r(t4["h2"], 3), r(t4["stock"], 3)) == (2.610, 0.947)
    # HBM2 per-pCH areas tie to Table IV too
    t4h = {x["design"]: float(x["logic_mm2"]) for x in csv.DictReader(open(os.path.join(HBM2_RAW, "dacp_table4.csv")))}
    assert abs(t4h["h2"] - t4h["stock"] - t["aps.hbm2.h2.dA"]) < 1e-6 and abs(t4h["core4"] - t4h["stock"] - t["aps.hbm2.core4.dA"]) < 1e-6
    print("Secs. I / III-D / VII-A numbers hold: 0.608 / 0.145 (4.2x), 0.337 / 0.107 (3.2x), e2e 4.1x / 3.2x, 86 / 91 %, "
          "0.457 mm2 -> 1.24x, +0.002 mm2 -> 4.17x, 0.54 / 0.48 mm2 per ALU, A8 4.2x, break-even 8.3x / 17.2x "
          "(1.41x / 1.36x at 3x), 1.7 mm2")


def iso(pn, k):
    """The guide y = 1 + x / k, clipped to the box and labelled with k (top edge, or below the line at ISO_AT)."""
    (x0, x1), (y0, y1) = pn.xlim, pn.ylim
    xa, xb = max(x0, 0.0), min(x1, k * (y1 - 1))
    pn.f.line(pn.px(xa), pn.py(1 + xa / k), pn.px(xb), pn.py(1 + xb / k), ISO, 0.5, ' stroke-dasharray="1 1.4"')
    lab = f"{k:g}"
    if k in ISO_AT:
        x = ISO_AT[k]
        pn.f.text(pn.px(x) + 2.0, pn.py(1 + x / k) + FT + 1.5, lab, FT, "start", f' fill="{GRAY}"')
    else:
        pn.f.text(pn.px(xb) + 1.0, pn.py(y1) + FT + 0.5, lab, FT, "start", f' fill="{GRAY}"')


def path(pn, key, pts):
    """A series drawn in the order given (HBM2's D = 3 sits 5e-5 mm^2 left of D = 2: synthesis noise), first point
    unmarked (stock AiM, drawn on its own)."""
    st = STYLE[key]
    xy = [(pn.px(x), pn.py(y)) for x, y in pts]
    rad = [0.0]
    svgs = []
    for x, y in xy[1:]:
        s, rr = marker(x, y, st["marker"], st["color"])
        svgs.append(s)
        rad.append(rr + 0.25)
    rad[0] = 2.15                                    # stock AiM's circle
    for (xa, ya), ra, (xb, yb), rb in zip(xy, rad, xy[1:], rad[1:]):
        dd = math.hypot(xb - xa, yb - ya)
        if dd <= ra + rb + 0.3:
            continue
        ux, uy = (xb - xa) / dd, (yb - ya) / dd
        da = f' stroke-dasharray="{st["dash"]}"' if st.get("dash") else ""
        pn.f.line(xa + ux * ra, ya + uy * ra, xb - ux * rb, yb - uy * rb, st["color"], LW, ' stroke-linecap="butt"' + da)
    pn.f.o.extend(svgs)


def label(pn, x, y, s, dx, dy, anchor="start"):
    pn.f.text(pn.px(x) + dx, pn.py(y) + dy, s, FT, anchor)


def main():
    d = load()
    checks(d)
    H = 150.0
    fig = Fig(COLUMNWIDTH, H)
    top, bottom = 33.0, H - 20.0
    ax = [dict(ylim=(0.5, 4.7), ylog=False, yticks=[1, 2, 3, 4]),
          dict(ylim=(0.5, 4.7), ylog=False, yticks=[1, 2, 3, 4])]
    # legend: two rows
    smp, gp, sp = 13.0, 2.0, 9.0
    fig.legend(["st_code", "st_lp"], 7.5, sample=smp, gap=gp, space=sp)
    w_iso = smp + gp + width("mm² per +1×", FL)
    w2 = sum(smp + gp + width(STYLE[k]["label"], FL) for k in ("st_lp8", "st_stock")) + 2 * sp + w_iso
    xs = (COLUMNWIDTH - w2) / 2
    w_l = sum(smp + gp + width(STYLE[k]["label"], FL) for k in ("st_lp8", "st_stock")) + sp
    fig.legend(["st_lp8", "st_stock"], 18.5, x_center=xs + w_l / 2, sample=smp, gap=gp, space=sp)
    xi = xs + w_l + sp
    fig.line(xi, 18.5 - 2.9, xi + smp, 18.5 - 2.9, ISO, 0.6, ' stroke-dasharray="1 1.4"')
    fig.text(xi + smp + gp, 18.5, "mm² per +1×")
    (xa, wa, la), (xb, wb, lb) = row(fig, ax, top, bottom, gap=6.0)
    spec = {"phone": dict(x0=xa, w=wa, lab=la, xlim=(-0.1, 2.1), xt=[0, 0.5, 1, 1.5, 2],
                          title="(a) Mobile platform", xl="added logic (mm² per die)"),
            "hbm2": dict(x0=xb, w=wb, lab=lb, xlim=(-0.05, 1.05), xt=[0, 0.25, 0.5, 0.75, 1],
                         title="(b) Edge server", xl="added logic (mm² per pCH)")}
    for p, c in spec.items():
        pn = Panel(fig, c["x0"], top, c["w"], bottom - top, c["xlim"], c["xt"], (0.5, 4.7), False, [1, 2, 3, 4],
                   xlog=False)
        pn.frame(c["title"], c["xl"], "speed-up over stock AiM", c["lab"])
        for k in ISO_K[p]:
            iso(pn, k)
        g = lambda se, pt: (float(d[(p, se, pt)]["dA_mm2"]), float(d[(p, se, pt)]["S_kernel_M8"]))   # noqa: E731
        code = [g("CoRe", f"D{i}") for i in range(1, 5)]
        path(pn, "st_lp", [(0.0, 1.0), g("LP-Spec-like", "A4")])
        path(pn, "st_code", [(0.0, 1.0)] + code)
        pn.series("st_stock", [(0.0, 1.0)])
        for i, (x, y) in enumerate(code, 1):
            label(pn, x, y, I("D") + f" = {i}" if i in (1, 4) else f"{i}", 3.8, FT * 0.34)
        x4, y4 = g("LP-Spec-like", "A4")
        label(pn, x4, y4, "4 ALUs", -4.0, FT * 0.34 - 2.0, "end")
        if p == "phone":
            x8, y8 = g("LP-Spec-like-A8", "A8")
            pn.series("st_lp8", [(x8, y8)])
            label(pn, x8, y8, "eight-token", -4.0, FT * 0.34, "end")
        pn.finish()
    fig.write("fig_storage", "scripts/make_fig_storage.py")


if __name__ == "__main__":
    main()
