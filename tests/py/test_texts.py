"""Text fetching/caching and verbatim sentence verification."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from camap.pubtator import PubTator
from test_build import BuildCase, rec

FIXTURES = Path(__file__).parent / "fixtures" / "pubtator"


class FakeHttp:
    def __init__(self):
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        if "idconv" in url:
            return {"records": [{"pmcid": "PMC9001", "pmid": 1001, "requested-id": "PMC9001"},
                                {"pmcid": "PMC404", "requested-id": "PMC404", "status": "error"}]}
        return json.loads((FIXTURES / "export_full.json").read_text())


class TestPubTatorCache(unittest.TestCase):
    def setUp(self):
        self.cache = Path(tempfile.mkdtemp())
        self.http = FakeHttp()
        self.pt = PubTator(self.cache, http_get_json=self.http)

    def tearDown(self):
        shutil.rmtree(self.cache)

    def test_fetch_caches_documents_and_second_fetch_uses_cache(self):
        self.pt.fetch_texts(["1001", "1002"])
        self.assertEqual(len(self.http.calls), 1)
        doc = self.pt.document("1001")
        self.assertEqual(doc["pmcid"], "PMC9001")
        self.assertEqual(doc["year"], "2019")
        self.assertEqual(doc["first_author"], "Srikanth S")
        self.pt.fetch_texts(["1001", "1002"])
        self.assertEqual(len(self.http.calls), 1)

    def test_text_includes_body_but_not_references(self):
        self.pt.fetch_texts(["1001"])
        text = self.pt.document("1001")["text"]
        self.assertIn("STIM1 interacts with STING", text)
        self.assertNotIn("Ishikawa", text)

    def test_document_lookup_by_pmcid(self):
        self.pt.fetch_texts(["1001"])
        self.assertEqual(self.pt.document("PMC9001")["pmid"], "1001")

    def test_pmcids_are_converted_to_pmids_before_fetching(self):
        self.pt.fetch_texts(["PMC9001", "PMC404"])
        self.assertEqual(self.pt.document("PMC9001")["pmid"], "1001")
        self.assertIn("pmids=1001", self.http.calls[-1])
        n = len(self.http.calls)
        self.pt.fetch_texts(["PMC9001"])
        self.assertEqual(len(self.http.calls), n)

    def test_unknown_document_is_none(self):
        self.assertIsNone(self.pt.document("999"))


class TestSentenceVerification(BuildCase):
    def setUp(self):
        super().setUp()
        self.cache = self.tmp / "cache"
        PubTator(self.cache, http_get_json=FakeHttp()).fetch_texts(["1001", "1002"])

    def verified(self, **kw):
        self.write_raw([rec(**kw)])
        ev = self.build(cache_dir=self.cache)["evidence"]
        self.assertEqual(len(ev), 1, "evidence row must be kept whatever the verification result")
        return ev[0]["sentence_verified"]

    def test_exact_sentence_is_verified(self):
        self.assertEqual(self.verified(ref="PMID:1001", sentence="STIM1 deficiency results in spontaneous STING activation."), "true")

    def test_whitespace_and_typographic_variants_are_verified(self):
        self.assertEqual(self.verified(ref="PMID:1001", sentence='We found that  STIM1 interacts\nwith STING via its "dimerization" domain.'), "true")

    def test_pmc_reference_resolves_to_the_same_text(self):
        self.assertEqual(self.verified(source_kind="pmc", ref="PMC9001", sentence="Loss of STIM1 in human cells enhances type I IFN expression."), "true")

    def test_paraphrase_is_not_verified(self):
        self.assertEqual(self.verified(ref="PMID:1001", sentence="STIM1 loss activates STING."), "false")

    def test_sentence_from_uncached_paper_is_not_verified(self):
        self.assertEqual(self.verified(ref="PMID:42", sentence="STIM1 deficiency results in spontaneous STING activation."), "false")

    def test_reference_section_does_not_count(self):
        self.assertEqual(self.verified(ref="PMID:1001", sentence="STING regulates intracellular DNA-mediated innate immune signalling."), "false")

    def test_no_sentence_leaves_status_empty(self):
        self.assertEqual(self.verified(source_kind="signor", ref="SIGNOR-1", sentence=""), "")


if __name__ == "__main__":
    unittest.main()
