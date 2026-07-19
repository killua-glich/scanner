# Backlog

Spec: PLAN.md

## M1: Contract
_Status: Complete_
_Goal: Data contract nailed down — scan prompt + sample data to develop the viewer against_

- [x] TICKET-01 — Write local scan-prompt.md: foglamp prompt with Publish/upload removed; agent writes scan.json to repo root; keep schema + rules verbatim for compatibility
- [x] TICKET-02 — Create sample scan.json: hand-written, ~25 nodes / ~35 edges, all 8 node kinds, all 4 edge kinds, 2 groups, edge labels — the viewer's test fixture
- [x] TICKET-03 — Add validate.py: checks caps, id uniqueness, edge refs, kind enums, label lengths; assert-based, runnable as `python3 validate.py scan.json`

## M2: Viewer MVP
_Status: Complete_
_Goal: viewer.html renders sample scan.json as a readable static map_

- [x] TICKET-04 — Viewer skeleton: single HTML file, CSS vars (light+dark), loads scan.json via fetch with drag-and-drop fallback for file://; header with project name/tagline/stats
- [x] TICKET-05 — Layered layout: longest-path layering, barycenter ordering, group stacking, x/y assignment; pure function graph→positions; assert self-check on sample data
- [x] TICKET-06 — Node cards: absolutely positioned divs, kind-based accent color + glyph, label/sub, favicon img with offline fallback
- [x] TICKET-07 — Edge rendering: SVG overlay, orthogonal paths with rounded Q corners, arrowheads, always-visible edge labels

## M3: Interactivity
_Status: Complete_
_Goal: Map explorable — pan, inspect, trace_

- [x] TICKET-08 — Pan/zoom: drag + wheel on wrapper transform, fit-to-view on load
- [x] TICKET-09 — Node detail panel: click → detail text, sourceRef, kind, connections; Esc/click-away closes
- [x] TICKET-10 — Hover highlight: dim unrelated nodes/edges, show edge kinds on connected edges
- [x] TICKET-11 — Flow trace: click entry/cron → animate downstream path (offset-path glow dot, dash draw-in)

## M4: Polish & dogfood
_Status: Complete_
_Goal: Proven on a real repo_

- [x] TICKET-12 — Run scan prompt on a real project (blinkergate), render result, fix whatever breaks — 4 prompt gaps found and fixed in scan-prompt.md
- [x] TICKET-13 — top-lists strip: topModels/topTools/topIntegrations chips under header
- [x] TICKET-14 — README.md: usage (run prompt, open viewer), schema summary, screenshot

## M5: Skill
_Status: Complete_
_Goal: "use the scanner for project xy" → scan, viewer opens with fresh JSON_

- [x] TICKET-15 — Viewer JSON loading for skill flow: accept `?src=` URL param and same-dir `scan.json` autoload, keep drag-and-drop as fallback
- [x] TICKET-16 — Write SKILL.md (~/.claude/skills/scanner/): trigger phrases ("use the scanner for X", "/scanner X"), steps = run scan prompt against target repo → validate.py → write scan.json → serve + open viewer
- [x] TICKET-17 — serve.sh: copy scan.json next to viewer, `python3 -m http.server` on free port, `open` browser at viewer URL; idempotent re-runs
- [x] TICKET-18 — End-to-end skill test: scan → validate → serve.sh → viewer verified on blinkergate scan.json (10 nodes, self-check green)

## M6: Post-publish improvements
_Status: Complete_
_Goal: Sharing-driven polish after the GitHub release_

- [x] TICKET-19 — Cross-platform serve.py replaces serve.sh; MIT license; independently rewritten scan prompt (history squashed for clean publish)
- [x] TICKET-20 — Obstacle-avoiding edge routing (grid Dijkstra, corridors + channels); self-check guard against edge-card crossings
- [x] TICKET-21 — Adjustable block spacing slider (0.8–2.5×, persisted, ?spacing= param); fixed latent float-drift router bug
- [x] TICKET-22 — Clickable edges with edge detail panel (kind badge, label, jump to endpoints)
- [x] TICKET-23 — Scan modes: standard vs full; full adds capped code snippets (≤600 chars/≤12 lines) rendered in detail panel; skill asks for mode when unspecified

## Ideas

- [ ] Draw-in animation on first load (staggered edges, foglamp-style)
- [ ] Rotating beam highlight on selected node (CSS @property conic-gradient)
- [ ] Export map as PNG/SVG
- [ ] Diff view: compare two scan.json versions (nodes added/removed)
- [x] Serve via tiny `python3 -m http.server` helper script to dodge file:// CORS (serve.sh)

---
_Last updated: 2026-07-19_
