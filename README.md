# DaRUS Review MCP

Connects Claude to [DaRUS](https://darus.uni-stuttgart.de), the University of Stuttgart's
research data repository. Claude can then search and review datasets for you and, if you
allow it, create and edit draft datasets.

## Installation

### 1. Get your DaRUS API token

Log in to [DaRUS](https://darus.uni-stuttgart.de), open the menu under your name and choose **API Token**. Copy the token.
It lets Claude see your unpublished and restricted datasets; keep it private.

### 2a. Claude Desktop

1. Download [`darus-mcp.mcpb`](https://github.com/SimTech-Research-Data-Management/darus-review-mcp/releases/latest/download/darus-mcp.mcpb).
2. Double-click it (or drag it into Claude Desktop) and click **Install**.
3. Paste your API token. Leave **Allow creating and editing drafts** off unless you want
   Claude to write to DaRUS (see below).

You also need `git` installed (macOS: run `xcode-select --install`; Windows:
[git-scm.com](https://git-scm.com)). Claude Desktop sets up everything else itself.
To change the token or the switch later: **Settings → Extensions → DaRUS → Configure**.

### 2b. Claude Code

Install [`uv`](https://docs.astral.sh/uv/) and `git`, then add your token to your shell
profile (`~/.zshrc` or `~/.bashrc`):

```bash
export DARUS_API_TOKEN="<your-darus-api-token>"
export DARUS_ALLOW_WRITE=1   # optional: allow creating and editing drafts
```

Then in Claude Code:

```
/plugin marketplace add SimTech-Research-Data-Management/darus-review-mcp
/plugin install darus-review@darus
```

This also installs the **dataset review skill**: ask Claude to review a dataset and it checks
the metadata, description and files for quality, FAIR compliance and internal consistency,
against [these review criteria](plugins/darus-review/skills/darus-dataset-review/references/review-criteria.md).

If the DaRUS tools don't show up, check that `which uv` finds uv and that `DARUS_API_TOKEN`
is set in the shell you started Claude Code from. After an update, restart Claude Code so it
reloads the tool list.

### Read-only or drafts?

By default Claude can only read from DaRUS. If you switch on drafts, Claude can also
create draft datasets and fill in their metadata. **Claude never publishes**: drafts stay
private until you publish them yourself in DaRUS.

## Try it

- *"Review the DaRUS dataset doi:10.18419/DARUS-1234"*
- *"Find DaRUS datasets on molecular dynamics simulations"*
- *"Which files and columns does doi:10.18419/DARUS-1234 contain?"*
- With drafts on: *"Create a draft dataset for my simulation data and suggest keywords"*

## What Claude can do with it

- search datasets and collections in DaRUS
- read dataset metadata, file lists and file contents, including tabular files
- check metadata for consistency and completeness, and write structured review notes
- link keywords to controlled vocabularies (Wikidata, TIB, EBI OLS)
- with drafts on: create draft datasets and edit their metadata

Answers are grounded in what is actually in DaRUS, which makes Claude useful for
triaging many records before a manual expert review.

## Tools

Read (always on): `Search_Dataverse`, `Search_DataCite`, `Search_Vocabulary`,
`Get_Dataset_Metadata`, `List_Files_in_Dataset`, `Get_Collection_Metadata`,
`List_Content_of_Collection`, `Read_File_Content`, `Read_Tabular_File`,
`Get_Tabular_File_Schema`, `Knowledge_Graph_Summary`, `Query_Knowledge_Graph`,
`Dataverse_Metrics`.

Write (only with drafts switched on; never publish):

- `Create_Dataset` — create a draft with core citation metadata (title, description, authors, contacts, subjects)
- `Edit_Dataset_Metadata` — edit common citation fields on a draft (friendly, typed)
- `Edit_Dataset_Fields` — edit **any** field in **any** metadata block on a draft, built from the live schema

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

## For developers

Built on `fastmcp` and `pydataverse[mcp]`. Needs Python `3.12+`, `uv` and `git`.

### Install script (Claude Desktop without the bundle)

```bash
./install-claude.sh --token "<your-darus-api-token>"                 # read-only
./install-claude.sh --token "<your-darus-api-token>" --allow-write   # + draft write tools
```

Adds a `darus-mcp` entry to `claude_desktop_config.json` (other servers are kept), with the
token in plain text. Fully quit and reopen Claude Desktop afterwards.

### Run locally

```bash
API_TOKEN="<your-darus-api-token>" uv run python main.py
```

The server starts on `http://0.0.0.0:8000` using `streamable-http` transport.

### Build the Claude Desktop bundle

```bash
npx @anthropic-ai/mcpb pack . darus-mcp.mcpb
```

CI attaches it to every published GitHub release.

### Configuration

All variables are optional except where noted; unset means the defaults below.

| Variable | Default | Purpose |
|---|---|---|
| `API_TOKEN` | — (required for `python main.py`) | Dataverse API token, sent as `X-Dataverse-key`. |
| `DATAVERSE_URL` | `https://darus.uni-stuttgart.de` | Dataverse instance to talk to. May include a path (e.g. a proxy at `http://127.0.0.1:9000/dv/<job_id>`); a trailing `/` is added automatically. |
| `ALLOW_WRITE` | off (read-only) | `1` adds the draft write tools. Set by the bundle's switch, `--allow-write` or `DARUS_ALLOW_WRITE`. |
| `MCP_TOOLS` | all tools | Comma-separated allowlist of tool names (see [Tools](#tools)). Other tools are hidden and fail as unknown. Names must match exactly; a misspelt name is silently not exposed. |

Tools always talk to `DATAVERSE_URL`. pyDataverse's per-call `base_url` argument is removed from every tool, so a caller cannot redirect a tool to another host.

The cost: `Search_DataCite` finds datasets on other Dataverse installations and returns a `base_url` for each hit. Those hits can no longer be opened through this server's tools; that takes another server instance with its own `DATAVERSE_URL`.

### Security

- Treat your API token as a secret and never commit it.
- Prefer passing credentials via environment variables or secure secret stores.

### Project layout

- `main.py` - MCP server bootstrap, DaRUS tool registration, and vocabulary-source config
- `manifest.json`, `.mcpbignore`, `icon.png` - Claude Desktop bundle (`.mcpb`). Keep `version` in sync with `pyproject.toml`.
- `install_claude.py` - cross-platform Claude Desktop installer (writes the launch entry + token)
- `install-claude.sh` - thin shell wrapper around the installer
- `test_darus.py` - runnable checks (`uv run python test_darus.py`)
- `docs/` - spec and implementation plan for the create-dataset workflow
- `.claude-plugin/marketplace.json` - marketplace catalog so others can install the plugin
- `plugins/darus-review/` - the shareable plugin: review skill + criteria + MCP wiring
- `pyproject.toml` - project metadata and dependencies
