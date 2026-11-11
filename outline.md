# Commands Are the Bottleneck: CoDe, a Command-Decoupled PIM for Skinny GEMMs on Mobile and Server DRAM: outline
Synced with: 214bcc5; ACM sigconf (acmart, 9 pt) since 2026-11-10; bold run-in heads (`\runin`) since ff51469; edge-server P3-LLM-style at P3-LLM's own placement since b992b75; measured weight-I/O cause of the gated 2.08× since a1e9db4; VI-F Beat Filling on Newer DRAM since 214bcc5: body ends p. 11 R with 32 column lines of slack; refs p. 11 to p. 13.
Legend: one entry per source paragraph, in source order, tied to the `.tex` by `% P:<id>`; Message = the one claim a reader takes away; Floats = figures/tables/equations cited (first cite marked); Numbers = key printed numbers ← the script that asserts them (evaluation topic in brackets); Cites = bib keys; Links = → promise fulfilled by <id>, ← relies on <id>. Check: `python3 scripts/check_outline.py`.

Number sources, short names: `tables` = scripts/make_tables.py (functions in brackets); `roof` = make_fig_roofline.py; `brk` = make_fig_breakdown.py; `map` = make_fig_mapping.py; `vsw` = make_fig_vsweep.py; `gemm` / `e2e` = make_fig_gemm.py / make_fig_e2e.py (ISCA ids `isca.gemm.*`, `isca.e2e.*`). Evaluation topics: `2x2` = evaluation/dac_2x2, `sd8g3` = evaluation/dac_sd8g3 (EV-58 pack via scripts/dac_data.py).

## Abstract  (sections/00_abstract.tex)
- **[abs-summary]**
  - Message: Speculative decoding and small batches turn decoding's GEMVs into memory-bound skinny GEMMs that suit PIM, but stock PIM, built for GEMVs, fills under a fifth of its GEMM time with useful MACs because a DRAM command paces every MAC; CoDe decouples MACs from commands (row reuse, beat filling) and buys LP-Spec-style's speed with about half its logic. Order (user-approved text, 2026-11-08): context → skinny GEMM, host memory-bound → PIM fits, stock PIM falls short → characterization (useful share, two root causes) → common cause → CoDe's two techniques → results.
  - Floats: —
  - Numbers: M 2 to 32 ← cited ranges (bg-skinny-range); useful 14.1–19.1 %, non-MAC 23.4–43.7 %, idle 42.2–57.4 % ← brk (2x2 §2j); mobile: LP-Spec-style's decoding speed on 0.539× its logic area ← tables [table4], e2e; 1.49× faster at about the same logic area (LP-Spec-style as published, 0.96× CoDe's logic, printed in I and VI-E, eval-placement) ← tables [lpsv_checks] (sd8g3 §2h); HBM2 batch of 8: 1.41× P3-LLM-style (P3-LLM's own placement, isca.e2e.hbm2.core4_over_p3own.speed; 1.68× all-PIM until 2026-11-10) and 1.28× NPU only ← e2e (sd8g3 §2f, 2x2 §2p), roof. 1.87× / 1.06× per mm², 1.52× energy, 5 / 4 ns column, four beats, 4× multipliers left the abstract (body only).
  - Cites: —
  - Links: → intro-code-proposal, mot-breakdown-setup, des-row-reuse, des-beat-decouple, eval-e2e-phone, eval-e2e-server, eval-e2e-per-mm2, eval-placement, eval-area-split

## I. Introduction  (sections/01_introduction.tex)
- **[intro-skinny-gemm]**
  - Message: Speculative decoding on a mobile platform and small batches on an edge server turn every linear layer of LLM decoding into a skinny GEMM with a few tokens per weight pass.
  - Floats: —
  - Numbers: M 2 to about 32 ← cited ranges (bg-skinny-range)
  - Cites: leviathan2023, sdnpu, lpspec, p3llm, flashdecodingpp
  - Links: → bg-skinny-range
- **[intro-host-memory-bound]**
  - Message: The host runs a skinny GEMM at the cost of a GEMV because it stays memory-bound far beyond the skinny range.
  - Floats: —
  - Numbers: ridge M ≈ 143; 42 GB/s ← roof
  - Cites: sd8g3
  - Links: → mot-host-roof
- **[intro-pim-gemv-ceiling]**
  - Message: AiM-style PIM removes the bandwidth limit but runs one MAC beat per column command, so a skinny GEMM costs M GEMVs and published systems send GEMMs back to the host.
  - Floats: Fig. 1 (first cite), Fig. 2 (first cite)
  - Numbers: 9.75× / 4× host bandwidth; crossover M = 6 (mobile), 2–3 (HBM2) ← roof
  - Cites: aimjssc, hbmpim, attacc, neupims, ianus, p3llm
  - Links: → mot-stock-crossover, mot-gemv-only, mot-idle-beats, mot-idle-cause
- **[intro-prior-families]**
  - Message: Prior PIM raises the ceiling either with more multipliers (wider PU) or with more commands (faster PU), and both families keep every MAC paced by a DRAM command.
  - Floats: —
  - Numbers: 4× multipliers; 16.92 % of an LPDDR5 die for compute units and buffers ← lpspec (cited, p. 7); two tokens per read (structural)
  - Cites: lpspec, p3llm
  - Links: → mot-wider-pu, mot-faster-pu, mot-logic-cost
- **[intro-timing-insight]**
  - Message: DRAM timing parameters space the column commands that access the array, not the MACs on a latched column, so one column period can feed D = 4 PU beats.
  - Floats: —
  - Numbers: 5 ns (LPDDR5-6400), 4 ns (HBM2) column; 1 GHz PU in silicon; 0.8 / 1 GHz; D = 4 ← cited / structural
  - Cites: hbmpim, lpspec, aimjssc
  - Links: → mot-depth, mot-pu-clock-precedent
- **[intro-code-proposal]**
  - Message: CoDe runs D beats per column command over a tile of V tokens at the stock multiplier count, and on each rival's own ground it decodes faster than LP-Spec-style on the mobile platform (46.4 against 46.1 tok/s, CoDe the subject: user 2026-11-10, CoDe leads every CoDe/LP-Spec-style sentence where its number is strictly higher) with the stock multiplier count clocked at 0.8 GHz on 0.539× its logic (1.87× per logic mm², supporting), beats LP-Spec-style as published (one unit per two banks, near-equal logic) by 1.49×, and on HBM2 decodes a batch of 8 faster than both P3-LLM-style (at P3-LLM's own placement, meth-systems; user 2026-11-10, option B) and NPU only. Never "stock multipliers" bare.
  - Floats: —
  - Numbers: 46.4 / 46.1 tok/s ← e2e; 0.539× logic area ← tables [table4]; 1.87× per logic mm²; 0.96×, 1.49× ← tables [lpsv_checks]; 1.41×, 1.28×, 1.52× (batch 8; core4_over_p3own.speed, p3own_over_core4.mJ_55W) ← e2e
  - Cites: sd8g3
  - Links: → des-tile-mac-overview, eval-e2e-phone, eval-e2e-server, eval-e2e-per-mm2, eval-placement, eval-energy
