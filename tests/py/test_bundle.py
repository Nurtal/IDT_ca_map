"""What goes into the folder the curator carries to another PC."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from camap.bundle import bundle_paths, write_bundle


def fake_project(root):
    files = [
        "review/index.html", "review/app.js", "review/style.css",
        "graph/index.html", "graph/graph.js", "graph/style.css",
        "shared/compat.js", "shared/core.js", "shared/ui.js", "shared/theme.css",
        "vendor/cytoscape.min.js", "vendor/README.md",
        "data/nodes.js", "data/interactions.js", "data/evidence.js", "data/graph_data.js",
        "data/nodes.csv", "data/raw/lit_x.jsonl",
        "pipeline/cli.py", "pipeline/state/queue.jsonl", "docs/EXTRACTION_PROTOCOL.md",
        "data_supp/sheet.xlsx",
    ]
    for rel in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")


class TestBundle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        fake_project(self.root)
        self.addCleanup(self.tmp.cleanup)

    def test_everything_the_two_pages_load_is_in_the_bundle(self):
        paths = bundle_paths(self.root)
        for rel in ["review/index.html", "review/app.js", "review/style.css",
                    "graph/index.html", "shared/compat.js", "shared/core.js", "shared/ui.js",
                    "shared/theme.css", "vendor/cytoscape.min.js",
                    "data/nodes.js", "data/interactions.js", "data/evidence.js", "data/graph_data.js"]:
            self.assertIn(rel, paths, rel + " is loaded by a page and must travel with it")

    def test_the_pipeline_and_the_raw_records_stay_behind(self):
        paths = bundle_paths(self.root)
        for rel in ["pipeline/cli.py", "pipeline/state/queue.jsonl", "data/raw/lit_x.jsonl",
                    "data/nodes.csv", "data_supp/sheet.xlsx"]:
            self.assertNotIn(rel, paths, rel + " is not read by the review app")

    def test_a_missing_build_is_an_error_rather_than_a_bundle_that_shows_nothing(self):
        (self.root / "data/nodes.js").unlink()
        with self.assertRaises(FileNotFoundError):
            bundle_paths(self.root)

    def test_the_zip_holds_the_folder_name_so_it_extracts_into_one_directory(self):
        dest = self.root / "dist/camap-review.zip"
        write_bundle(self.root, dest, folder="camap-review")
        with zipfile.ZipFile(dest) as z:
            names = z.namelist()
        self.assertIn("camap-review/review/index.html", names)
        self.assertIn("camap-review/data/nodes.js", names)
        self.assertTrue(all(n.startswith("camap-review/") for n in names))


if __name__ == "__main__":
    unittest.main()
