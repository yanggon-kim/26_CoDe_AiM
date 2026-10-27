# Commands Are the Bottleneck: CoDe, a Command-Decoupled PIM for Skinny GEMMs on Mobile and Server DRAM: outline
Synced with: f812c92; body ends p. 11 col R; refs end p. 13.
Legend: one entry per source paragraph, in source order, tied to the `.tex` by `% P:<id>`; Message = the one claim a reader takes away; Floats = figures/tables/equations cited (first cite marked); Numbers = key printed numbers ← the script that asserts them (evaluation topic in brackets); Cites = bib keys; Links = → promise fulfilled by <id>, ← relies on <id>. Check: `python3 scripts/check_outline.py`.

Number sources, short names: `tables` = scripts/make_tables.py (functions in brackets); `roof` = make_fig_roofline.py; `brk` = make_fig_breakdown.py; `seq` = make_fig_sequence.py; `vsw` = make_fig_vsweep.py; `phone` / `hbm2` = make_fig_phone.py / make_fig_hbm2.py. Evaluation topics: `2x2` = evaluation/dac_2x2, `sd8g3` = evaluation/dac_sd8g3 (EV-58 pack via scripts/dac_data.py).

## Abstract  (sections/00_abstract.tex)
- **[abs-summary]**
  - Message: CoDe lets one DRAM column command feed a tile of tokens at the PU's own clock, so PIM serves skinny decode GEMMs that command-paced PIM designs serve only with more multipliers or more commands.
  - Floats: —
  - Numbers: M 2–32; 4× multipliers; two tokens per read; 5 / 4 ns column; four beats at 0.8–1 GHz; 1.86× GEMM per logic mm², 1.00–1.006× decode speed; 1.68× step, 1.26× per mm², 1.64× energy ← tables [headline, phone_levels], roof
  - Cites: —
  - Links: → intro-code-proposal, eval-phone-per-mm2, eval-phone-decode-speed, eval-server-beats, eval-server-area, eval-server-energy

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
  - Links: → mot-stock-crossover, mot-gemv-only, mot-idle-beats
- **[intro-prior-families]**
  - Message: Prior PIM raises the ceiling either with more multipliers (wider PU) or with more commands (faster PU), and both families keep every MAC paced by a DRAM command.
  - Floats: —
  - Numbers: 4× multipliers; 16.92 % of an LPDDR5 die ← lpspec (cited); two tokens per read (structural)
  - Cites: lpspec, p3llm
  - Links: → mot-wider-pu, mot-faster-pu, mot-logic-cost
- **[intro-timing-insight]**
  - Message: DRAM timing parameters space the column commands that access the array, not the MACs on a latched column, so one column period can feed D = 4 PU beats.
  - Floats: —
  - Numbers: 5 ns (LPDDR5-6400), 4 ns (HBM2) column; 1 GHz PU in silicon; 0.8 / 1 GHz; D = 4 ← cited / structural
  - Cites: hbmpim, lpspec, aimjssc
  - Links: → mot-depth, mot-pu-clock-precedent
- **[intro-code-proposal]**
  - Message: CoDe runs D beats per column command over a tile of V tokens at the stock multiplier count, and on each rival's own ground it matches LP-Spec-style's decode speed on half the logic and outruns P3-LLM-style on HBM2.
  - Floats: —
  - Numbers: 1.86× per logic mm², 1.00–1.006×, 0.539× logic area; 1.68×, 1.26×, 1.64× ← tables [headline, phone_levels, table4]
  - Cites: sd8g3
  - Links: → des-tile-mac-overview, eval-phone-per-mm2, eval-phone-decode-speed, eval-server-beats, eval-server-area, eval-server-energy
