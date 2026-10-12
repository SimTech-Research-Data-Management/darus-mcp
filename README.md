# DaRUS Review MCP

`darus-review-mcp` is a Model Context Protocol (MCP) server that connects LLM assistants to the [DaRUS Dataverse](https://darus.uni-stuttgart.de) API.

It enables AI clients (for example Claude Desktop via MCP) to search datasets, inspect metadata, and retrieve repository context that can be used during scientific or data-quality reviews — and to **author** datasets: create draft datasets and enrich their metadata, including controlled-vocabulary keyword lookup.

## What It Is

This project provides a lightweight MCP wrapper around Dataverse capabilities using:

- `fastmcp` for exposing tools to MCP-compatible clients
- `pydataverse[mcp]` for Dataverse API and MCP tool integration
- a DaRUS-targeted configuration (`https://darus.uni-stuttgart.de`)

## What It Does

When running, the server exposes Dataverse-backed MCP tools that allow an LLM client to:

- search datasets and dataverses in DaRUS
- retrieve structured dataset metadata
- access publication and file-level repository context
- use repository evidence as context during review workflows
- create draft datasets and edit their metadata (draft only — never publishes)
- look up controlled-vocabulary terms to link keywords semantically

In practice, this turns DaRUS into a live, queryable context source for AI-assisted review — and a way to author well-described datasets from a chat client.

## Tools

Read / discovery (always on): `Search_Dataverse`, `Search_DataCite`, `Search_Vocabulary`,
`Get_Dataset_Metadata`, `List_Files_in_Dataset`, `Get_Collection_Metadata`,
`List_Content_of_Collection`, `Read_File_Content`, `Read_Tabular_File`,
`Get_Tabular_File_Schema`, `Knowledge_Graph_Summary`, `Query_Knowledge_Graph`,
`Dataverse_Metrics`.

Write (opt-in via `dataset=["read","create","edit"]`, requires `API_TOKEN`; all draft-only):

- `Create_Dataset` — create a draft with core citation metadata (title, description, authors, contacts, subjects)
- `Edit_Dataset_Metadata` — edit common citation fields on a draft (friendly, typed)
- `Edit_Dataset_Fields` — edit **any** field in **any** metadata block on a draft, built from the live schema

Writes never publish; publishing stays a manual step performed by the user.

## Controlled-vocabulary sources

`Search_Vocabulary` resolves a plain term to candidates with a term URI so keywords can be
linked to a controlled vocabulary (`keywordValue` + `keywordVocabulary` + `keywordTermURI`)
rather than left as free text. It queries the sources configured in `main.py`; by default:

| Source | Type | Endpoint | Coverage |
|--------|------|----------|----------|
| Wikidata | wikidata | `https://www.wikidata.org` | general, cross-domain |
| TIB | ols | `https://api.terminology.tib.eu` | engineering / chemistry (NFDI4Ing, NFDI4Chem), EDAM, ChMO |
| EBI OLS | ols | `https://www.ebi.ac.uk/ols4` | life sciences and general ontologies |

A query searches **all** configured sources by default (results tagged by source); pass
`source="TIB"` to narrow to one. Add or remove sources by editing the `vocabulary_sources`
list in `main.py` — any OLS4-compatible service works via its `base_url`. These choices live
here in the app; the generic `pyDataverse` library defaults to Wikidata + EBI OLS only.

## Using LLMs to Conduct Reviews

LLMs are most useful for review workflows when they can access repository-grounded facts instead of relying only on prompts.

With this MCP server:

1. the assistant can discover candidate datasets and related metadata in DaRUS,
2. inspect the relevant context (publication details, files, descriptive metadata),
3. generate review feedback based on that retrieved evidence.

Typical outcomes include:

- consistency checks between metadata fields
- completeness checks for dataset documentation
- structured review notes and suggested follow-ups
- faster triage across many records before manual expert review

## Installation

### Prerequisites

- Python `3.12+`
- [`uv`](https://docs.astral.sh/uv/) for environment and dependency execution
- A DaRUS API token

### Why the token is required

Your API token is passed to the MCP server as `API_TOKEN`.
It is used to authenticate against DaRUS and allows access to restricted or unpublished datasets that are not publicly visible.

Without a valid token, the server cannot query protected repository content.

### Install as a plugin (recommended for sharing)

The `darus-review` plugin bundles the review **skill** with this **MCP server**, so one
install gets both:

```
/plugin marketplace add SimTech-Research-Data-Management/darus-review-mcp
/plugin install darus-review@darus
```

Requires `uv` on your `PATH` and a `DARUS_API_TOKEN` environment variable.
See [plugins/darus-review/README.md](plugins/darus-review/README.md).

### Install for Claude Desktop (MCP only)

From the repository root:

```bash
chmod +x install-claude.sh
./install-claude.sh --token "<your-darus-api-token>"
```

The installer registers this MCP server and injects the token as:

```bash
--env API_TOKEN=<your-darus-api-token>
```

### Run locally

```bash
API_TOKEN="<your-darus-api-token>" uv run python main.py
```

The server starts on `http://0.0.0.0:8000` using `streamable-http` transport.

### Configuration

All variables are optional except where noted; unset means the defaults below.

| Variable | Default | Purpose |
|---|---|---|
| `API_TOKEN` | — (required for `python main.py`) | Dataverse API token, sent as `X-Dataverse-key`. |
| `DATAVERSE_URL` | `https://darus.uni-stuttgart.de` | Dataverse instance to talk to. May include a path (e.g. a proxy at `http://127.0.0.1:9000/dv/<job_id>`); a trailing `/` is added automatically. |
| `MCP_TOOLS` | all tools | Comma-separated allowlist of tool names (see [Tools](#tools)). Other tools are hidden and fail as unknown. Names must match exactly; a misspelt name is silently not exposed. |

Tools always talk to `DATAVERSE_URL`. pyDataverse's per-call `base_url` argument is removed from every tool, so a caller cannot redirect a tool to another host.

## Security Notes

- Treat your API token as a secret.
- Do not commit tokens to version control.
- Prefer passing credentials via environment variables or secure secret stores.

## Project Layout

- `main.py` - MCP server bootstrap, DaRUS tool registration, and vocabulary-source config
- `install_claude.py` - cross-platform Claude Desktop installer (writes the launch entry + token)
- `install-claude.sh` - thin shell wrapper around the installer
- `test_darus.py` - runnable checks (`uv run python test_darus.py`)
- `docs/` - spec and implementation plan for the create-dataset workflow
- `.claude-plugin/marketplace.json` - marketplace catalog so others can install the plugin
- `plugins/darus-review/` - the shareable plugin: review skill + criteria + MCP wiring
- `pyproject.toml` - project metadata and dependencies
