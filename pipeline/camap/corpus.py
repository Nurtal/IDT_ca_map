"""Corpus definition, counting pass and the resumable work queue.

Corpus (consistent with the node inclusion rule — only interactions touching an
anchor or linking two level-1 seeds can survive):
  tier 0  anchor × anchor            (STIM1 × STING1, the bridge)
  tier 1  level-1 seed × level-1 seed
  tier 2  each anchor alone          (its partners may be any calcium-related gene)
A calcium clause is added whenever every gene of a query is on the STING side.
"""
import itertools
import json
import re
from pathlib import Path

STATUSES = ("pending", "done", "skipped", "error")
AUTO_START = "<!-- auto:start -->"
AUTO_END = "<!-- auto:end -->"


def corpus_queries(config):
    calcium = config.get("calcium_query", "(calcium OR Ca2+)")
    seeds = {s["symbol"]: s for s in config["seeds"]}
    anchors = config["anchors"]

    def query(symbols):
        q = " AND ".join(f"@GENE_{s}" for s in symbols)
        if all(seeds[s]["module"] == "sting" for s in symbols):
            q += f" AND {calcium}"
        return q

    level1 = [s["symbol"] for s in config["seeds"] if s["level"] == 1]
    queries = []
    for a, b in itertools.combinations(level1, 2):
        tier = 0 if a in anchors and b in anchors else 1
        queries.append((tier, query([a, b])))
    queries += [(2, query([a])) for a in anchors]
    return sorted(queries, key=lambda t: t[0])


def search_all(pubtator, text, page_size):
    page, hits = 1, []
    while True:
        res = pubtator.search(text, page=page, size=page_size)
        hits += res.get("results", [])
        if page >= res.get("total_pages", 1):
            return res.get("count", len(hits)), hits
        page += 1


def build_queue(config, pubtator, state_dir, page_size=1000):
    state_dir = Path(state_dir)
    existing = {e["pmid"]: e for e in load_queue(state_dir)}
    entries, per_query = {}, {}
    for tier, text in corpus_queries(config):
        count, hits = search_all(pubtator, text, page_size)
        per_query[text] = count
        for h in hits:
            pmid = str(h["pmid"])
            e = entries.setdefault(pmid, {
                "pmid": pmid, "pmcid": h.get("pmcid", ""), "title": h.get("title", ""),
                "year": (h.get("date") or "")[:4], "tier": tier, "queries": [], "score": 0.0,
            })
            e["tier"] = min(e["tier"], tier)
            e["queries"].append(text)
            e["score"] = max(e["score"], float(h.get("score") or 0))

    for pmid, old in existing.items():
        e = entries.setdefault(pmid, old)
        e["status"] = old.get("status", "pending")
        if old.get("note"):
            e["note"] = old["note"]
    for e in entries.values():
        e.setdefault("status", "pending")

    save_queue(state_dir, entries.values())
    report = {"total_articles": len(entries), "per_query": per_query,
              "per_tier": {t: sum(1 for e in entries.values() if e["tier"] == t) for t in (0, 1, 2)}}
    (state_dir / "corpus_counts.json").write_text(json.dumps(report, indent=1))
    return report


def priority(e):
    return (e["tier"], -len(e["queries"]), -e["score"], int(e["pmid"]))


def queue_path(state_dir):
    return Path(state_dir) / "queue.jsonl"


def load_queue(state_dir):
    path = queue_path(state_dir)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def save_queue(state_dir, entries):
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    ordered = sorted(entries, key=priority)
    queue_path(state_dir).write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in ordered))
    write_progress(state_dir, ordered)


def set_status(state_dir, pmid, status, note=None):
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}")
    entries = load_queue(state_dir)
    for e in entries:
        if e["pmid"] == str(pmid):
            e["status"] = status
            if note:
                e["note"] = note
            break
    else:
        raise KeyError(pmid)
    save_queue(state_dir, entries)


def next_pending(state_dir, n):
    return [e for e in load_queue(state_dir) if e["status"] == "pending"][:n]


def write_progress(state_dir, ordered):
    counts = {s: sum(1 for e in ordered if e["status"] == s) for s in STATUSES}
    nxt = next((e for e in ordered if e["status"] == "pending"), None)
    tiers = {t: [e for e in ordered if e["tier"] == t] for t in (0, 1, 2)}
    tier_lines = "\n".join(
        f"- tier {t}: {sum(1 for e in es if e['status'] != 'pending')}/{len(es)} processed"
        for t, es in tiers.items())
    auto = f"""{AUTO_START}
## Status (generated)

{len(ordered)} articles in queue: {counts['done']} done, {counts['pending']} pending, {counts['skipped']} skipped, {counts['error']} error.

{tier_lines}

{"Next article: PMID " + nxt["pmid"] + " — " + nxt["title"] if nxt else "Queue empty: extraction complete."}
{AUTO_END}"""
    path = Path(state_dir) / "PROGRESS.md"
    if path.exists():
        text = path.read_text()
        text = re.sub(re.escape(AUTO_START) + ".*?" + re.escape(AUTO_END), lambda _: auto, text, flags=re.S)
    else:
        text = f"# Extraction progress\n\nSee docs/EXTRACTION_PROTOCOL.md for the session procedure.\n\n{auto}\n"
    path.write_text(text)
