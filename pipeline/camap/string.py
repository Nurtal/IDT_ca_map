"""STRING scores as an annotation on edges we already have (story 22 of issue #1).

STRING is never an edge source: its functional-association scores mix co-expression, text mining
and transfers between species, which would flood a curated map. What it is good for is a second
opinion on an edge somebody else found — "STRING also puts these two together, at 0.93".
"""
import json
from pathlib import Path
from urllib.parse import quote

from . import http

API = ("https://string-db.org/api/json/network?identifiers={ids}&species=9606"
       "&caller_identity=IDT_ca_map")


def network_path(cache_dir):
    return Path(cache_dir) / "string" / "network.json"


def _key(a, b):
    return "|".join(sorted((a.upper(), b.upper())))


def genes_only(node_ids):
    """STRING knows genes; a metabolite id would be a wasted identifier in the query."""
    return sorted({n.upper() for n in node_ids if ":" not in n})


def parse_network(rows):
    """STRING's network rows -> {"A|B": combined score}, symmetric and upper-cased."""
    scores = {}
    for row in rows:
        a, b = row.get("preferredName_A"), row.get("preferredName_B")
        if not a or not b:
            continue
        score = float(row.get("score") or 0)
        key = _key(a, b)
        scores[key] = max(scores.get(key, 0.0), score)
    return scores


def load_scores(cache_dir):
    path = network_path(cache_dir)
    return json.loads(path.read_text()) if path.exists() else {}


def score_of(scores, a, b):
    """The combined score of a pair, or None when STRING says nothing about it."""
    return scores.get(_key(a, b))


def fetch_scores(node_ids, cache_dir, http_get_json=http.get_json):
    """Scores among `node_ids`, from one request, cached until the gene set changes.

    The cache records which genes were asked for: a new actor in the map means the answer is
    incomplete, so the whole network is fetched again rather than patched.
    """
    genes = genes_only(node_ids)
    path = network_path(cache_dir)
    if path.exists():
        cached = json.loads(path.read_text())
        if cached.get("_genes") == genes:
            return {k: v for k, v in cached.items() if not k.startswith("_")}
    rows = http_get_json(API.format(ids=quote("\r".join(genes), safe=""))) if genes else []
    scores = parse_network(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**scores, "_genes": genes}, indent=1, sort_keys=True))
    return scores
