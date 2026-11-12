# Commands Are the Bottleneck: CoDe, a Command-Decoupled PIM for Skinny GEMMs on Mobile and Server DRAM: outline
Synced with: c324ba7; ACM sigconf (acmart, 9 pt) since 2026-11-10; bold run-in heads (`\runin`) since ff51469; edge-server P3-LLM-style at P3-LLM's own placement since b992b75; measured weight-I/O cause of the gated 2.08× since a1e9db4; VI-F Beat Filling on Newer DRAM since 214bcc5, its second trend points back to III-D since d592c11; DOTS credited for row-activation sharing, CoDe's novelty over it stated in III-C / IV-B since a448dfd, row-reuse-only design untied from DOTS and IV-B's column-read difference since c32defd; IV-C contrasts beat filling with P3-LLM's command-started MACs since 191da5e; mobile operating point M = 8 since 69055c5; area-efficiency reframing, VII Discussion (VII-A storage versus arithmetic, Fig. 10; VII-B = former VI-F) and VIII Conclusion since 463abcf; logic area on Synopsys DC / SAED14 × 10 since 9735faa; PU timing met in synthesis (intro, IV-D) since 762f818; SAED14 cited (V-C) and Fig. 9 per-mm² in CoDe tint since c324ba7: body ends p. 12 R (about 1.2 columns past p. 11); refs p. 12 to p. 14.
Legend: one entry per source paragraph, in source order, tied to the `.tex` by `% P:<id>`; Message = the one claim a reader takes away; Floats = figures/tables/equations cited (first cite marked); Numbers = key printed numbers ← the script that asserts them (evaluation topic in brackets); Cites = bib keys; Links = → promise fulfilled by <id>, ← relies on <id>. Check: `python3 scripts/check_outline.py`.

Number sources, short names: `tables` = scripts/make_tables.py (functions in brackets); `storage` = make_fig_storage.py (rows 114–115, 2x2 §2u); `roof` = make_fig_roofline.py; `brk` = make_fig_breakdown.py; `map` = make_fig_mapping.py; `vsw` = make_fig_vsweep.py; `gemm` / `e2e` = make_fig_gemm.py / make_fig_e2e.py (ISCA ids `isca.gemm.*`, `isca.e2e.*`). Evaluation topics: `2x2` = evaluation/dac_2x2, `sd8g3` = evaluation/dac_sd8g3 (EV-58 pack via scripts/dac_data.py).

## Abstract  (sections/00_abstract.tex)
- **[abs-summary]**
  - Message: Speculative decoding and small batches turn decoding's GEMVs into memory-bound skinny GEMMs that suit PIM, but stock PIM, built for GEMVs, fills under a fifth of its GEMM time with useful MACs because a DRAM command paces every MAC; prior PIM fills the idle beats at a cost (4× the multipliers in a die that builds logic 10× less densely than an ASIC, or one command per token, at most two tokens per read), whereas DRAM timing bounds column reads, not the MACs on a read, and an all-bank column already spans four command clocks; CoDe spends those cycles instead of multipliers (row reuse, beat filling) and returns 1.87× LP-Spec-style's tokens/s per logic mm², 1.60× faster at about equal logic, and 1.41× P3-LLM-style's speed on HBM2. Order (first half user-approved 2026-11-08, kept verbatim; second half user-approved 2026-11-11, area-efficiency reframing): context → skinny GEMM, host memory-bound → PIM fits, stock PIM falls short → characterization (useful share, two root causes) → common cause → the cost of prior fixes → the timing insight → CoDe's two techniques → results (area efficiency against LP-Spec-style first, speed against P3-LLM-style).
  - Floats: —
  - Numbers: M 2 to 32 ← cited ranges (bg-skinny-range); useful 14.1–19.1 %, non-MAC 23.4–43.7 %, idle 42.2–57.4 % ← brk (2x2 §2j); four times the multipliers (intro-prior-families), ten times less densely (devaux; intro-timing-insight, mot-logic-cost), two tokens per read (intro-prior-families, mot-faster-pu), four command-clock cycles (bg-aim-pu) ← cited / structural; mobile (M = 8): 1.87× tok/s per logic mm² (isca.e2e.phone.M8.core8_over_h2.per_mm2) ← e2e; 1.60× faster at about the same logic area (LP-Spec-style as published, 0.90× CoDe's logic, eval-placement; the abstract keeps "about the same logic area", brief 2026-11-11; lpsv.phone.loop.core8_over_h2sh.speed_M8) ← tables [lpsv_checks]; HBM2 batch of 8: 1.41× P3-LLM-style (P3-LLM's own placement) and 1.28× NPU only ← e2e. The 1.07× and 0.574× left the abstract (user, 2026-11-11; body only).
  - Cites: —
  - Links: → intro-code-proposal, mot-breakdown-setup, mot-logic-cost, mot-depth, des-row-reuse, des-beat-decouple, eval-e2e-overview, eval-e2e-lpspec, eval-e2e-p3, eval-placement, disc-storage-claim
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
  - Message: DRAM timing parameters space the column commands that access the array, not the MACs on a latched column, so one column period can feed D = 4 PU beats, and our pipelined PU meets timing in synthesis at 0.8 GHz (LPDDR5-6400) and 1 GHz (HBM2), the clocks at which it fits D = 4 (→ des-pu-clock; since 2026-11-11); closing (user, 2026-11-11): a DRAM die builds logic ten times less densely than an ASIC, so multipliers are the costliest way to fill idle beats, whereas the beats themselves come with the column period.
  - Floats: —
  - Numbers: 5 ns (LPDDR5-6400), 4 ns (HBM2) column; 1 GHz PU in silicon; 0.8 / 1 GHz met in synthesis ← timing.saed.{phone,hbm2}.core.{met,clk_MHz} (2x2 §2v) ← tables [timing_checks]; D = 4; ten times less densely (devaux, as in mot-logic-cost) ← cited / structural
  - Cites: hbmpim, lpspec, aimjssc, devaux
  - Links: → mot-depth, mot-pu-clock-precedent, des-pu-clock
