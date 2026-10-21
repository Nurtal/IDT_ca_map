# Extraction progress

See docs/EXTRACTION_PROTOCOL.md for the session procedure.

<!-- auto:start -->
## Status (generated)

13520 articles in queue: 814 done, 12570 pending, 134 skipped, 2 error.

- tier 0: 797/3801 processed
- tier 1: 150/3812 processed
- tier 2: 3/5907 processed

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

Leads from the reviews, chased in the same session (see the next note): **STING binds ITPR1** to
release ER calcium and trigger GSDMD pyroptosis and tissue-factor release (cited in PMC10001161
and PMC7473058), and LDL traffic between lysosome and ER driving Ca²⁺ release with STING
translocation (PMC12866496).

**Next session:** tier 1 continues at PMID 32408624.

### 2026-10-19 — chasing the two review leads to their primary papers

**Lead 1 — STING–ITPR1 was already in the map, but only half of it.** The primary paper is Zhang
et al., *Cell Host Microbe* 2020, "TMEM173 Drives Lethal Coagulation in Sepsis" (PMID 32142632),
already `done` since 2026-10-16 with the STING1–ITPR1 and STING1→Ca²⁺ records. What the abstract
also states, and what was missing, is the effector half:

- **STING1 → GSDMD** and **Ca²⁺ → GSDMD** (activation): the TMEM173-dependent calcium rise drives
  GSDMD cleavage, which releases F3 and starts coagulation. GSDMD enters on the calcium term in
  that sentence. `GSDMD → F3` is not recorded: F3 touches no anchor, so the rule would drop it —
  the clinical endpoint of this arm is therefore *not* visible in the map.

PubTator has no full text for this paper (abstract only), so there is nothing more to extract from
it without the publisher's PDF.

**Lead 2 was an artefact.** The sentence in PMC12866496 is a figure legend that welds two unrelated
mechanisms together: LDL moving between lysosome and ER drives Ca²⁺ release, *and* STING
translocates to the lysosome. The primary paper behind the STING half is Gaidt et al., *Cell* 2017
(PMID 29033128, found by title — PubTator's search does not surface it, and my first guess at the
PMID was a different paper entirely). It contains **zero** occurrences of calcium or Ca²⁺: the
mechanism is potassium efflux and lysosomal cell death.

Recorded from it anyway, as a judgement call to be settled at review: **STING1 → NLRP3**
(activation). It enters only because NLRP3 is in the curator's catalogue; the record's
justification says plainly that the mechanism shown is K⁺, not calcium, so rejecting the card
costs nothing. Neither of these two PMIDs is in the work queue — the corpus searches never
surfaced them — which is the second time a lead has had to be added by hand.

Map: **205 nodes, 401 interactions, 643 evidence rows**.

### 2026-10-19 — `queue add`, and the Woo paper was never missing

New command: `python3 pipeline/cli.py queue add <PMID...> [--note TEXT]`. It pulls the article's
metadata from PubTator, puts it at the **head** of the queue — ahead of the whole corpus, because
somebody asked for it by name — and flags it `manual` so the next `corpus` run does not drop it
(a pending article absent from the searches is normally discarded). An article already in the
queue is reported, never duplicated and never reset.

Used on Gaidt et al. (PMID 29033128), added and set `done` in the same session.

Then the older lead, **Woo et al., Cell 2024** (STING–STIM1 in neurons). The 2026-10-16 note says
"PubTator search does not surface it" — that was wrong, or no longer true: resolving the DOI
(10.1016/j.cell.2024.05.031) gives PMID **38878778**, which has been sitting in the queue as
tier 2, pending, found by `@GENE_STIM1`. It was never missing, only buried 8900 articles deep.
`queue add` reported it as already present, which is exactly the check that was wanted.

Read it (abstract only, no full text in PubTator). Two records, both STIM1–STING1:

- **STIM1 binds STING1** and **STIM1 ⊣ STING1**: neuronal STING activation requires its detachment
  from STIM1, triggered by glutamate excitotoxicity. The Srikanth 2019 retention mechanism outside
  immunity, in neurons of multiple sclerosis and its mouse model, with glutamate rather than store
  depletion as the release signal. `species_context` is `unknown`: the abstract covers human MS
  tissue and a mouse model without saying which carries the detachment experiment.
- **STING1 → GPX4** (autophagic degradation, the step that causes ferroptosis) is *not* recorded:
  GPX4 has no GO calcium annotation, is not in the catalogue, and the sentence carries no calcium
  term. Second time in this session that the effector end of an arm falls outside the map, after
  `GSDMD → F3`. Worth asking the curator whether GPX4 belongs in her catalogue.

Map: 205 nodes, 401 interactions, 645 evidence rows.

### 2026-10-19 — `beyond_calcium`: the ends of the arms, tagged

The researcher's call on the two endpoints that fell outside the map: record them, and tag what is
not calcium-related. A raw record may now carry `beyond_calcium: true` — keep this claim although
it fails the calcium criterion — written by hand, record by record. Two guards: the flag only
admits what **hangs off the map** (a flagged pair with no link to a kept node stays out, so one
flag cannot drag in a disconnected cluster), and everything it lets in says so on the card.

Recorded with it:

- **GSDMD → F3** (PMID 32142632): the pyroptotic pores release tissue factor. This is what makes
  the STING-ITPR1-calcium arm lethal, and its upregulation tracks DIC severity and mortality in
  septic patients.
- **STING1 → GPX4** (PMID 38878778): autophagic degradation of GPX4 is what kills the neuron by
  ferroptosis, downstream of the glutamate-triggered detachment from STIM1.

Both arms are now complete from the anchor to the pathology.

New columns: `beyond_calcium` on interactions, `calcium_related` on nodes. The second one turned
out to say more than expected — **81 of 207 nodes are `calcium_related = false`**, nearly all of
them the STING trafficking partners the wider net brought in (COPA, STEEP1, TOLLIP, RNF5, the
exocyst, the TRIMs...). Nothing in GO, in a sentence or in the catalogue marks them as calcium.
That is the honest reading of "ratisse large", and it is now visible on every node panel instead
of being implicit.

Map: **207 nodes, 403 interactions, 647 evidence rows**. 128 Python + 33 JS tests.

### 2026-10-19 — STRING as an annotation (story 22 of the spec)

The last unimplemented story of issue #1. STRING is **never an edge source** — its scores mix
co-expression, text mining and cross-species transfers, which is exactly the noise the spec wanted
kept out — so it annotates edges the map already has. `cli.py annotate` asks STRING once for the
pairwise scores among the genes of the last build (205 genes, one request, cached in
`pipeline/cache/string/network.json`); the next `build` fills the `string_score` column, and both
pages render "STRING 0.93 (annotation, not a source)".

The score lands one build late, which is harmless in the `annotate && build` loop, and the cache is
refetched whenever the gene set changes rather than patched.

**154 of 403 interactions have a score, median 0.83** — and the absences say more than the scores:
STRING has **nothing for STIM1–STING1**, the bridge this entire map is built around. Neither for
the three other STIM1/STING1 edges. The lowest scores among our edges are CDK1–STIM1 (0.40),
ADCY6–STIM1 (0.41), SQSTM1–STING1 (0.41) and TICAM1–STING1 (0.41) — all single-source claims, so
the column is immediately useful as a sanity check at review.

Map unchanged: 207 nodes, 403 interactions, 647 evidence rows. 138 Python + 34 JS tests.

### 2026-10-19 — crossing the axis is now visible (story 7)

Story 7 asked for interactions bridging STIM1 and STING to be highlighted. Only bridge *nodes*
were marked (the `bridge` module, a node touching both anchors); the edges that cross were drawn
like any other. `CamapCore.crossesAxis` splits the two endpoints the way the corpus queries do —
the STING module on one side, anything calcium on the other — and the graph gives those edges a
halo while keeping their type colour, with a legend entry. The review card gets a
"Crosses the axis: STIM1 ↔ STING" tag.

**69 of 403 interactions cross the axis.** A metabolite counts as calcium, so STING1→Ca²⁺ is a
crossing edge, which is right: that is the cross-talk.

One imprecision, deliberate: an edge from a `bridge` node to STING1 reads as crossing, because the
node's module is not "sting". It errs toward showing cross-talk, which is what the story wants.

### 2026-10-19 — batch 4 (tier 1, the SOCE core) and `queue next --primary`

The first `queue next 50 --tier 1` of this session returned **50 reviews in a row**. The priority
order is (cross-the-axis, then primary before review), so this is the queue saying something:
**tier 1 has no axis-crossing primary research left.** What sits in front now is 240 cross reviews,
and behind them 3612 single-anchor primary articles — the best unread material, ranked last.

Rather than reorder the queue, `queue next` (and `fetch-texts --next`, `candidates --next`) take
`--primary`: articles PubMed types as reviews keep their rank, they are simply not served. One
flag, no state change, and the reviews stay reachable with the plain command.

With it, the batch is the SOCE core literature: STIM1/ORAI1 biophysics, SARAF, STIM2, TRPC1.
50 articles read, all `done`, **12 records**, 3 new nodes (**CACNA1D, ESYT1, SEPTIN4**).

- **STIM1 binds CACNA1D (Cav1.3)** and **TRPC1 ⊣ CACNA1D** (PMID 28258168, mouse substantia nigra):
  the ER sensor reaching a plasma-membrane channel other than ORAI. Losing the contact kills
  dopaminergic neurons, and restoring TRPC1 rescues them.
