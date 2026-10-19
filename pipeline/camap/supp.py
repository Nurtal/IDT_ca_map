"""The curator's spreadsheets in data_supp/ -> raw records (`source_kind: "curated"`).

An .xlsx is a zip of XML, so the standard library is enough (the pipeline stays on
stdlib + requests, see issue #1). Sheets declare padded dimensions, so a row whose first
cell is empty is filler and is dropped.
"""
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PACKAGE_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def read_workbook(path):
    """{sheet name: [row dict keyed by the header row]} — padded and empty rows dropped."""
    with zipfile.ZipFile(path) as z:
        shared = _shared_strings(z)
        sheets = {}
        for name, part in _sheet_parts(z).items():
            sheets[name] = _sheet_rows(z, part, shared)
    return sheets


def _shared_strings(z):
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.iter(MAIN + "t")) for si in root.findall(MAIN + "si")]


def _sheet_parts(z):
    workbook = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels.iter(PACKAGE_REL + "Relationship")}
    parts = {}
    for sheet in workbook.find(MAIN + "sheets"):
        part = target[sheet.get(REL + "id")].lstrip("/")
        parts[sheet.get("name")] = part if part.startswith("xl/") else "xl/" + part
    return parts


def _sheet_rows(z, part, shared):
    data = ET.fromstring(z.read(part)).find(MAIN + "sheetData")
    rows = [_row_cells(row, shared) for row in (data if data is not None else [])]
    rows = [r for r in rows if r and r[0]]
    if not rows:
        return []
    header, *body = rows
    keys = _keys(header)
    # An empty cell is left out rather than stored as "": a row then says only what the
    # curator actually filled in.
    return [{k: v for k, v in zip(keys, row) if v} for row in body]


def _keys(header):
    """Column keys. Unnamed and duplicated headers keep a key of their own: the curator's
    reference DOIs spill into the columns past "Références", and collapsing them onto one
    key would drop all but the last."""
    keys, seen = [], set()
    for index, name in enumerate(header, 1):
        key = name if name and name not in seen else f"col_{index}"
        keys.append(key)
        seen.add(key)
    return keys


def _row_cells(row, shared):
    """The row's cells in column order. A real spreadsheet omits empty cells, so a cell's
    column comes from its reference (A2, D2, ...) — reading them positionally would shift
    every value after a gap into the wrong column."""
    cells = {}
    for index, cell in enumerate(row, 1):
        column = _column_index(cell.get("r")) or index
        cells[column] = _cell_text(cell, shared)
    return [cells.get(i, "") for i in range(1, max(cells, default=0) + 1)]


def _column_index(reference):
    """'AA2' -> 27, the 1-based column number. None when the cell carries no reference."""
    letters = "".join(c for c in (reference or "") if c.isalpha()).upper()
    if not letters:
        return None
    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter) - ord("A") + 1)
    return index


def _cell_text(cell, shared):
    if cell.get("t") == "inlineStr":
        return "".join(t.text or "" for t in cell.iter(MAIN + "t")).strip()
    value = cell.find(MAIN + "v")
    text = "" if value is None else (value.text or "")
    if cell.get("t") == "s" and text.strip().isdigit():
        text = shared[int(text)]
    return text.strip()


DOI = re.compile(r"10\.\d{4,9}/\S+")
# A gene cell the curator filled with prose rather than a symbol (see issue #18).
SYMBOL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/()+-]{0,19}$")


def dois_in(row):
    """Every DOI of a row, in column order, normalized to a bare DOI."""
    found = []
    for value in row.values():
        for match in DOI.finditer(value or ""):
            doi = match.group(0).rstrip(".,;)")
            if doi not in found:
                found.append(doi)
    return found


def interaction_records(sheet, rows, regulation_map, file_name, symbol_fixes=None):
    """(records, notes) for one interactome sheet. Nothing is guessed silently: a row the
    mapping cannot read is reported in `notes` and left out, never coerced into an edge."""
    records, notes = [], []
    origin = f"{file_name}/{sheet['name']}"
    for index, row in enumerate(rows, 2):  # row 1 is the header
        where = f"{origin}/row {index}"
        cell = (row.get(sheet["gene_column"]) or "").strip()
        symbol = (symbol_fixes or {}).get(cell, cell)
        if not SYMBOL.match(symbol):
            notes.append(f"{where}: not a gene symbol, row skipped: {cell!r}")
            continue
        if symbol.upper() == sheet["anchor"].upper():
            notes.append(f"{where}: the sheet anchor interacting with itself, row skipped")
            continue
        type_, warning = link_type(row.get(sheet.get("regulation_column"), ""),
                                   sheet["default_type"], regulation_map)
        if warning:
            notes.append(f"{where}: {warning}")
        note = curator_note(sheet, row)
        base = {
            "source": symbol, "target": sheet["anchor"], "type": type_, "curator_symbol": cell,
            "mechanism": note, "curator_note": note,
            "source_kind": "curated", "species_context": "unknown",
            "justification": sheet["justification"], "supp_source": where,
        }
        dois = dois_in(row)
        if not dois:
            records.append(dict(base, ref=f"CURATED:{origin}/{symbol}", doi=""))
        for doi in dois:
            records.append(dict(base, ref=f"DOI:{doi}", doi=doi))
    return records, notes


