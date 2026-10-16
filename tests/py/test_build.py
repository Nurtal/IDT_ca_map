"""Pipeline seam: raw extraction records in, canonical data files out."""
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from camap.build import build_dataset


def rec(**kw):
    base = dict(
        source="STIM1", target="STING1", type="inhibition", mechanism="ER retention",
        sentence="STIM1 retains STING at the ER.", source_kind="pubmed", ref="PMID:31511697",
        doi="10.1038/s41590-019-0485-2", year=2019, first_author="Srikanth",
        species_context="human", justification="Direct bridge between SOCE and STING.",
    )
    base.update(kw)
    return base


class BuildCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.raw = self.tmp / "raw"
        self.out = self.tmp / "out"
        self.raw.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write_raw(self, records, name="batch.jsonl"):
        with open(self.raw / name, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def build(self, **kw):
        build_dataset(self.raw, self.out, **kw)
        return {t: read_csv(self.out / f"{t}.csv") for t in ("nodes", "interactions", "evidence")}


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


class TestAggregation(BuildCase):
    def test_evidence_for_same_triplet_aggregates_into_one_interaction(self):
        self.write_raw([
            rec(),
            rec(ref="PMID:111", sentence="Another sentence."),
            rec(source_kind="signor", ref="SIGNOR-1", sentence=""),
        ])
        d = self.build()
        self.assertEqual(len(d["interactions"]), 1)
        i = d["interactions"][0]
        self.assertEqual((i["source"], i["target"], i["type"]), ("STIM1", "STING1", "inhibition"))
        self.assertEqual((i["n_sources"], i["n_pubs"], i["n_db"]), ("3", "2", "1"))
        self.assertEqual(i["directed"], "true")
        self.assertEqual(len(d["evidence"]), 3)
        self.assertTrue(all(e["interaction_id"] == i["interaction_id"] for e in d["evidence"]))

    def test_same_reference_twice_counts_once(self):
        self.write_raw([rec(), rec(sentence="Second sentence of same paper.")])
        i = self.build()["interactions"][0]
        self.assertEqual((i["n_sources"], i["n_pubs"]), ("1", "1"))

    def test_different_types_are_different_interactions(self):
        self.write_raw([rec(), rec(type="physical_binding")])
        self.assertEqual(len(self.build()["interactions"]), 2)

    def test_nodes_are_the_interaction_endpoints(self):
        self.write_raw([rec(), rec(source="ORAI1", target="STIM1", type="physical_binding")])
        symbols = sorted(n["symbol"] for n in self.build()["nodes"])
        self.assertEqual(symbols, ["ORAI1", "STIM1", "STING1"])


class TestIdentity(BuildCase):
    def test_ids_are_stable_across_runs(self):
        self.write_raw([rec(), rec(source="ORAI1", target="STIM1", type="physical_binding")])
        first = {i["interaction_id"] for i in self.build()["interactions"]}
        second = {i["interaction_id"] for i in self.build()["interactions"]}
        self.assertEqual(first, second)
        # literals from `printf 'A|B|type' | sha1sum | cut -c1-12`
        self.assertEqual(first, {"d82408bef80f", "ef02b46551ec"})

    def test_undirected_types_ignore_endpoint_order(self):
        self.write_raw([
            rec(source="ORAI1", target="STIM1", type="physical_binding"),
            rec(source="STIM1", target="ORAI1", type="physical_binding", ref="PMID:2"),
        ])
        d = self.build()
        self.assertEqual(len(d["interactions"]), 1)
        self.assertEqual(d["interactions"][0]["directed"], "false")

    def test_directed_types_keep_endpoint_order(self):
        self.write_raw([rec(), rec(source="STING1", target="STIM1")])
        self.assertEqual(len(self.build()["interactions"]), 2)


class TestJsMirrors(BuildCase):
    def test_js_mirrors_contain_the_same_rows(self):
        self.write_raw([rec()])
        d = self.build()
        js = (self.out / "interactions.js").read_text()
        prefix = "window.CAMAP = window.CAMAP || {};\nwindow.CAMAP.interactions = "
        self.assertTrue(js.startswith(prefix))
        rows = json.loads(js[len(prefix):].rstrip().rstrip(";"))
        self.assertEqual(rows[0]["interaction_id"], d["interactions"][0]["interaction_id"])


if __name__ == "__main__":
    unittest.main()
