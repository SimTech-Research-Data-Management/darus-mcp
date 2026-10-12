# DaRUS Review plugin

Bundles the **`darus-dataset-review` skill** (review workflow + FAIR/quality criteria)
with the **`darus-mcp` server** that gives it live access to DaRUS. One install gets
you both.

## Install

```
/plugin marketplace add SimTech-Research-Data-Management/darus-review-mcp
/plugin install darus-review@darus
```

Then ask Claude to review a dataset, e.g.
*"Review the DaRUS dataset doi:10.18419/DARUS-1234"*.

## Prerequisites

Two things can't be shipped inside a plugin — set them up once:

1. **[`uv`](https://docs.astral.sh/uv/)** on your `PATH`. The MCP server runs via
   `uv run`, which installs the Python dependencies on first launch.
2. **A DaRUS API token** exported as `DARUS_API_TOKEN`:

   ```bash
   export DARUS_API_TOKEN="<your-darus-api-token>"   # add to ~/.zshrc or ~/.bashrc
   ```

   The token authenticates against DaRUS and is required to read unpublished or
   restricted datasets. Treat it as a secret; never commit it.

## What you get

- **Skill** `darus-dataset-review` — reviews a dataset's metadata, description, and
  files for quality, FAIR compliance, and internal consistency, scored against
  [`references/review-criteria.md`](skills/darus-dataset-review/references/review-criteria.md).
- **MCP server** `darus-mcp` — search DaRUS, read dataset metadata and files, and
  (opt-in) create/edit draft datasets and look up controlled-vocabulary terms.

Writes are draft-only; the server never publishes a dataset.

## Troubleshooting

- **Server won't start** — check `uv` is on your `PATH` (`which uv`) and that
  `DARUS_API_TOKEN` is exported in the environment Claude was launched from.
- **Tools missing after an update** — MCP clients cache the tool list at connect
  time. Fully quit and reopen the client so it re-fetches.
