"""kept_interactions.csv -> graph data file loaded by the graph page."""
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from camap.graph import build_graph
from camap.schema import INTERACTION_COLUMNS

REVIEW_COLUMNS = ["decision", "comment", "reviewer", "reviewed_at"]


def row(iid, decision="keep", **kw):
    r = {c: "" for c in INTERACTION_COLUMNS + REVIEW_COLUMNS}
    r.update(interaction_id=iid, source="STIM1", target="STING1", type="inhibition", decision=decision,
             comment='tight, "direct"', reviewer="nf")
    r.update(kw)
    return r


class TestBuildGraph(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, rows, columns=INTERACTION_COLUMNS + REVIEW_COLUMNS):
        path = self.tmp / "kept.csv"
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        return path

    def load(self, out):
        js = out.read_text()
        prefix = "window.CAMAP = window.CAMAP || {};\nwindow.CAMAP.kept = "
        self.assertTrue(js.startswith(prefix))
        return json.loads(js[len(prefix):].rstrip().rstrip(";"))

    def test_kept_rows_become_graph_data_with_review_fields(self):
        out = self.tmp / "graph_data.js"
        n = build_graph(self.write([row("a"), row("b", decision="reject")]), out)
        self.assertEqual(n, 1)
        [r] = self.load(out)
        self.assertEqual((r["interaction_id"], r["comment"]), ("a", 'tight, "direct"'))

    def test_missing_columns_are_rejected(self):
        with self.assertRaises(ValueError):
            build_graph(self.write([row("a")], columns=["interaction_id", "source"]), self.tmp / "g.js")
