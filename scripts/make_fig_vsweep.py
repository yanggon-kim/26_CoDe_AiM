#!/usr/bin/env python3
"""Figure 9 (Sec. VI-D): the tile-size ablation, CoDe's V on both platforms (D = 4, SRAM GB, the committed staging).

(a) q_proj 4096 x 4096 (Llama-2-7B on the mobile platform, Llama-3.1-8B on HBM2) at M = 64, V = 1 ... 64: speed-up over
    stock AiM, and throughput per logic mm^2 over stock AiM's own (speed-up x A_stock / A(V), A_stock = stock AiM's logic
    per die / per pCH with the SRAM GB, dacp_table4.stock, the cvs_area scope). Mobile staging: the V-slice register below V = 8, the three-entry queue from V = 8 (the
    sweep's "fifo" rows, equal to the register at V <= 4); HBM2: the V-slice register.
(b) V = 8 / V = 4 decode-step throughput per logic mm^2 against M = 1 ... 16: mobile = the speculative verify step of
    Llama-2-7B at L = 1024 (queue staging), HBM2 = the batched step, geometric mean over five LLMs (register staging).
Sources (read only; evaluation/dac_2x2/raw, pass hold adopted, microarch 704c409 / evaluation 7589fe7, current files,
never *_pre): cvs_sum / cvs_area / cvs_pa (the V sweep, Sec. 2k), cvm_st_pa (phone V x M step, Sec. 2l), hvm_st_pa
(HBM2 V x M step, Sec. 2m), dacp_table4 (stock area, dac_sd8g3 / dac_2x2 raw), hvm_regret / hvm_st_regret (the minimax table, Sec. 2m-2n), cvm_pa (phone q_proj V x M).
Every number Sec. VI-D prints is asserted below; the shares 21 / 7 %, 18.9 -> 10.4 %, 20.5 us, the
mm^2 values, break-even 1.160x / 1.405x, 96.3 / 77.5 % of peak, 24.5 % and the one-tile 4.6 % are no longer printed
(guards only, 2026-10-30).
Writes figs/src/fig_vsweep.html; then python3 scripts/html2pdf.py fig_vsweep -> figs/fig_vsweep.pdf (+ .png preview).
"""
import csv
import os

from dac_data import HBM2_RAW, PHONE_RAW, STYLE
from svgchart import COLUMNWIDTH, FL, I, Fig, Panel, row, width

STYLE.update({
    "sp_m": dict(color="#505050", marker="diamond", label="Mobile, speed-up"),
    "sp_h": dict(color="#505050", marker="diamond", label="HBM2, speed-up", dash="2.4 1.4"),
    "pa_m": dict(color="#E03127", marker="diamond", label="Mobile, per mm²"),
    "pa_h": dict(color="#E03127", marker="diamond", label="HBM2, per mm²", dash="2.4 1.4"),
})
VS = [1, 2, 4, 8, 16, 32, 64]
D = 4
STAGING = {"phone": "fifo", "hbm2": "register"}       # the sweep's fifo rows = register below V = 8 (Sec. 2k caveat 1)


def rows(name, raw=HBM2_RAW):
    with open(os.path.join(raw, name)) as fh:
        return list(csv.DictReader(fh))


def pct(x):
    return round(100 * x + 1e-9, 1)


