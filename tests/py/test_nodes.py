"""Actor normalization, node annotations and the node inclusion rule."""
import shutil
from pathlib import Path

from test_build import BuildCase, rec

CACHE = Path(__file__).parent / "fixtures" / "cache"
NEUTRAL = "Both proteins were detected in the same complex."


class NodeCase(BuildCase):
    def setUp(self):
        super().setUp()
        self.cache = self.tmp / "cache"
        shutil.copytree(CACHE, self.cache)

    def build_with(self, records):
        self.write_raw(records)
        return self.build(cache_dir=self.cache)

    def node_ids(self, d):
        return sorted(n["id"] for n in d["nodes"])


class TestNormalization(NodeCase):
    def test_aliases_previous_symbols_and_mouse_case_collapse_to_hgnc(self):
        d = self.build_with([
            rec(source="STIM1", target="TMEM173", ref="PMID:1"),
            rec(source="Stim1", target="MITA", ref="PMID:2"),
            rec(source="STIM1", target="Sting1", ref="PMID:3"),
        ])
        self.assertEqual(self.node_ids(d), ["STIM1", "STING1"])
        self.assertEqual(len(d["interactions"]), 1)
        self.assertEqual(d["interactions"][0]["n_sources"], "3")

    def test_metabolites_map_to_chebi(self):
        d = self.build_with([
            rec(source="ORAI1", target="Ca2+", type="Ca2+_flux"),
            rec(source="CGAS", target="cGAMP", type="activation", ref="PMID:2"),
            rec(source="calcium", target="STIM1", type="activation", ref="PMID:3"),
        ])
        nodes = {n["id"]: n for n in d["nodes"]}
        self.assertEqual(nodes["CHEBI:29108"]["type"], "metabolite")
        self.assertEqual(nodes["CHEBI:29108"]["symbol"], "Ca2+")
        self.assertEqual(nodes["CHEBI:29108"]["module"], "metabolite")
        self.assertIn("CHEBI:75947", nodes)
        sources = {(i["source"], i["target"]) for i in d["interactions"]}
        self.assertIn(("CHEBI:29108", "STIM1"), sources)

    def test_nodes_carry_annotations_and_seed_status(self):
        d = self.build_with([rec()])
        n = {n["id"]: n for n in d["nodes"]}["STING1"]
        self.assertEqual(n["name"], "stimulator of interferon response cGAMP interactor 1")
        self.assertEqual(n["uniprot"], "Q86WV6")
        self.assertIn("TMEM173", n["synonyms"])
        self.assertEqual(n["function_summary"], "Innate immune signaling adapter.")
        self.assertEqual((n["is_seed"], n["module"], n["type"]), ("true", "sting", "gene"))


class TestInclusionRule(NodeCase):
    def test_calcium_annotated_partner_of_an_anchor_is_kept(self):
        d = self.build_with([rec(source="CASQ1", target="STIM1", type="physical_binding", sentence=NEUTRAL)])
        self.assertIn("CASQ1", self.node_ids(d))

    def test_partner_without_any_calcium_evidence_is_dropped(self):
        d = self.build_with([rec(source="GAPDH", target="STIM1", type="physical_binding", sentence=NEUTRAL)])
        self.assertNotIn("GAPDH", self.node_ids(d))
        self.assertEqual(d["interactions"], [])
        self.assertEqual(d["evidence"], [])

    def test_calcium_mention_in_sentence_is_enough(self):
        d = self.build_with([rec(source="TRIM29", target="STING1", type="ubiquitination",
                                 sentence="TRIM29 ubiquitinates STING after store-operated Ca2+ entry.")])
        self.assertIn("TRIM29", self.node_ids(d))

    def test_calcium_partner_of_a_non_anchor_seed_is_dropped(self):
        d = self.build_with([rec(source="CASQ1", target="ORAI1", type="physical_binding", sentence=NEUTRAL)])
        self.assertNotIn("CASQ1", self.node_ids(d))

    def test_interaction_between_level1_seeds_is_kept(self):
        d = self.build_with([rec(source="ORAI1", target="CALM1", type="physical_binding", sentence=NEUTRAL)])
        self.assertEqual(self.node_ids(d), ["CALM1", "ORAI1"])

    def test_level2_seed_needs_an_anchor(self):
        alone = self.build_with([rec(source="PPP3CA", target="NFATC1", type="activation", sentence=NEUTRAL)])
        self.assertEqual(alone["interactions"], [])
        self.write_raw([], name="batch.jsonl")
        linked = self.build_with([rec(source="STIM1", target="PPP3CA", type="activation", sentence=NEUTRAL)])
        self.assertIn("PPP3CA", self.node_ids(linked))


class TestModulesAndCalciumEvidence(NodeCase):
    def calcium(self, d, a, b):
        return next(i["calcium_evidence"] for i in d["interactions"] if {i["source"], i["target"]} == {a, b})

    def test_cholesterol_crac_motif_is_not_calcium_evidence(self):
        self.write_raw([
            rec(source="SOAT1", target="STING1", type="inhibition",
                sentence="Both STING CRAC mutants exhibited impaired interaction with cholesterol."),
        ])
        d = self.build()
        self.assertNotIn("SOAT1", [n["id"] for n in d["nodes"]],
                         "a cholesterol CRAC motif must not count as calcium evidence")

    def test_calcium_evidence_from_go_text_or_both(self):
        d = self.build_with([
            rec(source="CASQ1", target="STIM1", type="physical_binding", sentence=NEUTRAL),
            rec(source="TRIM29", target="STING1", type="ubiquitination", sentence="Calcium triggers it."),
            rec(source="STIM1", target="ORAI1", type="physical_binding", sentence="STIM1 gates CRAC channels."),
            rec(source="STING1", target="CGAS", type="physical_binding", sentence=NEUTRAL),
        ])
        self.assertEqual(self.calcium(d, "CASQ1", "STIM1"), "GO")
        self.assertEqual(self.calcium(d, "TRIM29", "STING1"), "text")
        self.assertEqual(self.calcium(d, "STIM1", "ORAI1"), "both")
        self.assertEqual(self.calcium(d, "STING1", "CGAS"), "")

    def test_non_seed_module_follows_its_anchors(self):
        d = self.build_with([
            rec(source="CASQ1", target="STIM1", type="physical_binding", sentence=NEUTRAL),
            rec(source="TRIM29", target="STING1", type="ubiquitination", sentence="Calcium triggers it."),
            rec(source="TRIM29", target="STIM1", type="physical_binding", sentence="Calcium again.", ref="PMID:9"),
        ])
        modules = {n["id"]: n["module"] for n in d["nodes"]}
        self.assertEqual(modules["CASQ1"], "soce")
        self.assertEqual(modules["TRIM29"], "bridge")
