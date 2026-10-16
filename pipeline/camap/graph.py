"""kept_interactions.csv (exported by the review app) -> data file for the graph page."""
import csv
import json
from pathlib import Path

from .schema import INTERACTION_COLUMNS

REQUIRED = {"interaction_id", "source", "target", "type", "directed", "decision"}


def build_graph(kept_csv, out_js):
    with open(kept_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{kept_csv}: missing columns {sorted(missing)}")
        rows = [r for r in reader if r["decision"] == "keep"]
    columns = [c for c in INTERACTION_COLUMNS if c in rows[0]] if rows else INTERACTION_COLUMNS
    extra = ["decision", "comment", "reviewer", "reviewed_at"]
    clean = [{c: r.get(c, "") for c in columns + extra} for r in rows]
    out = Path(out_js)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.CAMAP = window.CAMAP || {};\nwindow.CAMAP.kept = ")
        json.dump(clean, f, ensure_ascii=False, indent=1)
        f.write(";\n")
    return len(clean)
