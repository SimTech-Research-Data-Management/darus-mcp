"""Tests for the DaRUS MCP server and its Claude Desktop installer.

No pytest dependency on purpose: run it directly.

    uv run python test_darus.py

Covers (alongside `uv sync --locked` in CI):
  - the server imports without a token and serves its tools over MCP,
  - running the server without a token fails loud instead of starting,
  - the Claude Desktop installer builds the right entry, resolves the config
    path per OS, and merges into the config without clobbering other servers.
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent

READ_TOOLS = {
    "Dataverse_Metrics",
    "Get_Collection_Metadata",
    "Get_Dataset_Metadata",
    "Get_Tabular_File_Schema",
    "Knowledge_Graph_Summary",
    "List_Content_of_Collection",
    "List_Files_in_Dataset",
    "Query_Knowledge_Graph",
    "Read_File_Content",
    "Read_Tabular_File",
    "Search_DataCite",
    "Search_Dataverse",
}

def test_serves_tools_over_mcp():
    """Import must succeed with no API_TOKEN, and the server must actually serve
    its tools over the MCP protocol (not just hold them in a private registry).
    Uses fastmcp's in-process client — the same protocol Claude Desktop speaks."""
    os.environ.pop("API_TOKEN", None)
    from fastmcp import Client  # noqa: PLC0415

    import main  # noqa: PLC0415 - deferred so the pop above takes effect

    async def list_tools():
        async with Client(main.app) as client:
            return await client.list_tools()

    names = {t.name for t in asyncio.run(list_tools())}
    # Exactly the read tools: a new tool from pyDataverse (a write tool above all)
    # must fail here until a human has checked it.
    assert names == READ_TOOLS, (
        f"served tools changed: added {names - READ_TOOLS}, gone {READ_TOOLS - names}"
    )
    print(f"[ok] import clean, {len(names)} read-only tools served over MCP")










