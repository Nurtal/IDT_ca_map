# Extraction protocol

How a Claude Code session turns papers from the work queue into reviewed-ready interactions.
Read this first in every extraction session, then `pipeline/state/PROGRESS.md`.

## Pipeline at a glance

```
python3 pipeline/cli.py corpus        # (re)count corpus, (re)build the prioritized queue — idempotent
python3 pipeline/cli.py fetch-db      # SIGNOR / OmniPath / IntAct (/ BioGRID with BIOGRID_ACCESS_KEY) -> data/raw/db_*.jsonl
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
   read those first, then the full document where needed. Read a cached document with
   `PYTHONPATH=pipeline python3 -c "from camap.pubtator import PubTator; print(PubTator('pipeline/cache').document('123')['text'])"`.
4. For each article, read title + abstract (and full text when the abstract contains a candidate).
   Write one raw record per **(interaction, supporting sentence)** to
   `data/raw/lit_<YYYYMMDD>_<batch>.jsonl` (format below). An article may yield zero records.
5. Mark each article: `python3 pipeline/cli.py queue set <PMID...> done`
   (`skipped --note "review article, no primary data"`, or `error --note ...`).
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