- **ESYT1 and SEPTIN4 → STIM1** (PMC4270102): the ER-PM junction must be tethered by E-Syt1 and
  stabilized by Septin4 before SARAF can switch STIM1 off. Recorded as `unknown_regulation`: the
  paper shows the requirement, not a direction.
- **STIM2 ⊣ STIM1** and **STIM1–STIM2 binding** (PMID 16860747, 20436167): the brake inside the
  SOCE machinery, with two independent references.
- **A conflict worth having**: SARAF ⊣ STIM1 (3 publications) now faces SARAF → STIM1
  (PMC8562847, Zomot 2021), where SARAF *licenses* initial STIM1 activation by relieving the
  inactivation domain. The build paired the two cards automatically — the first real conflict
  badge in the map, and exactly the arbitration the review app exists for.

Map: **210 nodes, 411 interactions, 660 evidence rows**.

**Next session:** `queue next 50 --tier 1 --primary` continues in the same seam.

### 2026-10-19 — batch 5 (tier 1 primary, SOCE core continued)

50 articles, all `done`, 6 records. No new node: every actor was **already in the map through the
curator's spreadsheets**, so this batch did what the updated convention predicted — it put
publications behind her rows.

- **PTK2B (Pyk2) phosphorylates STIM1 at Y361** (PMC5316956, human pulmonary artery endothelial
  cells). The phospho-defective Y361F mutant still forms puncta but fails to recruit ORAI1 — the
  cleanest separation yet between clustering and channel activation.
- **NAPA (alpha-SNAP) is required for STIM1-ORAI1 coupling** (PMC3713520), NSF-independent: the
  cluster forms without it and carries no current.
- **ATP2C2 (SPCA2) activates ORAI1** (PMID 41015040), store-independent but STIM1-dependent — a
  publication behind one of the five curated ORAI1 rows that the wider net let in.
- **CASQ1 ⊣ STIM1** and the binding behind it (PMID 27185316): calsequestrin monomers hold back
  STIM1 aggregation through residues 362-396.
- **EFHB binds STIM1** (PMID 30481768): a second EF-hand sensor on STIM1, next to SARAF.

Read and deliberately left out, all for the same reason — the partner's only neighbour is ORAI1,
which is a seed but not an anchor, so the rule drops a *literature* row:
**KCNN3 (SK3)** boosted by ORAI1 (PMC8699475), **AKAP5 (AKAP79)** assembling with ORAI1/STIM1 under
STIM2 control (PMID 32601188), and the septin screen (PMID 23792561), whose abstract names no
individual septin — the same ambiguity as the `AP-1` cell in issue #18. If ORAI1 ever becomes an
anchor, these three come in together.

Map: **210 nodes, 416 interactions, 666 evidence rows**.

### 2026-10-19 — ORAI1 and TRPC1 are anchors

Researcher's decision, closing the asymmetry the last two batches kept running into: her `Orai`
and `TRPC` rows were entering on her authority while published work on the same partners was
dropped for sitting two hops from the axis. `pipeline/config/seeds.json` now lists four anchors:
**STIM1, STING1, ORAI1, TRPC1**.

Effect on the map, before any new reading: **210 → 229 nodes, 416 → 475 interactions, 666 → 752
evidence rows**. 57 interactions now touch ORAI1 or TRPC1 as an anchor. Three papers read in
batch 5 and deliberately left out became admissible the moment the change landed, and were
recorded:

- **ORAI1 → KCNN3 (SK3)**, activation and binding (PMC8699475): calcium through ORAI1 boosts an
  SK3 potassium current that sustains the driving force for more entry — a feedback loop on the
  SOCE side, and the one that supports proliferation in breast, colon and prostate cancer cells.
- **AKAP5 (AKAP79) binds ORAI1** and **ORAI1 → NFATC2** (PMID 32601188): the scaffold that turns
  calcium entry into a transcriptional decision. STIM2 knockdown barely changes global [Ca²⁺]i but
  attenuates both the assembly and NFAT1 activation — placement matters more than quantity.

**The corpus widened with the anchors**, since the queries are built from them: `cli.py corpus`
now finds **13519 articles, up from 9104**. Tier 0 went from 192 to 3800 — anchor×anchor pairs now
include STIM1×ORAI1, STIM1×TRPC1, ORAI1×STING1, TRPC1×STING1 and ORAI1×TRPC1 — and two new
single-anchor queries appeared (`@GENE_ORAI1` 4825 hits, `@GENE_TRPC1` 3953). Statuses were
preserved: 220 done, 120 skipped, 13177 pending.

That is the real cost of the decision: the unread corpus grew by 4415 articles, and the tier-0
band — the one that gets read first — is now 3800 articles rather than 192. The yield per article
should be much higher there than in the tier-1 tail we were grinding.

**Next session:** `queue next 50 --tier 0 --primary`.

### 2026-10-19 — batch 6 (tier 0, first anchor-pair batch under four anchors)

The widened tier 0 delivers what the grind of the tier-1 tail did not: **10 records from 50
articles, 4 new nodes**, where the last two batches gave 12 and 6 with almost no new actor.

What came in, and it is all one theme — **the ER-PM junction is a built structure, and several
proteins decide whether STIM1 and ORAI1 may meet there**:

- **ASPH (junctate)** is a structural component of the junctions where ORAI1 and STIM1 cluster
  in T cells (PMID 22586105), next to E-Syt1 and Septin4 already in the map.
- **SEPTIN4** again (PMID 34601312), this time named as the isoform, acting through
  PIP2 and a CDC42-WASP/WAVE-ARP2/3 cytoskeletal route. Second independent reference.
- **KSR2 binds ORAI1 and STIM1** (PMC4038503) and holds calcineurin against the channel; without
  KSR2 the STIM1-ORAI1 association is partially lost.
- **SIGMAR1 ⊣ STIM1** (PMC4828687): sigma1R follows STIM1 to the junction and keeps it from
  engaging ORAI1 — a brake applied at the meeting point rather than on either partner.
- **TRPA1 binds STIM1 and ORAI1** (PMID 23994313): removing it *strengthens* the STIM1-ORAI1
  pairing, so it holds the complex slightly apart.
- **CALM1 ⊣ STIM1** (PMC5648805): Ca²⁺-calmodulin binds the core of activated STIM1 and takes the
  complex and the oligomers apart. The feedback that shuts the channel, now explicit in the map.
- **STIM1 → EGR1** and **ORAI1 → EGR1** (PMID 28105751, rat VSMC): a transcriptional output of
  SOCE, the arm that links the channel to the gene programme of intimal hyperplasia.

One note on method: the EGR1 records were first written with the knockdown sentence, which carries
no calcium term — the build dropped them. The paper's own summary sentence says
"STIM-1/Orai-1/Ca2+ -dependent signaling pathways", which is the same claim *and* satisfies the
criterion, so that is the quote now. Choosing which true sentence to quote changes what the rule
sees; worth remembering rather than reaching for `beyond_calcium`.

Map: **232 nodes, 483 interactions, 762 evidence rows**.

### 2026-10-19 — batch 7 (tier 0): ten records, and not one new node

50 articles, 10 records, **zero new actors** — and that is the result. Six of the proteins came
back as names the curator had already written in her STIM1 sheet: **RTN4, HOMER1, MBP (Golli),
SPPL3, ASPH (junctate), SIGMAR1** all carried `curated` evidence and nothing else before today.
TRPC6 was database-only. The batch turned her rows into published claims with a verbatim sentence
each.

- **SPPL3 binds and activates STIM1** (PMID 25384971): an intramembrane protease, found in a
  screen for NFAT activators, that is required even by constitutively active STIM1 variants.
- **HOMER1 binds STIM1 and ORAI1** in human platelets (PMID 22506990), recruited by the calcium
  signal it helps produce.
- **MBP (Golli) binds STIM1** (PMC2943750) — a myelin basic protein product on the SOCE machinery.
- **RTN4 is needed for STIM1-ORAI1 coupling** (PMID 24558039): no ER tubules, no coupling. The
  only record of the batch resting on the paper's title sentence; the body shows the SOCE loss.
- **TRPC6 binds ORAI1 and STIM1** in human platelets (PMID 19260825), switching between the
  store-operated and the non-capacitative route depending on its partner.
- **KCNN3 binds TRPC1** (PMC5094991): the SK3/TRPC1/ORAI1 lipid-raft complex of colon cancer,
  the same feedback as PMC8699475 seen as a three-channel assembly.
- **SEPTIN4 → STIM1** (PMC6658532), a third reference and the one that says what septins do:
  they set the number of ER-PM junctions, they do not recruit the channel.

**Curated rows now backed by literature: 12 of 179.** Two batches ago that number was 5. The
remaining 167 are the honest measure of how much of her sheets the corpus has not yet reached.

Map: **232 nodes, 492 interactions, 772 evidence rows**.

### 2026-10-19 — batch 8 (tier 0): the cytoskeleton and a level-2 seed finally anchored

50 articles, 7 records, 3 new nodes (**CAMK2D, HDAC6, EFCAB13**). TMEM178, FLNA and TRPC4 were
already in the map from the curator's sheets or the databases, so those records back existing rows.

- **CAMK2D → STIM1** (PMID 29669320): overexpressing CaMKIIδ increases STIM1-ORAI1 co-localization
  and SOCE. This is the first **level-2 seed** to earn its place: calcineurin, NFAT and CaMKII were
  specified in story 2 as entering only when evidence links them to an anchor, and CaMKII now has
  that link. The calcium effector feeds back on the sensor that produced the signal.