def gain_by_v():
    """Panel (a) data and the Gain-by-tile-size / Area-against-speed numbers."""
    s = {(r["platform"], r["V"] or "stock"): r for r in rows("cvs_sum.csv") if r["workload"] == "W2"}
    t = lambda p, v, c="total_ns": float(s[(p, str(v))][c])   # noqa: E731
    # V 1 -> 2 (phone): the stock PU's idle beats appear as "other" at V = 1 and 2 (Sec. 2k ties); idle 72 %, row switch
    # 21 %, refresh 7 % of the saving (= abl.phone.W2.v1_to_v2.*; refresh-fixed phone, Sec. 2p)
    sav = t("phone", 1) - t("phone", 2)
    idle = (t("phone", 1, "other_ns") - t("phone", 2, "other_ns")) / sav
    rsw = (t("phone", 1, "row_switch_ns") - t("phone", 2, "row_switch_ns")) / sav
    ref = (t("phone", 1, "refresh_ns") - t("phone", 2, "refresh_ns")) / sav
    assert (round(100 * idle), round(100 * rsw), round(100 * ref)) == (72, 21, 7), (idle, rsw, ref)
    # V 4 -> 8 (phone): the row-switch commands give 91.6 % of the saving; their share of T 18.9 % -> 10.4 %
    sav = t("phone", 4) - t("phone", 8)
    assert pct((t("phone", 4, "row_switch_ns") - t("phone", 8, "row_switch_ns")) / sav) == 91.6
    assert pct(t("phone", 4, "row_switch_ns") / t("phone", 4)) == 18.9
    assert pct(t("phone", 8, "row_switch_ns") / t("phone", 8)) == 10.4
    # token load stays flat: 20.48-20.55 us at every V on the phone (prints 20.5 us)
    tl = [t("phone", v, "token_load_ns") for v in VS]
    assert (round(min(tl) / 1e3, 1), round(max(tl) / 1e3, 1)) == (20.5, 20.5), tl
    # speed-up endpoints: V = D and V = 64 (phone V = 4 = 3.860498 from the integer cycles, Sec. 2k)
    sp = {p: [t(p, v, "speedup_vs_stock") for v in VS] for p in ("phone", "hbm2")}
    assert [round(sp["phone"][i], 2) for i in (2, 6)] == [3.86, 4.90]
    assert [round(sp["hbm2"][i], 2) for i in (2, 6)] == [3.69, 4.39]
    assert round(sp["phone"][3] / sp["phone"][2], 3) == 1.117 and round(sp["hbm2"][3] / sp["hbm2"][2], 3) == 1.089
    # areas per die / per pCH and the break-even lead (= vmsweep.breakeven.fifo.sram, hvmsweep.breakeven.register.sram)
    ar = {(r["platform"], r["staging_form"], int(r["V"])): r for r in rows("cvs_area.csv")}
    a = {p: [float(ar[(p, STAGING[p], v)]["logic_sram_mm2"]) for v in VS] for p in ("phone", "hbm2")}
    at = {p: [float(ar[(p, STAGING[p], v)]["logic_sram_mm2_total"]) for v in VS] for p in ("phone", "hbm2")}
    assert [round(a["phone"][i], 3) for i in (2, 3)] == [1.212, 1.406]
    assert [round(a["hbm2"][i], 3) for i in (2, 3)] == [0.821, 1.153]
    assert round(a["phone"][3] / a["phone"][2], 3) == 1.160 and round(a["hbm2"][3] / a["hbm2"][2], 3) == 1.405
    assert round(100 * (a["phone"][3] / a["phone"][2] - 1)) == 16 and round(100 * (a["hbm2"][3] / a["hbm2"][2] - 1)) == 40
    # per logic mm^2: argmax at V = D on both platforms; V = 8 keeps 96.3 % / 77.5 % of the peak
    pa = {(r["platform"], int(r["V"])): r for r in rows("cvs_pa.csv")
          if r["workload"] == "W2" and r["gb_form"] == "sram" and r["staging_form"] == STAGING[r["platform"]]}
    for p in ("phone", "hbm2"):
        per = [float(pa[(p, v)]["speedup_per_mm2"]) for v in VS]
        assert VS[per.index(max(per))] == D and pa[(p, D)]["argmax"] == "True"
        for v, x, ttl, sv in zip(VS, per, at[p], sp[p]):
            assert abs(x - sv / ttl) < 1e-5 * x
    assert pct(float(pa[("phone", 8)]["vs_argmax"])) == 96.3 and pct(float(pa[("hbm2", 8)]["vs_argmax"])) == 77.5
    # stock AiM's logic in the cvs_area scope (per die / per pCH, SRAM GB): Table I's stock rows (dacp_table4.stock)
    st = {p: float(next(r for r in rows("dacp_table4.csv", raw) if r["design"] == "stock")["logic_mm2"])
          for p, raw in (("phone", PHONE_RAW), ("hbm2", HBM2_RAW))}
    assert (round(st["phone"], 3), round(st["hbm2"], 3)) == (0.947, 0.520), st
    # plotted: speed-up, and throughput per logic mm^2 over stock AiM's (speed-up x A_stock / A(V))
    out = {}
    for p, k in (("phone", "m"), ("hbm2", "h")):
        out["sp_" + k] = list(zip(VS, sp[p]))
        out["pa_" + k] = [(v, x * st[p] / ar_) for v, x, ar_ in zip(VS, sp[p], a[p])]
    # VI-C prints the peak (V = D) of each per-mm^2 curve
    assert max(out["pa_m"], key=lambda t: t[1])[0] == D and max(out["pa_h"], key=lambda t: t[1])[0] == D
    assert (round(out["pa_m"][2][1], 2), round(out["pa_h"][2][1], 2)) == (3.01, 2.34)
    return out


