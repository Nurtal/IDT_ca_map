"""Corpus definition, counting pass and the resumable work queue.

Corpus (consistent with the node inclusion rule — only interactions touching an
anchor or linking two level-1 seeds can survive):
  tier 0  anchor × anchor            (STIM1 × STING1, the bridge)
  tier 1  anchor × other level-1 seed
  tier 2  each anchor alone          (its partners may be any calcium-related gene)
A calcium clause is added whenever every gene of a query is on the STING side.
Seed pairs without an anchor (e.g. ITPR × RYR) are left out: they describe the
calcium toolkit itself, already covered by the interaction databases.
Within a tier, articles whose query crosses the two sides of the axis (a calcium-side
gene with a STING-side gene) come first — they are the bridge candidates — then primary
research before reviews (PubMed publication types).
"""
import itertools
import json
import re
from pathlib import Path

STATUSES = ("pending", "done", "skipped", "error")
AUTO_START = "<!-- auto:start -->"
AUTO_END = "<!-- auto:end -->"


def side(seeds, symbol):
    """Which side of the axis a seed sits on: the STING module, or everything calcium."""
    return "sting" if seeds[symbol]["module"] == "sting" else "ca"


def crosses_axis(config, symbols):
    seeds = {s["symbol"]: s for s in config["seeds"]}
    return len({side(seeds, s) for s in symbols if s in seeds}) > 1


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
        if a not in anchors and b not in anchors:
            continue
        tier = 0 if a in anchors and b in anchors else 1
        queries.append((tier, query([a, b]), crosses_axis(config, [a, b])))
    queries += [(2, query([a]), False) for a in anchors]
    return sorted(queries, key=lambda t: t[0])


def search_all(pubtator, text, page_size):
    page, hits = 1, []
    while True:
        res = pubtator.search(text, page=page, size=page_size)
        hits += res.get("results", [])
        if page >= res.get("total_pages", 1):
            return res.get("count", len(hits)), hits
        page += 1


REVIEW_TYPES = {"Review", "Systematic Review", "Meta-Analysis"}


def build_queue(config, pubtator, state_dir, page_size=1000, pubtypes=None):
    """pubtypes: callable pmids -> {pmid: [PubMed publication types]}, used to rank reviews last."""
    state_dir = Path(state_dir)
    existing = {e["pmid"]: e for e in load_queue(state_dir)}
    entries, per_query = {}, {}
    for tier, text, cross in corpus_queries(config):
        count, hits = search_all(pubtator, text, page_size)
        per_query[text] = count
        for h in hits:
            pmid = str(h["pmid"])
            e = entries.setdefault(pmid, {
                "pmid": pmid, "pmcid": h.get("pmcid", ""), "title": h.get("title", ""),
                "year": (h.get("date") or "")[:4], "tier": tier, "queries": [], "score": 0.0,
                "cross": False,
            })
            e["tier"] = min(e["tier"], tier)
            e["queries"].append(text)
            e["cross"] = e.get("cross", False) or cross
            e["score"] = max(e["score"], float(h.get("score") or 0))

    for pmid, old in existing.items():
        if pmid not in entries and old.get("status", "pending") == "pending" and not old.get("manual"):
            continue  # no longer in the corpus and never processed
        e = entries.setdefault(pmid, old)
        for key in ("status", "note", "review", "manual"):
            if key in old:
                e[key] = old[key]
    for e in entries.values():
        e.setdefault("status", "pending")
        e.setdefault("cross", False)
    if pubtypes:
        missing = [p for p, e in entries.items() if "review" not in e]
        for i in range(0, len(missing), 200):
            for pmid, types in pubtypes(missing[i:i + 200]).items():
                entries[pmid]["review"] = bool(REVIEW_TYPES & set(types))

    save_queue(state_dir, entries.values())
    report = {"total_articles": len(entries), "per_query": per_query,
              "per_tier": {t: sum(1 for e in entries.values() if e["tier"] == t) for t in (0, 1, 2)}}
    (state_dir / "corpus_counts.json").write_text(json.dumps(report, indent=1))
    return report


def priority(e):
    # a hand-picked lead comes before the whole corpus: somebody asked for it by name
    return (not e.get("manual"), e["tier"], not e.get("cross"), bool(e.get("review")),
            -e["score"], -len(e["queries"]), int(e["pmid"]))


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


def add_articles(state_dir, pmids, metadata, note=None):
    """([entries added], [pmids already there]) — hand-picked leads the searches never returned.

    A lead found in a review's text is invisible to the corpus queries, so it would otherwise be
    read without ever appearing as processed. It enters at tier 0, ahead of the corpus queue,
    and `manual` keeps `build_queue` from dropping it while it is still pending.
    """
    entries = load_queue(state_dir)
    known = {e["pmid"] for e in entries}
    added, present = [], []
    for pmid in map(str, pmids):
        if pmid in known or pmid in {e["pmid"] for e in added}:
            present.append(pmid)
            continue
        meta = metadata(pmid) or {}
        entry = {"pmid": pmid, "pmcid": meta.get("pmcid", ""), "title": meta.get("title", ""),
                 "year": meta.get("year", ""), "tier": 0, "queries": [], "score": 0.0,
                 "cross": True, "status": "pending", "review": False, "manual": True}
        if note:
            entry["note"] = note
        added.append(entry)
    save_queue(state_dir, entries + added)
    return added, present


def set_status(state_dir, pmid, status, note=None):
    set_statuses(state_dir, [pmid], status, note)


def set_statuses(state_dir, pmids, status, note=None):
    """Update several articles at once; nothing is written if any PMID is unknown."""
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}")
    entries = load_queue(state_dir)
    by_pmid = {e["pmid"]: e for e in entries}
    unknown = [p for p in map(str, pmids) if p not in by_pmid]
    if unknown:
        raise KeyError(f"not in queue: {', '.join(unknown)}")
    for p in map(str, pmids):
        by_pmid[p]["status"] = status
        if note:
            by_pmid[p]["note"] = note
    save_queue(state_dir, entries)


def next_pending(state_dir, n, tier=None, primary=False):
    """The n highest-priority pending articles, optionally restricted to one tier.

    `primary` passes over the articles PubMed types as reviews without touching their rank: once
    a tier's primary research is read, what heads the queue is a long tail of reviews that the
    protocol skips anyway, and the primary articles of the next priority band sit behind them.
    """
    return [e for e in load_queue(state_dir)
            if e["status"] == "pending" and (tier is None or e["tier"] == tier)
            and not (primary and e.get("review"))][:n]


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
