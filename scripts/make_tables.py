#!/usr/bin/env python3
"""Table I (Sec. V: design parameters, logic area and ungated peak power) and every Sec. IV / V / VI number the prose
prints, asserted. The 2026-10-18 trim merged the former peak-power table into Table I (its Total column; the Staging
column left the table, its values stay asserted) and cut the former command table (its M = 8 values that VI-A / VI-B
print stay asserted in mech_checks()).

Reads the EV-58 data pack as collected (evaluation a254d92, dacp ids; scripts/dac_data.py) and EV-56's bands (EVAL); every
energy and power number comes from the synthesised-PU model pupow (microarch 6074fea, collected at evaluation 88dad76: raw
pupow_*.csv and touched pupow.* ids; the pack's energy columns are the K_E reserve). Writes tables/tab_params.tex
(the configuration table, tab:params: a platform block from platform_block() above the design block of table4());
the prose numbers are asserted in each function.
Phone numbers since the JEDEC refresh fix (rfadopt, microarch fd39875, evaluation c2ad6f9: dac_sd8g3 Sec. 2g, dac_2x2
Sec. 2p); the phone umac constants are in the factor form (t_row 87.73 ns, rho 0.070) like HBM2.
The useful-MAC table (Sec. III-B, tab:umac) and every U / U_MAC / f_MAC / t_fix / t_tok number of Secs. III and VI come
from the umac paper form (microarch 8cef09a, collected at evaluation 0c20b6f, dac_2x2 Sec. 2h): the table source
evaluation/dac_2x2/figures/tab_umac_paper.csv (ids umacp.<p>/<d>/<M>.*), raw/umacp_const.csv (umacp_const.*) and the
touched ids umac.paper.* / umac.p3t.* / umac.<p>.h2.U_per_mult.*; the table prints SIMULATED values (user, 2026-10-19).
The stock faster-PU result of III-B (cycle-identical, time / M spread) is read from microarch/04_data/d1/stock_cmd
(refresh-fixed since microarch fd39875; = evaluation dac_2x2 raw/stockcmd_checks.csv, id stockcmd.phone.time_per_M_maxrel), the source of the cut Fig. stockcmd (its generator was retired with the figure).
The sources-of-gain table (Sec. VI-B, tab:umac_src) and the III-B row-switch numbers come from umac_src (microarch d59e4a2,
collected at evaluation 4ffbc7f, dac_2x2 Sec. 2i; D-35).
Run:  python3 scripts/make_tables.py
"""
import os

from dac_data import EVAL, REPO, WS, f, r2, r3, read

PHONE = [("stock", "Stock AiM"), ("h3", "P3-LLM-style"), ("h2", "LP-Spec-style"), ("core8", "CoDe")]
HBM2 = [("stock", "Stock AiM"), ("p3_500", "P3-LLM-style"), ("h2", "LP-Spec-style"), ("core4", "CoDe")]


def platform_block():
    """Platform block of the configuration table (tab:params), one row per platform value the paper uses. Every value
    is read from a collected evaluation input (dac_sd8g3 / dac_2x2 raw), or is a cited spec value (cite in the cell), or
    is labelled as a simulator preset / [assumption] as the prose had it. Row size: the collected kernel labels (cvs_sum.csv)
    give 64 columns of 32 B in one LPDDR5 row and in two HBM2 rows; the cells cite the JEDEC page sizes."""
    sraw, hraw = os.path.join(EVAL, "dac_sd8g3", "raw"), os.path.join(EVAL, "dac_2x2", "raw")
    host = {"phone": {r["row_id"]: r for r in read("ev57_host.csv", sraw)}["npu42"],
            "hbm2": {r["row_id"]: r for r in read("ev57_host.csv", hraw)}["peak"]}
    assert (f(host["phone"]["TOPS"]), f(host["phone"]["GBps"])) == (12.0, 42.0)
    assert (round(f(host["hbm2"]["TOPS"])), f(host["hbm2"]["GBps"])) == (131, 256.0)
    ceil = {"phone": {r["row_id"]: r for r in read("ev57_ceilings.csv", sraw)}["core8"],
            "hbm2": {r["row_id"]: r for r in read("ev57_ceilings.csv", hraw)}["core4"]}
    assert f(ceil["phone"]["internal_GBps"]) == 409.6 and f(ceil["hbm2"]["internal_GBps"]) == 1024.0
    mi = {r["row_id"]: r["value"] for r in read("ev56_mech_inputs.csv", sraw)}
    assert "x64 LPDDR5-6400 = 4 x16 dies, 16 banks each; 51.2 GB/s pins; 409.6 GB/s internal" in mi["platform"]
    assert f(mi["tCK_CA"]) == 1.25 and mi["A1"] == "5 ns all-bank column"            # CK = 6400 / 8 MHz; [A1]
    assert "tCCD_S = 2 tCK = 2.5 ns" in mi["A-SD4"]
    a0 = {r["row_id"]: r["value"] for r in read("dacp_inputs.csv", hraw)}["A0 - A1"]
    assert "HBM2 1 ns cycle" in a0
    setup = {r["row_id"]: r for r in read("dac2x2_setup.csv", hraw)}
    assert setup["memory - column"]["hbm2"].startswith("HBM2 2.0 Gb/s, 16 pCH, one PU per 2 banks")
    t4 = {(r["substrate"][:5], r["design"]): r for r in read("dac_table4.csv")}
    assert f(t4[("phone", "core8")]["PUs_per_bank"]) == 1 and f(t4[("serve", "core4")]["PUs_per_bank"]) == 0.5
    assert t4[("serve", "core4")]["logic_mm2_unit"] == "per pCH (16 banks, 8 PUs)"
    assert t4[("phone", "core8")]["logic_mm2_unit"] == "per die (16 banks)"
    # mobile refresh [A-REF1]: tRFCab 280 ns as the collected trace times it; tREFI 3.906 us from the topic's context
    ref = [r for r in read("utrace_run_core8_gbfill.csv", hraw) if r["cmd"] == "REFab"]
    assert ref and all(f(r["gap_next_ns"]) == 280.0 and "A-REF1" in r["rule"] for r in ref)
    with open(os.path.join(EVAL, "dac_sd8g3", "context.md")) as fh:
        assert "tREFI 3.906 µs, tRFCab 280 ns `[A-REF1]`" in fh.read()
    lab = {r["row_id"]: r["workload_label"] for r in read("cvs_sum.csv", hraw)}
    assert "one row per bank (K 2048 INT8 = 64 columns" in lab["phone/W1/stock"]                  # 64 x 32 B = 2 KB
    assert "64 columns over two 1 KB rows" in lab["hbm2/W1/stock"]                                # 2 x 32 x 32 B
    assert 64 * 32 == 2048 and 2 * 32 * 32 == 2048
    rows = [
        (r"Host NPU", r"Snapdragon 8 Gen 3~\cite{sd8g3}", r"P3-LLM's~\cite{p3llm}"),
        (r"NPU TOPS, GB/s", r"12, 42", r"131, 256"),
        (r"DRAM", r"x64 LPDDR5-6400", r"HBM2, 2.0\,Gb/s"),
        (r"Banks", r"4 dies $\times$ 16", r"16 pCH $\times$ 16"),
        (r"Internal bandwidth", r"409.6\,GB/s", r"1,024\,GB/s"),
        (r"\tck (CK)", r"1.25\,ns (0.8\,GHz)", r"1\,ns (1\,GHz)"),
        (r"\tccds, \tccdl{} (column)", r"2.5, 5\,ns~\cite{lpspec,ramulator2}", r"2, 4\,ns~\cite{hbmpim,p3llm}"),
        (r"Row (page) size", r"2\,KB~\cite{jedeclpddr5}", r"1\,KB~\cite{jedechbm2}"),
        (r"PU placement", r"one per bank", r"one per two banks"),
        (r"$t_\mathrm{REFI}$, $t_\mathrm{RFCab}$", r"3.906\,\textmu s, 280\,ns", r"simulator preset"),
        (r"Precision", r"INT8", r"W4A8"),
    ]
    assert 1.25 * 4 == 5.0 and 1.0 * 4 == 4.0 and 2 * 2.5 == 5.0                     # column period = 4 t_CK = 2 t_CCD_S
    out = [r"\begin{tabular}{@{}lll@{}}", r"\toprule", r"Platform & Mobile platform & Edge server \\", r"\midrule"]
    out += [" & ".join(r) + r" \\" for r in rows]
    out += [r"\bottomrule", r"\end{tabular}"]
    print("platform block: NPU 12 / 131 TOPS, 42 / 256 GB/s; internal 409.6 / 1,024 GB/s; t_CK 1.25 / 1 ns; column 5 / 4 ns")
    return "\n".join(out)


