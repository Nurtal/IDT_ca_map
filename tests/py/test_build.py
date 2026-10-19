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




def curated(**kw):
    base = dict(
        source="ALG2", target="STING1", type="inhibition", source_kind="curated",
        ref="DOI:10.1016/j.immuni.2014.11.011", doi="10.1016/j.immuni.2014.11.011",
        mechanism="Inhibits STING trafficking", curator_note="Inhibits STING trafficking",
        curator_symbol="ALG2", species_context="unknown",
        justification="Curated by the researcher as a STING1 interactor.",
        supp_source="interactome STING.xlsx/interactors/row 2",
    )
    base.update(kw)
    return base


class TestCuratedEvidence(BuildCase):
    """Issue #16: the curator's spreadsheets are a source of their own."""

    def write_catalogue(self, entries):
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "supp_catalogue.json").write_text(json.dumps(entries))

    def test_a_curated_row_becomes_an_interaction_counted_as_curated(self):
        self.write_catalogue({"ALG2": {}})
        self.write_raw([curated()])
        i = self.build()["interactions"][0]
        self.assertEqual((i["source"], i["target"], i["type"]), ("ALG2", "STING1", "inhibition"))
        self.assertEqual((i["n_sources"], i["n_pubs"], i["n_db"], i["n_curated"]), ("1", "0", "0", "1"))

    def test_the_curator_note_travels_on_the_evidence_row_and_carries_no_warning(self):
        self.write_catalogue({"ALG2": {}})
        self.write_raw([curated()])
        e = self.build()["evidence"][0]
        self.assertEqual(e["curator_note"], "Inhibits STING trafficking")
        self.assertEqual(e["sentence"], "")
        # an empty verification status means "no quote to check", not "quote not found"
        self.assertEqual(e["sentence_verified"], "")

    def test_the_catalogue_satisfies_the_calcium_half_of_the_inclusion_rule(self):
        self.write_catalogue({"ALG2": {"ca_functionality": "Ca2+ binding"}})
        self.write_raw([curated()])
        d = self.build()
        self.assertEqual(sorted(n["id"] for n in d["nodes"]), ["ALG2", "STING1"])
        self.assertEqual(d["interactions"][0]["calcium_evidence"], "curated")

    def test_a_partner_outside_the_catalogue_still_needs_GO_or_a_calcium_sentence(self):
        self.write_catalogue({"SOMETHING_ELSE": {}})
        self.write_raw([curated()])
        self.assertEqual(self.build()["interactions"], [])

    def test_catalogue_and_GO_criteria_are_both_reported(self):
        cache = self.tmp / "cache" / "annotations"
        cache.mkdir(parents=True)
        (cache / "ALG2.json").write_text(json.dumps({"go_calcium": True}))
        self.write_catalogue({"ALG2": {}})
        self.write_raw([curated()])
        i = self.build(cache_dir=self.tmp / "cache")["interactions"][0]
        self.assertEqual(i["calcium_evidence"], "GO+curated")

    def test_catalogue_annotations_land_on_the_node(self):
        self.write_catalogue({"ALG2": {"localization": "ER membrane", "genecards": "GC02P127061",
                                       "ca_functionality": "Ca2+ binding"}})
        self.write_raw([curated()])
        node = next(n for n in self.build()["nodes"] if n["id"] == "ALG2")
        self.assertEqual(node["localization"], "ER membrane")
        self.assertEqual(node["genecards"], "GC02P127061")
        self.assertEqual(node["ca_functionality"], "Ca2+ binding")


class TestDropReport(BuildCase):
    """Issue #16: a curated row the inclusion rule drops must say so, with its reason."""

    def dropped(self, **kw):
        _, dropped = build_dataset(self.raw, self.out, **kw)
        return dropped

    def test_a_partner_with_no_calcium_link_is_reported_not_silently_lost(self):
        self.write_raw([curated(source="COPA")])
        dropped = self.dropped()
        self.assertEqual(len(dropped), 1)
        self.assertIn("COPA", dropped[0])
        self.assertIn("not calcium-related", dropped[0])

    def test_a_partner_that_never_touches_an_anchor_is_reported_with_that_reason(self):
        # ORAI1 is a seed but not an anchor, so its partners are two hops from STIM1/STING1.
        (self.out).mkdir(parents=True, exist_ok=True)
        (self.out / "supp_catalogue.json").write_text(json.dumps({"ATP2C2": {}}))
        self.write_raw([curated(source="ATP2C2", target="ORAI1", type="activation")])
        dropped = self.dropped()
        self.assertEqual(len(dropped), 1)
        self.assertIn("ATP2C2", dropped[0])
        self.assertIn("no interaction with STIM1 or STING1", dropped[0])

    def test_an_admitted_curated_row_is_not_reported(self):
        (self.out).mkdir(parents=True, exist_ok=True)
        (self.out / "supp_catalogue.json").write_text(json.dumps({"ALG2": {}}))
        self.write_raw([curated()])
        self.assertEqual(self.dropped(), [])

    def test_only_curated_rows_are_reported_databases_are_expected_to_be_filtered(self):
        self.write_raw([rec(source="COPA", source_kind="signor", ref="SIGNOR-9", sentence="")])
        self.assertEqual(self.dropped(), [])


class TestSpeciesFlags(BuildCase):
    """Species unknown is not the same as species non-human (issue #16)."""

    def test_curated_rows_of_unknown_species_are_not_flagged_as_animal_evidence(self):
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "supp_catalogue.json").write_text(json.dumps({"ALG2": {}}))
        self.write_raw([curated()])
        i = self.build()["interactions"][0]
        self.assertEqual((i["has_human_evidence"], i["has_animal_evidence"]), ("false", "false"))

    def test_mouse_evidence_sets_the_animal_flag(self):
        self.write_raw([rec(species_context="mouse")])
        i = self.build()["interactions"][0]
        self.assertEqual((i["has_human_evidence"], i["has_animal_evidence"]), ("false", "true"))

    def test_human_evidence_keeps_both_flags_honest(self):
        self.write_raw([rec(species_context="human"), rec(ref="PMID:2", species_context="rat")])
        i = self.build()["interactions"][0]
        self.assertEqual((i["has_human_evidence"], i["has_animal_evidence"]), ("true", "true"))

if __name__ == "__main__":
    unittest.main()
