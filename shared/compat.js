// Browser capability guard for the review app and the graph page.
//
// Written in ES5 on purpose: it is the first script of the page, so it must still parse in a
// browser too old to parse the rest of the app. Without it, an Edge older than its Chromium
// floor shows a page with an empty stage and no explanation; with it, the curator reads what
// to open instead. The floor is Chromium 86 (Edge 86, October 2020), set by
// Element.replaceChildren, the newest API the review app leans on.
(function (root, factory) {
  var compat = factory();
  if (typeof module === "object" && module.exports) module.exports = compat;
  else root.CamapCompat = compat;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var FLOOR = "Edge or Chrome 86+, Firefox 78+, Safari 14+";

  function missingFeatures(win) {
    var proto = win.Element && win.Element.prototype;
    var checks = [
      ["Object.fromEntries", !!win.Object && typeof win.Object.fromEntries === "function"],
      ["Array.prototype.flat", !!win.Array && typeof win.Array.prototype.flat === "function"],
      ["Element.replaceChildren", !!proto && typeof proto.replaceChildren === "function"],
      ["Element.closest", !!proto && typeof proto.closest === "function"],
      ["PointerEvent", typeof win.PointerEvent === "function"],
    ];
    var missing = [];
    for (var i = 0; i < checks.length; i++) if (!checks[i][1]) missing.push(checks[i][0]);
    return missing;
  }

  function message(missing) {
    return "This browser is too old for the review app. Please open this page in "
      + FLOOR + ". Missing here: " + missing.join(", ") + ".";
  }

  // Every data file sets its own key on window.CAMAP, so an absent key means that <script>
  // never ran: the file is not next to the page. An empty array means the build found nothing,
  // which is the pipeline's business, not the copy's — the page says so elsewhere and the two
  // must not be confused, because "run the build first" is useless advice on a PC with no build.
  // A key is the window.CAMAP property, named after its file; where it is not (the graph page's
  // "kept" lives in data/graph_data.js), the caller passes [key, path] so the banner names the
  // file the curator has to go and find.
  function missingData(camap, keys) {
    var data = camap || {};
    var missing = [];
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i], path;
      if (typeof key === "string") path = "data/" + key + ".js";
      else { path = key[1]; key = key[0]; }
      if (!data[key]) missing.push(path);
    }
    return missing;
  }

  function dataMessage(missing) {
    return "Could not load " + missing.join(", ") + ". This page reads those files from the"
      + " folder above it, so it needs the whole project folder around it (data/, shared/,"
      + " vendor/): copy or extract the folder entirely, and open review/index.html from the"
      + " extracted copy — not from inside a ZIP, where Windows opens the page alone.";
  }

  // The notice declares what the page needs as "key" or "key:path", e.g.
  // data-requires="nodes, kept:data/graph_data.js".
  function requiredKeys(spec) {
    var keys = [];
    var parts = (spec || "").split(",");
    for (var i = 0; i < parts.length; i++) {
      var part = parts[i].replace(/^\s+|\s+$/g, "");
      if (!part) continue;
      var colon = part.indexOf(":");
      keys.push(colon < 0 ? part : [part.slice(0, colon), part.slice(colon + 1)]);
    }
    return keys;
  }

  // The notice is written into the page, visible, and this takes it away once the data is there.
  // It has to be that way round: when the copy lost the folder above it, this very file is one
  // of the missing ones, so no script can be the thing that speaks up.
  function resolveNotice(win) {
    var el = win.document.getElementById("assets-missing");
    if (!el) return null;
    var missing = missingData(win.CAMAP, requiredKeys(el.getAttribute("data-requires")));
    if (missing.length) el.textContent = dataMessage(missing);
    else if (el.parentNode) el.parentNode.removeChild(el);
    return missing;
  }

  function announce(doc, text) {
    var banner = doc.createElement("p");
    banner.setAttribute("role", "alert");
    banner.style.cssText = "margin:0;padding:14px 16px;background:#f85149;color:#fff;"
      + "font:16px/1.4 system-ui,sans-serif;position:relative;z-index:99";
    banner.appendChild(doc.createTextNode(text));
    doc.body.insertBefore(banner, doc.body.firstChild);
  }

  function guard(win) {
    var missing = missingFeatures(win);
    var show = function () {
      if (missing.length) announce(win.document, message(missing));
      // after the data scripts have run, so an absent key means an absent file
      resolveNotice(win);
    };
    if (win.document.readyState !== "loading") show();
    else win.document.addEventListener("DOMContentLoaded", show);
    return missing;
  }

  if (typeof document !== "undefined") guard(typeof window !== "undefined" ? window : self);

  return { missingFeatures: missingFeatures, message: message, missingData: missingData,
    dataMessage: dataMessage, requiredKeys: requiredKeys, resolveNotice: resolveNotice,
    announce: announce, guard: guard, FLOOR: FLOOR };
});
