# Extraction progress

See docs/EXTRACTION_PROTOCOL.md for the session procedure.

<!-- auto:start -->
## Status (generated)

9100 articles in queue: 78 done, 8985 pending, 36 skipped, 1 error.

- tier 0: 71/192 processed
- tier 1: 44/6582 processed
- tier 2: 0/2326 processed

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