def link_type(regulation, default, regulation_map):
    """(type, note). An unreadable regulation falls back to the sheet default and is reported."""
    value = (regulation or "").strip().strip(":").casefold()
    if not value:
        return default, ""
    if value in regulation_map:
        return regulation_map[value], ""
    return default, f"unmapped regulation {regulation.strip()!r}, read as {default}"


def curator_note(sheet, row):
    parts = []
    for column in sheet.get("note_columns", []):
        value = (row.get(column) or "").strip()
        if value:
            parts.append(f"{column}: {value}" if len(sheet.get("note_columns", [])) > 1 else value)
    return " | ".join(parts)


def catalogue_entries(catalogue, rows, resolve=None):
    """({symbol: expert annotations}, notes) from the curator's gene catalogue.

    The catalogue holds no interactions: it says which genes the researcher considers part of
    the calcium toolkit, and what is known about them (see issue #17). Symbols are resolved
    like any other actor, so a row filed under an HGNC alias still matches its node. Two rows
    for the same gene are merged — dropping one would lose curation.
    """
    entries, seen, notes = {}, {}, []
    for row in rows:
        written = (row.get(catalogue["symbol_column"]) or "").strip()
        if not written:
            continue
        symbol = (resolve(written) if resolve else written.upper())
        entry = {}
        for field, columns in catalogue["annotation_columns"].items():
            values = []
            for column in columns:
                value = (row.get(column) or "").strip()
                if value and value not in values:
                    values.append(value)
            if values:
                entry[field] = "; ".join(values)
        if symbol in entries:
            how = (f"{written} listed twice" if written == seen[symbol]
                   else f"{written} and {seen[symbol]} both map to {symbol}")
            notes.append(f"catalogue: {how}, rows merged")
            entries[symbol] = _merge(entries[symbol], entry)
        else:
            entries[symbol] = entry
        seen[symbol] = written
    return entries, notes


def _merge(left, right):
    merged = dict(left)
    for field, value in right.items():
        if field not in merged:
            merged[field] = value
        elif value not in merged[field].split("; "):
            merged[field] = f"{merged[field]}; {value}"
    return merged


def load_supp_config(path):
    return json.loads(Path(path).read_text())


def read_all(config, root, resolve=None):
    """(records, catalogue, notes) for every spreadsheet the config names.

    A missing file or sheet is reported, never fatal: the curator's folder is edited by hand.
    """
    records, notes = [], []
    base = Path(root) / config["dir"]
    for book in config["interactomes"]:
        path = base / book["file"]
        if not path.exists():
            notes.append(f"{book['file']}: file not found in {config['dir']}/, skipped")
            continue
        sheets = read_workbook(path)
        for sheet in book["sheets"]:
            rows = sheets.get(sheet["name"])
            if rows is None:
                notes.append(f"{book['file']}/{sheet['name']}: sheet not found, skipped")
                continue
            if not rows:
                notes.append(f"{book['file']}/{sheet['name']}: sheet is empty")
                continue
            sheet_records, sheet_notes = interaction_records(
                sheet, rows, regulation_map=config["regulation_map"], file_name=book["file"],
                symbol_fixes=config.get("symbol_fixes"))
            records.extend(sheet_records)
            notes.extend(sheet_notes)

    catalogue, cfg = {}, config["catalogue"]
    path = base / cfg["file"]
    if not path.exists():
        notes.append(f"{cfg['file']}: file not found in {config['dir']}/, skipped")
    else:
        rows = read_workbook(path).get(cfg["sheet"], [])
        catalogue, catalogue_notes = catalogue_entries(cfg, rows, resolve=resolve)
        notes.extend(catalogue_notes)
    return records, catalogue, notes


def unresolved_symbols(records, resolver):
    """Curated symbols the resolver cannot map to a gene we know — reported, never dropped."""
    unknown = {}
    for r in records:
        if resolver.resolve(r["source"]) not in resolver.genes:
            unknown.setdefault(r["source"], []).append(r["supp_source"])
    return unknown


def supp_file_stem(supp_source):
    """'interactome STING.xlsx/interactors/row 2' -> 'interactome_sting_interactors'."""
    book, sheet = supp_source.split("/")[:2]
    book = book.rsplit(".", 1)[0]
    return re.sub(r"[^a-z0-9]+", "_", f"{book} {sheet}".casefold()).strip("_")


def catalogue_report(catalogue, node_ids, seen_symbols):
    """How the curator's catalogue overlaps the map built so far (issue #17).

    A catalogue gene linked to an anchor is admitted automatically — the catalogue is itself
    the calcium criterion — so the useful middle group is the genes the corpus has already
    turned up without an anchor link yet: those are the extraction leads.
    """
    in_map = sorted(g for g in catalogue if g in node_ids)
    leads = sorted(g for g in catalogue if g not in node_ids and g in seen_symbols)
    untouched = len(catalogue) - len(in_map) - len(leads)
    lines = [f"Catalogue: {len(catalogue)} genes — {len(in_map)} in the map, "
             f"{len(leads)} seen in the corpus but not yet linked to an anchor, "
             f"{untouched} untouched."]
    if leads:
        shown = ", ".join(leads[:15])
        lines.append(f"  leads: {shown}{', …' if len(leads) > 15 else ''}")
    return lines
