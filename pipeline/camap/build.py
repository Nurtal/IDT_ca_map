"""Turn raw extraction records into the canonical data files (CSV + .js mirrors)."""
import csv
import hashlib
import json
from pathlib import Path

from .nodes import (DEFAULT_CONFIG, Annotations, Resolver, Universe, load_config, module_of,
                    select_nodes)
from .pubtator import PubTator
from .schema import (DATABASE_KINDS, EVIDENCE_COLUMNS, INTERACTION_COLUMNS, LINK_TYPES,
                     LITERATURE_KINDS, NODE_COLUMNS)
from .verify import sentence_in


def short_hash(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def read_raw(raw_dir):
    records = []
    for path in sorted(Path(raw_dir).glob("*.jsonl")):
        with open(path) as f:
            for line_no, line in enumerate(f, 1):
                if line.strip():
                    r = json.loads(line)
                    r.setdefault("_origin", f"{path.name}:{line_no}")
                    records.append(r)
    return records


def interaction_key(source, target, type_):
    if type_ not in LINK_TYPES:
        raise ValueError(f"unknown link type {type_!r}")
    if not LINK_TYPES[type_]:
        source, target = sorted((source, target))
    return source, target, type_


def sentence_status(r, texts):
    sentence = r.get("sentence", "")
    if not sentence:
        return ""
    doc = texts.document(r["ref"]) if r["source_kind"] in LITERATURE_KINDS else None
    return "true" if doc and sentence_in(sentence, doc["text"]) else "false"


def build_dataset(raw_dir, out_dir, cache_dir=None, config_path=DEFAULT_CONFIG):
    config = load_config(config_path)
    resolver = Resolver(cache_dir, config)
    universe = Universe(config)
    annotations = Annotations(cache_dir)
    texts = PubTator(cache_dir or Path(out_dir) / "_no_cache")

    interactions, evidence = collect(read_raw(raw_dir), resolver, universe, texts)

    go_calcium = lambda node: bool(annotations.get(node).get("go_calcium"))  # noqa: E731
    kept, neighbours = select_nodes(universe, interactions.values(), go_calcium)
    interactions = {k: i for k, i in interactions.items() if i["source"] in kept and i["target"] in kept}
    evidence = {k: e for k, e in evidence.items() if e["interaction_id"] in interactions}

    for iid, inter in interactions.items():
        finalize_interaction(inter, evidence, go_calcium)

    nodes = [node_row(n, resolver, universe, annotations, neighbours)
             for n in sorted({x for i in interactions.values() for x in (i["source"], i["target"])})]

    tables = {
        "nodes": (NODE_COLUMNS, nodes),
        "interactions": (INTERACTION_COLUMNS, sorted(interactions.values(),
                                                     key=lambda i: i["interaction_id"])),
        "evidence": (EVIDENCE_COLUMNS, sorted(evidence.values(), key=lambda e: e["evidence_id"])),
    }
    write_tables(out_dir, tables)
    return tables


def collect(records, resolver, universe, texts):
    interactions, evidence = {}, {}
    for r in records:
        source, target, type_ = interaction_key(resolver.resolve(r["source"]),
                                                resolver.resolve(r["target"]), r["type"])
        iid = short_hash(f"{source}|{target}|{type_}")
        inter = interactions.setdefault(iid, {
            "interaction_id": iid, "source": source, "target": target, "type": type_,
            "directed": "true" if LINK_TYPES[type_] else "false",
            "_mechanisms": [], "_justifications": [], "_refs": set(), "_text_calcium": False,
        })
        add_unique(inter["_mechanisms"], r.get("mechanism", ""))
        add_unique(inter["_justifications"], r.get("justification", ""))
        inter["_refs"].add((r["source_kind"], r["ref"]))
        sentence = r.get("sentence", "")
        inter["_text_calcium"] |= universe.mentions_calcium(sentence)
        eid = short_hash(f"{iid}|{r['source_kind']}|{r['ref']}|{sentence}")
        evidence[eid] = {
            "evidence_id": eid, "interaction_id": iid, "source_kind": r["source_kind"],
            "ref": r["ref"], "doi": r.get("doi", ""), "year": r.get("year", ""),
            "first_author": r.get("first_author", ""), "sentence": sentence,
            "sentence_verified": sentence_status(r, texts),
            "species_context": r.get("species_context", "unknown"),
        }
    return interactions, evidence


def finalize_interaction(inter, evidence, go_calcium):
    iid = inter["interaction_id"]
    refs = inter.pop("_refs")
    inter["n_pubs"] = sum(1 for k, _ in refs if k in LITERATURE_KINDS)
    inter["n_db"] = sum(1 for k, _ in refs if k in DATABASE_KINDS)
    inter["n_sources"] = len(refs)
    inter["mechanism"] = " | ".join(inter.pop("_mechanisms"))
    inter["justification"] = " | ".join(inter.pop("_justifications"))
    go = go_calcium(inter["source"]) or go_calcium(inter["target"])
    text = inter.pop("_text_calcium")
    inter["calcium_evidence"] = "both" if go and text else "GO" if go else "text" if text else ""
    inter["evidence_fingerprint"] = short_hash(
        "|".join(sorted(e for e, ev in evidence.items() if ev["interaction_id"] == iid)))


def node_row(node_id, resolver, universe, annotations, neighbours):
    ann = annotations.get(node_id)
    if node_id in resolver.metabolites:
        m = resolver.metabolites[node_id]
        return {"id": node_id, "symbol": m["symbol"], "name": m["name"], "type": "metabolite",
                "module": "metabolite", "is_seed": "true",
                "synonyms": "; ".join(m.get("synonyms", [])),
                "function_summary": ann.get("function_summary", "")}
    gene = resolver.gene(node_id)
    return {
        "id": node_id, "symbol": node_id, "name": gene.get("name", ""), "type": "gene",
        "module": module_of(universe, node_id, neighbours),
        "is_seed": "true" if node_id in universe.seeds else "false",
        "uniprot": ";".join(gene.get("uniprot_ids") or []),
        "synonyms": "; ".join((gene.get("prev_symbol") or []) + (gene.get("alias_symbol") or [])),
        "function_summary": ann.get("function_summary", ""),
    }


def add_unique(items, value):
    if value and value not in items:
        items.append(value)


def write_tables(out_dir, tables):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, (columns, rows) in tables.items():
        clean = [{c: str(row.get(c, "")) for c in columns} for row in rows]
        with open(out / f"{name}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=columns)
            w.writeheader()
            w.writerows(clean)
        with open(out / f"{name}.js", "w") as f:
            f.write("window.CAMAP = window.CAMAP || {};\n")
            f.write(f"window.CAMAP.{name} = ")
            json.dump(clean, f, ensure_ascii=False, indent=1)
            f.write(";\n")
