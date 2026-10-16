"""Database adapters -> raw evidence records, and the database-only sentence fallback."""
import json
import shutil
import unittest
from pathlib import Path

from camap.databases import biogrid_records, intact_records, omnipath_records, signor_records
from camap.pubtator import PubTator
from test_build import BuildCase

CACHE = Path(__file__).parent / "fixtures" / "cache"


def signor_row(a, b, effect, mechanism="", tax="9606", pmid="111", sentence="", sid="SIGNOR-1",
               type_a="protein", type_b="protein"):
    cols = [a, type_a, "IDA", "UNIPROT", b, type_b, "IDB", "UNIPROT", effect, mechanism, "", "", tax,
            "", "", "", "", "", "", "", "", pmid, "t", "", "curator", sentence, sid, "0.5"]
    return "\t".join(cols)


class TestSignor(unittest.TestCase):
    def one(self, *args, **kw):
        recs = signor_records(signor_row(*args, **kw) + "\n")
        self.assertEqual(len(recs), 1)
        return recs[0]

    def test_effect_and_mechanism_map_to_link_types(self):
        cases = [
            (("FAM20C", "STIM1", "up-regulates activity", "phosphorylation"), "phosphorylation"),
            (("PRKAA1", "STIM1", "down-regulates activity", ""), "inhibition"),
            (("STIM1", "ORAI1", "up-regulates activity", "binding"), "activation"),
            (("TRIM56", "STING1", "up-regulates", "ubiquitination"), "ubiquitination"),
            (("NFATC1", "X", "up-regulates quantity by expression", "transcriptional regulation"), "expression_regulation_up"),
            (("NFATC1", "Y", "down-regulates quantity by expression", "transcriptional regulation"), "expression_regulation_down"),
            (("STIM1", "ORAI1", "form complex", ""), "physical_binding"),
            (("A", "B", "up-regulates activity", "relocalization"), "translocation/trafficking"),
            (("A", "B", "unknown", ""), "unknown_regulation"),
        ]
        for args, expected in cases:
            self.assertEqual(self.one(*args)["type"], expected, args)

    def test_record_carries_reference_species_sentence_and_cited_paper(self):
        r = self.one("PRKAA1", "STIM1", "down-regulates activity", "phosphorylation", tax="10090",
                     pmid="31381180", sentence="AMPK phosphorylates STIM1.", sid="SIGNOR-277299")
        self.assertEqual((r["source"], r["target"]), ("PRKAA1", "STIM1"))
        self.assertEqual((r["source_kind"], r["ref"], r["cited_pmid"]), ("signor", "SIGNOR-277299", "31381180"))
        self.assertEqual(r["species_context"], "mouse")
        self.assertEqual(r["sentence"], "AMPK phosphorylates STIM1.")

    def test_complexes_families_and_phenotypes_are_skipped_but_small_molecules_kept(self):
        rows = "\n".join([
            signor_row("X", "STIM1", "up-regulates", type_a="complex"),
            signor_row("STIM1", "SOCE", "up-regulates", type_b="phenotype"),
            signor_row("calcium(2+)", "STIM1", "up-regulates", type_a="smallmolecule"),
        ])
        self.assertEqual([r["source"] for r in signor_records(rows)], ["calcium(2+)"])


class TestOmniPath(unittest.TestCase):
    def rec(self, **kw):
        base = {"source_genesymbol": "STIM1", "target_genesymbol": "TRPC1", "is_directed": True,
                "is_stimulation": False, "is_inhibition": False,
                "sources": ["IntAct", "TRIP"], "references": "TRIP:23686296;IntAct:19897728;HINT:19897728"}
        base.update(kw)
        return base

    def test_signs_map_to_activation_inhibition_or_unknown(self):
        types = lambda r: sorted(x["type"] for x in omnipath_records([r]))  # noqa: E731
        self.assertEqual(types(self.rec(is_stimulation=True)), ["activation"])
        self.assertEqual(types(self.rec(is_inhibition=True)), ["inhibition"])
        self.assertEqual(types(self.rec(is_stimulation=True, is_inhibition=True)), ["activation", "inhibition"])
        self.assertEqual(types(self.rec()), ["unknown_regulation"])
        self.assertEqual(types(self.rec(is_directed=False)), ["physical_binding"])

    def test_one_record_per_pair_citing_the_earliest_listed_reference(self):
        [r] = omnipath_records([self.rec(is_stimulation=True)])
        self.assertEqual((r["source_kind"], r["ref"]), ("omnipath", "OmniPath:STIM1>TRPC1"))
        self.assertEqual(r["cited_pmid"], "23686296")
        self.assertIn("IntAct", r["mechanism"])


