"""PubTator3 client with a local, git-ignored document cache."""
import json
from pathlib import Path
from urllib.parse import quote

from . import http

API = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"
EXCLUDED_SECTIONS = {"REF"}
BATCH = 100


class PubTator:
    def __init__(self, cache_dir, http_get_json=http.get_json):
        self.dir = Path(cache_dir) / "pubtator"
        self.get_json = http_get_json

    # ---- texts ----

    def _path(self, pmid):
        return self.dir / f"{pmid}.json"

    def fetch_texts(self, pmids):
        """Download (full text when available) every PMID not already cached."""
        missing = [str(p) for p in pmids if not self._path(p).exists()]
        for start in range(0, len(missing), BATCH):
            chunk = missing[start:start + BATCH]
            url = f"{API}/publications/export/biocjson?pmids={','.join(chunk)}&full=true"
            for raw in self.get_json(url).get("PubTator3", []):
                self._store(simplify(raw))
        return missing

    def _store(self, doc):
        self.dir.mkdir(parents=True, exist_ok=True)
        self._path(doc["pmid"]).write_text(json.dumps(doc, ensure_ascii=False))
        if doc.get("pmcid"):
            (self.dir / f"{doc['pmcid']}.ref").write_text(doc["pmid"])

    def document(self, ref):
        """Cached document for a PMID ('123', 'PMID:123') or PMCID ('PMC123'), else None."""
        ref = str(ref)
        if ref.upper().startswith("PMID:"):
            ref = ref[5:]
        if ref.upper().startswith("PMC"):
            link = self.dir / f"{ref.upper()}.ref"
            if not link.exists():
                return None
            ref = link.read_text().strip()
        path = self._path(ref)
        return json.loads(path.read_text()) if path.exists() else None

    # ---- search ----

    def search(self, query, page=1, size=1000):
        return self.get_json(f"{API}/search/?text={quote(query)}&page={page}&size={size}")


def simplify(raw):
    passages = [p for p in raw.get("passages", [])
                if (p.get("infons", {}).get("section_type") or "").upper() not in EXCLUDED_SECTIONS]
    title = next((p["text"] for p in passages
                  if (p["infons"].get("section_type") or p["infons"].get("type", "")).upper() == "TITLE"), "")
    authors = raw.get("authors") or []
    return {
        "pmid": str(raw.get("pmid") or raw.get("id")),
        "pmcid": raw.get("pmcid") or "",
        "title": title,
        "journal": raw.get("journal") or "",
        "year": (raw.get("date") or "")[:4],
        "first_author": authors[0] if authors else "",
        "full_text": len(passages) > 2,
        "text": "\n".join(p.get("text", "") for p in passages),
    }
