"""Reading aid for extraction sessions: the sentences of a cached paper worth reading.

A candidate sentence names an anchor (STIM1 / STING1, any alias) together with either
another seed, a calcium term, or an interaction verb. The extractor still reads the
title + abstract in full; candidates point at where the full-text claims are.
"""
import re

from .verify import _SENTENCE_SPLIT

VERBS = re.compile(
    r"(?i)\b(interact\w*|bind\w*|bound|associat\w*|phosphorylat\w*|ubiquitin\w*|activat\w*|inhibit\w*|"
    r"regulat\w*|traffick\w*|translocat\w*|complex\w*|recruit\w*|promot\w*|suppress\w*|degrad\w*|"
    r"co-?localiz\w*|puncta|gating|coupl\w*|block\w*|abolish\w*|impair\w*|enhanc\w*|reduc\w*)\b")


def _pattern(names):
    alts = sorted({re.escape(n) for n in names if len(n) >= 3}, key=len, reverse=True)
    return re.compile(r"(?<![\w-])(?:" + "|".join(alts) + r")(?![\w-])", re.I)


def candidate_sentences(doc, anchor_names, seed_names, calcium_pattern, limit=60):
    """-> list of (sentence, tags) in text order, de-duplicated, at most `limit`."""
    anchor, seed, calcium = _pattern(anchor_names), _pattern(seed_names), re.compile(calcium_pattern)
    seen, out = set(), []
    for s in _SENTENCE_SPLIT.split(doc["text"]):
        s = s.strip()
        if len(s) < 30 or len(s) > 1500 or s in seen or not anchor.search(s):
            continue
        tags = [t for t, p in (("seed", seed), ("Ca", calcium), ("verb", VERBS)) if p.search(s)]
        hits = {m.group(0).upper() for m in anchor.finditer(s)}
        if len(hits) > 1:
            tags.insert(0, "anchors")
        if tags:
            seen.add(s)
            out.append((s, tags))
    # strongest first when we must cut: anchor pairs, then seed, then calcium
    if len(out) > limit:
        rank = {s: i for i, (s, _) in enumerate(out)}
        out = sorted(out, key=lambda st: (-len(st[1]), rank[st[0]]))[:limit]
        out.sort(key=lambda st: rank[st[0]])
    return out
