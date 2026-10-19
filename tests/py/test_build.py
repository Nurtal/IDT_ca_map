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
        # a literature row: the curated rows come in on the curator's say-so anyway
        self.write_catalogue({"CASQ1": {"ca_functionality": "Ca2+ binding"}})
        self.write_raw([rec(source="CASQ1", target="STING1", type="physical_binding",
                            sentence="Both proteins were detected in the same complex.")])
        d = self.build()
        self.assertEqual(sorted(n["id"] for n in d["nodes"]), ["CASQ1", "STING1"])
        self.assertEqual(d["interactions"][0]["calcium_evidence"], "curated")

    def test_a_partner_outside_the_catalogue_still_needs_GO_or_a_calcium_sentence(self):
        self.write_catalogue({"SOMETHING_ELSE": {}})
        self.write_raw([rec(source="CASQ1", target="STING1", type="physical_binding",
                            sentence="Both proteins were detected in the same complex.")])
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


class TestCuratedInclusion(BuildCase):
    """The curator's own call admits a partner (user decision of 2026-10-19, issue #16).

    A row she wrote down is a deliberate choice, so a curated link to a level-1 seed is
    enough: neither the calcium criterion nor the one-hop-from-an-anchor rule applies to it.
    """

    def test_a_curated_partner_of_an_anchor_enters_without_any_calcium_link(self):
        # STING trafficking machinery: no GO calcium term, no catalogue entry, no sentence.
        self.write_raw([curated(source="COPA")])
        d = self.build()
        self.assertEqual(sorted(n["id"] for n in d["nodes"]), ["COPA", "STING1"])

    def test_a_curated_partner_of_a_seed_enters_although_it_is_two_hops_from_the_axis(self):
        # ORAI1 is a level-1 seed, not an anchor; its curated interactome comes in all the same.
        self.write_raw([curated(source="ATP2C2", target="ORAI1", type="activation")])
        self.assertIn("ATP2C2", [n["id"] for n in self.build()["nodes"]])

    def test_the_wider_net_is_cast_for_curated_rows_only(self):
        self.write_raw([rec(source="GAPDH", target="ORAI1", type="physical_binding",
                            sentence="Both proteins were detected in the same complex.")])
        self.assertEqual(self.build()["interactions"], [])

    def test_a_curated_partner_takes_the_module_of_the_seed_it_hangs_from(self):
        self.write_raw([curated(source="ATP2C2", target="ORAI1", type="activation")])
        node = next(n for n in self.build()["nodes"] if n["id"] == "ATP2C2")
        self.assertEqual(node["module"], "soce")


class TestDropReport(BuildCase):
    """Issue #16: a curated row the inclusion rule drops must say so, with its reason."""

    def dropped(self, **kw):
        _, dropped = build_dataset(self.raw, self.out, **kw)
        return dropped

    def test_a_curated_row_hanging_from_no_seed_at_all_is_reported_not_silently_lost(self):
        self.write_raw([curated(source="COPA", target="TOLLIP")])
        dropped = self.dropped()
        self.assertEqual(len(dropped), 2)
        self.assertIn("COPA", dropped[0])
        self.assertIn("no curated link to a seed", dropped[0])

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