- **FLNA binds STIM1 and brakes it** (PMID 29284605, human platelets): silencing filamin A gives
  *more* STIM1-ORAI1 interaction and more SOCE, and an anti-FLNA antibody makes platelets aggregate
  harder. Where the sensor is held in the cytoskeleton decides how much of it reaches the channel.
- **HDAC6 regulates STIM1-mediated SOCE** (PMID 23698468) — and does it *differently* in cervical
  cancer cells than in normal cervical epithelium. A context dependence worth carrying.
- **TMEM178 ⊣ STIM1** (PMID 31018906): a brake on puncta formation itself, in the myeloid lineage,
  which is also where the STING arm of this map lives.
- **EFCAB13 binds ORAI1** (PMID 40972679): an EF-hand protein uncharacterized until this year,
  found in primary human platelets, with an age-dependent contribution to SOCE.
- **STIM1 binds TRPC4 and *not* TRPC1** in glomerular mesangial cells (PMID 19307462) — the
  opposite of the salivary-gland and platelet picture already in the map. Kept as a negative
  result the reviewer can weigh against the TRPC1 edges.

Curated rows backed by literature: **14 of 179**. The 55 non-verbatim sentences remain entirely
SIGNOR's (the pre-existing issue); two more appeared because admitting new nodes pulled in their
database edges.

Map: **235 nodes, 518 interactions, 803 evidence rows**.

### 2026-10-19 — the ⚠️ count was lying: 55 warnings, 5 real

Before the next batch, a data-quality fix. Every curated and literature quote verifies, but 55
evidence rows were flagged "not found verbatim" — all SIGNOR's. Reading them explains why: a
SIGNOR excerpt quotes the **full text** of the paper it cites, often two or three sentences at a
time, and PubTator frequently holds only the abstract. Looking for it there and reporting failure
is not a check, it is noise — and 55 false alarms in the review stack is how the one alarm that
matters, a paraphrased quote of our own, gets ignored.

`sentence_verified` now has four values: `true`, `false` (the alarm), **`unverifiable`** (a
database excerpt whose cited paper is cached as an abstract only) and empty (no quote). Both pages
show ⚠️ for `false` alone; `unverifiable` gets a plain grey note saying why. `cli.py build` prints
the two counts separately and lists the first ten real mismatches instead of only counting them.

Result: **223 true, 50 unverifiable, 5 false, 525 without a quote.**

The 5 survivors deserve a human glance, and two of them are an artefact of my own sentence
splitter rather than of SIGNOR: the excerpt contains "(Fig. 5d), indicating that…", the splitter
breaks after "Fig." and the fragment "5d), indicating that…" is then searched as a sentence of its
own. Each of the five has at least one sentence present verbatim in the cached full text. I chose
**not** to add a fifth status for that: a quote that does not appear as given is worth a look, and
five is a number a reviewer can actually look at.

### 2026-10-19 — the last 5 ⚠️ were formatting, not paraphrase (correcting the previous note)

The note above says two of the five remaining flags were "an artefact of my own sentence
splitter". That was wrong, and the real causes are worth recording because each one is a trap for
anyone verifying quotes against PubTator:

1. **Greek letters.** PubTator transliterates inside names — the cached text says `IKKepsilon`
   where SIGNOR says `IKKε`. `normalize()` now transliterates the Greek alphabet (and the micro
   sign, which is a different code point from mu). Two flags gone.
2. **The full stop after a title.** SIGNOR quoted the *title* of PMID 31730483 and added a period;
   PubTator's text runs the title straight into "Background". Trailing punctuation is now forgiven.
3. **`|` separators.** A SIGNOR excerpt joins several passages of the paper with a pipe.
4. **No separator at all.** The last two excerpts glued a sentence onto the next with no space,
   and in the source a section heading sits between them.

So verification now asks: **is every sentence of the quote in the text?** — not: does the whole
string match contiguously. That is a correction of the rule, not a relaxation: an invented sentence
inside a real excerpt still fails, and there is a test for exactly that.

**233 verified, 45 unverifiable, 0 flagged, 525 without a quote.** The warning channel is silent,
which is the point: the next ⚠️ that appears will be a real one.

### 2026-10-19 — batch 9 (tier 0): the junction tether family, and a conflict with the curator

50 articles, 6 records, 1 new node (**SGK1**). CAV1, ESYT2, STC2 and SLC35B1 were already in the
map from her sheets or the databases.

- **ESYT2 binds STIM1** (PMC7468131): the short isoform E-Syt2S, predominant in T cells, recruits
  STIM1 to the junctions directly. With ESYT1 and ASPH and SEPTIN4 already in, the **junction
  tethers are now a family in the map**, not an anecdote.
- **SLC35B1 (POST) binds STIM1** (PMID 22084111): store depletion makes the STIM1-POST complex
  bind SERCAs, PMCAs, the Na/K-ATPase and the nuclear transporters. STIM1 does more on depletion
  than open ORAI1.
- **CAV1 → ORAI1** (PMID 25645930): caveolin-1 interacts with the STIM1-ORAI1 complex and raises
  channel activity — the protein that makes the lipid raft a better place for the channel.
- **SGK1 regulates ORAI1** (PMID 21385992), linking the growth-factor kinase to the entry that
  sustains proliferation.
- **STIM1 → NFATC2 expression** (PMID 37399784): in breast cancer cells STIM1 sets NFAT1
  *expression* and migration **independently of SOCE and of ORAI1**. An arm of the axis that does
  not pass through calcium at all — worth knowing in a map built on the calcium criterion.

**A conflict with the curator's own sheet, and it is a real one.** Her row says STC2 *inhibits*
STIM1; PMC5876523 shows platelets from STC2-/- mice with an *attenuated* STIM1-ORAI1 interaction,
i.e. STC2 *required* for it. The paper itself cites the other direction (Zeiger: STC2
overexpression reduces SOCE), which is what her row records. The build paired the two cards
automatically. Conflicting pairs now in the map: **SARAF/STIM1, STC2/STIM1, TRIM56/STING1**, plus
seven pairs that come from databases disagreeing with each other.

Not recorded, for want of a subject: PMC10406432 shows IP3 receptors are required for neuronal
SOCE even when they cannot release Ca²⁺ — but it says "IP3Rs", and ITPR1, ITPR2 and ITPR3 are
three separate seeds. The same ambiguity as `AP-1` and `septins`.

Map: **236 nodes, 524 interactions, 809 evidence rows**.

## 2026-10-19 — Extraction batch 10 (tier 0, `--primary`)

50 articles, **15 records** in `data/raw/lit_20261019_b14.jsonl`, **4 new nodes** (TPCN2, NFAT5,
PTGS2, IL6). Most of this batch is STIM1-ORAI1 structure-function — pore mutants, SOAR/CAD
geometry, gating checkpoints, CRAC inhibitors — which the map already holds as a single edge, so
the records come from the margins of the batch rather than its centre.

**Six records exist to put a publication under one of the curator's rows**, which had the
interaction but no reference: **BIN2** (PMID 32750041, the BAR-domain protein binding STIM1 and
IP3R in platelets), **PGRMC1** (PMID 35045297, binds the STIM1 coiled-coil and promotes the
conformational switch), **JPH1** ×2 (PMID 20937810, junctophilin-1 knockout myotubes lose STIM1
and ORAI1 protein), **TRPC5** and **TRPC1** (PMID 17486119, STIM1 binds TRPC1/4/5), **PRKCB**
(PMID 20534587, PKC phosphorylates ORAI1 at Ser-27/Ser-30 and suppresses SOCE).

**Measured coverage.** Curated *pairs* with a publication on the same pair: **31 of 174**. The
narrower count — a curated interaction *row* whose own id carries a publication — is only
**15 of 179**, because the type we read in the paper often differs from the type in her sheet
(she has BIN2 → STIM1 as `activation`, the paper shows `physical_binding`). The pair-level number
is the honest one; the row-level number undercounts and should not be read as a regression.

**A disagreement recorded on purpose.** PMID 17486119 says STIM1 **does not** bind TRPC3 or TRPC6
and reaches them only by pairing TRPC3 with TRPC1 and TRPC6 with TRPC4; PMID 23068106 finds the
**STIM1L** splice variant binding TRPC3 and TRPC6 directly. Both are in, each with the other named
in its `mechanism`. Likewise PMID 17486119 (STIM1 binds TRPC1) sits next to PMID 19307462 from
batch 7 (STIM1 binds TRPC4 *but not* TRPC1). `link_conflicts` does not pair these, because it
compares the sign of a regulation and both are bindings — a gap worth knowing.

**New arms.** **TPCN2 → STIM1 inhibition** (PMID 42386717, 2026): calcium released by the lysosomal
two-pore channel enforces calmodulin-dependent STIM1 inactivation — the second lysosomal entry
point into this map. **ORAI1 → PTGS2** and **ORAI1 → IL6** (PMC9180186): the same channel writes
two different gene programmes, PTGS2 with full stores and IL6 after thapsigargin, via NFAT1.
**STIM1 → ITPR3 expression** (PMC7555297): STIM1 knockout cuts ITPR3 and with it mitochondrial
calcium, respiration and ATP. **NFAT5 → ORAI1 expression** (PMC6997179): phosphate →
NFAT5 → SGK1 → ORAI1, which gives last batch's SGK1 its upstream.