- **[intro-contributions]** (itemize, six items; claim–evidence map since 2026-11-08, user-approved AI-review item 1)
  - Message: Each item states one claim, its headline number with its scope and the section that proves it: the depth analysis (III-D); the CoDe PU and command extension (IV); on one DRAM timing per platform, CoDe decodes at least as fast as LP-Spec-style (faster on the mobile platform, equal on HBM2; never "faster" on both), 1.49× over LP-Spec-style as published (mobile platform only) and 1.41× over P3-LLM-style at batch 8 on HBM2 (P3-LLM's own placement; VI-B and VI-E, the latter for the published sharing); under one area model with one tenfold DRAM-process factor, 0.539× LP-Spec-style's logic and 2.31 % / 1.95 % of the die / stack (VI-D); the least energy per token on the mobile platform and a tie with LP-Spec-style for the least on the edge server with a 55 W idle NPU (VI-C; user fix 2026-11-08: never "least on both platforms" in I); the two sources of gain (VI-E). The limits of the former eval-modelled sentence (one DRAM timing, one 10× factor, variants phone-only) sit here, next to the claims they bound (AI-review item 2).
  - Floats: —
  - Numbers: D = 4 (LPDDR5-6400, HBM2) ← structural; 1.49× ← tables [lpsv_checks]; 1.41× ← e2e; 0.539× ← tables [table4]; 2.31 % / 1.95 % ← tables [budget_checks]; 70.5 mJ ← e2e; 1.24× / 3.49× (beat filling's total over row reuse alone, D = 1 → 4; "adds 3.49×", not "a 3.49× step": Table V's steps are per beat since 2026-11-10) ← tables [umac_src_table] (every number also printed in VI)
  - Cites: —
  - Links: → mot-depth, des-command-set, des-tile-mac-pu, eval-e2e-phone, eval-e2e-server, eval-placement, eval-area-budget, eval-area-split, eval-energy, eval-gain-sources

## II. Background  (sections/02_background.tex)
### A. Skinny GEMM in LLM Decoding
- **[bg-skinny-range]**
  - Message: Published mobile verifiers and edge-server batches put M between 2 and 32 (the datacenter trees and batches sentence cut for space, 2026-11-08; medusa / sequoia bib entries kept, uncited).
  - Floats: —
  - Numbers: M ≪ 64; 2–8 padded to 32; 1–32; 4–64; 1–8; targets M = 2–32 and 2–8 ← cited
  - Cites: flashdecodingpp, leviathan2023, eagle2, sdnpu, lpspec, lever, p3llm
  - Links: ← intro-skinny-gemm; → mot-stock-crossover
### B. DRAM and AiM-Style PIM
- **[bg-dram-channel]**
  - Message: An activation opens one row of a bank (2 KB on LPDDR5) and each column command moves one 32 B column of it (32 B stated once); column commands issue every t_CCD_S across bank groups and every t_CCD_L within one, which is twice as long.
  - Floats: Fig. 1, Table III (row size)
  - Numbers: 16 banks, four bank groups, 32 B, 2 KB row ← structural; row size in Table III ← tables [platform_block] (2x2 raw cvs_sum labels; JEDEC page size)
  - Cites: jedeclpddr5, ramulator2, p3llm
  - Links: → bg-row-sweep, mot-faster-pu
- **[bg-aim-pu]**
  - Message: AiM-style PIM puts a PU beside each bank and a shared global buffer on the die, and one all-bank MAC command every t_CCD_L starts one MAC beat in every PU; the column period spans D = 4 CK cycles (D defined here as a timing fact; the "D beats per column read" opportunity is mot-depth's, the GEMV-to-bank mapping des-mapping's); commercial PIM places its units at the banks in two ways (2026-11-10, the reference for eval-placement): Samsung's LPDDR5X-PIM one per bank, HBM-PIM one per two banks, and Samsung's LPDDR-PIM design (Hot Chips 35) offers either, one per bank for maximum performance or one per two banks for less area; the HBM2 parenthetical on the PU sentence cut (Table III keeps the platform's placement).
  - Floats: Fig. 1, Table III (first cite; configuration table, F12 exception)
  - Numbers: 32 INT8 multiplies per beat; D = 4 (Table III); D defined: CK cycles per column period, named the depth (t_col spans D cycles of t_CK, bg-dram-channel; the restated equation cut 2026-11-10) (the intro and V-C already say "depth") ← structural
  - Cites: aimjssc, hbmpim, lp5xpim (layout only: one PIM block per bank; no clock or bandwidth), hc35pim (slide 22: unit per 1 bank, maximum performance, or per 2 banks, moderate area overhead; verified by main)
  - Links: → bg-mac-sequence, mot-breakdown-setup, mot-idle-beats, mot-prior-families, mot-depth, des-beat-decouple, des-mapping, eval-placement
- **[bg-mac-sequence]**
  - Message: MAC commands need non-MAC commands before and after them: the all-bank MAC command is the only MAC command, and the non-MAC commands follow a fixed order (colon into the list): WRGB, WRMAC16, TMOD and PREA + ACT16 before the MAC commands of a row, a second TMOD and RDMAC16 after them, in the order the simulator issues them.
  - Floats: Fig. 1 (c)
  - Numbers: — (command order ← microarch 05_reports/d1/useful_mac_util.md §11.2, §11.4)
  - Cites: aimjssc
  - Links: ← bg-aim-pu; → bg-row-sweep, mot-nonmac-classes, meth-simulator
- **[bg-row-sweep]**
  - Message: A row sweep streams c all-bank MAC commands over one open row, c = row bytes / column bytes = 2 KB / 32 B = 64 (the edge server's 1 KB HBM2 rows give 64 columns over two rows opened in turn); a row sweep serves the A tokens whose inputs the GB holds, and stock AiM's row sweep serves one token (A = 1).
  - Floats: Fig. 1 (c), Table III (row size)
  - Numbers: c = 2 KB / 32 B = 64; 1 KB HBM2 rows, two per sweep ← tables [platform_block] (2x2 raw cvs_sum labels); the layer-mean 62.38 (re-opens after refresh, short last chunks) is not printed
  - Cites: jedechbm2
  - Links: ← bg-dram-channel, bg-mac-sequence; → mot-nonmac-classes, des-row-reuse

## III. Motivation  (sections/03_motivation.tex)
### A. PIM–Host Crossover
- **[mot-roofline-setup]**
  - Message: Fig. 2 plots skinny-GEMM throughput against M in the roofline form for the host NPU's roof and for simulated PIM GEMMs of stock AiM and each platform's rival; order (figure-paragraph rule): what the figure shows → basic setup (geometric mean over the FC shapes, M = 2^k) → details (mobile NPU bandwidth, edge NPU); the closing pointer to Table III and Section V cut 2026-11-10 (Table III first cited in bg-aim-pu).
  - Floats: Fig. 2
  - Numbers: M = 2^k; 56 of 68 GB/s, 51.2 GB/s pins → 42 GB/s [assumption] ← cited; 42 asserted in roof; the edge NPU's 131 TOPS / 256 GB/s in Table III ← tables [platform_block]
  - Cites: roofline, sd8g3, powerinfer2, heterollm, p3llm
  - Links: ← bg-aim-pu (Table III first cite)
- **[mot-host-roof]** "Host roof in the skinny range"
  - Message: The host stays memory-bound across the whole skinny range because both NPUs' ridge points sit far above M = 32, so the host's roof rises linearly with M across the skinny range.
  - Floats: Fig. 2
  - Numbers: ridge M ≈ 143 and M = 128 ← roof
  - Cites: p3llm (sd8g3 cited once, in mot-roofline-setup)
  - Links: ← intro-host-memory-bound; → mot-gemv-only, mot-a-summary
- **[mot-stock-crossover]** "Stock-PIM crossover"
  - Message: Stock PIM beats the host only for the first few token rows, because stock AiM repeats the GEMV once per token row, so its GEMM time grows in proportion to M and the host's rising memory roof overtakes its flat ceiling below most published M.
  - Floats: Fig. 2
  - Numbers: 9.75× / 4× at M = 1; crossover M = 6 and 2–3 ← roof; GEMM time ∝ M (tolerance asserted, not printed) ← tables [stock_checks]
  - Cites: —
  - Links: ← intro-pim-gemv-ceiling, bg-skinny-range
- **[mot-gemv-only]** "GEMV-only use of PIM"
  - Message: Published PIM systems keep PIM for GEMVs and send the GEMMs to the host or NPU, even though the host runs every skinny GEMM on its memory roof (back-pointer to mot-host-roof); one sentence lists AttAcc, NeuPIMs, IANUS, P3-LLM (NeuPIMs quote cut, 2026-11-08); the A → B transition moved to mot-a-summary.
  - Floats: —
  - Numbers: batch 8 (P3-LLM offload) ← cited
  - Cites: attacc, neupims, ianus, p3llm
  - Links: ← intro-pim-gemv-ceiling, mot-host-roof; → mot-a-summary, meth-systems (the evaluation's NPU + P3-LLM-style follows this placement on the edge server, 2026-11-10), eval-e2e-server
- **[mot-a-summary]**
  - Message: Closing A summary and A → B transition (no heading): skinny GEMMs are memory-bound on the host and so belong on PIM, which reads the weights inside the DRAM, yet stock PIM's GEMM throughput stays flat at its GEMV ceiling; III-B splits a stock GEMM's time to locate the cause (summary sentence cut 2026-11-10 in e92f99e, restored by the user the same day).
  - Floats: —
  - Numbers: —
  - Cites: —
  - Links: ← mot-host-roof, mot-stock-crossover, mot-gemv-only; → mot-breakdown-setup
### B. Two Root Causes of Stock PIM Inefficiency
- **[mot-breakdown-setup]**
  - Message: Useful MAC work fills at most a fifth of a stock GEMM's time, and non-MAC commands and idle beats take the rest; order (figure-paragraph rule): what Fig. 3 shows → kernels → platforms (INT8 / W4A8 PU placement; the attribution of each precision to its rival lives in meth-platforms and Table III since 2026-11-08) → the two groups (non-MAC commands; MAC slots of useful and idle beats; MAC slot t_slot defined here) → finding → transition to the two root causes (non-MAC commands, then idle beats). Per-segment explanations live in B2–B7, U in mot-utilization.
  - Floats: Fig. 3 (first cite; float defined after this paragraph), Fig. 1 (b), Table III
  - Numbers: one tile 2048 × 64 / 4096 × 256 (one row sweep per bank, one GB chunk); q_proj 4096 × 4096; M = 8, one channel; useful 14.1–19.1 %, non-MAC 23.4–43.7 %, idle 42.2–57.4 % ← brk (2x2 §2j; the ≤ 0.015 % stalls stay a guard assert only)
  - Cites: —
  - Links: ← bg-aim-pu, bg-row-sweep, mot-a-summary; → mot-nonmac-classes, mot-idle-beats, mot-utilization
- **[mot-nonmac-classes]** "1) Non-MAC commands" (numbered bold run-in head over mot-nonmac-classes … mot-sweep-factor)
  - Message: Every row sweep pays a fixed set of non-MAC commands, and stock AiM pays the set for every token: plain opener (non-MAC commands stall every PU: no PU starts a MAC while they run) → Fig. 3's four non-MAC segments form three classes of II-B's commands (row-switch commands cost t_row once per row sweep; token load/drain commands cost t_tok once per token; refresh blocks commands for t_RFCab every t_REFI) → with one token per stock row sweep (A = 1, II-B), a GEMM pays a row's row-switch commands M times, a GEMV once.
  - Floats: Fig. 3, Fig. 1 (c), Table III
  - Numbers: — (structural)
  - Cites: —
  - Links: ← mot-breakdown-setup, bg-mac-sequence (commands defined there; III-B only groups them into classes), bg-row-sweep; → mot-rowswitch-cost, mot-sweep-factor, mot-other-pim (closing: a row sweep serves one MAC slot's tokens), des-row-reuse
- **[mot-rowswitch-cost]**
  - Message: Row-switch commands are the largest non-MAC class, and on the mobile platform they outlast the useful beats; token load/drain and refresh take less, and on the edge server only all non-MAC commands together outlast the useful beats (absorbs the former mot-load-refresh-cost; q_proj shares only, no ns values).
  - Floats: Fig. 3 (row-switch, token-load, token-drain, refresh segments)
  - Numbers: q_proj shares: row switch 19.5 / 13.8 %, useful 18.0 / 19.1 %; mobile TMOD 8.1 %, ACT16 pair 8.5 % (simulator preset; 8.545, not 8.6); token load / drain at most 2.4 / 1.0 %; 64 / 16 row sweeps per GB fill; refresh 7.1 / 6.2 %; edge non-MAC total 23.4 % vs useful 19.1 % ← brk (2x2 §2j, §2p; tab_umac_kernel_stock.csv). The former ns values (91.2 vs 78.0, TMOD 40.5, ACT16 37.9, PREA 11.5, WRMAC16 1.2; edge 146.2 incl. 41.8 vs 123.3) stay guard-only asserts in tables [umac_src_table]
  - Cites: —
  - Links: ← mot-nonmac-classes; → mot-sweep-factor, mot-two-levers, meth-simulator (refresh)
- **[mot-sweep-factor]**
  - Message: The paper defines the sweep factor f_MAC as the share of GEMM time the MAC slots get, set by the non-MAC commands through Eq. 1 (c, A from II-B; t_slot from mot-breakdown-setup; t_row, t_tok from mot-nonmac-classes; ρ defined here); one mobile case study gives stock AiM's 0.717 (no own heading; under "1) Non-MAC commands").
  - Floats: Eq. 1 (eq:fmac)
  - Numbers: mobile case study only: t_row 87.73 ns, t_tok 4.26 ns, ρ 0.070 (ρ relied on by meth-simulator) → f_MAC 0.717 of a decoder layer's time ← tables [umac_table, umac_src_table]; edge fit values (94.76, 9.64, 0.061) and the 91.2 ns MAC-tail sentence cut (guard-only asserts)
  - Cites: —
  - Links: ← mot-nonmac-classes, mot-rowswitch-cost; → mot-utilization, meth-simulator
- **[mot-idle-beats]** "2) Idle beats" (numbered bold run-in head over mot-idle-beats and mot-idle-cause)
  - Message: Even inside the MAC slots three of every four beats are idle: plain opener (an idle beat is a CK cycle in which a PU has nothing to compute) → a column period holds D = 4 such cycles, or beats (II-B); a beat is useful when it computes a token's MAC → stock's slot serves one token, so one beat per column period is useful and three are idle (Fig. 1b) → slot factor U_MAC = A × b × t_CK / t_slot = 1/4 (b defined here) → Fig. 3's idle segment.
  - Floats: Fig. 1 (b), Fig. 3 (MAC-idle segment)
  - Numbers: U_MAC = 1/4 (b = 1 mobile, 2 edge server); D from II-B (not derived here); idle 53.9 % / 57.4 % of q_proj, three times the useful beats ← brk
  - Cites: —
  - Links: ← bg-aim-pu, mot-breakdown-setup; → mot-idle-cause, mot-utilization, mot-depth, mot-two-levers, des-beat-decouple
- **[mot-idle-cause]**
  - Message: Idle beats arise because the column command, not the PU, paces every stock MAC (opener states the cause directly; a MAC starts only when a column command delivers its weights) → HBM-PIM / AiM pacing → each column command reads one column and DRAM timing spaces them by t_CCD_S / t_CCD_L → a GEMV needs one beat per column → evidence: a PU four times faster, at CK, leaves every stock GEMM at the same cycle count (paragraph ends there; never named "faster-PU").
  - Floats: —
  - Numbers: four times faster PU, same cycle count ← tables [stock_checks]
  - Cites: hbmpim, aimjssc, p3llm (GEMV target: JSSC p. 1, P3-LLM p. 3)
  - Links: ← mot-idle-beats; → mot-depth, des-beat-decouple
- **[mot-utilization]**
  - Message: Non-MAC commands and idle beats multiply into stock AiM's useful-MAC utilization of below a fifth: plain opener ("The two losses multiply.") → U = W × t_CK / T_GEMM against a PU that runs one useful beat per CK cycle (Fig. 3's MAC-useful segment) → U = U_MAC × f_MAC → stock values → transition to III-C (III-C examines how prior PIM designs answer each root cause).
  - Floats: Table I (first cite; float defined inside this paragraph), Fig. 3
  - Numbers: U = 1/4 × 0.717 = 0.179 (mobile); edge U 0.193 (also Table V) ← tables [umac_table]
  - Cites: —
  - Links: ← mot-breakdown-setup, mot-sweep-factor, mot-idle-beats; → mot-prior-families, mot-wider-pu, mot-two-levers, des-tile-mac-overview
### C. Related Work: GEMM Support in PIM
- **[mot-prior-families]**
  - Message: Prior PIM designs fill the idle beats in two families, with more multipliers or with more commands; Fig. 4 follows one weight column through eight tokens in stock AiM and one design of each family (LP-Spec, P3-LLM) (pure framing opener; the 'next paragraphs' map cut 2026-11-10; the figure's setup and counts moved into mot-wider-pu and mot-faster-pu; the row-sweep claim lives in mot-other-pim's closing; Fig. 4's CoDe row is explained in des-beat-decouple).
  - Floats: Fig. 4 (first cite; fig:timeline, float defined after mot-wider-pu)
  - Numbers: — (eight tokens, structural)
  - Cites: lpspec, p3llm
  - Links: ← intro-prior-families, mot-utilization; → mot-wider-pu, mot-faster-pu
- **[mot-wider-pu]** "Wider-PU family"
  - Message: Wider-PU designs trade area for MAC throughput by filling the idle beats with more multipliers per PU (opener), so LP-Spec-style, the mobile rival, reaches U_MAC = 1 only by quadrupling the multipliers, and per multiplier its U stays below stock AiM's (closing). LP-Spec shares one unit between two banks; we give LP-Spec-style one unit per bank on the mobile platform (on HBM2 every design shares one PU between two banks, Table III), SK hynix AiM's layout (aimjssc) and Samsung's maximum-performance option (hc35pim), and VI-E (eval-placement) evaluates the published sharing (2026-11-10; the per-bank design is the main rival everywhere; never "stronger": per mm² the shared variant narrows CoDe's lead to 1.42×).
  - Floats: Fig. 4 (column periods T of D = 4 beats defined for reading it), Fig. 2, Table I, Table IV
  - Numbers: four 32-wide ALUs, one MAC step per column period (200 MHz → Table IV); Fig. 4 counts: stock 8 column periods / 8 commands / 8 reads, LP-Spec 2 / 2 / 2 (M = 8, D = 4 from II-B) ← structural; crossover M = 20–24; U per multiplier 0.173–0.174 / 0.185 ← roof, tables [umac_table]
  - Cites: lpspec, aimjssc, hc35pim, papi, stepstone, duplex, h2llm, monde
  - Links: ← intro-prior-families, mot-prior-families, mot-idle-beats; → mot-logic-cost, mot-two-levers (area a PIM die gives to beat filling), eval-gemm-summary (ref → Section VI since 2026-10-30), eval-placement
- **[mot-logic-cost]** "Cost of logic in a DRAM die"
  - Message: Logic in a DRAM die costs capacity, so per logic mm² the wider-PU family keeps only part of its four-fold ceiling over stock AiM; one sentence reconciles LP-Spec's own 16.92 % with our LP-Spec-style's 4.28 %: LP-Spec's estimate includes register files of 50,688 bits per matrix unit, our model keeps only the accumulators its dataflow needs, which favours LP-Spec-style ("includes", never "mostly"; 9.80 / 12.08 mm² never printed: 16 vs 8 register-file sets unresolved, sd8g3 context §5 row 40).
  - Floats: Table IV (4.28 % = its 2.610 mm² over V-C's 60.92 mm² die, meth-area-model; the VI-D print of the share was cut 2026-11-10, user review 2)
  - Numbers: 10× less dense, 3 vs 10+ metal layers (UPMEM's report, devaux); 0.19 mm² per PU; 50 % capacity ← hbmpim (halved sub-arrays, p. 8); 16.92 % for compute units and buffers (lpspec p. 7) vs 20–25 % ← cited; 16.92 asserted from budget.lpspec_own.pct_of_die_1z, 50,688 bits ← budget.lpspec_own.rf_bits_per_mpu, 4.28 % ← budget.phone.h2.pct_of_die_1z ← tables [lpsv_checks, budget_cells] (pointer: Table IV; this is now the share's only print); LP-Spec-style 314 / 697 vs stock AiM 216 / 492 GOPS/mm² ← roof
  - Cites: devaux, aimjssc, hbmpim, lpspec
  - Links: ← intro-prior-families, mot-wider-pu, meth-area-model (die area); → eval-gemm-per-mm2, eval-e2e-per-mm2, eval-area-budget (AiM's 20–25 % printed here only; VI-D points back)
- **[mot-faster-pu]** "Faster-PU family"
  - Message: Faster-PU designs speed up the PU but still start every MAC with a command, so DRAM command timing, not the PU clock, caps them at two beats per column read (opener; the user's top point in this paragraph): commands issue every t_CCD_S, half of t_CCD_L, so P3-LLM-style, the edge-server rival, stops at U_MAC = 1/2 however fast its PU runs, yet keeps a higher ceiling per logic mm² than LP-Spec-style. P3-LLM shares one PU between two banks (stated like LP-Spec's placement in mot-wider-pu; p3llm p. 7, Sec. IV-A: "8 PCUs, each of them is shared by 2 banks").
  - Floats: Fig. 4 (P3-LLM row), Fig. 2, Table IV, Table III (placement row)
  - Numbers: one beat per t_CCD_S (500 MHz → Table IV); one PU per two banks ← p3llm p. 7; Fig. 4 counts 4 column periods, 8 commands, 4 reads ← structural; U_MAC stops at 1/2 wherever t_CCD_L = 2 t_CCD_S; crossover M = 4–6; 390 / 830 GOPS/mm² ← roof
  - Cites: p3llm, hbmpim
  - Links: ← bg-dram-channel, intro-prior-families, mot-prior-families, mot-idle-beats, mot-logic-cost; → mot-depth (the per-token command is what a PU at CK must drop), eval-gemm-summary (ref → Section VI since 2026-10-30)
- **[mot-other-pim]**
  - Message: The remaining LLM PIM designs either serve one input vector per weight read or reorganize the work around the PU, and the three that run several beats per column read still hold one vector (CD-PIM's host-GEMM clause cut 2026-11-10; the Precision-Flexible PU spends a column interval's four phases on the low-bit weights packed in one column, pfpu pp. 2–3, user review 2); closing C → D transition: across the two families and these three designs, a column read feeds several tokens only through added multipliers or added commands, and a row sweep serves only one MAC slot's tokens; novelty delta joined to it by a colon (AI-review T2, 2026-11-08): none of these designs, P3-LLM's two-token latch included, lets a larger tile share one row sweep and pay its row-switch commands once, or fills the idle beats with its tokens without added multipliers or commands (levers not named here: mot-two-levers names them).
  - Floats: —
  - Numbers: —
  - Cites: newton, cent, pimgpt, localut, pimpal, pimdl, pimba, paise, splitsync, dots, pimphony, salpim, pfpu, cdpim (paik2022 cut 2026-10-29; bib entry kept, uncited)
  - Links: ← mot-wider-pu, mot-faster-pu, mot-nonmac-classes (closing's row-sweep claim; the former "Row-switch commands in prior designs" paragraph was cut 2026-10-29); → mot-depth, des-row-reuse (stays last in III-C: user, 2026-10-27)
### D. The Opportunity: DRAM Timing Bounds Access, Not MACs
- **[mot-depth]**
  - Message: DRAM timing bounds how often a column is read, not how many MACs may consume it (opener); the PU's latched column stays usable after its command, so the column period sets how often weights arrive and the PU clock how often the PU computes, and a PU clocked at CK can spend all D beats of a column period on one latched column, as long as its MACs do not wait for per-token commands (conclusion; answers mot-faster-pu).
  - Floats: —
  - Numbers: — (D points back to bg-aim-pu; not re-derived)
  - Cites: hbmpim, p3llm
  - Links: ← intro-timing-insight, bg-aim-pu, mot-idle-beats, mot-idle-cause, mot-faster-pu, mot-other-pim; → conc-summary
- **[mot-pu-clock-precedent]** (no run-in head since 2026-10-29; III-D is three unheaded paragraphs)
  - Message: A PU clocked at CK has precedent in DRAM silicon, from UPMEM's 500 MHz design (350 MHz deployed) to GDDR6-AiM's 1 GHz multipliers and an HBM-PIM-style PU at CK (the Precision-Flexible PU, whose four phases serve the low-bit weights packed in one column for one input vector, so its gain is set by packing; user 2026-11-10, AI-review novelty concern), and DRAM periphery has since gained logic-process features (HKMG at three vendors, 5–6 metal layers on 1a-nm dies); never "a PU at CK is the trend", never the vendors' pin-rate speed claims.
  - Floats: —
  - Numbers: 1.0–1.2 GHz bus, 250–300 MHz, 20 nm; 500 MHz design, 2x-nm; 350 MHz deployed ← prim (p. 5); 1 GHz, 1y-nm; eight 1y-nm dies; five to six metal layers, 1a-nm ← tid1a16, tid1a24 ← cited
  - Cites: hbmpim, devaux, prim, aimjssc, flashbolt, pfpu, tiroadmap, tid1a16, tid1a24
  - Links: ← intro-timing-insight; → mot-two-levers, des-pu-clock
- **[mot-two-levers]**
  - Message: A PU at CK fits in a DRAM die, and the wider-PU family shows how much logic area a PIM die already gives to filling idle beats, so we keep the stock multiplier count, run it at CK within that area, and answer each root cause of III-B with one lever (opener): row reuse (IV-B) answers the non-MAC commands by cutting their time per token (no claim that row reuse raises f_MAC; the rival contrast lives in des-row-reuse); beat filling (IV-C) uses all D beats of a column period without adding multipliers and answers the idle beats (III-B's order, since 2026-10-29). "Within that area" checked against Table IV: CoDe's logic 1.406 vs LP-Spec-style 2.610 mm² per die (0.539×), 0.821 vs 1.469 mm² per pCH (0.56×); proved in eval-area-split.
  - Floats: Fig. 1
  - Numbers: D = 4 beats per column read, one used ← structural; no CoDe number
  - Cites: —
  - Links: ← mot-idle-beats, mot-nonmac-classes, mot-rowswitch-cost, mot-depth, mot-pu-clock-precedent, mot-logic-cost; → des-tile-mac-overview, des-row-reuse, des-beat-decouple, eval-area-split

## IV. CoDe Design  (sections/04_design.tex)  — mirrors III: IV-A one mechanism, IV-B ↔ III-B non-MAC commands, IV-C ↔ III-B idle beats (III-B's order; row reuse first since 2026-10-29); each component paragraph: cause recalled → mechanism → contrast with the III-C family → effect in Fig. 6
### A. Overview: One Command, Many MAC Beats
- **[des-tile-mac-overview]**
  - Message: One tile MAC per weight column for V tokens of a skinny GEMM carries both levers (row reuse, then beat filling); both come from the tile, whose inputs a global buffer extended from one input vector to V holds (the why-clause cut 2026-11-08; V ≥ D lives in des-tile-size), while every command keeps every DRAM timing parameter; Fig. 5 groups the PU's structures by lever (staging buffer, accumulator file, burst drain → row reuse; weight latch, beat sequencer → beat filling).
  - Floats: Fig. 5 (fig:tile, first cite; its two brackets), Table I (CoDe row)
  - Numbers: U 0.779 (mobile) against stock 0.179 ← tables [umac_table]; CoDe's 583 / 1,247 GOPS/mm² ceilings no longer printed (left with eval-phone-per-mm2 / eval-server-area, 2026-10-30); both-order gains left IV (eval-gain-sources is their only home); the old Fig. 5 walk-through sentence cut with fig:sequence
  - Cites: —
  - Links: → des-row-reuse, des-beat-decouple, des-tile-mac-pu, eval-gain-sources
### B. Row Reuse
- **[des-row-reuse]**
  - Message: Row reuse answers III-B's non-MAC commands by letting a tile's V tokens share one row sweep, so the row-switch commands are paid once per V tokens set by V rather than by one MAC slot as in the rivals (A = 2 and 4, Table I, pointed to from the families of III-C), and the non-MAC time per token falls (absolute form; never "raises f_MAC"); Fig. 6a defines the tile in GEMM terms (V tokens × one K chunk in the GB, one bank's 2 KB row = one output's weights, V sums), Fig. 6b's lanes show stock AiM paying a row switch and a drain per token against one row switch per tile.
  - Floats: Fig. 6 (fig:mapping, first cite; a, b lanes and table), Table I
  - Numbers: M = V = 8; 2 KB row; row opens 8 → 1, column reads 512 → 64 ← map; t_row / A + t_tok plus refresh per token (the storage-needs sentence cut 2026-11-08; des-storage carries it); non-MAC time per token 123.39 → 22.15 ns (mobile, V = 8), 146.17 → 43.51 ns (edge server, V = 4) ← tables [umac_table] (row-reuse-only 2,629 ns cut with fig:sequence; 3,250 → 738.75 ns, 4.40× moved to des-beat-slot-factor; 4.32× whole-GEMM asserted in map only)
  - Cites: —
  - Links: ← mot-nonmac-classes, mot-other-pim (closing), mot-two-levers; → des-storage, eval-gain-sources
### C. Beat Filling
- **[des-beat-decouple]**
  - Message: Beat filling answers III-B's idle beats by running the PU's beats at its own clock f_PU = D / t_col, so a tile MAC holds its column for V/D periods while the PU runs one beat per token (walked on Fig. 6b's enlarged tile MAC: one read → 8 beats, 4 per column period, burst drain after the last column; the V/D = 2 restatement cut 2026-11-08).
  - Floats: Table III (CK), Table IV (PU clock), Fig. 6 (b, zoom)
  - Numbers: V = 8, D = 4, V/D = 2 periods ← structural (asserted in map)
  - Cites: —
  - Links: ← mot-idle-beats, mot-idle-cause, mot-two-levers
- **[des-beat-slot-factor]**
  - Message: Beat filling raises the slot factor from 1/4 to 1, reaching the wider-PU family's 4× ceiling with the stock multiplier count and fewer MAC commands per token than the faster-PU family; joined with row reuse it makes the weight row 4.40× shorter (Fig. 6b's speedup gap).
  - Floats: Fig. 4 (family comparison, CoDe lane), Fig. 6 (b, table and speedup gap)
  - Numbers: 1/V MAC commands per token and column vs 1 (stock, P3-LLM-style), 1/4 (LP-Spec-style) ← structural; time in MAC slots 512 → 128 column periods for the same 8 × 64 MAC beats (the figure's "MAC time" column; CoDe's slot is 10 ns, so never "128 MAC slots"); weight row 3,250 → 738.75 ns, 4.40× ← map (2,560 → 640 ns and 1,360 ns cut with fig:sequence; the two-structures sentence moved to des-tile-mac-overview)
  - Cites: —
  - Links: ← mot-idle-beats, mot-wider-pu, mot-faster-pu; → eval-gemm-speed, eval-gain-sources
### D. Tile MAC Command and PU Microarchitecture
- **[des-command-set]** "Command set"
  - Message: CoDe adds the tile MAC and the burst drain to AiM's all-bank interface and keeps every other command.
  - Floats: Table II (first cite; tab:cmds)
  - Numbers: — (Table II ← map)
  - Cites: aimjssc
  - Links: ← intro-contributions
- **[des-tile-mac-pu]** "Tile MAC in the PU"
  - Message: Inside the PU a tile MAC latches the column, and a beat sequencer steps the V tokens through the lanes into their accumulator slots before a burst drain.
  - Floats: Fig. 5
  - Numbers: lanes (Table IV) ← structural
  - Cites: —
  - Links: ← intro-contributions, des-tile-mac-overview
- **[des-storage]** "Storage"
  - Message: The global buffer, the staging buffer and a double-set accumulator file hold the tile's inputs and partial sums.
  - Floats: Table IV
  - Numbers: 2,048 INT8 inputs, 2 KB per token, 16 KB GB, 512 writes of 32 B ← map; three-entry queue of 512-bit words; two / four sets of V slots ← structural (Table IV ← tables [table4])
  - Cites: —
  - Links: ← des-row-reuse
- **[des-tile-size]** "Tile size"
  - Message: The tile size V sizes only CoDe's storage (GB, HBM2 staging register, accumulator file; one sentence since 2026-11-08), so V is set by the range of M a platform serves: V = 2D = 8 on the mobile platform and V = D = 4 on HBM2 (the reason for V = 4 printed here only).
  - Floats: —
  - Numbers: V = 8 / 4; 4 KB K chunk, 512-bit slice ← structural
  - Cites: —
  - Links: → eval-vsweep-gain, eval-vsweep-choice
- **[des-pu-clock]** "PU clock"
  - Message: CoDe needs a PU clock above the column rate, not one equal to CK, and the tile keeps that clock within the reach of III-D's DRAM silicon: the PU pipelines its beats (operand registers for the latched column and token k's staging slice, multiply, registered adder-tree stages, accumulate; stages as in the synthesised RTL, microarch 03_tools/d1/synth/run_power.py gen_int / pipe_latency; AI-review T5, 2026-11-08), only the accumulate feeds back and each accumulator slot takes one update per V ≥ D beats, and the lanes multiply narrow integers (the grows-with-V closing sentence cut 2026-11-08).
  - Floats: —
  - Numbers: — (precedent and its citations live only in mot-pu-clock-precedent)
  - Cites: —
  - Links: ← mot-pu-clock-precedent; → meth-designs (PU clock in Table IV), eval-power-headroom, eval-power
### E. Mapping Skinny GEMMs and Attention
- **[des-mapping]**
  - Message: CoDe maps a skinny GEMM as stock AiM does but cuts the M token rows into tiles of V, and speculative-decoding attention maps the same way while batched attention stays one GEMV per request.
  - Floats: —
  - Numbers: —
  - Cites: —
  - Links: → eval-gemm-speed, eval-e2e-phone (attention runs inside the end-to-end systems)

## V. Methodology  (sections/05_methodology.tex)
### A. Hardware Platforms
- **[meth-platforms]**
  - Message: Each platform follows the published setup of the rival that targets it (the so-that clause cut 2026-11-08): the mobile platform takes x64 LPDDR5-6400 and INT8 from LP-Spec (its Snapdragon 8 Gen 3 host and NPU replace LP-Spec's modelled NPU), and the edge server takes its NPU, HBM2 and W4A8 from P3-LLM (P3-LLM's W4A8KV4P8 scheme), with one HBM2 stack (Table III). Verified 2026-11-06: LP-Spec Sec. III / VI-A (x64 LPDDR5, 4 x16 dies, 51.2 GB/s, INT8; its NPU is a 41 TFLOPS model of commercial products); P3-LLM Sec. VI (4-core NPU after [27], 16 pseudo HBM channels, HBM2 t_CCD_S, W4A8KV4P8).
  - Floats: Table III (platform table, F12 exception; float defined after this paragraph, lands p7 R top in the ACM build; the design block left for Table IV, 2026-11-06)
  - Numbers: platform block (NPU 12 / 131 TOPS, 42 / 256 GB/s; LPDDR5-6400 / HBM2 2.0 Gb/s; 4 dies × 16 / 16 pCH × 16 banks; 409.6 / 1,024 GB/s; t_CK 1.25 / 1 ns; t_CCD_S, t_CCD_L 2.5, 5 / 2, 4 ns; PU per bank / per two banks; t_REFI, t_RFCab 3.906 µs, 280 ns / simulator preset; INT8 / W4A8) ← tables [platform_block] (dac_sd8g3 ev57_host, ev57_ceilings, ev56_mech_inputs, context.md; dac_2x2 ev57_host, ev57_ceilings, dacp_inputs, dac2x2_setup, utrace_run_core8_gbfill; EV-58 dac_table4) and cited spec values; prose: 12 TOPS for INT8 [assumption], 131 TOPS peak [assumption]; 30 µs [assumption] ← npufaster; 2.285 W [assumption] ← derived from cites, no script; 55 W [assumption] ← tpuv4i
  - Cites: lpspec, p3llm, sd8g3, hao2025, npufaster, heterollm, tman, tpuv4i; Table III's Precision row cites lpspec / p3llm
  - Links: ← bg-aim-pu, mot-roofline-setup
### B. PIM Designs
- **[meth-designs]** (label sec:method:designs; was meth-designs-area until 2026-11-06: the area comparison moved to eval-area-split)
  - Message: Each platform carries four designs on one controller at the platform's precision (Table III), and Table IV lists each design's lanes, PU clock, D, V, accumulator slots and GB size; stock AiM also stands for Samsung's per-bank LPDDR5X-PIM (layout only, as in bg-aim-pu; AI-review T4, 2026-11-08); "on both platforms" after the V pointer cut for space; design facts only; area priced at each platform's precision, INT8 on the mobile platform and INT4 × INT8 on HBM2 (2026-11-10; dac_sd8g3 context row 44: phone areas are INT8 × INT8) [assumption]; one pointer to IV-D and VI-E for V (the V = 8 / V = D = 4 sentence cut 2026-11-08: Table IV and des-beat-decouple carry it).
  - Floats: Table IV (first cite in V; float defined after meth-area-model), Table III (precision)
  - Numbers: — (V in Table IV ← tables [table4])
  - Cites: aimjssc, lp5xpim (layout only)
  - Links: ← des-tile-size, des-pu-clock, bg-aim-pu; → eval-vsweep-gain (V sized in VI-E)
### C. Simulator and Models
- **[meth-simulator]** (label sec:method:models on V-C)
  - Message: A cycle-level AiM simulator on Ramulator 2.0 times every design's commands, including JEDEC refresh, and reproduces P3-LLM's own depth-2 step gain.
  - Floats: —
  - Numbers: 1.78× vs 1.6× ← tables [phone_levels]; U 0.355 → 0.351 (glossed "useful-MAC utilization", pointer to III-B) ← tables [umac_table]; t_REFI / t_RFCab → Table III [assumption]; refresh 7.0 % of stock AiM's time at M = 1 (ρ 0.070, fitted in III-B, Eq. 1; no symbol printed) ← tables [umac_table]
  - Cites: ramulator2, cent, p3llm
  - Links: ← mot-rowswitch-cost (refresh), mot-sweep-factor (ρ)
- **[meth-area-model]** (split from meth-simulator, 2026-11-06)
  - Message: Logic area comes from 45 nm synthesis scaled to 1z by AttAcc's estimated GEMV unit (an estimate carrying UPMEM's tenfold density penalty), with fixed control per PU and the GB as DRAM-process SRAM; AiM's fabricated 0.19 mm² PU is 2.24× our model of it, so VI-D also scales logic and registers by 2.24 as an upper bound; die shares divide by a 60.92 mm² 16 Gb LPDDR5 die (as LP-Spec reports) and by a stack of eight 84.4 mm² HBM-PIM dies standing in for plain HBM2 dies [assumption].
  - Floats: —
  - Numbers: 0.19 mm² (aimjssc p. 297); 2.24 ← budget.silicon_factor.aim; 60.92 mm² ← budget.cite.lpddr5_die_mm2_1z (LP-Spec p. 7; its ISSCC'21 origin unread, so never cited directly); 8 × 84.4 mm² ← budget.cite.hbmpim_die_mm2, budget.hbm2.stack_mm2 ([A-XC4]) ← tables [budget_checks] (sd8g3 §2g, 2x2 §2q)
  - Floats: — (Table IV tab:designs float defined after this paragraph since 2026-11-08; lands p8 L top in the ACM build)
  - Cites: attacc, devaux, aimjssc, lpspec, hbmpim
  - Links: → eval-area-budget, eval-area-split, eval-gemm-per-mm2, eval-vsweep-area, intro-contributions (one tenfold factor, limitation; moved from eval-modelled 2026-11-08)
- **[meth-power-model]** (split from meth-simulator, 2026-11-06)
  - Message: PU power and energy come from whole-PU synthesis calibrated to CENT's AiM MAC energy at 1.05 V; energy per token charges MACs, leakage, GB reads and DRAM commands; peak power runs every PU at its full MAC rate with leakage, GB reads and the column fetch but without activation, refresh, background or I/O power, which every design draws alike, so peak power isolates the logic each design adds; CoDe adds clock gates (accumulator slots, staging words, weight latch); the rivals' gating is not stated in the paper (user, 2026-11-06); yardsticks: a full-rate x16 LPDDR5X read 447 mW, an HBM2 stack read 8.0 W.
  - Floats: —
  - Numbers: Nangate45, 1.05 V; 87.6 / 54.8 mW fetch ← tables [table_power]; 447 mW ← budget.cite.lpddr5x_read_mW_per_x16_ch (Micron Y52Q Rev. G Table 16); 8.0 W at 3.92 pJ/bit ← budget.cite.hbm2_stack_read_W, budget.cite.hbm2_access_pJ_per_bit (O'Connor p. 43) ← tables [budget_checks]
  - Cites: abc, openroad, cent, horowitz, micronlp5x, oconnor
  - Links: ← des-pu-clock; → eval-energy, eval-power
### D. Algorithms and Workloads
- **[meth-workloads]** (label sec:method:work)
  - Message: The mobile platform runs speculative decoding of Llama-2-7B with a 1.1B draft (the EAGLE-head sentence cut 2026-11-10 with VI-E's EAGLE clause, its only reader; eagle bib entry kept, uncited) and the edge server batched decoding of five LLMs at a 4K context; GEMMs use six FC shapes (mobile) and 25 (edge server); end to end every system runs M = 4 (mobile) and batch 8 (edge server).
  - Floats: —
  - Floats: — (Fig. 7 fig:gemm, one column, float defined after this paragraph since 2026-11-08, lands p8 R top, VI-A's page; Fig. 8 fig:e2e figure* defined right after it since 2026-11-10, so that it renders at the top of p9, VI-B's page)
  - Numbers: acceptance 0.7; L = 1024; M = 4, batch 8; six / 25 FC shapes ← configuration (sd8g3 §2f, 2x2 §2p)
  - Cites: —
  - Links: → eval-gemm-summary, eval-e2e-phone, eval-e2e-server
- **[meth-systems]** (split from meth-workloads, user 2026-11-06)
  - Message: The five systems: NPU only runs the whole model on the NPU; in NPU + X, PIM design X runs every weight GEMM and attention layer and the NPU runs the element-wise work; the one exception (user, 2026-11-10, option B, after a reviewer's "a configuration P3-LLM would not run"): on the edge server NPU + P3-LLM-style follows P3-LLM's placement at batch 8, the NPU running the linear layers and P3-LLM-style the attention layers (P3-LLM p. 13). CoDe keeps every layer on PIM; the per-class-best placement (1.24×, 0.93× per mm²) is never printed.
  - Floats: —
  - Numbers: batch 8 ← configuration
  - Cites: p3llm
  - Links: ← meth-designs (the four designs X), mot-gemv-only; → eval-e2e-phone, eval-e2e-server, eval-energy
### E. Metrics
- **[meth-metrics]**
  - Message: GEMM speed is operations over time including the output drain, relative to stock AiM; end-to-end speed is tokens per second, relative to NPU only; area efficiency divides either throughput by the PIM logic area (Table IV); energy is system energy per token; edge-server values are geometric means over the five models (the C-bus counting rule and the M / L range rule left with eval-server-beats and VI-A's old ranges).
  - Floats: Table IV
  - Numbers: —
  - Cites: —
  - Links: → eval-gemm-summary, eval-e2e-phone

## VI. Evaluation  (sections/06_evaluation.tex)  — restructured 2026-10-30 (user): A GEMM level (Fig. 7), B end to end (Fig. 8), C energy and peak power (with the power headroom of all-bank PIM, 2026-11-06), D area against silicon budgets (2026-11-06), E ablation, F beat filling on newer DRAM (2026-11-10, user-approved brief); LP-Spec-style's comparison headline is throughput per logic mm² wherever it appears
- **[eval-modelled]** (fairness in one place since 2026-11-08, user-approved AI-review item 4; the limits moved to intro-contributions)
  - Message: All results are modelled and ratios above 1 favour CoDe; three modelling choices favour the rivals, each with a pointer to its original statement: LP-Spec-style keeps only the accumulators its dataflow needs (mot-logic-cost, "a reading that favours LP-Spec-style") and runs one unit per bank on the mobile platform, faster than LP-Spec's shared unit (eval-placement; speed only, never "stronger"), and P3-LLM-style gains more from depth 2 than P3-LLM reports (meth-simulator, 1.78× vs 1.6×). No number of its own.
  - Floats: —
  - Numbers: —
  - Cites: —
  - Links: ← mot-logic-cost, mot-wider-pu, meth-simulator, eval-placement

### A. Skinny GEMM Speedup and Area Efficiency
- **[eval-gemm-summary]**
  - Message: CoDe runs GEMMs at least as fast as LP-Spec-style on about half its logic (CoDe the subject; "at least": ties up to M = 4 and on HBM2, ahead on the mobile platform from M = 8) and faster than P3-LLM-style once a GEMM has more than two token rows (the Fig. 7 description sentence cut 2026-11-10; the caption names what is drawn, mot-roofline-setup the gmean over FC shapes).
  - Floats: —
  - Numbers: — (FC shapes in meth-workloads)
  - Cites: —
  - Links: ← intro-contributions, mot-wider-pu, mot-faster-pu, meth-workloads, meth-metrics
- **[eval-gemm-speed]** "GEMM speed"
  - Message: Up to M = 2 the column period paces every design; beyond M = 2 P3-LLM-style needs a second pass while CoDe fills up to D = 4 beats per command, and CoDe fills the four beats LP-Spec-style fills with 4× multipliers, so CoDe equals LP-Spec-style's speed (to M = 4 mobile, every M edge; CoDe the subject, never "faster" there); on the mobile platform CoDe runs ahead from M = 8 because its eight-token tile halves LP-Spec-style's row sweeps (the sentence names the tile as the cause; the repeated "a lead of the tile size, not of decoupling" caveat and its pointer cut 2026-11-08, T6: eval-lpspec-variants proves it; the 1.11× no longer printed, guard-only in gemm, 2026-11-08). Fig. 7 plots M = 1, 2, 4, …, 64 only, and every range is taken over those M (no claim at a rival's partial-tile dip, user 2026-10-30).
  - Floats: Fig. 7a (fig:gemm, first cite since 2026-11-10)
  - Numbers: 1.96–1.97× at M = 2; 3.74× / 3.82× vs P3-LLM-style 1.95× at M = 4; CoDe 4.16× / 3.80× at M = 64 (Fig. 7a right endpoint, AI-review item 3, 2026-11-08) ← gemm (sd8g3 §2f, 2x2 §2p)
  - Cites: —
  - Links: ← des-beat-slot-factor, des-mapping; → eval-lpspec-variants
- **[eval-gemm-per-mm2]** "GEMM throughput per logic mm$^2$" (headline)
  - Message: Per logic mm², CoDe nearly doubles LP-Spec-style's GEMM throughput on both platforms (same beats, area on storage instead of multipliers, so CoDe runs at least as fast on 0.539× / 0.56× the logic), and it beats P3-LLM-style beyond M = 2; P3-LLM-style's smaller PU leads only at M ≤ 2. No peak at LP-Spec-style's partial-tile dip (M = 5) is printed (user, 2026-10-30).
  - Floats: Fig. 7b
  - Numbers: 0.539× / 0.56× logic ← tables [table4], gemm; vs LP-Spec-style 1.86× (M ≤ 4), 2.07× (M ≥ 8) mobile, 1.79× every M (edge); vs P3-LLM-style 1.43× (M = 4), 1.59× (M ≥ 8) mobile, 1.46–1.47× (M ≥ 4) edge; 0.75× at M ≤ 2 ← gemm (M = 1, 2, 4, …, 64)
  - Cites: —
  - Links: ← mot-logic-cost, meth-area-model; → eval-area-split (0.539× / 0.56× proved there; ref Table IV; Section VI-D)
### B. End-to-End Speedup and Area Efficiency
- **[eval-e2e-phone]** "Mobile platform"
  - Message: Fig. 8 runs whole decoding on the five systems (mobile M = 4, edge batch 8), with the setting's reason (user, 2026-10-30): at acceptance 0.7 a round yields fewer than 1/(1 − 0.7) ≈ 3.3 tokens, and M = 4 is NPU only's best M and within 2 % of NPU + LP-Spec-style's and NPU + CoDe's best; batch 8 is a light edge-server load (cut for space 2026-11-08, T2–T6 pass: "so the verify pass stays short" and "the largest power of two before NPU only overtakes CoDe", the latter stated in eval-e2e-server); on the mobile platform CoDe decodes fastest, 4.37× NPU only at 46.4 tok/s, ahead of LP-Spec-style's 4.34× at 46.1 (CoDe the subject, user 2026-11-10), P3-LLM-style's two-token read needs two passes at M = 4, the order holds at each system's own best M (the past-M = 4 lead sentence removed 2026-11-08: the lead is the tile's, eval-lpspec-variants).
  - Floats: Fig. 8 (fig:e2e, first cite), Fig. 8a
  - Numbers: 4.37× / 4.34× NPU only at 46.4 / 46.1 tok/s; P3-LLM-style 2.96×, stock 1.81×; best M: 47.1 / 46.8 (M = 3), 43.8 / 26.5 (M = 2), NPU only 10.6 (M = 4); 3.3 (tokens per round = (1 − α^M)/(1 − α), from ev56_chain T_round × tok/s); within 2 % (CoDe 1.5 %, LP-Spec-style 1.7 %) ← e2e (sd8g3 §2f; ev56_best / ev56_chain L 1024)
  - Cites: —
  - Links: ← intro-code-proposal, abs-summary, meth-workloads, meth-systems, des-mapping
- **[eval-e2e-server]** "Edge server"
  - Message: At batch 8 CoDe decodes 1.28× faster than NPU only at 456 tok/s and matches LP-Spec-style's speed (equal tok/s in the data: the tie is stated, never a lead) on 0.56× its logic; stock AiM and P3-LLM-style stay below NPU only, so CoDe decodes 1.41× faster than P3-LLM-style; P3-LLM-style runs P3-LLM's own placement (linear layers on the NPU at this batch, attention on PIM), CoDe every layer on PIM, its fastest placement at batch 8 (user 2026-11-10, option B; replaces the all-PIM 0.76× / 1.68×); NPU only overtakes CoDe from batch 16 on the gmean.
  - Floats: Fig. 8a
  - Numbers: 1.28× at 456 tok/s (CoDe = LP-Spec-style exactly, asserted); 0.56× ← tables [table4]; stock 0.45×, P3-LLM-style 0.91× (isca.e2e.hbm2.p3own.speedup_vs_npu); 1.41× (core4_over_p3own.speed); batch 16 ← e2e (2x2 §2p)
  - Cites: —
  - Links: ← mot-gemv-only, intro-code-proposal, abs-summary
- **[eval-e2e-per-mm2]** "Throughput per logic mm$^2$" (headline)
  - Message: CoDe decodes at least as fast as LP-Spec-style on about half its logic and so returns 1.87× / 1.79× LP-Spec-style's tokens/s per logic mm² (one opener sentence since 2026-11-08; the about-half-the-logic reason clause cut 2026-11-08, T6: VI-A gives it), and CoDe's speed lead over P3-LLM-style more than repays its larger PU; on the edge server the metric charges P3-LLM-style no area for the linear layers it runs on the NPU (PIM logic only, 2x2 §2p).
  - Floats: Fig. 8b
  - Numbers: 1.87× / 1.79× vs LP-Spec-style; 1.10× / 1.06× vs P3-LLM-style (core4_over_p3own.per_mm2) ← e2e
  - Cites: —
  - Links: ← intro-code-proposal, abs-summary, mot-logic-cost
- **[eval-lpspec-variants]** "Eight-token LP-Spec-style" (new 2026-11-08 as "LP-Spec-style variants"; the shared design moved to eval-placement, 2026-11-10; lpsv, microarch 1a8bb77, collected a355e66)
  - Message: An eight-token tile does not close CoDe's per-mm² lead on the mobile platform: CoDe matches the eight-token LP-Spec-style's speed (CoDe the subject; 1.007× at M = 12 is CoDe's), so CoDe's M ≥ 8 lead over the per-bank rival (CoDe decodes 1.07× faster at M = 8 and 16, restored 2026-11-10) is the tile's, not decoupling's, but costs 4.72 % of the die and CoDe returns 2.05× its tokens/s per mm².
  - Floats: —
  - Numbers: A8 loop 1.000 at M = 2–4, 8, 16; GEMM 1.000 from M = 8, 1.007 at M = 12; 4.72 %; 2.05× ← tables [lpsv_checks] (sd8g3 §2h, §5 rows 38–41; lpsv.phone.*); CoDe / per-bank LP-Spec-style loop 1.07× at M = 8 and 16 ← tables [lpsv_checks], e2e (sd8g3 §2g; isca.e2e.phone.core8_over_h2.speed_M8 / _M16)
  - Cites: —
  - Links: ← mot-wider-pu, eval-gemm-speed
### C. Energy and Peak Power
- **[eval-energy]** "Energy per token"
  - Message: CoDe spends the least energy per token of the five systems on the mobile platform and ties for the least on the edge server (LP-Spec-style 1.00× printed; 1.0027× unprinted, never claimed as a lead), with the edge NPU idling at 55 W (gated case in one sentence: its ratio grows because P3-LLM-style's NPU reads the linear weights over the HBM pins); every Fig. 8c bar is printed (edge: CoDe's mJ and stock AiM's ratio added 2026-11-08, AI-review item 3).
  - Floats: Fig. 8c
  - Numbers: 70.5 mJ/token; NPU only 7.9×, stock 1.80×, P3-LLM-style 1.28×, LP-Spec-style 1.04× (mobile); CoDe 145 mJ/token, NPU only 1.48×, stock 2.73×, P3-LLM-style 1.52×, CoDe ties LP-Spec-style (1.00×, edge, 55 W); gated P3-LLM-style 2.08× (p3own_over_core4.mJ_55W / mJ_0W); cause (user-approved wording 2026-11-10, measured): CoDe keeps the linear layers in the banks, P3-LLM-style's NPU reads every linear-layer weight over the HBM pins = 76 % of the 0 W gap (hyb.esplit.hbm2.b8.gap_share.weight_io 0.759; context: gap 26.41 mJ/token, linear placement 0.788, P3-LLM-style NPU MAC share 0.0149, unprinted) ← e2e (2x2 §2p: isca.e2e.hbm2.core4.mJ_tok_55W, stock_over_core4.mJ_55W; 2x2 §2r/§8, evaluation 860384d)
  - Cites: —
  - Links: ← intro-code-proposal, abs-summary, meth-platforms (55 W)
- **[eval-power-headroom]** "Power headroom of all-bank PIM" (new 2026-11-06; setting before the peak-power finding)
  - Message: A stock DRAM die holds its banks to a tight current limit (t_FAW: four activations, set by the charge pumps and their power-delivery network), and PIM dies lift this limit so that all banks work at once (AiM ≈ 3× gapless read current with reservoir capacitors and split power nets, no t_FAW; AttAcc's IDD7 budget; Newton ≈ 4× a peak-bandwidth read; SK hynix's bank-count throttling cut 2026-11-10; tightened 2026-11-08: Newton's 2.8× average and the vendors-size-the-delivery clause cut); closing sentence: CoDe's design operates within this headroom (lead into eval-power; the user asked for it, restored 2026-11-08 after a cut). Tone (user, 2026-11-06): PIM relaxed a tight stock limit, never "all-bank PIM breaks t_FAW".
  - Floats: —
  - Numbers: four activations (shevgoor p. 2 / p. 6, PDF); AiM 3× ← budget.cite.aim_mac_current_x_read (JSSC p. 297; reservoir capacitors and tFAW-free ACT16 on p. 295, split power networks p. 297); Newton 4× (p. 380) ← budget.cite.newton_comp_x_peak_read (2.8× p. 382 no longer printed, still asserted); AttAcc IDD7 (author PDF p. 6) ← tables [budget_checks]
  - Cites: shevgoor, aimjssc, attacc, newton (aimxhc36 cut 2026-11-10; bib entry kept, uncited)
  - Links: ← meth-power-model; → eval-power
- **[eval-power]** "Peak power" (rewritten 2026-11-06: headroom first, then the LP-Spec-style ratios; rivals never gated)
  - Message: CoDe's peak power falls inside this headroom on both platforms and stays close to LP-Spec-style's: CoDe (its gated values, no "gated" in the prose, user 2026-11-06) draws 1.20× a full-rate x16 read per die (below AiM's 3×) and 0.75× a full-rate HBM2 stack read (HBM-PIM likewise stays within the original HBM's TDP); 0.92× / 0.87× LP-Spec-style, and without its clock gates 1.04× / 1.03× ("even" / "only" and the HBM2 fits-within-read-power restatement cut 2026-11-08, T6); each CoDe clock edge draws 3.4× / 3.1× less charge (the stock / P3-LLM-style draw-less sentence cut 2026-11-08: Table IV shows it).
  - Floats: Table IV (CoDe's gated mW in parentheses)
  - Numbers: 0.54 W per die, 1.20× ← budget.phone.core8_gated.*; 5.98 W per stack, 0.75× ← budget.hbm2.core4_gated.*; 0.92× / 0.87× ← budget.*.gated.over_h2_ungated (= pupow gate ids); 1.04× / 1.03×, 3.4× / 3.1× ← tables [table_power, budget_checks] (522 / 1,776 pJ no longer printed, asserted as guards; 2.4 % clock cost, 2.9× / 2.8× leakage, −11.6 / −15.1 % no longer printed)
  - Cites: hbmpim
  - Links: ← meth-power-model, eval-power-headroom, des-pu-clock
### D. Area Against Silicon Budgets  (label sec:eval:area; new 2026-11-06)
- **[eval-area-budget]** (subsection opener: frame first)
  - Message: Fabricated PIM dies set the scale for a PIM design's logic area, which a DRAM die pays for in memory capacity (one clause, Section III-C pointer to HBM-PIM's halved sub-arrays in mot-logic-cost; AI-review T3, 2026-11-08) (HBM-PIM 27 % of its die by our division; its halved sub-arrays printed in III-C only since 2026-11-08; AiM 20–25 %, pointed back to III-C), and CoDe's logic takes 2.31 % of the LPDDR5 die and 1.95 % of the HBM2 stack, 4.96 % / 4.02 % at AiM's silicon scale, at most a quarter of AiM's share, while keeping every cell array (the LP-Spec-style shares sentence, 4.28 / 3.48 / 9.47 / 7.50 %, cut 2026-11-10, user review 2; 4.28 % stays in III-C from Table IV; the others are guard-only asserts).
  - Floats: Table IV (logic mm², the source of the shares; the % column was removed 2026-11-10, so VI-D is the shares' print site)
  - Numbers: 32 × 0.712 mm² on 84.4 mm², 27 % (derived, never stated by Samsung) ← budget.hbmpim.area_share_pct; % of die / stack (Table IV mm² over the V-B denominators) ← budget.phone.<d>.pct_of_die_1z, budget.hbm2.<d>.pct_of_stack_model ← tables [budget_cells]; ×2.24 shares ← budget.*.pct_of_*_anch_aim ← tables [budget_checks]. LP-Spec's own 16.92 % is printed in I and III-C only (reconciled with 4.28 % in mot-logic-cost).
  - Cites: hbmpim
  - Links: ← meth-area-model, mot-logic-cost
- **[eval-area-split]** "Logic against LP-Spec-style" (moved from V-B, 2026-11-06)
  - Message: CoDe matches LP-Spec-style's peak throughput with 0.539× its logic per die (an exact tie of the 4× ceiling, CoDe the subject) because it spends its logic on storage rather than arithmetic; on HBM2 its logic is 0.56× LP-Spec-style's and 1.33× P3-LLM-style's for twice P3-LLM-style's beats per column period (the 0.524 / 0.536 silicon-scale ratio sentence cut, user 2026-11-06; guard-only assert).
  - Floats: — (Table V tab:umac_src float defined after this paragraph, before VI-E's heading; lands p10 R top in the ACM build, Fig. 9 alone on p11 L)
  - Numbers: 0.539×; arithmetic 0.73 / 0.34, storage 0.32 / 0.10; 0.56×, 1.33× ← tables [table4, area_split]; 0.524 / 0.536 no longer printed (guard-only in tables [budget_checks])
  - Cites: —
  - Links: ← meth-area-model, mot-two-levers, eval-gemm-per-mm2
### E. Ablation Study
- **[eval-gain-sources]** "Sources of CoDe's gain" (moved from VI-B to VI-D, 2026-10-30, VI-E since 2026-11-06; the both-sources-from-one-mechanism sentence cut)
  - Message: CoDe's gain over stock AiM comes from beat filling, which raises the slot factor, and row reuse, which keeps the sweep factor near stock AiM's level once beat filling shortens the MAC slots; Table V's layer is Table I's layer on the mobile platform (link added 2026-11-10; the "cumulative speed-up = U over stock AiM's U" clause was not added: exact in the data, but the printed U's give 1.25 / 2.96 against the printed 1.24 / 2.97 for row reuse only (mobile) and D = 3 (HBM2)); at D = 2, half its PU clock, CoDe already returns 1.14× / 1.02× LP-Spec-style's throughput per logic mm² on this layer (the measured rung replaces the interpolated D* 1.74 / 1.96); beat filling pays off only after row reuse: applied alone it would keep every row-switch command, which would then take about half of the time or more (f_MAC 0.425 / 0.506; the 2.37 / 1.83 / 2.62 / 1.46 steps no longer printed, guard-only). Relative form; never claims CoDe raises f_MAC on the edge server.
  - Floats: Table V (first cite), Table I (the same mobile layer; Table V's row labels carry the layers, the duplicate setting clause cut 2026-11-08; rows per platform since 2026-11-10: stock AiM, row reuse only (D = 1), D = 2, D = 3, CoDe (D = 4), each step over the row above)
  - Numbers: steps 1.24× / 1.15× after row reuse (Table V); U 0.223 / 0.222 after row reuse; beat filling one beat per step, U_MAC 0.25 → 0.50 → 0.73 → 1.00 (D = 3 runs 2.91 effective beats: the PU hold rounds to whole simulator cycles; one clause in the text, not the caption), its total over row reuse alone 3.49× / 3.33× (D = 1 → 4, umac.dsteps.<p>.bf_total); CoDe's Table V step 1.31 / 1.29 (over D = 3); per logic mm² at D = 2 CoDe returns 1.14× (mobile) / 1.02× (edge server) LP-Spec-style's, layer basis at M = 8, CoDe's logic moves ≤ 1.3 % across D (usrc_dsteps_permm2 per_mm2_vs_lp 1.139 / 1.020, tab_umac_src_dsteps.csv; 2x2 §2s; D* 1.74 / 1.96 no longer printed, guard-only; no f_max or timing-closure claim); CoDe f_MAC 0.779 / 0.739 vs stock 0.717 / 0.771 (Table V); beat filling alone (modelled as a per-sweep rule: a quarter of stock AiM's MAC slots plus its non-MAC time) f_MAC 0.425 / 0.506 (the both-order steps 2.37× then 1.83× and 2.62× then 1.46× guard-only since 2026-11-10) ← tables [umac_src_table] (2x2 §2i, §2s)
  - Cites: —
  - Links: ← des-tile-mac-overview, des-beat-slot-factor, des-row-reuse
- **[eval-vsweep-gain]** "Tile size on a full GEMM" (run-in head; restructured with eval-vsweep-area / -partial / -choice, user 2026-10-30: two heads of two paragraphs each)
  - Message: Setting first (V swept 1–64 for q_proj at M = 64, every tile full; the mobile-staging clause cut 2026-11-10); up to V = D a larger tile fills idle beats, and beyond V = D it removes only row-switch commands.
  - Floats: Fig. 9 (first cite), Fig. 9a
  - Numbers: 3.86× / 3.69× at V = D, 4.90× / 4.39× at V = 64; idle beats 72 % of the V 1 → 2 saving, row switches 91.6 % of the V 4 → 8 saving ← vsw (2x2 §2k). Cut 2026-10-30, asserts kept as guards: row-switch 21 % / refresh 7 % shares, 18.9 → 10.4 %, 20.5 µs token load
  - Cites: —
  - Links: ← des-tile-size
- **[eval-vsweep-area]** (no head; second paragraph under "Tile size on a full GEMM")
  - Message: Past V = D CoDe's storage grows faster than its speed, so throughput per logic mm² peaks at V = D on both platforms; transition: a full tile favours V = D, but a decode step runs at small M, where the last row sweep is often partly filled.
  - Floats: Fig. 9a
  - Numbers: V 4 → 8 logic +16 % (mobile) / +40 % (edge server) against speed 1.117× / 1.089×; peaks 3.01× / 2.34× stock AiM, 1.66× / 0.38× at V = 64 (Fig. 9a right endpoint, AI-review item 3, 2026-11-08) ← vsw (2x2 §2k). Cut 2026-10-30 (guards kept): 1.212 → 1.406 / 0.821 → 1.153 mm², break-even 1.160× / 1.405×, 96.3 % / 77.5 % of peak
  - Cites: —
  - Links: ← des-tile-size, meth-area-model
- **[eval-vsweep-choice]** "Tile size across $M$" (eval-vsweep-partial merged into it, user review 2, 2026-11-10; conclusion first; the M = 3–4 / EAGLE sentence cut)
  - Message: CoDe uses V = 8 on the mobile platform and V = 4 on the edge server, the tile size that loses least in its worst case across M = 3–16 (the small-M reason clause cut 2026-11-10: eval-vsweep-area's last sentence carries it); Fig. 9b divides V = 8's decode-step throughput per logic mm² by V = 4's: on the mobile platform V = 8 wins where it saves V = 4 a partly filled row sweep and loses at M ≤ 4, where both tiles run one row sweep; on the edge server V = 8 never breaks even. ("Wins where it saves" is a necessary condition: V = 8 also saves a sweep at M = 8, 11, 12, 16 and still loses there, 0.97–0.99×.)
  - Floats: Fig. 9b
  - Numbers: wins at M = 5–7, 9–10, 13–15, 1.324× at M = 5; M ≤ 4 → 0.862×; worst loss against the best V (of 2, 4, 8, 16) at each M over M = 3–16: mobile V = 8 13.8 % vs V = 4 29.4 % (q_proj, so printed "on q_proj"; decode step 24.5 % guard-only); edge server 0.712–0.944×, V = 4 11.7 % vs V = 8 28.8–30.0 % ← vsw (2x2 §2l–2n). Cut 2026-10-30 (guards kept): 24.5 % verify-step loss, one-tile 4.6 %, one-tile token load 28.3 % (brk); EAGLE best M = 4 guard-only in e2e
  - Cites: —
  - Links: ← des-tile-size, eval-vsweep-area
- **[eval-placement]** "PU placement" (new 2026-11-10, user-approved brief; last paragraph of VI-E, after the Fig. 9 float source)
  - Message: CoDe keeps its lead under the other placement commercial PIM uses, one unit shared between two banks (II-B; claim first, user review 2, 2026-11-10): sharing costs speed only when a bank delivers a column as often as a unit takes one; on the edge server a bank delivers one every 8 ns and a PU takes one every 4 ns, so every design there, CoDe included, already shares one PU between two banks at full speed; on the mobile platform a bank delivers one every 5 ns, as fast as a unit takes one, so a shared unit halves each bank's rate; built with one unit per two banks, LP-Spec-style takes 0.96× CoDe's logic ("as LP-Spec publishes it" and its cite cut, 2026-11-10), CoDe decodes 1.49× faster at M = 4 and returns 1.42× its tokens/s per logic mm²; conclusion: whichever placement LP-Spec-style uses, CoDe decodes at least as fast (per bank 46.4 vs 46.1 mobile, HBM2 tie) and returns more throughput per logic mm². The 10 ns bank-column sentence was cut (user decision, 2026-11-10).
  - Floats: Table III (t_CCD_L, internal bandwidth, banks)
  - Numbers: 8 ns = 1,024 GB/s / 256 banks of 32 B; 4 ns = t_CCD_L; 5 ns = 409.6 GB/s / 64 banks ← tables [platform_block]; 0.96×, 1.49× (M = 4), 1.42× (M = 4) ← tables [lpsv_checks] (sd8g3 §2h; lpsv.phone.*); the 10 ns clause no longer printed
  - Cites: —
  - Links: ← bg-aim-pu (hc35pim, the two placements), eval-e2e-per-mm2, eval-modelled, mot-wider-pu, intro-code-proposal, intro-contributions, abs-summary

### F. Beat Filling on Newer DRAM  (label sec:eval:newdram; new 2026-11-10, user-approved brief: "D with the PU at CK", no limitation sentence, "above 1 GHz" stated positively)
- **[eval-newer-dram-depth]** (no run-in head; subsection opener)
  - Message: Beat filling keeps a depth of four on newer DRAM, because each generation shortens CK but keeps the all-bank column at four CK (t_CCD_L = 4 t_CK); we evaluate LPDDR5-6400 and HBM2 because LP-Spec and P3-LLM were built on them; LPDDR5X-8533 / -9600 (CK 1.07 / 1.2 GHz) have 3.75 / 3.33 ns columns, HBM3 at 6.4 Gb/s (CK 1.6 GHz) a 2.5 ns column at HBM2's four-clock column [ASSUMPTION: JESD238 not public; never cite AttAcc for it]; a PU at CK runs D = 4 on each, V >= D fills all four beats, U_MAC stays 1 and the MAC rate grows as the column shortens.
  - Floats: Table III (HBM2's four-clock column: t_CK 1 ns, t_CCD_L 4 ns)
  - Numbers: 4 t_CK; 1.07 / 1.2 GHz; 3.75 / 3.33 ns; 6.4 Gb/s, 1.6 GHz, 2.5 ns; D = 4 ← tables [newdram_checks] (spec constants with their cites; 8533 / 8 = 1066.6 MHz and the datasheet bin 1066.5 MHz both print 1.07 GHz and 3.75 ns)
  - Cites: jedeclpddr5, micronlp5x, synopsyshbm3
  - Links: ← bg-aim-pu (D defined), mot-depth, des-pu-clock, eval-gain-sources (U_MAC 1 at D = 4); → conc-summary (decoupling carries over)
- **[eval-newer-dram-clock]** (no run-in head)
  - Message: CoDe on these memories clocks its PU above 1 GHz, at 1.07 to 1.6 GHz, and three DRAM trends support a PU above 1 GHz: the die already clocks command logic at CK and its data path faster (LPDDR5X WCK = 4 CK, HBM3 strobes 3.2 GHz); periphery has moved closer to logic-class transistors since the 1 GHz GDDR6-AiM PU of III-D (back-pointer only; III-D keeps AiM's 1y-nm and the general HKMG claim, E2) (SK hynix HKMG LPDDR5X 8.5 Gb/s at 25 % less power; Micron 1γ next-generation HKMG for transistor speed, DDR5 designed for 9200 MT/s) and TSMC plans HBM4 base dies in 12-nm and 5-nm logic processes; commercial PIM has moved to LPDDR5X (LPDDR5X-PIM 614 GB/s inside, eight times its 76.8 GB/s interface). No limitation sentence (user). Relaxes III-D's "never vendors' pin-rate claims" rule here only (user-approved text). Dropped at verification: "1a-nm" (SK hynix newsroom does not print it; only aggregator headlines), "-9600" on LPDDR5X-PIM (no fetched report prints it), "credits HKMG for 9200 MT/s" (Micron ties HKMG to speed capability, 9200 MT/s to the DDR5 design).
  - Floats: —
  - Numbers: 1.07 to 1.6 GHz; WCK 4 × CK; 3.2 GHz; 8.5 Gb/s, 25 %; 9200 MT/s; 1 GHz (back-pointer to III-D's aimjssc figure); 12 / 5 nm; 614 / 76.8 GB/s = 8.0 ("eight times") ← tables [newdram_checks] (cited constants)
  - Cites: micronlp5x, synopsyshbm3, skhynixhkmg, micron1gamma, tsmchbm4, lp5xpim
  - Links: ← mot-pu-clock-precedent (points back to AiM's 1 GHz PU; Observation 26 resolved), des-pu-clock

## VII. Conclusion  (sections/07_conclusion.tex)
- **[conc-summary]**
  - Message: Decoupling MAC timing from DRAM command timing lets one column command feed many PU beats over a tile of tokens: CoDe decodes slightly faster than LP-Spec-style (CoDe the subject, user 2026-11-10) with the stock multiplier count clocked at the command clock on 0.539× its logic, and on HBM2 decodes a batch of 8 faster than P3-LLM-style and NPU only; the decoupling carries over to any DRAM whose column outlasts one beat.
  - Floats: —
  - Numbers: 0.539× ← tables [table4]; 1.41×, 1.28× ← e2e
  - Cites: —
  - Links: ← mot-depth, eval-area-split, eval-e2e-server

## Float map
ACM sigconf since 2026-11-10: the paper prints Table 1–5, Figure 1–9 and Sections 1–7 with arabic subsections (3.2);
the outline's roman ids (Table I–V, III-B) name the same floats and sections. Pages are the ACM build's.
| float | label | source file | first cite | lands |
|---|---|---|---|---|
| Fig. 1 | fig:dram_pim | figs/fig_dram_pim.pdf ← figs/src/fig_dram_pim.html, html2pdf.py (01_introduction.tex) | intro-pim-gemv-ceiling (p1 L) | p1 R |
| Fig. 2 | fig:roofline | figs/fig_roofline.pdf ← roof (01_introduction.tex) | intro-pim-gemv-ceiling (p1 L) | p2 R top |
| Fig. 3 | fig:breakdown | figs/fig_breakdown.pdf ← brk (03_motivation.tex, after mot-breakdown-setup) | mot-breakdown-setup (p3 L) | p3 R top |
| Table I | tab:umac | tables/tab_umac.tex ← tables (03_motivation.tex, inside mot-utilization) | mot-utilization (p4 L) | p4 L top |
| Fig. 4 | fig:timeline | figs/fig_timeline.pdf ← make_fig_timeline.py (03_motivation.tex, after mot-wider-pu, so that it misses Table I's column) | mot-prior-families (p4 R) | p4 R top |
| Fig. 5 | fig:tile | figs/fig_tile.pdf ← figs/src/fig_tile.html, html2pdf.py (04_design.tex, top of IV) | des-tile-mac-overview (p5 R) | p5 R top |
| Fig. 6 | fig:mapping | figs/fig_mapping.pdf ← map, html2pdf.py (04_design.tex, after IV-A) | des-row-reuse (p6 R) | p6 L top |
| Table II | tab:cmds | tables/tab_cmds.tex ← map (04_design.tex) | des-command-set (p6 R) | p7 L top |
| Table III | tab:params | tables/tab_params.tex ← tables [platform_block] (05_methodology.tex, after meth-platforms; platform rows only since 2026-11-06) | bg-dram-channel (p2 R) | p7 R top (configuration table: F12 exception; first cite in V on p7 R) |
| Table IV | tab:designs | tables/tab_designs.tex ← tables [table4, budget_cells] (05_methodology.tex, after meth-area-model since 2026-11-08; split from tab:params 2026-11-06: lanes, MHz, D, V, slots, GB, mm², mW with CoDe's gated mW in parentheses) | mot-wider-pu (p4 R) | p8 L top (F12 exception; first cite in V, meth-designs, p7 R) |
| Fig. 7 | fig:gemm | figs/fig_gemm.pdf ← gemm, html2pdf.py (05_methodology.tex, one-column figure after meth-workloads since 2026-11-08; figure* until 2026-11-06) | eval-gemm-speed (p8 R) | p8 R top |
| Fig. 8 | fig:e2e | figs/fig_e2e.pdf ← e2e, html2pdf.py (05_methodology.tex, figure* right after Fig. 7's source since 2026-11-10 (ACM), so that it renders on VI-B's page; was after eval-gemm-per-mm2) | eval-e2e-phone (p9) | p9 top, both columns |
| Table V | tab:umac_src | tables/tab_umac_src.tex ← tables (06_evaluation.tex, after eval-area-split, before VI-E's heading; since 2026-11-06; D = 2 / 3 rows since 2026-11-10) | eval-gain-sources (p10 R) | p10 R top (citing page) |
| Fig. 9 | fig:vsweep | figs/fig_vsweep.pdf ← vsw (06_evaluation.tex) | eval-vsweep-gain (p10 R) | p11 L top |
| Eq. 1 | eq:fmac | 03_motivation.tex | mot-sweep-factor | p4 L |

## Observations
| # | kind | where | observation |
|---|---|---|---|
| 1 | resolved | mot-nonmac-classes … mot-utilization | Resolved again (user, 2026-10-28): III-B now runs setup (mot-breakdown-setup) → Non-MAC commands (classes, non-MAC cost with row switch first, sweep factor; mot-load-refresh-cost merged into mot-rowswitch-cost, user 2026-10-29) → Idle beats (idle beats, cause) → mot-utilization (U, Table I, transition to III-C). Before (user plan, 2026-10-27): split into Non-MAC commands (what each command costs per row sweep; row switches outlast the useful MAC work) and Sweep factor (Eq. 1, Table I, f_MAC 0.717, U 0.179). Was: one paragraph (≈ 30 source lines, ≈ 25 numbers) carries the f_MAC formula and fit, the per-command row-switch split, token load against GB fills, refresh, the edge-server totals and stock U = 0.179; class names are used before this paragraph defines them. |
| 2 | resolved | meth-simulator | Resolved (2026-11-06): V-C is three paragraphs, meth-simulator (simulator, P3-LLM validation, C/A re-timing, refresh), meth-area-model and meth-power-model. Was: one paragraph with five topics. |
| 3 | two messages | mot-logic-cost, eval-e2e-phone | mot-logic-cost (logic-die designs) still adds a second claim (eval-vsweep-robust's two claims split into eval-vsweep-partial / -choice, 2026-10-30, merged back into eval-vsweep-choice conclusion-first, 2026-11-10); eval-e2e-phone carries the figure setup and its reason (M = 4, batch 8), the M = 4 result, the best-M check and the M ≥ 5 lead. The former eval-phone-per-mm2 / -energy / eval-server-beats cases left with the VI restructure (2026-10-30). |
| 4 | placement | eval-gain-sources | eval-gain-sources opens VI-E (Ablation Study, VI-D until 2026-11-06); Table V lands at the top of its citing page (ACM build: cite p10 R, table p10 R top) from its source before VI-E's heading (moved from after the Conclusion heading, 2026-11-06). It remains the only home of the both-order gain. |
| 5 | resolved | eval-gain-sources | Resolved (user plan, 2026-10-27): des-gain-order deleted; the both-order gain lives only in VI-B (2.37× / 1.83×, Table V values); the 2.3 % reconciling sentence left IV-B. Was: the two-order gain printed 2.39× then 1.84× (Fig. 5 window) in IV-A and 2.37× then 1.83× (one layer, Table V) in VI-B; only des-beat-slot-factor's 2.3 % sentence reconciles them. |
| 6 | restatement | intro-prior-families / mot-prior-families; intro-timing-insight / mot-depth; mot-idle-beats / mot-depth | The two families are named in I and III-C; mot-depth now points to Table III for the column period and CK instead of reprinting the intro's 5 ns / 4 ns / 0.8–1 GHz, and mot-idle-cause's column-access argument is now one sentence (each column command reads one column; t_CCD spacing), leaving the latched-column argument to mot-depth. D is now defined once, in bg-aim-pu (its first point of need), and III and IV point back to it (resolves "D derived late"); intro-timing-insight still derives D = t_col × f_PU itself (introduction untouched). |
| 7 | restatement | intro-prior-families / mot-logic-cost; eval-area-budget | The V = 4 reason now lives in IV-D only (V-B points to it, 2026-11-08); LP-Spec's 16.92 % is printed in I and III-C (not in VI-D), reconciled with 4.28 % in III-C; 0.539× appears in the abstract, I, VI-A, VI-D and VII (the area-efficiency headline); HBM-PIM's halved sub-arrays in III-C only. |
| 8 | config table | Tables III / IV (tab:params, tab:designs) | Two configuration tables in V (platform, Table III; designs, Table IV; split 2026-11-06, user); III–VI refer to them, design rows (lanes, PU clock, GB, slots, area, %, peak power) to Table IV. Kept in prose where the sentence computes or derives: intro's 5 / 4 ns, 0.8 / 1 GHz and 42 GB/s (D and the ridge), III-A's 42 GB/s derivation, IV-D's GB / slice sizes, VI-C's 1.25 / 5 ns per-edge charge (the 800 / 200 MHz clock-cost sentence left on 2026-10-30). Row size has no collected source and stays out (for evaluation-owner). |
| 10 | resolved | intro-contributions | Resolved (2026-11-08, AI-review item 1): the claim–evidence contributions announce energy (VI-C), area against silicon budgets (VI-D) and the ablation (VI-E). Peak power and the tile-size study stay unannounced (not in a contribution item). |
| 11 | untraced number | meth-platforms, Table III | 2.285 W host power (derived from cites, no script); Table III's t_REFI 3.906 µs is asserted from evaluation/dac_sd8g3/context.md text ([A-REF1]) and t_RFCab 280 ns from the collected trace (utrace_run_core8_gbfill REFab gap), neither has a JEDEC cite; 131 TOPS (assumption with cite only); 56 / 68 / 51.2 GB/s (cites; only the 42 GB/s result is asserted). |
| 12 | resolved | eval-power | Resolved (2026-10-30): the 2.4 % clock cost (microarch pu_peak_power.csv, never collected) is no longer printed; make_tables.py keeps its assert as a guard. |
| 13 | structure | mot-other-pim | Stays last in III-C (user, 2026-10-27); no related-work section remains (options kept for later: (a) a short Related Work section before the Conclusion, from the ≈ 1 free column; (b) a landscape paragraph at the end of II-B; (c) keep it as the last paragraph of III-C, as now). mot-other-pim now closes III-C with the C → D transition (a column read feeds several tokens only through added multipliers or commands; a row sweep serves one MAC slot's tokens). Labels `sec:bg:*` point into Section III (cosmetic). |
| 14 | unverified source | mot-other-pim (closing), des-row-reuse, mot-idle-cause | LP-Spec's own text on row activations was not checked: no LP-Spec PDF exists under 00_doc (paper_isca2's is empty; paper_dac's references hold p3llm.pdf, the AiM JSSC paper and others, not LP-Spec), so LP-Spec-style's sharing of a row sweep among its four tokens rests on our model (Table I, A = 4). P3-LLM's own text (p. 11) supports its two-token row-activation saving. HBM-PIM's statement of a GEMV target was not checked (no PDF); AiM JSSC p. 1 (RNN and MLP layers with low memory reuse, evaluated on GEMV) and P3-LLM p. 3 (both PCUs perform GEMV) were. |
| 15 | timing | Table III, mot-idle-beats, eval-placement | HBM2's column period prints t_CCD_L = 4 ns (cited) while the simulator's all-bank HBM2 MAC slot is 8 ns (b = 2, two banks per PU; dac2x2_setup); U_MAC's b = 2 reconciles them; eval-placement now prints the 8 ns per-bank column (1,024 GB/s / 256 banks), Table III still shows no 8 ns slot. |
| 16 | resolved | mot-prior-families, mot-other-pim, mot-two-levers, des-row-reuse, eval-gain-sources | Resolved (user, 2026-10-27): f_MAC is a share, so row reuse is stated in absolute form in III-C, III-D and IV-C (it cuts the non-MAC time per token: 123.39 → 22.15 ns mobile, 146.17 → 43.51 ns edge server) and in relative form in VI-B (it keeps f_MAC near stock AiM's level once beat filling shortens the slots: 0.779 / 0.739 vs 0.717 / 0.771). Guard: no sentence says CoDe raises f_MAC on the edge server (0.739 < 0.771) or frames the rivals' flat f_MAC as their defect; only the D = 1 row-reuse-only row lifts f_MAC (0.892 / 0.887). |
| 17 | ordering | mot-logic-cost, mot-faster-pu | With logic cost before the faster-PU family (user order), mot-logic-cost compares LP-Spec-style's per-mm² ceiling with stock AiM's (314 / 697 vs 216 / 492) and P3-LLM-style's 390 / 830 moved into mot-faster-pu after P3-LLM-style is named. |
| 18 | restatement | intro-prior-families, intro-timing-insight vs mot-prior-families, mot-depth | The introduction still repeats III-C's two families and III-D's insight (and derives D itself); left untouched by the III/IV mirror pass (user plan, 2026-10-27). |
| 19 | resolved | eval-gemm-per-mm2 | Resolved (2026-10-30): the per-mm² ceilings of CoDe (583 / 1,247 GOPS) are no longer printed beside measured ratios; VI-A prints measured GEMM ratios against M only. |
| 20 | dropped number | des-row-reuse | The whole-GEMM 4.32× (CoDe vs stock AiM, q_proj, M = 8) left IV with des-gain-order; no other section printed it, and the 4.40× window carries IV-C's claim. Still asserted in make_fig_mapping.py; it could return to VI-B if a whole-kernel number is wanted. |
| 21 | resolved | mot-rowswitch-cost vs des-row-reuse | Resolved (user, 2026-10-29): III-B prints q_proj shares only, so the edge non-MAC time appears once, as 146.17 ns per token (IV-C, Table I). Was: 146.2 ns per row sweep in III-B and 146.17 ns in IV-C. |
| 22 | wording trap | meth-area-model, eval-area-budget, eval-power | Area / power budget (2026-11-06): 60.92 mm² is printed "as LP-Spec reports" (its ISSCC'21 origin is closed access, never cited); the HBM2 stack is 8 × the 84.4 mm² HBM-PIM die ([A-XC4], no plain HBM2 die area published); 27 % is our division; peak excludes activation, refresh, background and I/O power, so the read yardsticks (447 mW at LPDDR5X-7500 for a 6400 part; 8.0 W from O'Connor's 4-die figure on an 8-die stack) are scales, not budget shares; AiM's 3× is a GDDR6 current ratio (framing); the plan's "the stack in PIM mode draws less than in normal reads" became "CoDe's PUs fit within the read power an HBM2 stack already delivers" plus HBM-PIM's TDP sentence, because the peak omits activation power and HBM-PIM measured +5.4 %, within the original TDP. SK hynix's bank-count throttling is a "future AiM design" knob on its HC36 slide, not a shipped feature. |
| 23 | citation | shevgoor | The Shevgoor MICRO'13 entry has no pages or DOI (not verifiable offline); the quote is on PDF pp. 2 and 6 of the authors' copy. |
| 24 | reviewer risk | eval-placement, eval-lpspec-variants, mot-logic-cost | The LP-Spec-style variants (2026-11-08) are phone-only and modelled: the shared design (eval-placement, VI-E since 2026-11-10) at LP-Spec's own 10 ns bank column is not run (no longer stated in the paper: user cut the clause, 2026-11-10), no HBM2 shared variant is run (eval-placement argues it loses no speed: 8 ns bank column vs 4 ns PU), and the shared unit's 2:1 bank mux is unpriced (favours LP-Spec-style). The abstract keeps "1.49× faster at about the same logic area" (user, 2026-11-10). LP-Spec's register-file area stays unprinted (9.80 / 12.08 mm² at 16 sets vs 4.90 / 6.04 at 8 sets, sd8g3 context §5 row 40, for microarch-owner). |
| 25 | reviewer risk | meth-systems, eval-e2e-server, eval-e2e-per-mm2, eval-energy | Edge-server P3-LLM-style follows P3-LLM's own placement since 2026-11-10 (user, option B; reviewer: "a configuration P3-LLM would not run"): linear layers on the NPU at batch 8, attention on PIM (P3-LLM p. 13); CoDe stays all-PIM (its fastest placement at batch 8). Per logic mm² counts no NPU area, which favours P3-LLM-style (stated in eval-e2e-per-mm2). Not printed: the per-class best of each (1.24× speed, 0.93× per mm², hyb.hbm2.*). Old all-PIM ids isca.e2e.hbm2.p3_500.* (0.76×, 1.68×, 1.26×, 1.64× / 1.46×) are history; make_tables headline() still guards them as the pack's values. |
| 26 | resolved | mot-pu-clock-precedent vs eval-newer-dram-clock | Resolved (user-approved brief, 2026-11-10, E2): VI-F's second trend opens with a back-pointer to III-D's 1 GHz GDDR6-AiM PU and keeps only the product-specific facts (SK hynix, Micron, TSMC HBM4); the 1y-nm sentence and the general HKMG claim stay in III-D only; aimjssc left VI-F. |
