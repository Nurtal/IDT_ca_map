"""Pipeline seam: the curator's spreadsheets in data_supp/ in, raw records out."""
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from camap.supp import (catalogue_entries, catalogue_report, interaction_records,
                        read_workbook)

NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
RELNS = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


def write_xlsx(path, sheets, shared=()):
    """A minimal .xlsx: {sheet name: [[cell, ...], ...]} where a cell is a ready-made <c> element."""
    with zipfile.ZipFile(path, "w") as z:
        names = list(sheets)
        z.writestr("xl/workbook.xml", f"<workbook {NS} {RELNS}><sheets>" + "".join(
            f'<sheet name="{n}" sheetId="{i}" r:id="rId{i}"/>' for i, n in enumerate(names, 1)
        ) + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(
                       f'<Relationship Id="rId{i}" Target="worksheets/sheet{i}.xml"/>'
                       for i, _ in enumerate(names, 1)) + "</Relationships>")
        if shared:
            z.writestr("xl/sharedStrings.xml", f"<sst {NS}>" + "".join(
                f"<si><t>{s}</t></si>" for s in shared) + "</sst>")
        for i, name in enumerate(names, 1):
            rows = "".join(f'<row r="{n}">{"".join(_placed(cells, n))}</row>'
                           for n, cells in enumerate(sheets[name], 1))
            z.writestr(f"xl/worksheets/sheet{i}.xml", f"<worksheet {NS}><sheetData>{rows}</sheetData></worksheet>")


def _placed(cells, row_number):
    """Real spreadsheets omit empty cells and reference the rest by column (A2, D2, ...)."""
    out = []
    for column, cell in enumerate(cells, 1):
        if cell is None:
            continue
        letter = chr(ord("A") + column - 1)
        out.append(cell.replace("<c", f'<c r="{letter}{row_number}"', 1))
    return out


def shared_cell(index):
    return f'<c t="s"><v>{index}</v></c>'


def inline_cell(text):
    return f'<c t="inlineStr"><is><t>{text}</t></is></c>'


def empty_cell():
    return "<c/>"


class WorkbookCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def workbook(self, sheets, shared=()):
        path = self.tmp / "book.xlsx"
        write_xlsx(path, sheets, shared)
        return read_workbook(path)


class TestReadWorkbook(WorkbookCase):
    def test_rows_are_dicts_keyed_by_the_header_row(self):
        book = self.workbook(
            {"STIM1": [[shared_cell(0), shared_cell(1)], [shared_cell(2), shared_cell(3)]]},
            shared=["Gène", "Régulation", "ADCY6", "positive"],
        )
        self.assertEqual(book["STIM1"], [{"Gène": "ADCY6", "Régulation": "positive"}])

    def test_inline_strings_are_read_like_shared_strings(self):
        book = self.workbook({"S": [[inline_cell("Gène")], [inline_cell("ANO8")]]})
        self.assertEqual(book["S"], [{"Gène": "ANO8"}])

    def test_padded_rows_without_a_first_cell_are_dropped(self):
        book = self.workbook(
            {"S": [[shared_cell(0)], [shared_cell(1)], [empty_cell()], []]},
            shared=["Gène", "ANO8"],
        )
        self.assertEqual(book["S"], [{"Gène": "ANO8"}])

    def test_an_empty_sheet_reads_as_no_rows(self):
        book = self.workbook({"TRPC": [], "S": [[inline_cell("Gène")], [inline_cell("ANO8")]]})
        self.assertEqual(book["TRPC"], [])

    def test_cell_text_is_stripped(self):
        book = self.workbook({"S": [[inline_cell("Gène")], [inline_cell(" ATP2C2 ")]]})
        self.assertEqual(book["S"], [{"Gène": "ATP2C2"}])

    def test_columns_without_a_header_keep_their_own_key(self):
        # The curator's reference DOIs spill into unnamed columns past "Références";
        # collapsing them onto one key would silently drop all but the last.
        book = self.workbook(
            {"S": [[inline_cell("Gène"), inline_cell("Références"), empty_cell(), empty_cell()],
                   [inline_cell("APC"), inline_cell("10.1016/j.ceca.2013.06.008"),
                    inline_cell("10.1016/j.cell.2009.04.065"), inline_cell("10.1038/x")]]})
        self.assertEqual(sorted(book["S"][0].values()),
                         ["10.1016/j.ceca.2013.06.008", "10.1016/j.cell.2009.04.065",
                          "10.1038/x", "APC"])

    def test_duplicated_headers_keep_their_own_key(self):
        book = self.workbook({"S": [[inline_cell("Réf"), inline_cell("Réf")],
                                    [inline_cell("10.1/a"), inline_cell("10.2/b")]]})
        self.assertEqual(sorted(book["S"][0].values()), ["10.1/a", "10.2/b"])


