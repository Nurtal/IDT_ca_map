# Extraction progress

See docs/EXTRACTION_PROTOCOL.md for the session procedure.

<!-- auto:start -->
## Status (generated)

9104 articles in queue: 118 done, 8864 pending, 120 skipped, 2 error.

- tier 0: 71/192 processed
- tier 1: 169/6584 processed
- tier 2: 0/2328 processed

Next article: PMID 36769349 — How the Innate Immune DNA Sensing cGAS-STING Pathway Is Involved in Apoptosis
<!-- auto:end -->

### 2026-10-16 — batch 1 (tier 0)
Processed 24 tier-0 articles (19 done, 5 skipped as reviews/classification reports), 15 records.
New actors: STIMATE/TMEM110, TMEM203, SELENOK, UNC93B1.
Convention: STING partners with no calcium link (STAT2, COPA, STEEP, VAPB, TRIM13, SEL1L, ARF1...)
are NOT recorded — the build's inclusion rule would drop them anyway.
13 tier-0 articles were read but not recorded; they remain `pending` and are first in the queue.

### 2026-10-16 — tier 0 complete (primary research)
All tier-0 primary-research articles are processed: 49 done, 22 skipped.
The 121 tier-0 articles still pending are reviews/commentaries.
Records this session: 21 in data/raw/lit_20261016_b01.jsonl.

Notable: TRPV2 enters the map (STING binds and represses the ER Ca2+ channel; cGAMP
releases it) — the mirror image of STIM1 restraining STING. STIM1 is also *required*
for STING exocytosis during HSV-1 infection (PMC11005388), which conflicts with the
pure ER-brake model and should surface as a conflict badge.

Roughly half of the tier-0 articles yielded nothing: they cite Srikanth 2019 rather
than producing their own STIM1/STING data. Each decision carries a `--note` in the queue.

Lead not in the corpus: Woo et al., Cell 2024 (STING links glutamate excitotoxicity to
ferroptosis via STIM1), known only through its preview PMID 39059368. PubTator search
does not surface it; add it by PMID once identified.

### 2026-10-19 — tier 1, batch of 50 (the low-yield tail)
Processed the next 50 tier-1 articles (22 done, 28 skipped, each with a queue note), 5 records in
`data/raw/lit_20261019_b02.jsonl`. New nodes: BCL6, NFATC1.

**Next session:** keep going inside tier 1 (`queue next 50 --tier 1`), resuming at PMID 37961129.
The generated header line above names PMID 36769349 because it is the first pending article
overall, but tier 0 holds nothing but reviews now.

Yield: STING GOF T cells (PMC12423328) give the cleanest result of the batch — basal Ca2+ is
higher in STING V154M T cells and 4 h of DMXAA reproduces it in wild-type cells, with NFATc1
upregulated: STING drives the Ca2+-NFAT arm, the mirror of STIM1 restraining STING. BCL6 enters
the map as a transcriptional input to the anchor: Bcl6+/- Tfh cells downregulate Stim1 and show a
measurably weaker calcium response during B cell contact in vivo (FRET, 29% -> 8%).

Admitting NFATC1 also pulled six database-only edges into the graph (PRKACA, IKBKE, EGFR), with no
publications and no calcium content of their own. That is the build doing what it is told — every
kept node gets its database evidence — but it is worth watching: each new effector node widens the
graph more than the literature edge that justified it.

NEGATIVE worth keeping: in STING N153S Purkinje cells (PMC12746686) the CRAC inhibitor GSK-7975A
does not restore firing — the STIM1/CRAC arm is not the effector of that degeneration.

Lead not recorded: RCN1 (reticulocalbin-1, PMC10701779), an ER calcium-binding protein whose
knockdown switches on STING in AML cells — a second ER brake on STING next to STIM1, except that
the inclusion rule drops it (no GO calcium annotation, no calcium term in the claim sentence).
Revisit if a paper ties RCN1 to ER calcium and STING in one claim.

The tail is now mostly bioinformatics screens, atlases and network-pharmacology papers that
co-mention the genes without measuring anything. Seven articles were read in full; of the other
43, none had a single sentence carrying an anchor and a calcium term together, and only two
mentioned STIM1/ORAI1 at all (a patient count and an author-contribution artefact). That
co-occurrence screen is what made a 50-article batch feasible and is now step 3 of the protocol.

### 2026-10-19 — the curator's interactomes come in whole

