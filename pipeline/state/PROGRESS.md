# Extraction progress

See docs/EXTRACTION_PROTOCOL.md for the session procedure.

<!-- auto:start -->
## Status (generated)

13519 articles in queue: 370 done, 13027 pending, 120 skipped, 2 error.

- tier 0: 342/3800 processed
- tier 1: 149/3812 processed
- tier 2: 1/5907 processed

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
