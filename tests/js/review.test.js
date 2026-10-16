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
