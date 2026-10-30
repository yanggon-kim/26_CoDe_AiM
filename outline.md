# Commands Are the Bottleneck: CoDe, a Command-Decoupled PIM for Skinny GEMMs on Mobile and Server DRAM: outline
Synced with: PENDING; body ends p. 11 col R (≈ 0.3 column); refs end p. 13.
Legend: one entry per source paragraph, in source order, tied to the `.tex` by `% P:<id>`; Message = the one claim a reader takes away; Floats = figures/tables/equations cited (first cite marked); Numbers = key printed numbers ← the script that asserts them (evaluation topic in brackets); Cites = bib keys; Links = → promise fulfilled by <id>, ← relies on <id>. Check: `python3 scripts/check_outline.py`.

Number sources, short names: `tables` = scripts/make_tables.py (functions in brackets); `roof` = make_fig_roofline.py; `brk` = make_fig_breakdown.py; `map` = make_fig_mapping.py; `vsw` = make_fig_vsweep.py; `gemm` / `e2e` = make_fig_gemm.py / make_fig_e2e.py (ISCA ids `isca.gemm.*`, `isca.e2e.*`). Evaluation topics: `2x2` = evaluation/dac_2x2, `sd8g3` = evaluation/dac_sd8g3 (EV-58 pack via scripts/dac_data.py).

## Abstract  (sections/00_abstract.tex)
- **[abs-summary]**
  - Message: CoDe lets one DRAM column command feed a tile of tokens at the PU's own clock, so PIM serves skinny decode GEMMs that command-paced PIM designs serve only with more multipliers or more commands.
  - Floats: —
  - Numbers: M 2–32; 4× multipliers; two tokens per read; 5 / 4 ns column; four beats at 0.8–1 GHz; mobile: matches LP-Spec-style's end-to-end speed with 1.87× its throughput per logic mm²; HBM2 batch of 8: 1.68× speed, 1.26× per mm², 1.64× energy over P3-LLM-style ← e2e (sd8g3 §2f, 2x2 §2p), roof
  - Cites: —
  - Links: → intro-code-proposal, eval-e2e-phone, eval-e2e-server, eval-e2e-per-mm2, eval-energy

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
  - Message: CoDe runs D beats per column command over a tile of V tokens at the stock multiplier count, and on each rival's own ground it matches LP-Spec-style's end-to-end speed on half the logic (1.87× per logic mm²) and outruns P3-LLM-style on HBM2.
  - Floats: —
  - Numbers: 0.539× logic area ← tables [table4]; 1.87× per logic mm²; 1.68×, 1.26×, 1.64× (batch 8) ← e2e
  - Cites: sd8g3
  - Links: → des-tile-mac-overview, eval-e2e-phone, eval-e2e-server, eval-e2e-per-mm2, eval-energy
