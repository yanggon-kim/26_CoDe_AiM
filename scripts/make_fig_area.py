#!/usr/bin/env python3
"""Figure 4 (Sec. IV-E): logic area per design, split into arithmetic, control, storage and global buffer.

Reads dac_fig4_area.csv of the EV-58 pack (scripts/dac_data.py). Storage = accumulators + staging (+ the FIFO's
control on the phone) + weight latch. Phone in mm^2 per die (16 banks), server in mm^2 per pseudo-channel (16 banks,
8 PUs). Asserts the totals Table IV prints. Writes figs/fig_area.pdf (vector) and, with --png, a preview.
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from dac_data import KEY, REPO, STYLE, f, frame, r3, rc, read  # noqa: E402

PARTS = [("arithmetic", ("arithmetic",), "#404040"), ("control", ("control",), "#8C8C8C"),
         ("storage", ("accumulators", "staging", "staging_fifo_control", "weight_latch"), "#D9D9D9"),
         ("global buffer", ("global_buffer",), "#FFFFFF")]
ORDER = ["stock", "p3", "lpspec", "code"]
TOTAL = {"phone": {"stock": 0.947, "p3": 1.050, "lpspec": 2.610, "code": 1.406},
         "hbm2": {"stock": 0.520, "p3": 0.617, "lpspec": 1.469, "code": 0.821}}


def load():
    out = {}
    for r in read("dac_fig4_area.csv"):
        out.setdefault((r["substrate"], r["design"]), {})[r["component"]] = f(r["mm2"])
    for sub in ("phone", "hbm2"):
        for d in ORDER:
            parts = out[(sub, KEY[sub][d])]
            assert r3(sum(parts.values())) == TOTAL[sub][d], (sub, d)
    return out


def main():
    data = load()
    rc()
    fig, axs = plt.subplots(1, 2, figsize=(3.45, 1.55))
    for ax, sub, title, xmax in ((axs[0], "phone", "(a) Mobile, per die", 2.8),
                                 (axs[1], "hbm2", "(b) Server, per pCH", 1.6)):
        for i, d in enumerate(ORDER):
            y = len(ORDER) - 1 - i
            parts = data[(sub, KEY[sub][d])]
            x = 0.0
            for _, comps, col in PARTS:
                w = sum(parts[c] for c in comps if c in parts)
                ax.barh(y, w, left=x, height=0.62, color=col, edgecolor="black", lw=0.5, zorder=3)
                x += w
            if d == "code":
                ax.barh(y, x, height=0.62, fill=False, edgecolor=STYLE["code"]["color"], lw=1.2, zorder=4)
        ax.set_yticks(range(len(ORDER)))
        labs = [STYLE[d]["label"] for d in reversed(ORDER)]
        ax.set_yticklabels(labs if sub == "phone" else [""] * len(ORDER))
        for t, d in zip(ax.get_yticklabels(), reversed(ORDER)):
            t.set_color(STYLE[d]["color"] if d == "code" else "black")
            if d == "code":
                t.set_fontweight("bold")
        ax.set_xlim(0, xmax)
        ax.set_ylim(-0.6, len(ORDER) - 0.4)
        ax.set_title(title, fontsize=8, pad=3)
        ax.set_xlabel("logic area (mm$^2$)", labelpad=1)
        frame(ax)
        ax.grid(False)
        ax.tick_params(axis="y", length=0)
    handles = [Patch(facecolor=c, edgecolor="black", lw=0.5, label=n) for n, _, c in PARTS]
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False, fontsize=7.5, handlelength=1.2,
               columnspacing=0.9, handletextpad=0.4, bbox_to_anchor=(0.56, 1.03))
    fig.tight_layout(rect=(0, 0, 1, 0.86), w_pad=0.3)
    out = os.path.join(REPO, "figs", "fig_area.pdf")
    fig.savefig(out)
    if "--png" in sys.argv:
        fig.savefig(out.replace(".pdf", ".png"), dpi=220)
    print("wrote", out)


if __name__ == "__main__":
    main()
