#!/usr/bin/env python3
"""Pipeline entry point.

    python3 pipeline/cli.py corpus         # count the corpus and (re)build the prioritized work queue
    python3 pipeline/cli.py queue next 50  # list the next pending articles
    python3 pipeline/cli.py queue set PMID done|skipped|error|pending [--note TEXT]
    python3 pipeline/cli.py queue add PMID...   # a lead the corpus searches never returned
    python3 pipeline/cli.py fetch-db       # SIGNOR / OmniPath / IntAct / BioGRID -> data/raw/db_*.jsonl
    python3 pipeline/cli.py fetch-texts    # cache PubTator texts of every paper cited in data/raw
    python3 pipeline/cli.py annotate       # cache HGNC set + GO calcium / UniProt annotations of every actor
    python3 pipeline/cli.py graph [CSV]    # kept_interactions.csv -> data/graph_data.js for graph/index.html
    python3 pipeline/cli.py supp           # data_supp/*.xlsx -> data/raw/supp_*.jsonl + data/supp_catalogue.json
    python3 pipeline/cli.py build          # data/raw/*.jsonl -> data/{nodes,interactions,evidence}.{csv,js}
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from camap.build import build_dataset, read_raw  # noqa: E402
from camap.corpus import add_articles, build_queue, next_pending, set_statuses  # noqa: E402
from camap.pubmed import publication_types  # noqa: E402
from camap.candidates import candidate_sentences, strong_only  # noqa: E402
from camap.databases import fetch_all  # noqa: E402
from camap.graph import build_graph  # noqa: E402
from camap.annotate import annotate_genes, ensure_hgnc  # noqa: E402
from camap.nodes import Resolver, load_config  # noqa: E402
from camap.pubtator import PubTator  # noqa: E402
from camap.string import fetch_scores, genes_only  # noqa: E402
from camap.supp import (catalogue_report, load_supp_config, read_all, split_unresolved,  # noqa: E402
                        supp_file_stem)

CACHE = ROOT / "pipeline" / "cache"
SUPP_CONFIG = ROOT / "pipeline" / "config" / "supp.json"
STATE = ROOT / "pipeline" / "state"


def show(path):
    """A path relative to the repo when it is inside it, absolute otherwise."""
    path = Path(path).resolve()
    return path.relative_to(ROOT) if path.is_relative_to(ROOT) else path


def main(argv=None):
    p = argparse.ArgumentParser(prog="cli.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build data files from raw extraction records")
    b.add_argument("--raw", default=ROOT / "data" / "raw", type=Path)
    b.add_argument("--out", default=ROOT / "data", type=Path)
    f = sub.add_parser("fetch-texts", help="cache PubTator texts for papers cited in raw records")
    f.add_argument("--raw", default=ROOT / "data" / "raw", type=Path)
    f.add_argument("--pmids", nargs="+", help="fetch these PMIDs instead of those cited in raw records")
    f.add_argument("--tier", type=int, choices=(0, 1, 2), help="restrict --next to this corpus tier")
    f.add_argument("--next", type=int, metavar="N", help="fetch the next N pending articles of the queue")
    f.add_argument("--primary", action="store_true", help="with --next, skip review articles")
    sub.add_parser("fetch-db", help="import interaction databases around the seeds into data/raw")
    a = sub.add_parser("annotate", help="cache HGNC + GO calcium + UniProt annotations for all actors")
    a.add_argument("--raw", default=ROOT / "data" / "raw", type=Path)
    a.add_argument("--nodes", default=ROOT / "data" / "nodes.csv", type=Path,
                   help="the previous build's nodes, whose pairs get a STRING score")
    sub.add_parser("corpus", help="count the corpus and (re)build the work queue")
    s = sub.add_parser("supp", help="read the curator's spreadsheets in data_supp/ into data/raw")
    s.add_argument("--out", default=ROOT / "data", type=Path)
    s.add_argument("--report", action="store_true",
                   help="also report how the gene catalogue overlaps the map built so far")
    q = sub.add_parser("queue", help="inspect or update the work queue")
    qsub = q.add_subparsers(dest="qcmd", required=True)
    qn = qsub.add_parser("next")
    qn.add_argument("--tier", type=int, choices=(0, 1, 2), help="only this corpus tier")
    qn.add_argument("--primary", action="store_true",
                    help="pass over the articles PubMed types as reviews (they keep their rank)")
    qn.add_argument("n", type=int, nargs="?", default=50)
    qs = qsub.add_parser("set")
    qs.add_argument("pmids", nargs="+")
    qs.add_argument("status", choices=["pending", "done", "skipped", "error"])
    qs.add_argument("--note")
    qa = qsub.add_parser("add", help="add articles the corpus searches never returned")
    qa.add_argument("pmids", nargs="+")
    qa.add_argument("--note", help="where the lead came from")
    c = sub.add_parser("candidates", help="print title, abstract and candidate sentences of cached papers")
    c.add_argument("pmids", nargs="*")
    c.add_argument("--next", type=int, help="the next N pending articles of the queue")
    c.add_argument("--tier", type=int, choices=(0, 1, 2), help="restrict --next to this corpus tier")
    c.add_argument("--primary", action="store_true", help="with --next, skip review articles")
    c.add_argument("--limit", type=int, default=40)
    c.add_argument("--strong", action="store_true",
                   help="only anchor-pair sentences, or anchor + seed/calcium with an interaction verb")
    g = sub.add_parser("graph", help="kept_interactions.csv -> data/graph_data.js")
    g.add_argument("csv", nargs="?", default=ROOT / "data" / "kept_interactions.csv", type=Path)
    args = p.parse_args(argv)

    if args.cmd == "build":
        tables, dropped = build_dataset(args.raw, args.out, cache_dir=CACHE,
                                        catalogue_path=ROOT / "data" / "supp_catalogue.json")
        for name, (_, rows) in tables.items():
            print(f"{name}: {len(rows)} rows")
        rows = tables["evidence"][1]
        unverified = [e for e in rows if e["sentence_verified"] == "false"]
        if unverified:
            print(f"WARNING: {len(unverified)} sentence(s) not found verbatim in cached texts")
            for e in unverified[:10]:
                print(f"         {e['ref']}: {e['sentence'][:70]}...")
        unverifiable = sum(1 for e in rows if e["sentence_verified"] == "unverifiable")
        if unverifiable:
            print(f"{unverifiable} database excerpt(s) not checkable: only the abstract of the "
                  f"cited paper is cached")
        report = Path(args.out) / "supp_dropped.txt"
        if dropped:
            print(f"WARNING: {len(dropped)} curated interaction(s) dropped by the inclusion rule "
                  f"(see data/supp_dropped.txt)")
            report.write_text("\n".join(dropped) + "\n")
        elif report.exists():  # a stale report would claim drops the current build does not make
            report.unlink()
    elif args.cmd == "fetch-texts":
        pt = PubTator(CACHE)
        pmids = set(args.pmids or [])
        if args.next:
            pmids |= {e["pmid"] for e in next_pending(STATE, args.next, tier=args.tier,
                                                      primary=args.primary)}
        for r in ([] if pmids else read_raw(args.raw)):
            if r["source_kind"] in ("pubmed", "pmc"):
                pmids.add(r["ref"])
            if r.get("cited_pmid"):
                pmids.add(r["cited_pmid"])
        fetched = pt.fetch_texts(sorted(pmids))
        print(f"{len(pmids)} cited papers, {len(fetched)} newly fetched")
    elif args.cmd == "candidates":
        config = load_config()
        resolver, pt = Resolver(CACHE, config), PubTator(CACHE)
        anchors = [n for a in config["anchors"] for n in resolver.names(a)]
        seeds = [n for s in config["seeds"] if s["symbol"] not in config["anchors"] for n in resolver.names(s["symbol"])]
        pmids = list(args.pmids) + [e["pmid"] for e in next_pending(STATE, args.next or 0,
                                                                    tier=args.tier, primary=args.primary)]
        for pmid in pmids:
            doc = pt.document(pmid)
            if doc is None:
                print(f"=== {pmid}: not cached (run fetch-texts)\n")
                continue
            lines = doc["text"].split("\n")
            print(f"=== PMID {doc['pmid']} {doc['pmcid'] or ''} | {doc['first_author']} {doc['year']} | "
                  f"{'full text' if doc['full_text'] else 'abstract only'}\n# {doc['title']}")
            abstract = " ".join(l for l in lines[1:12] if len(l) > 40)[:2500] if not doc["full_text"] else \
                next((l for l in lines[1:12] if len(l) > 200), "")
            print("ABSTRACT: " + abstract)
            cands = candidate_sentences(doc, anchors, seeds, config["calcium_text_pattern"], args.limit)
            if args.strong:
                cands = strong_only(cands)
            for i, (s, tags) in enumerate(cands):
                print(f"  [{i}] ({','.join(tags)}) {s}")
            print()
    elif args.cmd == "graph":
        n = build_graph(args.csv, ROOT / "data" / "graph_data.js")
        print(f"{n} kept interactions -> data/graph_data.js")
    elif args.cmd == "corpus":
        report = build_queue(load_config(), PubTator(CACHE), STATE, pubtypes=publication_types)
        for text, count in report["per_query"].items():
            if count:
                print(f"{count:6d}  {text}")
        zero = [t for t, c in report["per_query"].items() if not c]
        print(f"{len(zero)} queries with no hit")
        print(f"TOTAL unique articles: {report['total_articles']}  per tier: {report['per_tier']}")
    elif args.cmd == "queue" and args.qcmd == "next":
        for e in next_pending(STATE, args.n, tier=args.tier, primary=args.primary):
            review = " [review]" if e.get("review") else ""
            print(f"{e['pmid']}\t{e.get('pmcid') or '-'}\ttier {e['tier']}\t{e['year']}\t{e['title'][:90]}{review}")
    elif args.cmd == "queue" and args.qcmd == "set":
        try:
            set_statuses(STATE, args.pmids, args.status, note=args.note)
        except KeyError as e:
            sys.exit(f"Nothing updated: {e.args[0]}")
        print(f"{len(args.pmids)} article(s) -> {args.status}")
    elif args.cmd == "queue" and args.qcmd == "add":
        texts = PubTator(CACHE)
        texts.fetch_texts([f"PMID:{p}" for p in args.pmids])

        def metadata(pmid):
            doc = texts.document(pmid)
            return {k: doc.get(k, "") for k in ("title", "year", "pmcid")} if doc else None

        added, present = add_articles(STATE, args.pmids, metadata, note=args.note)
        for e in added:
            print(f"added  {e['pmid']}\t{e['title'][:80] or '(no title: PubTator knows nothing of it)'}")
        for pmid in present:
            print(f"already in the queue: {pmid}")
    elif args.cmd == "fetch-db":
        ensure_hgnc(CACHE)
        config = load_config()
        resolver = Resolver(CACHE, config)
        genes = [(s["symbol"], (resolver.gene(s["symbol"]).get("uniprot_ids") or [""])[0]) for s in config["seeds"]]
        results, warnings = fetch_all(genes)
        raw = ROOT / "data" / "raw"
        for kind, records in results.items():
            path = raw / f"db_{kind}.jsonl"
            if not records:
                # skipped or empty answer: keep whatever an earlier run committed
                print(f"{kind}: no records fetched, {path.relative_to(ROOT)} left unchanged")
                continue
            unique = {json.dumps(r, sort_keys=True) for r in records}
            path.write_text("".join(line + "\n" for line in sorted(unique)))
            print(f"{kind}: {len(unique)} records -> {path.relative_to(ROOT)}")
        for w in warnings:
            print("WARNING:", w)
    elif args.cmd == "supp":
        ensure_hgnc(CACHE)
        config = load_config()
        resolver = Resolver(CACHE, config)
        supp_config = load_supp_config(SUPP_CONFIG)
        records, catalogue, notes = read_all(supp_config, ROOT, resolve=resolver.resolve)
        records, unknown = split_unresolved(records, resolver)

        raw = args.out / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        by_sheet = {}
        for r in records:
            by_sheet.setdefault(supp_file_stem(r["supp_source"]), []).append(r)
        for stem, rows in sorted(by_sheet.items()):
            path = raw / f"supp_{stem}.jsonl"
            path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
            print(f"{len(rows):4d} records -> {show(path)}")
        catalogue_path = args.out / "supp_catalogue.json"
        catalogue_path.write_text(json.dumps(catalogue, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
        print(f"{len(catalogue):4d} catalogue genes -> {show(catalogue_path)}")

        lines = []
        if unknown:
            lines.append(f"{len(unknown)} cell(s) the resolver could not map to HGNC, "
                         f"held out of the map (see issue #18):")
            for symbol, where in sorted(unknown.items()):
                lines.append(f"  {symbol:20s} {where[0]}"
                             f"{'' if len(where) == 1 else f' (+{len(where) - 1} more)'}")
        lines.extend(f"NOTE: {n}" for n in notes)
        print()
        for line in lines:
            print(line)
        report_path = args.out / "supp_report.txt"
        report_path.write_text("\n".join(lines) + "\n")
        print(f"\nreport -> {show(report_path)}")
        if args.report:
            print()
            nodes_csv = args.out / "nodes.csv"
            node_ids = {row["id"] for row in csv.DictReader(nodes_csv.open())} if nodes_csv.exists() else set()
            seen = {resolver.resolve(n) for r in read_raw(raw) for n in (r["source"], r["target"])}
            for line in catalogue_report(catalogue, node_ids, seen):
                print(line)
    elif args.cmd == "annotate":
        ensure_hgnc(CACHE)
        config = load_config()
        resolver = Resolver(CACHE, config)
        names = {s["symbol"] for s in config["seeds"]}
        for r in read_raw(args.raw):
            names.update((r["source"], r["target"]))
        symbols = {resolver.resolve(n) for n in names} - set(resolver.metabolites)
        print(f"{len(symbols)} actors, {annotate_genes(symbols, CACHE)} newly annotated")
        # STRING scores the pairs of the map itself, not every actor seen in a raw record:
        # it is an annotation on edges the map already has (story 22 of issue #1).
        if args.nodes.exists():
            with open(args.nodes, newline="") as f:
                nodes = genes_only(r["id"] for r in csv.DictReader(f))
            scores = fetch_scores(nodes, CACHE)
            print(f"{len(nodes)} genes of the map, {len(scores)} STRING pair score(s) "
                  f"(annotation only, never an edge)")
        else:
            print(f"no {show(args.nodes)} yet: run build once, then annotate again for STRING scores")


if __name__ == "__main__":
    main()