The researcher's call on the two open questions of issue #16: *ratisse large, garde les 78 et
les 5*. A curated interaction with a level-1 seed now admits its partner on its own — no calcium
criterion, no one-hop-from-an-anchor rule. Literature and database rows keep the full inclusion
rule, so the wider net is exactly as wide as her spreadsheets.

Map: **117 -> 202 nodes, 255 -> 394 interactions, 466 -> 635 evidence rows**, zero curated rows
dropped (`data/supp_dropped.txt` is gone, and the build deletes it rather than leaving it stale).
Modules now fall back to the level-1 seed a node hangs from, so the ORAI1 and TRPC1 partners read
`soce` instead of nothing.

Two things the wider net exposed, both fixed:
- Six cells that are not genes (`AP-1`, `PTPN1/2`, `SAR1`, `SEC23`, `SEC24`, `SEC31`) were about
  to become nodes named after the cell. `cli.py supp` now holds those rows out of `data/raw` and
  lists them at the top of `data/supp_report.txt` — they wait for issue #18.
- The sheet's section headings (`Negative Regulators of SOCE:` and its variants) were read as
  plain binding. Mapped: 19 unreadable regulations down to 9, and the nine left are regulations of
  *another* channel (NMDA, AMPAR, Cav, ARC/CRAC) plus one `??`, where binding is the honest read.

Both pages gained an evidence-kind filter (literature / databases / curator's sheets): with 179
curated cards in the stack, reviewing source by source is the only practical way through.

**Next session:** the review stack is what matters now — 394 interactions, most of them unreviewed.
Extraction resumes at tier 1, PMID 37961129.

### 2026-10-19 — batch 3 (tier 1, 50 articles)

7 done, 43 skipped (27 reviews/commentaries/meeting reports, 16 omics screens or atlases that
list the genes without measuring them). 5 records in `data/raw/lit_20261019_b03.jsonl`, 2 new
nodes: **MCOLN1** and **PLSCR1**. Map: 203 nodes, 398 interactions, 640 evidence rows.

- **MCOLN1 (TRPML1) binds STIM1** (PMC6656764, NSC-34 mouse motor neurons): reciprocal co-IP,
  co-localization lost on TRPML1 silencing. The lysosomal Ca²⁺ channel touching the ER anchor —
  a lysosome–ER contact feeding the store that drives SOCE. `calcium_evidence = GO+text+curated`.
- **STING1 → PLSCR1 and IRF3 → PLSCR1** (PMC4320088, T80 human ovarian epithelial cells): STING
  or IRF3 knockdown ablates dsDNA-induced PLSCR1 protein. PLSCR1 is a Ca²⁺-dependent scramblase
  in the catalogue, so the STING arm reaches calcium-dependent machinery by transcription, not by
  binding. This edge exists **only because the catalogue supplies the calcium criterion**.
- **CGAS → STING1 → IRF3** (PMC4077721, human STAT1-/- fibroblasts): the canonical arm, shown
  independently of IFN/STAT1 signalling. Strengthens edges the databases already carried.

Read but nothing admissible: **MG53/TRIM72** (PMC7368064) is a real calcium brake on interferon —
it co-IPs with RyR, suppresses RyR-mediated Ca²⁺ oscillation and so suppresses IFNβ, IRF3 and
NF-κB activity — but nothing ties TRIM72 to STIM1 or STING1, so the rule drops it. Worth a second
look if a paper links MG53 to either anchor. Also read: entinostat/IFIT1-STING (PMC7244011, drug
effect on expression, no interaction of ours), SARS-CoV-2 nsp interactomics (PMC7373130, STING
only in the introduction), Nampt/Sirt6 (PMC6409323, temporal expression only).

**Convention updated** by the wider net: a claim about a partner the curator brought in (COPA,
STEEP1, VAPB, ARF1, the ORAI1 interactome) is now admissible and strengthens her edge with a
publication. The 2026-10-16 rule — do not record a STING partner with no calcium link — only
still holds for a partner that is in neither the sheets nor the catalogue.

Leads from the reviews, each pointing at a primary paper worth pulling in by PMID: **STING binds
ITPR1** to release ER calcium and trigger GSDMD pyroptosis and tissue-factor release (cited in
PMC10001161 and PMC7473058) — ITPR1 is a level-1 seed, so that edge would land on the axis
directly. And LDL traffic between lysosome and ER driving Ca²⁺ release with STING translocation
(PMC12866496).

**Next session:** tier 1 continues at PMID 32408624.