def test_run_without_token_fails_loud():
    """`python main.py` with no token must exit non-zero and name the token."""
    env = {k: v for k, v in os.environ.items() if k != "API_TOKEN"}
    proc = subprocess.run(
        [sys.executable, "main.py"],
        cwd=HERE,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode != 0, "server started without a token — guard is broken"
    assert "API_TOKEN" in proc.stderr, f"expected API_TOKEN error, got:\n{proc.stderr}"
    print("[ok] no-token run failed loud")


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


REVIEW_TOOLS = [
    "Get_Dataset_Metadata",
    "List_Files_in_Dataset",
    "Read_File_Content",
    "Read_Tabular_File",
    "Get_Tabular_File_Schema",
]


def test_mcp_tools_allowlist():
    """With MCP_TOOLS set, exactly those tools are served (12 -> 5) and a hidden
    tool fails as unknown rather than running. Runs in a subprocess because
    `main` is already imported above with every tool enabled."""
    script = """
import asyncio, json, main
from fastmcp import Client

async def go():
    async with Client(main.app) as c:
        names = sorted(t.name for t in await c.list_tools())
        try:
            await c.call_tool("Search_Dataverse", {"query": "x"})
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
    print(f"[ok] MCP_TOOLS allowlist: 12 -> {len(out['names'])}, hidden tool unknown")


def test_no_tool_takes_base_url():
    """No caller may choose the host: pyDataverse's per-call base_url is hidden on
    every tool, so all calls go to DATAVERSE_URL (spec §6 item 3)."""
    os.environ.pop("API_TOKEN", None)
    from fastmcp import Client  # noqa: PLC0415

    import main  # noqa: PLC0415

    async def schemas():
        async with Client(main.app) as client:
            return {t.name: t for t in await client.list_tools()}

    served = asyncio.run(schemas())
    tools = {n: t.inputSchema for n, t in served.items()}
    assert set(tools) == READ_TOOLS, f"hiding an argument must not drop tools: {sorted(tools)}"
    leaky = [n for n, s in tools.items() if "base_url" in s.get("properties", {})]
    assert not leaky, f"tools still take base_url: {leaky}"
    told = [n for n, t in served.items() if "base_url" in (t.description or "")]
    assert not told, f"tool descriptions still mention base_url: {told}"
    print("[ok] no tool takes base_url")


def test_review_tool_arguments():
    """Pin the review tools' argument names. Every base_url safeguard keys on that
    literal name and pyDataverse comes from a git branch, so a rename or a new host
    argument would silently reopen the channel."""
    os.environ.pop("API_TOKEN", None)
    from fastmcp import Client  # noqa: PLC0415

    import main  # noqa: PLC0415

    expected = {
        "Get_Dataset_Metadata": {"full", "identifier"},
        "List_Files_in_Dataset": {"filter_mime_types", "identifier", "only_tabular"},
        "Read_Tabular_File": {"identifier", "n_rows", "path", "read_kwargs", "summarize"},
        "Read_File_Content": {"identifier", "path"},
        "Get_Tabular_File_Schema": {"identifier", "path"},
    }

    async def schemas():
        async with Client(main.app) as client:
            return {t.name: t.inputSchema for t in await client.list_tools()}

    tools = asyncio.run(schemas())
    got = {n: set(tools[n].get("properties", {})) for n in expected}
    assert got == expected, (
        "review tool arguments changed: a human must check for new host/URL "
        f"arguments (base_url safeguards key on the literal name). got {got}"
    )
    print("[ok] review tool arguments pinned")


def test_base_url_cannot_redirect_a_call():
    """Passing base_url anyway reaches nothing: the request never goes to that host."""
    import http.server  # noqa: PLC0415
    import threading  # noqa: PLC0415

    os.environ.pop("API_TOKEN", None)
    from fastmcp import Client  # noqa: PLC0415

    import main  # noqa: PLC0415

    hits = []

    class Recorder(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            hits.append(self.path)
            self.send_response(404)
            self.end_headers()

        do_HEAD = do_GET  # noqa: N815

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Recorder)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    evil = f"http://127.0.0.1:{server.server_port}/?leak=draft-text"

    async def call():
        async with Client(main.app) as client:
            return await client.call_tool(
                "Get_Dataset_Metadata",
                {"identifier": "doi:10.18419/darus-0000", "full": False, "base_url": evil},
                raise_on_error=False,
            )

    try:
        asyncio.run(call())
    finally:
        server.shutdown()
    assert not hits, f"a tool call reached the injected host: {hits}"
    print("[ok] base_url cannot redirect a call")




def test_mcpb_manifest_matches_project():
    """The .mcpb manifest must carry the release version and launch the same way
    as the plugin, with the token wired from user_config and no write toggle."""
    import tomllib  # noqa: PLC0415

    manifest = json.loads((HERE / "manifest.json").read_text())
    project = tomllib.loads((HERE / "pyproject.toml").read_text())["project"]
    assert manifest["version"] == project["version"], "bump manifest.json with pyproject"
    plugin = json.loads((HERE / "plugins/darus-review/.claude-plugin/plugin.json").read_text())
    assert plugin["version"] == project["version"], "bump plugin.json with pyproject"
    cfg = manifest["server"]["mcp_config"]
    assert cfg["args"][-3:] == ["fastmcp", "run", "main.py"]
    assert cfg["env"] == {"API_TOKEN": "${user_config.api_token}"}
    assert set(manifest["user_config"]) == {"api_token"}, "read-only: no write toggle"
    print("[ok] mcpb manifest matches project")


def test_install_entry_shape():
    """The generated Claude Desktop entry uses an absolute uv path and the fast,
    self-healing launch command (no --with, no --no-sync)."""
    import install_claude as ic

    entry = ic.build_entry("/abs/path/to/uv", "my-token")
    assert entry["command"] == "/abs/path/to/uv", "must use the absolute uv path"
    assert entry["args"][:3] == ["run", "--project", str(ic.REPO)]
    assert entry["args"][-3:] == ["fastmcp", "run", str(ic.REPO / "main.py")]
    assert "--with" not in entry["args"], "the --with overlay is what made startup ~48s"
    assert "--no-sync" not in entry["args"], "keep self-healing sync on"
    assert entry["env"] == {"API_TOKEN": "my-token"}
    print("[ok] install entry shape")


def test_install_merge_preserves_other_servers():
    """Installing us must never clobber a user's other MCP servers."""
    import install_claude as ic

    existing = {"mcpServers": {"neo4j-database": {"command": "uvx"}}}
    merged = ic.with_server(existing, ic.SERVER_NAME, {"command": "uv"})
    assert "neo4j-database" in merged["mcpServers"], "clobbered another server!"
    assert ic.SERVER_NAME in merged["mcpServers"]
    # original input must be untouched (pure function)
    assert existing == {"mcpServers": {"neo4j-database": {"command": "uvx"}}}
    print("[ok] install merge preserves other servers")


def test_install_config_path_per_os():
    """Config path resolves correctly on each supported OS."""
    import install_claude as ic

    orig_platform, orig_appdata = sys.platform, os.environ.get("APPDATA")
    try:
        sys.platform = "darwin"
        assert (
            ic.claude_desktop_config_path()
            .as_posix()
            .endswith("Library/Application Support/Claude/claude_desktop_config.json")
        )
        sys.platform = "win32"
        os.environ["APPDATA"] = str(Path.home() / "AppData" / "Roaming")
        assert (
            ic.claude_desktop_config_path()
            .as_posix()
            .endswith("Claude/claude_desktop_config.json")
        )
        sys.platform = "linux"
        assert (
            ic.claude_desktop_config_path()
            .as_posix()
            .endswith("Claude/claude_desktop_config.json")
        )
    finally:
        sys.platform = orig_platform
        if orig_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = orig_appdata
    print("[ok] install config path per OS")


def test_install_writes_and_merges_on_disk():
    """Writing the config to a real file must create missing parents, handle an
    empty file, and preserve any pre-existing servers."""
    import install_claude as ic  # noqa: PLC0415

    # Case 1: merge into an existing config that already has another server.
    with tempfile.TemporaryDirectory() as d:
        cfg = Path(d) / "claude_desktop_config.json"
        cfg.write_text(
            json.dumps({"mcpServers": {"neo4j-database": {"command": "uvx"}}})
        )
        ic.write_config(cfg, ic.SERVER_NAME, ic.build_entry("/abs/uv", "tok"))
        data = json.loads(cfg.read_text())
        assert set(data["mcpServers"]) == {"neo4j-database", ic.SERVER_NAME}
        assert data["mcpServers"][ic.SERVER_NAME]["env"]["API_TOKEN"] == "tok"

    # Case 2: no file and a missing parent directory -> created from scratch.
    with tempfile.TemporaryDirectory() as d:
        cfg = Path(d) / "Claude" / "claude_desktop_config.json"  # parent doesn't exist
        ic.write_config(cfg, ic.SERVER_NAME, ic.build_entry("/abs/uv", "t"))
        assert cfg.exists()
        assert json.loads(cfg.read_text())["mcpServers"][ic.SERVER_NAME]
    print("[ok] install writes & merges on disk")


if __name__ == "__main__":
    test_serves_tools_over_mcp()
    test_run_without_token_fails_loud()
    test_dataverse_url_keeps_path_prefix()
    test_mcp_tools_allowlist()
    test_no_tool_takes_base_url()
    test_review_tool_arguments()
    test_base_url_cannot_redirect_a_call()
    test_mcpb_manifest_matches_project()
    test_install_entry_shape()
    test_install_merge_preserves_other_servers()
    test_install_config_path_per_os()
    test_install_writes_and_merges_on_disk()
    print("all tests passed")
