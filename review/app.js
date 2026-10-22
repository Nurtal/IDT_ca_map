// Review app UI: thin layer over CamapCore.
(function () {
  "use strict";
  const KEYS = {
    reviews: "camap.reviews.v1", filters: "camap.filters.v1", reviewer: "camap.reviewer", theme: "camap.theme",
    hops: "camap.hops",
  };
  const { modules: MODULES, species: SPECIES } = CamapCore.LABELS;
  const { refHref, calciumLabel, stringLabel } = CamapCore;
  const { el, link, load, store, storageWorks, download } = CamapUI;

  // A data file that did not load leaves its key unset: the page is a copy that lost the
  // folder around it, which must not read as "the build produced nothing" (see render()).
  const absent = CamapCompat.missingData(window.CAMAP, ["nodes", "interactions", "evidence"]);

  const data = window.CAMAP || {};
  const interactions = data.interactions || [];
  const nodesById = Object.fromEntries((data.nodes || []).map((n) => [n.id, n]));
  const evidenceByInteraction = groupBy(data.evidence || [], "interaction_id");
  const $ = (id) => document.getElementById(id);

  const session = CamapCore.createSession({
    interactions, reviews: load(KEYS.reviews, {}), filters: load(KEYS.filters, {}),
    reviewer: load(KEYS.reviewer, ""),
  });
  let fileHandle = null;
  let hops = load(KEYS.hops, 1);
  let miniGraph = null;

  // ---------- storage ----------

  async function persist() {
    store(KEYS.reviews, session.reviews());
    if (!fileHandle) return;
    try {
      const w = await fileHandle.createWritable();
      await w.write(session.exportReviews());
      await w.close();
      $("file-status").textContent = "Auto-saved to " + fileHandle.name + " at " + new Date().toLocaleTimeString();
    } catch (e) {
      $("file-status").textContent = "Auto-save failed (" + e.message + "). Use Export.";
    }
  }

  // ---------- rendering helpers ----------

  function groupBy(rows, key) {
    const out = {};
    for (const r of rows) (out[r[key]] = out[r[key]] || []).push(r);
    return out;
  }

  function refLink(ev) {
    const label = [ev.first_author, ev.year].filter(Boolean).join(" ");
    const main = link(refHref(ev.ref || "") || (ev.doi ? "https://doi.org/" + ev.doi : null), (label ? label + " · " : "") + ev.ref);
    if (!ev.cited_pmid) return main;
    return el("span", {}, main, " · cites ", link(refHref("PMID:" + ev.cited_pmid), "PMID:" + ev.cited_pmid));
  }

  function sourceBadges(evs) {
    const kinds = {};
    for (const ev of evs) (kinds[ev.source_kind] = kinds[ev.source_kind] || new Set()).add(ev.ref);
    return el("div", { class: "badges" },
      Object.entries(kinds).map(([k, refs]) => el("span", { class: "badge " + k }, `${k} × ${refs.size}`)));
  }

  function endpoint(id) {
    const n = nodesById[id] || {};
    return el("div", { class: "endpoint" },
      el("div", { class: "symbol" }, n.symbol || id),
      n.name ? el("div", { class: "name" }, n.name) : null,
      n.module ? el("span", { class: "module m-" + n.module }, MODULES[n.module] || n.module) : null);
  }

  function sentence(ev) {
    // A curated row is the researcher's own summary of a paper, never a quote from it,
    // so it is labelled as such and carries no verbatim-verification marker (issue #16).
    if (ev.source_kind === "curated") {
      return el("div", { class: "curator-note" },
        el("div", { class: "note-label" }, "Curator summary" + (ev.supp_source ? " · " + ev.supp_source : "")),
        el("p", {}, ev.curator_note || "—"));
    }
    if (!ev.sentence) return el("p", { class: "muted" }, "Database-only, no sentence found");
    const note = CamapCore.verificationNote(ev.sentence_verified);
    return el("blockquote", { class: note && note.level === "warn" ? "unverified" : "verified" },
      ev.sentence,
      note ? el("div", { class: note.level }, note.text) : null);
  }

  const byId = Object.fromEntries(interactions.map((i) => [i.interaction_id, i]));

  function cardFlags(i) {
    const flags = [];
    const previous = session.reviews()[i.interaction_id];
    if (session.hasNewEvidence(i)) {
      flags.push(el("span", { class: "flag new" }, `🆕 New evidence since your review (was: ${previous.decision})`));
    }
    for (const id of (i.conflict_with || "").split(";").filter(Boolean)) {
      const other = byId[id];
      if (!other) continue;
      flags.push(el("button", {
        type: "button", class: "flag", title: "Open the conflicting interaction",
        onclick: () => { session.jumpTo(id); render(); },
      }, `⚠️ Conflicting evidence: ${other.source} ${other.type.replace(/_/g, " ")} ${other.target} →`));
    }
    return flags.length ? el("div", { class: "card-flags" }, flags) : null;
  }

  function renderCard(i) {
    const evs = evidenceByInteraction[i.interaction_id] || [];
    return el("article", { class: "card", id: "card" },
      cardFlags(i),
      el("section", { class: "edge" },
        endpoint(i.source),
        el("div", { class: "link " + i.type },
          el("span", { class: "link-type" }, i.type.replace(/_/g, " ")),
          el("span", { class: "arrow" }, i.directed === "true" ? (i.type === "inhibition" ? "⊣" : "⟶") : "⟷")),
        endpoint(i.target)),
      i.mechanism ? el("p", { class: "mechanism" }, i.mechanism) : null,
      el("div", { class: "tags" },
        el("span", { class: "tag" + (i.beyond_calcium === "true" ? " beyond-tag" : "") },
           "Calcium evidence: " + calciumLabel(i.calcium_evidence, i.beyond_calcium)),
        i.has_human_evidence === "false" && i.has_animal_evidence === "true"
          ? el("span", { class: "tag warn-tag" }, "Non-human evidence only") : null,
        i.has_human_evidence === "false" && i.has_animal_evidence === "false"
          ? el("span", { class: "tag" }, "Species not recorded") : null,
        stringLabel(i.string_score) ? el("span", { class: "tag" }, stringLabel(i.string_score)) : null,
        CamapCore.crossesAxis(i, (n) => (nodesById[n] || {}).module || "")
          ? el("span", { class: "tag bridge-tag" }, "Crosses the axis: STIM1 ↔ STING") : null),
      el("section", { class: "why" }, el("h3", {}, "Why it matters"), el("p", {}, i.justification || "—")),
      neighbourhoodSection(),
      el("section", { class: "sources" },
        el("h3", {}, `Supported by ${i.n_sources} source(s) · ${i.n_pubs} publication(s) · ${i.n_db} database(s)`
          + (Number(i.n_curated) ? ` · ${i.n_curated} curated` : "")),
        sourceBadges(evs),
        el("ul", {}, evs.map((ev) =>
          el("li", { class: "evidence" },
            el("div", { class: "meta" },
              el("span", { class: "badge " + ev.source_kind }, ev.source_kind), refLink(ev),
              el("span", { class: "species s-" + ev.species_context }, SPECIES[ev.species_context] || ev.species_context)),
            sentence(ev))))));
  }

  function neighbourhoodSection() {
    const choose = (h) => el("button", {
      type: "button", class: "hop" + (h === hops ? " active" : ""),
      onclick: () => { hops = h; store(KEYS.hops, h); render(); },
    }, h + " hop" + (h > 1 ? "s" : ""));
    return el("section", { class: "neighbourhood" },
      el("h3", {}, "Local neighbourhood ", choose(1), choose(2)),
      el("div", { class: "mini-graph", id: "mini-graph" }),
      el("div", { class: "legend" },
        el("span", {}, el("i", { style: "background:var(--accent)" }), "this interaction"),
        el("span", {}, el("i", { style: "background:var(--keep)" }), "kept"),
        el("span", {}, el("i", { style: "background:var(--reject)" }), "rejected"),
        el("span", {}, el("i", { style: "background:var(--uncertain)" }), "unsure"),
        el("span", {}, el("i", { style: "background:var(--muted)" }), "pending"),
        el("span", { id: "nb-note" })));
  }

  function drawNeighbourhood(card) {
    if (miniGraph) { miniGraph.destroy(); miniGraph = null; }
    const box = $("mini-graph");
    if (!box || typeof cytoscape !== "function") return;
    const nb = CamapCore.neighbourhood(interactions, card.interaction_id, { hops, reviews: session.reviews() });
    const css = getComputedStyle(document.documentElement);
    const v = (name) => css.getPropertyValue(name).trim();
    const statusColor = { pending: v("--muted"), keep: v("--keep"), reject: v("--reject"), uncertain: v("--uncertain") };
    $("nb-note").textContent = nb.truncated ? `· showing the ${nb.nodes.length} closest actors` : "";
    miniGraph = cytoscape({
      container: box,
      elements: [
        ...nb.nodes.map((n) => {
          const node = nodesById[n.id] || {};
          return { data: { id: n.id, label: node.symbol || n.id, distance: n.distance, color: v("--m-" + node.module) || v("--muted") } };
        }),
        ...nb.edges.map((e) => ({ data: { ...e, color: e.focal ? v("--accent") : statusColor[e.status] } })),
      ],
      layout: { name: "cose", animate: false, randomize: false, padding: 30, nodeRepulsion: () => 9000,
        idealEdgeLength: () => 70, nodeDimensionsIncludeLabels: true },
      maxZoom: 1.3,
      style: [
        { selector: "node", style: { label: "data(label)", "background-color": "data(color)", color: v("--text"),
          "font-size": 11, "text-valign": "bottom", "text-margin-y": 4, width: 16, height: 16 } },
        { selector: "node[distance = 0]", style: { width: 26, height: 26, "font-weight": "bold", "font-size": 13 } },
        { selector: "edge", style: { width: 2, "line-color": "data(color)", "target-arrow-color": "data(color)",
          "curve-style": "bezier", opacity: 0.8 } },
        { selector: 'edge[directed = "true"]', style: { "target-arrow-shape": "triangle" } },
        { selector: 'edge[type = "inhibition"]', style: { "target-arrow-shape": "tee" } },
        { selector: 'edge[status = "reject"]', style: { "line-style": "dashed", opacity: 0.5 } },
        { selector: "edge[?focal]", style: { width: 4, opacity: 1 } },
      ],
      userZoomingEnabled: true, boxSelectionEnabled: false, autoungrabify: false,
    });
  }

  function render() {
    const c = session.counts();
    $("progress").textContent =
      `${c.reviewed}/${c.total} reviewed · ${c.remaining} left · ✓ ${c.keep} · ✕ ${c.reject} · ? ${c.uncertain}`;
    document.querySelectorAll(".modes button").forEach((b) => b.classList.toggle("active", b.dataset.mode === session.mode()));
    const stage = $("stage");
    stage.replaceChildren();
    const card = session.current();
    if (card) {
      stage.append(renderCard(card));
      drawNeighbourhood(card);
    } else {
      const msg = absent.length ? "The data files next to this page did not load — see the banner above."
        : !interactions.length ? "No interactions loaded. Run the pipeline build first."
        : session.mode() === "uncertain" ? "No uncertain interactions." : "All interactions reviewed 🎉";
      stage.append(el("div", { class: "empty" }, msg));
    }
    ["btn-keep", "btn-reject", "btn-uncertain"].forEach((b) => ($(b).disabled = !card));
    $("comment").value = card ? ((session.reviews()[card.interaction_id] || {}).comment || "") : "";
  }

  // ---------- actions ----------

  let deciding = false; // blocks a second decision while the card animates out

  function decide(decision) {
    if (deciding || !session.current()) return;
    deciding = true;
    const card = $("card");
    const comment = $("comment").value.trim();
    const done = () => {
      session.decide(decision, comment);
      deciding = false;
      persist();
      render();
    };
    if (!card || matchMedia("(prefers-reduced-motion: reduce)").matches) return done();
    card.classList.add("leave-" + decision);
    setTimeout(done, 180);
  }

  function undo() {
    if (deciding) return;
    const id = session.undo();
    if (!id) return;
    const r = session.reviews()[id];
    if (r && r.decision === "uncertain") session.setMode("uncertain");
    if (!r) session.setMode("pending");
    persist();
    render();
  }

  function enableSwipe() {
    let start = null;
    $("stage").addEventListener("pointerdown", (e) => {
      if (e.target.closest("a, button, textarea, input, .neighbourhood")) return;
      const card = $("card");
      if (card) start = { x: e.clientX, card };
    });
    window.addEventListener("pointermove", (e) => {
      if (!start) return;
      const dx = e.clientX - start.x;
      start.card.style.transform = `translateX(${dx}px) rotate(${dx / 30}deg)`;
      start.card.dataset.hint = dx > 60 ? "keep" : dx < -60 ? "reject" : "";
    });
    window.addEventListener("pointerup", (e) => {
      if (!start) return;
      const dx = e.clientX - start.x;
      start.card.style.transform = "";
      start.card.dataset.hint = "";
      start = null;
      if (dx > 120) decide("keep");
      else if (dx < -120) decide("reject");
    });
  }

  // ---------- wiring ----------

  $("btn-keep").addEventListener("click", () => decide("keep"));
  $("btn-reject").addEventListener("click", () => decide("reject"));
  $("btn-uncertain").addEventListener("click", () => decide("uncertain"));
  $("btn-undo").addEventListener("click", undo);
  document.querySelectorAll(".modes button").forEach((b) =>
    b.addEventListener("click", () => { session.setMode(b.dataset.mode); render(); }));

  const filterMouse = $("filter-mouse");
  const filterKind = $("filter-kind");
  const saved = load(KEYS.filters, {});
  filterMouse.checked = !!saved.excludeMouseOnly;
  filterKind.value = (saved.sourceKinds || []).length === 1 ? saved.sourceKinds[0] : "";
  const applyFilters = () => {
    const filters = {
      excludeMouseOnly: filterMouse.checked,
      // one kind at a time here: the stack is reviewed source by source
      sourceKinds: filterKind.value ? [filterKind.value] : null,
    };
    session.setFilters(filters);
    store(KEYS.filters, filters);
    render();
  };
  filterMouse.addEventListener("change", applyFilters);
  filterKind.addEventListener("change", applyFilters);

  const reviewer = $("reviewer");
  reviewer.value = load(KEYS.reviewer, "");
  reviewer.addEventListener("change", () => {
    store(KEYS.reviewer, reviewer.value.trim());
    location.reload();
  });

  $("export-reviews").addEventListener("click", () =>
    download("reviews.json", session.exportReviews(), "application/json"));
  $("export-kept").addEventListener("click", () =>
    download("kept_interactions.csv", CamapCore.keptCsv(interactions, session.reviews()), "text/csv"));
  $("import-reviews").addEventListener("click", () => $("import-file").click());
  $("import-file").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      session.importReviews(await file.text());
      persist();
      render();
      $("file-status").textContent = "Imported " + file.name;
    } catch (err) {
      $("file-status").textContent = "Import failed: " + err.message;
    }
    e.target.value = "";
  });

  if ("showSaveFilePicker" in window) {
    const link = $("link-file");
    link.hidden = false;
    link.addEventListener("click", async () => {
      try {
        fileHandle = await window.showSaveFilePicker({
          suggestedName: "reviews.json", types: [{ description: "Reviews", accept: { "application/json": [".json"] } }],
        });
        persist();
      } catch (e) {
        // Cancelling the picker is an AbortError and means nothing. Anything else is the
        // browser refusing the File System Access API — which is what Edge and Chrome do
        // when the page was opened from a network share or a sandboxed profile — and the
        // curator must hear it, or the button looks broken and the reviews look saved.
        if (e.name !== "AbortError") {
          $("file-status").textContent = "This browser will not auto-save to a file (" + e.name
            + "). Use Export reviews.json instead; your reviews are kept in the browser meanwhile.";
        }
      }
    });
  }

  if (!storageWorks()) {
    // the same banner the capability guard uses: a warning about losing a day of review
    // cannot sit inside a collapsed menu
    CamapCompat.announce(document, "This browser is not letting the page store anything "
      + "(InPrivate window, or site data blocked for file:// pages): your decisions live in this "
      + "tab only — export reviews.json before you close it.");
  }

  CamapUI.applyTheme(load(KEYS.theme, null));
  $("theme").addEventListener("click", () => {
    CamapUI.toggleTheme(KEYS.theme);
    render();
  });

  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return; // leave browser shortcuts alone
    if (e.target instanceof Element && e.target.closest("input, textarea")) {
      if (e.key === "Escape") e.target.blur();
      return;
    }
    const action = { ArrowRight: () => decide("keep"), ArrowLeft: () => decide("reject"),
      ArrowDown: () => decide("uncertain"), Backspace: undo, c: () => $("comment").focus() }[e.key];
    if (action) { e.preventDefault(); action(); }
  });

  enableSwipe();
  render();
})();
