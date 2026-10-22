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
    if (!missing.length) return missing;
    var show = function () { announce(win.document, message(missing)); };
    if (win.document.body) show();
    else win.document.addEventListener("DOMContentLoaded", show);
    return missing;
  }

  if (typeof document !== "undefined") guard(typeof window !== "undefined" ? window : self);

  return { missingFeatures: missingFeatures, message: message, announce: announce, guard: guard, FLOOR: FLOOR };
});