- **[intro-contributions]** (itemize, three items)
  - Message: The paper contributes the depth analysis of command-decoupled MACs, the CoDe PU and command extension, and a two-pairing evaluation on each rival's own memory.
  - Floats: —
  - Numbers: D = 4 (LPDDR5-6400, HBM2) ← structural (HBM3 dropped with mot-depth's extrapolation)
  - Cites: —
  - Links: → mot-depth, des-command-set, des-tile-mac-pu, eval-phone-summary, eval-server-summary

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
  - Message: Column commands move one 32-byte atom of an open row and may issue every t_CCD_S across bank groups and every t_CCD_L within one, which is twice as long.
  - Floats: Fig. 1
  - Numbers: 16 banks, four bank groups, 32 B ← structural
  - Cites: ramulator2, p3llm
  - Links: → mot-faster-pu
- **[bg-aim-pu]**
  - Message: AiM-style PIM puts a PU beside each bank and a shared global buffer on the die, and one all-bank MAC command every t_CCD_L starts one MAC beat in every PU.
  - Floats: Fig. 1
  - Numbers: 32 INT8 multiplies per beat ← structural
  - Cites: aimjssc, hbmpim
  - Links: → mot-idle-beats
- **[bg-row-sweep]**
  - Message: A GEMV runs as row sweeps of about 62 all-bank MAC commands between non-MAC commands, and stock AiM sweeps each row once per token.
  - Floats: Fig. 1
  - Numbers: c ≈ 62 ← tables [umac_table] (2x2 §2h)
  - Cites: aimjssc
  - Links: → mot-nonmac-commands, des-row-reuse

## III. Motivation  (sections/03_motivation.tex)
- **[mot-modelled]**
  - Message: The throughput numbers of the motivation are modelled on the two platforms of Table III and the methodology.
  - Floats: Table III (first cite; configuration table, lives in V-A: F12 exception)
  - Numbers: —
  - Cites: —
  - Links: ← meth-platforms
### A. PIM–Host Crossover
- **[mot-roofline-setup]**
  - Message: Fig. 2 sets the host NPU's roofline against simulated stock and rival PIM GEMMs on each platform.
  - Floats: Fig. 2, Table III
  - Numbers: M = 2^k; 56 of 68 GB/s, 51.2 GB/s pins → 42 GB/s [assumption] ← cited; 42 asserted in roof; the edge NPU's 131 TOPS / 256 GB/s moved to Table III ← tables [platform_block]
  - Cites: roofline, sd8g3, powerinfer2, heterollm, p3llm
  - Links: → meth-platforms
- **[mot-host-roof]** "Host roof in the skinny range"
  - Message: The host stays memory-bound across the whole skinny range because both NPUs' ridge points sit far above M = 32.
  - Floats: Fig. 2
  - Numbers: ridge M ≈ 143 and M = 128 ← roof
  - Cites: sd8g3, p3llm
  - Links: ← intro-host-memory-bound
- **[mot-stock-crossover]** "Stock-PIM crossover"
  - Message: Stock PIM beats the host only for the first few token rows, because stock AiM runs a GEMM as M repeated GEMVs, whose flat ceiling the host's rising memory roof overtakes below most published M.
  - Floats: Fig. 2
  - Numbers: 9.75× / 4× at M = 1; crossover M = 6 and 2–3 ← roof; GEMM time ∝ M (tolerance asserted, not printed) ← tables [stock_checks]
  - Cites: —
  - Links: ← intro-pim-gemv-ceiling, bg-skinny-range
- **[mot-gemv-only]** "GEMV-only use of PIM"
  - Message: Published PIM systems keep PIM for GEMVs and send the GEMMs to the host or NPU.
  - Floats: —
  - Numbers: batch 8 (P3-LLM offload) ← cited
  - Cites: attacc, neupims, ianus, p3llm
  - Links: ← intro-pim-gemv-ceiling; → eval-server-beats
### B. Two Root Causes of Stock PIM Inefficiency
- **[mot-time-breakdown]** "Useful-MAC share of stock GEMM time"
  - Message: Stock AiM's useful MAC work fills at most a fifth of a GEMM's time because two root causes, idle beats inside the MAC slots and non-MAC commands between them, cut the slot factor U_MAC and the sweep factor f_MAC of U = U_MAC × f_MAC.
  - Floats: Fig. 1 (b, c), Fig. 3 (first cite), Table III (t_CK)
  - Numbers: order setting → setup → finding → transition: MAC slots (useful / idle beats) and non-MAC commands (row switch, token load/drain, refresh) by Fig. 1b, c; one channel; 2048×64, 4096×256, 4096×4096; U = W t_CK / T_GEMM, D = 4; useful 14.1–19.1 %, idle 42.2–57.4 %, non-MAC 23.4–43.7 %, stalls ≤ 0.015 % ← brk (2x2 §2j); U = U_MAC × f_MAC ← tables [umac_table]; closing transition "two root causes: idle beats …, which set the slot factor, and non-MAC commands …, which set the sweep factor"
  - Cites: —
  - Links: ← bg-aim-pu, bg-row-sweep; → mot-idle-beats, mot-nonmac-commands
- **[mot-idle-beats]** "Idle beats"
  - Message: Stock PIM couples every MAC to a column access, which leaves three of every four beats of a MAC slot idle.
  - Floats: Fig. 1 (panel b), Table III (the stock PU's clock), Fig. 3
  - Numbers: U_MAC = A b t_CK / t_slot = 1/4 (b = 1 mobile, 2 edge server); a PU four times faster, at CK, leaves every stock GEMM at the same cycle count (described before its result; never named "faster-PU") ← tables [stock_checks]; idle 53.9 % / 57.4 % of q_proj ← brk
  - Cites: hbmpim, aimjssc, p3llm (GEMV target: JSSC p. 1, P3-LLM p. 3)
  - Links: ← bg-aim-pu, mot-time-breakdown; → mot-depth, mot-two-levers, des-beat-slot-factor
- **[mot-nonmac-commands]** "Non-MAC commands"
  - Message: Stock AiM's row-switch commands outlast the useful MAC work of their row sweep, so the sweep factor caps stock AiM's useful-MAC utilization below a fifth.
  - Floats: Eq. 1 (eq:fmac), Table I (first cite; float defined inside the paragraph), Fig. 1, Fig. 3
  - Numbers: t_row 87.73 / 94.76 ns, t_tok 4.26 / 9.64 ns, ρ 0.070 / 0.061; 91.2 vs 78.0 ns; TMOD 40.5, ACT16 37.9, PREA 11.5, WRMAC16 1.2 ns; row switch 19.5 / 13.8 %; RDMAC16 ≤ 1.0 %; 64 / 16 / 1 sweeps per fill; token load 0.6 / 2.4 % vs 28.3 / 28.5 %; refresh 7.1 / 6.2 %; 146.2 incl. 41.8 vs 123.3 ns; f_MAC 0.717, U 0.179 / 0.193 ← tables [umac_table, umac_src_table] (2x2 §2h–2i, §2p), brk
  - Cites: —
  - Links: ← mot-time-breakdown, bg-row-sweep; → mot-rival-row-switch, mot-two-levers, des-row-reuse
### C. GEMM Support in Prior PIM
- **[mot-prior-families]**
  - Message: Prior PIM designs fill idle beats in two families, with more multipliers or with more commands, and tie the tokens that share a row sweep to the width of one MAC slot.
  - Floats: Fig. 4 (first cite; fig:timeline, float defined after this paragraph)
  - Numbers: M = 8, D = 4; 8 periods, 8 commands, 8 reads (stock row) ← structural
  - Cites: —
  - Links: ← intro-prior-families, mot-time-breakdown; → mot-wider-pu, mot-faster-pu, mot-rival-row-switch
- **[mot-wider-pu]** "Wider-PU family"
  - Message: Wider-PU designs fill a column period's idle beats with four times the multipliers, so LP-Spec-style, the mobile rival, reaches U_MAC = 1 only at four times the stock arithmetic.
  - Floats: Fig. 2, Table I, Table III
  - Numbers: four 32-wide ALUs, one MAC step per column period (200 MHz → Table III); crossover M = 20–24; U per multiplier 0.173–0.174 / 0.185 ← roof, tables [umac_table]
  - Cites: lpspec, papi, stepstone, duplex, h2llm, monde
  - Links: ← intro-prior-families, mot-idle-beats; → mot-logic-cost, eval-phone-summary
- **[mot-logic-cost]** "Cost of logic in a DRAM die"
  - Message: Logic in a DRAM die costs capacity, so per logic mm² the wider-PU family keeps only part of its four-fold ceiling over stock AiM.
  - Floats: —
  - Numbers: 10× less dense, 3 vs 10+ metal layers; 0.19 mm² per PU; 50 % capacity; 16.92 % vs 20–25 % ← cited; LP-Spec-style 314 / 697 vs stock AiM 216 / 492 GOPS/mm² ← roof (logic-die and hybrid-bonding sentences cut: out of scope)
  - Cites: devaux, aimjssc, hbmpim, pimpal, lpspec
  - Links: ← intro-prior-families, mot-wider-pu; → eval-phone-per-mm2, eval-server-area
- **[mot-faster-pu]** "Faster-PU family"
  - Message: A faster PU paced by per-token commands fills at most two beats per column read, so P3-LLM-style, the edge-server rival, stops at U_MAC = 1/2 but keeps a higher ceiling per logic mm² than LP-Spec-style.
  - Floats: Fig. 2, Table III
  - Numbers: one beat per t_CCD_S (500 MHz → Table III); 4 periods, 8 commands, 4 reads; depth cap 2; crossover M = 4–6; 390 / 830 GOPS/mm² (moved from mot-logic-cost, after P3-LLM-style is named) ← roof
  - Cites: p3llm, hbmpim
  - Links: ← bg-dram-channel, intro-prior-families, mot-idle-beats, mot-logic-cost; → eval-server-summary
- **[mot-rival-row-switch]** "Row-switch commands in prior designs"
  - Message: Both families share a row sweep's row-switch commands only among the tokens of one MAC slot, so their non-MAC time per token falls only as far as the slot widens, with multipliers or with commands (absolute form; a flat f_MAC is not framed as the defect, since CoDe's HBM2 f_MAC sits at the same level).
  - Floats: Table I, Eq. 1
  - Numbers: A = 2 / 4; non-MAC time per token 123.39 → 63.94 (P3-LLM-style) / 34.41 ns (LP-Spec-style), mobile ← tables [umac_table] (Table I); Eq. 1 within 0.33 % / 0.59 % on the designs it was not fitted on ← tables [umac_table]
  - Cites: p3llm (p. 11: each access reused twice, fewer duplicated row activations)
  - Links: ← mot-nonmac-commands, mot-wider-pu, mot-faster-pu; → mot-two-levers
- **[mot-other-pim]**
  - Message: The remaining LLM PIM designs either serve one input vector per weight read or reorganize the work around the PU, and the three that run several beats per column read still hold one vector.
  - Floats: —
  - Numbers: —
  - Cites: newton, cent, pimgpt, localut, pimpal, pimdl, pimba, paise, splitsync, dots, pimphony, paik2022, salpim, pfpu, cdpim
  - Links: — (stays last in III-C: user, 2026-10-27)
### D. The Opportunity: DRAM Timing Bounds Access, Not MACs
- **[mot-depth]**
  - Message: The column period sets how often weights reach a PU and the PU clock sets how often the PU computes, so one column read can feed D = ⌊t_col × f_PU⌋ = 4 beats on both platforms.
  - Floats: Table III (column period = 4 t_CK)
  - Numbers: D = 4 ← structural (5 / 4 ns, 1.25 / 1 ns and 0.8 / 1 GHz now in Table III; HBM3 extrapolation cut: not evaluated)
  - Cites: hbmpim, p3llm
  - Links: ← intro-timing-insight, mot-idle-beats; → conc-summary
- **[mot-pu-clock-precedent]** "PU clock in a DRAM die"
  - Message: A PU clocked at CK has precedent in DRAM silicon, from UPMEM's 500 MHz cores to GDDR6-AiM's 1 GHz multipliers and an HBM-PIM-style PU at CK.
  - Floats: —
  - Numbers: 1.0–1.2 GHz bus, 250–300 MHz, 20 nm; 500 MHz, 2x-nm; 1 GHz, 1y-nm; eight 1y-nm dies ← cited
  - Cites: hbmpim, devaux, aimjssc, flashbolt, pfpu
  - Links: ← intro-timing-insight; → des-pu-clock
- **[mot-two-levers]**
  - Message: Stock AiM uses one of the D = 4 beats each column read offers and pays a row sweep's row-switch commands for every token, which leaves one lever per root cause: beat filling (IV-B) for the idle beats and the slot factor, row reuse (IV-C) for the non-MAC commands, by cutting their time per token (no claim that row reuse raises f_MAC).
  - Floats: Fig. 1
  - Numbers: D = 4 beats per column read, one used ← structural; no CoDe number; closing clause: the rivals share a row sweep only among one slot's tokens, row reuse sets the tokens per sweep by the tile size V at unchanged lanes (from IV-C / IV-D's definitions)
  - Cites: —
  - Links: ← mot-idle-beats, mot-nonmac-commands, mot-rival-row-switch, mot-depth; → des-tile-mac-overview, des-beat-decouple, des-row-reuse

