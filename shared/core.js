// DOM-free core shared by the review app and the graph page.
// Loaded as a plain <script> in the browser (window.CamapCore) and via require() in tests.
(function (root, factory) {
  const core = factory();
  if (typeof module === "object" && module.exports) module.exports = core;
  else root.CamapCore = core;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const INTERACTION_COLUMNS = [
    "interaction_id", "source", "target", "type", "directed", "mechanism", "n_sources", "n_pubs",
    "n_db", "has_human_evidence", "calcium_evidence", "justification", "conflict_with",
    "evidence_fingerprint",
  ];
  const REVIEW_COLUMNS = ["decision", "comment", "reviewer", "reviewed_at"];

  // ---------- CSV ----------

  function parseCsv(text) {
    const records = [];
    let row = [], field = "", inQuotes = false, i = 0;
    while (i < text.length) {
      const c = text[i];
      if (inQuotes) {
        if (c === '"' && text[i + 1] === '"') { field += '"'; i += 2; continue; }
        if (c === '"') { inQuotes = false; i++; continue; }
        field += c; i++; continue;
      }
      if (c === '"') { inQuotes = true; i++; continue; }
      if (c === ",") { row.push(field); field = ""; i++; continue; }
      if (c === "\r" && text[i + 1] === "\n") i++;
      if (c === "\n" || c === "\r") { row.push(field); records.push(row); row = []; field = ""; i++; continue; }
      field += c; i++;
    }
    if (field !== "" || row.length) { row.push(field); records.push(row); }
    const header = records.shift() || [];
    return records
      .filter((r) => !(r.length === 1 && r[0] === ""))
      .map((r) => Object.fromEntries(header.map((h, k) => [h, r[k] ?? ""])));
  }

  function csvField(value) {
    const s = value == null ? "" : String(value);
    return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function toCsv(rows, columns) {
    const lines = [columns.map(csvField).join(",")];
    for (const r of rows) lines.push(columns.map((c) => csvField(r[c])).join(","));
    return lines.join("\r\n") + "\r\n";
  }

  // ---------- review session ----------

  function createSession({ interactions, reviews = {}, reviewer = "", now = () => new Date().toISOString() }) {
    const state = { reviews: { ...reviews } };
    const isPending = (i) => !state.reviews[i.interaction_id];

    function queue() {
      return interactions.filter(isPending);
    }

    return {
      current() {
        return queue()[0] || null;
      },
      decide(decision, comment = "") {
        const card = queue()[0];
        if (!card) return;
        state.reviews[card.interaction_id] = {
          decision, comment, reviewer, reviewed_at: now(),
          evidence_fingerprint: card.evidence_fingerprint,
        };
      },
      reviews() {
        return state.reviews;
      },
      counts() {
        const c = { total: interactions.length, reviewed: 0, remaining: 0, keep: 0, reject: 0, uncertain: 0 };
        for (const i of interactions) {
          const r = state.reviews[i.interaction_id];
          if (r) { c.reviewed++; c[r.decision]++; } else c.remaining++;
        }
        return c;
      },
    };
  }

  function keptRows(interactions, reviews) {
    return interactions
      .filter((i) => reviews[i.interaction_id] && reviews[i.interaction_id].decision === "keep")
      .map((i) => {
        const r = reviews[i.interaction_id];
        return { ...i, decision: r.decision, comment: r.comment || "", reviewer: r.reviewer || "", reviewed_at: r.reviewed_at || "" };
      });
  }

  function keptCsv(interactions, reviews) {
    return toCsv(keptRows(interactions, reviews), INTERACTION_COLUMNS.concat(REVIEW_COLUMNS));
  }

  return { parseCsv, toCsv, createSession, keptRows, keptCsv, INTERACTION_COLUMNS, REVIEW_COLUMNS };
});
