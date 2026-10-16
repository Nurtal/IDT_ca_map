#!/usr/bin/env python3
"""Pipeline entry point.

    python3 pipeline/cli.py fetch-texts    # cache PubTator texts of every paper cited in data/raw
    python3 pipeline/cli.py annotate       # cache HGNC set + GO calcium / UniProt annotations of every actor
    python3 pipeline/cli.py build          # data/raw/*.jsonl -> data/{nodes,interactions,evidence}.{csv,js}
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from camap.build import build_dataset, read_raw  # noqa: E402
from camap.annotate import annotate_genes, ensure_hgnc  # noqa: E402
from camap.nodes import Resolver, load_config  # noqa: E402
from camap.pubtator import PubTator  # noqa: E402

CACHE = ROOT / "pipeline" / "cache"


def main(argv=None):
    p = argparse.ArgumentParser(prog="cli.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build data files from raw extraction records")
    b.add_argument("--raw", default=ROOT / "data" / "raw", type=Path)
    b.add_argument("--out", default=ROOT / "data", type=Path)
    f = sub.add_parser("fetch-texts", help="cache PubTator texts for papers cited in raw records")
    f.add_argument("--raw", default=ROOT / "data" / "raw", type=Path)
    a = sub.add_parser("annotate", help="cache HGNC + GO calcium + UniProt annotations for all actors")
    a.add_argument("--raw", default=ROOT / "data" / "raw", type=Path)
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
        pmids = {r["ref"][5:] for r in read_raw(args.raw) if r["ref"].upper().startswith("PMID:")}
        fetched = pt.fetch_texts(sorted(pmids))
        print(f"{len(pmids)} cited papers, {len(fetched)} newly fetched")
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
