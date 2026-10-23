#!/usr/bin/env python3
"""Figure 2 (Sec. III-A): skinny-GEMM roofline, (a) phone on LPDDR5-6400 and (b) edge server on HBM2, at the column width.

The per-logic-mm^2 panels were cut in the 2026-10-18 trim (Fig. 6(b) plots the mobile GEMM per logic mm^2 from the
EV-58 pack); their ceilings stay asserted below because Sec. III prints them (314 / 697, 390 / 830, 583 / 1,247).

Reads the EV-57 rows collected by evaluation-owner (never microarch directly):
  phone : ../../../evaluation/dac_sd8g3/raw/ev57_{ceilings,host,summary}.csv  (platform = phone)
  HBM2  : ../../../evaluation/dac_2x2/raw/ev57_{ceilings,host,summary}.csv    (platform = hbm2)
Every value printed in the paper text or caption is asserted against the collected value below.
Plotted points (user, 2026-10-17): M = 1, 2, 4, ..., 64 for the PIM designs, the host roof also at 128 and 256 with
its ridge as an unmarked vertex (the roof is exact between them); the text's crossovers come from the full M grid.
Writes figs/src/fig_roofline.html (inline SVG at the column width, scripts/svgchart.py); then
  python3 scripts/html2pdf.py fig_roofline  ->  figs/fig_roofline.pdf (+ .png preview).

Run from anywhere:  python3 scripts/make_fig_roofline.py
"""
import csv
import os

from svgchart import COLUMNWIDTH, FL, I, Fig, Panel, row

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
EVAL = os.path.normpath(os.path.join(REPO, "..", "..", "evaluation"))
TOPIC = {"phone": os.path.join(EVAL, "dac_sd8g3", "raw"), "hbm2": os.path.join(EVAL, "dac_2x2", "raw")}


def rows(platform, name):
    with open(os.path.join(TOPIC[platform], name + ".csv")) as f:
        return [r for r in csv.DictReader(f) if r["platform"] == platform]


# design keys per platform, in legend order (wider-PU family first); CoDe is the paper's design. Second item: the
# palette key in dac_data.STYLE (colour + marker shared with Figs. 6, 7 and Table II). DESIGNS lists every design whose
# ceiling the text or Table II prints (asserted below); PLOTTED lists the lines each panel draws (user, 2026-10-18):
# stock, the platform's own rival and CoDe (LP-Spec-style on the mobile platform, P3-LLM-style on the edge server).
DESIGNS = {
    "phone": [("stock", "stock"), ("h2", "lpspec"), ("h3", "p3"), ("core8", "code")],
    "hbm2": [("stock", "stock"), ("h2", "lpspec"), ("p3_500", "p3"), ("core4", "code")],
}
PLOTTED = {"phone": ("stock", "h2", "core8"), "hbm2": ("stock", "p3_500", "core4")}
HOST_ROW = {"phone": "npu42", "hbm2": "peak"}
POW2 = [1, 2, 4, 8, 16, 32, 64]

# ---- frozen values the text and Table II print (asserted against the collected rows) ----
# absolute ceilings back the prose's "2x" / "4x" ceiling (III-A); per-mm^2 ceilings are Table II's rows
EXPECT = {
    ("phone", "ceil"): {"stock": 819, "h3": 1638, "h2": 3277, "core8": 3277},
    ("phone", "mm2"): {"stock": 216, "h3": 390, "h2": 314, "core8": 583},
    ("hbm2", "ceil"): {"stock": 4096, "p3_500": 8192, "h2": 16384, "core4": 16384},
    ("hbm2", "mm2"): {"stock": 492, "p3_500": 830, "h2": 697, "core4": 1247},
}


def load(platform):
    ceil = {r["design"]: r for r in rows(platform, "ev57_ceilings")}
    host = {r["row_id"]: r for r in rows(platform, "ev57_host")}[HOST_ROW[platform]]
    summ = {}
    for r in rows(platform, "ev57_summary"):
        summ.setdefault(r["design"], []).append(r)
    for d in summ:
        summ[d].sort(key=lambda r: int(r["M"]))
    for d, _ in DESIGNS[platform]:
        assert round(float(ceil[d]["peak_GOPS"])) == EXPECT[(platform, "ceil")][d], (platform, d)
        assert round(float(ceil[d]["peak_GOPS_per_mm2"])) == EXPECT[(platform, "mm2")][d], (platform, d)
    return ceil, host, summ