- **[intro-code-proposal]**
  - Message: CoDe runs D beats per column command over a tile of V tokens at the stock multiplier count; the beats come with the column period, so CoDe adds only the tile's storage (why it is cheap); against LP-Spec-style on the mobile platform it takes 0.574× its logic with the stock multiplier count clocked at 0.8 GHz and returns 1.87× its tokens/s per logic mm², and against LP-Spec as published (one unit per two banks, 0.90× CoDe's logic) it decodes 1.60× faster than this shared design (SAED14 areas: "about equal logic" no longer printed in the body; the abstract keeps "about the same logic area"); on HBM2 it decodes a batch of 8 1.41× faster than P3-LLM-style (P3-LLM's own placement) and 1.28× faster than NPU only, with 1.52× P3-LLM-style's energy efficiency. The 1.07× and 29.9 / 27.9 tok/s left the introduction (user, 2026-11-11; VI-B keeps them). Never "stock multipliers" bare.
  - Floats: —
  - Numbers: 0.574× logic area ← tables [table4]; 0.8 GHz (Table IV); 1.87× per logic mm² (isca.e2e.phone.M8.core8_over_h2.per_mm2) ← e2e; 0.90×, 1.60× ← tables [lpsv_checks]; 1.41×, 1.28×, 1.52× (batch 8; core4_over_p3own.speed, p3own_over_core4.mJ_55W) ← e2e
  - Cites: sd8g3
  - Links: → des-tile-mac-overview, eval-e2e-lpspec, eval-e2e-p3, eval-placement, eval-energy, eval-area-split
- **[intro-contributions]** (itemize, seven items; claim–evidence map since 2026-11-08, user-approved AI-review item 1; area-led since 2026-11-11)
  - Message: Each item states one claim, its headline number with its scope and the section that proves it: the depth analysis (III-D); the CoDe PU and command extension (IV); against the wider-PU family (area first, user 2026-11-11), under one area model with one tenfold DRAM-process factor, CoDe reaches the 4× MAC ceiling with the stock multiplier count on 0.574× LP-Spec-style's logic, 1.87× (mobile) / 1.80× (HBM2) its tokens/s per logic mm², 1.60× faster than a shared LP-Spec-style design with 0.90× its logic (mobile platform only), and logic of 2.64 % of the die / 2.28 % of the stack (VI-B, VI-D, VI-E; the former area bullet merged here); against the faster-PU family (speed first), on one DRAM timing per platform, 1.41× P3-LLM-style's speed at batch 8 on HBM2 (P3-LLM's own placement; VI-B); storage against arithmetic: filling beats with storage costs 3.5× (mobile) / 3.1× (HBM2) less added logic per unit of speed-up (VII-A); the least energy per token on the mobile platform and a tie with LP-Spec-style for the least on the edge server with a 55 W idle NPU (VI-C); the two sources of gain (VI-E). No 1.07× (user, 2026-11-11).
  - Floats: —
  - Numbers: D = 4 (LPDDR5-6400, HBM2) ← structural; 0.574× ← tables [table4]; 1.87× / 1.80× ← e2e; 0.90×, 1.60× ← tables [lpsv_checks]; 2.64 % / 2.28 % ← tables [budget_checks]; 1.41× ← e2e; 3.5× / 3.1× (aps.<p>.h2.kernel_M8.ratio_to_core 3.47 / 3.11) ← storage; 105.8 mJ (isca.e2e.phone.M8.core8.mJ_tok) ← e2e; 1.24× / 3.49× (beat filling's total over row reuse alone, D = 1 → 4; "adds 3.49×") ← tables [umac_src_table] (every number also printed in VI or VII)
  - Cites: —
  - Links: → mot-depth, des-command-set, des-tile-mac-pu, eval-e2e-lpspec, eval-e2e-p3, eval-placement, eval-area-budget, eval-area-split, disc-storage-claim, eval-energy, eval-gain-sources
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
  - Links: ← intro-pim-gemv-ceiling, mot-host-roof; → mot-a-summary, meth-systems (the evaluation's NPU + P3-LLM-style follows this placement on the edge server, 2026-11-10), eval-e2e-p3
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
  - Links: ← mot-breakdown-setup, bg-mac-sequence (commands defined there; III-B only groups them into classes), bg-row-sweep; → mot-rowswitch-cost, mot-sweep-factor, mot-other-pim (closing: only DOTS shares a row's activation beyond one MAC slot's tokens), des-row-reuse
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
  - Message: Wider-PU designs trade area for MAC throughput by filling the idle beats with more multipliers per PU (opener), so LP-Spec-style, the mobile rival, reaches U_MAC = 1 only by quadrupling the multipliers, and per multiplier its U stays below stock AiM's (closing). LP-Spec shares one unit between two banks; we give LP-Spec-style one unit per bank on the mobile platform (on HBM2 every design shares one PU between two banks, Table III), SK hynix AiM's layout (aimjssc) and Samsung's maximum-performance option (hc35pim), and VI-E (eval-placement) evaluates the published sharing (2026-11-10; the per-bank design is the main rival everywhere; never "stronger": per mm² the shared variant narrows CoDe's lead to 1.44×).
  - Floats: Fig. 4 (column periods T of D = 4 beats defined for reading it), Fig. 2, Table I, Table IV
  - Numbers: four 32-wide ALUs, one MAC step per column period (200 MHz → Table IV); Fig. 4 counts: stock 8 column periods / 8 commands / 8 reads, LP-Spec 2 / 2 / 2 (M = 8, D = 4 from II-B) ← structural; crossover M = 20–24; U per multiplier 0.173–0.174 / 0.185 ← roof, tables [umac_table]
  - Cites: lpspec, aimjssc, hc35pim, papi, stepstone, duplex, h2llm, monde
  - Links: ← intro-prior-families, mot-prior-families, mot-idle-beats; → mot-logic-cost, mot-two-levers (area a PIM die gives to beat filling), eval-gemm-summary (ref → Section VI since 2026-10-30), eval-placement
- **[mot-logic-cost]** "Cost of logic in a DRAM die"
  - Message: Logic in a DRAM die costs capacity, so per logic mm² the wider-PU family keeps only part of its four-fold ceiling over stock AiM; one sentence reconciles LP-Spec's own 16.92 % with our LP-Spec-style's 4.60 %: LP-Spec's estimate includes register files of 50,688 bits per matrix unit, our model keeps only the accumulators its dataflow needs, which favours LP-Spec-style ("includes", never "mostly"; 9.80 / 12.08 mm² never printed: 16 vs 8 register-file sets unresolved, sd8g3 context §5 row 40).
  - Floats: Table IV (4.60 % = its 2.800 mm² over V-C's 60.92 mm² die, meth-area-model; the VI-D print of the share was cut 2026-11-10, user review 2)
  - Numbers: 10× less dense, 3 vs 10+ metal layers (UPMEM's report, devaux); 0.19 mm² per PU; 50 % capacity ← hbmpim (halved sub-arrays, p. 8); 16.92 % for compute units and buffers (lpspec p. 7) vs 20–25 % ← cited; 16.92 asserted from budget.lpspec_own.pct_of_die_1z, 50,688 bits ← budget.lpspec_own.rf_bits_per_mpu, 4.60 % ← budget.phone.h2.pct_of_die_1z ← tables [lpsv_checks, budget_cells] (pointer: Table IV; this is now the share's only print); LP-Spec-style 293 / 591 vs stock AiM 203 / 431 GOPS/mm² (SAED14 × 10 areas) ← roof
  - Cites: devaux, aimjssc, hbmpim, lpspec
  - Links: ← intro-prior-families, mot-wider-pu, meth-area-model (die area); → eval-gemm-per-mm2, eval-e2e-lpspec, eval-area-budget (AiM's 20–25 % printed here only; VI-D points back)
- **[mot-faster-pu]** "Faster-PU family"
  - Message: Faster-PU designs speed up the PU but still start every MAC with a command, so DRAM command timing, not the PU clock, caps them at two beats per column read (opener; the user's top point in this paragraph): commands issue every t_CCD_S, half of t_CCD_L, so P3-LLM-style, the edge-server rival, stops at U_MAC = 1/2 however fast its PU runs, yet keeps a higher ceiling per logic mm² than LP-Spec-style. P3-LLM shares one PU between two banks (stated like LP-Spec's placement in mot-wider-pu; p3llm p. 7, Sec. IV-A: "8 PCUs, each of them is shared by 2 banks").
  - Floats: Fig. 4 (P3-LLM row), Fig. 2, Table IV, Table III (placement row)
  - Numbers: one beat per t_CCD_S (500 MHz → Table IV); one PU per two banks ← p3llm p. 7; Fig. 4 counts 4 column periods, 8 commands, 4 reads ← structural; U_MAC stops at 1/2 wherever t_CCD_L = 2 t_CCD_S; crossover M = 4–6; 361 / 718 GOPS/mm² ← roof
  - Cites: p3llm, hbmpim
  - Links: ← bg-dram-channel, intro-prior-families, mot-prior-families, mot-idle-beats, mot-logic-cost; → mot-depth (the per-token command is what a PU at CK must drop), eval-gemm-summary (ref → Section VI since 2026-10-30)
- **[mot-other-pim]**
  - Message: The remaining LLM PIM designs either serve one input vector per weight read or reorganize the work around the PU, and the three that run several beats per column read still hold one vector (CD-PIM's host-GEMM clause cut 2026-11-10; the Precision-Flexible PU spends a column interval's four phases on the low-bit weights packed in one column, pfpu pp. 2–3, user review 2); four designs are the closest prior art: three run several beats per column read but hold M = 1; DOTS (DATE'25, Fig. 1c) holds several input vectors, keeps a weight row open across tokens with several result latches per PU, so a tile shares the row's activation, yet every token re-reads every column with its own MAC command, so each read feeds one token at one beat per column period (user, 2026-11-10: DOTS left the scheduling list; credit it for sharing a row's activation, state CoDe's novelty); closing C → D transition (true since 2026-11-10, replaces the AI-review T2 claim that no design shares a row sweep across a larger tile): across the two families and these four designs, only DOTS shares a row's activation beyond the tokens of one MAC slot, and none, P3-LLM's two-token latch included, lets one column read feed several tokens without added multipliers or commands (levers not named here: mot-two-levers names them); last sentence (user, 2026-11-11): neither family reaches the 4× ceiling without spending multipliers or commands.
  - Floats: —
  - Numbers: —
  - Cites: newton, cent, pimgpt, localut, pimpal, pimdl, pimba, paise, splitsync, pimphony, salpim, pfpu, cdpim, dots (paik2022 cut 2026-10-29; bib entry kept, uncited)
  - Links: ← mot-wider-pu, mot-faster-pu, mot-nonmac-classes (closing's row-sweep claim; the former "Row-switch commands in prior designs" paragraph was cut 2026-10-29); → mot-depth, des-row-reuse (stays last in III-C: user, 2026-10-27)
### D. The Opportunity: DRAM Timing Bounds Access, Not MACs
- **[mot-depth]**
  - Message: DRAM timing bounds how often a column is read, not how many MACs may consume it (opener); the PU's latched column stays usable after its command, so the column period sets how often weights arrive and the PU clock how often the PU computes, and a PU clocked at CK can spend all D beats of a column period on one latched column, as long as its MACs do not wait for per-token commands (conclusion; answers mot-faster-pu).
  - Floats: —
  - Numbers: — (D points back to bg-aim-pu; not re-derived)
  - Cites: hbmpim, p3llm
  - Links: ← intro-timing-insight, bg-aim-pu, mot-idle-beats, mot-idle-cause, mot-faster-pu, mot-other-pim; → des-row-reuse (power point reused), conc-summary
- **[mot-pu-clock-precedent]** (no run-in head since 2026-10-29; III-D is three unheaded paragraphs)
  - Message: A PU clocked at CK has precedent in DRAM silicon, from UPMEM's 500 MHz design (350 MHz deployed) to GDDR6-AiM's 1 GHz multipliers and an HBM-PIM-style PU at CK (the Precision-Flexible PU, whose four phases serve the low-bit weights packed in one column for one input vector, so its gain is set by packing; user 2026-11-10, AI-review novelty concern), and DRAM periphery has since gained logic-process features (HKMG at three vendors, 5–6 metal layers on 1a-nm dies); never "a PU at CK is the trend", never the vendors' pin-rate speed claims.
  - Floats: —
  - Numbers: 1.0–1.2 GHz bus, 250–300 MHz, 20 nm; 500 MHz design, 2x-nm; 350 MHz deployed ← prim (p. 5); 1 GHz, 1y-nm; eight 1y-nm dies; five to six metal layers, 1a-nm ← tid1a16, tid1a24 ← cited
  - Cites: hbmpim, devaux, prim, aimjssc, flashbolt, pfpu, tiroadmap, tid1a16, tid1a24
  - Links: ← intro-timing-insight; → mot-two-levers, des-pu-clock
- **[mot-two-levers]**
  - Message: A PU at CK fits in a DRAM die and fills idle beats at a different cost from the wider-PU family (opener): our LP-Spec-style model spends about 1.8 mm² per die on the logic it adds to stock AiM to fill the beats (Table IV: 2.800 − 1.009), whereas a PU at CK fills the same beats with storage for a tile of tokens and a beat sequencer clocked at CK (the trade, user 2026-11-11; "we", not "CoDe", inside III); we therefore keep the stock multiplier count, run it at CK, and answer each root cause of III-B with one lever: row reuse (IV-B) answers the non-MAC commands by cutting their time per token (no claim that row reuse raises f_MAC); beat filling (IV-C) uses all D beats of a column period without adding multipliers and answers the idle beats (III-B's order, since 2026-10-29).
  - Floats: Fig. 1, Table IV
  - Numbers: about 1.8 mm² per die (aps.phone.h2.dA 1.791 = Table IV LP-Spec-style 2.800 − stock 1.009) ← storage; D = 4 beats per column read, one used ← structural; no CoDe number
  - Cites: —
  - Links: ← mot-idle-beats, mot-nonmac-classes, mot-rowswitch-cost, mot-depth, mot-pu-clock-precedent, mot-logic-cost; → des-tile-mac-overview, des-row-reuse, des-beat-decouple, eval-area-split, disc-storage-cause
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
  - Message: Row reuse answers III-B's non-MAC commands by letting a tile's V tokens share one row sweep, so the row-switch commands are paid once per V tokens set by V rather than by one MAC slot as in the rivals (A = 2 and 4, Table I, pointed to from the families of III-C), and the non-MAC time per token falls (absolute form; never "raises f_MAC"); Fig. 6a defines the tile in GEMM terms (V tokens × one K chunk in the GB, one bank's 2 KB row = one output's weights, V sums), Fig. 6b's lanes show stock AiM paying a row switch and a drain per token against one row switch per tile; difference from DOTS (user, 2026-11-11; our mechanism first, the precedent as a citation): row reuse differs from DOTS's weight-stationary order in what one column read serves; DOTS keeps the row open but sweeps it once per token (one MAC command and one column read per token on every column, 512 reads for Fig. 6b's tile), CoDe's tile MAC reads each column once and latches it beside the PU for all V tokens (64 reads, 64 commands); each avoided read saves cell-access and column-decoder energy, the majority of PIM power (points back to mot-depth, sec:bg:depth), and the latched column is what beat filling (IV-C) spends in D beats.
  - Floats: Fig. 6 (fig:mapping, first cite; a, b lanes and table), Table I
  - Numbers: M = V = 8; 2 KB row; row opens 8 → 1, column reads 512 → 64 ← map; DOTS keeps 512 reads, CoDe 64 reads and 64 tile MAC commands (8 × 64, structural, make_tables dots_checks, make_fig_mapping); t_row / A + t_tok plus refresh per token (the storage-needs sentence cut 2026-11-08; des-storage carries it); non-MAC time per token 123.39 → 22.15 ns (mobile, V = 8), 146.17 → 43.51 ns (edge server, V = 4) ← tables [umac_table] (row-reuse-only 2,629 ns cut with fig:sequence; 3,250 → 738.75 ns, 4.40× moved to des-beat-slot-factor; 4.32× whole-GEMM asserted in map only)
  - Cites: dots
  - Links: ← mot-nonmac-classes, mot-other-pim (closing), mot-two-levers, mot-depth (cell-access and column-decoder power); → des-storage, des-beat-decouple (the latched column), eval-gain-sources
### C. Beat Filling
- **[des-beat-decouple]**
  - Message: Beat filling answers III-B's idle beats by running the PU's beats at its own clock f_PU = D / t_col, so a tile MAC holds its column for V/D periods while the PU runs one beat per token (walked on Fig. 6b's enlarged tile MAC: one read → 8 beats, 4 per column period, burst drain after the last column; the V/D = 2 restatement cut 2026-11-08).
  - Floats: Table III (CK), Table IV (PU clock), Fig. 6 (b, zoom)
  - Numbers: V = 8, D = 4, V/D = 2 periods ← structural (asserted in map)
  - Cites: —
  - Links: ← mot-idle-beats, mot-idle-cause, mot-two-levers, des-row-reuse (the latched column)
- **[des-beat-slot-factor]**
  - Message: Beat filling raises the slot factor from 1/4 to 1, reaching the wider-PU family's 4× ceiling with the stock multiplier count; unlike P3-LLM's faster PU, whose MACs each wait for a command every tCCD_S (at most two tokens per column read, 4 reads for Fig. 4's 8 tokens; points back to mot-faster-pu), CoDe starts its beats from the PU clock, so one tile MAC command and one column read feed all V tokens (beats per column period follow t_col × f_PU, not tCCD_L / tCCD_S) and it issues fewer MAC commands per token; joined with row reuse it makes the weight row 4.40× shorter (Fig. 6b's speedup gap).
  - Floats: Fig. 4 (family comparison, CoDe lane), Fig. 6 (b, table and speedup gap)
  - Numbers: 1/V MAC commands per token and column vs 1 (stock, P3-LLM-style), 1/4 (LP-Spec-style) ← structural; time in MAC slots 512 → 128 column periods for the same 8 × 64 MAC beats (the figure's "MAC time" column; CoDe's slot is 10 ns, so never "128 MAC slots"); weight row 3,250 → 738.75 ns, 4.40× ← map (2,560 → 640 ns and 1,360 ns cut with fig:sequence; the two-structures sentence moved to des-tile-mac-overview)
  - Cites: p3llm
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
  - Message: CoDe needs a PU clock above the column rate, not one equal to CK, and the tile keeps that clock within the reach of III-D's DRAM silicon: the PU pipelines its beats (operand registers for the latched column and token k's staging slice, multiply, registered adder tree, accumulate; consistent with the SAED14 DC configurations, inferred 3-stage — no depth is printed, no id carries it; AI-review T5, 2026-11-08), only the accumulate feeds back and each accumulator slot takes one update per V ≥ D beats, and the lanes multiply narrow integers; closing (since 2026-11-11): synthesized with Synopsys DC on a 14 nm library (→ meth-area-model), the pipelined PU meets timing at 0.8 GHz (mobile) and 1 GHz (HBM2), as PrimeTime confirms (no slack or f_max).
  - Floats: —
  - Numbers: 0.8 / 1 GHz met ← timing.saed.{phone,hbm2}.core.{met,clk_MHz} (2x2 §2v; evaluation 51e9688) ← tables [timing_checks] (precedent and its citations live only in mot-pu-clock-precedent)
  - Cites: —
  - Links: ← mot-pu-clock-precedent, intro-timing-insight; → meth-area-model, meth-designs (PU clock in Table IV), eval-power-headroom, eval-power
### E. Mapping Skinny GEMMs and Attention
- **[des-mapping]**
  - Message: CoDe maps a skinny GEMM as stock AiM does but cuts the M token rows into tiles of V, and speculative-decoding attention maps the same way while batched attention stays one GEMV per request.
  - Floats: —
  - Numbers: —
  - Cites: —
  - Links: → eval-gemm-speed, eval-e2e-overview (attention runs inside the end-to-end systems)

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
  - Message: Logic area comes from Synopsys Design Compiler (compile_ultra, DesignWare) on the SAED14 educational 14 nm library (RVT, typical corner tt0p8v25c), × 10 for UPMEM's tenfold DRAM-process density penalty [assumption]; registers priced per bit from synthesized register blocks, fixed control per PU, the GB as DRAM-process SRAM [assumption]; PrimeTime confirms timing at each PU's Table IV clock (no f_max or slack printed; all six met ← timing.saed.paper_units_met_n ← tables [timing_checks]; IV-D prints CoDe's two clocks); PU power and energy stay on the separate flow of meth-power-model (one clause); AiM's fabricated 0.19 mm² PU is 1.98× our model of it, so VI-D also scales logic and registers by 1.98 as an upper bound (since 2026-11-11, microarch 721f156 / evaluation 35c9d06; the Nangate45 × AttAcc-scaled area model is history); die shares divide by a 60.92 mm² 16 Gb LPDDR5 die (as LP-Spec reports) and by a stack of eight 84.4 mm² HBM-PIM dies standing in for plain HBM2 dies [assumption].
  - Floats: —
  - Numbers: 0.19 mm² (aimjssc p. 297); 1.98 ← budget.silicon_factor.aim; SAED14 cited at its name (saed14: Melikyan et al., SSSS 2018, the 14 nm FinFET EDK paper; verified in the proceedings PDF); DC / PrimeTime named as tools, not cited; 60.92 mm² ← budget.cite.lpddr5_die_mm2_1z (LP-Spec p. 7; its ISSCC'21 origin unread, so never cited directly); 8 × 84.4 mm² ← budget.cite.hbmpim_die_mm2, budget.hbm2.stack_mm2 ([A-XC4]) ← tables [budget_checks] (sd8g3 §2g, 2x2 §2q)
  - Floats: — (Table IV tab:designs float defined after this paragraph since 2026-11-08; lands p8 L top in the ACM build)
  - Cites: devaux, aimjssc, lpspec, hbmpim, saed14
  - Links: → eval-area-budget, eval-area-split, eval-gemm-per-mm2, eval-vsweep-area, intro-contributions (one tenfold factor, limitation; moved from eval-modelled 2026-11-08)
- **[meth-power-model]** (split from meth-simulator, 2026-11-06)
  - Message: PU power and energy come from whole-PU synthesis calibrated to CENT's AiM MAC energy at 1.05 V; energy per token charges MACs, leakage, GB reads and DRAM commands; peak power runs every PU at its full MAC rate with leakage, GB reads and the column fetch but without activation, refresh, background or I/O power, which every design draws alike, so peak power isolates the logic each design adds; CoDe adds clock gates (accumulator slots, staging words, weight latch); the rivals' gating is not stated in the paper (user, 2026-11-06); yardsticks: a full-rate x16 LPDDR5X read 447 mW, an HBM2 stack read 8.0 W.
  - Floats: —
  - Numbers: Nangate45, 1.05 V; 87.6 / 54.8 mW fetch ← tables [table_power]; 447 mW ← budget.cite.lpddr5x_read_mW_per_x16_ch (Micron Y52Q Rev. G Table 16); 8.0 W at 3.92 pJ/bit ← budget.cite.hbm2_stack_read_W, budget.cite.hbm2_access_pJ_per_bit (O'Connor p. 43) ← tables [budget_checks]
  - Cites: abc, openroad, cent, horowitz, micronlp5x, oconnor
  - Links: ← des-pu-clock; → eval-energy, eval-power
### D. Algorithms and Workloads
- **[meth-workloads]** (label sec:method:work)
  - Message: The mobile platform runs speculative decoding of Llama-2-7B with a 1.1B draft (the EAGLE-head sentence cut 2026-11-10 with VI-E's EAGLE clause, its only reader; eagle bib entry kept, uncited) and the edge server batched decoding of five LLMs at a 4K context; GEMMs use six FC shapes (mobile) and 25 (edge server); end to end every system runs M = 8 (mobile: seven drafted tokens, within the 2–8 that published mobile decoders verify, sdnpu as in bg-skinny-range) and batch 8 (edge server). Operating point stated as a fact, never as a change (user, 2026-11-11).
  - Floats: —
  - Floats: — (Fig. 7 fig:gemm, one column, float defined after this paragraph since 2026-11-08, lands p8 R top, VI-A's page; Fig. 8 fig:e2e figure* defined right after it since 2026-11-10, so that it renders at the top of p9, VI-B's page)
  - Numbers: acceptance 0.7; L = 1024; M = 8, batch 8; 2–8 drafted tokens ← sdnpu (bg-skinny-range); six / 25 FC shapes ← configuration (sd8g3 §2f, 2x2 §2p)
  - Cites: —
  - Links: → eval-gemm-summary, eval-e2e-overview, eval-e2e-p3
- **[meth-systems]** (split from meth-workloads, user 2026-11-06)
  - Message: The five systems: NPU only runs the whole model on the NPU; in NPU + X, PIM design X runs every weight GEMM and attention layer and the NPU runs the element-wise work; the one exception (user, 2026-11-10, option B, after a reviewer's "a configuration P3-LLM would not run"): on the edge server NPU + P3-LLM-style follows P3-LLM's placement at batch 8, the NPU running the linear layers and P3-LLM-style the attention layers (P3-LLM p. 13). CoDe keeps every layer on PIM; the per-class-best placement (1.24×, 0.93× per mm²) is never printed.
  - Floats: —
  - Numbers: batch 8 ← configuration
  - Cites: p3llm
  - Links: ← meth-designs (the four designs X), mot-gemv-only; → eval-e2e-overview, eval-e2e-p3, eval-energy
### E. Metrics
- **[meth-metrics]**
  - Message: GEMM speed is operations over time including the output drain, relative to stock AiM; end-to-end speed is tokens per second, relative to NPU only; area efficiency divides either throughput by the PIM logic area (Table IV) and is a primary metric beside speed, because a DRAM die pays for logic in memory capacity (pointer to III-C's HBM-PIM 50 %, not repeated; user 2026-11-11); energy is system energy per token; edge-server values are geometric means over the five models (the C-bus counting rule and the M / L range rule left with eval-server-beats and VI-A's old ranges).
  - Floats: Table IV
  - Numbers: —
  - Cites: —
  - Links: ← mot-logic-cost; → eval-gemm-summary, eval-e2e-overview

## VI. Evaluation  (sections/06_evaluation.tex)  — restructured 2026-10-30 (user): A GEMM level (Fig. 7), B end to end (Fig. 8), C energy and peak power (with the power headroom of all-bank PIM, 2026-11-06), D area against silicon budgets (2026-11-06), E ablation (the former F, beat filling on newer DRAM, moved to VII-B on 2026-11-11); LP-Spec-style's comparison headline is throughput per logic mm² wherever it appears, P3-LLM-style's is speed
- **[eval-modelled]** (fairness in one place since 2026-11-08, user-approved AI-review item 4; the limits moved to intro-contributions)
  - Message: All results are modelled and ratios above 1 favour CoDe; three modelling choices favour the rivals, each with a pointer to its original statement: LP-Spec-style keeps only the accumulators its dataflow needs (mot-logic-cost, "a reading that favours LP-Spec-style") and runs one unit per bank on the mobile platform, faster than LP-Spec's shared unit (eval-placement; speed only, never "stronger"), and P3-LLM-style gains more from depth 2 than P3-LLM reports (meth-simulator, 1.78× vs 1.6×). No number of its own.
  - Floats: —
  - Numbers: —
  - Cites: —
  - Links: ← mot-logic-cost, mot-wider-pu, meth-simulator, eval-placement

### A. Skinny GEMM Speedup and Area Efficiency
- **[eval-gemm-summary]**
  - Message: CoDe reaches LP-Spec-style's GEMM speed on under three fifths of its logic (0.574× / 0.554×, printed in the next paragraph), and exceeds P3-LLM-style's speed beyond two token rows (user wording, 2026-11-11; "reaches": ties up to M = 4 and on HBM2, ahead on the mobile platform from M = 8).
  - Floats: —
  - Numbers: — (FC shapes in meth-workloads)
  - Cites: —
  - Links: ← intro-contributions, mot-wider-pu, mot-faster-pu, meth-workloads, meth-metrics
- **[eval-gemm-per-mm2]** "GEMM throughput per logic mm$^2$" (headline; first in VI-A since 2026-11-11, user)
  - Message: Per logic mm², CoDe leads LP-Spec-style's GEMM throughput on both platforms ("nearly doubles" dropped with the SAED14 areas: 1.74–1.94×; same beats, area on storage instead of multipliers, so CoDe runs at least as fast on 0.574× / 0.554× the logic), and it beats P3-LLM-style beyond M = 2; P3-LLM-style's smaller PU leads only at M ≤ 2. No peak at LP-Spec-style's partial-tile dip (M = 5) is printed (user, 2026-10-30).
  - Floats: Fig. 7 (fig:gemm, first cite), Fig. 7b
  - Numbers: 0.574× / 0.554× logic ← tables [table4], gemm; vs LP-Spec-style 1.74× (M ≤ 4), 1.94× (M ≥ 8) mobile, 1.80× every M (edge); vs P3-LLM-style 1.35× (M = 4), 1.50–1.51× (M ≥ 8) mobile, 1.44–1.45× (M ≥ 4) edge; 0.71× (mobile) / 0.74–0.75× (edge) at M ≤ 2 ← gemm (M = 1, 2, 4, …, 64)
  - Cites: —
  - Links: ← mot-logic-cost, meth-area-model; → eval-area-split (0.574× / 0.554× proved there; ref Table IV; Section VI-D)
- **[eval-gemm-speed]** "GEMM speed"
  - Message: Up to M = 2 the column period paces every design; beyond M = 2 P3-LLM-style needs a second pass while CoDe fills up to D = 4 beats per command, and, filling LP-Spec-style's four beats (eval-gemm-per-mm2 states the cost), CoDe equals LP-Spec-style's speed (to M = 4 mobile, every M edge; CoDe the subject, never "faster" there); on the mobile platform CoDe runs ahead from M = 8 because its eight-token tile halves LP-Spec-style's row sweeps (the sentence names the tile as the cause; the repeated "a lead of the tile size, not of decoupling" caveat and its pointer cut 2026-11-08, T6: eval-lpspec-variants proves it; the 1.11× no longer printed, guard-only in gemm, 2026-11-08). Fig. 7 plots M = 1, 2, 4, …, 64 only, and every range is taken over those M (no claim at a rival's partial-tile dip, user 2026-10-30).
  - Floats: Fig. 7a
  - Numbers: 1.96–1.97× at M = 2; 3.74× / 3.82× vs P3-LLM-style 1.95× at M = 4; CoDe 4.16× / 3.80× at M = 64 (Fig. 7a right endpoint, AI-review item 3, 2026-11-08) ← gemm (sd8g3 §2f, 2x2 §2p)
  - Cites: —
  - Links: ← des-beat-slot-factor, des-mapping; → eval-lpspec-variants
### B. End-to-End Speedup and Area Efficiency
- **[eval-e2e-overview]** (no run-in head; subsection opener; replaces the former platform-ordered paragraphs "Mobile platform", "Edge server" and "Throughput per logic mm²", user 2026-11-11: VI-B by rival, LP-Spec-style area first, P3-LLM-style speed first)
  - Message: Fig. 8 runs whole decoding on the five systems at the operating points of meth-workloads (mobile M = 8, edge batch 8, a light load; no M justification here); CoDe decodes 3.22× faster than NPU only on the mobile platform at 29.9 tok/s and 1.28× faster on the edge server at 456 tok/s, where stock AiM reaches 1.27× and 0.45× (never "fastest" on the edge server: LP-Spec-style ties); the order holds at each system's own best M on the mobile platform (best-M sentence kept, user 2026-11-11); NPU only overtakes CoDe from batch 16 on the gmean.
  - Floats: Fig. 8 (fig:e2e, first cite), Fig. 8a
  - Numbers: 3.22× at 29.9 tok/s, 1.28× at 456 tok/s; stock 1.27× / 0.45× (isca.e2e.phone.M8.<d>.speedup_vs_npu / tok_s; isca.e2e.hbm2.*); best M: 47.1 / 46.8 (M = 3), 43.8 / 26.5 (M = 2), NPU only 10.6 (M = 4); batch 16 ← e2e (sd8g3 §2f, 2x2 §2p)
  - Cites: —
  - Links: ← intro-code-proposal, abs-summary, meth-workloads, meth-systems, des-mapping
- **[eval-e2e-lpspec]** "Area efficiency against LP-Spec-style" (headline; area first, then speed)
  - Message: CoDe returns 1.87× (mobile) / 1.80× (edge) LP-Spec-style's tokens/s per logic mm² because it decodes at least as fast on less logic: LP-Spec-style reaches 3.00× NPU only at 27.9 tok/s, so CoDe decodes 1.07× faster on the mobile platform on 0.574× its logic (CoDe the subject), and CoDe matches LP-Spec-style's speed on the edge server on 0.554× its logic (tie stated, never a lead).
  - Floats: Fig. 8b, Fig. 8a
  - Numbers: 1.87× / 1.80× (isca.e2e.phone.M8.core8_over_h2.per_mm2, isca.e2e.hbm2.core4_over_h2.per_mm2); 3.00× at 27.9 tok/s; 1.07× (isca.e2e.phone.M8.core8_over_h2.speed); 0.574× / 0.554× ← tables [table4] ← e2e
  - Cites: —
  - Links: ← intro-code-proposal, intro-contributions, abs-summary, mot-logic-cost, meth-metrics
- **[eval-lpspec-variants]** "Eight-token LP-Spec-style" (rewritten as the argument, user 2026-11-11)
  - Message: The eight-token tile is what decoupling makes affordable: an eight-token LP-Spec-style design matches CoDe's loop speed at every M we run (2–4, 8, 16) and its GEMM speed from M = 8 (CoDe 1.007× at M = 12) but grows its logic to 5.18 % of the die, so CoDe returns 1.96× its tokens/s per logic mm²; the tile thus gives CoDe its speed lead over the per-bank LP-Spec-style (at M = 8 and 16), and CoDe's tile costs storage, not multipliers (the honest fact kept as part of the argument, not a concession).
  - Floats: —
  - Numbers: A8 loop 1.000 at M = 2–4, 8, 16; GEMM 1.000 from M = 8, 1.007 at M = 12; 5.18 %; 1.96× ← tables [lpsv_checks] (sd8g3 §2h; lpsv.phone.*); the lead at M = 8 and 16 (1.07×, printed in eval-e2e-lpspec) ← e2e
  - Cites: —
  - Links: ← mot-wider-pu, eval-gemm-speed, eval-e2e-lpspec; → disc-storage-cause
- **[eval-e2e-p3]** "Speed against P3-LLM-style" (speed first, then per mm²)
  - Message: CoDe decodes a batch of 8 1.41× faster than P3-LLM-style on the edge server, where P3-LLM-style runs at 0.91× NPU only's speed under P3-LLM's own placement (linear layers on the NPU, attention on PIM; CoDe every layer on PIM, its fastest placement at this batch; user 2026-11-10, option B); on the mobile platform P3-LLM-style reaches 2.06× because its two-token read needs four passes over the eight token rows; CoDe's speed lead more than repays its larger logic, 1.11× / 1.05× per logic mm², although the metric charges P3-LLM-style no area for the linear layers it runs on the NPU.
  - Floats: Fig. 8a, Fig. 8b
  - Numbers: 1.41× (core4_over_p3own.speed); 0.91× (isca.e2e.hbm2.p3own.speedup_vs_npu); 2.06×; four passes = ⌈8 / 2⌉; 1.11× / 1.05× (isca.e2e.phone.M8.core8_over_h3.per_mm2, core4_over_p3own.per_mm2) ← e2e (2x2 §2p)
  - Cites: —
  - Links: ← mot-gemv-only, mot-faster-pu, intro-code-proposal, intro-contributions, abs-summary
### C. Energy and Peak Power
- **[eval-energy]** "Energy per token"
  - Message: CoDe spends the least energy per token of the five systems on the mobile platform and ties for the least on the edge server (LP-Spec-style 1.00× printed; 1.0027× unprinted, never claimed as a lead), with the edge NPU idling at 55 W (gated case in one sentence: its ratio grows because P3-LLM-style's NPU reads the linear weights over the HBM pins); every Fig. 8c bar is printed (edge: CoDe's mJ and stock AiM's ratio added 2026-11-08, AI-review item 3).
  - Floats: Fig. 8c
  - Numbers: 105.8 mJ/token at M = 8; NPU only 6.0×, stock 1.96×, P3-LLM-style 1.40×, LP-Spec-style 1.14× (mobile; isca.e2e.phone.M8.core8.mJ_tok, <d>_over_core8.mJ); CoDe 145 mJ/token, NPU only 1.48×, stock 2.73×, P3-LLM-style 1.52×, CoDe ties LP-Spec-style (1.00×, edge, 55 W); gated P3-LLM-style 2.08× (p3own_over_core4.mJ_55W / mJ_0W); cause (user-approved wording 2026-11-10, measured): CoDe keeps the linear layers in the banks, P3-LLM-style's NPU reads every linear-layer weight over the HBM pins = 76 % of the 0 W gap (hyb.esplit.hbm2.b8.gap_share.weight_io 0.759; context: gap 26.41 mJ/token, linear placement 0.788, P3-LLM-style NPU MAC share 0.0149, unprinted) ← e2e (2x2 §2p: isca.e2e.hbm2.core4.mJ_tok_55W, stock_over_core4.mJ_55W; 2x2 §2r/§8, evaluation 860384d)
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
  - Message: Fabricated PIM dies set the scale for a PIM design's logic area, which a DRAM die pays for in memory capacity (one clause, Section III-C pointer to HBM-PIM's halved sub-arrays in mot-logic-cost; AI-review T3, 2026-11-08) (HBM-PIM 27 % of its die by our division; its halved sub-arrays printed in III-C only since 2026-11-08; AiM 20–25 %, pointed back to III-C), and CoDe's logic takes 2.64 % of the LPDDR5 die and 2.28 % of the HBM2 stack, 5.06 % / 4.24 % at AiM's silicon scale, against AiM's 20–25 % (the former "at most a quarter of AiM's share" no longer holds: 5.06 > 5), while keeping every cell array (the LP-Spec-style shares sentence, 4.60 / 4.11 / 9.00 / 7.90 %, cut 2026-11-10, user review 2; 4.60 % stays in III-C from Table IV; the others are guard-only asserts).
  - Floats: Table IV (logic mm², the source of the shares; the % column was removed 2026-11-10, so VI-D is the shares' print site)
  - Numbers: 32 × 0.712 mm² on 84.4 mm², 27 % (derived, never stated by Samsung) ← budget.hbmpim.area_share_pct; % of die / stack (Table IV mm² over the V-B denominators) ← budget.phone.<d>.pct_of_die_1z, budget.hbm2.<d>.pct_of_stack_model ← tables [budget_cells]; ×1.98 shares ← budget.*.pct_of_*_anch_aim ← tables [budget_checks]. LP-Spec's own 16.92 % is printed in I and III-C only (reconciled with 4.60 % in mot-logic-cost).
  - Cites: hbmpim
  - Links: ← meth-area-model, mot-logic-cost
- **[eval-area-split]** "Logic against LP-Spec-style" (moved from V-B, 2026-11-06)
  - Message: CoDe matches LP-Spec-style's peak throughput with 0.574× its logic per die (an exact tie of the 4× ceiling, CoDe the subject) because it spends its logic on storage rather than arithmetic; CoDe does not pay for the saved area with power: its peak power stays below LP-Spec-style's on both platforms (pointer to VI-C, where 0.92× / 0.87× are printed once; user 2026-11-11); on HBM2 its logic is 0.554× LP-Spec-style's and 1.35× P3-LLM-style's for twice P3-LLM-style's beats per column period (the 0.562 / 0.537 silicon-scale ratio sentence cut, user 2026-11-06; guard-only assert).
  - Floats: — (Table V tab:umac_src float defined right after VI-E's heading since 2026-11-11; lands p11 L top, Fig. 9 alone on p11 R)
  - Numbers: 0.574×; arithmetic 0.71 / 0.31, storage 0.39 / 0.14; peak power below LP-Spec-style's (pupow gate ids < 1, asserted in storage); 0.554×, 1.35× ← tables [table4, area_split]; 0.562 / 0.537 no longer printed (guard-only in tables [budget_checks])
  - Cites: —
  - Links: ← meth-area-model, mot-two-levers, eval-gemm-per-mm2
### E. Ablation Study
- **[eval-gain-sources]** "Sources of CoDe's gain" (moved from VI-B to VI-D, 2026-10-30, VI-E since 2026-11-06; the both-sources-from-one-mechanism sentence cut)
  - Message: CoDe's gain over stock AiM comes from beat filling, which raises the slot factor, and row reuse, which keeps the sweep factor near stock AiM's level once beat filling shortens the MAC slots; Table V's layer is Table I's layer on the mobile platform (link added 2026-11-10; the "cumulative speed-up = U over stock AiM's U" clause was not added: exact in the data, but the printed U's give 1.25 / 2.96 against the printed 1.24 / 2.97 for row reuse only (mobile) and D = 3 (HBM2)); at D = 2, half its PU clock, CoDe already returns 1.07× / 1.015× LP-Spec-style's throughput per logic mm² on this layer, because its logic is the same at every D (the measured rung replaces the interpolated D* 1.87 / 1.97); beat filling pays off only after row reuse: applied alone it would keep every row-switch command, which would then take about half of the time or more (f_MAC 0.425 / 0.506; the 2.37 / 1.83 / 2.62 / 1.46 steps no longer printed, guard-only). Relative form; never claims CoDe raises f_MAC on the edge server. The row-reuse-only design is CoDe's trace at D = 1, which still reads each column once per tile; end to end, beat filling makes CoDe decode 2.03× (phone loop, M = 8) / 2.29× (HBM2, batch 8) faster than row reuse alone (dots.e2e.* ids; names do not print). Never tied to DOTS (user, 2026-11-11): DOTS appears only in III-C and IV-B.
  - Floats: Table V (first cite), Table I (the same mobile layer; Table V's row labels carry the layers, the duplicate setting clause cut 2026-11-08; rows per platform since 2026-11-10: stock AiM, row reuse only (D = 1 in the text; the "DOTS-style" label dropped 2026-11-11), D = 2, D = 3, CoDe (D = 4), each step over the row above)
  - Numbers: steps 1.24× / 1.15× after row reuse (Table V); U 0.223 / 0.222 after row reuse; beat filling one beat per step, U_MAC 0.25 → 0.50 → 0.73 → 1.00 (D = 3 runs 2.91 effective beats: the PU hold rounds to whole simulator cycles; one clause in the text, not the caption), its total over row reuse alone 3.49× / 3.33× (D = 1 → 4, umac.dsteps.<p>.bf_total); CoDe's Table V step 1.31 / 1.29 (over D = 3); per logic mm² at D = 2 CoDe returns 1.07× (mobile) / 1.015× (edge server) LP-Spec-style's, layer basis at M = 8, CoDe's logic the same at every D (usrc_dsteps_permm2 per_mm2_vs_lp 1.067 / 1.015, tab_umac_src_dsteps.csv; x.saed.core_logic_change_across_D_maxabs_pct 0; 2x2 §2s, §2v; D* 1.87 / 1.97 no longer printed, guard-only; no f_max or timing-closure claim); CoDe f_MAC 0.779 / 0.739 vs stock 0.717 / 0.771 (Table V); CoDe over row reuse alone end to end 2.03× / 2.29× (beat filling's end-to-end gain) ← dots.e2e.phone.loop.M8.core8_over_d1.speed 2.026 (sd8g3 §2j, evaluation 7cf79d5), dots.e2e.hbm2.b8.core4_over_d1.speed 2.287 (2x2 §2t), evaluation 0683cc6 [dots_checks]; beat filling alone (modelled as a per-sweep rule: a quarter of stock AiM's MAC slots plus its non-MAC time) f_MAC 0.425 / 0.506 (the both-order steps 2.37× then 1.83× and 2.62× then 1.46× guard-only since 2026-11-10) ← tables [umac_src_table] (2x2 §2i, §2s)
  - Cites: — (dots removed 2026-11-11: VI-E no longer names DOTS)
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
  - Numbers: V 4 → 8 logic +19 % (mobile) / +45 % (edge server) against speed 1.117× / 1.089×; peaks 2.89× / 2.28× stock AiM, 1.51× / 0.34× at V = 64 (= abl.<p>.W2.<st>.sram.v{4,64}.per_mm2_over_stock) (Fig. 9a right endpoint, AI-review item 3, 2026-11-08) ← vsw (2x2 §2k). Cut 2026-10-30 (guards kept): 1.349 → 1.607 / 0.961 → 1.393 mm², break-even 1.191× / 1.449×, 93.8 % / 75.1 % of peak
  - Cites: —
  - Links: ← des-tile-size, meth-area-model
- **[eval-vsweep-choice]** "Tile size across $M$" (eval-vsweep-partial merged into it, user review 2, 2026-11-10; conclusion first; the M = 3–4 / EAGLE sentence cut)
  - Message: CoDe uses V = 8 on the mobile platform and V = 4 on the edge server, the tile size that loses least in its worst case across M = 3–16 (the small-M reason clause cut 2026-11-10: eval-vsweep-area's last sentence carries it); Fig. 9b divides V = 8's decode-step throughput per logic mm² by V = 4's: on the mobile platform V = 8 wins where it saves V = 4 a partly filled row sweep and loses at M ≤ 4, where both tiles run one row sweep; on the edge server V = 8 never breaks even. ("Wins where it saves" is a necessary condition: V = 8 also saves a sweep at M = 8, 11, 12, 16 and still loses there, 0.97–0.99×.)
  - Floats: Fig. 9b
  - Numbers: wins at M = 5–7, 9–10, 13–14 (M = 15 no longer, SAED14), 1.290× at M = 5; M ≤ 4 → 0.840×; worst loss against the best V (of 2, 4, 8, 16) at each M over M = 3–16: mobile V = 8 16.0 % vs V = 4 27.5 % (q_proj, so printed "on q_proj"; decode step 22.5 % guard-only); edge server 0.690–0.915×, V = 4 8.9 % vs V = 8 31.0–32.2 % ← vsw (2x2 §2l–2n). Cut 2026-10-30 (guards kept): 22.5 % verify-step loss, one-tile 2.0 %, one-tile token load 28.3 % (brk); EAGLE best M = 4 guard-only in e2e
  - Cites: —
  - Links: ← des-tile-size, eval-vsweep-area
- **[eval-placement]** "PU placement" (new 2026-11-10, user-approved brief; last paragraph of VI-E, after the Fig. 9 float source)
  - Message: CoDe keeps its lead under the other placement commercial PIM uses, one unit shared between two banks (II-B; claim first, user review 2, 2026-11-10): sharing costs speed only when a bank delivers a column as often as a unit takes one; on the edge server a bank delivers one every 8 ns and a PU takes one every 4 ns, so every design there, CoDe included, already shares one PU between two banks at full speed; on the mobile platform a bank delivers one every 5 ns, as fast as a unit takes one, so a shared unit halves each bank's rate; built with one unit per two banks, LP-Spec-style takes 0.90× CoDe's logic ("as LP-Spec publishes it" and its cite cut, 2026-11-10), and CoDe decodes 1.60× faster than this shared design at M = 8 and returns 1.44× its tokens/s per logic mm² (the near-iso-area comparison, user 2026-11-11; "about equal logic area" dropped with the SAED14 areas); conclusion: whichever placement LP-Spec-style uses, CoDe decodes at least as fast (per bank 29.9 vs 27.9 mobile, HBM2 tie) and returns more throughput per logic mm². The 10 ns bank-column sentence was cut (user decision, 2026-11-10).
  - Floats: Table III (t_CCD_L, internal bandwidth, banks)
  - Numbers: 8 ns = 1,024 GB/s / 256 banks of 32 B; 4 ns = t_CCD_L; 5 ns = 409.6 GB/s / 64 banks ← tables [platform_block]; 0.90×, 1.60× (M = 8), 1.44× (M = 8) ← tables [lpsv_checks] (sd8g3 §2h; lpsv.phone.loop.core8_over_h2sh.{speed,per_mm2}_M8); the 10 ns clause no longer printed
  - Cites: —
  - Links: ← bg-aim-pu (hc35pim, the two placements), eval-e2e-lpspec, eval-modelled, mot-wider-pu, intro-code-proposal, intro-contributions, abs-summary

## VII. Discussion  (sections/07_discussion.tex; label sec:disc; new 2026-11-11, user-approved brief: the area-efficiency reframing)
### A. Storage Versus Arithmetic in a DRAM Die  (label sec:disc:storage; no P3-LLM-style and no shared design here, user decision)
- **[disc-storage-claim]** (no run-in head; subsection opener: claim + metric)
  - Message: Filling idle beats with storage costs a DRAM die less area per unit of speed than filling them with arithmetic: we charge each design the logic it adds over stock AiM per unit of speed-up over stock AiM, ΔA / (S − 1); on GEMMs of eight token rows LP-Spec-style adds 0.655 mm² per die per +1× and CoDe 0.189, 3.5× less (Fig. 10); on HBM2 3.1× (0.405 against 0.130 mm² per pseudo-channel); end to end at V-D's operating points 3.4× and 3.1×; the added logic differs in kind (arithmetic 83 % of LP-Spec-style's, storage 93 % of CoDe's; shares of added logic, not of VI-D's total logic).
  - Floats: Fig. 10 (fig:storage, first cite; float defined after this paragraph)
  - Numbers: 0.655 / 0.189 mm² per die per +1× (aps.phone.<h2|core8>.kernel_M8.mm2_per_x), 3.5× (aps.phone.h2.kernel_M8.ratio_to_core 3.47); 0.405 / 0.130, 3.1× (aps.hbm2.*, 3.11); e2e 3.4× / 3.1× (aps.<p>.h2.e2e_M8.ratio_to_core 3.38 / 3.11); 83 % (aps.phone.h2.arith_share 0.830), 93 % (aps.phone.core8.storage_share 0.930) ← storage (2x2 §2u, §2v; evaluation 35c9d06)
  - Cites: —
  - Links: ← intro-contributions, abs-summary, meth-workloads, meth-area-model; → disc-storage-cause
- **[disc-storage-cause]** (no run-in head)
  - Message: CoDe pays once, for the tile, and then gains its beats from the clock: on the mobile platform the tile costs 0.598 mm² per die of storage and control and, through row reuse alone, speeds a GEMM up 1.24×; raising the PU clock from one to four beats per column period adds no logic area (SAED14: CoDe and stock AiM share one arithmetic netlist) and lifts the speed-up to 4.17×; LP-Spec-style pays about 0.59 mm² per die per 32-wide ALU, 0.50 of it in multipliers and adder trees, and its eight-token variant reaches CoDe's speed at 3.6× CoDe's added area per unit of speed-up (the per-unit ratio only; 5.18 % / 1.96× stay in VI-B, E2); the DRAM die sets the trade (logic ten times less dense than an ASIC, devaux; the all-bank column already spans four command clocks, III-D); CoDe pays for those cycles in power rather than area, and its peak power stays below LP-Spec-style's (pointer to VI-C; 0.92× not reprinted).
  - Floats: Fig. 10
  - Numbers: 0.598 mm² (aps.marg.phone.stock_d1.dA 0.5977), 1.24× (CoRe D1 S_kernel_M8 1.239); no logic area (aps.marg.phone.d1_d4.dA 0, aps.phone.core_per_beat_dA 0), 4.17× (aps.phone.core8.kernel_M8.S 4.165); about 0.59 mm² per ALU (aps.phone.lp_alu.step_dA mean 0.586, aps.phone.lp_per_beat_dA), 0.50 (step_arith 0.495); 3.6× (aps.phone.h2a8.kernel_M8.ratio_to_core 3.59) ← storage
  - Cites: devaux
  - Links: ← mot-logic-cost, mot-depth, mot-two-levers, eval-lpspec-variants, eval-power, eval-gain-sources
- **[disc-storage-robust]** (no run-in head)
  - Message: The trade survives costlier storage: CoDe keeps its lead per logic mm² over LP-Spec-style until storage (flip-flops and SRAM) costs 6.5× our estimate (V-C) on the mobile platform and 16.5× on the edge server, and at three times our estimate it still returns 1.29× / 1.34× LP-Spec-style's tokens/s per logic mm² (answers reviewer-risk item 1, the area scale; no P3-LLM-style values).
  - Floats: —
  - Numbers: 6.5× / 16.5× (stor.<p>.be.all.lp 6.53 / 16.49); 1.29× / 1.34× (stor.<p>.all.s3.per_mm2_vs_lp 1.292 / 1.344) ← storage
  - Cites: —
  - Links: ← meth-area-model, eval-e2e-lpspec
### B. Beat Filling on Newer DRAM  (label sec:disc:newdram, was sec:eval:newdram; moved verbatim from VI-F, 2026-11-11; user-approved brief 2026-11-10: "D with the PU at CK", no limitation sentence, "above 1 GHz" stated positively)
- **[disc-newer-dram-depth]** (no run-in head; subsection opener; moved verbatim from VI-F, 2026-11-11)
  - Message: Beat filling keeps a depth of four on newer DRAM, because each generation shortens CK but keeps the all-bank column at four CK (t_CCD_L = 4 t_CK); we evaluate LPDDR5-6400 and HBM2 because LP-Spec and P3-LLM were built on them; LPDDR5X-8533 / -9600 (CK 1.07 / 1.2 GHz) have 3.75 / 3.33 ns columns, HBM3 at 6.4 Gb/s (CK 1.6 GHz) a 2.5 ns column at HBM2's four-clock column [ASSUMPTION: JESD238 not public; never cite AttAcc for it]; a PU at CK runs D = 4 on each, V >= D fills all four beats, U_MAC stays 1 and the MAC rate grows as the column shortens.
  - Floats: Table III (HBM2's four-clock column: t_CK 1 ns, t_CCD_L 4 ns)
  - Numbers: 4 t_CK; 1.07 / 1.2 GHz; 3.75 / 3.33 ns; 6.4 Gb/s, 1.6 GHz, 2.5 ns; D = 4 ← tables [newdram_checks] (spec constants with their cites; 8533 / 8 = 1066.6 MHz and the datasheet bin 1066.5 MHz both print 1.07 GHz and 3.75 ns)
  - Cites: jedeclpddr5, micronlp5x, synopsyshbm3
  - Links: ← bg-aim-pu (D defined), mot-depth, des-pu-clock, eval-gain-sources (U_MAC 1 at D = 4); → conc-summary (decoupling carries over)
- **[disc-newer-dram-clock]** (no run-in head)
  - Message: CoDe on these memories clocks its PU above 1 GHz, at 1.07 to 1.6 GHz, and three DRAM trends support a PU above 1 GHz: the die already clocks command logic at CK and its data path faster (LPDDR5X WCK = 4 CK, HBM3 strobes 3.2 GHz); periphery has moved closer to logic-class transistors since the 1 GHz GDDR6-AiM PU of III-D (back-pointer only; III-D keeps AiM's 1y-nm and the general HKMG claim, E2) (SK hynix HKMG LPDDR5X 8.5 Gb/s at 25 % less power; Micron 1γ next-generation HKMG for transistor speed, DDR5 designed for 9200 MT/s) and TSMC plans HBM4 base dies in 12-nm and 5-nm logic processes; commercial PIM has moved to LPDDR5X (LPDDR5X-PIM 614 GB/s inside, eight times its 76.8 GB/s interface). No limitation sentence (user). Relaxes III-D's "never vendors' pin-rate claims" rule here only (user-approved text). Dropped at verification: "1a-nm" (SK hynix newsroom does not print it; only aggregator headlines), "-9600" on LPDDR5X-PIM (no fetched report prints it), "credits HKMG for 9200 MT/s" (Micron ties HKMG to speed capability, 9200 MT/s to the DDR5 design).
  - Floats: —
  - Numbers: 1.07 to 1.6 GHz; WCK 4 × CK; 3.2 GHz; 8.5 Gb/s, 25 %; 9200 MT/s; 1 GHz (back-pointer to III-D's aimjssc figure); 12 / 5 nm; 614 / 76.8 GB/s = 8.0 ("eight times") ← tables [newdram_checks] (cited constants)
  - Cites: micronlp5x, synopsyshbm3, skhynixhkmg, micron1gamma, tsmchbm4, lp5xpim
  - Links: ← mot-pu-clock-precedent (points back to AiM's 1 GHz PU; Observation 26 resolved), des-pu-clock

## VIII. Conclusion  (sections/08_conclusion.tex)
- **[conc-summary]**
  - Message: Mirrors the abstract (user, 2026-11-11): prior DRAM PIM paces every MAC by a DRAM command and fills idle beats with multipliers or commands; DRAM timing bounds column accesses, not MACs on a latched column, so a PIM die can fill those beats with clock cycles instead of multipliers; CoDe feeds many PU beats from one column command over a tile of tokens; against LP-Spec-style 1.87× tokens/s per logic mm² and 1.60× faster than a shared LP-Spec-style design with 0.90× its logic; against P3-LLM-style 1.41× on HBM2 (+ 1.28× over NPU only); the decoupling carries over to any DRAM whose column outlasts one beat. No 1.07×.
  - Floats: —
  - Numbers: 1.87× ← e2e; 0.90×, 1.60× ← tables [lpsv_checks]; 1.41×, 1.28× ← e2e
  - Cites: —
  - Links: ← mot-depth, eval-e2e-lpspec, eval-placement, eval-e2e-p3, disc-storage-claim, disc-newer-dram-depth
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
| Fig. 7 | fig:gemm | figs/fig_gemm.pdf ← gemm, html2pdf.py (05_methodology.tex, one-column figure after meth-workloads since 2026-11-08; figure* until 2026-11-06) | eval-gemm-per-mm2 (p9 L) | p9 L top |
| Fig. 8 | fig:e2e | figs/fig_e2e.pdf ← e2e, html2pdf.py (05_methodology.tex, figure* right after Fig. 7's source since 2026-11-10 (ACM), so that it renders on VI-B's page; was after eval-gemm-per-mm2) | eval-e2e-overview (p9 R) | p10 top, both columns (next page) |
| Table V | tab:umac_src | tables/tab_umac_src.tex ← tables (06_evaluation.tex, right after VI-E's heading since 2026-11-11, so that it misses p10 R under Fig. 8; D = 2 / 3 rows since 2026-11-10) | eval-gain-sources (p10 R bottom) | p11 L top (next column) |
| Fig. 9 | fig:vsweep | figs/fig_vsweep.pdf ← vsw (06_evaluation.tex) | eval-vsweep-gain (p11 L) | p11 R top |
| Fig. 10 | fig:storage | figs/fig_storage.pdf ← storage = scripts/make_fig_storage.py, html2pdf.py (07_discussion.tex, after disc-storage-claim) | disc-storage-claim (p11 R) | p12 L top (next page) |
| Eq. 1 | eq:fmac | 03_motivation.tex | mot-sweep-factor | p4 L |

## Observations
| # | kind | where | observation |
|---|---|---|---|
| 1 | resolved | mot-nonmac-classes … mot-utilization | Resolved again (user, 2026-10-28): III-B now runs setup (mot-breakdown-setup) → Non-MAC commands (classes, non-MAC cost with row switch first, sweep factor; mot-load-refresh-cost merged into mot-rowswitch-cost, user 2026-10-29) → Idle beats (idle beats, cause) → mot-utilization (U, Table I, transition to III-C). Before (user plan, 2026-10-27): split into Non-MAC commands (what each command costs per row sweep; row switches outlast the useful MAC work) and Sweep factor (Eq. 1, Table I, f_MAC 0.717, U 0.179). Was: one paragraph (≈ 30 source lines, ≈ 25 numbers) carries the f_MAC formula and fit, the per-command row-switch split, token load against GB fills, refresh, the edge-server totals and stock U = 0.179; class names are used before this paragraph defines them. |
| 2 | resolved | meth-simulator | Resolved (2026-11-06): V-C is three paragraphs, meth-simulator (simulator, P3-LLM validation, C/A re-timing, refresh), meth-area-model and meth-power-model. Was: one paragraph with five topics. |
| 3 | two messages | mot-logic-cost, eval-e2e-overview | mot-logic-cost (logic-die designs) still adds a second claim (eval-vsweep-robust's two claims split into eval-vsweep-partial / -choice, 2026-10-30, merged back into eval-vsweep-choice conclusion-first, 2026-11-10); eval-e2e-overview carries the figure setup (M = 8, batch 8; the reason is meth-workloads'), the M = 8 result and the best-M check. The former eval-phone-per-mm2 / -energy / eval-server-beats cases left with the VI restructure (2026-10-30). |
| 4 | placement | eval-gain-sources | eval-gain-sources opens VI-E (Ablation Study, VI-D until 2026-11-06); Table V lands at the top of the column after its cite (ACM build: VI-E's heading and cite p10 R bottom, table p11 L top) from its source right after VI-E's heading (2026-11-11; before the heading it shared p10 R with Fig. 8). It remains the only home of the both-order gain. |
| 5 | resolved | eval-gain-sources | Resolved (user plan, 2026-10-27): des-gain-order deleted; the both-order gain lives only in VI-B (2.37× / 1.83×, Table V values); the 2.3 % reconciling sentence left IV-B. Was: the two-order gain printed 2.39× then 1.84× (Fig. 5 window) in IV-A and 2.37× then 1.83× (one layer, Table V) in VI-B; only des-beat-slot-factor's 2.3 % sentence reconciles them. |
| 6 | restatement | intro-prior-families / mot-prior-families; intro-timing-insight / mot-depth; mot-idle-beats / mot-depth | The two families are named in I and III-C; mot-depth now points to Table III for the column period and CK instead of reprinting the intro's 5 ns / 4 ns / 0.8–1 GHz, and mot-idle-cause's column-access argument is now one sentence (each column command reads one column; t_CCD spacing), leaving the latched-column argument to mot-depth. D is now defined once, in bg-aim-pu (its first point of need), and III and IV point back to it (resolves "D derived late"); intro-timing-insight still derives D = t_col × f_PU itself (introduction untouched). |
| 7 | restatement | intro-prior-families / mot-logic-cost; eval-area-budget | The V = 4 reason now lives in IV-D only (V-B points to it, 2026-11-08); LP-Spec's 16.92 % is printed in I and III-C (not in VI-D), reconciled with 4.60 % in III-C; 0.574× appears in the abstract, I, VI-A, VI-D and VII (the area-efficiency headline); HBM-PIM's halved sub-arrays in III-C only. |
| 8 | config table | Tables III / IV (tab:params, tab:designs) | Two configuration tables in V (platform, Table III; designs, Table IV; split 2026-11-06, user); III–VI refer to them, design rows (lanes, PU clock, GB, slots, area, %, peak power) to Table IV. Kept in prose where the sentence computes or derives: intro's 5 / 4 ns, 0.8 / 1 GHz and 42 GB/s (D and the ridge), III-A's 42 GB/s derivation, IV-D's GB / slice sizes, VI-C's 1.25 / 5 ns per-edge charge (the 800 / 200 MHz clock-cost sentence left on 2026-10-30). Row size has no collected source and stays out (for evaluation-owner). |
| 10 | resolved | intro-contributions | Resolved (2026-11-08, AI-review item 1): the claim–evidence contributions announce energy (VI-C), area against silicon budgets (VI-D) and the ablation (VI-E). Peak power and the tile-size study stay unannounced (not in a contribution item). |
| 11 | untraced number | meth-platforms, Table III | 2.285 W host power (derived from cites, no script); Table III's t_REFI 3.906 µs is asserted from evaluation/dac_sd8g3/context.md text ([A-REF1]) and t_RFCab 280 ns from the collected trace (utrace_run_core8_gbfill REFab gap), neither has a JEDEC cite; 131 TOPS (assumption with cite only); 56 / 68 / 51.2 GB/s (cites; only the 42 GB/s result is asserted). |
| 12 | resolved | eval-power | Resolved (2026-10-30): the 2.4 % clock cost (microarch pu_peak_power.csv, never collected) is no longer printed; make_tables.py keeps its assert as a guard. |
| 13 | structure | mot-other-pim | Stays last in III-C (user, 2026-10-27); no related-work section remains (options kept for later: (a) a short Related Work section before the Conclusion, from the ≈ 1 free column; (b) a landscape paragraph at the end of II-B; (c) keep it as the last paragraph of III-C, as now). mot-other-pim now closes III-C with the C → D transition (a column read feeds several tokens only through added multipliers or commands; a row sweep serves one MAC slot's tokens). Labels `sec:bg:*` point into Section III (cosmetic). |
| 14 | unverified source | mot-other-pim (closing), des-row-reuse, mot-idle-cause | LP-Spec's own text on row activations was not checked: no LP-Spec PDF exists under 00_doc (paper_isca2's is empty; paper_dac's references hold p3llm.pdf, the AiM JSSC paper and others, not LP-Spec), so LP-Spec-style's sharing of a row sweep among its four tokens rests on our model (Table I, A = 4). P3-LLM's own text (p. 11) supports its two-token row-activation saving. HBM-PIM's statement of a GEMV target was not checked (no PDF); AiM JSSC p. 1 (RNN and MLP layers with low memory reuse, evaluated on GEMV) and P3-LLM p. 3 (both PCUs perform GEMV) were. |
| 15 | timing | Table III, mot-idle-beats, eval-placement | HBM2's column period prints t_CCD_L = 4 ns (cited) while the simulator's all-bank HBM2 MAC slot is 8 ns (b = 2, two banks per PU; dac2x2_setup); U_MAC's b = 2 reconciles them; eval-placement now prints the 8 ns per-bank column (1,024 GB/s / 256 banks), Table III still shows no 8 ns slot. |
| 16 | resolved | mot-prior-families, mot-other-pim, mot-two-levers, des-row-reuse, eval-gain-sources | Resolved (user, 2026-10-27): f_MAC is a share, so row reuse is stated in absolute form in III-C, III-D and IV-C (it cuts the non-MAC time per token: 123.39 → 22.15 ns mobile, 146.17 → 43.51 ns edge server) and in relative form in VI-B (it keeps f_MAC near stock AiM's level once beat filling shortens the slots: 0.779 / 0.739 vs 0.717 / 0.771). Guard: no sentence says CoDe raises f_MAC on the edge server (0.739 < 0.771) or frames the rivals' flat f_MAC as their defect; only the D = 1 row-reuse-only row lifts f_MAC (0.892 / 0.887). |
| 17 | ordering | mot-logic-cost, mot-faster-pu | With logic cost before the faster-PU family (user order), mot-logic-cost compares LP-Spec-style's per-mm² ceiling with stock AiM's (293 / 591 vs 203 / 431 on SAED14 areas) and P3-LLM-style's 361 / 718 moved into mot-faster-pu after P3-LLM-style is named. |
| 18 | restatement | intro-prior-families, intro-timing-insight vs mot-prior-families, mot-depth | The introduction still repeats III-C's two families and III-D's insight (and derives D itself); left untouched by the III/IV mirror pass (user plan, 2026-10-27). |
| 19 | resolved | eval-gemm-per-mm2 | Resolved (2026-10-30): the per-mm² ceilings of CoDe (583 / 1,247 GOPS) are no longer printed beside measured ratios; VI-A prints measured GEMM ratios against M only. |
| 20 | dropped number | des-row-reuse | The whole-GEMM 4.32× (CoDe vs stock AiM, q_proj, M = 8) left IV with des-gain-order; no other section printed it, and the 4.40× window carries IV-C's claim. Still asserted in make_fig_mapping.py; it could return to VI-B if a whole-kernel number is wanted. |
| 21 | resolved | mot-rowswitch-cost vs des-row-reuse | Resolved (user, 2026-10-29): III-B prints q_proj shares only, so the edge non-MAC time appears once, as 146.17 ns per token (IV-C, Table I). Was: 146.2 ns per row sweep in III-B and 146.17 ns in IV-C. |
| 22 | wording trap | meth-area-model, eval-area-budget, eval-power | Area / power budget (2026-11-06): 60.92 mm² is printed "as LP-Spec reports" (its ISSCC'21 origin is closed access, never cited); the HBM2 stack is 8 × the 84.4 mm² HBM-PIM die ([A-XC4], no plain HBM2 die area published); 27 % is our division; peak excludes activation, refresh, background and I/O power, so the read yardsticks (447 mW at LPDDR5X-7500 for a 6400 part; 8.0 W from O'Connor's 4-die figure on an 8-die stack) are scales, not budget shares; AiM's 3× is a GDDR6 current ratio (framing); the plan's "the stack in PIM mode draws less than in normal reads" became "CoDe's PUs fit within the read power an HBM2 stack already delivers" plus HBM-PIM's TDP sentence, because the peak omits activation power and HBM-PIM measured +5.4 %, within the original TDP. SK hynix's bank-count throttling is a "future AiM design" knob on its HC36 slide, not a shipped feature. |
| 23 | citation | shevgoor | The Shevgoor MICRO'13 entry has no pages or DOI (not verifiable offline); the quote is on PDF pp. 2 and 6 of the authors' copy. |
| 24 | reviewer risk | eval-placement, eval-lpspec-variants, mot-logic-cost | The LP-Spec-style variants (2026-11-08) are phone-only and modelled: the shared design (eval-placement, VI-E since 2026-11-10) at LP-Spec's own 10 ns bank column is not run (no longer stated in the paper: user cut the clause, 2026-11-10), no HBM2 shared variant is run (eval-placement argues it loses no speed: 8 ns bank column vs 4 ns PU), and the shared unit's 2:1 bank mux is unpriced (favours LP-Spec-style). The abstract keeps "1.60× faster at about the same logic area" (user, 2026-11-10; M = 8). LP-Spec's register-file area stays unprinted (9.80 / 12.08 mm² at 16 sets vs 4.90 / 6.04 at 8 sets, sd8g3 context §5 row 40, for microarch-owner). |
| 25 | reviewer risk | meth-systems, eval-e2e-p3, eval-e2e-lpspec, eval-energy | Edge-server P3-LLM-style follows P3-LLM's own placement since 2026-11-10 (user, option B; reviewer: "a configuration P3-LLM would not run"): linear layers on the NPU at batch 8, attention on PIM (P3-LLM p. 13); CoDe stays all-PIM (its fastest placement at batch 8). Per logic mm² counts no NPU area, which favours P3-LLM-style (stated in eval-e2e-lpspec). Not printed: the per-class best of each (1.24× speed, 0.93× per mm², hyb.hbm2.*). Old all-PIM ids isca.e2e.hbm2.p3_500.* (0.76×, 1.68×, 1.26×, 1.64× / 1.46×) are history; make_tables headline() still guards them as the pack's values. |
| 26 | resolved | mot-pu-clock-precedent vs disc-newer-dram-clock | Resolved (user-approved brief, 2026-11-10, E2): VI-F's second trend opens with a back-pointer to III-D's 1 GHz GDDR6-AiM PU and keeps only the product-specific facts (SK hynix, Micron, TSMC HBM4); the 1y-nm sentence and the general HKMG claim stay in III-D only; aimjssc left VI-F. |
| 27 | novelty | mot-other-pim, des-row-reuse, eval-gain-sources | DOTS (DATE'25, 2 pages, read from 00_doc/ai_style; Fig. 1c drawn, not stated in its text) shares a row's activation across a tile of tokens (weight-stationary, several result latches, double-buffered GB), i.e. row reuse at the row level at the stock pace of one column read per token. The former III-C closing ("none lets a larger tile share one row sweep and pay its row-switch commands once") was false against DOTS and was replaced (user, 2026-11-10); CoDe's novelty over DOTS is decoupled beat filling plus the read-once tile MAC. The row-reuse-only design (CoDe at D = 1) still reads each column once per tile, so it is not DOTS and is never tied to DOTS (user, 2026-11-11: the "DOTS-style" label, the VI-E timing-equivalence sentence and "which DOTS lacks" removed); DOTS appears only in III-C and IV-B, and IV-B states the difference as what one column read serves (512 vs 64 reads, cell-access and column-decoder energy, pointing to III-D). No number compares CoDe with DOTS. The abstract's "row reuse lets a tile of tokens share one row sweep" names the technique, not a novelty claim; left unchanged. |
| 28 | reviewer risk | meth-workloads, eval-e2e-overview, eval-vsweep-choice, abs-summary | The mobile operating point is M = 8 (user, 2026-11-11): the paper presents M = 8 only and never names another operating point as history or a change; its reason is a fact (seven drafted tokens within the 2–8 that published mobile decoders verify, sdnpu). The best-M sentence stays (user), so a reviewer sees CoDe reach 47.1 tok/s at M = 3 against 29.9 at M = 8; the systems keep one order in speed, per mm² and energy across the points checked (isca.e2e.phone.M8.order_same_as_M4.*). V = 8 is never justified by the operating point: at M = 8 V = 8 returns 0.970× V = 4 per mm² (abl.phone.step.M8.v8_over_v4.*, unprinted); the minimax-regret reason stands. |
| 29 | framing | abs-summary, intro-*, mot-two-levers, meth-metrics, VI-A, VI-B, eval-placement, disc-*, conc-summary | Area-efficiency reframing (user-approved brief, 2026-11-11): CoDe is the area-efficiency answer to the wider-PU family (LP-Spec-style: per logic mm² first, then speed; 1.60× framed as the iso-area comparison) and the speed answer to the faster-PU family (P3-LLM-style: speed first). The 1.07× and 29.9 / 27.9 tok/s left the abstract, introduction and conclusion (VI-B keeps them). The DRAM-specific reason (logic 10× less dense, devaux; the column already spans four command clocks) is stated in I, III-C/D and VII-A. New VII-A (storage versus arithmetic, ΔA / (S − 1), Fig. 10, storage-cost break-even) speaks of LP-Spec-style only; VI-F moved to VII-B; the conclusion is VIII. |
