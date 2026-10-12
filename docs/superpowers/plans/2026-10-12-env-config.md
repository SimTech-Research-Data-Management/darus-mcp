# Env-var configuration (DATAVERSE_URL, MCP_TOOLS) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let whoever spawns darus-mcp choose the Dataverse base URL and the set of exposed tools through environment variables, with unset meaning today's behaviour.

**Architecture:** Two edits to the entry point `main.py`, nothing else in code. `DATAVERSE_URL` replaces the hardcoded base URL and is normalised to end in `/`. `MCP_TOOLS` switches FastMCP into allowlist mode with `app.enable(names=..., only=True)`. Each gets one runnable check in `test_darus.py` and one row in a new README configuration table.

**Tech Stack:** Python 3.12, FastMCP 3.4.4, pyDataverse (vendored dependency, not modified), uv.

**Spec:** `~/code/darus/docs/superpowers/specs/2026-09-22-selfreview-design.md` §6 items 1 and 2, and `~/code/darus/docs/decisions/0004-gate-darus-mcp-at-the-mcp-layer.md`. Decisions made after the spec are listed under Global Constraints and override it where they differ.

## Global Constraints

- Branch: `dev`. Commit after each task. Do not push.
- Do not modify pyDataverse or anything under `.venv/` (ADR 0004). All code changes go in `main.py`.
- Every variable is optional. Unset means today's behaviour, so the desktop plugin keeps working. This overrides spec §6's "required, fails at start" for `DATAVERSE_URL`.
- Default base URL: `https://darus.uni-stuttgart.de`.
- `API_TOKEN` handling stays exactly as it is.
- Out of scope: `mask_error_details` (decided: not added), the destination gate / `DATAVERSE_ALLOWED_URLS` (separate change), dataset or collection scoping (the bridge proxy is the authority), startup validation of `MCP_TOOLS` names (a typo hides a tool, which is fail-closed; a clean check isn't possible because `fastmcp run` imports `main.py` inside a running event loop), anything in `~/code/darus`.
- Tests run with: `uv run python test_darus.py` (no pytest). The existing tests import `main` from DaRUS over the network; the new tests do too.

## Verified facts the tasks rely on

- pyDataverse builds every URL with `urljoin(base_url, "api/...")` (`pyDataverse/api/api.py:224`, `api/data_access.py:35`). `urljoin` drops the last path segment unless the base ends in `/`:
  - `http://host/dv/job1` → requests `/dv/api//info/version` (job id lost)
  - `http://host/dv/job1/` → requests `/dv/job1/api//info/version` (kept)
- `Dataverse(...)` makes requests in its constructor (`/info/version`, then `/metadatablocks`), so importing `main` contacts the configured URL at once.
- With `app.enable(names=<the 5 review tools>, only=True)`, `list_tools` returns exactly those 5 (out of 16), and `call_tool("Create_Dataset", {})` raises `ToolError` with message `Unknown tool: 'Create_Dataset'`.
- Tools called with `base_url=None` use the configured client from context, so the trailing slash on the default URL doesn't change any lookup.

---

### Task 1: `DATAVERSE_URL` with path-prefix normalisation

**Files:**
- Modify: `main.py:43-50` (the `darus = Dataverse(...)` block)
- Modify: `test_darus.py` (new test function and a call in `__main__`)
- Modify: `README.md` (new `### Configuration` subsection after `### Run locally`, before `## Security Notes`)

**Interfaces:**
- Consumes: nothing.
- Produces: env var `DATAVERSE_URL` (string, optional). `main.darus.base_url` always ends in `/`.

- [ ] **Step 1: Write the failing test**

Add to `test_darus.py`, after `test_run_without_token_fails_loud`:

```python
def test_dataverse_url_keeps_path_prefix():
    """DATAVERSE_URL may carry a path (the bridge's per-job proxy, e.g.
    http://127.0.0.1:9000/dv/<job_id>). pyDataverse joins with urljoin, which
    drops the last segment unless the base ends in '/', so every request must
    still start with the prefix."""
    import http.server  # noqa: PLC0415
    import threading  # noqa: PLC0415

    paths = []

    class Stub(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            paths.append(self.path)
            self.send_response(404)
            self.end_headers()

        def log_message(self, *args):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        env = {
            **os.environ,
            "DATAVERSE_URL": f"http://127.0.0.1:{srv.server_port}/dv/job1",
        }
        # Import fails on the stub's 404; only the requested paths matter.
        subprocess.run(
            [sys.executable, "-c", "import main"],
            cwd=HERE,
            env=env,
            capture_output=True,
            timeout=60,
        )
    finally:
        srv.shutdown()
    assert paths, "no request reached the stub; DATAVERSE_URL ignored?"
    assert all(p.startswith("/dv/job1/") for p in paths), f"prefix dropped: {paths}"
    print("[ok] DATAVERSE_URL path prefix kept on every request")
```

And in the `__main__` block, after `test_run_without_token_fails_loud()`:

```python
    test_dataverse_url_keeps_path_prefix()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run python test_darus.py`
Expected: `AssertionError: no request reached the stub; DATAVERSE_URL ignored?`. The URL is still hardcoded, so the import goes to DaRUS, not the stub.

- [ ] **Step 3: Implement**

In `main.py`, replace:

```python
# Initialize connection to the DaRUS Dataverse instance
# DaRUS is the institutional data repository of the University of Stuttgart
darus = Dataverse(
    base_url="https://darus.uni-stuttgart.de",
    api_token=api_token,
    verbose=0,
)
```

with:

```python
# Dataverse instance to talk to; defaults to DaRUS, the institutional data
# repository of the University of Stuttgart. The trailing "/" is required:
# pyDataverse joins paths with urljoin, which drops the last path segment of a
# base like http://host/dv/<job_id> unless it ends in "/".
darus = Dataverse(
    base_url=os.environ.get("DATAVERSE_URL", "https://darus.uni-stuttgart.de").rstrip("/")
    + "/",
    api_token=api_token,
    verbose=0,
)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run python test_darus.py`
Expected: every `[ok]` line including `[ok] DATAVERSE_URL path prefix kept on every request`, then `all tests passed`. `[ok] import clean, 16 tools served over MCP` confirms the default URL still works.

- [ ] **Step 5: Document**

In `README.md`, insert between the end of `### Run locally` and `## Security Notes`:

```markdown
### Configuration

All variables are optional except where noted; unset means the defaults below.

| Variable | Default | Purpose |
|---|---|---|
| `API_TOKEN` | — (required for `python main.py`) | Dataverse API token, sent as `X-Dataverse-key`. |
| `DATAVERSE_URL` | `https://darus.uni-stuttgart.de` | Dataverse instance to talk to. May include a path (e.g. a proxy at `http://127.0.0.1:9000/dv/<job_id>`); a trailing `/` is added automatically. |
```

- [ ] **Step 6: Commit**

```bash
git add main.py test_darus.py README.md
git commit -m "feat: base URL from DATAVERSE_URL, keeping any path prefix"
```

End the commit message body with the `Co-Authored-By` trailer from the session's attribution rule.

---

### Task 2: `MCP_TOOLS` allowlist

**Files:**
- Modify: `main.py`: insert after the `DataverseMCP(...).to_mcp(app)` call, before `if __name__ == "__main__":`
- Modify: `test_darus.py` (new test function and a call in `__main__`)
- Modify: `README.md` (one row added to the table from Task 1)

**Interfaces:**
- Consumes: `main.app` (the `FastMCP` instance, already exists).
- Produces: env var `MCP_TOOLS` (comma-separated exact tool names, optional).

- [ ] **Step 1: Write the failing test**

Add to `test_darus.py`, after `test_dataverse_url_keeps_path_prefix`:

```python
REVIEW_TOOLS = [
    "Get_Dataset_Metadata",
    "List_Files_in_Dataset",
    "Read_File_Content",
    "Read_Tabular_File",
    "Get_Tabular_File_Schema",
]


def test_mcp_tools_allowlist():
    """With MCP_TOOLS set, exactly those tools are served (16 -> 5) and a hidden
    tool fails as unknown rather than running. Runs in a subprocess because
    `main` is already imported above with every tool enabled."""
    script = """
import asyncio, json, main
from fastmcp import Client

async def go():
    async with Client(main.app) as c:
        names = sorted(t.name for t in await c.list_tools())
        try:
            await c.call_tool("Create_Dataset", {})
            hidden = "ran"
        except Exception as e:
            hidden = str(e)
    print(json.dumps({"names": names, "hidden": hidden}))

asyncio.run(go())
"""
    env = {**os.environ, "MCP_TOOLS": ", ".join(REVIEW_TOOLS)}
    env.pop("API_TOKEN", None)
    env.pop("DATAVERSE_URL", None)
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=HERE,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["names"] == sorted(REVIEW_TOOLS), f"served: {out['names']}"
    assert "Unknown tool" in out["hidden"], f"hidden tool not refused: {out['hidden']}"
    print(f"[ok] MCP_TOOLS allowlist: 16 -> {len(out['names'])}, hidden tool unknown")
```

`", ".join` with a space after the comma is deliberate: it checks that names are stripped.

And in the `__main__` block, after `test_dataverse_url_keeps_path_prefix()`:

```python
    test_mcp_tools_allowlist()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run python test_darus.py`
Expected: `AssertionError: served: [...]` listing all 16 tool names.

- [ ] **Step 3: Implement**

In `main.py`, insert after the `DataverseMCP(...).to_mcp(app)` call:

```python
# Optional tool allowlist, e.g. for a read-only review agent. Unset = all tools.
# Hidden tools are not listed, and calling one fails as "Unknown tool".
if tools := os.environ.get("MCP_TOOLS"):
    app.enable(names={name.strip() for name in tools.split(",")}, only=True)
```

Don't filter out empty names. `MCP_TOOLS=","` gives `{""}`, which matches no tool, so the server exposes nothing (fail-closed). An empty set would be falsy and could be read as "match all".

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run python test_darus.py`
Expected: `[ok] MCP_TOOLS allowlist: 16 -> 5, hidden tool unknown`, `[ok] import clean, 16 tools served over MCP` (unset still means all tools), then `all tests passed`.

- [ ] **Step 5: Document**

Add this row to the README configuration table from Task 1, after the `DATAVERSE_URL` row:

```markdown
| `MCP_TOOLS` | all tools | Comma-separated allowlist of tool names (see [Tools](#tools)). Other tools are hidden and fail as unknown. Names must match exactly; a misspelt name is silently not exposed. |
```

- [ ] **Step 6: Commit**

```bash
git add main.py test_darus.py README.md
git commit -m "feat: tool allowlist from MCP_TOOLS"
```

End the commit message body with the `Co-Authored-By` trailer from the session's attribution rule.

---

## Follow-ups (not in this plan)

- Bridge (`~/code/darus`): the proxy must allow `/info/version` and `/metadatablocks` and accept the double slash pyDataverse sends (`api//info/version`), or darus-mcp cannot start behind it.
- Destination gate (`DATAVERSE_ALLOWED_URLS`, spec §6 item 3): its own change, unless the container's egress is guaranteed to reach only the proxy.
- Upstream pyDataverse: the `urljoin` prefix-dropping is worth an issue. The normalisation in `main.py` stays harmless after any fix.
