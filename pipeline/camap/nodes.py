"""Actor normalization (HGNC / ChEBI), node annotations and the inclusion rule."""
import json
import re
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "seeds.json"


def load_config(path=DEFAULT_CONFIG):
    return json.loads(Path(path).read_text())


class Resolver:
    """Maps any gene/protein/metabolite name to a canonical node id."""

    def __init__(self, cache_dir, config):
        self.genes = {}
        self.aliases = {}
        hgnc = Path(cache_dir) / "hgnc" / "hgnc_complete_set.json" if cache_dir else None
        if hgnc and hgnc.exists():
            docs = json.loads(hgnc.read_text())["response"]["docs"]
            self.genes = {d["symbol"]: d for d in docs}
            prev, alias = {}, {}
            for d in docs:
                for p in d.get("prev_symbol") or []:
                    prev.setdefault(p.upper(), set()).add(d["symbol"])
                for a in d.get("alias_symbol") or []:
                    alias.setdefault(a.upper(), set()).add(d["symbol"])
            # previous symbols win over aliases; ambiguous names are not resolved
            for table in (alias, prev):
                for name, targets in table.items():
                    if len(targets) == 1:
                        self.aliases[name] = next(iter(targets))
        self.metabolites = {m["id"]: m for m in config.get("metabolites", [])}
        self.metabolite_names = {}
        for m in self.metabolites.values():
            for s in [m["symbol"], *m.get("synonyms", [])]:
                self.metabolite_names[s.casefold()] = m["id"]

    def resolve(self, name):
        name = name.strip()
        if name.casefold() in self.metabolite_names:
            return self.metabolite_names[name.casefold()]
        if name in self.metabolites:
            return name
        upper = name.upper()
        if upper in self.genes:
            return upper
        return self.aliases.get(upper, upper)

    def names(self, node_id):
        """Every name an actor may appear under in a text."""
        if node_id in self.metabolites:
            m = self.metabolites[node_id]
            return [m["symbol"], *m.get("synonyms", [])]
        g = self.genes.get(node_id, {})
        return [node_id, *(g.get("prev_symbol") or []), *(g.get("alias_symbol") or [])]

    def gene(self, symbol):
        return self.genes.get(symbol, {})


class Annotations:
    def __init__(self, cache_dir):
        self.dir = Path(cache_dir) / "annotations" if cache_dir else None

    def get(self, node_id):
        if not self.dir:
            return {}
        path = self.dir / f"{node_id.replace(':', '_')}.json"
        return json.loads(path.read_text()) if path.exists() else {}


class Universe:
    """Seeds, anchors and the calcium criterion, as configured."""

    def __init__(self, config):
        self.anchors = set(config["anchors"])
        self.seeds = {s["symbol"]: s for s in config["seeds"]}
        for m in config.get("metabolites", []):
            self.seeds[m["id"]] = {"symbol": m["symbol"], "module": "metabolite", "level": m.get("level", 1)}
        self.calcium_re = re.compile(config["calcium_text_pattern"])

    def level(self, node_id):
        return self.seeds.get(node_id, {}).get("level")

    def mentions_calcium(self, sentence):
        return bool(sentence and self.calcium_re.search(sentence))


def select_nodes(universe, interactions, go_calcium, curated_calcium=None):
    """Apply the inclusion rule. `interactions` are dicts with source, target, _text_calcium.

    A gene of the curator's catalogue is calcium-related by her own judgement (issue #17),
    on a par with a GO annotation or a calcium term in the supporting sentence.
    """
    curated_calcium = curated_calcium or (lambda node: False)
    neighbours, text_calcium = {}, {}
    for i in interactions:
        for a, b in ((i["source"], i["target"]), (i["target"], i["source"])):
            neighbours.setdefault(a, set()).add(b)
            text_calcium[a] = text_calcium.get(a, False) or i["_text_calcium"]

    kept = set()
    for node, nbrs in neighbours.items():
        level = universe.level(node)
        touches_anchor = bool(nbrs & universe.anchors)
        if level == 1:
            kept.add(node)
        elif level == 2:
            if touches_anchor:
                kept.add(node)
        elif touches_anchor and (go_calcium(node) or text_calcium[node] or curated_calcium(node)):
            kept.add(node)
    return kept, neighbours


def module_of(universe, node_id, neighbours):
    if node_id in universe.seeds:
        return universe.seeds[node_id]["module"]
    modules = {universe.seeds[a]["module"] for a in neighbours.get(node_id, ()) if a in universe.anchors}
    if len(modules) > 1:
        return "bridge"
    return next(iter(modules), "")
