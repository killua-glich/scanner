# Codebase scan prompt

You are pointed at a repository. Build a compact JSON map of how it works —
where AI is used (if anywhere) and the business logic around it. Everything
stays on this machine; nothing gets uploaded. Your only output is data: the
`scan.json` described below. A separate local viewer (`viewer.html`) draws
it, so write no HTML or CSS yourself.

## Steps
1. Explore the repo and assemble the JSON. Save it as `scan.json` in the
   target repo's root.
2. If `validate.py` is available (next to this prompt or in the repo root),
   run `python3 validate.py scan.json` and repair anything it flags.
3. Tell the user where `scan.json` landed and how to look at it: run
   `serve.py`, or open `viewer.html` in a browser and drop the file in.

## What to look for
- AI call sites, in whatever shape the stack uses:
  - JS/TS: the Vercel AI SDK surface (`generateText`, `streamText`,
    `generateObject`, `streamObject`, `@ai-sdk/*` providers, `tool({...})`
    definitions), LangChain, raw OpenAI/Anthropic/Google SDK clients.
  - Python: `openai`, `anthropic`, `litellm`, LangChain, agent frameworks.
  - Native apps (Swift/Kotlin/etc.): `URLSession`/OkHttp requests to LLM API
    endpoints, API keys in config, prompt string constants, and on-device
    inference (CoreML, MLX, Foundation Models, llama.cpp bindings).
- Which models are called, and who provides them.
- Tools/functions exposed to models (search APIs, scrapers, DB lookups,
  internal functions) and third-party services the product talks to.
- The non-AI core of the product: the internal services and pipelines it is
  actually made of — billing, ingestion, sync, background workers, domain
  services. Represent each as a `service` node, and put the memorable
  one-liner on its edges (e.g. "locks account after 3 fails").
- The flows that tie it together: entry points (routes, webhooks, screens,
  CLIs), scheduled/background jobs, agents, the models and tools they use,
  and the stores/services they read and write.
- If the repo contains no AI at all, that is a perfectly good scan: map the
  business logic only, leave `topModels`/`topTools` as `[]` and the stats at
  0. Never invent AI nodes to make the map look richer.
- Granularity: one `service` node per domain concept (a controller and the
  service class behind it are one node), never one node per file or class.
- Deployment-level dependencies from compose files or infra config (reverse
  proxies, tunnels, CDNs) count as `external` nodes and integrations even if
  application code never calls them directly — they are part of how the
  system runs.

## Output contract — scan.json must have exactly this shape
{
  "version": 1,
  "project": {
    "name": "string (<=48)",
    "slug": "lowercase-dashed (<=48)",
    "tagline": "one line (<=80, optional)",
    "iconDomain": "favicon domain of the product, e.g. example.com (optional)",
    "date": "YYYY-MM-DD"
  },
  "stats": { "agents": 0, "models": 0, "tools": 0, "integrations": 0 },
  "topModels":       [ { "id": "sonnet", "label": "Claude Sonnet", "domain": "claude.ai" } ],
  "topTools":        [ { "id": "serp", "label": "SERP search", "domain": "serpapi.com" } ],
  "topIntegrations": [ { "id": "twilio", "label": "Twilio", "domain": "twilio.com" } ],
  "graph": {
    "nodes": [
      { "id": "inbox", "label": "Inbox webhook", "kind": "entry", "sub": "/hooks/inbound" },
      { "id": "sorter", "label": "Mail sorter agent", "kind": "agent", "sub": "tool loop",
        "sourceRef": "app/agents/sorter.py:31",
        "detail": "Files each inbound mail into a folder and drafts a reply when confident." },
      { "id": "sonnet", "label": "Claude Sonnet", "kind": "model", "domain": "claude.ai" },
      { "id": "folders", "label": "Folder service", "kind": "service",
        "sourceRef": "app/services/folders.py" },
      { "id": "db", "label": "SQLite", "kind": "store", "domain": "sqlite.org" }
    ],
    "edges": [
      { "from": "inbox", "to": "sorter", "kind": "triggers" },
      { "from": "sorter", "to": "sonnet", "kind": "calls" },
      { "from": "folders", "to": "db", "kind": "writes", "label": "locks after 3 fails" }
    ]
  }
}

## Constraints (the validator enforces most of these)
- Size caps: `topModels` <= 3, `topTools` <= 10, `topIntegrations` <= 10,
  `graph.nodes` <= 60, `graph.edges` <= 120. Everything goes on ONE map —
  AI flows and plain business logic together. A substantial codebase usually
  lands at 20-40 nodes; a small MVP may honestly be 8-15. Never pad.
- Every node must justify itself. Prefer fewer, denser nodes over sprawl.
- Agents: when there are up to ~10 distinct agents, each gets its own node.
  Collapse them into one node only when they are many and interchangeable —
  and say so in `sub` (e.g. "9 identical fetchers"). If one agent hands off
  to another, connect them with an agent-to-agent edge.
- `group` (optional, <=24 chars): nodes sharing a group name are drawn as one
  labeled stack. Group by product area as a teammate would name it
  ("Checkout", "Import pipeline"), never by directory structure. Two or
  three groups of 3-6 nodes is the sweet spot; leave hubs ungrouped.
- Length caps: node `label` <= 28, `sub` <= 40, edge `label` <= 24.
- Node `kind` must be one of: `entry` (route/page/webhook/CLI), `cron`
  (scheduled or queued job), `agent`, `model`, `tool`, `service` (internal
  domain module the project owns), `store` (DB/cache/index), `external`
  (third-party API or infrastructure).
- Edge `kind` (optional but preferred): `calls`, `reads`, `writes`, or
  `triggers`. The viewer keeps it subtle and reveals it on trace/hover. Use
  an edge `label` only when a concrete phrase carries real information
  ("retries 3x then pages") — labels are always visible, so don't waste them
  on generic verbs.
- `domain` is a bare favicon domain (no scheme): set it on nodes owned by a
  recognizable product or company; leave it off internal nodes. For models,
  use the product's own domain (e.g. `claude.ai`, `gemini.google.com`).
- `detail` (optional, <=200): one sentence shown when the node is clicked.
  `sourceRef` (optional, <=120): repo-relative path with optional `:line`,
  so a teammate can jump straight to the code — add it to internal nodes.
- Edge `from`/`to` must name existing node ids; ids must be unique.
- `project.date` is today's date.