STING_SHEET = {
    "name": "interactors",
    "anchor": "STING1",
    "gene_column": "Gène",
    "regulation_column": "Régulation",
    "default_type": "physical_binding",
    "note_columns": ["Effet de l'interaction", "domain of the interactor", "domain of STING"],
    "justification": "Curated by the researcher as a STING1 interactor.",
}
REGULATION_MAP = {"positive": "activation", "negative": "inhibition"}


def records(rows, sheet=None, **kw):
    cfg = dict(STING_SHEET, **(sheet or {}))
    return interaction_records(cfg, rows, regulation_map=REGULATION_MAP, file_name="STING.xlsx", **kw)


class TestInteractionRecords(unittest.TestCase):
    def test_a_row_becomes_an_interaction_with_the_sheet_anchor_as_target(self):
        recs, _ = records([{"Gène": "ALG2", "Régulation": "negative",
                            "Effet de l'interaction": "Inhibits STING trafficking"}])
        self.assertEqual(len(recs), 1)
        r = recs[0]
        self.assertEqual((r["source"], r["target"], r["type"]), ("ALG2", "STING1", "inhibition"))
        self.assertEqual(r["source_kind"], "curated")
        self.assertEqual(r["species_context"], "unknown")

    def test_the_curator_note_keeps_the_spreadsheet_wording_and_there_is_no_sentence(self):
        recs, _ = records([{"Gène": "ALG2", "Régulation": "negative",
                            "domain of STING": "CTD",
                            "Effet de l'interaction": "Inhibits STING trafficking"}])
        self.assertNotIn("sentence", recs[0])
        self.assertIn("Inhibits STING trafficking", recs[0]["curator_note"])
        self.assertIn("CTD", recs[0]["curator_note"])

    def test_regulation_maps_to_a_link_type_whatever_its_capitalisation(self):
        recs, _ = records([{"Gène": "AMFR", "Régulation": "Positive"}])
        self.assertEqual(recs[0]["type"], "activation")

    def test_an_empty_regulation_falls_back_to_the_sheet_default(self):
        recs, notes = records([{"Gène": "ARMH3", "Régulation": ""}])
        self.assertEqual(recs[0]["type"], "physical_binding")
        self.assertEqual(notes, [])

    def test_an_unmapped_regulation_is_reported_rather_than_guessed(self):
        recs, notes = records([{"Gène": "APC", "Régulation": "modulates somehow"}])
        self.assertEqual(recs[0]["type"], "physical_binding")
        self.assertEqual(len(notes), 1)
        self.assertIn("modulates somehow", notes[0])

    def test_one_record_per_doi_each_normalised_to_a_bare_doi(self):
        recs, _ = records([{"Gène": "APC", "Régulation": "positive",
                            "Références": "https://doi.org/10.1016/j.ceca.2013.06.008",
                            "col_9": "/10.1371/journal.ppat.1010989"}])
        self.assertEqual([r["ref"] for r in recs],
                         ["DOI:10.1016/j.ceca.2013.06.008", "DOI:10.1371/journal.ppat.1010989"])
        self.assertEqual(recs[0]["doi"], "10.1016/j.ceca.2013.06.008")

    def test_a_row_without_a_doi_still_yields_a_record_credited_to_the_curator(self):
        recs, _ = records([{"Gène": "DDOST", "Régulation": ""}])
        self.assertEqual(recs[0]["ref"], "CURATED:STING.xlsx/interactors/DDOST")

    def test_every_record_says_which_cell_it_came_from(self):
        recs, _ = records([{"Gène": "ALG2", "Régulation": "negative"}])
        self.assertEqual(recs[0]["supp_source"], "STING.xlsx/interactors/row 2")

    def test_rows_whose_gene_cell_is_a_sentence_are_reported_not_imported(self):
        recs, notes = records([{"Gène": "SLC19A1 Is an Importer of the Immunotransmitter cGAMP."}])
        self.assertEqual(recs, [])
        self.assertEqual(len(notes), 1)
        self.assertIn("SLC19A1 Is an Importer", notes[0])

    def test_the_anchor_interacting_with_itself_is_dropped(self):
        recs, notes = records([{"Gène": "STING1", "Régulation": "positive"}])
        self.assertEqual(recs, [])
        self.assertEqual(len(notes), 1)


CATALOGUE = {
    "symbol_column": "Gene name",
    "annotation_columns": {
        "genecards": ["GeneCards Identifier"],
        "aliases": ["alias names"],
        "protein_type": ["protein type 1", "protein type 2"],
        "localization": ["localization 1", "localization 2"],
        "ca_functionality": ["Ca2+ functionality 1", "Ca2+ functionality 2"],
        "functional_assignment": ["Functional assignment  1"],
    },
}