**The verifier lost one more class of false alarm.** Two new ⚠️ appeared with PTGS2 (SIGNOR-264025/6
quote `incancer cells` where the paper reads "in cancer cells"). `sentence_in` now retries with all
whitespace removed on both sides — it forgives a lost word boundary and nothing else, since every
character of the quote must still appear in order. Red test first, plus one asserting an altered
sentence still fails. **0 flagged, 46 unverifiable.**

Not recorded, for want of a subject: PMID 35853265 shows lipid transfer proteins controlling SOCE
through PM phosphoinositides, but names only "ORPs" generically — the fourth time this ambiguity
has blocked a record, after `AP-1`, `septins` and `IP3Rs`. PMID 32916960's claim that STIM1 binds
CaV1.2 is background cited to others; the pair is already in the map from the curator's sheet.

Map: **241 nodes, 541 interactions, 829 evidence rows**. Tests: **153 Python + 36 JS**.

**Next session:** `queue next 50 --tier 0 --primary`.

## 2026-10-19 — Extraction batch 11 (tier 0, `--primary`)

50 articles, **18 records** in `data/raw/lit_20261019_b15.jsonl`, **9 new nodes** (RHOA, NOS1,
RACK1, FOS, TNF, CDK2, CCT2, CCT5, TMEM97). All 18 sentences verified `true`.

**A second non-calcium arm of STIM1, flagged as such.** PMID 23512989: in endothelium the
thrombin-induced loss of barrier function requires STIM1 but **neither Ca²⁺ entry nor ORAI1** —
STIM1 couples the thrombin receptor to **RhoA**, myosin light chain phosphorylation and stress
fibres. Recorded with `beyond_calcium: true`, next to STIM1 → NFATC2 expression from batch 9.
The map now holds three `beyond_calcium` edges: STING1 → GPX4, GSDMD → F3, STIM1 → RHOA.

**The isoform ambiguity answered, twice.** PMID 20022948 names **type I and type II** IP3
receptors rather than writing "IP3Rs": ORAI1 associates with both on stimulation, and silencing
TRPC3 abolishes the ITPR1 contact but not the ITPR2 one. The same complex brings in **RACK1** and
**TRPC3** on ORAI1. PMC6157965 likewise names **CCT1 (TCP1), CCT2 and CCT5** instead of leaving
the chaperonin generic, so the complex enters as proteins: the contact is on the ORAI1
intracellular loop, and knocking down either CCT1 or CCT2 raises ORAI1 at the plasma membrane
without changing its total level. How much channel is at the surface is itself regulated.

**Four records had to be requoted** before they survived the inclusion rule: the subunit-level
co-immunoprecipitation sentences carry no calcium term, so CCT2, CCT5 and RACK1 were being
dropped although the paper is about calcium signalling. Requoted with each paper's own
calcium-bearing conclusion, with the co-IP left in `mechanism` — the same fix as EGR1 (batch 6)
and SLC35B1 (batch 9). **This is now the commonest reason a good record fails: the evidence
sentence and the calcium sentence are different sentences.**

**Other arms.** **NOS1 → STIM1 inhibition** (PMID 29705071): S-nitrosylation at Cys49/Cys56, with
a double-mutant control — a redox brake in the sarcoplasmic reticulum of cardiomyocytes.
**TMEM97 (sigma 2 receptor) binds STIM1 and not ORAI1** (PMC7072710), beside SIGMAR1 from batch 7:
both sigma receptors act on the sensor. **STIM2 → ORAI1 inhibition** (PMID 38537434): the two
STIM2 splice variants have opposite signs, STIM2.1 suppressing and STIM2.2 enhancing SOCE, which
is why STIM2 knockdown can *increase* SOCE. **ORAI1 → TRPC4** (PMID 22534489): ORAI1 as a subunit
that decides whether a TRPC1/4 channel is calcium-selective. **STIM1 → CDK2** (PMC4768259),
**ORAI1 → FOS** (PMC6555828, two transcription factors needing different numbers of STIM1-ORAI1
clusters), **STIM1/ORAI1 → TNF** (PMID 33713955, endothelium in sepsis).

**A question for the curator, and a concrete one.** `PPP3CA` is in her seed list but is **not in
the map**: it is a level-2 seed and needs a link to an anchor, and the papers that would give it
one — PMC5833430 (caerulein → STIM1-ORAI1 → calcineurin → NFAT/TFEB), PMC4038503 (the KSR2-
calcineurin complex on the channel) — write "calcineurin", not an isoform. Same shape as `IP3Rs`,
`AP-1`, `septins`, `ORPs` and now "NF-κB" (PMID 33713955 shows forced NF-κB expression inducing
STIM1 — a cross-axis link we cannot record for want of a subunit). A single convention from her
would unblock six records at once.

Map: **249 nodes, 571 interactions, 862 evidence rows**. Tests: **153 Python + 36 JS**.

**Next session:** `queue next 50 --tier 0 --primary`.

### 2026-10-20 — Extraction batch 12 (tier 0, `--primary`)
50 tier-0 primary articles (49 done, 1 skipped as a commentary), **20 records** in
`data/raw/lit_20261020_b16.jsonl`, **1 new node** (DYRK2). All 20 sentences verified `true`;
0 flagged, 46 unverifiable.

**The yield of this band is dropping, and for a readable reason.** Deep in tier 0 the queue is
now dominated by STIM1-ORAI1 biophysics: pore mutants, concatemers, hydrophobic gates,
2-APB pharmacology, stoichiometry. Those papers say a great deal about *how* the two anchors
couple and nothing about *who else* is involved, so they are read and marked `done` with no
record. 38 of the 50 ended that way. The records came from the twelve papers that brought a
third actor in.

**Abundance as an edge type, between the two anchors themselves.** PMC11730744 (Nieto-Felipe
2024) shows STIM1 and STIM2 driving ORAI1 to **endo-lysosomal degradation**: bafilomycin A1
rescues the protein, and the pore-dead ORAI1-E106Q is degraded just as much, so the loss is not
a consequence of Ca2+ influx. The reciprocal arm exists too — the Orai1 variants set the STIM1
protein level and leave STIM2 alone — recorded as `unknown_regulation` because that sentence
gives no sign. The same paper gives **STIM2-ORAI1 binding at rest**, before any store depletion,
which is what a basal Ca2+ thermostat needs.

**Publications under the curator's rows, again the highest-yield vein.** Her JPH1 row carries
the note "STIM1 and JPH4 colocolize" with nothing behind it: PMID 26929330 shows JPH4 *binding*
STIM1 through its cytoplasmic domain and recruiting it into the junction, with junctate. Her
SARAF row names "TMEM 66" as the synonym and gives SARAF → ORAI1 inhibition with no publication:
PMID 31173198 supplies one, in a rat carotid artery, and adds a second mode — SARAF holds down
how much STIM1 and ORAI1 the cell *makes*, not only whether the channel is open. HGNC previous
symbols resolve TMEM66 → SARAF, so the paper's own name could be kept in the record.
Her STIM1-VIM row was a BioID proteomics hit with no function: PMID 31243341 makes vimentin a
transcriptional output of the channel, and splits it — EGTA-AM and thapsigargin need ORAI1,
cytochalasin D needs STIM1 and **TRPC1** but not ORAI1. Same gene, two channels, stimulus
decides.

**A loop closed.** SIGNOR already had PRKAA1 phosphorylating STIM1 at Ser257 and down-regulating
it; PMID 25242372 shows STIM1-dependent SOCE *activating* AMPK (Thr172, through CaMKKbeta) and
with it glucose uptake. Recorded as PRKAA1 because that subunit already stands for AMPK in the
map — but the paper only ever writes "AMPK", so this is the generic-name convention of issue #18
being applied rather than answered. Noted here so it can be revisited with her reply.

**Other arms.** **DYRK2 → STIM1 phosphorylation** (PMC9113749): a kinase that sets the *strength
of the STIM1-ORAI1 coupling* itself, with a non-phosphorylatable STIM1-10M and a kinase-dead
control. **ORAI1 → TRPC5 activation** (PMID 19815560): no protein contact at all — the message is
the Ca2+ ion, over a distance the buffer sets (EGTA permits it, BAPTA abolishes it).
**ORAI1-ITPR3 binding** in primary pancreatic acinar cells (PMC3262233), the third IP3 receptor
after ITPR1 and ITPR2 in batch 11, plus the lesson that one anchor can hold two spatially
separate pools with different partners. **TRPC1-ITPR2 binding** (PMID 16870612), a second paper
naming "type II" instead of "IP3Rs" — ITPR2 now carries both ORAI1 and TRPC1, which argues
against collapsing the IP3 receptors into one node. **NFAT5 → ORAI1 and → STIM1**
(PMID 28446591): an independent second paper for the batch-10 NFAT5 → ORAI1 edge, in
megakaryocytes, with the silencing half, and it extends NFAT5 to the sensor.

**Generic names blocking records, now eight.** `ERK1/2` (PMID 20736304, ERK1/2 phosphorylates
STIM1 and the mutants lose ORAI1 FRET — and PMID 34715400 is its published contradiction, so the
pair would have entered the map as a conflict), `Akt/mTOR/NF-kappaB` (PMID 32882268, ORAI1/ORAI2
silencing), and `NFAT` (PMC3480383, where ORAI1 drives NFAT and TRPC1 drives NF-kappaB from the
same store depletion — a result the map cannot hold without a subunit). These join calcineurine,
IP3Rs, AP-1, septins and ORPs on the issue #18 list.

