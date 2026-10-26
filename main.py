"""
DaRUS MCP Server

This module provides a Model Context Protocol (MCP) server for interacting with the
DaRUS (Data Repository of the University of Stuttgart) Dataverse instance.

The server exposes Dataverse functionality through MCP tools, allowing AI assistants
to search, retrieve, and interact with datasets and metadata stored in DaRUS.

Features:
    - Search datasets and dataverses in DaRUS
    - Retrieve dataset metadata and files
    - Access publication information

Usage:
    Run this server to expose DaRUS functionality via MCP:

    $ python main.py

    The server will start on http://0.0.0.0:8000 and provide MCP tools for:
    - Dataverse operations (search, metadata retrieval)

Dependencies:
    - fastmcp: MCP server framework
    - pyDataverse: Dataverse API client
    - python-dotenv: loads API_TOKEN from a local .env file
"""

import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.tools.tool_transform import ArgTransformConfig, ToolTransformConfig
from pyDataverse import Dataverse
from pyDataverse.mcp import DataverseMCP

load_dotenv()

# Load the API token from the environment variable.
api_token = os.environ.get("API_TOKEN")

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


# Create the FastMCP application
_version = tomllib.loads((Path(__file__).parent / "pyproject.toml").read_text())[
    "project"
]["version"]
app = FastMCP(name="darus-mcp", version=_version)

# Register Dataverse MCP tools with the application. pyDataverse's default
# configuration is read-only: no tool creates, edits or publishes anything.
# The draft write tools live on the `write-tools` branch.
DataverseMCP(dataverse=darus).to_mcp(app)

# pyDataverse puts a per-call `base_url` argument on its tools. With it, any caller
# (a prompt-injected model included) could point a tool at a host of its choosing
# and carry data out in that request's URL. This server is bound to one instance,
# DATAVERSE_URL; hidden, the argument always takes its default, None, which means
# exactly that instance.
_hide_base_url = {"base_url": ArgTransformConfig(hide=True)}

# pyDataverse's `base_url_instructions` ends every description with this exact
# sentence (even on tools without the argument). Removed verbatim, so any other
# mention of base_url stays visible and fails test_no_tool_takes_base_url.
_base_url_sentence = (
    " Provide the `base_url` parameter if you want to use a different dataverse."
)

# Optional tool allowlist, e.g. for a narrower review agent. Unset = all tools.
# Left-out tools are removed, so they are not listed and calling one fails as
# "Unknown tool".
allowlist = os.environ.get("MCP_TOOLS")
keep = {name.strip() for name in allowlist.split(",")} if allowlist else None

# shortcut: reads fastmcp 2's private tool registry, because `fastmcp run` imports
# this module inside its event loop, where the async get_tools() can't be awaited.
# Replace with the v3 Transform API (see the `write-tools` branch) once pyDataverse
# allows fastmcp 3.
for name, tool in list(app._tool_manager._tools.items()):
    if keep is not None and name not in keep:
        app.remove_tool(name)
        continue
    takes_base_url = "base_url" in tool.parameters.get("properties", {})
    told = bool(tool.description) and "base_url" in tool.description
    if takes_base_url or told:
        app.add_tool_transformation(
            name,
            ToolTransformConfig(
                arguments=_hide_base_url if takes_base_url else {},
                description=tool.description.replace(_base_url_sentence, "").rstrip()
                if told
                else None,
            ),
        )

if __name__ == "__main__":
    """
    Main entry point for the DaRUS MCP server.
    
    Starts the MCP server using streamable HTTP transport on all interfaces
    at port 8000. The server will handle MCP requests and provide access to
    the DaRUS Dataverse tools.
    
    Server Configuration:
        - Transport: streamable-http (compatible with MCP clients)
        - Host: 0.0.0.0 (accepts connections from any interface)
        - Port: 8000 (standard development port)
    """
    if not api_token:
        raise ValueError("API_TOKEN environment variable is not set")

    # Start the MCP server
    app.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
    )
