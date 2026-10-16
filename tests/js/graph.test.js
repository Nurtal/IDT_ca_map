// Shared JS core seam: graph queries used by the review card and the graph page.
const test = require("node:test");
const assert = require("node:assert/strict");
const core = require("../../shared/core.js");

const E = (id, source, target, type = "activation") => ({ interaction_id: id, source, target, type, directed: "true" });
// chain: A -AB- B -BC- C -CD- D -DE- E, plus B -BX- X
const CHAIN = [E("AB", "A", "B"), E("BC", "B", "C"), E("CD", "C", "D"), E("DE", "D", "E"), E("BX", "X", "B")];
const ids = (xs) => xs.map((x) => x.id).sort();

test("1-hop neighbourhood of an interaction includes partners of either endpoint", () => {
  const n = core.neighbourhood(CHAIN, "BC", { hops: 1 });
  assert.deepEqual(ids(n.nodes), ["A", "B", "C", "D", "X"]);
  assert.deepEqual(ids(n.edges), ["AB", "BC", "BX", "CD"]);
});

test("2-hop neighbourhood reaches one node further", () => {
  const n = core.neighbourhood(CHAIN, "AB", { hops: 2 });
  assert.deepEqual(ids(n.nodes), ["A", "B", "C", "D", "X"]);
  assert.deepEqual(ids(n.edges), ["AB", "BC", "BX", "CD"]);
});

test("nodes carry their distance and the focal edge is flagged", () => {
  const n = core.neighbourhood(CHAIN, "AB", { hops: 2 });
  const dist = Object.fromEntries(n.nodes.map((x) => [x.id, x.distance]));
  assert.deepEqual(dist, { A: 0, B: 0, C: 1, X: 1, D: 2 });
  assert.equal(n.edges.find((e) => e.id === "AB").focal, true);
  assert.equal(n.edges.find((e) => e.id === "BC").focal, false);
});

test("edges carry review status", () => {
  const reviews = { BC: { decision: "keep" }, BX: { decision: "reject" }, CD: { decision: "uncertain" } };
  const n = core.neighbourhood(CHAIN, "AB", { hops: 2, reviews });
  const status = Object.fromEntries(n.edges.map((e) => [e.id, e.status]));
  assert.deepEqual(status, { AB: "pending", BC: "keep", BX: "reject", CD: "uncertain" });
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
  const n = core.neighbourhood(star, "AB", { hops: 2, maxNodes: 10 });
  assert.equal(n.nodes.length, 10);
  assert.ok(n.truncated);
  assert.ok(n.nodes.every((x) => x.distance <= 1));
  assert.ok(n.edges.every((e) => n.nodes.some((x) => x.id === e.source) && n.nodes.some((x) => x.id === e.target)));
});
