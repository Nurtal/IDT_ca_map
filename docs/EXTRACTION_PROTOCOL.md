# Extraction protocol

How a Claude Code session turns papers from the work queue into reviewed-ready interactions.
Read this first in every extraction session, then `pipeline/state/PROGRESS.md`.

## Pipeline at a glance

```
python3 pipeline/cli.py corpus        # (re)count corpus, (re)build the prioritized queue — idempotent
python3 pipeline/cli.py fetch-db      # SIGNOR / OmniPath / IntAct (/ BioGRID with BIOGRID_ACCESS_KEY) -> data/raw/db_*.jsonl
python3 pipeline/cli.py supp          # data_supp/*.xlsx -> data/raw/supp_*.jsonl + data/supp_catalogue.json
python3 pipeline/cli.py queue next 50 # next pending articles
python3 pipeline/cli.py fetch-texts   # cache texts of every paper cited in data/raw (git-ignored cache)
python3 pipeline/cli.py annotate      # HGNC + GO calcium + UniProt for every actor
python3 pipeline/cli.py build         # data/raw -> data/{nodes,interactions,evidence}.{csv,js}
```

Then open `review/index.html` (double-click, no server). After review, export
`kept_interactions.csv` into `data/`, run `python3 pipeline/cli.py graph`, open `graph/index.html`.

## One extraction batch (~50 articles)

1. `git pull`, read `pipeline/state/PROGRESS.md` (status block + session notes).
2. `python3 pipeline/cli.py queue next 50` (add `--tier N` to stay inside one tier) — take them in that order (priority: STIM1×STING1,
   then anchor × seed pairs, then each anchor alone; within a tier, queries crossing the two
   sides of the axis — a calcium-side gene with a STING-side gene — come first, then primary
   research before reviews, which are flagged `[review]`).
3. Fetch their texts: `python3 pipeline/cli.py fetch-texts --next 50` (or `--pmids 123 456`; `--tier N` applies).
   Process articles **one at a time**: `queue next 1 --tier N`, read, record, `queue set`. Reading a
   dozen papers' candidate sentences in one go has repeatedly failed mid-batch.
   `python3 pipeline/cli.py candidates --next 50` prints, per paper, the title, abstract and the
   sentences naming an anchor with a seed / calcium term / interaction verb (tags in brackets);
   read those first, then the full document where needed. `--strong` keeps only the sentences
   that carry both anchors, or an anchor plus a seed/calcium term *and* an interaction verb —
   use it to triage the long tail, where most articles only co-mention the genes. Deep in tier 1
   even `--strong` leaves too much to read: screen first for articles with an anchor **and** a
   seed or a calcium term in the same sentence (regex over the cached text) — the same pairing the
   inclusion rule needs, so nothing that could become an edge is screened out — and read those in
   full, plus any whose title promises primary calcium or STING work. A 50-article batch of that
   tail typically leaves fewer than ten articles worth reading. Read a cached document with
   `PYTHONPATH=pipeline python3 -c "from camap.pubtator import PubTator; print(PubTator('pipeline/cache').document('123')['text'])"`.
4. For each article, read title + abstract (and full text when the abstract contains a candidate).
   Write one raw record per **(interaction, supporting sentence)** to
   `data/raw/lit_<YYYYMMDD>_<batch>.jsonl` (format below). An article may yield zero records.
5. Mark each article: `python3 pipeline/cli.py queue set <PMID...> done`
   (`skipped --note "review article, no primary data"`, or `error --note ...`).
   `done` means the article's own experiments were read, whether or not they yielded a record;
   `skipped` means there was nothing of ours to read — a review, a commentary, or a paper that
   only lists the genes (bioinformatic screen, atlas, network pharmacology). Every status carries
   a `--note` saying which, so the done/skipped counts stay readable.
6. `python3 pipeline/cli.py fetch-texts && python3 pipeline/cli.py annotate && python3 pipeline/cli.py build`.
   The build prints how many sentences are not verbatim: fix them (copy the sentence exactly) before committing.
7. Add a dated line under `## Session notes` in `PROGRESS.md` (what was done, anything odd).
8. Commit: `Extraction batch N: PMIDs a..b (k interactions)`.

## Raw record format (one JSON object per line)

