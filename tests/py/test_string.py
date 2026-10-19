"""Pipeline seam: STRING as a score annotation on existing edges, never as an edge source.

Story 22 of issue #1: "I want STRING used only as a score annotation, not as an edge source,
so that co-expression noise does not flood the graph."
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from camap.string import fetch_scores, load_scores, score_of

NETWORK = [
    {"preferredName_A": "STIM1", "preferredName_B": "ORAI1", "score": 0.999},
    {"preferredName_A": "STING1", "preferredName_B": "TBK1", "score": 0.986},
    {"preferredName_A": "stim1", "preferredName_B": "STING1", "score": 0.42},
]


class FakeHttp:
    def __init__(self, rows=NETWORK):
        self.rows = rows
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        return self.rows

    def identifiers(self):
        return parse_qs(urlparse(self.urls[0]).query)["identifiers"][0].split("%0d")


class StringCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)


class TestFetch(StringCase):
    def test_one_request_asks_for_every_gene_and_caches_the_pairwise_scores(self):
        http = FakeHttp()
        scores = fetch_scores(["STIM1", "ORAI1", "STING1", "TBK1"], self.tmp, http_get_json=http)
        self.assertEqual(len(http.urls), 1)
        self.assertEqual(score_of(scores, "STIM1", "ORAI1"), 0.999)
        # the cache key is the pair sorted, so one entry answers both directions
        self.assertEqual(json.loads((self.tmp / "string" / "network.json").read_text())["ORAI1|STIM1"],
                         0.999)

    def test_a_score_is_symmetric_and_case_insensitive(self):
        scores = fetch_scores(["STIM1", "STING1"], self.tmp, http_get_json=FakeHttp())
        self.assertEqual(score_of(scores, "STING1", "STIM1"), 0.42)

    def test_metabolites_and_unknown_pairs_have_no_score(self):
        scores = fetch_scores(["STIM1"], self.tmp, http_get_json=FakeHttp())
        self.assertIsNone(score_of(scores, "STIM1", "CHEBI:29108"))
        self.assertIsNone(score_of(scores, "STIM1", "GPX4"))

    def test_a_second_run_reuses_the_cache_instead_of_asking_again(self):
        http = FakeHttp()
        fetch_scores(["STIM1", "ORAI1"], self.tmp, http_get_json=http)
        again = fetch_scores(["STIM1", "ORAI1"], self.tmp, http_get_json=http)
        self.assertEqual(len(http.urls), 1)
        self.assertEqual(score_of(again, "STIM1", "ORAI1"), 0.999)

    def test_a_new_gene_refreshes_the_cache(self):
        http = FakeHttp()
        fetch_scores(["STIM1", "ORAI1"], self.tmp, http_get_json=http)
        fetch_scores(["STIM1", "ORAI1", "TBK1"], self.tmp, http_get_json=http)
        self.assertEqual(len(http.urls), 2)

    def test_chebi_ids_are_never_sent_to_string(self):
        http = FakeHttp()
        fetch_scores(["STIM1", "CHEBI:29108"], self.tmp, http_get_json=http)
        self.assertNotIn("CHEBI:29108", http.identifiers())

    def test_an_absent_cache_reads_as_no_scores_at_all(self):
        self.assertEqual(load_scores(self.tmp), {})
        self.assertIsNone(score_of(load_scores(self.tmp), "STIM1", "ORAI1"))


if __name__ == "__main__":
    unittest.main()
