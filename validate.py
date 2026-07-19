#!/usr/bin/env python3
"""Validate a scan.json against the codebase-scan data contract.

Usage: python3 validate.py [path/to/scan.json]   (default: ./scan.json)
       python3 validate.py --selftest            (run built-in bad-fixture checks)
"""
import copy
import json
import re
import sys

NODE_KINDS = {"entry", "cron", "agent", "model", "tool", "service", "store", "external"}
EDGE_KINDS = {"calls", "reads", "writes", "triggers"}
MODES = {"standard", "full"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SNIPPET_MAX_CHARS = 600
SNIPPET_MAX_LINES = 12


def check_len(errors, loc, value, cap, field):
    if isinstance(value, str) and len(value) > cap:
        errors.append(f"{loc}.{field}: {len(value)} chars, max {cap}")


def validate(data):
    """Return a list of violation strings (empty = valid)."""
    errors = []

    if data.get("version") != 1:
        errors.append(f"$.version: expected 1, got {data.get('version')!r}")

    project = data.get("project")
    if not isinstance(project, dict):
        errors.append("$.project: missing or not an object")
        project = {}
    for field in ("name", "slug", "date"):
        if not project.get(field):
            errors.append(f"$.project.{field}: required")
    check_len(errors, "$.project", project.get("name", ""), 48, "name")
    check_len(errors, "$.project", project.get("slug", ""), 48, "slug")
    slug = project.get("slug")
    if slug and not SLUG_RE.match(slug):
        errors.append(f"$.project.slug: {slug!r} must be lowercase-dashed")
    check_len(errors, "$.project", project.get("tagline", ""), 80, "tagline")
    mode = project.get("mode")
    if mode is not None and mode not in MODES:
        errors.append(f"$.project.mode: {mode!r} not in {sorted(MODES)}")

    for key, cap in (("topModels", 3), ("topTools", 10), ("topIntegrations", 10)):
        items = data.get(key, [])
        if len(items) > cap:
            errors.append(f"$.{key}: {len(items)} items, max {cap}")

    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if len(nodes) > 60:
        errors.append(f"$.graph.nodes: {len(nodes)} items, max 60")
    if len(edges) > 120:
        errors.append(f"$.graph.edges: {len(edges)} items, max 120")

    seen_ids = set()
    for i, node in enumerate(nodes):
        loc = f"$.graph.nodes[{i}]"
        node_id = node.get("id")
        if not node_id:
            errors.append(f"{loc}.id: required")
        elif node_id in seen_ids:
            errors.append(f"{loc}.id: duplicate id {node_id!r}")
        else:
            seen_ids.add(node_id)

        kind = node.get("kind")
        if kind not in NODE_KINDS:
            errors.append(f"{loc}.kind: {kind!r} not in {sorted(NODE_KINDS)}")

        check_len(errors, loc, node.get("label", ""), 28, "label")
        check_len(errors, loc, node.get("sub", ""), 40, "sub")
        check_len(errors, loc, node.get("detail", ""), 200, "detail")
        check_len(errors, loc, node.get("sourceRef", ""), 120, "sourceRef")
        check_len(errors, loc, node.get("group", ""), 24, "group")

        snippet = node.get("snippet")
        if snippet is not None:
            check_len(errors, loc, snippet, SNIPPET_MAX_CHARS, "snippet")
            lines = snippet.count("\n") + 1
            if lines > SNIPPET_MAX_LINES:
                errors.append(f"{loc}.snippet: {lines} lines, max {SNIPPET_MAX_LINES}")

        domain = node.get("domain")
        if domain and "://" in domain:
            errors.append(f"{loc}.domain: {domain!r} must not include a scheme")

    for i, edge in enumerate(edges):
        loc = f"$.graph.edges[{i}]"
        frm, to = edge.get("from"), edge.get("to")
        if frm not in seen_ids:
            errors.append(f"{loc}.from: {frm!r} references unknown node id")
        if to not in seen_ids:
            errors.append(f"{loc}.to: {to!r} references unknown node id")

        kind = edge.get("kind")
        if kind is not None and kind not in EDGE_KINDS:
            errors.append(f"{loc}.kind: {kind!r} not in {sorted(EDGE_KINDS)}")

        check_len(errors, loc, edge.get("label", ""), 24, "label")

    return errors


def selftest():
    base_nodes = [
        {"id": "a", "label": "A", "kind": "entry"},
        {"id": "b", "label": "B", "kind": "agent"},
    ]
    base_edge = {"from": "a", "to": "b", "kind": "calls"}
    base = {
        "version": 1,
        "project": {"name": "T", "slug": "t", "date": "2026-07-19"},
        "graph": {"nodes": base_nodes, "edges": [base_edge]},
    }

    def with_graph(nodes, edges):
        d = copy.deepcopy(base)
        d["graph"]["nodes"] = nodes
        d["graph"]["edges"] = edges
        return d

    def with_mode(mode):
        d = copy.deepcopy(base)
        d["project"]["mode"] = mode
        return d

    cases = {
        "valid base case": (base, True),
        "bad edge ref": (
            with_graph(base_nodes, [{"from": "a", "to": "ghost", "kind": "calls"}]), False),
        "dup id": (
            with_graph(base_nodes + [{"id": "a", "label": "A2", "kind": "tool"}], [base_edge]), False),
        "bad kind": (
            with_graph([{"id": "a", "label": "A", "kind": "spaceship"}, base_nodes[1]], [base_edge]), False),
        "over-long label": (
            with_graph(
                [{"id": "a", "label": "A" * 40, "kind": "entry"}, base_nodes[1]], [base_edge]), False),
        "bad mode": (with_mode("advanced"), False),
        "over-long snippet": (
            with_graph(
                [{"id": "a", "label": "A", "kind": "entry", "snippet": "x" * 601}, base_nodes[1]],
                [base_edge]), False),
        "over-many-lines snippet": (
            with_graph(
                [{"id": "a", "label": "A", "kind": "entry", "snippet": "\n".join(["x"] * 13)},
                 base_nodes[1]],
                [base_edge]), False),
    }

    failed = False
    for name, (doc, should_pass) in cases.items():
        errors = validate(doc)
        ok = (len(errors) == 0) == should_pass
        status = "ok" if ok else "FAIL"
        print(f"[{status}] {name}: {'passed' if not errors else errors[0]}")
        if not ok:
            failed = True

    sys.exit(1 if failed else 0)


def main():
    if "--selftest" in sys.argv:
        selftest()
        return

    path = sys.argv[1] if len(sys.argv) > 1 else "scan.json"
    with open(path) as f:
        data = json.load(f)

    errors = validate(data)
    if errors:
        for e in errors:
            print(e)
        sys.exit(1)

    print(f"OK: {path} is a valid scan.json")


if __name__ == "__main__":
    main()
