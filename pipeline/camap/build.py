"""Turn raw extraction records into the canonical data files (CSV + .js mirrors)."""
import csv
import hashlib
import json
from pathlib import Path

from .nodes import (DEFAULT_CONFIG, Annotations, Resolver, Universe, load_config, module_of,
                    select_nodes)
from .pubtator import PubTator
from .schema import (ANIMAL_CONTEXTS, CURATED_KINDS, CURATED_NODE_FIELDS, DATABASE_KINDS,
                     EVIDENCE_COLUMNS, HUMAN_CONTEXTS,
                     INTERACTION_COLUMNS, LINK_TYPES, LITERATURE_KINDS, NODE_COLUMNS,
                     SPECIES_CONTEXTS)
from .verify import find_sentence, sentence_in


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


def source_document(r, texts):
    """The paper an evidence row quotes: the paper itself, or the one a database cites."""
    if r["source_kind"] in LITERATURE_KINDS:
        return texts.document(r["ref"])
    return texts.document(r["cited_pmid"]) if r.get("cited_pmid") else None


def evidence_sentence(r, doc, names):
    """(sentence, verified) — database rows without a sentence borrow one from the cited abstract."""
    sentence = r.get("sentence", "")
    if sentence:
        return sentence, "true" if doc and sentence_in(sentence, doc["text"]) else "false"
    if r["source_kind"] in DATABASE_KINDS and doc:
        found = find_sentence(doc["text"], names(r["_source_id"]), names(r["_target_id"]))
        if found:
            return found, "true"
    return "", ""


def load_catalogue(path):
    """The curator's gene catalogue, keyed by symbol (issue #17). Absent is fine: it only
    adds a calcium criterion and node annotations."""
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else {}


def build_dataset(raw_dir, out_dir, cache_dir=None, config_path=DEFAULT_CONFIG,
                  catalogue_path=None):
    config = load_config(config_path)
    catalogue = load_catalogue(catalogue_path or Path(out_dir) / "supp_catalogue.json")
    resolver = Resolver(cache_dir, config)
    universe = Universe(config)
    annotations = Annotations(cache_dir)
    texts = PubTator(cache_dir or Path(out_dir) / "_no_cache")

    interactions, evidence = collect(read_raw(raw_dir), resolver, universe, texts)

    go_calcium = lambda node: bool(annotations.get(node).get("go_calcium"))  # noqa: E731
    curated_calcium = lambda node: node in catalogue  # noqa: E731
    kept, neighbours, calcium = select_nodes(universe, interactions.values(), go_calcium,
                                             curated_calcium=curated_calcium)
    dropped = dropped_curated(interactions, kept, universe, neighbours, go_calcium, curated_calcium)
    interactions = {k: i for k, i in interactions.items() if i["source"] in kept and i["target"] in kept}
    evidence = {k: e for k, e in evidence.items() if e["interaction_id"] in interactions}

    evidence_ids = {}
    for eid, ev in evidence.items():
        evidence_ids.setdefault(ev["interaction_id"], []).append(eid)
    for iid, inter in interactions.items():
        finalize_interaction(inter, evidence_ids.get(iid, []), go_calcium, curated_calcium)
    link_conflicts(interactions.values())

    nodes = [node_row(n, resolver, universe, annotations, neighbours, catalogue, calcium)
             for n in sorted({x for i in interactions.values() for x in (i["source"], i["target"])})]

    tables = {
        "nodes": (NODE_COLUMNS, nodes),
        "interactions": (INTERACTION_COLUMNS, sorted(interactions.values(),
                                                     key=lambda i: i["interaction_id"])),
        "evidence": (EVIDENCE_COLUMNS, sorted(evidence.values(), key=lambda e: e["evidence_id"])),
    }
    write_tables(out_dir, tables)
    return tables, dropped


def dropped_curated(interactions, kept, universe, neighbours, go_calcium, curated_calcium):
    """Why each curated interaction did not make it into the map (issue #16).

    These rows come from the researcher, so losing one in silence would be a bug; database
    and literature rows are expected to be filtered and are not reported here.
    """
    notes = []
    for inter in sorted(interactions.values(), key=lambda i: (i["source"], i["target"])):
        if not inter.get("_curated") or (inter["source"] in kept and inter["target"] in kept):
            continue
        for node in (inter["source"], inter["target"]):
            if node in kept:
                continue
            anchors = " or ".join(sorted(universe.anchors))
            also = (f"no interaction with {anchors}"
                    if not (neighbours.get(node, set()) & universe.anchors)
                    else "not calcium-related (no GO annotation, no calcium term, not in the catalogue)")
            notes.append(f"{inter['source']} {inter['type']} {inter['target']}: {node} dropped, "
                         f"no curated link to a seed, and {also}")
    return notes


