"""Annotation fetcher: HGNC + QuickGO + UniProt responses -> annotation cache."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from camap.annotate import annotate_genes
from camap.nodes import Annotations

HGNC = Path(__file__).parent / "fixtures" / "cache" / "hgnc"


class FakeHttp:
    def __init__(self):
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        if "QuickGO" in url:
            return {"numberOfHits": 12 if "Q13586" in url else 0}
        if "rest.uniprot.org" in url:
            return {"comments": [{"commentType": "FUNCTION",
                                  "texts": [{"value": "Plays a role in SOCE (PubMed:123)."}]}]}
        raise AssertionError(url)


class TestAnnotate(unittest.TestCase):
    def setUp(self):
        self.cache = Path(tempfile.mkdtemp())
        shutil.copytree(HGNC, self.cache / "hgnc")
        self.http = FakeHttp()

    def tearDown(self):
        shutil.rmtree(self.cache)

    def test_annotations_are_fetched_once_and_cached(self):
        annotate_genes(["STIM1", "STING1"], self.cache, http_get_json=self.http)
        a = Annotations(self.cache)
        self.assertTrue(a.get("STIM1")["go_calcium"])
        self.assertFalse(a.get("STING1")["go_calcium"])
        self.assertEqual(a.get("STIM1")["function_summary"], "Plays a role in SOCE.")
        n = len(self.http.calls)
        annotate_genes(["STIM1", "STING1"], self.cache, http_get_json=self.http)
        self.assertEqual(len(self.http.calls), n)

    def test_genes_unknown_to_hgnc_are_skipped(self):
        annotate_genes(["NOTAGENE"], self.cache, http_get_json=self.http)
        self.assertEqual(self.http.calls, [])
        self.assertEqual(Annotations(self.cache).get("NOTAGENE"), {})


if __name__ == "__main__":
    unittest.main()
