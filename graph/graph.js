// Global interaction graph: kept interactions rendered with Cytoscape.js + fcose.
(function () {
  "use strict";
  const KEYS = { theme: "camap.theme", filters: "camap.graph.filters.v2" };
  const MODULES = { ...CamapCore.LABELS.modules, "": "Other" };
  const SPECIES = CamapCore.LABELS.species;
  const { refHref } = CamapCore;
  const { el, link, load, store, download } = CamapUI;
  const LINK_TYPES = [
    "activation", "inhibition", "physical_binding", "phosphorylation", "ubiquitination",
    "translocation/trafficking", "expression_regulation_up", "expression_regulation_down",
    "coexpression", "Ca2+_flux", "unknown_regulation",
  ];

  if (window.cytoscapeFcose) cytoscape.use(window.cytoscapeFcose);
  // cytoscape-svg registers itself when loaded after cytoscape

  const data = window.CAMAP || {};
  const nodesById = Object.fromEntries((data.nodes || []).map((n) => [n.id, n]));
  const evidenceByInteraction = {};
  for (const e of data.evidence || []) (evidenceByInteraction[e.interaction_id] = evidenceByInteraction[e.interaction_id] || []).push(e);
  let kept = data.kept || [];
  // types/modules: null = all, [] = none (see CamapCore.applyFilters)
  let filters = { excludeMouseOnly: false, minSources: 1, types: null, modules: null, sourceKinds: null, ...load(KEYS.filters, {}) };
  let cy = null;
  window.__camapGraph = () => cy; // handle for debugging and headless smoke checks
  let pathHighlight = null;

  const $ = (id) => document.getElementById(id);
  const moduleOf = (id) => (nodesById[id] || {}).module || "";

  // ---------- helpers ----------

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function label(id) {
    return (nodesById[id] || {}).symbol || id;
  }

  // ---------- graph ----------

  function visibleInteractions() {
    return CamapCore.applyFilters(kept, filters, moduleOf);
  }

  function elements(items) {
    const degree = {};
    for (const i of items) for (const n of [i.source, i.target]) degree[n] = (degree[n] || 0) + 1;
    return [
      ...Object.keys(degree).map((id) => ({
        data: { id, label: label(id), module: moduleOf(id) || "none", degree: degree[id],
          size: 18 + 7 * Math.sqrt(degree[id]), seed: (nodesById[id] || {}).is_seed === "true" },
      })),
      ...items.map((i) => ({
        data: { id: i.interaction_id, source: i.source, target: i.target, type: i.type,
          directed: i.directed, n: Number(i.n_sources || 1), width: 1.2 + 1.6 * Math.log2(1 + Number(i.n_sources || 1)) },
      })),
    ];
  }

  function style() {
    const v = cssVar;
    const moduleColor = (m) => v("--m-" + m) || v("--muted");
    return [
      { selector: "node", style: {
        label: "data(label)", width: "data(size)", height: "data(size)", "background-color": v("--muted"),
        color: v("--text"), "font-size": 11, "text-valign": "bottom", "text-margin-y": 4,
        "text-outline-color": v("--bg"), "text-outline-width": 2, "border-width": 0,
      } },
      ...Object.keys(MODULES).filter(Boolean).map((m) => ({ selector: `node[module = "${m}"]`, style: { "background-color": moduleColor(m) } })),
      { selector: "node[?seed]", style: { "border-width": 2, "border-color": v("--text"), "font-weight": "bold", "font-size": 13 } },
      { selector: "edge", style: {
        width: "data(width)", "line-color": v("--muted"), "target-arrow-color": v("--muted"),
        "curve-style": "bezier", opacity: 0.85, "arrow-scale": 0.9,
      } },
      { selector: 'edge[directed = "true"]', style: { "target-arrow-shape": "triangle" } },
      { selector: 'edge[type = "activation"], edge[type = "expression_regulation_up"]', style: { "line-color": v("--keep"), "target-arrow-color": v("--keep") } },
      { selector: 'edge[type = "inhibition"], edge[type = "expression_regulation_down"]', style: { "line-color": v("--reject"), "target-arrow-color": v("--reject"), "target-arrow-shape": "tee" } },
      { selector: 'edge[type = "phosphorylation"], edge[type = "ubiquitination"]', style: { "line-color": v("--uncertain"), "target-arrow-color": v("--uncertain") } },
      { selector: 'edge[type = "Ca2+_flux"]', style: { "line-color": v("--m-ca_stores"), "target-arrow-color": v("--m-ca_stores") } },
      { selector: 'edge[type = "coexpression"]', style: { "line-style": "dashed" } },
      { selector: 'edge[type = "unknown_regulation"]', style: { "line-style": "dotted" } },
      { selector: ".faded, .dim", style: { opacity: 0.12, "text-opacity": 0.2 } },
      { selector: "node.hl", style: { "border-width": 3, "border-color": v("--accent") } },
      { selector: "edge.hl", style: { opacity: 1, "z-index": 10 } },
      { selector: ".path", style: { "border-width": 4, "border-color": v("--accent"), "line-color": v("--accent"), "target-arrow-color": v("--accent"), opacity: 1, "z-index": 20 } },
      { selector: ":selected", style: { "overlay-color": v("--accent"), "overlay-opacity": 0.15, "overlay-padding": 6 } },
    ];
  }

  function draw() {
    const items = visibleInteractions();
    $("stats").textContent = `${new Set(items.flatMap((i) => [i.source, i.target])).size} actors · ${items.length} interactions` +
      (items.length < kept.length ? ` (of ${kept.length})` : "");
    $("empty").hidden = items.length > 0;
    $("empty").textContent = kept.length
      ? "No interaction matches the current filters."
      : "No kept interactions yet. Review interactions, export kept_interactions.csv, then run `python3 pipeline/cli.py graph` or drop the CSV here.";
    if (cy) cy.destroy();
    cy = cytoscape({
      container: $("cy"), elements: elements(items), style: style(),
      layout: { name: window.cytoscapeFcose ? "fcose" : "cose", quality: "proof", animate: false, randomize: true,
        nodeRepulsion: () => 9000, idealEdgeLength: () => 90, nodeSeparation: 90, packComponents: true },
      minZoom: 0.1, maxZoom: 3,
    });
    wireGraph();
    refreshSymbols(items);
    if (pathHighlight) findPath();
  }

  function wireGraph() {
    cy.on("mouseover", "node", (e) => {
      const hood = e.target.closedNeighborhood();
      cy.elements().not(hood).addClass("dim");
      hood.addClass("hl");
    });
    cy.on("mouseout", "node", () => cy.elements().removeClass("dim hl"));
    cy.on("tap", "node", (e) => showNode(e.target.id()));
    cy.on("tap", "edge", (e) => showEdge(e.target.id()));
    cy.on("tap", (e) => { if (e.target === cy) setInfoVisible(false); });
  }

  function refreshSymbols(items) {
    const ids = [...new Set(items.flatMap((i) => [i.source, i.target]))].sort();
    $("symbols").replaceChildren(...ids.map((id) => el("option", { value: label(id) })));
  }

  function idFor(text) {
    const t = (text || "").trim().toUpperCase();
    return cy.nodes().filter((n) => n.id().toUpperCase() === t || String(n.data("label")).toUpperCase() === t).first();
  }

  // ---------- info panels ----------

  function setInfoVisible(visible) {
    if ($("info").hidden === !visible) return;
    $("info").hidden = !visible;
    if (cy) cy.resize();
  }

  function openInfo(...content) {
    $("info-body").replaceChildren(...content);
    setInfoVisible(true);
  }

  function showNode(id) {
    const n = nodesById[id] || { id, symbol: id };
    const items = visibleInteractions().filter((i) => i.source === id || i.target === id)
      .sort((a, b) => Number(b.n_sources) - Number(a.n_sources));
    const acc = (n.uniprot || "").split(";")[0];
    openInfo(
      el("h2", {}, n.symbol || id),
      n.name ? el("p", { class: "muted" }, n.name) : null,
      el("div", { class: "chips" },
        el("span", { class: "module m-" + n.module }, MODULES[n.module || ""] || n.module),
        n.is_seed === "true" ? el("span", { class: "chip" }, "seed") : null,
        n.type === "metabolite" ? el("span", { class: "chip" }, "metabolite") : null,
        n.calcium_related === "false" ? el("span", { class: "chip beyond" }, "not calcium-related") : null),
      n.synonyms ? el("p", { class: "small muted" }, "Synonyms: " + n.synonyms) : null,
      curatedAnnotations(n),
      n.function_summary ? el("p", { class: "summary" }, n.function_summary) : null,
      el("p", { class: "links" },
        acc ? link("https://www.uniprot.org/uniprotkb/" + acc + "/entry", "UniProt " + acc) : null,
        n.type === "gene" ? link("https://www.ncbi.nlm.nih.gov/gene/?term=" + encodeURIComponent(id + "[sym] AND human[orgn]"), "NCBI Gene") : null,
        n.type === "metabolite" ? link("https://www.ebi.ac.uk/chebi/searchId.do?chebiId=" + id, "ChEBI " + id) : null),
      el("h3", {}, `${items.length} interaction(s)`),
      el("ul", { class: "list" }, items.map((i) => el("li", {},
        el("button", { type: "button", class: "linkish", onclick: () => { showEdge(i.interaction_id); cy.getElementById(i.interaction_id).select(); } },
          `${label(i.source)} ${arrow(i)} ${label(i.target)}`),
        el("span", { class: "muted small" }, ` ${i.type.replace(/_/g, " ")} · ${i.n_sources} source(s)`)))));
  }

  // What the researcher's own gene catalogue says about this actor (issue #17). Shown next
  // to the automatic UniProt summary, never instead of it.
  const CURATED_FIELDS = [
    ["localization", "Localization"], ["protein_type", "Protein type"], ["domains", "Domains"],
    ["ca_functionality", "Ca²⁺ functionality"], ["regulation", "Regulates"],
    ["functional_assignment", "Functional assignment"],
  ];

  function curatedAnnotations(n) {
    const rows = CURATED_FIELDS.filter(([key]) => n[key]);
    if (!rows.length && !n.genecards) return null;
    return el("div", { class: "curated-block" },
      el("div", { class: "note-label" }, "Curator's gene catalogue"),
      el("dl", { class: "curated" }, rows.flatMap(([key, label]) => [
        el("dt", {}, label), el("dd", {}, n[key])])),
      n.genecards ? el("p", { class: "links" },
        link("https://www.genecards.org/cgi-bin/carddisp.pl?gene=" + encodeURIComponent(n.symbol || n.id),
             "GeneCards " + n.genecards)) : null);
  }

  function arrow(i) {
    if (i.directed !== "true") return "—";
    return i.type === "inhibition" || i.type === "expression_regulation_down" ? "⊣" : "→";
  }

  function showEdge(id) {
    const i = kept.find((x) => x.interaction_id === id);
    if (!i) return;
    const evs = evidenceByInteraction[id] || [];
    openInfo(
      el("h2", {}, `${label(i.source)} ${arrow(i)} ${label(i.target)}`),
      el("p", { class: "edge-type t-" + i.type }, i.type.replace(/_/g, " ")),
      i.mechanism ? el("p", { class: "muted" }, i.mechanism) : null,
      el("div", { class: "chips" },
        el("span", { class: "chip" }, `${i.n_sources} source(s): ${i.n_pubs || 0} pub · ${i.n_db || 0} db`),
        i.beyond_calcium === "true"
          ? el("span", { class: "chip beyond" }, "not calcium-related (kept on purpose)")
          : i.calcium_evidence ? el("span", { class: "chip" }, "Ca²⁺: " + CamapCore.calciumLabel(i.calcium_evidence)) : null,
        i.has_human_evidence === "false" && i.has_animal_evidence === "true"
          ? el("span", { class: "chip warn" }, "non-human only") : null,
        i.has_human_evidence === "false" && i.has_animal_evidence === "false"
          ? el("span", { class: "chip" }, "species not recorded") : null),
      el("h3", {}, "Why it matters"), el("p", {}, i.justification || "—"),
      i.comment ? el("div", {}, el("h3", {}, "Review comment"), el("p", {}, i.comment + (i.reviewer ? " — " + i.reviewer : ""))) : null,
      el("h3", {}, "Evidence"),
      evs.length ? el("ul", { class: "evidence" }, evs.map((ev) => el("li", {},
        el("div", { class: "meta" },
          el("span", { class: "badge " + ev.source_kind }, ev.source_kind),
          link(refHref(ev.ref), [ev.first_author, ev.year, ev.ref].filter(Boolean).join(" · ")),
          ev.cited_pmid ? link(refHref("PMID:" + ev.cited_pmid), "cites PMID:" + ev.cited_pmid) : null,
          el("span", { class: "small muted" }, SPECIES[ev.species_context] || ev.species_context)),
        ev.source_kind === "curated"
          ? el("div", { class: "curator-note" },
              el("div", { class: "note-label" }, "Curator summary"), el("p", {}, ev.curator_note || "—"))
          : ev.sentence ? el("blockquote", { class: ev.sentence_verified === "true" ? "" : "unverified" }, ev.sentence,
          ev.sentence_verified === "true" ? null : el("div", { class: "warn small" }, "⚠️ not found verbatim"))
          : el("p", { class: "muted small" }, "Database-only, no sentence found"))))
        : el("p", { class: "muted small" }, "Evidence details not available for this export."));
  }

  // ---------- path ----------

  function findPath() {
    if (!cy) return;
    cy.elements().removeClass("path faded");
    const a = idFor($("path-from").value), b = idFor($("path-to").value);
    if (!a.length || !b.length) {
      $("path-result").textContent = "Both actors must be in the displayed graph.";
      return;
    }
    const p = CamapCore.shortestPath(visibleInteractions(), a.id(), b.id());
    pathHighlight = true;
    if (!p) {
      $("path-result").textContent = `No path between ${a.data("label")} and ${b.data("label")}.`;
      return;
    }
    const col = cy.collection([...p.nodes, ...p.edges].map((x) => cy.getElementById(x)));
    cy.elements().not(col).addClass("faded");
    col.addClass("path");
    cy.animate({ fit: { eles: col, padding: 80 } }, { duration: 300 });
    $("path-result").textContent = `${p.edges.length} step(s): ` + p.nodes.map(label).join(" → ");
  }

  // ---------- filters UI ----------

  function checks(container, values, selected, labelOf, onChange) {
    container.replaceChildren(...values.map((v) => {
      const input = el("input", { type: "checkbox", value: v });
      input.checked = selected == null || selected.includes(v);
      input.addEventListener("change", () => {
        const all = [...container.querySelectorAll("input")];
        const on = all.filter((x) => x.checked).map((x) => x.value);
        onChange(on.length === all.length ? null : on);
      });
      return el("label", { class: "check" }, input, " ", labelOf(v));
    }));
  }

  function setFilters(patch) {
    filters = { ...filters, ...patch };
    store(KEYS.filters, filters);
    draw();
  }

  const KINDS = { literature: ["n_pubs", "literature"], database: ["n_db", "databases"], curated: ["n_curated", "curator's sheets"] };

  function buildFilterUI() {
    const kinds = Object.keys(KINDS).filter((k) => kept.some((i) => Number(i[KINDS[k][0]] || 0) > 0));
    checks($("f-kinds"), kinds, filters.sourceKinds, (k) => KINDS[k][1], (on) => setFilters({ sourceKinds: on }));
    const types = LINK_TYPES.filter((t) => kept.some((i) => i.type === t));
    checks($("f-types"), types, filters.types, (t) => t.replace(/_/g, " "), (on) => setFilters({ types: on }));
    const modules = Object.keys(MODULES).filter((m) => kept.some((i) => moduleOf(i.source) === m || moduleOf(i.target) === m));
    checks($("f-modules"), modules, filters.modules, (m) => el("span", {}, el("i", { class: "dot", style: `background:var(--m-${m}, var(--muted))` }), MODULES[m]), (on) => setFilters({ modules: on }));
    const max = Math.max(1, ...kept.map((i) => Number(i.n_sources || 1)));
    $("f-min").max = String(Math.min(max, 20));
    $("f-min").value = String(filters.minSources || 1);
    $("f-min-out").textContent = $("f-min").value;
    $("f-mouse").checked = !!filters.excludeMouseOnly;
  }

  function buildLegend() {
    const edge = (cls, text) => el("div", { class: "lg" }, el("i", { class: "line " + cls }), text);
    $("legend").replaceChildren(
      ...Object.keys(MODULES).filter(Boolean).map((m) => el("div", { class: "lg" }, el("i", { class: "dot", style: `background:var(--m-${m})` }), MODULES[m])),
      el("div", { class: "lg" }, el("i", { class: "dot ring" }), "seed actor (size = degree)"),
      edge("act", "activation / up-regulation →"),
      edge("inh", "inhibition / down-regulation ⊣"),
      edge("mod", "phosphorylation / ubiquitination"),
      edge("ca", "Ca²⁺ flux"),
      edge("bind", "binding (thickness = number of sources)"),
      edge("dash", "co-expression"));
  }

  // ---------- CSV loading ----------

  async function loadCsv(file) {
    try {
      const rows = CamapCore.parseCsv(await file.text());
      if (!rows.length || !("interaction_id" in rows[0]) || !("source" in rows[0])) throw new Error("not a kept_interactions.csv");
      kept = rows.filter((r) => !("decision" in r) || r.decision === "keep");
      pathHighlight = null;
      $("path-result").textContent = `Loaded ${file.name}`;
      buildFilterUI();
      draw();
    } catch (e) {
      $("path-result").textContent = "Could not load CSV: " + e.message;
    }
  }

  // ---------- wiring ----------

  $("f-mouse").addEventListener("change", (e) => setFilters({ excludeMouseOnly: e.target.checked }));
  $("f-min").addEventListener("input", (e) => { $("f-min-out").textContent = e.target.value; });
  $("f-min").addEventListener("change", (e) => setFilters({ minSources: Number(e.target.value) }));
  $("search").addEventListener("change", () => {
    const n = idFor($("search").value);
    if (!n.length) return;
    cy.elements().unselect();
    n.select();
    cy.animate({ center: { eles: n }, zoom: 1.6 }, { duration: 300 });
    showNode(n.id());
  });
  $("path-go").addEventListener("click", findPath);
  $("path-clear").addEventListener("click", () => {
    pathHighlight = null;
    cy.elements().removeClass("path faded");
    $("path-result").textContent = "";
  });
  $("info-close").addEventListener("click", () => setInfoVisible(false));
  $("toggle-side").addEventListener("click", () => $("side").classList.toggle("open"));

  $("export-png").addEventListener("click", () =>
    download("calcium-map.png", cy.png({ full: true, scale: 2, bg: cssVar("--bg"), output: "blob" })));
  $("export-svg").addEventListener("click", () => {
    if (!cy.svg) return;
    download("calcium-map.svg", new Blob([cy.svg({ full: true, bg: cssVar("--bg") })], { type: "image/svg+xml" }));
  });

  $("load-csv").addEventListener("click", () => $("csv-file").click());
  $("csv-file").addEventListener("change", (e) => { if (e.target.files[0]) loadCsv(e.target.files[0]); e.target.value = ""; });
  let dragDepth = 0;
  window.addEventListener("dragenter", (e) => { e.preventDefault(); dragDepth++; $("drop").hidden = false; });
  window.addEventListener("dragleave", () => { if (--dragDepth <= 0) { dragDepth = 0; $("drop").hidden = true; } });
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("drop", (e) => {
    e.preventDefault();
    dragDepth = 0;
    $("drop").hidden = true;
    const f = e.dataTransfer.files[0];
    if (f) loadCsv(f);
  });

  CamapUI.applyTheme(load(KEYS.theme, null));
  $("theme").addEventListener("click", () => {
    CamapUI.toggleTheme(KEYS.theme);
    cy.style(style());
  });

  buildFilterUI();
  buildLegend();
  draw();
})();