def robustness():
    """Panel (b) data and the Robustness-across-M numbers."""
    ph = {(int(r["M"]), int(r["V"])): float(r["speedup_per_mm2"]) for r in rows("cvm_st_pa.csv")
          if r["L"] == "1024" and r["staging_form"] == "fifo" and r["gb_form"] == "sram"}
    hb = {(int(r["M"]), int(r["V"])): float(r["speedup_per_mm2"]) for r in rows("hvm_st_pa.csv")
          if r["mode"] == "batch" and r["model"] == "gmean" and r["staging_form"] == "register" and r["gb_form"] == "sram"}
    k2 = {(int(r["M"]), int(r["V"])): float(r["speedup_per_mm2"]) for r in rows("cvm_pa.csv")
          if r["workload"] == "W2" and r["staging_form"] == "fifo" and r["gb_form"] == "sram"}
    Ms = range(1, 17)
    rp = [(m, ph[(m, 8)] / ph[(m, 4)]) for m in Ms]
    rh = [(m, hb[(m, 8)] / hb[(m, 4)]) for m in Ms]
    rk = [(m, k2[(m, 8)] / k2[(m, 4)]) for m in Ms]
    win = [5, 6, 7, 9, 10, 13, 14, 15]
    assert [m for m, x in rp if x > 1] == win and [m for m, x in rk if x > 1] == win
    assert max(x for _, x in rh) < 1 and max(rh, key=lambda t: t[1])[0] == 5
    assert round(rp[4][1], 3) == 1.324 and round(rk[4][1], 3) == 1.416 and round(rh[4][1], 3) == 0.944
    # at M <= 4 both tiles run one pass: the ratio is the area ratio (1 / 1.160, 1 / 1.405)
    assert all(abs(x - rp[0][1]) < 1e-5 for _, x in rp[:4]) and round(1 / rp[0][1], 3) == 1.160 and round(rp[0][1], 3) == 0.862
    assert all(abs(x - rh[0][1]) < 1e-5 for _, x in rh[:4]) and round(1 / rh[0][1], 3) == 1.405
    # worst per-mm^2 loss over M 3-16 against the best of V = 2, 4, 8, 16 at each M (the minimax table, current)
    reg = {}
    for r in rows("hvm_regret.csv") + rows("hvm_st_regret.csv"):
        if r["gb_form"] == "sram" and r["metric"] == "speedup_per_mm2" and r["row_id"].split("/")[-2] == "3-16":
            reg[(r["row_id"].split("/")[0], r["row_id"].split("/")[1], r["staging_form"], int(r["V"]))] = \
                (pct(float(r["worst_loss"])), r["worst_at_M"])
    q = lambda p, w, v: reg[(p, w, STAGING[p], v)][0]   # noqa: E731
    assert (q("phone", "W2", 4), q("phone", "step", 4)) == (29.4, 24.5)
    assert reg[("phone", "W2", "fifo", 4)][1] == "5" and reg[("phone", "step", "fifo", 4)][1] == "5"
    assert q("phone", "W2", 8) == q("phone", "step", 8) == q("phone", "W1", 8) == 13.8
    assert round(100 * (1 - 1 / 1.160), 1) == 13.8               # V = 8's area premium where both run one pass
    # VI-D eval-vsweep-choice: the mobile V = 8 pays its worst loss at M = 3-4 (Sec. VI-B's M = 4 among them)
    assert all(reg[("phone", w, "fifo", 8)][1] in ("3", "4") for w in ("W1", "W2", "step"))
    assert q("phone", "W1", 4) == 4.6                            # the exception: the one-tile kernel prefers V = 4
    hb4 = [q("hbm2", w, 4) for w in ("W1", "W2", "step batch (gmean)")]
    hb8 = [q("hbm2", w, 8) for w in ("W1", "W2", "step batch (gmean)")]
    assert max(hb4) == 11.7 and (min(hb8), max(hb8)) == (28.8, 30.0), (hb4, hb8)
    return {"pa_m": rp, "pa_h": rh}


