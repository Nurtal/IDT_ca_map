"""Corpus counting and the resumable work queue."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from camap.corpus import build_queue, load_queue, set_status, set_statuses
from camap.pubtator import PubTator

CONFIG = {
    "anchors": ["STIM1", "STING1"],
    "calcium_query": "(calcium OR Ca2+)",
    "seeds": [
        {"symbol": "STIM1", "module": "soce", "level": 1},
        {"symbol": "ORAI1", "module": "soce", "level": 1},
        {"symbol": "STING1", "module": "sting", "level": 1},
        {"symbol": "CGAS", "module": "sting", "level": 1},
        {"symbol": "PPP3CA", "module": "effectors", "level": 2},
    ],
}

# query text -> list of (pmid, score); STIM1 alone spans two pages of 2
RESULTS = {
    "@GENE_STIM1 AND @GENE_STING1": [("10", 50.0)],
    "@GENE_STIM1 AND @GENE_ORAI1": [("20", 40.0), ("10", 30.0)],
    "@GENE_ORAI1 AND @GENE_STING1": [],
    "@GENE_STIM1": [("30", 90.0), ("20", 10.0), ("10", 5.0), ("40", 80.0)],
    "@GENE_STING1 AND (calcium OR Ca2+)": [("50", 70.0), ("10", 1.0)],
}
PAGE = 2


class FakeSearch:
    def __init__(self, results=RESULTS):
        self.results = results
        self.queries = []

    def __call__(self, url):
        qs = parse_qs(urlparse(url).query)
        text, page = qs["text"][0], int(qs.get("page", ["1"])[0])
        self.queries.append(text)
        hits = self.results.get(text, [])
        chunk = hits[(page - 1) * PAGE: page * PAGE]
        return {"count": len(hits), "total_pages": max(1, -(-len(hits) // PAGE)), "current": page,
                "results": [{"pmid": int(p), "title": f"T{p}", "date": "2020-01-01T00:00:00Z", "score": s}
                            for p, s in chunk]}


class FakePubmed:
    """pmids -> {pmid: [publication types]}; unknown PMIDs are plain journal articles."""
    def __init__(self, types):
        self.types = types
        self.calls = []

    def __call__(self, pmids):
        self.calls.append(list(pmids))
        return {p: self.types.get(p, ["Journal Article"]) for p in pmids}


class CorpusCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.state = self.tmp / "state"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_build(self, results=RESULTS, pubmed=None):
        http = FakeSearch(results)
        report = build_queue(CONFIG, PubTator(self.tmp / "cache", http_get_json=http), self.state,
                             page_size=PAGE, pubtypes=pubmed)
        return report, http


class TestQueue(CorpusCase):
    def test_queries_cover_anchors_and_anchor_seed_pairs_with_calcium_when_only_sting_side(self):
        _, http = self.run_build()
        self.assertEqual(set(http.queries), set(RESULTS) | {
            "@GENE_STIM1 AND @GENE_CGAS",
            "@GENE_STING1 AND @GENE_CGAS AND (calcium OR Ca2+)",
        })

    def test_seed_pairs_without_an_anchor_are_not_queried(self):
        _, http = self.run_build()
        self.assertNotIn("@GENE_ORAI1 AND @GENE_CGAS", http.queries)

    def test_pending_articles_out_of_corpus_are_dropped_but_processed_ones_kept(self):
        self.run_build()
        set_status(self.state, "40", "done")
        fewer = dict(RESULTS, **{"@GENE_STIM1": [("30", 90.0)], "@GENE_STING1 AND (calcium OR Ca2+)": []})
        self.run_build(fewer)
        q = {e["pmid"]: e["status"] for e in load_queue(self.state)}
        self.assertNotIn("50", q)
        self.assertEqual(q["40"], "done")

    def test_reviews_come_after_primary_research_within_a_tier(self):
        pubmed = FakePubmed({"30": ["Journal Article", "Review"]})
        self.run_build(pubmed=pubmed)
        q = load_queue(self.state)
        self.assertEqual([e["pmid"] for e in q], ["10", "20", "40", "50", "30"])
        self.assertTrue(next(e for e in q if e["pmid"] == "30")["review"])
        asked = len(pubmed.calls)
        self.run_build(pubmed=pubmed)
        self.assertEqual(len(pubmed.calls), asked, "publication types are cached in the queue")

    def test_priority_bridge_first_then_seed_pairs_then_anchors_by_score(self):
        self.run_build()
        self.assertEqual([e["pmid"] for e in load_queue(self.state)], ["10", "20", "30", "40", "50"])

    def test_report_counts_unique_articles_and_hits_per_query(self):
        report, _ = self.run_build()
        self.assertEqual(report["total_articles"], 5)
        self.assertEqual(report["per_query"]["@GENE_STIM1"], 4)
        counts = json.loads((self.state / "corpus_counts.json").read_text())
        self.assertEqual(counts["total_articles"], 5)

    def test_rebuild_is_idempotent_and_keeps_statuses(self):
        self.run_build()
        set_status(self.state, "20", "done")
        set_status(self.state, "40", "skipped", note="review article")
        more = dict(RESULTS, **{"@GENE_STIM1": RESULTS["@GENE_STIM1"] + [("60", 1.0)]})
        self.run_build(more)
        q = {e["pmid"]: e for e in load_queue(self.state)}
        self.assertEqual(len(q), 6)
        self.assertEqual(q["20"]["status"], "done")
        self.assertEqual((q["40"]["status"], q["40"]["note"]), ("skipped", "review article"))
        self.assertEqual(q["60"]["status"], "pending")

    def test_batch_status_update_is_all_or_nothing(self):
        self.run_build()
        with self.assertRaises(KeyError):
            set_statuses(self.state, ["10", "999", "20"], "done")
        self.assertTrue(all(e["status"] == "pending" for e in load_queue(self.state)))
        set_statuses(self.state, ["10", "20"], "done", note="batch 1")
        q = {e["pmid"]: e for e in load_queue(self.state)}
        self.assertEqual((q["10"]["status"], q["20"]["note"]), ("done", "batch 1"))

    def test_bridge_crossing_articles_come_before_same_side_ones(self):
        results = {
            "@GENE_STIM1 AND @GENE_ORAI1": [("20", 90.0)],          # calcium side only
            "@GENE_STIM1 AND @GENE_CGAS": [("30", 10.0)],           # crosses to the STING side
            "@GENE_ORAI1 AND @GENE_STING1": [("40", 20.0)],         # crosses the other way
        }
        self.run_build(dict.fromkeys(RESULTS, []) | results)
        q = {e["pmid"]: e for e in load_queue(self.state)}
        self.assertEqual([p for p in q if q[p]["tier"] == 1], ["40", "30", "20"])
        self.assertTrue(q["30"]["cross"])
        self.assertFalse(q["20"]["cross"])

    def test_next_pending_can_be_restricted_to_one_tier(self):
        from camap.corpus import next_pending
        self.run_build()
        self.assertEqual([e["pmid"] for e in next_pending(self.state, 5, tier=2)], ["30", "40", "50"])
        self.assertEqual([e["pmid"] for e in next_pending(self.state, 5, tier=0)], ["10"])
        self.assertEqual(len(next_pending(self.state, 5)), 5)

    def test_progress_note_reports_state_and_next_step(self):
        self.run_build()
        set_status(self.state, "10", "done")
        note = (self.state / "PROGRESS.md").read_text()
        self.assertIn("1 done", note)
        self.assertIn("4 pending", note)
        self.assertIn("Next article: PMID 20", note)

    def test_progress_note_keeps_manual_notes(self):
        self.run_build()
        path = self.state / "PROGRESS.md"
        path.write_text(path.read_text() + "\n## Session notes\nStopped after batch 3.\n")
        set_status(self.state, "10", "done")
        self.assertIn("Stopped after batch 3.", path.read_text())


if __name__ == "__main__":
    unittest.main()
