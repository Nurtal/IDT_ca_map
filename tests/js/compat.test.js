// Browser capability guard seam: what the page decides is missing, with no DOM involved.
const test = require("node:test");
const assert = require("node:assert/strict");
const compat = require("../../shared/compat.js");

// a browser that can run the app: only the globals the guard looks at
const modern = () => ({
  Object: { fromEntries: () => ({}) },
  Array: { prototype: { flat: () => [] } },
  Element: { prototype: { replaceChildren: () => {}, closest: () => null } },
  PointerEvent: function () {},
});

test("a current Chromium browser is missing nothing", () => {
  assert.deepEqual(compat.missingFeatures(modern()), []);
});

test("an Edge too old to replace a card's children is named as such", () => {
  const win = modern();
  delete win.Element.prototype.replaceChildren;
  assert.deepEqual(compat.missingFeatures(win), ["Element.replaceChildren"]);
});

test("a browser with no modern DOM at all reports every missing feature, not just the first", () => {
  assert.equal(compat.missingFeatures({}).length, 5);
});

test("the message names the browsers the curator can use, and what is missing", () => {
  const msg = compat.message(["Object.fromEntries", "PointerEvent"]);
  assert.match(msg, /Edge/);
  assert.match(msg, /Object\.fromEntries, PointerEvent/);
});