## IV. CoDe Design  (sections/04_design.tex)
### A. Overview: One Command, Many MAC Beats
- **[des-tile-mac-overview]**
  - Message: CoDe's tile MAC command serves V tokens per weight column and carries both levers of III-D, while every command keeps every DRAM timing parameter (opening does not repeat III-D's transition).
  - Floats: Table I (CoDe row)
  - Numbers: 1/V MAC commands per token and column vs 1, 1/4, 1 ← structural; ceiling 583 / 1,247 GOPS per logic mm² with one PU, one command and the stock multiplier count; U 0.779 (mobile) ← tables [umac_table], roof
  - Cites: —
  - Links: ← mot-two-levers; → des-beat-decouple, des-row-reuse
- **[des-sequence-walk]**
  - Message: One q_proj weight row at M = 8 shrinks from stock AiM's eight sweeps to CoDe's one sweep of 64 tile MACs as the two components are added.
  - Floats: Fig. 5 (first cite)
  - Numbers: 3,250 ns, 512 MAC commands; 1,360 ns; 2,629 ns; 64 tile MACs, 738.75 ns ← seq (2x2 §2j)
  - Cites: —
  - Links: → des-gain-order
- **[des-gain-order]**
  - Message: CoDe's window is 4.40× shorter than stock AiM's in either order of the two components, and beat filling alone is only a model because it needs row reuse to exist.
  - Floats: Fig. 5
  - Numbers: 4.40×; 2.39× then 1.84×; 1.24× then 3.56×; one CK cycle vs the column period (Table III); WRGB per 64 sweeps; q_proj 4.32× ← seq
  - Cites: —
  - Links: → eval-gain-sources