class TestBeyondCalcium(BuildCase):
    """`beyond_calcium`: an effector endpoint the researcher wants kept, tagged as not calcium.

    The calcium criterion stops the map at the axis, so the biological end of an arm —
    GSDMD -> F3, STING1 -> GPX4 — fell out. The flag is written by hand, record by record
    (user decision of 2026-10-19), and everything it lets in says so on the card.
    """

    def test_a_flagged_record_enters_although_nothing_about_it_is_calcium(self):
        self.write_raw([rec(source="STING1", target="GPX4", type="expression_regulation_down",
                            sentence="STING degrades GPX4.", beyond_calcium=True)])
        self.assertIn("GPX4", [n["id"] for n in self.build()["nodes"]])

    def test_the_interaction_and_the_node_both_say_they_are_not_calcium_related(self):
        self.write_raw([rec(source="STING1", target="GPX4", type="expression_regulation_down",
                            sentence="STING degrades GPX4.", beyond_calcium=True)])
        d = self.build()
        i = d["interactions"][0]
        self.assertEqual((i["beyond_calcium"], i["calcium_evidence"]), ("true", ""))
        nodes = {n["id"]: n for n in d["nodes"]}
        self.assertEqual(nodes["GPX4"]["calcium_related"], "false")
        self.assertEqual(nodes["STING1"]["calcium_related"], "true", "an anchor is the axis itself")

    def test_a_flagged_record_still_has_to_hang_off_the_map(self):
        self.write_raw([rec(source="GPX4", target="F3", type="activation",
                            sentence="Unrelated pair.", beyond_calcium=True)])
        self.assertEqual(self.build()["interactions"], [])

    def test_a_flag_reaches_down_a_chain_that_starts_on_the_map(self):
        self.write_raw([
            rec(source="STING1", target="GSDMD", type="activation",
                sentence="STING raises cytosolic calcium, which cleaves GSDMD."),
            rec(source="GSDMD", target="F3", type="activation", ref="PMID:2",
                sentence="GSDMD pores release F3.", beyond_calcium=True),
        ])
        self.assertEqual(sorted(n["id"] for n in self.build()["nodes"]),
                         ["F3", "GSDMD", "STING1"])

    def test_an_unflagged_partner_with_no_calcium_link_is_still_dropped(self):
        self.write_raw([rec(source="STING1", target="GPX4", type="expression_regulation_down",
                            sentence="STING degrades GPX4.")])
        self.assertEqual(self.build()["interactions"], [])


class TestStringAnnotation(BuildCase):
    """Story 22: STRING annotates the edges we have; it never creates one."""

    def write_string(self, scores):
        path = self.tmp / "cache" / "string"
        path.mkdir(parents=True, exist_ok=True)
        (path / "network.json").write_text(json.dumps(scores))

    def test_an_interaction_carries_the_string_score_of_its_pair(self):
        self.write_string({"STIM1|STING1": 0.42})
        self.write_raw([rec()])
        self.assertEqual(self.build(cache_dir=self.tmp / "cache")["interactions"][0]["string_score"],
                         "0.42")

    def test_a_pair_string_knows_nothing_about_leaves_the_column_empty(self):
        self.write_string({"STIM1|ORAI1": 0.999})
        self.write_raw([rec()])
        self.assertEqual(self.build(cache_dir=self.tmp / "cache")["interactions"][0]["string_score"], "")

    def test_a_string_pair_with_no_evidence_of_ours_is_not_an_interaction(self):
        self.write_string({"STIM1|ORAI1": 0.999, "GAPDH|ACTB": 0.9})
        self.write_raw([rec()])
        d = self.build(cache_dir=self.tmp / "cache")
        self.assertEqual([(i["source"], i["target"]) for i in d["interactions"]], [("STIM1", "STING1")])
        self.assertNotIn("GAPDH", [n["id"] for n in d["nodes"]])


class TestVerificationStatus(BuildCase):
    """A quote that cannot be checked is not a quote that failed the check.

    A database excerpt usually comes from the full text of the paper it cites, and PubTator
    often has only the abstract. Flagging those "not found verbatim" put 55 false warnings in
    the review stack, which is how a real alarm — our own paraphrased quote — gets ignored.
    """

    def cache_doc(self, pmid, text, full_text=False):
        d = self.tmp / "cache" / "pubtator"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{pmid}.json").write_text(json.dumps(
            {"pmid": pmid, "title": "T", "text": text, "full_text": full_text}))
        return self.tmp / "cache"

    def status(self, records, cache):
        self.write_raw(records)
        return [e["sentence_verified"] for e in self.build(cache_dir=cache)["evidence"]]

    def test_a_database_excerpt_absent_from_an_abstract_only_paper_is_unverifiable(self):
        cache = self.cache_doc("999", "An abstract that says nothing of the kind.")
        rec_ = rec(source_kind="signor", ref="SIGNOR-1", cited_pmid="999",
                   sentence="A multi-sentence excerpt from the full text. With a figure call.")
        self.assertEqual(self.status([rec_], cache), ["unverifiable"])

    def test_a_database_excerpt_absent_from_a_cached_full_text_is_a_real_mismatch(self):
        cache = self.cache_doc("999", "The full text, which does not contain it.", full_text=True)
        rec_ = rec(source_kind="signor", ref="SIGNOR-1", cited_pmid="999", sentence="Not in there.")
        self.assertEqual(self.status([rec_], cache), ["false"])

    def test_our_own_quote_that_is_not_in_the_abstract_stays_a_warning(self):
        cache = self.cache_doc("PMID:31511697", "An abstract without that sentence.")
        self.assertEqual(self.status([rec()], cache), ["false"])

    def test_a_quote_found_verbatim_is_verified_whatever_the_source(self):
        cache = self.cache_doc("999", "SIGNOR says: STING recruits TBK1 here.")
        rec_ = rec(source_kind="signor", ref="SIGNOR-1", cited_pmid="999",
                   sentence="STING recruits TBK1 here.")
        self.assertEqual(self.status([rec_], cache), ["true"])


