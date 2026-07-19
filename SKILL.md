---
name: scanner
description: Trigger on "use the scanner for X", "scan project X", "/scanner X" — analyze a codebase into scan.json and open the local viewer.
---

# Scanner

Maps a codebase's AI flows and business logic into a local `scan.json`, then
opens the local HTML viewer to browse it. Nothing leaves the machine. All
tool files live in this skill's base directory (the directory containing
this SKILL.md) — referred to as `<skill-dir>` below.

## Steps

1. **Resolve the target repo.** Figure out the path from the user's wording
   (project name, relative path, or explicit path). If it's ambiguous or you
   can't find a matching directory, ask the user for the path before doing
   anything else.

2. **Investigate and write scan.json.** Follow `<skill-dir>/scan-prompt.md`
   to analyze the target repo, and write the result to `<target>/scan.json`
   (in the TARGET repo root, not the skill directory). If `<target>/scan.json`
   already exists, tell the user you're regenerating it before overwriting —
   after telling them, overwriting is fine, it's just derived data.

3. **Validate.** Run:
   `python3 <skill-dir>/validate.py <target>/scan.json`
   Fix any reported violations and re-run until it passes.

4. **Serve and open the viewer.** Run:
   `python3 <skill-dir>/serve.py <target>/scan.json`
   This starts (or reuses) a local static server and opens the viewer with
   the fresh scan loaded via `?src=`. On Windows the interpreter may be
   `python` or `py` instead of `python3`.

5. **Report.** Give the user the URL serve.py printed, plus a 3-sentence
   summary of the map: what the entry points/crons are, which agents and
   models are involved, and the shape of the business logic (services,
   stores, external integrations).