def checks():
    """Values quoted in Sec. I / III that come from these files (beyond the ceilings above)."""
    pc, ph, _ = load("phone")
    hc, hh, _ = load("hbm2")
    assert abs(float(ph["ridge_M"]) - 142.857) < 1e-3          # NPU ridge M ~ 143 (x.ev56.npu.ridge_M 142.9)
    assert float(ph["GBps"]) == 42.0 and float(ph["TOPS"]) == 12.0
    assert float(pc["core8"]["internal_GBps"]) == 409.6
    assert abs(409.6 / 42.0 - 9.752) < 1e-3                     # ev57.phone.ceiling_over_npu_roof_M1 = 9.752
    assert float(hh["GBps"]) == 256.0 and float(hc["core4"]["internal_GBps"]) == 1024.0  # 4.000x
    assert abs(float(hh["ridge_M"]) - 128.0) < 1e-9
    r = float(pc["core8"]["peak_GOPS_per_mm2"]) / float(pc["h2"]["peak_GOPS_per_mm2"])
    assert abs(r - 1.857) < 1e-3                                # ev57.phone.core8_over_h2.ceiling_per_mm2
    for c, (s, p3, lp, co) in ((pc, ("stock", "h3", "h2", "core8")), (hc, ("stock", "p3_500", "h2", "core4"))):
        g = {d: float(c[d]["peak_GOPS"]) for d in (s, p3, lp, co)}
        assert (g[p3] / g[s], g[lp] / g[s], g[co] / g[s]) == (2.0, 4.0, 4.0), g   # "2x" / "4x" ceiling (III-A)
    # whole-decode-step crossovers quoted in Sec. I / III-A
    # only each platform's own pairing is quoted (stock, rival, CoDe); the off-pair crossovers left the text with
    # the off-pair lines of the figure (user, 2026-10-18)
    hb = {r["design"]: r["wins_up_to_M"] for r in rows("hbm2", "ev57_crossover") if r["row_id"].startswith("batch/")}
    assert (hb["stock"], hb["p3_500"], hb["core4"]) == ("2-3", "4-6", "8-12"), hb
    # phone verify step vs the NPU at 42 GB/s: EV-56 as collected (dac_sd8g3 touched.csv x.ev56.xover.npu42.*)
    with open(os.path.join(EVAL, "dac_sd8g3", "touched.csv")) as f:
        tv = {r["id"]: float(r["value"]) for r in csv.DictReader(f)}
    got = {d: (tv[f"x.ev56.xover.npu42.{d}.grid_min"], tv[f"x.ev56.xover.npu42.{d}.grid_max"])
           for d in ("stock", "h2", "core8")}
    assert got == {"stock": (6, 7), "h2": (24, 24), "core8": (24, 28)}, got
    print("checks: all frozen values hold")


def host_line(host, ms):
    gbps, tops, opb = float(host["GBps"]), float(host["TOPS"]), float(host["ops_per_weight_byte_per_row"])
    return [min(gbps * opb * m, tops * 1e3) for m in ms]


# panel: platform, title, x range, y range (log)
SPEC = [("phone", "(a) Mobile, LPDDR5-6400", 256, (60, 2.0e4)),
        ("hbm2", "(b) Server, HBM2", 256, (4.0e2, 2.0e5))]


def main():
    checks()
    H = 128.0
    fig = Fig(COLUMNWIDTH, H)
    top, bottom = 31.0, H - 19.3
    lay = row(fig, [dict(ylim=s[3], ylog=True) for s in SPEC], top, bottom, right=5.0, gap=5.0)
    # two legend rows: the shared lines, then each panel's rival (a mobile, b server)
    fig.legend(["host", "stock", "code"], 7.0, sample=13.0, gap=2.0, space=6.0)
    fig.legend(["lpspec", "p3"], 17.0, sample=13.0, gap=2.0, space=6.0,
               labels={"lpspec": "LP-Spec-style (a)", "p3": "P3-LLM-style (b)"})
    for (x0, w, ylx), (p, title, xm, ylim) in zip(lay, SPEC):
        _, host, summ = load(p)
        xt = [t for t in (1, 4, 16, 64, 256) if t <= xm]
        pn = Panel(fig, x0, top, w, bottom - top, (1, xm), xt, ylim, True)
        pn.frame(title, "token rows " + I("M"), "GOPS", ylx)
        ms = POW2 + [128, 256]
        ridge = float(host["ridge_M"])
        assert abs(host_line(host, [ridge])[0] - float(host["TOPS"]) * 1e3) < 1e-6 * float(host["TOPS"]) * 1e3
        pn.series("host", list(zip(ms, host_line(host, ms))), knees=[(ridge, float(host["TOPS"]) * 1e3)])
        # CoDe first (beneath), so the rival's hollow markers stay visible where the two lines meet
        for d, key in sorted([t for t in DESIGNS[p] if t[0] in PLOTTED[p]], key=lambda t: t[1] != "code"):
            pts = [(int(r["M"]), float(r["GOPS_gmean"])) for r in summ[d] if int(r["M"]) in POW2]
            assert [m for m, _ in pts] == POW2, (p, d)
            pn.series(key, pts)
        rm = round(float(host["ridge_M"]))
        tx, ty = (100, 150) if p == "phone" else (95, 1000)
        pn.note(tx, ty, ["NPU ridge", I("M") + f" = {rm}"], "end", to=(float(host["ridge_M"]), float(host["TOPS"]) * 1e3),
                attach=(pn.px(tx) + 1.5, pn.py(ty) - FL * 0.3))
        pn.finish()
    fig.write("fig_roofline", "scripts/make_fig_roofline.py")


if __name__ == "__main__":
    main()
