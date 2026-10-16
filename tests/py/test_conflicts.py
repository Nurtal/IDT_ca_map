"""Conflicting interactions on the same endpoints reference each other."""
from test_build import BuildCase, rec


class TestConflicts(BuildCase):
    def conflicts(self, records):
        self.write_raw(records)
        rows = self.build()["interactions"]
        return {(i["type"]): i for i in rows}

    def test_activation_and_inhibition_of_the_same_target_conflict(self):
        d = self.conflicts([rec(type="activation"), rec(type="inhibition", ref="PMID:2")])
        self.assertEqual(d["activation"]["conflict_with"], d["inhibition"]["interaction_id"])
        self.assertEqual(d["inhibition"]["conflict_with"], d["activation"]["interaction_id"])

    def test_expression_up_and_down_conflict(self):
        d = self.conflicts([rec(type="expression_regulation_up"), rec(type="expression_regulation_down", ref="PMID:2")])
        self.assertEqual(d["expression_regulation_up"]["conflict_with"], d["expression_regulation_down"]["interaction_id"])

    def test_opposite_directions_and_compatible_types_do_not_conflict(self):
        d = self.conflicts([rec(type="activation"), rec(source="STING1", target="STIM1", type="inhibition", ref="PMID:2"),
                            rec(type="physical_binding", ref="PMID:3")])
        self.assertTrue(all(i["conflict_with"] == "" for i in d.values()))