### B. Beat Filling
- **[des-beat-decouple]**
  - Message: Beat filling runs the PU's beats at its own clock f_PU = D / t_col, so a tile MAC holds its column for V/D periods while the PU runs one beat per token.
  - Floats: Table III, Fig. 4 (fig:timeline, CoDe row)
  - Numbers: V = 8, D = 4, V/D = 2 periods ← structural
  - Cites: —
  - Links: ← mot-two-levers
- **[des-beat-slot-factor]**
  - Message: Beat filling raises the slot factor from 1/4 to 1 and reaches LP-Spec-style's 4× ceiling with the stock multiplier count.
  - Floats: Fig. 5
  - Numbers: MAC slots 2,560 → 640 ns; one MAC command per two periods; per-sweep rule 2.3 % shorter ← seq
  - Cites: —
  - Links: ← mot-idle-beats; → des-tile-mac-pu, eval-phone-per-mm2, eval-gain-sources
### C. Row Reuse
- **[des-row-reuse]**
  - Message: Row reuse lets the V tokens of a tile share one row sweep, so the row-switch commands are paid once per V tokens and the non-MAC time per token falls, while token load and drain stay per token.
  - Floats: Fig. 5, Table I
  - Numbers: t_row / A + t_tok plus refresh per token; moved from des-tile-mac-overview: simulated non-MAC time per token 123.39 → 22.15 ns (mobile, V = 8), 146.17 → 43.51 ns (edge server, V = 4) ← tables [umac_table]; 8 → 1 row switch; MAC slots 2,560 ns; drain block 61.25 ns ← seq
  - Cites: —
  - Links: ← mot-nonmac-commands; → des-storage, eval-gain-sources
### D. Tile MAC Command and PU Microarchitecture
- **[des-command-set]** "Command set"
  - Message: CoDe adds the tile MAC and the burst drain to AiM's all-bank interface and keeps every other command.
  - Floats: Table II (first cite; tab:cmds)
  - Numbers: — (Table II ← seq)
  - Cites: aimjssc
  - Links: ← intro-contributions
- **[des-tile-mac-pu]** "Tile MAC in the PU"
  - Message: Inside the PU a tile MAC latches the column, and a beat sequencer steps the V tokens through the lanes into their accumulator slots before a burst drain.
  - Floats: Fig. 6 (first cite)
  - Numbers: lanes (Table III) ← structural
  - Cites: —
  - Links: ← intro-contributions, des-beat-slot-factor
- **[des-storage]** "Storage"
  - Message: The global buffer, the staging buffer and a double-set accumulator file hold the tile's inputs and partial sums.
  - Floats: Table III
  - Numbers: 2,048 INT8 inputs, 2 KB per token, 16 KB GB, 512 writes of 32 B ← seq; three-entry queue of 512-bit words; two / four sets of V slots ← structural (Table III ← tables [table4])
  - Cites: —
  - Links: ← des-row-reuse
