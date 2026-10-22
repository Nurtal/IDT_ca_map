// Small DOM and storage helpers shared by the review app and the graph page (browser only).
window.CamapUI = (function () {
  "use strict";

  function el(tag, attrs = {}, ...children) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k === "class") e.className = v;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v);
    }
    for (const c of children.flat()) if (c != null && c !== false) e.append(c.nodeType ? c : String(c));
    return e;
  }

  function link(href, text) {
    return href ? el("a", { href, target: "_blank", rel: "noopener" }, text) : el("span", {}, text);
  }

  // localStorage may be unavailable (private mode, blocked site data): never let it break the page.
  function load(key, fallback) {
    try {
      const v = localStorage.getItem(key);
      return v == null ? fallback : JSON.parse(v);
    } catch (e) {
      return fallback;
    }
  }

  function store(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      /* per-viewer convenience only; exports are the durable path */
    }
  }

  // Blocked site data is survivable for a filter or a theme, but it means the decisions only
  // live in this tab: worth saying out loud rather than discovering it on a reload.
  function storageWorks() {
    try {
      localStorage.setItem("camap.probe", "1");
      localStorage.removeItem("camap.probe");
      return true;
    } catch (e) {
      return false;
    }
  }

  function download(name, data, type) {
    const blob = data instanceof Blob ? data : new Blob([data], { type });
    const a = el("a", { href: URL.createObjectURL(blob), download: name });
    document.body.append(a);
    a.click();
    a.remove();
  }

  function applyTheme(theme) {
    if (theme) document.documentElement.dataset.theme = theme;
  }

  function toggleTheme(key) {
    const t = (document.documentElement.dataset.theme || "dark") === "dark" ? "light" : "dark";
    applyTheme(t);
    store(key, t);
    return t;
  }

  return { el, link, load, store, storageWorks, download, applyTheme, toggleTheme };
})();
