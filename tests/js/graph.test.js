// Shared JS core seam: graph queries used by the review card and the graph page.
const test = require("node:test");
const assert = require("node:assert/strict");
const core = require("../../shared/core.js");

const E = (id, source, target, type = "activation") => ({ interaction_id: id, source, target, type, directed: "true" });
// chain: A -AB- B -BC- C -CD- D -DE- E, plus B -BX- X
const CHAIN = [E("AB", "A", "B"), E("BC", "B", "C"), E("CD", "C", "D"), E("DE", "D", "E"), E("BX", "X", "B")];
const ids = (xs) => xs.map((x) => x.id).sort();

test("1-hop neighbourhood of an interaction includes partners of either endpoint", () => {
  // B has 3 partners and C has 2: neither is a hub beside the other, so both expand
  const n = core.neighbourhood(CHAIN, "BC", { hops: 1 });
  assert.deepEqual(ids(n.nodes), ["A", "B", "C", "D", "X"]);
  assert.deepEqual(ids(n.edges), ["AB", "BC", "BX", "CD"]);
});

test("2-hop neighbourhood reaches one node further", () => {
  const n = core.neighbourhood(CHAIN, "AB", { hops: 2, expandFrom: "both" });
  assert.deepEqual(ids(n.nodes), ["A", "B", "C", "D", "X"]);
  assert.deepEqual(ids(n.edges), ["AB", "BC", "BX", "CD"]);
});

test("nodes carry their distance and the focal edge is flagged", () => {
  const n = core.neighbourhood(CHAIN, "AB", { hops: 2, expandFrom: "both" });
  const dist = Object.fromEntries(n.nodes.map((x) => [x.id, x.distance]));
  assert.deepEqual(dist, { A: 0, B: 0, C: 1, X: 1, D: 2 });
  assert.equal(n.edges.find((e) => e.id === "AB").focal, true);
  assert.equal(n.edges.find((e) => e.id === "BC").focal, false);
});

test("edges carry review status", () => {
  const reviews = { BC: { decision: "keep" }, BX: { decision: "reject" }, CD: { decision: "uncertain" } };
  const n = core.neighbourhood(CHAIN, "AB", { hops: 2, reviews, expandFrom: "both" });
  const status = Object.fromEntries(n.edges.map((e) => [e.id, e.status]));
  assert.deepEqual(status, { AB: "pending", BC: "keep", BX: "reject", CD: "uncertain" });
});

test("by default A-B in the chain shows A's side only, B being three times as connected", () => {
  const n = core.neighbourhood(CHAIN, "AB", { hops: 2 });
  assert.deepEqual(ids(n.nodes), ["A", "B"]);
  assert.equal(n.expandedFrom, "A");
});

test("an isolated interaction has only its two endpoints", () => {
  const n = core.neighbourhood([E("PQ", "P", "Q"), ...CHAIN], "PQ", { hops: 2 });
  assert.deepEqual(ids(n.nodes), ["P", "Q"]);
  assert.deepEqual(ids(n.edges), ["PQ"]);
});

test("large neighbourhoods are capped, keeping the closest nodes", () => {
  const star = [E("AB", "A", "B")];
  for (let k = 0; k < 30; k++) star.push(E("A" + k, "A", "n" + k));
  star.push(E("far", "n0", "far0"));
  const n = core.neighbourhood(star, "AB", { hops: 2, maxNodes: 10, expandFrom: "both" });
  assert.equal(n.nodes.length, 10);
  assert.ok(n.truncated);
  assert.ok(n.nodes.every((x) => x.distance <= 1));
  assert.ok(n.edges.every((e) => n.nodes.some((x) => x.id === e.source) && n.nodes.some((x) => x.id === e.target)));
});

test("shortest path between two actors ignores edge direction", () => {
  const p = core.shortestPath(CHAIN, "E", "X");
  assert.deepEqual(p.nodes, ["E", "D", "C", "B", "X"]);
  assert.deepEqual(p.edges, ["DE", "CD", "BC", "BX"]);
});

test("shortest path is null when actors are disconnected or unknown", () => {
  assert.equal(core.shortestPath([...CHAIN, E("PQ", "P", "Q")], "A", "P"), null);
  assert.equal(core.shortestPath(CHAIN, "A", "ZZZ"), null);
});

