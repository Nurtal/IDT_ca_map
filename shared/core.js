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

  const LABELS = {
    modules: {
      soce: "SOCE / STIM1", sting: "STING / innate immunity", ca_stores: "Ca²⁺ stores & pumps",
      effectors: "Ca²⁺ effectors", bridge: "STIM1–STING bridge", metabolite: "Metabolite",
    },
    species: {
      human: "🧍 human", in_vitro_human_cells: "🧫 human cells", mouse: "🐭 mouse", rat: "🐀 rat",
      other: "other species", unknown: "species ?",
    },
    calcium: { GO: "GO annotation", text: "mentioned in source text", both: "GO annotation + source text" },
  };

  // Web page of a literature or database reference, or null.
  function refHref(ref) {
    ref = ref || "";
    if (ref.startsWith("PMID:")) return "https://pubmed.ncbi.nlm.nih.gov/" + ref.slice(5) + "/";
    if (ref.startsWith("PMC")) return "https://www.ncbi.nlm.nih.gov/pmc/articles/" + ref + "/";
    if (ref.startsWith("SIGNOR-")) return "https://signor.uniroma2.it/relation_result.php?id=" + ref;
    if (ref.startsWith("EBI-")) return "https://www.ebi.ac.uk/intact/search?query=" + ref;
    if (ref.startsWith("BIOGRID:")) return "https://thebiogrid.org/interaction/" + ref.slice(8);
    if (ref.startsWith("OmniPath:")) {
      const [a, b] = ref.slice(9).split(">");
      return "https://omnipathdb.org/interactions?partners=" + a + "," + b + "&genesymbols=yes&fields=sources,references";
    }
    return null;
  }

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

  // ---------- graph queries ----------

  function adjacency(interactions) {
    const adj = new Map();
    const add = (a, b) => (adj.get(a) || adj.set(a, new Set()).get(a)).add(b);
    for (const i of interactions) { add(i.source, i.target); add(i.target, i.source); }
    return adj;
  }

  // Nodes within `hops` of either endpoint of the focal interaction, and the
  // interactions among them, each tagged with its review status.
  function neighbourhood(interactions, focalId, { hops = 2, reviews = {}, maxNodes = 60 } = {}) {
    const focal = interactions.find((i) => i.interaction_id === focalId);
    if (!focal) return { nodes: [], edges: [], truncated: false };
    const adj = adjacency(interactions);
    const distance = new Map([[focal.source, 0], [focal.target, 0]]);
    let frontier = [focal.source, focal.target];
    for (let d = 1; d <= hops; d++) {
      const next = [];
      for (const n of frontier) {
        for (const m of [...(adj.get(n) || [])].sort()) {
          if (!distance.has(m)) { distance.set(m, d); next.push(m); }
        }
      }
      frontier = next;
    }
    let ordered = [...distance.entries()].sort((a, b) => a[1] - b[1] || (a[0] < b[0] ? -1 : 1));
    const truncated = ordered.length > maxNodes;
    ordered = ordered.slice(0, maxNodes);
    const keep = new Map(ordered);
    const edges = interactions
      .filter((i) => keep.has(i.source) && keep.has(i.target))
      .map((i) => ({
        id: i.interaction_id, source: i.source, target: i.target, type: i.type, directed: i.directed,
        focal: i.interaction_id === focalId,
        status: (reviews[i.interaction_id] || {}).decision || "pending",
      }));
    return { nodes: ordered.map(([id, d]) => ({ id, distance: d })), edges, truncated };
  }

  // Fewest-hops path between two actors (direction ignored). Returns {nodes, edges} or null.
  function shortestPath(interactions, from, to) {
    const links = new Map();
    for (const i of interactions) {
      for (const [a, b] of [[i.source, i.target], [i.target, i.source]]) {
        (links.get(a) || links.set(a, []).get(a)).push([b, i.interaction_id]);
      }
    }
    if (!links.has(from) || !links.has(to)) return null;
    const parent = new Map([[from, null]]);
    let frontier = [from];
    while (frontier.length && !parent.has(to)) {
      const next = [];
      for (const n of frontier) {
        for (const [m, edge] of links.get(n).slice().sort((x, y) => (x[0] < y[0] ? -1 : 1))) {
          if (!parent.has(m)) { parent.set(m, [n, edge]); next.push(m); }
        }
      }
      frontier = next;
    }
    if (!parent.has(to)) return null;
    const nodes = [to], edges = [];
    for (let cur = to; parent.get(cur); cur = parent.get(cur)[0]) {
      edges.push(parent.get(cur)[1]);
      nodes.push(parent.get(cur)[0]);
    }
    return { nodes: nodes.reverse(), edges: edges.reverse() };
  }

  // ---------- filters ----------

  // filters: {excludeMouseOnly, types: [...], minSources, modules: [...]};
  // an absent (null/undefined) list means "all", an empty list means "none".
  function applyFilters(interactions, filters = {}, moduleOf = () => "") {
    const types = Array.isArray(filters.types) ? new Set(filters.types) : null;
    const modules = Array.isArray(filters.modules) ? new Set(filters.modules) : null;
    const minSources = Number(filters.minSources) || 0;
    return interactions.filter((i) =>
      !(filters.excludeMouseOnly && i.has_human_evidence === "false") &&
      (!types || types.has(i.type)) &&
      Number(i.n_sources || 0) >= minSources &&
      (!modules || (modules.has(moduleOf(i.source)) && modules.has(moduleOf(i.target)))));
  }

  // ---------- review session ----------

  function createSession({ interactions, reviews = {}, reviewer = "", filters = {}, now = () => new Date().toISOString() }) {
    const state = { reviews: { ...reviews }, filters: { ...filters }, mode: "pending", history: [], pinned: null };
    const visible = () => applyFilters(interactions, state.filters);
    const hasNewEvidence = (i) => {
      const r = state.reviews[i.interaction_id];
      return !!(r && r.evidence_fingerprint && i.evidence_fingerprint && r.evidence_fingerprint !== i.evidence_fingerprint);
    };
    const inMode = {
      pending: (i) => !state.reviews[i.interaction_id] || hasNewEvidence(i),
      uncertain: (i) => (state.reviews[i.interaction_id] || {}).decision === "uncertain",
    };

    const reviewedAt = (i) => (state.reviews[i.interaction_id] || {}).reviewed_at || "";

    function queue() {
      let q = visible().filter(inMode[state.mode]);
      // uncertain stack: oldest deferral first, so deferring again moves a card to the back
      if (state.mode === "uncertain") q = q.slice().sort((a, b) => (reviewedAt(a) < reviewedAt(b) ? -1 : reviewedAt(a) > reviewedAt(b) ? 1 : 0));
      const pinned = state.pinned && interactions.find((i) => i.interaction_id === state.pinned);
      return pinned ? [pinned, ...q.filter((i) => i !== pinned)] : q;
    }

    function restore(id, previous) {
      if (previous) state.reviews[id] = previous;
      else delete state.reviews[id];
    }

    return {
      current() {
        return queue()[0] || null;
      },
      decide(decision, comment = "") {
        const card = queue()[0];
        if (!card) return;
        const id = card.interaction_id;
        state.history.push({ id, previous: state.reviews[id] });
        state.reviews[id] = {
          decision, comment, reviewer, reviewed_at: now(),
          evidence_fingerprint: card.evidence_fingerprint,
        };
        state.pinned = null;
      },
      jumpTo(id) {
        state.pinned = id;
      },
      hasNewEvidence,
      undo() {
        const last = state.history.pop();
        if (!last) return null;
        restore(last.id, last.previous);
        return last.id;
      },
      reviews() {
        return state.reviews;
      },
      setFilters(f) {
        state.filters = { ...f };
      },
      setMode(mode) {
        if (!inMode[mode]) throw new Error("unknown mode " + mode);
        state.mode = mode;
      },
      mode() {
        return state.mode;
      },
      exportReviews() {
        return JSON.stringify({ version: 1, exported_at: now(), reviews: state.reviews }, null, 1);
      },
      importReviews(json) {
        const data = JSON.parse(json);
        if (!data || data.version !== 1 || typeof data.reviews !== "object") throw new Error("not a review export");
        for (const [id, r] of Object.entries(data.reviews)) {
          const mine = state.reviews[id];
          if (!mine || (r.reviewed_at || "") > (mine.reviewed_at || "")) state.reviews[id] = r;
        }
        state.history = [];
      },
      counts() {
        const shown = visible();
        const c = { total: shown.length, reviewed: 0, remaining: 0, keep: 0, reject: 0, uncertain: 0 };
        for (const i of shown) {
          const r = state.reviews[i.interaction_id];
          if (r && !hasNewEvidence(i)) { c.reviewed++; c[r.decision]++; } else c.remaining++;
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

  return { LABELS, refHref, parseCsv, toCsv, neighbourhood, shortestPath, applyFilters, createSession, keptRows, keptCsv, INTERACTION_COLUMNS, REVIEW_COLUMNS };
});
