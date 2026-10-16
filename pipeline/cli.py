#!/usr/bin/env python3
"""Pipeline entry point.

    python3 pipeline/cli.py build          # data/raw/*.jsonl -> data/{nodes,interactions,evidence}.{csv,js}
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from camap.build import build_dataset  # noqa: E402


def main(argv=None):
    p = argparse.ArgumentParser(prog="cli.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build data files from raw extraction records")
    b.add_argument("--raw", default=ROOT / "data" / "raw", type=Path)
    b.add_argument("--out", default=ROOT / "data", type=Path)
    args = p.parse_args(argv)

    if args.cmd == "build":
        tables = build_dataset(args.raw, args.out)
        for name, (_, rows) in tables.items():
            print(f"{name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