test("graph filters: link types, minimum sources, modules, mouse-only (absent list = all)", () => {
  const items = [
    { ...E("1", "A", "B", "activation"), n_sources: "3", has_human_evidence: "true" },
    { ...E("2", "A", "C", "inhibition"), n_sources: "1", has_human_evidence: "true" },
    { ...E("3", "B", "C", "physical_binding"), n_sources: "5", has_human_evidence: "false", has_animal_evidence: "true" },
  ];
  const modules = { A: "soce", B: "sting", C: "metabolite" };
  const ids = (f) => core.applyFilters(items, f, (id) => modules[id]).map((i) => i.interaction_id);
  assert.deepEqual(ids({ types: ["activation", "physical_binding"] }), ["1", "3"]);
  assert.deepEqual(ids({ minSources: 2 }), ["1", "3"]);
  assert.deepEqual(ids({ excludeMouseOnly: true }), ["1", "2"]);
  assert.deepEqual(ids({ modules: ["soce", "sting"] }), ["1"]);
  assert.deepEqual(ids({ minSources: 0 }), ["1", "2", "3"]);
  assert.deepEqual(ids({ types: [] }), [], "an empty selection shows nothing");
  assert.deepEqual(ids({ modules: [] }), []);
});

test("reference links cover literature and every database", () => {
  assert.equal(core.refHref("PMID:30643259"), "https://pubmed.ncbi.nlm.nih.gov/30643259/");
  assert.equal(core.refHref("PMC6340781"), "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6340781/");
  assert.equal(core.refHref("SIGNOR-277299"), "https://signor.uniroma2.it/relation_result.php?id=SIGNOR-277299");
  assert.equal(core.refHref("EBI-2291793"), "https://www.ebi.ac.uk/intact/search?query=EBI-2291793");
  assert.equal(core.refHref("BIOGRID:12"), "https://thebiogrid.org/interaction/12");
  assert.match(core.refHref("OmniPath:STIM1>TRPC1"), /omnipathdb\.org\/interactions\?partners=STIM1,TRPC1/);
  assert.equal(core.refHref("something"), null);
});

test("a deck keeps every card with a foot on that side, so a bridge is in both", () => {
  const items = [
    E("soce", "STIM1", "ORAI1"), E("sting", "STING1", "TBK1"),
    E("bridge", "STIM1", "STING1"), E("loose", "P", "Q"),
  ];
  const modules = { STIM1: "soce", ORAI1: "soce", STING1: "sting", TBK1: "sting", P: "", Q: "" };
  const ids = (f) => core.applyFilters(items, f, (id) => modules[id]).map((i) => i.interaction_id);
  assert.deepEqual(ids({ side: "ca" }), ["soce", "bridge"]);
  assert.deepEqual(ids({ side: "sting" }), ["sting", "bridge"]);
  assert.deepEqual(ids({}), ["soce", "sting", "bridge", "loose"], "no deck chosen shows everything");
});

test("the expression filter keeps the transcriptional layer, both directions of it", () => {
  const items = [
    E("up", "STING1", "STIM1", "expression_regulation_up"),
    E("down", "GSK3B", "ORAI1", "expression_regulation_down"),
    E("bind", "STIM1", "ORAI1", "physical_binding"),
  ];
  const ids = (f) => core.applyFilters(items, f).map((i) => i.interaction_id);
  assert.deepEqual(ids({ expressionOnly: true }), ["up", "down"]);
  assert.deepEqual(ids({ expressionOnly: false }), ["up", "down", "bind"]);
  assert.deepEqual(ids({}), ["up", "down", "bind"]);
});

// A card's preview exists to situate the interaction, and a hub ruins it: STIM1 alone has 274
// partners, so expanding both endpoints drew a hairball the curator could not read.
test("the preview expands the sparser endpoint only, leaving the hub a single node", () => {
  // HUB touches H1..H4; SMALL touches S1; the focal edge joins them
  const edges = [E("focal", "HUB", "SMALL"), E("s1", "SMALL", "S1")];
  for (const n of ["H1", "H2", "H3", "H4"]) edges.push(E("h-" + n, "HUB", n));
  const n = core.neighbourhood(edges, "focal", { hops: 1 });
  assert.deepEqual(n.nodes.map((x) => x.id).sort(), ["HUB", "S1", "SMALL"]);
  assert.equal(n.expandedFrom, "SMALL");
});

test("the preview still expands both endpoints when neither is a hub, or when asked", () => {
  const edges = [E("focal", "A", "B"), E("a1", "A", "A1"), E("b1", "B", "B1")];
  const tie = core.neighbourhood(edges, "focal", { hops: 1 });
  assert.deepEqual(tie.nodes.map((x) => x.id).sort(), ["A", "A1", "B", "B1"]);
  assert.equal(tie.expandedFrom, null);
  const both = core.neighbourhood(
    [E("focal", "HUB", "SMALL"), E("h", "HUB", "H1")], "focal", { hops: 1, expandFrom: "both" });
  assert.deepEqual(both.nodes.map((x) => x.id).sort(), ["H1", "HUB", "SMALL"]);
});

test("an actor's partner count is distinct partners, not edges", () => {
  const edges = [E("1", "A", "B"), E("2", "A", "B", "physical_binding"), E("3", "A", "C")];
  assert.equal(core.neighbourCount(edges, "A"), 2);
  assert.equal(core.neighbourCount(edges, "C"), 1);
  assert.equal(core.neighbourCount(edges, "ZZZ"), 0);
});
