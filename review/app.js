// Review app UI: thin layer over CamapCore.
(function () {
  "use strict";
  const STORAGE_KEY = "camap.reviews.v1";
  const FILTER_KEY = "camap.filters.v1";
  const data = window.CAMAP || {};
  const interactions = data.interactions || [];
  const evidence = data.evidence || [];
  const nodesById = Object.fromEntries((data.nodes || []).map((n) => [n.id, n]));
  const evidenceByInteraction = groupBy(evidence, "interaction_id");

  const session = CamapCore.createSession({ interactions, reviews: loadReviews(), filters: load(FILTER_KEY) });

  const $ = (id) => document.getElementById(id);
  const MODULES = {
    soce: "SOCE / STIM1", sting: "STING / innate immunity", ca_stores: "Ca²⁺ stores & pumps",
    effectors: "Ca²⁺ effectors", bridge: "STIM1–STING bridge", metabolite: "Metabolite",
  };
  const SPECIES = {
    human: "🧍 human", in_vitro_human_cells: "🧫 human cells", mouse: "🐭 mouse", rat: "🐀 rat",
    other: "other species", unknown: "species ?",
  };
  const CALCIUM = { GO: "GO annotation", text: "mentioned in source text", both: "GO annotation + source text" };

  function groupBy(rows, key) {
    const out = {};
    for (const r of rows) (out[r[key]] = out[r[key]] || []).push(r);
    return out;
  }

  function load(key) {
    try {
      return JSON.parse(localStorage.getItem(key) || "{}");
    } catch (e) {
      return {};
    }
  }

  function store(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      /* storage unavailable: export remains the durable path */
    }
  }

  function loadReviews() {
    return load(STORAGE_KEY);
  }

  function saveReviews() {
    store(STORAGE_KEY, session.reviews());
  }

  function el(tag, attrs = {}, ...children) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") e.className = v;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v);
    }
    for (const c of children.flat()) if (c != null) e.append(c.nodeType ? c : String(c));
    return e;
  }

  function refLink(ev) {
    const ref = ev.ref || "";
    let href = null;
    if (ref.startsWith("PMID:")) href = "https://pubmed.ncbi.nlm.nih.gov/" + ref.slice(5) + "/";
    else if (ref.startsWith("PMC")) href = "https://www.ncbi.nlm.nih.gov/pmc/articles/" + ref + "/";
    else if (ev.doi) href = "https://doi.org/" + ev.doi;
    const label = [ev.first_author, ev.year].filter(Boolean).join(" ") || ref;
    return href ? el("a", { href, target: "_blank", rel: "noopener" }, label + " · " + ref) : el("span", {}, label);
  }

  function endpoint(id) {
    const n = nodesById[id] || {};
    return el("div", { class: "endpoint" },
      el("div", { class: "symbol" }, n.symbol || id),
      n.name ? el("div", { class: "name" }, n.name) : null,
      n.module ? el("span", { class: "module m-" + n.module }, MODULES[n.module] || n.module) : null);
  }

  function sentence(ev) {
    const ok = ev.sentence_verified === "true";
    return el("blockquote", { class: ok ? "verified" : "unverified" },
      ev.sentence,
      ok ? null : el("div", { class: "warn" }, "⚠️ Not found verbatim in the source text"));
  }

  function renderCard(i) {
    const evs = evidenceByInteraction[i.interaction_id] || [];
    return el("article", { class: "card" },
      el("section", { class: "edge" },
        endpoint(i.source),
        el("div", { class: "link " + i.type },
          el("span", { class: "link-type" }, i.type.replace(/_/g, " ")),
          el("span", { class: "arrow" }, i.directed === "true" ? "⟶" : "⟷")),
        endpoint(i.target)),
      i.mechanism ? el("p", { class: "mechanism" }, i.mechanism) : null,
      el("div", { class: "tags" },
        el("span", { class: "tag" }, "Calcium evidence: " + (CALCIUM[i.calcium_evidence] || "none")),
        i.has_human_evidence === "false" ? el("span", { class: "tag warn-tag" }, "Non-human evidence only") : null),
      el("section", { class: "why" }, el("h3", {}, "Why it matters"), el("p", {}, i.justification || "—")),
      el("section", { class: "sources" },
        el("h3", {}, `Sources (${i.n_sources}) · ${i.n_pubs} publication(s) · ${i.n_db} database(s)`),
        el("ul", {}, evs.map((ev) =>
          el("li", { class: "evidence" },
            el("div", { class: "meta" }, el("span", { class: "badge " + ev.source_kind }, ev.source_kind), refLink(ev),
              el("span", { class: "species s-" + ev.species_context }, SPECIES[ev.species_context] || ev.species_context)),
            ev.sentence ? sentence(ev) : el("p", { class: "muted" }, "No sentence"))))));
  }

  function render() {
    const c = session.counts();
    $("progress").textContent = `${c.reviewed}/${c.total} reviewed · ✓ ${c.keep} · ✕ ${c.reject}`;
    const stage = $("stage");
    stage.replaceChildren();
    const card = session.current();
    if (card) stage.append(renderCard(card));
    else stage.append(el("div", { class: "empty" }, interactions.length ? "All interactions reviewed 🎉" : "No interactions loaded. Run the pipeline build first."));
    $("btn-keep").disabled = $("btn-reject").disabled = !card;
  }

  function decide(decision) {
    if (!session.current()) return;
    session.decide(decision);
    saveReviews();
    render();
  }

  function download(name, text, type) {
    const a = el("a", { href: URL.createObjectURL(new Blob([text], { type })), download: name });
    document.body.append(a);
    a.click();
    a.remove();
  }

  const filterMouse = $("filter-mouse");
  filterMouse.checked = !!load(FILTER_KEY).excludeMouseOnly;
  filterMouse.addEventListener("change", () => {
    const filters = { excludeMouseOnly: filterMouse.checked };
    session.setFilters(filters);
    store(FILTER_KEY, filters);
    render();
  });

  $("btn-keep").addEventListener("click", () => decide("keep"));
  $("btn-reject").addEventListener("click", () => decide("reject"));
  $("export-kept").addEventListener("click", () =>
    download("kept_interactions.csv", CamapCore.keptCsv(interactions, session.reviews()), "text/csv"));
  document.addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea")) return;
    if (e.key === "ArrowRight") decide("keep");
    if (e.key === "ArrowLeft") decide("reject");
  });

  render();
})();
