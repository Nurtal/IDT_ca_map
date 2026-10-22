"""The self-contained copy of the review app, for a PC that has no pipeline.

The two pages load their siblings by relative path (`../data/nodes.js`, `../vendor/…`), so a
copy that keeps `review/` alone, or an HTML file opened from inside a ZIP, has nothing to show.
This writes one zip that extracts into a single folder holding exactly what the pages read —
and nothing else, so the curator is never carrying the raw records or the queue around.
"""
import zipfile

# every directory the two pages reference, and the built data files they load
DIRS = ("review", "graph", "shared", "vendor")
DATA = ("nodes.js", "interactions.js", "evidence.js", "graph_data.js")
# graph_data.js is written by `cli.py graph` from the curator's own export, so an absent one
# is a graph page with nothing kept yet, not a broken copy
REQUIRED_DATA = ("nodes.js", "interactions.js", "evidence.js")


def bundle_paths(root):
    """Relative paths to carry, sorted. Raises FileNotFoundError when the build is missing."""
    paths = []
    for name in DIRS:
        d = root / name
        if not d.is_dir():
            raise FileNotFoundError(f"{name}/ is missing from {root}")
        paths += [str(p.relative_to(root)) for p in sorted(d.rglob("*")) if p.is_file()]
    for name in DATA:
        p = root / "data" / name
        if p.is_file():
            paths.append(str(p.relative_to(root)))
        elif name in REQUIRED_DATA:
            raise FileNotFoundError(f"data/{name} is missing: run `python3 pipeline/cli.py build` first")
    return sorted(paths)


def write_bundle(root, dest, folder="camap-review"):
    """Write the bundle as a zip whose every entry sits under `folder`. Returns the paths."""
    paths = bundle_paths(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in paths:
            z.write(root / rel, f"{folder}/{rel}")
    return paths
