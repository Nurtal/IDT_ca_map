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

test("every data script having run is reported as nothing missing", () => {
  const camap = { nodes: [], interactions: [], evidence: [] };
  assert.deepEqual(compat.missingData(camap, ["nodes", "interactions", "evidence"]), []);
});

test("a data file that never loaded is named by its path, an empty one is not", () => {
  // the key is absent when the <script> did not run at all: file missing from the copy.
  // an empty array means the build produced nothing, which is a different story.
  const camap = { interactions: [] };
  assert.deepEqual(compat.missingData(camap, ["nodes", "interactions", "evidence"]),
    ["data/nodes.js", "data/evidence.js"]);
});

test("a page opened with no data at all names all three files", () => {
  assert.deepEqual(compat.missingData(undefined, ["nodes", "interactions", "evidence"]),
    ["data/nodes.js", "data/interactions.js", "data/evidence.js"]);
});

test("a key whose file is not named after it is reported under the real file name", () => {
  assert.deepEqual(compat.missingData({}, [["kept", "data/graph_data.js"]]), ["data/graph_data.js"]);
});

test("the notice's data-requires attribute names the keys, and the odd file path", () => {
  assert.deepEqual(compat.requiredKeys("nodes,interactions,evidence"),
    ["nodes", "interactions", "evidence"]);
  assert.deepEqual(compat.requiredKeys("nodes, kept:data/graph_data.js"),
    ["nodes", ["kept", "data/graph_data.js"]]);
  assert.deepEqual(compat.requiredKeys(""), []);
  assert.deepEqual(compat.requiredKeys(null), []);
});

test("the data message tells the curator to copy the whole folder", () => {
  const msg = compat.dataMessage(["data/nodes.js"]);
  assert.match(msg, /data\/nodes\.js/);
  assert.match(msg, /whole project folder/i);
  assert.match(msg, /ZIP/);
});

test("the message names the browsers the curator can use, and what is missing", () => {
  const msg = compat.message(["Object.fromEntries", "PointerEvent"]);
  assert.match(msg, /Edge/);
  assert.match(msg, /Object\.fromEntries, PointerEvent/);
});
