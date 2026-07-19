# scanner

A local, no-upload alternative to [foglamp.dev/scan](https://www.foglamp.dev/scan):
an AI agent maps how a codebase uses AI (and the business logic around it)
into a small JSON file, and a single-file HTML viewer renders it as a
pannable map. Nothing leaves the machine.

## Install as a Claude Code skill

```
git clone https://github.com/killua-glich/scanner.git ~/.claude/skills/scanner
```

Windows:

```
git clone https://github.com/killua-glich/scanner.git "%USERPROFILE%\.claude\skills\scanner"
```

That's the whole install. In a new Claude Code session, say:

> use the scanner for ~/projects/my-app

Claude analyzes the repo, writes `scan.json` into it, validates it, starts a
local static server, and opens the interactive map in your browser.

Requirements: macOS, Linux, or Windows; only Python 3 (stdlib) required.
Update later with `git -C ~/.claude/skills/scanner pull`.

## Quick start (without Claude Code)

1. Point an AI agent at `scan-prompt.md` to analyze a repo. It writes
   `scan.json` to that repo's root.
   ```
   python3 validate.py path/to/repo/scan.json
   ```
2. Serve and open the viewer:
   ```
   python3 serve.py path/to/repo/scan.json
   ```
   On Windows the interpreter may be `python` or `py` instead of `python3`.
   With no argument, `serve.py` just serves this directory and opens the
   viewer with its default `scan.json` / `sample/scan.json` fallback chain.
   Drag-and-drop a JSON file onto the viewer also works, including offline
   via `file://`.

## Schema summary

`scan.json`: `version`, `project` (name/slug/tagline/iconDomain/date),
`stats`, `topModels`/`topTools`/`topIntegrations`, `graph.nodes`, `graph.edges`.

| Field | On | Notes |
|---|---|---|
| `id`, `label`, `kind` | node | required; label <=28 chars |
| `sub`, `detail`, `sourceRef`, `group`, `domain` | node | all optional |
| `from`, `to` | edge | required, must reference node ids |
| `kind`, `label` | edge | both optional; label <=24 chars |

Node kinds: `entry`, `cron`, `agent`, `model`, `tool`, `service`, `store`, `external`.
Edge kinds: `calls`, `reads`, `writes`, `triggers`.

Caps: `topModels` <=3, `topTools`/`topIntegrations` <=10, `graph.nodes` <=60,
`graph.edges` <=120.

## Files

- `SKILL.md` — the Claude Code skill definition (this repo doubles as the skill folder).
- `scan-prompt.md` — the prompt an AI agent runs against a repo to produce `scan.json`.
- `viewer.html` — single-file viewer: layout, pan/zoom, detail panel, hover, flow trace.
- `serve.py` — cross-platform: starts a local static server and opens the viewer, idempotently.
- `validate.py` — checks a `scan.json` against the schema and caps.
- `check.js` — Node self-check for the viewer's layout engine.
- `sample/scan.json` — fixture used as the viewer's final fallback and for `check.js`.
- `PLAN.md` / `BACKLOG.md` — design notes and the milestone/ticket tracker.

## Credit

The scan idea, the JSON schema, and the visual style come from
[foglamp.dev/scan](https://www.foglamp.dev/scan) — this project reimplements
them as a fully local tool. The scan prompt shipped here (`scan-prompt.md`)
is an independently written local variant; the schema stays compatible with
foglamp's so either prompt's output renders in this viewer.