- **[des-tile-size]** "Tile size"
  - Message: The tile size V sizes only CoDe's storage, so V is set by the range of M a platform serves: V = 2D = 8 on the mobile platform and V = D = 4 on HBM2.
  - Floats: —
  - Numbers: V = 8 / 4; 4 KB K chunk, 512-bit slice ← structural
  - Cites: —
  - Links: → eval-vsweep-summary, eval-vsweep-robust
- **[des-pu-clock]** "PU clock"
  - Message: The tile keeps the PU clock within a DRAM process's reach because each accumulator slot takes one update per V ≥ D beats and the lanes multiply narrow integers.
  - Floats: —
  - Numbers: 1 GHz BF16 (cited) ← aimjssc
  - Cites: aimjssc, p3llm
  - Links: ← mot-pu-clock-precedent; → meth-designs-area, eval-power-clock-cost
### E. Mapping Skinny GEMMs and Attention
- **[des-mapping]**
  - Message: CoDe maps a skinny GEMM as stock AiM does but cuts the M token rows into tiles of V, and speculative-decoding attention maps the same way while batched attention stays one GEMV per request.
  - Floats: —
  - Numbers: —
  - Cites: —
  - Links: → eval-phone-per-mm2

## V. Methodology  (sections/05_methodology.tex)
### A. Hardware Platforms
- **[meth-platforms]**
  - Message: The mobile platform pairs a Snapdragon 8 Gen 3 NPU with PIM on x64 LPDDR5-6400, and the edge server pairs P3-LLM's NPU with one HBM2 stack (Table III).
  - Floats: Table III (configuration table: platform block above design block; float defined at V-A's start)
  - Numbers: platform block (NPU 12 / 131 TOPS, 42 / 256 GB/s; LPDDR5-6400 / HBM2 2.0 Gb/s; 4 dies × 16 / 16 pCH × 16 banks; 409.6 / 1,024 GB/s; t_CK 1.25 / 1 ns; t_CCD_S, t_CCD_L 2.5, 5 / 2, 4 ns; PU per bank / per two banks; t_REFI, t_RFCab 3.906 µs, 280 ns / simulator preset; INT8 / W4A8) ← tables [platform_block] (dac_sd8g3 ev57_host, ev57_ceilings, ev56_mech_inputs, context.md; dac_2x2 ev57_host, ev57_ceilings, dacp_inputs, dac2x2_setup, utrace_run_core8_gbfill; EV-58 dac_table4) and cited spec values; prose: 12 TOPS for INT8 [assumption], 131 TOPS peak [assumption]; 30 µs [assumption] ← npufaster; 2.285 W [assumption] ← derived from cites, no script; 55 W [assumption] ← tpuv4i
  - Cites: sd8g3, lpspec, hao2025, npufaster, heterollm, tman, p3llm, tpuv4i
  - Links: ← mot-roofline-setup
### B. PIM Designs and Area
- **[meth-designs-area]**
  - Message: Every design computes at its rival's precision on one controller, and CoDe reaches LP-Spec-style's peak on 0.539× its logic area by spending area on storage instead of arithmetic.
  - Floats: Table III
  - Numbers: V = 8 / V = D = 4; 0.539×; arithmetic 0.73 / 0.34, storage 0.32 / 0.10; HBM2 0.56× and 1.33× ← tables [table4, area_split]
  - Cites: aimjssc, lpspec, p3llm
  - Links: ← des-tile-size, des-pu-clock; → eval-vsweep-summary
### C. Simulator and Models
- **[meth-simulator]**
  - Message: A cycle-level AiM simulator on Ramulator 2.0 times every design's commands, including JEDEC refresh, and synthesis-based models give area, peak power and energy per token.
  - Floats: — (Fig. 7 float defined here)
  - Numbers: 1.78× vs 1.6× ← tables [phone_levels]; U 0.355 → 0.351 ← tables [umac_table]; t_REFI / t_RFCab → Table III [assumption]; ρ 0.070 ← tables [umac_table]; 45 nm → 1z, Nangate45, 1.05 V; 87.6 / 54.8 mW fetch ← tables [table_power]
  - Cites: ramulator2, cent, p3llm, attacc, abc, openroad, horowitz
  - Links: ← mot-nonmac-commands; → eval-power-peak
### D. Algorithms and Workloads
- **[meth-workloads]**
  - Message: The mobile platform runs speculative decoding of Llama-2-7B with a 1.1B draft or an EAGLE head, and the edge server runs batched decoding of five LLMs at a 4K context.
  - Floats: —
  - Numbers: acceptance 0.7; L = 128–1024, 128–4096; six FC shapes, three head configurations; batch 1–64 ← configuration
  - Cites: eagle
  - Links: → eval-phone-decode-speed, eval-server-summary
### E. Metrics
- **[meth-metrics]**
  - Message: Speed is tokens per second, area efficiency is that speed per PIM logic mm², and energy is system energy per token, with ranges taken over M and L on the mobile platform and over per-M means on the edge server.
  - Floats: Table III
  - Numbers: —
  - Cites: —
  - Links: → eval-phone-summary, eval-server-summary

## VI. Evaluation  (sections/06_evaluation.tex)
- **[eval-modelled]**
  - Message: All results are modelled, and ratios above 1 favour CoDe.
  - Floats: —
  - Numbers: —
  - Cites: —
  - Links: —
### A. Mobile Platform against LP-Spec-Style
- **[eval-phone-summary]**
  - Message: CoDe matches LP-Spec-style's decode speed on the mobile platform with 0.539× its logic area, so each unit of decode throughput costs about half the silicon.
  - Floats: Fig. 7 (first cite)
  - Numbers: 0.539×; L = 1024 ← tables [table4]
  - Cites: —
  - Links: ← intro-code-proposal, mot-wider-pu
- **[eval-phone-per-mm2]** "Throughput per logic mm$^2$"
  - Message: CoDe nearly doubles LP-Spec-style's throughput per logic mm² for GEMMs, attention layers and decode steps, with the area ratio as the floor.
  - Floats: Fig. 7, Table I
  - Numbers: 1.86–3.06×, 1.86–2.34×, 1.86–2.85×; attention 1.01–1.14× at M = 2–4; 0.125 MAC commands per token and column; U 0.779 vs 0.694; 0.695 at M = 4 ← tables [phone_levels, mech_checks, umac_table], phone
  - Cites: —
  - Links: ← intro-code-proposal, des-beat-slot-factor, mot-logic-cost
- **[eval-phone-decode-speed]** "Decode speed"
  - Message: CoDe never decodes slower than LP-Spec-style end to end and runs single decode steps faster from M = 5 on.
  - Floats: Fig. 7
  - Numbers: 47.1 vs 46.8 tok/s (M = 3); 68.1 tok/s (M = 4); 1.00–1.006×; 1.54× at M = 5, 1.07–1.31× from M = 8; NPU crossover M = 24–26; 7.71× of 6.1 tok/s; 10.6 tok/s ← tables [headline, phone_levels] (sd8g3 §2g)
  - Cites: —
  - Links: ← intro-code-proposal, meth-workloads
- **[eval-phone-energy]** "Energy per token"
  - Message: The speculative loop on PIM spends an order of magnitude less energy per token than the NPU, and CoDe also saves attention-layer energy against LP-Spec-style.
  - Floats: —
  - Numbers: 66.2 / 49.8 mJ vs 971 / 558 mJ; 1.05–1.16× at M ≤ 4, 1.16–1.28× from M = 8 ← tables [headline, phone_levels]
  - Cites: —
  - Links: —
### B. Edge-Server Platform against P3-LLM-Style
- **[eval-server-summary]**
  - Message: CoDe runs batched HBM2 decode steps faster than P3-LLM-style, and the speed more than repays CoDe's larger logic.
  - Floats: Fig. 8 (first cite)
  - Numbers: —
  - Cites: —
  - Links: ← intro-code-proposal, mot-faster-pu
- **[eval-server-beats]** "Beats per command"
  - Message: CoDe's four beats per command against P3-LLM-style's two make its batched step 1.68× faster from batch 8 with about half the C-bus load.
  - Floats: Fig. 8
  - Numbers: 1.68×, 2.87–2.88× stock; 1.43–1.71× at batch 3–6; C bus 0.791 vs 0.431; U 0.739 vs 0.379; NPU crossover batch 8–12 ← tables [headline, mech_checks, umac_table], hbm2, roof
  - Cites: p3llm
  - Links: ← mot-gemv-only, intro-code-proposal
- **[eval-server-area]** "Speed against area"
  - Message: CoDe's speed more than pays for its larger logic from batch 3, while P3-LLM-style's smaller PU leads at batch 1–2.
  - Floats: Fig. 8
  - Numbers: 1.26× from batch 8; 1.08–1.28× at 3–6; 0.80–0.84× at 1–2 ← tables [headline], hbm2
  - Cites: —
  - Links: ← intro-code-proposal, mot-logic-cost
- **[eval-server-energy]** "System energy"
  - Message: CoDe's speed lead carries over to system energy whether the idle NPU draws 55 W or is power-gated.
  - Floats: —
  - Numbers: 1.64× (55 W), 1.46× (gated) ← tables [headline]
  - Cites: p3llm
  - Links: ← intro-code-proposal, meth-platforms
- **[eval-gain-sources]** "Sources of CoDe's gain"
  - Message: CoDe's gain over stock AiM comes from beat filling, which raises the slot factor, and row reuse, which keeps the sweep factor near stock AiM's level once beat filling shortens the MAC slots; beat filling earns its full step only after row reuse has removed most of the row-switch overhead (relative form; never claims CoDe raises f_MAC on the edge server).
  - Floats: Table IV (first cite), Table I
  - Numbers: U 0.223 / 0.222 after row reuse; beat-filling step 3.49× / 3.33×; CoDe f_MAC 0.779 / 0.739 vs stock 0.717 / 0.771 (Table IV); other order f_MAC = U 0.425 / 0.506, steps 2.37× then 1.83× and 2.62× then 1.46× ← tables [umac_src_table] (2x2 §2i)
  - Cites: —
  - Links: ← des-gain-order, des-beat-slot-factor, des-row-reuse
### C. Ablation Study
- **[eval-vsweep-summary]**
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
  - Numbers: wins at M = 5–7, 9–10, 13–15; 1.324× and 0.862×; HBM2 peak 0.944×; 29.4 / 24.5 % vs 13.8 %; HBM2 11.7 % vs 28.8–30.0 %; one-tile 4.6 / 13.8 %; best M = 3 / 4 ← vsw (2x2 §2l–2n)
  - Cites: —
  - Links: ← des-tile-size, eval-phone-decode-speed
### D. Peak Power
- **[eval-power-peak]**
  - Message: CoDe's faster PU clock leaves its peak power within a few percent of LP-Spec-style's on both platforms.
  - Floats: Table III
  - Numbers: 1.04× per die, 1.03× per pCH ← tables [table_power]
  - Cites: lpspec
  - Links: ← meth-simulator
- **[eval-power-clock-cost]** "Cost of the faster clock"
  - Message: CoDe's 800 MHz clock costs little arithmetic energy, and its higher PU power comes from clocked storage while LP-Spec-style pays in leakage.
  - Floats: —
  - Numbers: 2.4 % ← tables [table_power] (microarch d1/pu_power/pu_peak_power.csv, not collected); leakage 2.9× / 2.8× ← tables [table_power]
  - Cites: —
  - Links: ← des-pu-clock
- **[eval-power-edge-charge]** "Charge per clock edge"
  - Message: CoDe spreads the same MAC rate over four times as many clock edges, so each edge draws several times less charge from the supply.
  - Floats: —
  - Numbers: 522 pJ per 1.25 ns vs 1,776 pJ per 5 ns; 3.4× / 3.1× ← tables [table_power]
  - Cites: —
  - Links: —
- **[eval-power-gating]** "Clock gating in CoDe"
  - Message: CoDe's registers idle on most cycles, so clock gating cuts CoDe's peak power far more than LP-Spec-style's, though every other number describes the ungated designs.
  - Floats: —
  - Numbers: every 16 / 6 / 8 cycles; −11.6 % / −15.1 % vs −0.5 % / −3.6 %; 0.92× / 0.87× ← tables [table_power]
  - Cites: —
  - Links: —

## VII. Conclusion  (sections/07_conclusion.tex)
- **[conc-summary]**
  - Message: Decoupling MAC timing from DRAM command timing lets one column command feed many PU beats over a tile of tokens, and the decoupling carries over to any DRAM whose column outlasts one beat.
  - Floats: —
  - Numbers: 1.86×; 1.68× ← tables [headline, phone_levels]
  - Cites: —
  - Links: ← mot-depth, eval-phone-per-mm2, eval-server-beats

## Float map
| float | label | source file | first cite | lands |
|---|---|---|---|---|
| Fig. 1 | fig:dram_pim | figs/fig_dram_pim.pdf (01_introduction.tex) | intro-pim-gemv-ceiling (p1 L) | p1 R |
| Fig. 2 | fig:roofline | figs/fig_roofline.pdf ← roof (01_introduction.tex) | intro-pim-gemv-ceiling (p1 L) | p2 L |
| Fig. 3 | fig:breakdown | figs/fig_breakdown.pdf ← brk (03_motivation.tex) | mot-time-breakdown (p3 L) | p3 R |
| Table I | tab:umac | tables/tab_umac.tex ← tables (03_motivation.tex, inside mot-nonmac-commands) | mot-nonmac-commands (p4 L) | p4 L |
| Fig. 4 | fig:timeline | figs/fig_timeline.pdf ← make_fig_timeline.py (03_motivation.tex, after mot-prior-families) | mot-prior-families (p4 L) | p4 R |
| Fig. 5 | fig:sequence | figs/fig_sequence.pdf ← seq (04_design.tex) | des-sequence-walk (p6 L) | p6 L |
| Fig. 6 | fig:tile | figs/fig_tile.pdf ← figs/src/fig_tile.html, html2pdf.py (04_design.tex) | des-tile-mac-pu (p7 L) | p7 L |
| Table II | tab:cmds | tables/tab_cmds.tex ← seq (04_design.tex) | des-command-set (p7) | p7 R |
| Table III | tab:params | tables/tab_params.tex ← tables [platform_block, table4] (05_methodology.tex, V-A) | mot-modelled (p3 L) | p8 L (configuration table: F12 exception; first cite in V on p8) |
| Fig. 7 | fig:phone | figs/fig_phone.pdf ← phone (05_methodology.tex, figure*) | eval-phone-summary (p9) | p9 top, both columns |
| Fig. 8 | fig:hbm2 | figs/fig_hbm2.pdf ← hbm2 (06_evaluation.tex) | eval-server-summary (p9 R) | p10 L |
| Fig. 9 | fig:vsweep | figs/fig_vsweep.pdf ← vsw (06_evaluation.tex) | eval-vsweep-summary (p10 L) | p10 R |
| Table IV | tab:umac_src | tables/tab_umac_src.tex ← tables (06_evaluation.tex) | eval-gain-sources (p10) | p11 L |
| Eq. 1 | eq:fmac | 03_motivation.tex | mot-nonmac-commands | p4 L |

## Observations
| # | kind | where | observation |
|---|---|---|---|
| 1 | two messages | mot-nonmac-commands | One paragraph (≈ 30 source lines, ≈ 25 numbers) carries the f_MAC formula and fit, the per-command row-switch split, token load against GB fills, refresh, the edge-server totals and stock U = 0.179; class names are used before this paragraph defines them. |
| 2 | two messages | meth-simulator | One paragraph carries five topics: the simulator and PU model, P3-LLM validation and C/A re-timing, refresh, area scaling, and the power/energy flow. |
| 3 | two messages | des-beat-slot-factor, des-gain-order, eval-phone-per-mm2, eval-phone-energy, eval-server-beats, eval-vsweep-robust, mot-logic-cost | Each paragraph's opening claim is followed by a second claim (command-bus room and the VI-B composition rule; why row (b) is a model and the 4.32× GEMM; the M = 8 command mechanism; attention energy against LP-Spec-style; the NPU crossover; the minimax choice of V = 8; the logic-die designs). |
| 4 | placement | eval-gain-sources | The stock-to-CoDe sources-of-gain paragraph covers both platforms but sits in VI-B (edge server against P3-LLM-style), and its Table IV lands two pages after the citation. |
| 5 | same claim, two values | des-gain-order vs eval-gain-sources | The two-order gain prints 2.39× then 1.84× (Fig. 5 window) in IV-A and 2.37× then 1.83× (one layer, Table IV) in VI-B; only des-beat-slot-factor's 2.3 % sentence reconciles them. |
| 6 | restatement | intro-prior-families / mot-prior-families; intro-timing-insight / mot-depth; mot-idle-beats / mot-depth | The two families are named in I and III-C; mot-depth now points to Table III for the column period and CK instead of reprinting the intro's 5 ns / 4 ns / 0.8–1 GHz, but mot-idle-beats' column-access argument (column decoder, I/O sense amplifiers, hbmpim) and mot-depth's opener still share one argument. |
| 7 | restatement | des-tile-size / meth-designs-area; intro-prior-families / mot-logic-cost | The reason for V = 4 on HBM2 (twice the slice, one PU per two banks) is given in IV-D and again in V-B; LP-Spec's 16.92 % is printed in I and III-C; 0.539× appears in I, V-B and VI-A. |
| 8 | config table | Table III (tab:params) | One configuration table in V-A (platform block above design block); III–VI refer to it. Kept in prose where the sentence computes or derives: intro's 5 / 4 ns, 0.8 / 1 GHz and 42 GB/s (D and the ridge), III-A's 42 GB/s derivation, IV-D's GB / slice sizes, VI-C's 800 / 200 MHz and 1.25 / 5 ns per-edge charge. Row size has no collected source and stays out (for evaluation-owner). |
| 10 | promise | intro-code-proposal, intro-contributions | No intro paragraph announces the tile-size ablation (VI-C) or the peak-power study (VI-D); these results answer only des-tile-size and meth-simulator. |
| 11 | untraced number | meth-platforms, Table III | 2.285 W host power (derived from cites, no script); Table III's t_REFI 3.906 µs is asserted from evaluation/dac_sd8g3/context.md text ([A-REF1]) and t_RFCab 280 ns from the collected trace (utrace_run_core8_gbfill REFab gap), neither has a JEDEC cite; 131 TOPS (assumption with cite only); 56 / 68 / 51.2 GB/s (cites; only the 42 GB/s result is asserted). |
| 12 | number outside evaluation | eval-power-clock-cost | The 2.4 % clock cost is asserted by make_tables.py from microarch/04_data/d1/pu_power/pu_peak_power.csv, which no evaluation topic has collected. |
| 13 | structure | mot-other-pim | Stays last in III-C (user, 2026-10-27); no related-work section remains (options kept for later: (a) a short Related Work section before the Conclusion, from the ≈ 1 free column; (b) a landscape paragraph at the end of II-B; (c) keep it as the last paragraph of III-C, as now). mot-other-pim has no root-cause role in the reframed III-C. Labels `sec:bg:*` point into Section III (cosmetic). |
| 14 | unverified source | mot-rival-row-switch, mot-idle-beats | LP-Spec's own text on row activations was not checked: no LP-Spec PDF exists under 00_doc (paper_isca2's is empty; paper_dac's references hold p3llm.pdf, the AiM JSSC paper and others, not LP-Spec), so LP-Spec-style's sharing of a row sweep among its four tokens rests on our model (Table I, A = 4). P3-LLM's own text (p. 11) supports its two-token row-activation saving. HBM-PIM's statement of a GEMV target was not checked (no PDF); AiM JSSC p. 1 (RNN and MLP layers with low memory reuse, evaluated on GEMV) and P3-LLM p. 3 (both PCUs perform GEMV) were. |
| 15 | timing | Table III, mot-idle-beats | HBM2's column period prints t_CCD_L = 4 ns (cited) while the simulator's all-bank HBM2 MAC slot is 8 ns (b = 2, two banks per PU; dac2x2_setup); U_MAC's b = 2 reconciles them, but Table III shows no 8 ns slot. |
| 16 | resolved | mot-prior-families, mot-rival-row-switch, mot-two-levers, des-row-reuse, eval-gain-sources | Resolved (user, 2026-10-27): f_MAC is a share, so row reuse is stated in absolute form in III-C, III-D and IV-C (it cuts the non-MAC time per token: 123.39 → 22.15 ns mobile, 146.17 → 43.51 ns edge server) and in relative form in VI-B (it keeps f_MAC near stock AiM's level once beat filling shortens the slots: 0.779 / 0.739 vs 0.717 / 0.771). Guard: no sentence says CoDe raises f_MAC on the edge server (0.739 < 0.771) or frames the rivals' flat f_MAC as their defect; only the D = 1 row-reuse-only row lifts f_MAC (0.892 / 0.887). |
| 17 | ordering | mot-logic-cost, mot-faster-pu | With logic cost before the faster-PU family (user order), mot-logic-cost compares LP-Spec-style's per-mm² ceiling with stock AiM's (314 / 697 vs 216 / 492) and P3-LLM-style's 390 / 830 moved into mot-faster-pu after P3-LLM-style is named. |