class TestQuoteMatching(BuildCase):
    """Two mechanical reasons a genuine database quote looked non-verbatim."""

    def cache_doc(self, pmid, text):
        d = self.tmp / "cache" / "pubtator"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{pmid}.json").write_text(json.dumps(
            {"pmid": pmid, "title": "T", "text": text, "full_text": True}))
        return self.tmp / "cache"

    def status(self, sentence, text):
        cache = self.cache_doc("999", text)
        self.write_raw([rec(source_kind="signor", ref="SIGNOR-1", cited_pmid="999",
                            sentence=sentence)])
        return self.build(cache_dir=cache)["evidence"][0]["sentence_verified"]

    def test_a_greek_letter_matches_the_name_pubtator_writes_it_with(self):
        # PubTator transliterates: the cached text says IKKepsilon where SIGNOR says IKKε
        self.assertEqual(
            self.status("STING recruits TBK1 and IKKε here.",
                        "We found that STING recruits TBK1 and IKKepsilon here."), "true")

    def test_every_passage_of_a_pipe_joined_excerpt_must_be_found(self):
        text = "First passage of the paper. Then unrelated prose. Second passage of the paper."
        self.assertEqual(self.status("First passage of the paper.|Second passage of the paper.", text),
                         "true")
        self.assertEqual(self.status("First passage of the paper.|A claim nobody made.", text),
                         "false")

    def test_a_quote_of_the_title_tolerates_the_full_stop_pubtator_strips(self):
        self.assertEqual(
            self.status("Phosphorylation of NFATC1 is essential for cell migration and invasion.",
                        "Phosphorylation of NFATC1 is essential for cell migration and invasion "
                        "Background Progression of prostate cancer is a multistep process."), "true")

    def test_two_passages_the_database_joined_without_a_separator_still_verify(self):
        text = ("Here we show that SRC phosphorylates IRF3 at Y107 in infected cells. "
                "Unrelated prose sits between them. "
                "Taken together, these results suggest that progesterone acts through PGR.")
        quote = ("Here we show that SRC phosphorylates IRF3 at Y107 in infected cells. "
                 "Taken together, these results suggest that progesterone acts through PGR.")
        self.assertEqual(self.status(quote, text), "true")

    def test_an_invented_sentence_inside_a_real_excerpt_is_still_caught(self):
        text = "Here we show that SRC phosphorylates IRF3 at Y107 in infected cells."
        quote = ("Here we show that SRC phosphorylates IRF3 at Y107 in infected cells. "
                 "STIM1 was shown to be dispensable throughout the study.")
        self.assertEqual(self.status(quote, text), "false")

    def test_a_word_boundary_the_database_lost_still_verifies(self):
        # SIGNOR-264025 quotes "incancer cells" where the paper reads "in cancer cells"
        text = "Similarly, NFAT induces the transcription of the COX2 gene in cancer cells."
        quote = "NFAT induces the transcription of the COX2 gene incancer cells"
        self.assertEqual(self.status(quote, text), "true")

    def test_dropping_spaces_does_not_make_an_invented_sentence_match(self):
        text = "Similarly, NFAT induces the transcription of the COX2 gene in cancer cells."
        quote = "NFAT represses the transcription of the COX2 gene in cancer cells"
        self.assertEqual(self.status(quote, text), "false")

    def test_sentences_glued_without_a_space_are_still_split(self):
        text = ("Induction of downstream antiviral genes followed. "
                "A section heading sits here. "
                "In the above experiments we noticed the same effect.")
        quote = ("Induction of downstream antiviral genes followed."
                 "In the above experiments we noticed the same effect.")
        self.assertEqual(self.status(quote, text), "true")
