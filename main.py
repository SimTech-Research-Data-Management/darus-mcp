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
from collections.abc import Sequence
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.transforms import GetToolNext, Transform
from fastmcp.tools import Tool
from fastmcp.tools.tool_transform import ArgTransformConfig, ToolTransformConfig
from fastmcp.utilities.versions import VersionSpec
from pyDataverse import Dataverse
from pyDataverse.mcp import DataverseMCP, MCPConfiguration, VocabularySource

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

# Register Dataverse MCP tools with the application.
# dataset=["read", "create", "edit"] opts in to the draft write tools (needs API_TOKEN).
# vocabulary_sources are DaRUS's choice of term services (kept out of generic pyDataverse):
# Wikidata for general terms, plus the TIB Terminology Service for engineering/chemistry
# ontologies (NFDI4Ing/NFDI4Chem), plus the EBI OLS for life sciences.
DataverseMCP(
    dataverse=darus,
    config=MCPConfiguration(
        dataset=["read", "create", "edit"],
        vocabulary_sources=[
            VocabularySource(name="Wikidata", type="wikidata"),
            VocabularySource(
                name="TIB", type="ols", base_url="https://api.terminology.tib.eu"
            ),
            VocabularySource(
                name="EBI OLS", type="ols", base_url="https://www.ebi.ac.uk/ols4"
            ),
        ],
    ),
).to_mcp(app)


class HideBaseUrl(Transform):
    """Remove the per-call `base_url` argument pyDataverse puts on its tools.

    With it, any caller (a prompt-injected model included) could point a tool at a
    host of its choosing and carry data out in that request's URL. This server is
    bound to one instance, DATAVERSE_URL; hidden, the argument always takes its
    default, None, which means exactly that instance.
    """

    _hide = ToolTransformConfig(arguments={"base_url": ArgTransformConfig(hide=True)})

    # pyDataverse's `base_url_instructions` ends every description with this exact
    # sentence (even on tools without the argument). Removed verbatim, so any other
    # mention of base_url stays visible and fails test_no_tool_takes_base_url.
    _sentence = (
        " Provide the `base_url` parameter if you want to use a different dataverse."
    )

    def _apply(self, tool: Tool) -> Tool:
        if "base_url" in tool.parameters.get("properties", {}):
            tool = self._hide.apply(tool)
        if tool.description and "base_url" in tool.description:
            tool = tool.model_copy(
                update={
                    "description": tool.description.replace(self._sentence, "").rstrip()
                }
            )
        return tool

    async def list_tools(self, tools: Sequence[Tool]) -> Sequence[Tool]:
        return [self._apply(t) for t in tools]

    async def get_tool(
        self, name: str, call_next: GetToolNext, *, version: VersionSpec | None = None
    ) -> Tool | None:
        tool = await call_next(name, version=version)
        return self._apply(tool) if tool is not None else None


app.add_transform(HideBaseUrl())

# Optional tool allowlist, e.g. for a read-only review agent. Unset = all tools.
# Hidden tools are not listed, and calling one fails as "Unknown tool".
if tools := os.environ.get("MCP_TOOLS"):
    app.enable(names={name.strip() for name in tools.split(",")}, only=True)

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