- **[intro-contributions]** (itemize, three items)
  - Message: The paper contributes the depth analysis of command-decoupled MACs, the CoDe PU and command extension, and a two-pairing evaluation on each rival's own memory.
  - Floats: —
  - Numbers: D = 4 (LPDDR5-6400, HBM2) ← structural (HBM3 dropped with mot-depth's extrapolation)
  - Cites: —
  - Links: → mot-depth, des-command-set, des-tile-mac-pu, eval-gemm-summary, eval-e2e-phone, eval-e2e-server

## II. Background  (sections/02_background.tex)
### A. Skinny GEMM in LLM Decoding
- **[bg-skinny-range]**
  - Message: Published mobile verifiers and edge-server batches put M between 2 and 32, while datacenter trees and batches reach past the range and belong to the host.
  - Floats: —
  - Numbers: M ≪ 64; 2–8 padded to 32; 1–32; 4–64; 1–8; 48–60, 64, 64–128, 16–27; targets M = 2–32 and 2–8 ← cited
  - Cites: flashdecodingpp, leviathan2023, eagle2, sdnpu, lpspec, lever, p3llm, medusa, sequoia, attacc
  - Links: ← intro-skinny-gemm; → mot-stock-crossover
### B. DRAM and AiM-Style PIM
- **[bg-dram-channel]**
  - Message: An activation opens one row of a bank (2 KB on LPDDR5) and each column command moves one 32 B column of it (32 B stated once); column commands issue every t_CCD_S across bank groups and every t_CCD_L within one, which is twice as long.
  - Floats: Fig. 1, Table III (row size)
  - Numbers: 16 banks, four bank groups, 32 B, 2 KB row ← structural; row size in Table III ← tables [platform_block] (2x2 raw cvs_sum labels; JEDEC page size)
  - Cites: jedeclpddr5, ramulator2, p3llm
  - Links: → bg-row-sweep, mot-faster-pu
- **[bg-aim-pu]**
  - Message: AiM-style PIM puts a PU beside each bank and a shared global buffer on the die, and one all-bank MAC command every t_CCD_L starts one MAC beat in every PU; the column period spans D = 4 CK cycles (D defined here as a timing fact; the "D beats per column read" opportunity is mot-depth's, the GEMV-to-bank mapping des-mapping's); commercial PIM ships the same per-bank layout (HBM-PIM, Samsung's LPDDR5X-PIM).
  - Floats: Fig. 1, Table III (first cite; configuration table, F12 exception)
  - Numbers: 32 INT8 multiplies per beat; D = 4 (Table III); D defined: CK cycles per column period, t_col = D × t_CK, named the depth (the intro and V-C already say "depth") ← structural
  - Cites: aimjssc, hbmpim, lp5xpim (layout only: one PIM block per bank; no clock or bandwidth)
  - Links: → bg-mac-sequence, mot-breakdown-setup, mot-idle-beats, mot-prior-families, mot-depth, des-beat-decouple, des-mapping
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
  - Message: Fig. 2 plots skinny-GEMM throughput against M in the roofline form for the host NPU's roof and for simulated PIM GEMMs of stock AiM and each platform's rival; order (figure-paragraph rule): what the figure shows → basic setup (geometric mean over the FC shapes, M = 2^k) → details (mobile NPU bandwidth, edge NPU) → closing pointer to Table III and Section V.
  - Floats: Fig. 2, Table III
  - Numbers: M = 2^k; 56 of 68 GB/s, 51.2 GB/s pins → 42 GB/s [assumption] ← cited; 42 asserted in roof; the edge NPU's 131 TOPS / 256 GB/s in Table III ← tables [platform_block]
  - Cites: roofline, sd8g3, powerinfer2, heterollm, p3llm
  - Links: ← bg-aim-pu (Table III first cite); → meth-platforms
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
  - Message: Published PIM systems keep PIM for GEMVs and send the GEMMs to the host or NPU, even though the host runs every skinny GEMM on its memory roof (back-pointer to mot-host-roof); the A → B transition moved to mot-a-summary.
  - Floats: —
  - Numbers: batch 8 (P3-LLM offload) ← cited
  - Cites: attacc, neupims, ianus, p3llm
  - Links: ← intro-pim-gemv-ceiling, mot-host-roof; → mot-a-summary, eval-e2e-server
- **[mot-a-summary]**
  - Message: Skinny GEMMs, memory-bound on the host, belong on PIM, which reads the weights inside the DRAM, yet stock PIM's GEMM throughput stays flat at its GEMV ceiling; closing A → B transition: III-B splits a stock GEMM's time to locate the cause (two sentences, no heading).
  - Floats: —
  - Numbers: —
  - Cites: —
  - Links: ← mot-host-roof, mot-stock-crossover, mot-gemv-only; → mot-breakdown-setup
### B. Two Root Causes of Stock PIM Inefficiency
- **[mot-breakdown-setup]**
  - Message: Useful MAC work fills at most a fifth of a stock GEMM's time, and non-MAC commands and idle beats take the rest; order (figure-paragraph rule): what Fig. 3 shows → kernels → platforms (precision follows each platform's prior target design: LP-Spec on the mobile platform, P3-LLM on the edge server; V-B points back here) → the two groups (non-MAC commands; MAC slots of useful and idle beats; MAC slot t_slot defined here) → finding → transition to the two root causes (non-MAC commands, then idle beats). Per-segment explanations live in B2–B7, U in mot-utilization.
  - Floats: Fig. 3 (first cite; float defined after this paragraph), Fig. 1 (b), Table III
  - Numbers: one tile 2048 × 64 / 4096 × 256 (one row sweep per bank, one GB chunk); q_proj 4096 × 4096; M = 8, one channel; useful 14.1–19.1 %, non-MAC 23.4–43.7 %, idle 42.2–57.4 % ← brk (2x2 §2j; the ≤ 0.015 % stalls stay a guard assert only)
  - Cites: lpspec, p3llm
  - Links: ← bg-aim-pu, bg-row-sweep, mot-a-summary; → mot-nonmac-classes, mot-idle-beats, mot-utilization, meth-designs-area, eval-vsweep-robust (Fig. 3's one tile)
- **[mot-nonmac-classes]** "Non-MAC commands" (run-in head over mot-nonmac-classes … mot-sweep-factor)
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
  - Message: The paper defines the sweep factor f_MAC as the share of GEMM time the MAC slots get, set by the non-MAC commands through Eq. 1 (c, A from II-B; t_slot from mot-breakdown-setup; t_row, t_tok from mot-nonmac-classes; ρ defined here); one mobile case study gives stock AiM's 0.717 (no own heading; under "Non-MAC commands").
  - Floats: Eq. 1 (eq:fmac)
  - Numbers: mobile case study only: t_row 87.73 ns, t_tok 4.26 ns, ρ 0.070 (ρ relied on by meth-simulator) → f_MAC 0.717 of a decoder layer's time ← tables [umac_table, umac_src_table]; edge fit values (94.76, 9.64, 0.061) and the 91.2 ns MAC-tail sentence cut (guard-only asserts)
  - Cites: —
  - Links: ← mot-nonmac-classes, mot-rowswitch-cost; → mot-utilization, meth-simulator
- **[mot-idle-beats]** "Idle beats" (run-in head over mot-idle-beats and mot-idle-cause)
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
  - Numbers: U = 1/4 × 0.717 = 0.179 (mobile); edge U 0.193 (also Table IV) ← tables [umac_table]
  - Cites: —
  - Links: ← mot-breakdown-setup, mot-sweep-factor, mot-idle-beats; → mot-prior-families, mot-wider-pu, mot-two-levers, des-tile-mac-overview
### C. GEMM Support in Prior PIM
- **[mot-prior-families]**
  - Message: Prior PIM designs fill the idle beats in two families, with more multipliers or with more commands; Fig. 4 follows one weight column through eight tokens in stock AiM and one design of each family (LP-Spec, P3-LLM), and the next paragraphs take the families in turn (pure framing opener; the figure's setup and counts moved into mot-wider-pu and mot-faster-pu; the row-sweep claim lives in mot-other-pim's closing; Fig. 4's CoDe row is explained in des-beat-decouple).
  - Floats: Fig. 4 (first cite; fig:timeline, float defined after mot-wider-pu)
  - Numbers: — (eight tokens, structural)
  - Cites: lpspec, p3llm
  - Links: ← intro-prior-families, mot-utilization; → mot-wider-pu, mot-faster-pu
- **[mot-wider-pu]** "Wider-PU family"
  - Message: Wider-PU designs trade area for MAC throughput by filling the idle beats with more multipliers per PU (opener), so LP-Spec-style, the mobile rival, reaches U_MAC = 1 only by quadrupling the multipliers, and per multiplier its U stays below stock AiM's (closing).
  - Floats: Fig. 4 (column periods T of D = 4 beats defined for reading it), Fig. 2, Table I, Table III
  - Numbers: four 32-wide ALUs, one MAC step per column period (200 MHz → Table III); Fig. 4 counts: stock 8 column periods / 8 commands / 8 reads, LP-Spec 2 / 2 / 2 (M = 8, D = 4 from II-B) ← structural; crossover M = 20–24; U per multiplier 0.173–0.174 / 0.185 ← roof, tables [umac_table]
  - Cites: lpspec, papi, stepstone, duplex, h2llm, monde
  - Links: ← intro-prior-families, mot-prior-families, mot-idle-beats; → mot-logic-cost, mot-two-levers (area a PIM die gives to beat filling), eval-gemm-summary (ref → Section VI since 2026-10-30)
- **[mot-logic-cost]** "Cost of logic in a DRAM die"
  - Message: Logic in a DRAM die costs capacity, so per logic mm² the wider-PU family keeps only part of its four-fold ceiling over stock AiM.
  - Floats: —
  - Numbers: 10× less dense, 3 vs 10+ metal layers (UPMEM's report, devaux); 0.19 mm² per PU; 50 % capacity ← hbmpim (halved sub-arrays, p. 8); 16.92 % for compute units and buffers (lpspec p. 7) vs 20–25 % ← cited; LP-Spec-style 314 / 697 vs stock AiM 216 / 492 GOPS/mm² ← roof
  - Cites: devaux, aimjssc, hbmpim, lpspec
  - Links: ← intro-prior-families, mot-wider-pu; → eval-gemm-per-mm2, eval-e2e-per-mm2
- **[mot-faster-pu]** "Faster-PU family"
  - Message: Faster-PU designs speed up the PU but still start every MAC with a command, so DRAM command timing, not the PU clock, caps them at two beats per column read (opener; the user's top point in this paragraph): commands issue every t_CCD_S, half of t_CCD_L, so P3-LLM-style, the edge-server rival, stops at U_MAC = 1/2 however fast its PU runs, yet keeps a higher ceiling per logic mm² than LP-Spec-style.
  - Floats: Fig. 4 (P3-LLM row), Fig. 2, Table III
  - Numbers: one beat per t_CCD_S (500 MHz → Table III); Fig. 4 counts 4 column periods, 8 commands, 4 reads ← structural; U_MAC stops at 1/2 wherever t_CCD_L = 2 t_CCD_S; crossover M = 4–6; 390 / 830 GOPS/mm² ← roof
  - Cites: p3llm, hbmpim
  - Links: ← bg-dram-channel, intro-prior-families, mot-prior-families, mot-idle-beats, mot-logic-cost; → mot-depth (the per-token command is what a PU at CK must drop), eval-gemm-summary (ref → Section VI since 2026-10-30)
- **[mot-other-pim]**
  - Message: The remaining LLM PIM designs either serve one input vector per weight read or reorganize the work around the PU, and the three that run several beats per column read still hold one vector; closing C → D transition: across the two families and these three designs, a column read feeds several tokens only through added multipliers or added commands, and a row sweep serves only one MAC slot's tokens.
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
  - Message: A PU clocked at CK has precedent in DRAM silicon, from UPMEM's 500 MHz design (350 MHz deployed) to GDDR6-AiM's 1 GHz multipliers and an HBM-PIM-style PU at CK, and DRAM periphery has since gained logic-process features (HKMG at three vendors, 5–6 metal layers on 1a-nm dies); never "a PU at CK is the trend", never the vendors' pin-rate speed claims.
  - Floats: —
  - Numbers: 1.0–1.2 GHz bus, 250–300 MHz, 20 nm; 500 MHz design, 2x-nm; 350 MHz deployed ← prim (p. 5); 1 GHz, 1y-nm; eight 1y-nm dies; five to six metal layers, 1a-nm ← tid1a16, tid1a24 ← cited
  - Cites: hbmpim, devaux, prim, aimjssc, flashbolt, pfpu, tiroadmap, tid1a16, tid1a24
  - Links: ← intro-timing-insight; → mot-two-levers, des-pu-clock
- **[mot-two-levers]**
  - Message: A PU at CK fits in a DRAM die, and the wider-PU family shows how much logic area a PIM die already gives to filling idle beats, so we keep the stock multipliers, run them at CK within that area, and answer each root cause of III-B with one lever (opener): row reuse (IV-B) answers the non-MAC commands by cutting their time per token (no claim that row reuse raises f_MAC; the rival contrast lives in des-row-reuse); beat filling (IV-C) uses all D beats of a column period without adding multipliers and answers the idle beats (III-B's order, since 2026-10-29). "Within that area" checked against Table III: CoDe's logic 1.406 vs LP-Spec-style 2.610 mm² per die (0.539×), 0.821 vs 1.469 mm² per pCH (0.56×).
  - Floats: Fig. 1
  - Numbers: D = 4 beats per column read, one used ← structural; no CoDe number
  - Cites: —
  - Links: ← mot-idle-beats, mot-nonmac-classes, mot-rowswitch-cost, mot-depth, mot-pu-clock-precedent, mot-logic-cost; → des-tile-mac-overview, des-row-reuse, des-beat-decouple, meth-designs-area

## IV. CoDe Design  (sections/04_design.tex)  — mirrors III: IV-A one mechanism, IV-B ↔ III-B non-MAC commands, IV-C ↔ III-B idle beats (III-B's order; row reuse first since 2026-10-29); each component paragraph: cause recalled → mechanism → contrast with the III-C family → effect in Fig. 6
### A. Overview: One Command, Many MAC Beats
- **[des-tile-mac-overview]**
  - Message: One tile MAC per weight column for V tokens of a skinny GEMM carries both levers (row reuse, then beat filling); both come from the tile, held in a global buffer extended from one input vector to V (sharing a row sweep needs V tokens' inputs beside the PU; filling D beats needs ≥ D tokens per command), while every command keeps every DRAM timing parameter; Fig. 5 groups the PU's structures by lever (staging buffer, accumulator file, burst drain → row reuse; weight latch, beat sequencer → beat filling).
  - Floats: Fig. 5 (fig:tile, first cite; its two brackets), Table I (CoDe row)
  - Numbers: U 0.779 (mobile) against stock 0.179 ← tables [umac_table]; CoDe's 583 / 1,247 GOPS/mm² ceilings no longer printed (left with eval-phone-per-mm2 / eval-server-area, 2026-10-30); both-order gains left IV (eval-gain-sources is their only home); the old Fig. 5 walk-through sentence cut with fig:sequence
  - Cites: —
  - Links: → des-row-reuse, des-beat-decouple, des-tile-mac-pu, eval-gain-sources
### B. Row Reuse
- **[des-row-reuse]**
  - Message: Row reuse answers III-B's non-MAC commands by letting a tile's V tokens share one row sweep, so the row-switch commands are paid once per V tokens set by V rather than by one MAC slot as in the rivals (A = 2 and 4, Table I, pointed to from the families of III-C), and the non-MAC time per token falls (absolute form; never "raises f_MAC"); Fig. 6a defines the tile in GEMM terms (V tokens × one K chunk in the GB, one bank's 2 KB row = one output's weights, V sums), Fig. 6b's lanes show stock AiM paying a row switch and a drain per token against one row switch per tile.
  - Floats: Fig. 6 (fig:mapping, first cite; a, b lanes and table), Table I
  - Numbers: M = V = 8; 2 KB row; row opens 8 → 1, column reads 512 → 64 ← map; t_row / A + t_tok plus refresh per token; non-MAC time per token 123.39 → 22.15 ns (mobile, V = 8), 146.17 → 43.51 ns (edge server, V = 4) ← tables [umac_table] (row-reuse-only 2,629 ns cut with fig:sequence; 3,250 → 738.75 ns, 4.40× moved to des-beat-slot-factor; 4.32× whole-GEMM asserted in map only)
  - Cites: —
  - Links: ← mot-nonmac-classes, mot-other-pim (closing), mot-two-levers; → des-storage, eval-gain-sources
### C. Beat Filling
- **[des-beat-decouple]**
  - Message: Beat filling answers III-B's idle beats by running the PU's beats at its own clock f_PU = D / t_col, so a tile MAC holds its column for V/D periods while the PU runs one beat per token (walked on Fig. 6b's enlarged tile MAC: one read → 8 beats, 4 per column period, next tile MAC 2 periods later, burst drain after the last column).
  - Floats: Table III, Fig. 6 (b, zoom)
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
  - Numbers: lanes (Table III) ← structural
  - Cites: —
  - Links: ← intro-contributions, des-tile-mac-overview
- **[des-storage]** "Storage"
  - Message: The global buffer, the staging buffer and a double-set accumulator file hold the tile's inputs and partial sums.
  - Floats: Table III
  - Numbers: 2,048 INT8 inputs, 2 KB per token, 16 KB GB, 512 writes of 32 B ← map; three-entry queue of 512-bit words; two / four sets of V slots ← structural (Table III ← tables [table4])
  - Cites: —
  - Links: ← des-row-reuse
- **[des-tile-size]** "Tile size"
  - Message: The tile size V sizes only CoDe's storage, so V is set by the range of M a platform serves: V = 2D = 8 on the mobile platform and V = D = 4 on HBM2.
  - Floats: —
  - Numbers: V = 8 / 4; 4 KB K chunk, 512-bit slice ← structural
  - Cites: —
  - Links: → eval-vsweep-summary, eval-vsweep-robust
- **[des-pu-clock]** "PU clock"
  - Message: CoDe needs a PU clock above the column rate, not one equal to CK, and the tile keeps that clock within the reach of III-D's DRAM silicon because each accumulator slot takes one update per V ≥ D beats and the lanes multiply narrow integers.
  - Floats: —
  - Numbers: — (precedent and its citations live only in mot-pu-clock-precedent)
  - Cites: —
  - Links: ← mot-pu-clock-precedent; → meth-designs-area, eval-power
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
  - Message: The mobile platform pairs a Snapdragon 8 Gen 3 NPU with PIM on x64 LPDDR5-6400, and the edge server pairs P3-LLM's NPU with one HBM2 stack (Table III).
  - Floats: Table III (configuration table: platform block above design block; float defined at V-A's start)
  - Numbers: platform block (NPU 12 / 131 TOPS, 42 / 256 GB/s; LPDDR5-6400 / HBM2 2.0 Gb/s; 4 dies × 16 / 16 pCH × 16 banks; 409.6 / 1,024 GB/s; t_CK 1.25 / 1 ns; t_CCD_S, t_CCD_L 2.5, 5 / 2, 4 ns; PU per bank / per two banks; t_REFI, t_RFCab 3.906 µs, 280 ns / simulator preset; INT8 / W4A8) ← tables [platform_block] (dac_sd8g3 ev57_host, ev57_ceilings, ev56_mech_inputs, context.md; dac_2x2 ev57_host, ev57_ceilings, dacp_inputs, dac2x2_setup, utrace_run_core8_gbfill; EV-58 dac_table4) and cited spec values; prose: 12 TOPS for INT8 [assumption], 131 TOPS peak [assumption]; 30 µs [assumption] ← npufaster; 2.285 W [assumption] ← derived from cites, no script; 55 W [assumption] ← tpuv4i
  - Cites: sd8g3, lpspec, hao2025, npufaster, heterollm, tman, p3llm, tpuv4i
  - Links: ← bg-aim-pu, mot-roofline-setup
### B. PIM Designs and Area
- **[meth-designs-area]** (label sec:method:designs)
  - Message: Every design computes at its platform's precision (back-reference to mot-breakdown-setup) on one controller, and CoDe reaches LP-Spec-style's peak on 0.539× its logic area by spending area on storage instead of arithmetic.
  - Floats: Table III
  - Numbers: V = 8 / V = D = 4; 0.539×; arithmetic 0.73 / 0.34, storage 0.32 / 0.10; HBM2 0.56× and 1.33× ← tables [table4, area_split]
  - Cites: aimjssc
  - Links: ← des-tile-size, des-pu-clock, mot-breakdown-setup (precision); → eval-gemm-per-mm2 (0.539× / 0.56×), eval-vsweep-summary
### C. Simulator and Models
- **[meth-simulator]**
  - Message: A cycle-level AiM simulator on Ramulator 2.0 times every design's commands, including JEDEC refresh, and synthesis-based models give area, peak power and energy per token.
  - Floats: — (Fig. 7 fig:gemm float defined at V-C's start)
  - Numbers: 1.78× vs 1.6× ← tables [phone_levels]; U 0.355 → 0.351 ← tables [umac_table]; t_REFI / t_RFCab → Table III [assumption]; ρ 0.070 ← tables [umac_table]; 45 nm → 1z by AttAcc's estimated GEMV-unit area, Nangate45, 1.05 V; 87.6 / 54.8 mW fetch ← tables [table_power]
  - Cites: ramulator2, cent, p3llm, attacc, abc, openroad, horowitz
  - Links: ← mot-rowswitch-cost (refresh), mot-sweep-factor (ρ); → eval-power
### D. Algorithms and Workloads
- **[meth-workloads]** (label sec:method:work)
  - Message: The mobile platform runs speculative decoding of Llama-2-7B with a 1.1B draft (EAGLE head only in VI-D) and the edge server batched decoding of five LLMs at a 4K context; end to end every system runs M = 4 (mobile) and batch 8 (edge server); NPU only runs everything on the NPU, NPU + X runs every weight GEMM and attention layer on PIM design X and the element-wise work on the NPU; GEMMs use six FC shapes (mobile) and 25 (edge server).
  - Floats: —
  - Numbers: acceptance 0.7; L = 1024; M = 4, batch 8; six / 25 FC shapes ← configuration (sd8g3 §2f, 2x2 §2p)
  - Cites: eagle
  - Links: → eval-gemm-summary, eval-e2e-phone, eval-e2e-server, eval-vsweep-robust (EAGLE)
### E. Metrics
- **[meth-metrics]**
  - Message: GEMM speed is operations over time including the output drain, relative to stock AiM; end-to-end speed is tokens per second, relative to NPU only; area efficiency divides either throughput by the PIM logic area (Table III); energy is system energy per token; edge-server values are geometric means over the five models (the C-bus counting rule and the M / L range rule left with eval-server-beats and VI-A's old ranges).
  - Floats: Table III
  - Numbers: —
  - Cites: —
  - Links: → eval-gemm-summary, eval-e2e-phone

## VI. Evaluation  (sections/06_evaluation.tex)  — restructured 2026-10-30 (user): A GEMM level (Fig. 7), B end to end (Fig. 8), C energy and peak power, D ablation; LP-Spec-style's comparison headline is throughput per logic mm² wherever it appears
- **[eval-modelled]**
  - Message: All results are modelled, and ratios above 1 favour CoDe.
  - Floats: —
  - Numbers: —
  - Cites: —
  - Links: —
### A. GEMM Speed and Area Efficiency
- **[eval-gemm-summary]**
  - Message: CoDe matches LP-Spec-style's GEMM speed on about half its logic and outruns P3-LLM-style once a GEMM has more than two token rows; Fig. 7 plots speed-up over stock AiM and GOPS per logic mm² against M (rows mobile / edge server), with the NPU as a line, gmean over the FC shapes.
  - Floats: Fig. 7 (fig:gemm, first cite)
  - Numbers: — (FC shapes in meth-workloads)
  - Cites: —
  - Links: ← intro-contributions, mot-wider-pu, mot-faster-pu, meth-workloads, meth-metrics
- **[eval-gemm-speed]** "GEMM speed"
  - Message: Up to M = 2 the column period paces every design; from M = 3 P3-LLM-style needs a second pass while CoDe fills up to D = 4 beats per command, and LP-Spec-style fills four with 4× multipliers, so its curve coincides with CoDe's (to M = 4 mobile, every M edge); CoDe's eight-token mobile tile covers M = 5–8 in one row sweep.
  - Floats: Fig. 7a
  - Numbers: 1.96–1.97× at M = 2; 3.74× / 3.82× vs P3-LLM-style 1.95× at M = 4; 1.62× LP-Spec-style at M = 5 (mobile) ← gemm (sd8g3 §2f, 2x2 §2p)
  - Cites: —
  - Links: ← des-beat-slot-factor, des-mapping
- **[eval-gemm-per-mm2]** "GEMM throughput per logic mm$^2$" (headline)
  - Message: Per logic mm², CoDe nearly doubles LP-Spec-style's GEMM throughput on both platforms (same beats, area on storage instead of multipliers), and it beats P3-LLM-style from M = 3; P3-LLM-style's smaller PU leads only at M ≤ 2.
  - Floats: Fig. 7b
  - Numbers: 0.539× / 0.56× logic ← tables [table4], gemm; vs LP-Spec-style 1.86× (M ≤ 4), 1.99–2.07× (M ≥ 8), 3.01× peak at M = 5 (mobile), 1.79× every M (edge); vs P3-LLM-style 1.43× (M = 4), 1.53–1.59× (M ≥ 8) mobile, 1.46–1.48× (M = 3–4, ≥ 8) edge; 0.75× at M ≤ 2 ← gemm
  - Cites: —
  - Links: ← mot-logic-cost, meth-designs-area
### B. End-to-End Speedup
- **[eval-e2e-phone]** "Mobile platform"
  - Message: Fig. 8 runs whole decoding on the five systems (mobile M = 4, edge batch 8); on the mobile platform CoDe and LP-Spec-style decode fastest, P3-LLM-style's two-token read needs two passes at M = 4, the order holds at each system's own best M, and CoDe pulls ahead of LP-Spec-style past M = 4.
  - Floats: Fig. 8 (fig:e2e, first cite), Fig. 8a
  - Numbers: 4.37× / 4.34× NPU only at 46.4 / 46.1 tok/s; P3-LLM-style 2.96×, stock 1.81×; best M: 47.1 / 46.8 (M = 3), 43.8 / 26.5 (M = 2), NPU only 10.6 (M = 4); 1.31× at M = 5, 1.05–1.31× over M = 5–16 ← e2e (sd8g3 §2f; ev56_best L 1024)
  - Cites: —
  - Links: ← intro-code-proposal, abs-summary, meth-workloads, des-mapping
- **[eval-e2e-server]** "Edge server"
  - Message: At batch 8 only CoDe and LP-Spec-style decode faster than NPU only; at the batch where P3-LLM offloads its linear layers, CoDe decodes 1.68× faster than P3-LLM-style; NPU only overtakes CoDe from batch 16 on the gmean.
  - Floats: Fig. 8a
  - Numbers: 1.28× at 456 tok/s; stock 0.45×, P3-LLM-style 0.76×; 1.68×; batch 16 ← e2e (2x2 §2p)
  - Cites: p3llm
  - Links: ← mot-gemv-only, intro-code-proposal, abs-summary
- **[eval-e2e-per-mm2]** "Throughput per logic mm$^2$" (headline)
  - Message: At LP-Spec-style's decoding speed CoDe nearly doubles LP-Spec-style's tokens/s per logic mm² on both platforms, and CoDe's speed lead over P3-LLM-style more than repays its larger PU.
  - Floats: Fig. 8b
  - Numbers: 1.87× / 1.79× vs LP-Spec-style; 1.10× / 1.26× vs P3-LLM-style ← e2e
  - Cites: —
  - Links: ← intro-code-proposal, abs-summary, mot-logic-cost
### C. Energy and Peak Power
- **[eval-energy]** "Energy per token"
  - Message: CoDe spends the least energy per token of the five systems on both platforms, with the edge NPU idling at 55 W (gated case in one clause).
  - Floats: Fig. 8c
  - Numbers: 70.5 mJ/token; NPU only 7.9×, stock 1.80×, P3-LLM-style 1.28×, LP-Spec-style 1.04× (mobile); NPU only 1.48×, P3-LLM-style 1.64×, LP-Spec-style ties (edge, 55 W); gated 1.46× ← e2e
  - Cites: —
  - Links: ← intro-code-proposal, abs-summary, meth-platforms (55 W)
- **[eval-power]** "Peak power" (merges the former eval-power-peak, -clock-cost, -edge-charge, -gating)
  - Message: CoDe's faster PU clock keeps its peak power within a few percent of LP-Spec-style's, each clock edge draws several times less charge, and clock gating is an option (every other number ungated).
  - Floats: Table III
  - Numbers: 1.04× per die, 1.03× per pCH; 522 pJ per 1.25 ns vs 1,776 pJ per 5 ns, 3.4× / 3.1×; gated 0.92× / 0.87× ← tables [table_power] (2.4 % clock cost, 2.9× / 2.8× leakage, −11.6 / −15.1 % no longer printed)
  - Cites: —
  - Links: ← meth-simulator, des-pu-clock
### D. Ablation Study
- **[eval-gain-sources]** "Sources of CoDe's gain" (moved from VI-B to VI-D, 2026-10-30; the both-sources-from-one-mechanism sentence cut)
  - Message: CoDe's gain over stock AiM comes from beat filling, which raises the slot factor, and row reuse, which keeps the sweep factor near stock AiM's level once beat filling shortens the MAC slots; beat filling earns its full step only after row reuse has removed most of the row-switch overhead (relative form; never claims CoDe raises f_MAC on the edge server).
  - Floats: Table IV (first cite), Table I
  - Numbers: steps 1.24× / 1.15× after row reuse (Table IV); U 0.223 / 0.222 after row reuse; beat-filling step 3.49× / 3.33×; CoDe f_MAC 0.779 / 0.739 vs stock 0.717 / 0.771 (Table IV); other order (beat filling alone, defined here as a per-sweep rule: a quarter of stock AiM's MAC slots plus its non-MAC time; moved from des-beat-slot-factor) f_MAC = U 0.425 / 0.506, steps 2.37× then 1.83× and 2.62× then 1.46× (only home of the both-order gain) ← tables [umac_src_table] (2x2 §2i)
  - Cites: —
  - Links: ← des-tile-mac-overview, des-beat-slot-factor, des-row-reuse
- **[eval-vsweep-summary]** "Choice of tile size" (run-in head added 2026-10-30, as it follows eval-gain-sources)
  - Message: Throughput per logic mm² peaks at V = D on both platforms, and the mobile platform's V = 8 bounds the per-mm² loss across a decode step's token rows.
  - Floats: Fig. 9 (first cite)
  - Numbers: V 1–64 at M = 64; M = 1–16 ← vsw
  - Cites: —
  - Links: ← des-tile-size, meth-designs-area
- **[eval-vsweep-gain]** "Gain by tile size"
  - Message: Up to V = D a larger tile fills idle beats, and beyond V = D it removes only row-switch commands.
  - Floats: —
  - Numbers: 3.86× / 3.69× at V = D, 4.90× / 4.39× at V = 64; 72 / 21 / 7 %; 91.6 %; 18.9 → 10.4 %; 20.5 µs ← vsw (2x2 §2k)
  - Cites: —
  - Links: ← des-tile-size
- **[eval-vsweep-area]** "Area against speed"
  - Message: Past V = D CoDe's storage grows faster than its speed, so both per-mm² curves peak at V = D.
  - Floats: Fig. 9
  - Numbers: 3.01× / 2.34×; +16 % (1.212 → 1.406 mm²), +40 % (0.821 → 1.153 mm²); break-even 1.160× / 1.405×; 1.117× / 1.089×; 96.3 % / 77.5 % ← vsw (2x2 §2k, §2l)
  - Cites: —
  - Links: ← des-tile-size
- **[eval-vsweep-robust]** "Robustness across $M$"
  - Message: Partial last row sweeps make V = 8 win per mm² at several M on the mobile platform, and V = 8 caps the worst per-mm² loss over M = 3–16 at 13.8 % against V = 4's 29.4 %.
  - Floats: Fig. 9
  - Numbers: wins at M = 5–7, 9–10, 13–15; 1.324× and 0.862×; HBM2 peak 0.944×; 29.4 / 24.5 % vs 13.8 %; HBM2 11.7 % vs 28.8–30.0 %; one-tile 4.6 / 13.8 %, its token load 28.3 % of stock AiM's time at M = 8 (one GB fill serves one row sweep; moved from mot-load-refresh-cost) ← brk; best M = 3 / 4 ← vsw (2x2 §2l–2n)
  - Cites: —
  - Links: ← des-tile-size, meth-workloads (EAGLE), eval-e2e-phone (best M 3 with the 1.1B draft), mot-breakdown-setup (Fig. 3 one tile)

## VII. Conclusion  (sections/07_conclusion.tex)
- **[conc-summary]**
  - Message: Decoupling MAC timing from DRAM command timing lets one column command feed many PU beats over a tile of tokens, and the decoupling carries over to any DRAM whose column outlasts one beat.
  - Floats: —
  - Numbers: 1.87× per logic mm² at matched speed; 1.68× ← e2e
  - Cites: —
  - Links: ← mot-depth, eval-e2e-per-mm2, eval-e2e-server

## Float map
| float | label | source file | first cite | lands |
|---|---|---|---|---|
| Fig. 1 | fig:dram_pim | figs/fig_dram_pim.pdf (01_introduction.tex) | intro-pim-gemv-ceiling (p1 L) | p1 R |
| Fig. 2 | fig:roofline | figs/fig_roofline.pdf ← roof (01_introduction.tex) | intro-pim-gemv-ceiling (p1 L) | p2 L |
| Fig. 3 | fig:breakdown | figs/fig_breakdown.pdf ← brk (03_motivation.tex, after mot-breakdown-setup) | mot-breakdown-setup (p3 L) | p3 R |
| Table I | tab:umac | tables/tab_umac.tex ← tables (03_motivation.tex, inside mot-utilization) | mot-utilization (p4 R) | p4 R |
| Fig. 4 | fig:timeline | figs/fig_timeline.pdf ← make_fig_timeline.py (03_motivation.tex, after mot-wider-pu, so that it misses Table I's column) | mot-prior-families (p4 R) | p5 L |
| Fig. 5 | fig:tile | figs/fig_tile.pdf ← figs/src/fig_tile.html, html2pdf.py (04_design.tex, top of IV) | des-tile-mac-overview (p6 L) | p6 L |
| Fig. 6 | fig:mapping | figs/fig_mapping.pdf ← map, html2pdf.py (04_design.tex, after IV-A) | des-row-reuse (p6 L) | p6 R |
| Table II | tab:cmds | tables/tab_cmds.tex ← map (04_design.tex) | des-command-set (p7 L) | p7 R |
| Table III | tab:params | tables/tab_params.tex ← tables [platform_block, table4] (05_methodology.tex, V-A) | bg-dram-channel (p2) | p8 L (configuration table: F12 exception; first cite in V on p8) |
| Fig. 7 | fig:gemm | figs/fig_gemm.pdf ← gemm, html2pdf.py (05_methodology.tex, figure* at V-C's start) | eval-gemm-summary (p9 L) | p9 top, both columns |
| Fig. 8 | fig:e2e | figs/fig_e2e.pdf ← e2e, html2pdf.py (06_evaluation.tex, figure* after eval-gemm-per-mm2) | eval-e2e-phone (p9 R) | p10 top, both columns |
| Fig. 9 | fig:vsweep | figs/fig_vsweep.pdf ← vsw (06_evaluation.tex) | eval-vsweep-summary (p10 R) | p11 L |
| Table IV | tab:umac_src | tables/tab_umac_src.tex ← tables (06_evaluation.tex, end of VI) | eval-gain-sources (p10 L) | p11 R (next page; p10's top holds Fig. 8) |
| Eq. 1 | eq:fmac | 03_motivation.tex | mot-sweep-factor | p4 L |

## Observations
| # | kind | where | observation |
|---|---|---|---|
| 1 | resolved | mot-nonmac-classes … mot-utilization | Resolved again (user, 2026-10-28): III-B now runs setup (mot-breakdown-setup) → Non-MAC commands (classes, non-MAC cost with row switch first, sweep factor; mot-load-refresh-cost merged into mot-rowswitch-cost, user 2026-10-29) → Idle beats (idle beats, cause) → mot-utilization (U, Table I, transition to III-C). Before (user plan, 2026-10-27): split into Non-MAC commands (what each command costs per row sweep; row switches outlast the useful MAC work) and Sweep factor (Eq. 1, Table I, f_MAC 0.717, U 0.179). Was: one paragraph (≈ 30 source lines, ≈ 25 numbers) carries the f_MAC formula and fit, the per-command row-switch split, token load against GB fills, refresh, the edge-server totals and stock U = 0.179; class names are used before this paragraph defines them. |
| 2 | two messages | meth-simulator | One paragraph carries five topics: the simulator and PU model, P3-LLM validation and C/A re-timing, refresh, area scaling, and the power/energy flow. |
| 3 | two messages | eval-vsweep-robust, mot-logic-cost, eval-e2e-phone | eval-vsweep-robust (minimax choice of V = 8) and mot-logic-cost (logic-die designs) still add a second claim; eval-e2e-phone carries the figure setup, the M = 4 result, the best-M check and the M ≥ 5 lead. The former eval-phone-per-mm2 / -energy / eval-server-beats cases left with the VI restructure (2026-10-30). |
| 4 | placement | eval-gain-sources | Since 2026-10-30 eval-gain-sources opens VI-D (Ablation Study), which fits its stock-to-CoDe, both-platform scope; Table IV still lands on the page after its citation (cite p10 L, table p11 R; p10's top holds Fig. 8). It remains the only home of the both-order gain. |
| 5 | resolved | eval-gain-sources | Resolved (user plan, 2026-10-27): des-gain-order deleted; the both-order gain lives only in VI-B (2.37× / 1.83×, Table IV values); the 2.3 % reconciling sentence left IV-B. Was: the two-order gain printed 2.39× then 1.84× (Fig. 5 window) in IV-A and 2.37× then 1.83× (one layer, Table IV) in VI-B; only des-beat-slot-factor's 2.3 % sentence reconciles them. |
| 6 | restatement | intro-prior-families / mot-prior-families; intro-timing-insight / mot-depth; mot-idle-beats / mot-depth | The two families are named in I and III-C; mot-depth now points to Table III for the column period and CK instead of reprinting the intro's 5 ns / 4 ns / 0.8–1 GHz, and mot-idle-cause's column-access argument is now one sentence (each column command reads one column; t_CCD spacing), leaving the latched-column argument to mot-depth. D is now defined once, in bg-aim-pu (its first point of need), and III and IV point back to it (resolves "D derived late"); intro-timing-insight still derives D = t_col × f_PU itself (introduction untouched). |
| 7 | restatement | des-tile-size / meth-designs-area; intro-prior-families / mot-logic-cost | The reason for V = 4 on HBM2 (twice the slice, one PU per two banks) is given in IV-D and again in V-B; LP-Spec's 16.92 % is printed in I and III-C; 0.539× appears in I, V-B and VI-A. |
| 8 | config table | Table III (tab:params) | One configuration table in V-A (platform block above design block); III–VI refer to it. Kept in prose where the sentence computes or derives: intro's 5 / 4 ns, 0.8 / 1 GHz and 42 GB/s (D and the ridge), III-A's 42 GB/s derivation, IV-D's GB / slice sizes, VI-C's 1.25 / 5 ns per-edge charge (the 800 / 200 MHz clock-cost sentence left on 2026-10-30). Row size has no collected source and stays out (for evaluation-owner). |
| 10 | promise | intro-code-proposal, intro-contributions | No intro paragraph announces the ablation (VI-D: sources of gain, tile size) or the peak-power study (VI-C); these results answer only des-tile-size, des-pu-clock and meth-simulator. |
| 11 | untraced number | meth-platforms, Table III | 2.285 W host power (derived from cites, no script); Table III's t_REFI 3.906 µs is asserted from evaluation/dac_sd8g3/context.md text ([A-REF1]) and t_RFCab 280 ns from the collected trace (utrace_run_core8_gbfill REFab gap), neither has a JEDEC cite; 131 TOPS (assumption with cite only); 56 / 68 / 51.2 GB/s (cites; only the 42 GB/s result is asserted). |
| 12 | resolved | eval-power | Resolved (2026-10-30): the 2.4 % clock cost (microarch pu_peak_power.csv, never collected) is no longer printed; make_tables.py keeps its assert as a guard. |
| 13 | structure | mot-other-pim | Stays last in III-C (user, 2026-10-27); no related-work section remains (options kept for later: (a) a short Related Work section before the Conclusion, from the ≈ 1 free column; (b) a landscape paragraph at the end of II-B; (c) keep it as the last paragraph of III-C, as now). mot-other-pim now closes III-C with the C → D transition (a column read feeds several tokens only through added multipliers or commands; a row sweep serves one MAC slot's tokens). Labels `sec:bg:*` point into Section III (cosmetic). |
| 14 | unverified source | mot-other-pim (closing), des-row-reuse, mot-idle-cause | LP-Spec's own text on row activations was not checked: no LP-Spec PDF exists under 00_doc (paper_isca2's is empty; paper_dac's references hold p3llm.pdf, the AiM JSSC paper and others, not LP-Spec), so LP-Spec-style's sharing of a row sweep among its four tokens rests on our model (Table I, A = 4). P3-LLM's own text (p. 11) supports its two-token row-activation saving. HBM-PIM's statement of a GEMV target was not checked (no PDF); AiM JSSC p. 1 (RNN and MLP layers with low memory reuse, evaluated on GEMV) and P3-LLM p. 3 (both PCUs perform GEMV) were. |
| 15 | timing | Table III, mot-idle-beats | HBM2's column period prints t_CCD_L = 4 ns (cited) while the simulator's all-bank HBM2 MAC slot is 8 ns (b = 2, two banks per PU; dac2x2_setup); U_MAC's b = 2 reconciles them, but Table III shows no 8 ns slot. |
| 16 | resolved | mot-prior-families, mot-other-pim, mot-two-levers, des-row-reuse, eval-gain-sources | Resolved (user, 2026-10-27): f_MAC is a share, so row reuse is stated in absolute form in III-C, III-D and IV-C (it cuts the non-MAC time per token: 123.39 → 22.15 ns mobile, 146.17 → 43.51 ns edge server) and in relative form in VI-B (it keeps f_MAC near stock AiM's level once beat filling shortens the slots: 0.779 / 0.739 vs 0.717 / 0.771). Guard: no sentence says CoDe raises f_MAC on the edge server (0.739 < 0.771) or frames the rivals' flat f_MAC as their defect; only the D = 1 row-reuse-only row lifts f_MAC (0.892 / 0.887). |
| 17 | ordering | mot-logic-cost, mot-faster-pu | With logic cost before the faster-PU family (user order), mot-logic-cost compares LP-Spec-style's per-mm² ceiling with stock AiM's (314 / 697 vs 216 / 492) and P3-LLM-style's 390 / 830 moved into mot-faster-pu after P3-LLM-style is named. |
| 18 | restatement | intro-prior-families, intro-timing-insight vs mot-prior-families, mot-depth | The introduction still repeats III-C's two families and III-D's insight (and derives D itself); left untouched by the III/IV mirror pass (user plan, 2026-10-27). |
| 19 | resolved | eval-gemm-per-mm2 | Resolved (2026-10-30): the per-mm² ceilings of CoDe (583 / 1,247 GOPS) are no longer printed beside measured ratios; VI-A prints measured GEMM ratios against M only. |
| 20 | dropped number | des-row-reuse | The whole-GEMM 4.32× (CoDe vs stock AiM, q_proj, M = 8) left IV with des-gain-order; no other section printed it, and the 4.40× window carries IV-C's claim. Still asserted in make_fig_mapping.py; it could return to VI-B if a whole-kernel number is wanted. |
| 21 | resolved | mot-rowswitch-cost vs des-row-reuse | Resolved (user, 2026-10-29): III-B prints q_proj shares only, so the edge non-MAC time appears once, as 146.17 ns per token (IV-C, Table I). Was: 146.2 ns per row sweep in III-B and 146.17 ns in IV-C. |