MITAB = "\t".join([
    "uniprotkb:Q13586", "uniprotkb:Q96D31", "intact:EBI-1", "intact:EBI-2",
    "psi-mi:stim1_human(display_long)|uniprotkb:STIM1(gene name)|uniprotkb:GOK(gene name synonym)",
    "psi-mi:crcm1_human(display_long)|uniprotkb:ORAI1(gene name)",
    'psi-mi:"MI:0007"(anti tag coimmunoprecipitation)', "Park et al. (2009)", "imex:IM-1|pubmed:19249086",
    "taxid:9606(human)|taxid:9606(Homo sapiens)", "taxid:10090(mouse)",
    'psi-mi:"MI:0915"(physical association)', 'psi-mi:"MI:0469"(IntAct)', "intact:EBI-2291793|imex:IM-12069-6",
    "intact-miscore:0.91",
])


class TestIntAct(unittest.TestCase):
    def test_mitab_rows_become_physical_bindings(self):
        [r] = intact_records(MITAB + "\n")
        self.assertEqual((r["source"], r["target"], r["type"]), ("STIM1", "ORAI1", "physical_binding"))
        self.assertEqual((r["source_kind"], r["ref"], r["cited_pmid"]), ("intact", "EBI-2291793", "19249086"))
        self.assertEqual((r["first_author"], r["year"]), ("Park et al.", "2009"))
        self.assertEqual(r["species_context"], "other")  # human x mouse
        self.assertIn("anti tag coimmunoprecipitation", r["mechanism"])

    def test_self_interactions_are_skipped(self):
        row = MITAB.replace("uniprotkb:ORAI1(gene name)", "uniprotkb:STIM1(gene name)")
        self.assertEqual(intact_records(row), [])


class TestBioGrid(unittest.TestCase):
    def test_physical_interactions_only(self):
        data = {
            "1": {"BIOGRID_INTERACTION_ID": 1, "OFFICIAL_SYMBOL_A": "STIM1", "OFFICIAL_SYMBOL_B": "ORAI1",
                  "EXPERIMENTAL_SYSTEM": "Affinity Capture-Western", "EXPERIMENTAL_SYSTEM_TYPE": "physical",
                  "PUBMED_ID": 16807233, "PUBMED_AUTHOR": "Yeromin AV (2006)", "ORGANISM_A": 9606, "ORGANISM_B": 9606},
            "2": {"BIOGRID_INTERACTION_ID": 2, "OFFICIAL_SYMBOL_A": "STIM1", "OFFICIAL_SYMBOL_B": "XYZ",
                  "EXPERIMENTAL_SYSTEM": "Synthetic Lethality", "EXPERIMENTAL_SYSTEM_TYPE": "genetic",
                  "PUBMED_ID": 1, "PUBMED_AUTHOR": "A (2000)", "ORGANISM_A": 9606, "ORGANISM_B": 9606},
        }
        [r] = biogrid_records(data)
        self.assertEqual((r["source"], r["target"], r["type"]), ("STIM1", "ORAI1", "physical_binding"))
        self.assertEqual((r["ref"], r["cited_pmid"], r["species_context"]), ("BIOGRID:1", "16807233", "human"))
        self.assertEqual((r["first_author"], r["year"]), ("Yeromin AV", "2006"))


class FakeHttp:
    def __call__(self, url):
        return {"PubTator3": [{"pmid": 777, "date": "2010-01-01", "authors": ["Roe K"], "passages": [
            {"infons": {"type": "title"}, "text": "A study."},
            {"infons": {"type": "abstract"}, "text": "Cells were stimulated. Here, STIM1 associated with "
             "Orai1 at ER-plasma membrane junctions. Calcium rose."}]}]}


class TestDatabaseOnlySentence(BuildCase):
    def setUp(self):
        super().setUp()
        self.cache = self.tmp / "cache"
        shutil.copytree(CACHE, self.cache)
        PubTator(self.cache, http_get_json=FakeHttp()).fetch_texts(["777"])

    def db_rec(self, **kw):
        r = {"source": "STIM1", "target": "ORAI1", "type": "physical_binding", "source_kind": "intact",
             "ref": "EBI-9", "cited_pmid": "777", "sentence": "", "species_context": "human"}
        r.update(kw)
        return r

    def evidence(self, rec):
        self.write_raw([rec])
        [e] = self.build(cache_dir=self.cache)["evidence"]
        return e

    def test_sentence_mentioning_both_actors_is_taken_from_the_cited_abstract(self):
        e = self.evidence(self.db_rec())
        self.assertEqual(e["sentence"], "Here, STIM1 associated with Orai1 at ER-plasma membrane junctions.")
        self.assertEqual(e["sentence_verified"], "true")
        self.assertEqual(e["cited_pmid"], "777")

    def test_no_matching_sentence_leaves_it_empty(self):
        e = self.evidence(self.db_rec(cited_pmid="404"))
        self.assertEqual((e["sentence"], e["sentence_verified"]), ("", ""))

    def test_curated_database_sentence_is_verified_against_the_cited_paper(self):
        e = self.evidence(self.db_rec(source_kind="signor", ref="SIGNOR-9", sentence="Calcium rose."))
        self.assertEqual(e["sentence_verified"], "true")


if __name__ == "__main__":
    unittest.main()
