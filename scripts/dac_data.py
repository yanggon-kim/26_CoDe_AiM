"""Shared loaders for the Sec. III / IV figures and tables (read-only).

Sources (all read only)
  The EV-58 data pack (microarch 4511d75), as collected by evaluation-owner at a254d92 (ids dacp.phone.* in
  evaluation/dac_sd8g3/numbers.md, dacp.hbm2.* in evaluation/dac_2x2/numbers.md): read_pack(<pack file name>) joins the
  per-platform collected copies evaluation/dac_{sd8g3,2x2}/raw/dacp_*.csv back into the pack's file shape.
  EVAL : ../../evaluation (EV-56 layer-energy bands, touched ids, P3-LLM reproduction).
Internal records say CoRe / -like; the paper says CoDe / -style (D-33). Data keys are unchanged (core8, core4, h2, ...).
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WS = os.path.normpath(os.path.join(REPO, "..", ".."))
EVAL = os.path.join(WS, "evaluation")
PHONE_RAW = os.path.join(EVAL, "dac_sd8g3", "raw")
HBM2_RAW = os.path.join(EVAL, "dac_2x2", "raw")
# pack file -> collected copies (phone part, HBM2 part)
COLLECTED = {
    "dac_table4.csv": [(PHONE_RAW, "dacp_table4.csv"), (HBM2_RAW, "dacp_table4.csv")],
    "dac_fig4_area.csv": [(PHONE_RAW, "dacp_fig4.csv"), (HBM2_RAW, "dacp_fig4.csv")],
    "dac_fig5_phone.csv": [(PHONE_RAW, "dacp_fig5.csv")],
    "dac_fig6_hbm2.csv": [(HBM2_RAW, "dacp_fig6.csv")],
    "dac_mech.csv": [(PHONE_RAW, "dacp_mech.csv"), (HBM2_RAW, "dacp_mech.csv")],
    "dac_headline.csv": [(PHONE_RAW, "dacp_head_e2e.csv"), (PHONE_RAW, "dacp_head_xover.csv"),
                         (HBM2_RAW, "dacp_head_bands.csv"), (HBM2_RAW, "dacp_head_xover.csv")],
}

# one hue per design (user, 2026-10-16), shared by Table II and Figs. 2, 5, 6, 7: stock blue, P3-LLM-style orange,
# LP-Spec-style green, CoDe red; the line charts (svgchart.py) draw every series at one thin width and add a hollow
# marker per design (user, 2026-10-17): host circle, stock square, LP-Spec-style triangle, P3-LLM-style inverted
# triangle, CoDe diamond
STYLE = {
    "stock": dict(color="#0072B2", marker="square", label="Stock AiM"),
    "p3": dict(color="#E69F00", marker="tri_down", label="P3-LLM-style"),
    "lpspec": dict(color="#009E73", marker="tri_up", label="LP-Spec-style"),
    "code": dict(color="#E03127", marker="diamond", label="CoDe"),
}
KEY = {"phone": {"stock": "stock", "p3": "h3", "lpspec": "h2", "code": "core8"},
       "hbm2": {"stock": "stock", "p3": "p3_500", "lpspec": "h2", "code": "core4"}}


def read(name, base=None):
    """A pack file name (no base) reads the collected copies; otherwise read base/name."""
    if base is None:
        out = []
        for d, fn in COLLECTED[name]:
            with open(os.path.join(d, fn)) as fh:
                out += list(csv.DictReader(fh))
        return out
    with open(os.path.join(base, name)) as f:
        return list(csv.DictReader(f))


def f(x):
    return float(x) if x not in ("", None) else None


def r3(x):
    return round(float(x) + 1e-12, 3)


def r2(x):
    return round(float(x) + 1e-12, 2)


def rc():
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 8, "font.family": "serif", "mathtext.fontset": "dejavuserif",
                         "axes.labelsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8, "pdf.fonttype": 42})


def frame(ax):
    for s in ax.spines.values():
        s.set_linewidth(0.8)
        s.set_color("black")
    ax.tick_params(which="both", direction="in", top=True, right=True, length=2.5, width=0.6)
    ax.tick_params(which="minor", length=1.5)
    ax.grid(axis="y", which="major", ls=":", lw=0.5, color="#808080")
