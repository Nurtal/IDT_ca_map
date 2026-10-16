"""Species context per evidence and has_human_evidence per interaction."""
from test_build import BuildCase, rec


class TestSpecies(BuildCase):
    def human_flag(self, *contexts):
        self.write_raw([rec(ref=f"PMID:{n}", species_context=c) for n, c in enumerate(contexts)])
        return self.build()["interactions"][0]["has_human_evidence"]

    def test_mouse_only_interaction_has_no_human_evidence(self):
        self.assertEqual(self.human_flag("mouse", "mouse", "rat"), "false")

    def test_one_human_evidence_is_enough(self):
        self.assertEqual(self.human_flag("mouse", "human"), "true")

    def test_human_cell_lines_count_as_human(self):
        self.assertEqual(self.human_flag("in_vitro_human_cells"), "true")

    def test_unknown_species_is_not_human(self):
        self.assertEqual(self.human_flag("unknown", "other"), "false")

    def test_species_context_kept_per_evidence(self):
        self.write_raw([rec(ref="PMID:1", species_context="mouse"), rec(ref="PMID:2", species_context="human")])
        self.assertEqual(sorted(e["species_context"] for e in self.build()["evidence"]), ["human", "mouse"])

    def test_invalid_species_context_is_rejected(self):
        self.write_raw([rec(species_context="zebrafish")])
        with self.assertRaises(ValueError):
            self.build()