def collect(records, resolver, universe, texts):
    interactions, evidence = {}, {}
    docs = {}

    def document(r):
        key = r["ref"] if r["source_kind"] in LITERATURE_KINDS else "PMID:" + (r.get("cited_pmid") or "")
        if key not in docs:
            docs[key] = source_document(r, texts)
        return docs[key]

    for r in records:
        r["_source_id"], r["_target_id"] = resolver.resolve(r["source"]), resolver.resolve(r["target"])
        if r["_source_id"] == r["_target_id"]:
            continue
        source, target, type_ = interaction_key(r["_source_id"], r["_target_id"], r["type"])
        iid = short_hash(f"{source}|{target}|{type_}")
        inter = interactions.setdefault(iid, {
            "interaction_id": iid, "source": source, "target": target, "type": type_,
            "directed": "true" if LINK_TYPES[type_] else "false",
            "_mechanisms": [], "_justifications": [], "_refs": set(), "_text_calcium": False,
        })
        add_unique(inter["_mechanisms"], r.get("mechanism", ""))
        add_unique(inter["_justifications"], r.get("justification", ""))
        inter["_refs"].add((r["source_kind"], r["ref"]))
        inter["_curated"] = inter.get("_curated", False) or r["source_kind"] in CURATED_KINDS
        inter["_beyond_calcium"] = inter.get("_beyond_calcium", False) or bool(r.get("beyond_calcium"))
        species = r.get("species_context") or "unknown"
        if species not in SPECIES_CONTEXTS:
            raise ValueError(f"{r.get('_origin')}: unknown species_context {species!r}")
        inter["_human"] = inter.get("_human", False) or species in HUMAN_CONTEXTS
        inter["_animal"] = inter.get("_animal", False) or species in ANIMAL_CONTEXTS
        sentence, verified = evidence_sentence(r, document(r), resolver.names)
        inter["_text_calcium"] |= universe.mentions_calcium(sentence)
        eid = short_hash(f"{iid}|{r['source_kind']}|{r['ref']}|{r.get('sentence', '')}")
        evidence[eid] = {
            "evidence_id": eid, "interaction_id": iid, "source_kind": r["source_kind"],
            "ref": r["ref"], "cited_pmid": r.get("cited_pmid", ""), "doi": r.get("doi", ""), "year": r.get("year", ""),
            "first_author": r.get("first_author", ""), "sentence": sentence,
            "sentence_verified": verified,
            "species_context": species,
            "curator_note": r.get("curator_note", ""), "supp_source": r.get("supp_source", ""),
        }
    return interactions, evidence


def finalize_interaction(inter, evidence_ids, go_calcium, curated_calcium):
    refs = inter.pop("_refs")
    inter.pop("_curated", None)
    inter["beyond_calcium"] = "true" if inter.pop("_beyond_calcium", False) else "false"
    inter["n_pubs"] = sum(1 for k, _ in refs if k in LITERATURE_KINDS)
    inter["n_db"] = sum(1 for k, _ in refs if k in DATABASE_KINDS)
    inter["n_curated"] = sum(1 for k, _ in refs if k in CURATED_KINDS)
    inter["n_sources"] = len(refs)
    inter["mechanism"] = " | ".join(inter.pop("_mechanisms"))
    inter["justification"] = " | ".join(inter.pop("_justifications"))
    inter["has_human_evidence"] = "true" if inter.pop("_human") else "false"
    inter["has_animal_evidence"] = "true" if inter.pop("_animal") else "false"
    criteria = []
    if go_calcium(inter["source"]) or go_calcium(inter["target"]):
        criteria.append("GO")
    if inter.pop("_text_calcium"):
        criteria.append("text")
    if curated_calcium(inter["source"]) or curated_calcium(inter["target"]):
        criteria.append("curated")
    # "both" is kept for the historical GO+text pair so reviews made before the catalogue
    # existed still read the same.
    inter["calcium_evidence"] = "both" if criteria == ["GO", "text"] else "+".join(criteria)
    inter["evidence_fingerprint"] = short_hash("|".join(sorted(evidence_ids)))


OPPOSITES = {"activation": "inhibition", "inhibition": "activation",
             "expression_regulation_up": "expression_regulation_down",
             "expression_regulation_down": "expression_regulation_up"}


def link_conflicts(interactions):
    by_key = {(i["source"], i["target"], i["type"]): i for i in interactions}
    for i in interactions:
        other = by_key.get((i["source"], i["target"], OPPOSITES.get(i["type"])))
        i["conflict_with"] = other["interaction_id"] if other else ""


def node_row(node_id, resolver, universe, annotations, neighbours, catalogue=None, calcium=None):
    ann = annotations.get(node_id)
    # false only for what `beyond_calcium` let in: the biological end of an arm, kept on purpose
    is_calcium = "true" if (calcium or {}).get(node_id, True) else "false"
    curated = {k: v for k, v in (catalogue or {}).get(node_id, {}).items()
               if k in CURATED_NODE_FIELDS}
    if node_id in resolver.metabolites:
        m = resolver.metabolites[node_id]
        return {"id": node_id, "symbol": m["symbol"], "name": m["name"], "type": "metabolite",
                "module": "metabolite", "is_seed": "true", "calcium_related": is_calcium,
                "synonyms": "; ".join(m.get("synonyms", [])),
                "function_summary": ann.get("function_summary", ""), **curated}
    gene = resolver.gene(node_id)
    return {
        "id": node_id, "symbol": node_id, "name": gene.get("name", ""), "type": "gene",
        "module": module_of(universe, node_id, neighbours),
        "is_seed": "true" if node_id in universe.seeds else "false",
        "calcium_related": is_calcium,
        "uniprot": ";".join(gene.get("uniprot_ids") or []),
        "synonyms": "; ".join((gene.get("prev_symbol") or []) + (gene.get("alias_symbol") or [])),
        "function_summary": ann.get("function_summary", ""),
        **curated,
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