class TestCatalogueEntries(unittest.TestCase):
    def test_a_gene_becomes_one_entry_keyed_by_symbol(self):
        entries, _ = catalogue_entries(CATALOGUE, [
            {"Gene name": "ACTN1", "GeneCards Identifier": "GC14M068874",
             "alias names": "Actinin Alpha 1", "protein type 1": "Cytoskeleton protein",
             "localization 1": "cytosol", "Ca2+ functionality 1": "Ca2+ binding",
             "Ca2+ functionality 2": "Ca2+ regulated",
             "Functional assignment  1": "actin filament organization"}])
        self.assertEqual(sorted(entries), ["ACTN1"])
        e = entries["ACTN1"]
        self.assertEqual(e["genecards"], "GC14M068874")
        self.assertEqual(e["ca_functionality"], "Ca2+ binding; Ca2+ regulated")
        self.assertEqual(e["localization"], "cytosol")

    def test_empty_annotation_columns_are_left_out(self):
        entries, _ = catalogue_entries(CATALOGUE, [{"Gene name": "ABHD2", "localization 1": "ER membrane"}])
        self.assertEqual(entries["ABHD2"], {"localization": "ER membrane"})

    def test_symbols_are_upper_cased_so_the_lookup_matches_hgnc_ids(self):
        entries, _ = catalogue_entries(CATALOGUE, [{"Gene name": "cGas"}])
        self.assertIn("CGAS", entries)

    def test_a_row_without_a_symbol_is_ignored(self):
        entries, _ = catalogue_entries(CATALOGUE, [{"Gene name": "", "localization 1": "ER"}])
        self.assertEqual(entries, {})


class TestCatalogueReport(unittest.TestCase):
    def test_splits_the_catalogue_into_in_map_leads_and_untouched(self):
        lines = catalogue_report({"STIM1": {}, "ACTN1": {}, "ABHD2": {}, "A2M": {}},
                                 node_ids={"STIM1", "STING1"}, seen_symbols={"STIM1", "ACTN1"})
        text = "\n".join(lines)
        self.assertIn("1 in the map", text)
        self.assertIn("1 seen in the corpus", text)
        self.assertIn("2 untouched", text)

    def test_names_a_few_leads_so_the_next_extraction_batch_has_targets(self):
        lines = catalogue_report({"ACTN1": {}}, node_ids=set(), seen_symbols={"ACTN1"})
        self.assertIn("ACTN1", "\n".join(lines))


class TestSymbolFixes(unittest.TestCase):
    def test_a_configured_fix_replaces_the_curator_cell(self):
        recs, notes = records([{"Gène": "TBB4B", "Régulation": "positive"}],
                              symbol_fixes={"TBB4B": "TUBB4B"})
        self.assertEqual(recs[0]["source"], "TUBB4B")
        self.assertEqual(notes, [])

    def test_a_fix_rescues_a_cell_that_is_not_a_bare_symbol(self):
        recs, _ = records([{"Gène": "E3 ubiquitin ligase RNF5", "Régulation": "negative"}],
                          symbol_fixes={"E3 ubiquitin ligase RNF5": "RNF5"})
        self.assertEqual(recs[0]["source"], "RNF5")

    def test_the_record_keeps_the_cell_the_curator_actually_wrote(self):
        recs, _ = records([{"Gène": "TBB4B", "Régulation": "positive"}],
                          symbol_fixes={"TBB4B": "TUBB4B"})
        self.assertEqual(recs[0]["curator_symbol"], "TBB4B")


class TestSparseRows(WorkbookCase):
    """A real .xlsx omits empty cells, so a value's column comes from its cell reference."""

    def test_a_gap_does_not_shift_the_values_that_follow_it(self):
        book = self.workbook({"S": [
            [inline_cell("Gene name"), inline_cell("localization 1"), inline_cell("domain"),
             inline_cell("Functional assignment")],
            [inline_cell("ACTN1"), None, None, inline_cell("actin filament organization")],
        ]})
        self.assertEqual(book["S"], [{"Gene name": "ACTN1",
                                      "Functional assignment": "actin filament organization"}])

    def test_a_row_shorter_than_the_header_keeps_the_columns_it_has(self):
        book = self.workbook({"S": [
            [inline_cell("Gène"), inline_cell("Régulation"), inline_cell("Références")],
            [inline_cell("ANO8"), None, inline_cell("10.1/a")],
        ]})
        self.assertEqual(book["S"][0], {"Gène": "ANO8", "Références": "10.1/a"})


class TestCatalogueDuplicatesAndAliases(unittest.TestCase):
    def test_two_rows_for_the_same_gene_are_merged_not_overwritten(self):
        entries, notes = catalogue_entries(CATALOGUE, [
            {"Gene name": "APP", "localization 1": "ER"},
            {"Gene name": "APP", "localization 1": "Golgi", "protein type 1": "receptor"},
        ])
        self.assertEqual(entries["APP"]["localization"], "ER; Golgi")
        self.assertEqual(entries["APP"]["protein_type"], "receptor")
        self.assertEqual(len(notes), 1)
        self.assertIn("APP", notes[0])

    def test_a_catalogue_symbol_is_resolved_so_it_matches_the_node_it_describes(self):
        entries, _ = catalogue_entries(CATALOGUE, [{"Gene name": "MYLPF", "localization 1": "cytosol"}],
                                       resolve=lambda s: "MYL11" if s == "MYLPF" else s)
        self.assertEqual(sorted(entries), ["MYL11"])