def table4(peak):
    t = read("dac_table4.csv")
    by = {(r["substrate"][:5], r["design"]): r for r in t}
    exp = {  # frozen: lanes x ALUs, MHz, D, V, accumulator slots, staging bits, GB KB, logic mm2 (V prose)
        ("phone", "stock"): (32, 1, 200, 1, 1, 1, 256, 2, 0.947), ("phone", "h3"): (32, 1, 400, 2, 2, 2, 512, 4, 1.050),
        ("phone", "h2"): (32, 4, 200, 4, 4, 4, 1024, 8, 2.610), ("phone", "core8"): (32, 1, 800, 4, 8, 16, 1536, 16, 1.406),
        ("serve", "stock"): (64, 1, 250, 1, 1, 2, 512, 4, 0.520), ("serve", "p3_500"): (64, 1, 500, 2, 2, 4, 1024, 8, 0.617),
        ("serve", "h2"): (64, 4, 250, 4, 4, 8, 2048, 16, 1.469), ("serve", "core4"): (64, 1, 1000, 4, 4, 16, 2048, 16, 0.821),
    }
    lines = []
    for sub, designs, head in (("phone", PHONE, r"\multicolumn{9}{@{}l}{\emph{Mobile platform,} per die} \\"),
                               ("serve", HBM2, r"\multicolumn{9}{@{}l}{\emph{Edge server,} per pseudo-channel} \\")):
        lines.append(r"\midrule")
        lines.append(head)
        for d, name in designs:
            r = by[(sub, d)]
            got = (int(r["multipliers_per_PU"]) // int(r["alus_per_PU"]), int(r["alus_per_PU"]), int(float(r["PU_clock_MHz"])),
                   int(r["D_beats_per_column"]), int(r["V_tile"]), int(r["acc_slots_per_PU"]), int(r["staging_bits_per_PU"]),
                   int(r["GB_KB"]), r3(r["logic_mm2"]))
            assert got == exp[(sub, d)], (sub, d, got)
            lanes = f"{got[1]}$\\times${got[0]}" if got[1] > 1 else f"{got[0]}"
            pw = peak[("phone" if sub == "phone" else "hbm2", d)]
            assert got[2] == pw[0]                                    # one MHz column serves both former tables
            nm = r"\textbf{CoDe}" if name == "CoDe" else name
            mm = f"\\textbf{{{got[8]:.3f}}}" if name == "CoDe" else f"{got[8]:.3f}"
            mw = f"{pw[1]:.1f}"
            mw = f"\\textbf{{{mw}}}" if name == "CoDe" else mw
            lines.append(f"{nm} & {lanes} & {got[2]} & {got[3]} & {got[4]} & {got[5]} & {got[7]} & {mm} & {mw} \\\\")
    # ratios the prose prints
    p = {d: f(by[("phone", d)]["logic_mm2"]) for d, _ in PHONE}
    s = {d: f(by[("serve", d)]["logic_mm2"]) for d, _ in HBM2}
    assert r3(p["core8"] / p["h2"]) == 0.539                     # x.ev56.area.core8_over_h2
    assert r2(s["core4"] / s["p3_500"]) == 1.33                   # CoDe / P3-LLM-style logic, per pCH
    assert r2(s["core4"] / s["h2"]) == 0.56                       # CoDe / LP-Spec-style logic on HBM2
    assert all(f(by[(k, d)]["peak_GOPS"]) == v for k, d, v in
               (("phone", "h2", 3276.8), ("phone", "core8", 3276.8), ("serve", "core4", 16384.0)))
    out = os.path.join(REPO, "tables", "tab_params.tex")
    with open(out, "w") as fh:
        fh.write("% generated by scripts/make_tables.py: platform block (platform_block(): evaluation dac_sd8g3 / dac_2x2 raw "
                 "inputs, cited spec values, simulator presets) above the design block (EV-58 pack dac_table4.csv, pupow "
                 "pupow_peak_*.csv); do not edit\n")
        fh.write(platform_block() + "\n\\par\\smallskip\n")
        fh.write("\\begin{tabular}{@{}lcccccccc@{}}\n\\toprule\n"
                 "Design & Lanes & MHz & $D$ & $V$ & Acc. & GB KB & mm$^2$ & mW \\\\\n")
        fh.write("\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n")
    print("wrote", out)


