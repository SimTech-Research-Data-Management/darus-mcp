#!/usr/bin/env python3
"""Register the DaRUS MCP server with Claude Desktop, cross-platform.

Why this exists instead of `fastmcp install`:
  Claude Desktop is a GUI app that launches MCP servers with a minimal PATH, so a
  bare `uv` command isn't found. And `fastmcp install` adds `--with fastmcp`,
  which makes uv rebuild an overlay environment on every launch (~48s) — long
  enough that Desktop times out and shows the server as missing. This writes a
  launch command that is both fast and self-healing:

      <abs-uv> run --project <repo> fastmcp run <repo>/main.py

  - absolute uv path  -> found regardless of Desktop's PATH
  - plain `uv run`    -> rebuilds .venv from uv.lock if missing/stale (self-heal)
  - no `--with`       -> ~2s warm start instead of ~48s

Usage:
    uv run python install_claude.py --token <darus-api-token> [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SERVER_NAME = "darus-mcp"
REPO = Path(__file__).resolve().parent


def claude_desktop_config_path() -> Path:
    """Return the Claude Desktop config path for the current OS."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if not base:
            raise RuntimeError("APPDATA is not set; cannot locate the Claude Desktop config.")
        return Path(base) / "Claude" / "claude_desktop_config.json"
    # Linux / other: Claude Desktop (where available) follows the XDG config dir.
    base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(base) / "Claude" / "claude_desktop_config.json"


def find_uv() -> str:
    """Absolute path to the uv executable (needed because Desktop's PATH is minimal)."""
    uv = shutil.which("uv")
    if not uv:
        sys.exit("Error: 'uv' not found on PATH. Install uv first: https://docs.astral.sh/uv/")
    return uv


def build_entry(uv_bin: str, token: str) -> dict:
    main_py = REPO / "main.py"
    return {
        "command": uv_bin,
        "args": ["run", "--project", str(REPO), "fastmcp", "run", str(main_py)],
        "env": {"API_TOKEN": token},
    }


def with_server(config: dict, name: str, entry: dict) -> dict:
    """Return a copy of config with `name` set to `entry`, preserving other servers.

    Kept pure (no disk I/O) so it can be tested — the important guarantee is that
    installing us never clobbers a user's other MCP servers.
    """
    config = dict(config)
    servers = dict(config.get("mcpServers", {}))
    servers[name] = entry
    config["mcpServers"] = servers
    return config


def write_config(cfg_path: Path, name: str, entry: dict) -> dict:
    """Merge `entry` into the config file at cfg_path (creating it if absent).

    Handles the fiddly cases a naive write would get wrong — a missing parent
    directory and an empty/whitespace file — so those are covered by tests
    instead of only surfacing on someone's machine.
    """
    if cfg_path.exists():
        data = json.loads(cfg_path.read_text() or "{}")
    else:
        data = {}
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
    data = with_server(data, name, entry)
    cfg_path.write_text(json.dumps(data, indent=2))
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the DaRUS MCP server into Claude Desktop.")
    parser.add_argument("--token", required=True, help="DaRUS API token")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be written and exit.")
    args = parser.parse_args()
    if not args.token.strip():
        sys.exit("Error: --token must not be empty.")

    uv_bin = find_uv()
    cfg_path = claude_desktop_config_path()
    entry = build_entry(uv_bin, args.token)

    if args.dry_run:
        print(f"Config path: {cfg_path}")
        print(f"Server '{SERVER_NAME}':")
        print(json.dumps({**entry, "env": {**entry["env"], "API_TOKEN": "<redacted>"}}, indent=2))
        return

    # Pre-sync so the very first Desktop launch is already fast (env built ahead of time).
    print("Syncing environment (uv sync)...")
    subprocess.run([uv_bin, "sync", "--project", str(REPO)], check=True)

    # Merge into any existing config without clobbering other servers.
    write_config(cfg_path, SERVER_NAME, entry)

    print(f"Installed '{SERVER_NAME}' -> {cfg_path}")
    print("Fully quit Claude Desktop (Cmd/Ctrl+Q) and reopen it; the DaRUS tools appear after ~2s.")


if __name__ == "__main__":
    main()
