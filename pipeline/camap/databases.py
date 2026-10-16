"""Interaction databases -> raw evidence records (same format as literature extraction).

Each adapter is a pure converter (tested on recorded payloads); the fetch_* helpers do the I/O.
"""
import os
import re
from urllib.parse import quote

from . import http

SIGNOR_URL = "https://signor.uniroma2.it/getData.php?organism=9606&id={acc}"
OMNIPATH_URL = ("https://omnipathdb.org/interactions?partners={symbols}&genesymbols=yes"
                "&fields=sources,references&organisms=9606&format=json")
INTACT_URL = ("https://www.ebi.ac.uk/Tools/webservices/psicquic/intact/webservices/current/search/query/"
              "identifier:{acc}?format=tab25")
BIOGRID_URL = ("https://webservice.thebiogrid.org/interactions/?searchNames=true&geneList={symbols}"
               "&taxId=9606&includeInteractors=true&format=json&accessKey={key}")

TAXA = {"9606": "human", "10090": "mouse", "10116": "rat"}


def species(*taxids):
    names = {TAXA.get(str(t).strip(), "other") for t in taxids if str(t).strip()}
    if not names:
        return "unknown"
    return names.pop() if len(names) == 1 else "other"


def record(source, target, type_, kind, ref, **kw):
    r = {"source": source, "target": target, "type": type_, "source_kind": kind, "ref": ref,
         "mechanism": "", "sentence": "", "cited_pmid": "", "doi": "", "year": "", "first_author": "",
         "species_context": "unknown", "justification": ""}
    r.update(kw)
    return r


# ---------- SIGNOR ----------

SIGNOR_KEEP_TYPES = {"protein", "smallmolecule", "chemical"}
SIGNOR_MECHANISMS = {
    "phosphorylation": "phosphorylation",
    "ubiquitination": "ubiquitination",
    "relocalization": "translocation/trafficking",
}


def signor_type(effect, mechanism):
    effect, mechanism = effect.lower(), mechanism.lower()
    if effect == "form complex":
        return "physical_binding"
    if mechanism in SIGNOR_MECHANISMS:
        return SIGNOR_MECHANISMS[mechanism]
    up, down = effect.startswith("up-regulates"), effect.startswith("down-regulates")
    if "by expression" in effect or mechanism == "transcriptional regulation":
        if up:
            return "expression_regulation_up"
        if down:
            return "expression_regulation_down"
    if up:
        return "activation"
    if down:
        return "inhibition"
    return "unknown_regulation"


def signor_records(tsv):
    out = []
    for line in tsv.splitlines():
        c = line.split("\t")
        if len(c) < 27 or c[0] == "ENTITYA" or c[1] not in SIGNOR_KEEP_TYPES or c[5] not in SIGNOR_KEEP_TYPES:
            continue
        if c[0] == c[4]:
            continue
        out.append(record(
            c[0], c[4], signor_type(c[8], c[9]), "signor", c[26],
            mechanism=" ".join(x for x in (c[8], c[9], c[10]) if x).strip(),
            sentence=c[25].strip(), cited_pmid=c[21].strip() if c[21].strip().isdigit() else "",
            species_context=species(c[12]) if c[12].strip() else "unknown"))
    return out


# ---------- OmniPath ----------

def omnipath_records(rows):
    out = []
    for r in rows:
        a, b = r["source_genesymbol"], r["target_genesymbol"]
        if a == b:
            continue
        if not r.get("is_directed"):
            types = ["physical_binding"]
        else:
            types = [t for t, flag in (("activation", r.get("is_stimulation")),
                                       ("inhibition", r.get("is_inhibition"))) if flag] or ["unknown_regulation"]
        refs = [x.split(":", 1)[1] for x in (r.get("references") or "").split(";") if ":" in x]
        pmid = next((p for p in refs if p.isdigit()), "")
        for t in types:
            out.append(record(a, b, t, "omnipath", f"OmniPath:{a}>{b}", cited_pmid=pmid,
                              mechanism="OmniPath sources: " + ", ".join(r.get("sources") or []),
                              species_context="human"))
    return out


# ---------- IntAct (PSICQUIC MITAB 2.5) ----------

def _gene_name(aliases):
    m = re.search(r"uniprotkb:([^|(]+)\(gene name\)", aliases)
    return m.group(1) if m else ""


def intact_records(mitab):
    out = []
    for line in mitab.splitlines():
        c = line.split("\t")
        if len(c) < 14:
            continue
        a, b = _gene_name(c[4]), _gene_name(c[5])
        if not a or not b or a == b:
            continue
        pmid = next(iter(re.findall(r"pubmed:(\d+)", c[8])), "")
        ref = next(iter(re.findall(r"intact:(EBI-\d+)", c[13])), "")
        author = re.match(r"(.*?)\s*\((\d{4})\)", c[7])
        method = next(iter(re.findall(r"\(([^)]*)\)", c[6])), "")
        taxa = [t.split("(")[0] for t in (c[9].split("|")[0][6:], c[10].split("|")[0][6:])]
        out.append(record(a, b, "physical_binding", "intact", ref, cited_pmid=pmid,
                          first_author=author.group(1) if author else "",
                          year=author.group(2) if author else "",
                          mechanism=method, species_context=species(*taxa)))
    return out


# ---------- BioGRID ----------

def biogrid_records(payload):
    out = []
    for r in payload.values():
        if r.get("EXPERIMENTAL_SYSTEM_TYPE") != "physical":
            continue
        a, b = r["OFFICIAL_SYMBOL_A"], r["OFFICIAL_SYMBOL_B"]
        if a == b:
            continue
        author = re.match(r"(.*?)\s*\((\d{4})\)", r.get("PUBMED_AUTHOR") or "")
        out.append(record(a, b, "physical_binding", "biogrid", f"BIOGRID:{r['BIOGRID_INTERACTION_ID']}",
                          cited_pmid=str(r.get("PUBMED_ID") or ""), mechanism=r.get("EXPERIMENTAL_SYSTEM", ""),
                          first_author=author.group(1) if author else "",
                          year=author.group(2) if author else "",
                          species_context=species(r.get("ORGANISM_A"), r.get("ORGANISM_B"))))
    return out


# ---------- fetchers ----------

def fetch_all(genes, get_text=http.get_text, get_json=http.get_json, biogrid_key=None):
    """genes: list of (symbol, uniprot accession). Returns {source_kind: [records]} and warnings."""
    out, warnings = {"signor": [], "omnipath": [], "intact": [], "biogrid": []}, []
    for sym, acc in genes:
        if acc:
            out["signor"] += signor_records(get_text(SIGNOR_URL.format(acc=acc)))
            out["intact"] += intact_records(get_text(INTACT_URL.format(acc=quote(acc))))
    symbols = [s for s, _ in genes]
    for start in range(0, len(symbols), 20):
        chunk = ",".join(symbols[start:start + 20])
        out["omnipath"] += omnipath_records(get_json(OMNIPATH_URL.format(symbols=chunk)))
    key = biogrid_key if biogrid_key is not None else os.environ.get("BIOGRID_ACCESS_KEY", "")
    if key:
        for start in range(0, len(symbols), 20):
            chunk = "|".join(symbols[start:start + 20])
            out["biogrid"] += biogrid_records(get_json(BIOGRID_URL.format(symbols=quote(chunk), key=key)))
    else:
        warnings.append("BioGRID skipped: set BIOGRID_ACCESS_KEY (free at https://webservice.thebiogrid.org)")
    return out, warnings
