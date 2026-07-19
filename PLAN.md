# Local Codebase Scan — Plan

Self-hosted clone of foglamp.dev/scan. No upload, no server, no account.
Two artifacts: a scan prompt any AI agent runs against a repo, and a
single-file HTML viewer that renders the resulting JSON.

Reference: foglamp's original scan prompt (captured 2026-07-19, kept outside
the repo for licensing reasons — get a fresh copy from their site's "Copy scan
prompt" button if needed).

## Architecture

```
your repo ──(AI agent + scan prompt)──▶ scan.json ──▶ viewer.html (local, offline)
```

1. **scan-prompt.md** — foglamp's prompt with the Publish/upload section removed.
   Agent investigates repo, writes `scan.json` next to it. Schema unchanged
   (stay compatible: any foglamp-style scan.json renders in our viewer).
2. **scan.json** — the data contract. `project`, `stats`, `top*` lists,
   `graph.nodes` (kind: entry|cron|agent|model|tool|service|store|external),
   `graph.edges` (kind: calls|reads|writes|triggers). Caps: 60 nodes, 120 edges.
3. **viewer.html** — one self-contained file, zero dependencies, zero build.
   Open via `file://` or any static server. Loads scan.json (fetch, with
   drag-and-drop fallback for file:// CORS).

## Viewer design (from renderer research)

- **Nodes**: absolutely positioned HTML cards inside a wrapper div.
  Pan/zoom = `transform: translate() scale()` on the wrapper. No canvas.
- **Edges**: one SVG overlay; orthogonal paths with rounded `Q` corners,
  arrowhead paths, `pathLength=1` dash draw-in.
- **Layout**: deterministic layered DAG (Sugiyama-lite): longest-path layer
  assignment, barycenter ordering within layers, grouped nodes stacked
  vertically. ~100 lines. No physics, no d3.
- **Interactivity**: pan/zoom, click node → detail panel (detail, sourceRef),
  hover → highlight connected edges, flow trace = CSS `offset-path` glow dot.
- **Icons**: `https://www.google.com/s2/favicons?domain=X&sz=64` when online,
  kind-based fallback glyph offline.
- **Theme**: CSS variables, light + dark via `prefers-color-scheme`.

## Non-goals

- No server, no sharing URLs, no edit tokens (that's foglamp's SaaS half).
- No graph editing in the viewer — regenerate scan.json instead.
- No framework, no npm, no build step.

## Skill packaging

End state: a Claude Code skill (`~/.claude/skills/scanner/`). Saying
"use the scanner for project xy" triggers: agent investigates that repo with
the scan prompt → writes `scan.json` → starts a tiny static server (dodges
file:// CORS) → opens viewer.html with the fresh JSON loaded. No manual steps.

## Milestones

1. **M1 Contract** — local scan prompt + valid sample scan.json to develop against.
2. **M2 Viewer MVP** — static render: layout, cards, edges, readable map.
3. **M3 Interactivity** — pan/zoom, details, hover highlight, flow trace.
4. **M4 Polish & dogfood** — groups, theme, icons, run on a real repo.
5. **M5 Skill** — package as `/scanner` skill: scan any named project, auto-launch viewer.