def area_split():
    a = read("dac_fig4_area.csv")
    sh = {(r["substrate"], r["design"], r["component"]): f(r["share"]) for r in a}
    arith = {k[:2]: v for k, v in sh.items() if k[2] == "arithmetic"}
    store = {}
    for (sub, d, c), v in sh.items():
        if c in ("accumulators", "staging", "staging_fifo_control", "weight_latch"):
            store[(sub, d)] = store.get((sub, d), 0) + v
    # V prose (former Fig. area): share of the logic in multipliers vs in storage
    assert r2(arith[("phone", "h2")]) == 0.73 and r2(arith[("phone", "core8")]) == 0.34
    assert r2(store[("phone", "core8")]) == 0.32 and r2(store[("phone", "h2")]) == 0.10
    assert r2(arith[("hbm2", "core4")]) == 0.30 and r2(store[("hbm2", "core4")]) == 0.33
    print("area split: phone arith LP 0.73 / CoDe 0.34, storage CoDe 0.32 / LP 0.10; HBM2 CoDe arith 0.30 storage 0.33")


def mech_checks():
    """M = 8 command counts and C-bus occupancy that VI-A / VI-B print (former Table V; no file is written); the
    pu_busy_trace column equals the useful-MAC U of umac_table() at M = 8 (asserted there)."""
    m = [r for r in read("dac_mech.csv") if r["scope"].startswith("one decoder") and r["M"] == "8"]
    by = {(r["substrate"], r["design"]): r for r in m}
    exp = {  # M = 8: MAC commands, column reads (per token per column), C/A or C-bus occupancy, pu_busy_trace
        ("phone", "stock"): (1.0, 1.0, 0.214, 0.717), ("phone", "h3"): (1.0, 0.5, 0.394, 0.709),
        ("phone", "h2"): (0.25, 0.25, 0.222, 0.694), ("phone", "core8"): (0.125, 0.125, 0.136, 0.779),
        ("hbm2", "stock"): (1.0, 1.0, 0.404, 0.771), ("hbm2", "p3_500"): (1.0, 0.5, 0.791, 0.758),
        ("hbm2", "core4"): (0.25, 0.25, 0.431, 0.739),
    }
    for (sub, d), e in exp.items():
        r = by[(sub, d)]
        occ = r["ca_occupancy"] if sub == "phone" else r["cbus_occupancy"]
        got = (r3(r["mac_cmds_per_token_per_column"]), r3(r["column_reads_per_token_per_column"]), r3(occ),
               r3(r["pu_busy_trace"]))
        assert got == e, (sub, d, got)
    # M = 4 on the phone: CoDe's counts equal LP-Spec-style's (prose)
    m4 = {(r["substrate"], r["design"]): r for r in read("dac_mech.csv")
          if r["scope"].startswith("one decoder") and r["M"] == "4"}
    for c in ("mac_cmds_per_token_per_column", "ca_occupancy", "pu_busy_trace"):
        assert m4[("phone", "core8")][c] == m4[("phone", "h2")][c], c
    print("mechanism (M = 8): phone MAC cmds CoDe 0.125 / LP 0.25; HBM2 C bus CoDe 0.431 / P3 0.791")