**Leads worth a `queue add` once their PMIDs are known**: the KDM2B paper behind
PMID 38903530's "ORAI1 and STIM1 expression was controlled by KDM2B"; the Pyk2 paper behind
PMID 37739164's STIM1 Tyr361 phosphorylation; Gudlur et al., Nat Commun 9:4536, the paper
PMID 30528613 comments on (five more Ca2+ sites in the STIM1 luminal domain).

Map: **250 nodes, 590 interactions, 884 evidence rows**. Tests: **153 Python + 36 JS**.

**Next session:** `queue next 50 --tier 0 --primary`.

### 2026-10-20 — Extraction batch 13 (tier 0, `--primary`)
50 tier-0 primary articles (46 done, 4 skipped as commentaries/reviews) plus **2 leads chased to
their primary papers**, **23 records** in `data/raw/lit_20261020_b17.jsonl`, **6 new nodes**
(ATP2A2 already present; CFTR, PIK3R1, MTOR, ITGAL, CXCL8, KDM2B are new). All 23 sentences
verified `true`; 0 flagged, 46 unverifiable.

**Two literature conflicts now carry a badge, both deliberate.**
`STIM1 → PRKAA1`: batch 12 recorded activation (PMID 25242372, STIM1 siRNA cuts AMPK
phosphorylation at Thr172 through CaMKKbeta in neuroblastoma); this batch records inhibition
(PMID 25917875, losing SOCE to resveratrol causes ER stress that *activates* AMPK in prostate
cancer cells). `ORAI3 → ORAI1`: inhibition in store-operated entry (PMC7968378, the ORAI2,3
double knockout raises the fraction of cells reaching a Ca2+ plateau from 16% to ~70%) and
activation in the store-independent ARC current (PMID 17991693, ORAI3 raises ARC only in cells
expressing ORAI1, and a dominant-negative ORAI3 kills ARC without touching CRAC). In both cases
the two mechanisms are in the records, so the badge points at a real context difference rather
than at a contradiction to be resolved.

**The STIM-IP3R question, and why the convention on issue #18 now blocks a conflict.**
PMC4266619 shows STIM1 and STIM2 co-immunoprecipitating with **IP3R-1** by isoform-specific
antibody, and STIM1 knockdown — not STIM2 — cutting IP3R-dependent Ca2+ release without touching
ER content: a *positive* regulation, recorded. PMC7968378 reports the opposite, that the
unactivated STIM1/2 luminal domains *inhibit* IP3R-evoked release — but it works in IP3R
triple-knockout cells and never names an isoform, so **the claim cannot be entered and the
conflict cannot be shown**. Chasing the commentary PMID 40828111 to its primary paper
(PMID 40719699, added with `queue add`) reframed rather than settled it: the crosstalk there is
functional, through resting ER Ca2+ level, and the co-immunoprecipitation shows **no interaction
between STIM1 and IP3R2 or IP3R3**. Taken with PMC4266619 and with PMID 20022948 from batch 11
(ORAI1 holds ITPR1 and ITPR2 with *different* TRPC3 dependence), the IP3 receptors behave like
three different proteins. That is the concrete argument for option 3 on #18 — leave `IP3Rs`
unrecorded rather than fan out or pick a representative.

**New arms.** **STIM1 → CACNA1C inhibition** *and* STIM1-CACNA1C binding (PMID 20929813): one
sensor suppressing the voltage-gated channel while activating ORAI, both through the same SOAR
region, in one ER-PM junction that contains all three proteins. **ATP2A2 (SERCA2a) → STIM1
inhibition** (PMID 21195084): keep the store full and STIM1 never meets ORAI1 — the pump as an
upstream regulator of the sensor, with the smooth-muscle phenotypic switch as the readout.
**CFTR → ORAI1 inhibition** and **ORAI1 → IL8 up** (PMID 21873556): in DeltaF508 cystic fibrosis
epithelia, ORAI1 insertion into the membrane doubles and IL-8 secretion follows; rescuing CFTR
trafficking normalises it. **KDM2B → ORAI1 and → STIM1** (PMID 38817821, the lead from batch 12):
a histone demethylase upstream of both anchors. **STIM1/ORAI1 → ITGAL** (PMC12849750): CD11a but
not CD11b, E-selectin and CXCL-1 but not P-selectin, and kidney function preserved after
ischaemia-reperfusion when neutrophils lack them. **STIM1 → MTOR** (PMID 25917875),
**TRPC1-PIK3R1** (PMC9563726, only after acid adaptation), **PDGFRB → ORAI1** (PMID 20107038,
by elimination among six channels), **STIM1-ORAI2 / STIM1-ORAI3 binding** stronger at rest than
STIM1-ORAI1 (PMC7968378), **STIM2-ORAI2** as the working pair in dendritic cells (PMID 20971921),
**ORAI1-TRPC1 clustering** by immunogold electron microscopy (PMC10025536, which also contradicts
the model that ORAI1-mediated entry recruits TRPC1 to the membrane).

