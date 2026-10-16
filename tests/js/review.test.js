// Shared JS core seam: review session state and exports, no DOM.
const test = require("node:test");
const assert = require("node:assert/strict");
const core = require("../../shared/core.js");

const I = (id, extra = {}) => ({
  interaction_id: id, source: "STIM1", target: "STING1", type: "inhibition", directed: "true",
  mechanism: "ER retention", n_sources: "1", n_pubs: "1", n_db: "0", has_human_evidence: "true",
  calcium_evidence: "text", justification: "Bridge", conflict_with: "", evidence_fingerprint: "fp-" + id,
  ...extra,
});

test("session presents pending cards in order and advances on decision", () => {
  const s = core.createSession({ interactions: [I("a"), I("b")], reviewer: "nf" });
  assert.equal(s.current().interaction_id, "a");
  s.decide("keep");
  assert.equal(s.current().interaction_id, "b");
  s.decide("reject");
  assert.equal(s.current(), null);
  assert.deepEqual(s.counts(), { total: 2, reviewed: 2, remaining: 0, keep: 1, reject: 1, uncertain: 0 });
});

test("decisions record reviewer, timestamp and evidence fingerprint", () => {
  const s = core.createSession({ interactions: [I("a")], reviewer: "nf", now: () => "2026-10-16T10:00:00Z" });
  s.decide("keep", "solid");
  assert.deepEqual(s.reviews().a, {
    decision: "keep", comment: "solid", reviewer: "nf",
    reviewed_at: "2026-10-16T10:00:00Z", evidence_fingerprint: "fp-a",
  });
});

test("already reviewed interactions are not presented again", () => {
  const reviews = { a: { decision: "keep", evidence_fingerprint: "fp-a" } };
  const s = core.createSession({ interactions: [I("a"), I("b")], reviews });
  assert.equal(s.current().interaction_id, "b");
});

test("kept CSV contains only kept interactions with review columns appended", () => {
  const interactions = [I("a", { mechanism: 'binds, "tightly"\nat ER' }), I("b")];
  const reviews = {
    a: { decision: "keep", comment: "ok", reviewer: "nf", reviewed_at: "t1" },
    b: { decision: "reject", comment: "", reviewer: "nf", reviewed_at: "t2" },
  };
  const rows = core.parseCsv(core.keptCsv(interactions, reviews));
  assert.equal(rows.length, 1);
  assert.equal(rows[0].interaction_id, "a");
  assert.equal(rows[0].mechanism, 'binds, "tightly"\nat ER');
  assert.equal(rows[0].decision, "keep");
  assert.equal(rows[0].comment, "ok");
  assert.equal(rows[0].reviewer, "nf");
  assert.equal(rows[0].reviewed_at, "t1");
});

test("parseCsv handles quoted fields, escaped quotes, CRLF and multiline values", () => {
  const rows = core.parseCsv('a,b\r\n"x, y","say ""hi""\nthere"\r\n1,\n');
  assert.deepEqual(rows, [{ a: "x, y", b: 'say "hi"\nthere' }, { a: "1", b: "" }]);
});

test("mouse-only filter hides interactions without human evidence", () => {
  const items = [I("a"), I("b", { has_human_evidence: "false" })];
  assert.deepEqual(core.applyFilters(items, { excludeMouseOnly: true }).map((i) => i.interaction_id), ["a"]);
  assert.equal(core.applyFilters(items, {}).length, 2);
});

test("session skips filtered-out cards and counts only visible ones", () => {
  const s = core.createSession({
    interactions: [I("a", { has_human_evidence: "false" }), I("b")],
    filters: { excludeMouseOnly: true },
  });
  assert.equal(s.current().interaction_id, "b");
  assert.equal(s.counts().total, 1);
  s.setFilters({});
  assert.equal(s.current().interaction_id, "a");
  assert.equal(s.counts().total, 2);
});

test("uncertain cards leave the main stack and form their own stack", () => {
  const s = core.createSession({ interactions: [I("a"), I("b"), I("c")] });
  s.decide("uncertain");
  assert.equal(s.current().interaction_id, "b");
  assert.equal(s.counts().uncertain, 1);
  s.setMode("uncertain");
  assert.equal(s.current().interaction_id, "a");
  s.decide("keep");
  assert.equal(s.current(), null);
  assert.equal(s.reviews().a.decision, "keep");
  s.setMode("pending");
  assert.equal(s.current().interaction_id, "b");
});

test("undo restores the previous state, including an overwritten uncertain decision", () => {
  const s = core.createSession({ interactions: [I("a"), I("b")] });
  s.decide("uncertain", "check figure 3");
  s.decide("reject");
  assert.equal(s.undo(), "b");
  assert.equal(s.current().interaction_id, "b");
  s.setMode("uncertain");
  s.decide("keep");
  assert.equal(s.undo(), "a");
  assert.equal(s.reviews().a.decision, "uncertain");
  assert.equal(s.reviews().a.comment, "check figure 3");
  assert.equal(s.undo(), "a");
  assert.equal(s.reviews().a, undefined);
  assert.equal(s.undo(), null);
});

test("exported reviews re-imported into a fresh session give identical state", () => {
  const items = [I("a"), I("b"), I("c")];
  const s = core.createSession({ interactions: items, reviewer: "nf" });
  s.decide("keep", "good");
  s.decide("uncertain");
  const json = s.exportReviews();
  const t = core.createSession({ interactions: items });
  t.importReviews(json);
  assert.deepEqual(t.reviews(), s.reviews());
  assert.deepEqual(t.counts(), s.counts());
  assert.equal(t.current().interaction_id, "c");
});

test("import keeps the most recent decision when both sides reviewed a card", () => {
  const items = [I("a")];
  const s = core.createSession({ interactions: items, reviews: { a: { decision: "reject", reviewed_at: "2026-01-02" } } });
  s.importReviews(JSON.stringify({ version: 1, reviews: { a: { decision: "keep", reviewed_at: "2026-01-01" } } }));
  assert.equal(s.reviews().a.decision, "reject");
  s.importReviews(JSON.stringify({ version: 1, reviews: { a: { decision: "keep", reviewed_at: "2026-01-03" } } }));
  assert.equal(s.reviews().a.decision, "keep");
});

test("import rejects files that are not review exports", () => {
  const s = core.createSession({ interactions: [I("a")] });
  assert.throws(() => s.importReviews('{"hello": 1}'), /not a review export/);
});