| field | required | notes |
|---|---|---|
| `source`, `target` | yes | as written in the paper; the build normalizes to HGNC / ChEBI. For directed types, `source` acts on `target`. |
| `type` | yes | `activation`, `inhibition`, `physical_binding`, `phosphorylation`, `ubiquitination`, `translocation/trafficking`, `expression_regulation_up`, `expression_regulation_down`, `coexpression`, `Ca2+_flux`, `unknown_regulation` |
| `mechanism` | no | short free text (domain, residue, assay) |
| `sentence` | yes | **verbatim** sentence from the article supporting the claim |
| `source_kind` | yes | `pubmed` (abstract) or `pmc` (full text) |
| `ref` | yes | `PMID:123` or `PMC123` |
| `doi`, `year`, `first_author` | recommended | from the cached document |
| `species_context` | yes | `human`, `in_vitro_human_cells`, `mouse`, `rat`, `other`, `unknown` — the system the claim was shown in |
| `justification` | yes | one or two sentences: why this interaction matters for the STIM1/STING calcium axis |

Rules of thumb:

- Extract **mechanistic** claims shown in the paper (not background statements citing others,
  not speculation). Prefer the results sentence over the introduction.
- One claim per record; if a sentence supports two interactions, write two records.
- Bridges between the STIM1/SOCE side and the STING side deserve an explicit justification.
- Do not invent direction: if unclear, use `physical_binding` or `unknown_regulation`.
- Keep reviews/meta-analyses as `skipped` unless they report primary data.

## Inclusion rule (applied by the build, for reference)

A non-seed actor survives only if it interacts directly with an anchor (STIM1 or STING1) **and** is
calcium-related (GO calcium transport/signalling annotation, or a calcium term in a supporting sentence).
Level-1 seeds are always kept; level-2 seeds (calcineurin, NFAT, CaMKII) need a link to an anchor.
See `pipeline/config/seeds.json`.

## The curator's spreadsheets (`data_supp/`)

`data_supp/` holds spreadsheets the researcher maintains by hand. They are a fourth source,
next to the literature and the interaction databases, and `cli.py supp` turns them into raw
records like any other (mapping in `pipeline/config/supp.json`, open questions in issue #18).

| File | What the pipeline does with it |
|---|---|
| `interactome STIM1 bis.xlsx` (`STIM1`, `Orai`, `TRPC`) | one interaction per row, anchored on STIM1 / ORAI1 / TRPC1 |
| `interactome STING.xlsx` (`interactors`, `modulators`) | one interaction per row, anchored on STING1 |
| `Genes sauvegardes 24022022.xlsx` | **not** nodes: the calcium-relevance reference, plus expert annotations for the nodes that do enter |

Rules that keep these rows honest:

- `source_kind` is `curated` and `ref` is the row's DOI (`DOI:10.xxxx/...`), or
  `CURATED:<file>/<sheet>/<symbol>` when the curator cites no paper. One record per DOI.
- A curated row carries a **`curator_note`, never a `sentence`**: it is the researcher's summary
  of a paper, not a quote from it. `sentence_verified` stays empty, so the ⚠️ of a quote that
  could not be found verbatim keeps its meaning. Both pages label it "Curator summary".
- `supp_source` records file, sheet and row, so every record traces back to a cell.
- Nothing is guessed in silence. A regulation value the mapping does not know, a cell that is not
  a gene symbol, a symbol HGNC does not have: each is printed by `cli.py supp` and, where the row
  cannot become an edge, left out rather than coerced. Symbol repairs are explicit in
  `symbol_fixes`; cells naming a family or several genes are left for the curator.
- A gene of the catalogue satisfies the calcium half of the inclusion rule on its own
  (`calcium_evidence` then contains `curated`, e.g. `GO+curated`), but it still needs an
  interaction with an anchor to enter the graph — the catalogue adds no isolated nodes.
- `cli.py supp --report` says how many catalogue genes are in the map, how many the corpus has
  already turned up without an anchor link yet (the extraction leads), and how many it has never
  touched. The run also writes `data/supp_report.txt` with every symbol and value it could not read.
- `cli.py build` writes `data/supp_dropped.txt`: every curated interaction the inclusion rule
  dropped, with its reason. Partners of ORAI1 and TRPC1 land there whenever nothing links them to
  STIM1 or STING1 — those two are seeds, not anchors, so their partners sit two hops from the axis.
- A curated row records no species, so its interaction has neither human nor animal evidence. The
  pages say "species not recorded" and the murine-only filter leaves it visible: unknown is not
  the same as non-human.