def umac_table():
    """Table (Sec. III-B, tab:umac): useful-MAC utilization U = U_MAC x f_MAC of one Llama-2-7B decoder layer's weight
    GEMMs on the mobile platform at M = 8, simulated values; plus every useful-MAC number the prose prints."""
    rows = {}
    for r in read("tab_umac_paper.csv", os.path.join(EVAL, "dac_2x2", "figures")):
        rows[(r["platform"], r["design"], int(r["M"]))] = r
    const = {r["row_id"]: f(r["value"]) for r in read("umacp_const.csv", os.path.join(EVAL, "dac_2x2", "raw"))}
    tid = {r["id"]: float(r["value"]) for r in read("touched.csv", os.path.join(EVAL, "dac_2x2"))}
    rec = {"stock": "stock AiM", "p3": "P3-like", "lpspec": "LP-Spec-like"}
    code = {"phone": "CoRe V = 8", "hbm2": "CoRe V = 4"}

    def row(p, d, M):
        return rows[(p, code[p] if d == "code" else rec[d], M)]

    def cell(p, d, M):
        r = row(p, d, M)
        return (int(f(r["A"])), int(f(r["t_slot_ns"])), f"{f(r['U_MAC']):.2f}", f"{r3(r['f_MAC_sim']):.3f}",
                f"{r3(r['U_sim']):.3f}", f"{r2(r['oh_ns_per_token_per_row_sim']):.2f}")
    # the printed table (mobile platform, M = 8), every cell asserted
    want = {"stock": (1, 5, "0.25", "0.717", "0.179", "123.39"), "p3": (2, 5, "0.50", "0.709", "0.355", "63.94"),
            "lpspec": (4, 5, "1.00", "0.694", "0.694", "34.41"), "code": (8, 10, "1.00", "0.779", "0.779", "22.15")}
    names = {"stock": "Stock AiM", "p3": "P3-LLM-style", "lpspec": "LP-Spec-style (4 ALUs)", "code": r"\textbf{CoDe} ($V = 8$)"}
    lines = [r"% generated by scripts/make_tables.py from evaluation/dac_2x2/figures/tab_umac_paper.csv (umacp ids,"
             r" simulated columns, M = 8); do not edit",
             r"\begin{tabular}{@{}lcccccc@{}}", r"\toprule",
             r"Design & $A$ & \tslot & \UMAC & \fMAC & $U$ & Non-MAC \\",
             r" & & ns & & & & ns/token \\", r"\midrule"]
    for d in ("stock", "p3", "lpspec", "code"):
        c = cell("phone", d, 8)
        assert c == want[d], (d, c)
        lines.append(" & ".join([names[d]] + [str(x) for x in c]) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(REPO, "tables", "tab_umac.tex"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    # U = U_MAC x f_MAC per row (simulated columns), and the stock worked example 1/4 x 0.717 = 0.179
    for k, r in rows.items():
        assert abs(f(r["U_MAC"]) * f(r["f_MAC_sim"]) - f(r["U_sim"])) < 1e-5, k
    # edge server, M = 8 (prose): stock 0.193 (f_MAC 0.771), P3-LLM-style 0.379, LP-Spec-style = CoDe V = 4 0.739;
    # simulated non-MAC ns per token per open row 146.17 / 78.70 / 43.51
    e = {d: cell("hbm2", d, 8) for d in ("stock", "p3", "lpspec", "code")}
    assert [e[d][4] for d in ("stock", "p3", "lpspec", "code")] == ["0.193", "0.379", "0.739", "0.739"], e
    assert e["stock"][3] == "0.771" and [e[d][5] for d in ("stock", "p3", "lpspec")] == ["146.17", "78.70", "43.51"], e
    assert e["code"] == e["lpspec"] and [e[d][1] for d in e] == [8] * 4
    # III-C (rival row switch): edge-server sweep factors P3-LLM-style 0.758, LP-Spec-style 0.739 vs stock 0.771
    assert (e["p3"][3], e["lpspec"][3]) == ("0.758", "0.739"), e
    # mobile, M = 4: CoDe issues LP-Spec-style's command stream (U 0.695, VI-A)
    assert cell("phone", "code", 4) == cell("phone", "lpspec", 4) and cell("phone", "code", 4)[4] == "0.695"
    # the same U as the pack's pu_busy_trace at M = 8 (VI-A 0.779 / 0.694, VI-B 0.739)
    mech = {(r["substrate"], r["design"]): r3(r["pu_busy_trace"]) for r in read("dac_mech.csv")
            if r["scope"].startswith("one decoder") and r["M"] == "8"}
    assert mech[("phone", "core8")] == 0.779 and mech[("phone", "h2")] == 0.694 and mech[("hbm2", "core4")] == 0.739
    # formula constants (III-B prints the mobile case study only: 87.73, 4.26, 0.070; the HBM2 fit values 94.76 / 9.64 /
    # 0.061 are guard-only since 2026-10-29): t_row (data key t_fix) / t_tok, refresh share, columns per run
    assert round(tid["umac.paper.phone.t_fix_paper_ns"], 2) == 87.73 == round(const["phone/t_fix_factor"], 2)
    assert round(const["phone/rho"], 3) == 0.070
    assert round(tid["umac.paper.hbm2.t_fix_paper_ns"], 2) == 94.76 == round(const["hbm2/t_fix_factor"], 2)
    assert round(const["phone/t_tok"], 2) == 4.26 and round(const["hbm2/t_tok"], 2) == 9.64
    assert round(f(row("hbm2", "stock", 8)["t_slot_ns"])) == 8 and round(const["hbm2/rho"], 3) == 0.061
    assert round(const["phone/c"]) == 62 == round(const["hbm2/c"])
    # convergence: formula within 0.33 % (mobile) and 0.59 % (edge server) on the designs it was not fitted on
    assert round(tid["umac.paper.phone.maxres_nonstock_pct"], 2) == 0.33
    assert round(tid["umac.paper.hbm2.maxres_nonstock_pct"], 2) == 0.59
    # V: P3-LLM-style re-timed on the mobile C/A bus, U 0.355 -> 0.351
    assert round(tid["umac.p3t.phone.U_timed.min"], 3) == 0.351 == round(tid["umac.p3t.phone.U_timed.max"], 3)
    # III-C: LP-Spec-style's U per multiplier, 0.173-0.174 mobile (M = 4, 8, 16) / 0.185 edge server; below stock AiM's 0.179
    assert (round(tid["umac.phone.h2.U_per_mult.min"], 3), round(tid["umac.phone.h2.U_per_mult.max"], 3)) == (0.173, 0.174)
    assert tid["umac.phone.h2.U_per_mult.max"] < f(row("phone", "stock", 8)["U_sim"])
    assert round(tid["umac.hbm2.h2.U_per_mult.min"], 3) == 0.185 == round(tid["umac.hbm2.h2.U_per_mult.max"], 3)
    print("useful-MAC table: mobile M = 8 U 0.179 / 0.355 / 0.694 / 0.779; edge 0.193 / 0.379 / 0.739; "
          "t_fix 87.73 / 94.76, t_tok 4.26 / 9.64, rho 0.070 / 0.061; residual 0.33 % / 0.59 %")


def umac_src_table():
    """Table (Sec. VI-B, tab:umac_src): CoDe's gain over stock AiM in two sources (D-35), stock AiM -> run sharing only
    (simulated: CoDe's trace at D = 1) -> CoDe, one decoder layer's weight GEMMs at M = 8 on both platforms; plus the
    III-B row-switch numbers (stock t_row split by command, the motivation fact) and the VI-B other-order clause
    (model-composed beat fill only). Source: umac_src (microarch d59e4a2, collected at evaluation 4ffbc7f, dac_2x2 Sec. 2i):
    figures/tab_umac_src_steps.csv (usrc_steps ids), raw/usrc_nonmac.csv, raw/usrc_motiv.csv, touched umac.src.* ids.
    The composed run-sharing-only row is never printed (the paper uses the simulated one)."""
    st = {}
    for r in read("tab_umac_src_steps.csv", os.path.join(EVAL, "dac_2x2", "figures")):
        st[(r["platform"], r["design"], int(r["M"]))] = r
    raw = os.path.join(EVAL, "dac_2x2", "raw")
    nm = {r["row_id"]: f(r["full_ns_per_token_per_run"]) for r in read("usrc_nonmac.csv", raw)}
    mo = {r["row_id"]: r for r in read("usrc_motiv.csv", raw)}
    tid = {r["id"]: float(r["value"]) for r in read("touched.csv", os.path.join(EVAL, "dac_2x2"))}
    const = {r["row_id"]: f(r["value"]) for r in read("umacp_const.csv", raw)}
    lab = {"stock": "stock AiM", "rs": "run sharing only (sim)", "core": "CoRe (both)", "bf": "beat fill only (composed)",
           "oo": "CoRe via beat fill (other order)"}

    def g(p, d, c, M=8):
        return f(st[(p, lab[d], M)][c])

    want = {  # U_MAC, f_MAC, U, step, cumulative (printed; frozen)
        ("phone", "stock"): ("0.25", "0.717", "0.179", "--", "1.00"), ("phone", "rs"): ("0.25", "0.892", "0.223", "1.24", "1.24"),
        ("phone", "core"): ("1.00", "0.779", "0.779", "3.49", "4.35"),
        ("hbm2", "stock"): ("0.25", "0.771", "0.193", "--", "1.00"), ("hbm2", "rs"): ("0.25", "0.887", "0.222", "1.15", "1.15"),
        ("hbm2", "core"): ("1.00", "0.739", "0.739", "3.33", "3.83"),
    }
    names = {"stock": "Stock AiM", "rs": "Row reuse only", "core": r"\textbf{CoDe}"}
    lines = [r"% generated by scripts/make_tables.py from evaluation/dac_2x2/figures/tab_umac_src_steps.csv (usrc_steps ids,"
             r" simulated rows, layer, M = 8); do not edit",
             r"\begin{tabular}{@{}lccccc@{}}", r"\toprule",
             r"Design & \UMAC & \fMAC & $U$ & \multicolumn{2}{c@{}}{Speedup} \\", r"\cmidrule(l){5-6}",
             r" & & & & step & cumul. \\"]
    for p, head in (("phone", r"\emph{Mobile:} Llama-2-7B, $V = 8$"), ("hbm2", r"\emph{Server:} Llama-3.1-8B, $V = 4$")):
        lines += [r"\midrule", r"\multicolumn{6}{@{}l}{" + head + r"} \\"]
        for d in ("stock", "rs", "core"):
            r = st[(p, lab[d], 8)]
            assert "composed" not in r["design"] and "composed" not in r["flags"], (p, d)   # simulated rows only
            step = "--" if d == "stock" else f"{r2(r['step_speedup']):.2f}"
            c = (f"{f(r['U_MAC']):.2f}", f"{r3(r['f_MAC']):.3f}", f"{r3(r['U']):.3f}", step, f"{r2(r['cumulative_speedup']):.2f}")
            assert c == want[(p, d)], (p, d, c)
            lines.append(" & ".join([names[d]] + list(c)) + r" \\")
        # identities: U = U_MAC x f_MAC, product of the steps = cumulative, both orders' products agree
        for d in ("stock", "rs", "core"):
            assert abs(g(p, d, "U_MAC") * g(p, d, "f_MAC") - g(p, d, "U")) < 1e-5
        assert abs(g(p, "rs", "step_speedup") * g(p, "core", "step_speedup") - g(p, "core", "cumulative_speedup")) < 1e-3
        assert abs(tid[f"umac.src.{p}.M8.order_product"] - tid[f"umac.src.{p}.M8.other_order_product"]) < 1e-3
        # VI-B prose: run sharing alone lifts f_MAC; U_MAC stays at 1/4; the composed beat-fill-only f_MAC falls to 0.425 (mobile)
        # and 0.506 (edge server): the non-MAC commands take 57.5 % and about half of the shortened time
        assert g(p, "rs", "f_MAC") > g(p, "stock", "f_MAC") and g(p, "rs", "U_MAC") == 0.25
        assert r3(g(p, "bf", "f_MAC")) == {"phone": 0.425, "hbm2": 0.506}[p] and g(p, "bf", "f_MAC") < g(p, "stock", "f_MAC")
        # "row reuse has removed most of the row-switch overhead per token" (per token per sweep, stock -> row reuse only)
        assert tid[f"umac.src.{p}.rs.M8.framing_full_ns"] < 0.5 * tid[f"umac.src.{p}.stock.M8.framing_full_ns"]
        # "each source is worth more once the other is present"
        assert g(p, "core", "step_speedup") > g(p, "bf", "step_speedup") and g(p, "oo", "step_speedup") > g(p, "rs", "step_speedup")
    lines += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(REPO, "tables", "tab_umac_src.tex"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    # the stock and CoDe rows are the rows of tab:umac (mobile) and of the VI-B prose (edge server)
    assert want[("phone", "stock")][2] == "0.179" and want[("phone", "core")][2] == "0.779"
    # VI-B other-order clause (model-composed): beat fill only U 0.425 / 0.506, steps 2.37 x 1.83 / 2.62 x 1.46
    assert (r3(g("phone", "bf", "U")), r3(g("hbm2", "bf", "U"))) == (0.425, 0.506)
    assert (r2(g("phone", "bf", "step_speedup")), r2(g("phone", "oo", "step_speedup"))) == (2.37, 1.83)
    assert (r2(g("hbm2", "bf", "step_speedup")), r2(g("hbm2", "oo", "step_speedup"))) == (2.62, 1.46)
    # guard only (III-B prints q_proj shares since 2026-10-29): stock row-switch overhead, layer, M = 8, ns per sweep
    cls = {c: nm[f"phone/stock/8/{c}"] for c in ("TMOD", "ACT16", "PREA", "WRMAC16")}
    assert [round(cls[c], 1) for c in ("TMOD", "ACT16", "PREA", "WRMAC16")] == [40.5, 37.9, 11.5, 1.2], cls
    assert sorted(cls, key=cls.get, reverse=True) == ["TMOD", "ACT16", "PREA", "WRMAC16"]   # printed largest first
    assert round(tid["umac.src.phone.stock.M8.tmod_each_ns"]) == 20 and round(nm["phone/stock/8/TMOD"] / 20) == 2
    pm, hm = mo["phone/layer/8"], mo["hbm2/layer/8"]
    assert round(f(pm["framing_full_ns_per_token_per_run"]), 1) == 91.2 == round(tid["umac.src.phone.stock.M8.framing_full_ns"], 1)
    assert round(f(pm["useful_mac_ns_per_token_per_run"]), 1) == 78.0
    assert f(pm["framing_full_over_useful"]) > 1                                       # mobile: framing > useful work
    assert tid["umac.src.phone.stock.M8.framing_full_ns_per_run"] == tid["umac.src.phone.stock.M8.framing_full_ns"]
    # fitted t_fix (87.73, factor form) lies below the framing sum: the fit nets out the MAC tail (guard only)
    assert const["phone/t_fix_factor"] < tid["umac.src.phone.stock.M8.framing_full_ns"] and nm["phone/stock/8/pu_tail"] < 0
    # edge server: only the whole non-MAC time exceeds the useful work (never "run framing exceeds it", D-35); III-B prints
    # this as q_proj shares (23.4 % vs 19.1 %, make_fig_breakdown.py); the ns values are guard only
    assert round(f(hm["nonmac_ns_per_token_per_run"]), 1) == 146.2 and round(nm["hbm2/stock/8/refresh"], 1) == 41.8
    assert round(f(hm["useful_mac_ns_per_token_per_run"]), 1) == 123.3
    assert f(hm["nonmac_over_useful"]) > 1 > f(hm["framing_full_over_useful"])
    print("umac sources: U phone 0.179 -> 0.223 -> 0.779 (1.24 x 3.49 = 4.35), HBM2 0.193 -> 0.222 -> 0.739 (1.15 x 3.33 = 3.83); "
          "other order 2.37 x 1.83 / 2.62 x 1.46; stock framing 91.2 > 78.0 ns (mobile), non-MAC 146.2 > 123.3 ns (HBM2)")


def stock_checks():
    """III-A: stock GEMM time grows in proportion to M (the spread is asserted, no longer printed); III-B: the
    cycle-identical re-run of stock AiM with a PU four times faster, clocked at CK
    (microarch/04_data/d1/stock_cmd, refresh-fixed since microarch fd39875; the asserts of the retired make_fig_stockcmd.py)."""
    src = os.path.join(WS, "microarch", "04_data", "d1", "stock_cmd")
    checks = {r["check"]: r for r in read("stock_cmd_checks.csv", src)}
    ident = checks["stock runs with the D = 4 PU occupancy: cycle-identical"]
    assert ident["ok"] == "True" and ident["value"] == ident["expect"], ident
    tm = {p: float(checks[f"{p} stock time / M across M per shape (max |rel|; refresh phase only)"]["value"])
          for p in ("phone", "hbm2")}
    assert f"{100 * tm['phone']:.2f}" == "1.84" and f"{100 * tm['hbm2']:.1f}" == "2.7", tm
    print("stock faster-PU test: cycle-identical; time / M within 1.84 % (mobile) and 2.7 % (edge server)")


def headline():
    h = read("dac_headline.csv")
    e2e = {(r["draft"], r["design"]): r for r in h if r["item"].startswith("phone end to end")}
    g = lambda k, c: f(e2e[k][c])  # noqa: E731
    assert r2(g(("1B draft", "all CoRe V = 8"), "tok_s")) == 47.12 and r2(g(("1B draft", "all LP-Spec-like"), "tok_s")) == 46.84
    assert round(g(("EAGLE head", "all CoRe V = 8"), "tok_s"), 1) == 68.1 == round(g(("EAGLE head", "all LP-Spec-like"), "tok_s"), 1)
    assert round(g(("none", "plain NPU decode"), "tok_s"), 1) == 6.1
    assert round(g(("1B draft", "NPU speculative loop"), "tok_s"), 1) == 10.6
    # energy per token: synthesised PU (pupow @ microarch 6074fea, evaluation 88dad76); the pack's mJ columns are the K_E reserve
    pe = {r["row_id"]: f(r["mJ_per_tok_reads"]) for r in read("pupow_e2e.csv", os.path.join(EVAL, "dac_sd8g3", "raw"))}
    assert round(pe["d1b/all_core"], 1) == 66.2 and round(pe["eagle/all_core"], 1) == 49.8
    assert round(pe["plain/plain_npu"]) == 971 and round(pe["d1b/all_npu"]) == 558
    assert r2(g(("1B draft", "all CoRe V = 8"), "gain_vs_plain_npu")) == 7.71
    assert r2(g(("EAGLE head", "all CoRe V = 8"), "gain_vs_plain_npu")) == 11.14
    assert int(g(("1B draft", "all CoRe V = 8"), "M")) == 3 and int(g(("EAGLE head", "all CoRe V = 8"), "M")) == 4
    # HBM2 batch bands, CoDe (V = 4) / P3-LLM-style, min-max of per-M geomeans over five models
    b = {(r["design"], r["metric"], r["band"]): (r2(r["lo"]), r2(r["hi"])) for r in h if r["item"].startswith("HBM2 batch step")}
    assert b[("core4 vs p3_500", "speed", ">=8")] == (1.68, 1.68)
    assert b[("core4 vs p3_500", "per_logic_mm2", ">=8")] == (1.26, 1.26)
    # system energy, P3-LLM-style / CoDe from batch 8: synthesised PU (pupow_head_hbm2 synth column); printed at the lower end
    ph = {r["row_id"]: f(r["synth"]) for r in read("pupow_head_hbm2.csv", os.path.join(EVAL, "dac_2x2", "raw"))}
    e = lambda w, k: ph[f"batch/vs_p3_500/energy_sys_{w}/b8+/{k}"]  # noqa: E731
    assert r2(e("55W", "lo")) == 1.64 and r2(e("55W", "hi")) == 1.64   # both ends round to the printed "1.64x"
    assert r2(e("0W", "lo")) == 1.46 and r2(e("0W", "hi")) == 1.46
    assert b[("core4 vs p3_500", "speed", "3-6")] == (1.43, 1.71)
    assert b[("core4 vs p3_500", "per_logic_mm2", "3-6")] == (1.08, 1.28)
    assert b[("core4 vs p3_500", "per_logic_mm2", "1-2")] == (0.80, 0.84)
    assert b[("core4 vs p3_500", "speed", "1-2")] == (1.07, 1.12)
    assert b[("core4 vs stock", "speed", ">=8")] == (2.87, 2.88)
    # crossovers vs the NPU (largest grid M at which the PIM step wins; min-max)
    xo = {}
    for r in h:
        if "crossover" in r["item"] and ("primary" in r["item"] or "batch step" in r["item"]):
            xo.setdefault((r["item"][:5], r["design"]), []).append(int(r["wins_up_to_M"]))
    rng = {k: (min(v), max(v)) for k, v in xo.items()}
    assert rng[("phone", "core8")] == (24, 26) and rng[("phone", "h2")] == (20, 24) and rng[("phone", "stock")] == (6, 6)
    assert rng[("HBM2 ", "core4")] == (8, 12) and rng[("HBM2 ", "p3_500")] == (4, 6) and rng[("HBM2 ", "stock")] == (2, 3)
    print("headline: phone e2e, HBM2 bands, crossovers hold")


def phone_levels():
    rows = read("dac_fig5_phone.csv")

    def band(level, metric, lo=1, hi=64):
        v = [f(r[metric]) for r in rows if r["level"].startswith(level) and r["design"] == "h2"
             and f(r[metric]) is not None and lo <= int(r["M"]) <= hi]
        return r2(min(v)), r2(max(v))
    assert band("GEMM", "core_per_mm2_vs") == (1.86, 3.06)
    assert band("attention", "core_per_mm2_vs") == (1.86, 2.34)
    assert band("decode", "core_per_mm2_vs") == (1.86, 2.85)
    assert band("decode", "core_speed_vs", 5, 5) == (1.54, 1.54)
    assert band("decode", "core_speed_vs", 8, 64) == (1.07, 1.31)
    assert band("decode", "core_speed_vs", 1, 4) == (1.00, 1.00)
    # attention layer already faster at M = 2-4 (gmean over head configs); max = dacp.phone.fig5.layer.core8_vs_h2.speed_Mle4.max
    assert band("attention", "core_speed_vs", 2, 4) == (1.01, 1.14)
    assert band("GEMM", "core_speed_vs", 1, 4) == (1.00, 1.00)
    # attention-layer energy, LP-Spec-style / CoDe, synthesised PU (pupow_ev56_table, reads priced; the mux is inside the PU)
    t = {r["row_id"]: (f(r["lo"]), f(r["hi"])) for r in read("pupow_ev56_table.csv", os.path.join(EVAL, "dac_sd8g3", "raw"))}
    le4 = [t["reads/h2/layer/energy/b1-2"], t["reads/h2/layer/energy/b3-6"]]
    assert (r2(min(x[0] for x in le4)), r2(max(x[1] for x in le4))) == (1.05, 1.16)
    assert (r2(t["reads/h2/layer/energy/b8+"][0]), r2(t["reads/h2/layer/energy/b8+"][1])) == (1.16, 1.28)
    # P3-LLM reproduction (EV-49, INT8): depth-2 step gain over a depth-1 PIM, mean over models and batch 2 / 4
    rep = {r["row_id"]: r for r in read("hbm2_p3llm_repro.csv", os.path.join(EVAL, "dac_2x2", "raw"))}
    assert r2(rep["tep_mean/all/2,4"]["ours"]) == 1.78 and float(rep["tep_mean/all/2,4"]["p3llm"]) == 1.6
    # end-to-end loop speed, CoDe / LP-Spec-style over L 128-1024 (dac_sd8g3 x.ev56.loop.*.speed.*): "1.00--1.006"
    tid = {r["id"]: float(r["value"]) for r in read("touched.csv", os.path.join(EVAL, "dac_sd8g3"))}
    lo = min(tid[f"x.ev56.loop.{d}.speed.min"] for d in ("d1b", "eagle"))
    hi = max(tid[f"x.ev56.loop.{d}.speed.max"] for d in ("d1b", "eagle"))
    assert (r2(lo), r3(hi)) == (1.00, 1.006), (lo, hi)
    print("phone levels, layer energy, P3-LLM reproduction, loop speed hold")


def table_power():
    """Peak power on the 1.05 V supply, synthesised PU, ungated (Table I's mW column) and the VI-C prose numbers.
    Returns {(substrate, design): (MHz, total mW)}."""
    raw = {"phone": os.path.join(EVAL, "dac_sd8g3", "raw"), "hbm2": os.path.join(EVAL, "dac_2x2", "raw")}
    pk = {sub: {r["row_id"]: r for r in read(f"pupow_peak_{sub}.csv", raw[sub])} for sub in raw}
    exp = {  # MHz, PU dynamic, leakage, GB reads, total mW, / LP-Spec-style, pJ per edge (pupow_peak_<sub>.<d>/synth)
        ("phone", "stock"): (200, 87.6, 22.2, 6.4, 203.9, 0.35, 438), ("phone", "h3"): (400, 178.9, 24.2, 18.2, 308.9, 0.53, 447),
        ("phone", "h2"): (200, 355.2, 89.6, 51.5, 583.9, 1.00, 1776), ("phone", "core8"): (800, 417.3, 30.7, 72.9, 608.5, 1.04, 522),
        ("hbm2", "stock"): (250, 57.1, 11.7, 11.4, 134.9, 0.32, 228), ("hbm2", "p3_500"): (500, 128.7, 13.4, 32.2, 229.1, 0.53, 257),
        ("hbm2", "h2"): (250, 235.2, 47.2, 91.1, 428.3, 1.00, 941), ("hbm2", "core4"): (1000, 304.5, 16.8, 64.4, 440.4, 1.03, 304),
    }
    fetch = {"phone": 87.6, "hbm2": 54.8}
    peak = {}
    for sub, designs in (("phone", PHONE), ("hbm2", HBM2)):
        for d, _ in designs:
            r = pk[sub][f"{d}/synth"]
            assert round(f(r["fetch_mW"]), 1) == fetch[sub]
            got = (int(f(r["clk_MHz"])), round(f(r["pu_dyn_mW"]), 1), round(f(r["leak_mW"]), 1), round(f(r["gb_mW"]), 1),
                   round(f(r["total_mW"]), 1), r2(r["ratio_to_lps"]), round(f(r["edge_pJ"])))
            assert got == exp[(sub, d)], (sub, d, got)
            peak[(sub, d)] = (got[0], got[4])
    # prose: per-edge charge ratio, the clock penalty of the arithmetic, gating (a CoDe option), idle fractions
    tid = {}
    for sub in ("dac_sd8g3", "dac_2x2"):
        tid.update({r["id"]: float(r["value"]) for r in read("touched.csv", os.path.join(EVAL, sub))})
    assert round(tid["pupow.phone.edge.h2_over_core.pC"], 1) == 3.4 and round(tid["pupow.hbm2.edge.h2_over_core.pC"], 1) == 3.1
    assert f(pk["phone"]["h2/synth"]["edge_ns"]) == 5.0 and f(pk["phone"]["core8/synth"]["edge_ns"]) == 1.25
    assert r2(f(pk["phone"]["h2/synth"]["leak_mW"]) / f(pk["phone"]["core8/synth"]["leak_mW"])) == 2.92   # "2.9x"
    assert r2(f(pk["hbm2"]["h2/synth"]["leak_mW"]) / f(pk["hbm2"]["core4/synth"]["leak_mW"])) == 2.81    # "2.8x"
    cuts = {r["row_id"]: r for r in read("pupow_cuts_phone.csv", raw["phone"])}
    assert f(cuts["base"]["v_pu"]) == 1.05                                                              # VDD2H, V
    # 800 vs 200 MHz, same INT8 32-lane arithmetic (not collected: microarch 04_data/d1/pu_power, read through this script)
    cp = [r for r in read("pu_peak_power.csv", os.path.join(WS, "microarch", "04_data", "d1", "pu_power"))
          if r["table"] == "clock_penalty" and r["design"] == "int8_32" and r["clk_MHz"] == "800"]
    assert len(cp) == 1 and round((f(cp[0]["rel_synth"]) - 1) * 100, 1) == 2.4
    g = {k: tid[k] for k in tid if k.startswith(("pupow.phone.gate", "pupow.hbm2.gate"))}
    assert round(-g["pupow.phone.gate.core8.d_total_pct"], 1) == 11.6 and round(-g["pupow.hbm2.gate.core4.d_total_pct"], 1) == 15.1
    assert round(-g["pupow.phone.gate.h2.d_total_pct"], 1) == 0.5 and round(-g["pupow.hbm2.gate.h2.d_total_pct"], 1) == 3.6
    assert r2(g["pupow.phone.gate.core8.over_h2"]) == 0.92 and r2(g["pupow.hbm2.gate.core4.over_h2"]) == 0.87
    assert r2(g["pupow.phone.gate.core8_over_gated_h2"]) == 0.93 and r2(g["pupow.hbm2.gate.core4_over_gated_h2"]) == 0.91
    assert tid["pupow.phone.idle.core8.acc_slot_cycles_per_write"] == 16 == tid["pupow.hbm2.idle.core4.acc_slot_cycles_per_write"]
    assert round(tid["pupow.phone.idle.core8.staging_cycles_per_write"]) == 6 and tid["pupow.hbm2.idle.core4.staging_cycles_per_write"] == 8
    assert tid["pupow.phone.idle.h2.max_idle"] == 0.0
    return peak


if __name__ == "__main__":
    os.makedirs(os.path.join(REPO, "tables"), exist_ok=True)
    table4(table_power())
    area_split()
    mech_checks()
    umac_table()
    umac_src_table()
    stock_checks()
    headline()
    phone_levels()
    print("checks: all frozen values hold")
