#!/usr/bin/env node
// Static sanity check for the layout engine, run outside the browser.
// Extracts the pure `<script id="layout-lib">` block from viewer.html (no DOM
// access in that block, so it runs as-is under plain Node) and lays out
// sample/scan.json, asserting the same invariants as the in-browser
// runSelfCheck(): every node gets coordinates, no NaNs, no overlaps, every
// edge references a laid-out node, non-back-edges point layer-forward, and
// (since routeEdges() is DOM-free too) every routed edge path avoids every
// card it doesn't start/end at.
//
// Usage: node check.js

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const viewerSrc = fs.readFileSync(path.join(__dirname, 'viewer.html'), 'utf8');
const match = viewerSrc.match(/<script id="layout-lib">([\s\S]*?)<\/script>/);
if (!match) { console.error('FAIL: could not find <script id="layout-lib"> in viewer.html'); process.exit(1); }

const sandbox = { module: { exports: {} } };
vm.createContext(sandbox);
vm.runInContext(match[1], sandbox);
const { layout, routeEdges } = sandbox.module.exports;
if (typeof layout !== 'function') { console.error('FAIL: layout() was not exported'); process.exit(1); }
if (typeof routeEdges !== 'function') { console.error('FAIL: routeEdges() was not exported'); process.exit(1); }

const scan = JSON.parse(fs.readFileSync(path.join(__dirname, 'sample', 'scan.json'), 'utf8'));
const graph = scan.graph;
const result = layout(graph);

const fails = [];
const posById = {};
result.nodes.forEach(n => (posById[n.id] = n));

graph.nodes.forEach(n => {
  const p = posById[n.id];
  if (!p) fails.push(`node ${n.id}: missing coordinates`);
  else if ([p.x, p.y, p.w, p.h].some(v => Number.isNaN(v))) fails.push(`node ${n.id}: NaN in geometry`);
});

for (let i = 0; i < result.nodes.length; i++) {
  for (let j = i + 1; j < result.nodes.length; j++) {
    const a = result.nodes[i], b = result.nodes[j];
    const overlap = a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
    if (overlap) fails.push(`cards overlap: ${a.id} / ${b.id}`);
  }
}

const backSet = new Set(result.backEdges);
// ponytail: grouping forces every member to the group's min layer (by design, see
// scan-prompt.md group rule), which can make an edge into/out of a group point
// "upward" in y even though it isn't a real cycle back-edge. Only enforce forward
// layering on edges where neither endpoint belongs to a group.
const groupedIds = new Set(graph.nodes.filter(n => n.group).map(n => n.id));
graph.edges.forEach(e => {
  const a = posById[e.from], b = posById[e.to];
  if (!a || !b) { fails.push(`edge ${e.from}->${e.to}: dangling reference`); return; }
  const isBack = backSet.has(e.from + '->' + e.to);
  const grouped = groupedIds.has(e.from) || groupedIds.has(e.to);
  if (!isBack && !grouped && b.y < a.y) fails.push(`edge ${e.from}->${e.to}: forward edge points upward (y ${a.y} -> ${b.y})`);
});

// Routed-edge guard: no segment of any edge's path may cross a card other
// than the one it starts/ends at (2px tolerance for touching that card).
const nodeGroup = {};
graph.nodes.forEach(n => { if (n.group) nodeGroup[n.id] = n.group; });
const routes = routeEdges(graph.edges, posById, result.groups, nodeGroup);
const GUARD_TOL = 2;
function segHitsCard(x1, y1, x2, y2, r) {
  if (Math.abs(x1 - x2) < 0.01) {
    const x = x1, ylo = Math.min(y1, y2), yhi = Math.max(y1, y2);
    return x > r.x + GUARD_TOL && x < r.x + r.w - GUARD_TOL && yhi > r.y + GUARD_TOL && ylo < r.y + r.h - GUARD_TOL;
  }
  const y = y1, xlo = Math.min(x1, x2), xhi = Math.max(x1, x2);
  return y > r.y + GUARD_TOL && y < r.y + r.h - GUARD_TOL && xhi > r.x + GUARD_TOL && xlo < r.x + r.w - GUARD_TOL;
}
graph.edges.forEach((e, idx) => {
  const route = routes[idx];
  if (!route) return;
  const pts = route.points;
  for (let s = 0; s < pts.length - 1; s++) {
    result.nodes.forEach(c => {
      if (c.id === e.from || c.id === e.to) return;
      if (segHitsCard(pts[s].x, pts[s].y, pts[s + 1].x, pts[s + 1].y, c)) {
        fails.push(`edge ${e.from}->${e.to}: routed path crosses card ${c.id}`);
      }
    });
  }
});

if (fails.length) {
  console.error(`FAIL: ${fails.length} violation(s)`);
  fails.forEach(f => console.error('  - ' + f));
  process.exit(1);
}
console.log(`OK: ${result.nodes.length} nodes, ${graph.edges.length} edges laid out and routed, no overlaps, no dangling edges, no backward forward-edges, no edge path crosses a card.`);
