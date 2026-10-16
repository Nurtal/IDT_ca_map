#!/usr/bin/env python3
"""Pipeline entry point.

    python3 pipeline/cli.py corpus         # count the corpus and (re)build the prioritized work queue
    python3 pipeline/cli.py queue next 50  # list the next pending articles
    python3 pipeline/cli.py queue set PMID done|skipped|error|pending [--note TEXT]
    python3 pipeline/cli.py fetch-db       # SIGNOR / OmniPath / IntAct / BioGRID -> data/raw/db_*.jsonl
    python3 pipeline/cli.py fetch-texts    # cache PubTator texts of every paper cited in data/raw
    python3 pipeline/cli.py annotate       # cache HGNC set + GO calcium / UniProt annotations of every actor
    python3 pipeline/cli.py graph [CSV]    # kept_interactions.csv -> data/graph_data.js for graph/index.html
    python3 pipeline/cli.py build          # data/raw/*.jsonl -> data/{nodes,interactions,evidence}.{csv,js}
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from camap.build import build_dataset, read_raw  # noqa: E402
from camap.corpus import build_queue, next_pending, set_statuses  # noqa: E402
from camap.databases import fetch_all  # noqa: E402
from camap.graph import build_graph  # noqa: E402
from camap.annotate import annotate_genes, ensure_hgnc  # noqa: E402
from camap.nodes import Resolver, load_config  # noqa: E402
from camap.pubtator import PubTator  # noqa: E402

CACHE = ROOT / "pipeline" / "cache"
STATE = ROOT / "pipeline" / "state"


def main(argv=None):
    p = argparse.ArgumentParser(prog="cli.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build data files from raw extraction records")
    b.add_argument("--raw", default=ROOT / "data" / "raw", type=Path)
    b.add_argument("--out", default=ROOT / "data", type=Path)
    f = sub.add_parser("fetch-texts", help="cache PubTator texts for papers cited in raw records")
    f.add_argument("--raw", default=ROOT / "data" / "raw", type=Path)
    f.add_argument("--pmids", nargs="+", help="fetch these PMIDs instead of those cited in raw records")
    f.add_argument("--next", type=int, metavar="N", help="fetch the next N pending articles of the queue")
    sub.add_parser("fetch-db", help="import interaction databases around the seeds into data/raw")
    a = sub.add_parser("annotate", help="cache HGNC + GO calcium + UniProt annotations for all actors")
    a.add_argument("--raw", default=ROOT / "data" / "raw", type=Path)
    sub.add_parser("corpus", help="count the corpus and (re)build the work queue")
    q = sub.add_parser("queue", help="inspect or update the work queue")
    qsub = q.add_subparsers(dest="qcmd", required=True)
    qn = qsub.add_parser("next")
    qn.add_argument("n", type=int, nargs="?", default=50)
    qs = qsub.add_parser("set")
    qs.add_argument("pmids", nargs="+")
    qs.add_argument("status", choices=["pending", "done", "skipped", "error"])
    qs.add_argument("--note")
    g = sub.add_parser("graph", help="kept_interactions.csv -> data/graph_data.js")
    g.add_argument("csv", nargs="?", default=ROOT / "data" / "kept_interactions.csv", type=Path)
    args = p.parse_args(argv)

    if args.cmd == "build":
        tables = build_dataset(args.raw, args.out, cache_dir=CACHE)
        for name, (_, rows) in tables.items():
            print(f"{name}: {len(rows)} rows")
        unverified = [e for e in tables["evidence"][1] if e["sentence_verified"] == "false"]
        if unverified:
            print(f"WARNING: {len(unverified)} sentence(s) not found verbatim in cached texts")
    elif args.cmd == "fetch-texts":
        pt = PubTator(CACHE)
        pmids = set(args.pmids or [])
        if args.next:
            pmids |= {e["pmid"] for e in next_pending(STATE, args.next)}
        for r in ([] if pmids else read_raw(args.raw)):
            if r["source_kind"] in ("pubmed", "pmc"):
                pmids.add(r["ref"])
            if r.get("cited_pmid"):
                pmids.add(r["cited_pmid"])
        fetched = pt.fetch_texts(sorted(pmids))
        print(f"{len(pmids)} cited papers, {len(fetched)} newly fetched")
    elif args.cmd == "graph":
        n = build_graph(args.csv, ROOT / "data" / "graph_data.js")
        print(f"{n} kept interactions -> data/graph_data.js")
    elif args.cmd == "corpus":
        report = build_queue(load_config(), PubTator(CACHE), STATE)
        for text, count in report["per_query"].items():
            if count:
                print(f"{count:6d}  {text}")
        zero = [t for t, c in report["per_query"].items() if not c]
        print(f"{len(zero)} queries with no hit")
        print(f"TOTAL unique articles: {report['total_articles']}  per tier: {report['per_tier']}")
    elif args.cmd == "queue" and args.qcmd == "next":
        for e in next_pending(STATE, args.n):
            print(f"{e['pmid']}\t{e.get('pmcid') or '-'}\ttier {e['tier']}\t{e['year']}\t{e['title'][:90]}")
    elif args.cmd == "queue" and args.qcmd == "set":
        try:
            set_statuses(STATE, args.pmids, args.status, note=args.note)
        except KeyError as e:
            sys.exit(f"Nothing updated: {e.args[0]}")
        print(f"{len(args.pmids)} article(s) -> {args.status}")
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
    elif args.cmd == "annotate":
        ensure_hgnc(CACHE)
        config = load_config()
        resolver = Resolver(CACHE, config)
        names = {s["symbol"] for s in config["seeds"]}
        for r in read_raw(args.raw):
            names.update((r["source"], r["target"]))
        symbols = {resolver.resolve(n) for n in names} - set(resolver.metabolites)
        print(f"{len(symbols)} actors, {annotate_genes(symbols, CACHE)} newly annotated")


if __name__ == "__main__":
    main()