**One new class of verification false alarm, fixed.** MTOR entering the map pulled in
SIGNOR-278237, whose excerpt keeps the publisher's reference marker (`... catalytic activity of
mTOR [216].`) where the cached text ends the sentence at `mTOR.`. `normalize` now strips numeric
reference markers (`[216]`, `[12,13]`, `[4-7]`) from both sides, red test first; an altered
sentence still fails. Back to 0 flagged.

**Generic names still blocking records**: `IP3Rs` (above), `Rap1` (PMC12849750: STIM1/ORAI1 →
Rap1 activation, upstream of the integrin arm we did record), `NF-kappaB` (PMID 36334371, where
STIM1/ORAI1 overexpression activates it and beta-carotene switches it off), `calmodulin`
(PMC9563726, the third member of the TRPC1-PI3K complex), plus calcineurine, AP-1, septins,
ORPs, ERK1/2, Akt/mTOR, NFAT and AMPK from earlier batches.

Map: **256 nodes, 619 interactions, 938 evidence rows**. Tests: **155 Python + 36 JS**.

**Next session:** `queue next 50 --tier 0 --primary`.

## 2026-10-21 — Extraction batch 14 (tier 0, `--primary`)

`queue next 50 --tier 0 --primary`, read one by one, plus one lead chased to its primary paper.
**40 records** in `data/raw/lit_20261021_b18.jsonl`, all 40 sentences verified `true`, zero
flagged. Two articles marked `skipped` (PMID 22111611, a review of ORAI pharmacology; PMID
30217863, a JGP commentary on Orai1 gating stoichiometry); the other 48 `done`. The deep tier-0
pattern of batches 12 and 13 holds: about two thirds of the batch is STIM1-ORAI1 biophysics or a
knockdown phenotype with no third named actor — read, marked `done`, no record.

**The lead.** Bhardwaj 2013 (PMC3814058, this batch) mentions in passing that "CRACR2A regulates
the interaction of STIM1 and Orai1". Chased by esearch to **PMID 20418871 / PMC2875865**
(Srikanth 2010), already in the queue, cached in full. It yields six records: CRACR2A binds
**ORAI1** (direct, GST pulldown, Orai1 N-terminal residues 64-93, abolished in 2 mM Ca2+, lost in
the Orai1 K85A/K87A mutant) and **STIM1** (coiled-coil and PEST domains, not the S/T-rich region
that binds ORAI1), so one protein bridges the pair instead of competing with it; it also
co-precipitates **ORAI2** and **ORAI3**. Functionally CRACR2A depletion cuts SOCE by half in
Jurkat T cells and stops ORAI1 and STIM1 clustering, and the paralogue **CRACR2B** fills the same
slot in HEK293 cells — the isoform-swap pattern again (ORAI1/2/3, STIM1/2, IP3R1/2/3).

**New arms.** **BCL2 → STIM1 / ORAI1 / ORAI2 expression down** (PMC5841437): wild-type Bcl-2
lowers all three and reduces SOCE, the BH1 alpha5-helix mutant (144WGR146→AAA) does the opposite;
note the paper's own next sentence writes "Bcl-2 increased ..." where the figure shows the mutant,
so only the WT sentence is recorded. **ORAI1 → MYOZ2 and → RCAN1 up** (PMC7290784): named
calcineurin regulators under ORAI1 in the angiotensin-II-treated heart, with `Ppp3ca` itself
unchanged — the closest the map can get to ORAI1 → calcineurin while the isoform convention is
open. Same paper: **ORAI1 → STIM1 and → ORAI3 expression up**, the stress-evoked induction of the
sensor needing the channel. **STIM1 → CAPN1 activation** (PMID 18337467), substrate stiffness as
the input and apoptosis of normal epithelium as the output. **STIM1-PRDX4 binding** (PMID
29804005), on endogenous protein in rat rough ER; Prx-4 does not set the size of SOCE, it
protects it from H2O2. **STIM1/ORAI1 → PRKCA** (PMC6322368, ventilator-induced lung injury, the
isoform written out). **STIM1/ORAI1 → RHOA, flagged `beyond_calcium`** (PMC6267368): in DLBCL the
migration arm survives EGTA, BAPTA-AM and BTP2, so the anchors act here as scaffolding effectors
coupling CXCR4 to RhoA/ROCK — a Ca2+-independent function of a calcium anchor, which is what the
flag is for. **CXCL12 → ORAI1 / STIM1** from the same paper, a physiological agonist upstream for
once. **TMEM97 → ORAI1** (PMID 33618021), through the cholesterol bound to the channel.
**STIM1/ORAI1 → IL8** (PMID 25190815, histamine, HUVEC) — independent support for the ORAI1 → IL8
arm of batch 13 in another tissue. **TRPC1 → ADIPOQ, → VAMP2, → SNAP25** (PMC6633397): an
exocytosis arm, insulin-stimulated, with body composition as the whole-animal readout.
**STIM1 → NFE2L2 and → EIF2AK3 inhibition** (PMID 23076152): losing STIM1 drives NRF2 into the
nucleus via PERK/eIF2alpha, the first link from an anchor to the antioxidant response.
**EDN1 → TRPC1 up** and **STIM1 → TRPC1/TRPC3/TRPC4/TRPC6 up** (PMC5690472, pressure overload):
STIM1 sets how much partner channel there is, not only when it opens. **F2RL3 (PAR4) → ORAI1**
(PMID 29677491), the allergen protease Der p3 input, PAR4 discriminated from PAR2 by experiment.
**STIM1-ORAI1 binding** under LPS and mitochondrial ROS in rat cardiomyocytes (PMC7674615).

**Generic names still blocking records**: `MLC2` and `ROCK` (PMC6267368, the two steps between
RHOA and actin), `syntaxin 1` (PMC6633397, the third SNARE — STX1A or STX1B is not said),
`NF-kappaB` again (PMC4530453, where STIM1/ORAI1 overexpression *inhibits* it, the opposite sign
to PMID 36334371), `L-type Ca2+ channels` (PMID 24720513), plus `IP3Rs`, `Rap1`, `calmodulin`,
calcineurine, AP-1, septins, ORPs, ERK1/2, Akt/mTOR, NFAT and AMPK from earlier batches.

Map: **270 nodes, 658 interactions, 982 evidence rows**. Tests: **155 Python + 36 JS**.

**Next session:** `queue next 50 --tier 0 --primary`.

## 2026-10-21 — Extraction batch 15 (tier 0, `--primary`)

`queue next 50 --tier 0 --primary`, read one at a time, plus **three leads chased** to their
primary papers. **53 records** in `data/raw/lit_20261021_b19.jsonl`, all 53 sentences verified
`true`, zero flagged. One article `skipped` (PMID 30217863 was a JGP commentary; PMID 29581306
was *not* a commentary, it was mis-marked and corrected to `done`). Map: **285 nodes, 754
interactions, 1110 evidence rows**; 20 new nodes, among them four of the curator's own rows that
had no literature edge until now (SGK1, PRKCB, TMEM38A, NOTCH1, PLN).

**Three generic names resolved by the articles themselves — this is the best batch yet for
issue #18.**
- `ORPs` → **ORP5 and ORP8** (PMC10469337). The family was blocked, and the reason is now
  demonstrated: in the same cells, in the same experiment, **OSBPL5 inhibits and OSBPL8
  facilitates** STIM1 clustering, STIM1-ORAI1 interaction and the ORAI1 current. Collapsing the
  family into one node would have cancelled the biology out.
- `CaMKII` → **CaMKIIalpha** (PMC8536888). STIM1 and ORAI1 drive CAMK2A phosphorylation in the
  rat spinal dorsal horn, and YM-58483 suppresses it without changing anchor expression. CAMK2A
  is a level-2 seed of the curator's effector module and had no literature edge; it now has one,
  and it arrives with its database neighbourhood (CAMK2A-DLG1, -EGFR, -NOS1 conflicts appeared in
  the build as a consequence).
- `NF-kappaB` → **p65/RELA**, in the upstream direction (PMID 22110130, replicated in PMID
  24522202). Both papers transfect named subunits (p65, p65/p50, p65/p52) and the first one ChIPs
  the Orai1 and STIM1 promoters. So the map can now draw **SGK1 -> RELA -> ORAI1/STIM1** with
  named proteins, plus **KL (klotho) -> ... -> anchors** through 1,25(OH)2 vitamin D3, with
  thrombus formation as the whole-animal read-out. The *downstream* direction is still a problem:
  PMID 35094865 (dairy cows) names phospho-p65 and was recorded, but it is in vivo co-regulation
  without a loss-of-function control, so the sign conflict between PMC4530453 and PMID 36334371
  remains unshowable.

**Two generic names resolved by me, flagged as such in the records and on #18**: `LTCC` →
**CACNA1C** in ventricular myocytes (PMID 26241845) and `DHPR` → **CACNA1S** in skeletal myotubes
(PMC6915709). The first one matters because it creates a conflict badge: **STIM1 -> CACNA1C is
now activation in cardiac muscle and inhibition in smooth muscle/HEK (PMID 20929813, batch 13)**.
A badge resting on my own name resolution is worth the curator's attention.

**A conflict that is pure biology.** PMC12830608: the active Notch1 intracellular domain
**lowers** ORAI1 and ORAI3 in MDA-MB-231 and **raises** them in BT20 - same construct, same
subtype, different cell line - and leaves them alone in MCF10A while lowering STIM1 there. Both
signs come from one paper, so the badge points at context, not at a disagreement between
laboratories. The mechanism is **HEY1**, a repressor switched off by phosphorylation at Ser-68.

**The leads.** PMC10592933 mentions in passing that "STIM1 binds to phospholamban ... to
indirectly activate SERCA2" and PMC6915709 that "STIM2 attenuates SERCA1a activity ... in a tug
of war with STIM1". Chased by esearch to **PMID 26261328** (rat ventricular myocytes: STIM1-PLN
binding, STIM1 -> ATP2A2 activation, in cells with *no* SOCE at all), **PMID 24077737** (STIM1
binds SERCA1a through residues 449-671 and is required for its full activity at micromolar
cytosolic Ca2+) and **PMC5738411** (STIM2 binds SERCA1a through the homologous region 453-729 and
*attenuates* it). Two homologous sensors, the same pump, the same binding region, opposite signs.
Batch 13 had ATP2A2 -> STIM1 inhibition; the loop is now closed in both directions.

**Other arms.** ORAI1-**KCNMA1** binding, reduced in diabetic mice although ORAI1 protein is
raised (PMC8564290) - Ca2+ entry read straight into membrane potential. **DLG1 (SAP97) -> ORAI1
trafficking** (PMC8583858): knocking it down leaves SOCE intact and changes only the *shape* of
the T cell Ca2+ response, which no other record in the map does. **TMEM38A (TRIC-A)** gets
between the anchors and lowers ICRAC, the mirror image of CRACR2A from batch 14. **PRKCB ->
STIM1 phosphorylation at Ser660**, and the sign is inhibition, against the grain of the other
kinases reported on STIM1. **F2RL1 (PAR2) -> ORAI1/STIM1** (PMC10105462, blastocyst proteases),
which completes the contrast with F2RL3 (PAR4) from batch 14, where PAR2 was explicitly *not* the
coupled receptor. **LEP -> ORAI1** in dendritic cells, **PGF -> ORAI1/STIM1 -> HIF1A** in ovarian
carcinoma, **PLA2G6 -> ORAI1** (visible only at endogenous expression - overexpressing either
anchor hides the requirement), **STIM1 -> RYR2 activation** in cardiac muscle against **STIM1 ->
RYR1 inhibition** in skeletal muscle, and **STIM2 -> EIF2AK3 inhibition** (PMC10592933), where
losing STIM2 activates PERK and losing STIM1 does not - PERK now has both sensors on it with the
same sign from two unrelated papers (the STIM1 one is PMID 23076152, batch 14).

**Two records dropped by the inclusion rule, both worth reporting rather than hiding.**
`JAK2 -> ORAI1` (PMID 30054044), the kinase between leptin and the channel: no sentence in the
paper names Jak2 together with a calcium term, and JAK2 has no GO calcium annotation, so the node
was not admitted and the record was deleted. `STIM2 -> MYC` and `STIM2 -> ATF4` (PMC10592933)
fail a different rule: they are two hops from an anchor, since STIM2 is a seed and not an anchor.
The PERK edge survived only because EIF2AK3 was already admitted under STIM1.

**Generic names still blocking records**: `IP3R` again (PMC6125598, a whole paper on the
IP3R-STIM1 association and the intraluminal microdomain, no isoform anywhere), `MLC2`, `ROCK`,
`syntaxin 1`, `L-type Ca2+ channels` outside the two tissues resolved above, `KCa channels`
(PMID 41344216), `ClCa`/TMEM16A as a "probable candidate" only (PMID 20204722), plus `Rap1`,
`calmodulin`, calcineurine, AP-1, septins, ERK1/2, Akt/mTOR, NFAT and AMPK from earlier batches.

A negative claim worth remembering: **PMID 19332491 says TRPC channels function independently of
STIM1 and Orai1** in HEK293 and vascular smooth muscle, which contradicts several STIM1-TRPC1
records in the map. The schema has no way to record a negative, so it lives here.

Map: **285 nodes, 754 interactions, 1110 evidence rows**. Tests: **155 Python + 36 JS**.

**Next session:** `queue next 50 --tier 0 --primary`.

## 2026-10-21 — Extraction batch 16 (tier 0, `--primary`)

`queue next 50 --tier 0 --primary`, read one at a time, plus two leads chased. **64 records** in
`data/raw/lit_20261021_b20.jsonl`, all 64 sentences verified `true`, zero flagged. Three articles
`skipped` (PMID 31010205 and PMID 36809524 are expression-profiling/bioinformatic screens, PMID
40522762 a review). Map: **305 nodes, 814 interactions, 1184 evidence rows**; 21 new nodes, and a
striking number of the curator's own rows finally get a publication under them: TRPC6, TRPC5,
PAK1, SRC, PTGS2, IL6, TNF, GRIN2A, GRIN2B, NFATC2, MTOR.

**`NFAT` is unblocked, by two papers in the same batch.** PMC6716836 writes **NFAT1** (= NFATC2)
and shows STIM2, but not STIM1, controlling its expression and its occupancy of the TGF-beta1
promoter; PMC10641176 writes NFAT1 too and shows STIM1 and STIM2 knock-outs each reducing its
nuclear translocation, with the double knock-out abolishing it. The second one is what admits
NFATC2 to the map at all, since a level-2 seed has to touch an **anchor** and STIM2 is not one.
TGFB1 itself is *not* recorded: it hangs off NFATC2, two hops from an anchor.

**`CaMKII` and `calmodulin` again, with a result.** CAMKK2 (CaMKKbeta) enters from PMID 41765055
and closes a gap left open since batch 12: STIM1 -> PRKAA1 was recorded *through CaMKKbeta* and
the kinase had no node. The same paper reports an **ORAI1-p65 co-immunoprecipitation** - the only
named-subunit physical link between an anchor and NF-kappaB the map has seen - recorded with its
weakness stated (one pull-down, in tissue, no reciprocal). `calmodulin` stays blocked: PMID
23109337 is a crystal structure of the ORAI1 CMBD with Ca2+-CaM and never says which CALM gene.
`NFAT` in PMC9011325 also stays blocked, because there the isoform appears only in an antibody
catalogue number and a construct name - the same evidence I refused for IP3R1/2/3 in batch 13.

**Three feedback loops now close in the map**, each with the two arrows from different papers:
**STIM1 <-> SRC** (PMC4242838: the anchors activate Src at invadopodia; PMID 28866365: STIM1 is a
*downstream* target of Src-Raf-MEK-ERK, and that paper's whole point is that the direction has
been assumed backwards), **STIM1 <-> MTOR** (batch 13 for the forward arrow; PMC9153009 shows
rapamycin lowering STIM1 and ORAI1 in vivo), and **STIM1 <-> PLA2G6** (batch 15: the lipase is
required for endogenous SOCE; PMID 22223729: STIM1 but not ORAI1 is required to activate the
lipase, and its product then acts on ORAI1 but not STIM1).

**New arms.** **TRPC6 binds ORAI1 and ORAI3** and is required for their surface delivery, with
the partner swapping between MDA-MB-231 and MCF7 (PMC6162527) - a trafficking edge beside DLG1
from batch 15. **TRPC5 in a stoichiometric complex with STIM1 and ORAI1**, argued from Sr2+
permeability (PMID 18250430). **PAK1** binds and activates STIM1 (PMC5960643), pushing it the
opposite way to PRKCB from batch 15. **STIM1/STIM2 bind GRIN2A and GRIN2B** as endogenous
proteins in cortical neurons and *restrain* NMDA-evoked Ca2+ (PMC7017226): STIM1-NR2A association
rises on store depletion while STIM1-NR2B falls, and STIM1 displaces STIM2 from NR2A. **AVP ->
ORAI1/STIM1 -> RUNX2, MSX2, SOX9, ALPL** (PMID 33409552): a whole osteogenic programme under the
channel, ending in vascular calcification. **COL6A1 -> STIM1/ORAI1** through mTOR, in mice and in
Bethlem/Ullrich patients' platelets. **VPS13A (chorein) -> ORAI1/STIM1**, a neurodegeneration
gene whose loss *lowers* both anchors, reversed by lithium through NF-kappaB. **GNB5 -> STIM1**
(needs the STIM1 ERM region, not a conducting ORAI1), **MFN2 -> STIM1 trafficking** (mitochondrial
depolarization blocks the sensor's migration), **NEUROD2 -| STIM1** with a ChIP-seq'd intronic
binding site (lead chased to PMC5343279), **STIM1/ORAI1 -> MMP14 recycling** and **-> SRC** at
invadopodia, **-> KRT1** in keratinocytes, **-> KDR** in thyroid cancer, **-> IL2** in T cells,
**-> CSF1/IL34** in T-ALL, **-> TNF/IL6** in spinal astrocytes (where STIM2 and not STIM1 carries
the LPS response, in the same cells), **-> PTGS2/IL8/TNF** under cisplatin, and **ORAI3 -> EGFR**
phosphorylation under hypoxia, which ORAI1 does not do.

**The `beyond_calcium` flag, used for the first time since batch 11, and deliberately.** PMC8316191
shows STIM1 knock-down *reinstating* TSHR and the thyroid-specific proteins and raising iodine
uptake, and raising p21. Thyroid differentiation and the cell cycle are the biological end of an
arm with nothing calcium about them, which is exactly what the user's decision of 2026-10-19
created the flag for. Both nodes are tagged "not calcium-related" on their pages.

**Three records dropped by the one-hop rule, and they raise a new question for #18.** The lead
from PMID 29480205 ("mutant Huntingtin sensitizes InsP3R1") was chased to **PMID 12873381** (Tang
2003), which gives an **InsP3R1-HAP1A-Htt ternary complex** and shows InsP3R1 sensitized by
polyglutamine-expanded but not normal huntingtin in a planar lipid bilayer. All three records
(HTT-ITPR1 binding, HAP1-ITPR1 binding, HTT -> ITPR1 activation) were **silently dropped by the
build**: ITPR1 is a seed, not an anchor, so HTT and HAP1 are two hops out. The records were
deleted rather than forced with `beyond_calcium`, which would have mislabelled a polyglutamine
calcium-release mechanism as "not calcium-related". The question for the curator: should seeds
that are themselves Ca2+ channels or pumps (ITPR1/2/3, RYR1/2, ATP2A1/2) count as anchors for the
one-hop rule? Everything the map holds upstream of ITPR1 today comes from the databases or her
own sheets, never from the literature, for exactly this reason.

**Negative claims the schema cannot hold** (recorded here, as in batch 15): PMID 26109647 shows
STIM1, STIM2 and SOCE are **dispensable** for macrophage and dendritic cell effector functions,
which sits oddly beside PMID 30054044 (batch 14, leptin -> ORAI1 in dendritic cell maturation).
PMID 28866365 shows ERK1/2 activation does not need SOCE at all.

**Generic names still blocking records**: `calmodulin` (PMID 23109337), `NFAT` where only an
antibody names the isoform (PMC9011325), `S1P receptor` (PMC8316191, one of five), `MAPK`
(PMC7424994), `KV1.3`/`SKCa` (PMC8268022), plus `IP3R`, `MLC2`, `ROCK`, `syntaxin 1`, `KCa`,
`Rap1`, calcineurine, AP-1, septins, ERK1/2, Akt/mTOR and AMPK from earlier batches.

Map: **305 nodes, 814 interactions, 1184 evidence rows**. Tests: **155 Python + 36 JS**.

**Next session:** `queue next 50 --tier 0 --primary`.

## 2026-10-21 — Extraction batch 17 (tier 0, `--primary`)

`queue next 50 --tier 0 --primary`, read one at a time, plus **four leads chased**. **89 records**
in `data/raw/lit_20261021_b21.jsonl`, all 89 sentences verified `true`, zero flagged. Four
articles `skipped`: PMID 17193710 is off-topic corpus noise (transposons in *Antirrhinum majus*),
PMID 23496221 a review of CRAC inhibitors, PMID 36775558 a duplicate PubMed record of PMID
33649466, and PMID 30401791 the authors' own commentary on their own work — chased to the primary,
PMID 29284605. Map: **338 nodes, 921 interactions, 1314 evidence rows**; **33 new nodes**, the
largest single-batch gain so far. Tests: **157 Python + 36 JS**.

**A bug this batch surfaced, fixed with a test: verbatim verification was case-sensitive.**
`MAPK1` entering the map pulled in SIGNOR-192788, whose excerpt lower-cases the gene symbols
(`between cdo and stim1 ... at serine 575` where the paper reads `Cdo` and `Stim1`). The quote is
faithful; the check called it **`false`**, which in the review app reads as *claim disproved*
rather than *not quoted verbatim*. `sentence_in` now compares case-insensitively (two tests in
`TestQuoteMatching`: the faithful lower-cased excerpt verifies, an altered one still fails).
Effect on the whole corpus: the single `false` is gone and **15 database excerpts moved from
`unverifiable` to `true`** (57 -> 42 unverifiable, 590 -> 606 true).

**The ER/PM junction gets a builder, and the pump turns around.** PMID 31061173 identifies
**ANO8** as the tether that makes the junction: without it STIM1 neither oligomerizes with itself
nor reaches ORAI1. The same paper assembles ORAI1, PMCA, STIM1, IP3 receptors and **SERCA2** at
that junction and describes a new form of channel inactivation in which **ATP2A2 -| ORAI1**,
SERCA2 pumping the entering Ca2+ straight back into the ER. The map had ATP2A2 only as a *target*
of STIM1 (batch 15); it is now also an inhibitor of the channel, and **ATP2A2 <-> STIM1** closes
as a loop with the second arrow from PMID 36442136 (below).

**Which pump is broken decides where the sensor sits — in patients.** PMID 36442136: Darier
disease (ATP2A2 mutations) shows **cytoplasmic** STIM1 by immunohistochemistry, Hailey-Hailey
disease (ATP2C1 mutations) a **membrane-associated** pattern, while ORAI1 shows no differential
pattern at all. Small series (five ambiguous cases, eight controls) and the readout is a staining
pattern, both written into the mechanism field. **ATP2C1**, a Golgi pump, is a new node.

**Filamin A, both ways round, from two papers.** PMID 39764579: the **calpain-cleaved C-terminal
fragment** of FLNA (repeats 16-24) slows ORAI1 and STIM1 protein degradation, abolishes Orai1alpha
*lysosomal* degradation and keeps the channel at the membrane — Orai1beta unaffected. The chased
primary PMID 29284605 gives the opposite sign for full-length FLNA: it **binds STIM1 on store
depletion** (dependent on Ser2152 phosphorylation by PKA, lost in the STIM1 K684,685E mutant) and
**brakes** the coupling — knocking FLNA down raises SOCE, the STIM1-ORAI1 association and
thrombin-induced platelet aggregation, and re-expression reverses it, while the S2152A mutant does
not. With batch 14's STIM1 -> CAPN1, the map now shows a cycle rather than a chain: the anchor
raises calpain, calpain cuts filamin A, the fragment raises the anchor.

**FAK and Pyk2, chased from a parenthesis.** PMID 31652779 remarks "we previously found that Orai1
is involved in FAK phosphorylation"; that lead is **PMID 27865925** (ORAI1 and ORAI2 -> PTK2 in
HL60 cells, where TRPC1/3/6 are absent so the entry is Orai-only) and, beside it, **PMID 25433371**
(ORAI1 -> PTK2B in glioma, with an ORAI1 rescue restoring p-Pyk2). The map carried "SOCE drives
migration" from a dozen papers with no gene at the mechanical end; it now has both focal-adhesion
kinases. The same AC8 paper gives **ADCY8-ORAI1**: co-IP with Orai1alpha only, strengthened by
store depletion *but only when Ca2+ actually enters*, and the AC8-bound subset of ORAI1 is not
serine-phosphorylated — a cAMP cyclase shielding the channel from its own inactivation.

**New upstream endocrine and receptor inputs**, which now number four on the same channel:
**NR3C2** (aldosterone, PMID 27129253: ORAI1, STIM1, TRPC1, TRPC4, TRPC5 all up through MR, with
SGK1 in between), **AGT** (angiotensin II, PMID 34079454), **FFAR1** (GPR40, PMID 31664108: the
fasiglifam potentiation of insulin secretion dies with knockdown of IP3R1, STIM1 *or* ORAI1, and
in beta-cell-specific Stim1 knockout mice in vivo), and **MRGPRX2** (PMID 35126366, the receptor
behind non-IgE mast cell activation). **CASR** arrives on the other side: the receptor that senses
extracellular Ca2+ lowering the abundance of the channel that lets it in (PMID 33804889).

**Effector ends named as genes.** **ANO1** and **TLR8** in salivary glands (PMID 38260625: SOCE
activates the chloride channel, and the transcriptome rules out an abundance explanation; TLR8 is
the authors' answer to why losing SOCE does *not* produce Sjogren's disease). **FASLG, TNF, IFNG**
in cytotoxic T cells in vivo (PMID 23922331). **IL5, IL13, CSF2, IL9, IL6** in pulmonary ILC2s
(PMID 37752127). **CCL3** with TNF and CXCL8 in mast cells. **CCND1** in hepatoma (PMID 18506892).
**MCU** — the mitochondrial uniporter, lower in DT40 cells lacking IP3R, STIM1 *or* ORAI1, through
CREB bound to its promoter (PMID 25737585). **MAP1LC3B, NPPA, NPPB, COL1A1** in the heart (PMID
34079454, AAV-shRNA-Orai1 by tail vein), with **CAMKK2 -> MAP1LC3B** completing channel ->
CaMKKbeta -> AMPK/LC3 from batch 12. **BAX** and **CASP3** twice over: by abundance in lung injury
(PMID 27025854, where the 2-APB arm's weakness is written into the mechanism) and by activation
through STIM1 N-glycosylation (PMID 36612199, where the link *breaks* in breast cancer cells).

**Two Alzheimer genes, and a sensor acting on a voltage-gated channel.** PMID 36499137: hippocampal
neurons of 5xFAD mice have excessive store-operated entry before any plaque, with unchanged STIM1
and STIM2 protein — a change of function, not abundance. Recorded as **APP -> STIM1** and **PSEN1
-> STIM1** with the mechanism stating plainly that the model carries mutations in both genes and
the experiment cannot separate them. The same paper gives **STIM2 -> CACNA1C** (nifedipine
sensitive, ML218 insensitive, STIM2-dependent *with stores full*), which lands beside the
STIM1 -> CACNA1C conflict opened in batches 13 and 15.

**GSK3 as a brake on the whole module.** PMID 24523925: dendritic cells from mice whose GSK3alpha
and GSK3beta carry PKB/SGK-resistant knock-in mutations have **less ORAI1, STIM1 and STIM2**.
Recorded as six records (both isoforms x three targets) because the knock-in hits both at once;
four to twenty-four hours of pharmacological inhibition changed no abundance, so the effect is
chronic. **JAK3** enters with the epistasis test batch 15's lost JAK2 record lacked (PMID 31879743:
re-expressing ORAI1 *or* STIM1 restores migration in JAK3-silenced cells), and its sentence carries
the SOCE sentence alongside, which is what the calcium criterion needs.

**ORAI1 and TRPC1, resolved by variant and by direction.** PMID 34988680: APEX2 proximity
labelling, co-IP and a channel-fused Ca2+ sensor all agree that **Orai1alpha, not Orai1beta**, binds
TRPC1, that histamine and store depletion strengthen it, and that **ORAI1 carries TRPC1 to the
membrane while TRPC1 does nothing to ORAI1's location** — an asymmetry between two anchors, tested
both ways. Beside it, **ORAI1-CTTN** by endogenous-to-endogenous co-IP at the leading edge (PMID
28341841), with the STIM1-cortactin half recorded as the weaker one it is (colocalization of
pS575-STIM1, no pulldown). **TRPC1-ORAI1-STIM1** as a ternary co-IP in *human parathyroid tissue*
rather than in overexpression (PMID 20194530), and **ORAI1/STIM1 colocalized with RYR** in
preformed 300 nm patches of resting T cells (PMID 30563862), where RYR1 and ORAI1 together build
Ca2+ microdomains within the first second of TCR stimulation.

**The 33 new nodes dragged in 34 database edges**, several of which matter more than the records
that admitted them: **MAPK1 -> STIM1** phosphorylation at Ser575 (SIGNOR, from PMID 22298426) now
closes **ORAI1 -> MAPK1 -> STIM1** — and the cortactin paper independently stains **pS575-STIM1**
at the leading edge, the same site. **MAP1LC3B-TBK1** binding is the first edge that ties the
autophagy machinery to the STING arm. **APP binds CALM1 and CAMK2A**; **GSK3B -| NFATC1/NFATC2**
and **-| ATP2A2**; **AKT1** binds ITPR1, CAMK2A, IKBKE and NFATC1; **CRACR2A-FFAR1**; **CAMK2A ->
PTK2**. **NTN1** arrives from the axon-guidance paper (PMID 24289807, Xenopus growth cones, netrin-1
attraction needing STIM1 and TRPC1) and immediately meets the SIGNOR netrin-2/Cdo/STIM1 row that
the verification fix rescued.

**Records not written, and why.** PMID 34065942 shows **ORAI3 -> NANOG and -> SOX2** enriching
cancer stem cells under cisplatin, with ORAI1 and STIM1 explicitly *not* changed. Both records
would have been **silently dropped**: ORAI3 is a level-1 seed but not an anchor, so NANOG and SOX2
are two hops out — the same wall that cost the huntingtin records in batch 16, and a second
argument for the #18 question, widened: should **ORAI2, ORAI3 and STIM2** count as anchors too?
They are the canonical SOCE proteins, and today anything hanging off them alone falls out.
PMID 26055321 (SOCE restored in invasive melanoma by a PKC-insensitive ORAI1 mutant, with WNT5A
upstream) is blocked by `PKC` with no isoform. PMID 33804889 and its chased primary PMID 32015442
both *assert* NFAT5 -> SGK1 -> ORAI1 and neither knocks NFAT5 down, so **NFAT5 is not in the map**:
the records would have been an abundance correlation dressed as a cascade.

**Negative claims the schema cannot hold**: PMID 36612199 — SOCE in MCF7 and MDA-MB-231 is
*insensitive* to Orai1 and STIM1 N-linked glycosylation, which is only a defect in non-tumoral
cells. PMID 29242293 — FERMT3 (kindlin-3) patients lose platelet thrombus formation entirely, by a
route independent of ORAI1/STIM1. PMID 33182378 — forty STIM1/ORAI1 polymorphisms in 3631 chronic
hepatitis B patients, none significant after correction for multiple testing.

**Generic names still blocking records**: `PKC` and `PKA` on the ORAI1 Ser-27/30/34 sites (PMID
26055321, PMID 31652779), `CaMKK` under STO-609 (PMID 34079454, recorded against CAMKK2 with the
ambiguity stated), `ERK1/2` and `Akt` in mast cells (recorded against MAPK1/MAPK3/AKT1, same
caveat), plus `calmodulin`, `IP3R`, `MLC2`, `ROCK`, `syntaxin 1`, `KCa`, `Rap1`, calcineurine,
AP-1, septins and AMPK from earlier batches.

Map: **338 nodes, 921 interactions, 1314 evidence rows**. Tests: **157 Python + 36 JS**.

**Next session:** `queue next 50 --tier 0 --primary`.