def main():
    a, b = gain_by_v(), robustness()
    H = 128.0
    fig = Fig(COLUMNWIDTH, H)
    top, bottom = 31.0, H - 19.3
    ax = [dict(ylim=(0, 5.2), ylog=False, yticks=[0, 1, 2, 3, 4, 5]),
          dict(ylim=(0.6, 1.5), ylog=False, yticks=[0.6, 0.8, 1.0, 1.2, 1.4])]
    # legend: two rows in two aligned columns (mobile left, HBM2 right)
    smp, gp, sp = 13.0, 2.0, 10.0
    w = lambda k: smp + gp + width(STYLE[k]["label"], FL)   # noqa: E731
    c0 = max(w("sp_m"), w("pa_m"))
    x0 = (COLUMNWIDTH - (c0 + sp + max(w("sp_h"), w("pa_h")))) / 2
    for y, (km, kh) in ((7.0, ("sp_m", "sp_h")), (17.0, ("pa_m", "pa_h"))):
        fig.legend([km], y, x_center=x0 + w(km) / 2, sample=smp, gap=gp)
        fig.legend([kh], y, x_center=x0 + c0 + sp + w(kh) / 2, sample=smp, gap=gp)
    (xa, wa, la), (xb, wb, lb) = row(fig, ax, top, bottom, gap=5.0)
    # (a) q_proj at M = 64 against V
    pn = Panel(fig, xa, top, wa, bottom - top, (1, 64), [1, 4, 16, 64], ax[0]["ylim"], False, ax[0]["yticks"])
    pn.frame("(a) q_proj, " + I("M") + " = 64", "tile size " + I("V"), "× stock AiM", la)
    x4 = pn.px(D)
    fig.line(x4, top, x4, bottom, sw=0.5, extra=' stroke-dasharray="1 1.5"')
    pn.note(D * 1.12, 0.45, [I("V") + " = " + I("D")], "start")
    for k in ("sp_h", "sp_m", "pa_h", "pa_m"):
        pn.series(k, a[k])
    pn.finish()
    # (b) V = 8 / V = 4 per logic mm^2 of the decode step against M
    pn = Panel(fig, xb, top, wb, bottom - top, (1, 16), [1, 4, 8, 12, 16], ax[1]["ylim"], False, ax[1]["yticks"],
               xlog=False)
    pn.frame("(b) Decode step", "token rows " + I("M"), I("V") + " = 8 ÷ " + I("V") + " = 4, per mm²", lb)
    y1 = pn.py(1.0)
    fig.line(xb, y1, xb + wb, y1, sw=0.5, extra=' stroke-dasharray="1 1.5"')
    pn.note(7.6, 1.40, ["break-even"], "start", to=(11.5, 1.0), attach=(pn.px(11.0), pn.py(1.40) + 2.0))
    for k in ("pa_h", "pa_m"):
        pn.series(k, b[k])
    pn.finish()
    fig.write("fig_vsweep", "scripts/make_fig_vsweep.py")
    print("V sweep: every Sec. VI-C number holds")


if __name__ == "__main__":
    main()
