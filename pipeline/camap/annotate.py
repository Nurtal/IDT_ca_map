"""Fetch node annotations (HGNC set, GO calcium terms via QuickGO, UniProt function)."""
import json
import re
import urllib.request
from pathlib import Path

from . import http
from .nodes import load_config

HGNC_URL = "https://storage.googleapis.com/public-download-files/hgnc/json/json/hgnc_complete_set.json"
QUICKGO = ("https://www.ebi.ac.uk/QuickGO/services/annotation/search?geneProductId=UniProtKB:{acc}"
           "&goId={terms}&goUsage=descendants&taxonId=9606&limit=1")
UNIPROT = "https://rest.uniprot.org/uniprotkb/{acc}.json?fields=cc_function"


def ensure_hgnc(cache_dir):
    path = Path(cache_dir) / "hgnc" / "hgnc_complete_set.json"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(HGNC_URL, headers={"User-Agent": http.USER_AGENT})
        with urllib.request.urlopen(req, timeout=300) as resp:
            path.write_bytes(resp.read())
    return path


def annotate_genes(symbols, cache_dir, http_get_json=http.get_json, config=None):
    config = config or load_config()
    terms = ",".join(config["calcium_go_terms"])
    docs = json.loads((Path(cache_dir) / "hgnc" / "hgnc_complete_set.json").read_text())["response"]["docs"]
    by_symbol = {d["symbol"]: d for d in docs}
    out_dir = Path(cache_dir) / "annotations"
    out_dir.mkdir(parents=True, exist_ok=True)
    done = 0
    for sym in sorted(set(symbols)):
        path = out_dir / f"{sym}.json"
        gene = by_symbol.get(sym)
        if path.exists() or not gene or not gene.get("uniprot_ids"):
            continue
        acc = gene["uniprot_ids"][0]
        hits = http_get_json(QUICKGO.format(acc=acc, terms=terms)).get("numberOfHits", 0)
        up = http_get_json(UNIPROT.format(acc=acc))
        path.write_text(json.dumps({"go_calcium": hits > 0, "function_summary": function_text(up)}))
        done += 1
    return done


def function_text(uniprot_json):
    for c in uniprot_json.get("comments", []):
        if c.get("commentType") == "FUNCTION" and c.get("texts"):
            text = c["texts"][0]["value"]
            return re.sub(r"\s*\((?:PubMed|ECO):[^)]*\)", "", text).strip()
    return ""
