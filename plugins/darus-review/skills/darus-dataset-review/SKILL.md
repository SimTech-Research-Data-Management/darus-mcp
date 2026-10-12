---
name: darus-dataset-review
description: >-
  Review a DaRUS (or any Dataverse) research dataset for quality, FAIR
  compliance, and internal consistency between its metadata, human-readable
  description, and data files/tables. Use this whenever the user wants to
  review, audit, quality-check, curate, or assess a DaRUS/Dataverse dataset;
  check whether a dataset's metadata is complete; verify that a description
  matches its files or tabular columns; evaluate EngMeta / discipline metadata
  for computational-science and engineering data; check whether a dataset that
  ships code is reproducible (dependencies declared, run instructions given); or
  judge whether a dataset meets University of Stuttgart / SimTech / FoKUS RDM and
  FAIR best practices — even if they don't say the word "review". Requires the
  darus-mcp MCP server.
---

# DaRUS Dataset Review

## What this does

Review a DaRUS dataset by pulling its real metadata, files, and tabular schemas
via `darus-mcp` and checking them against `references/review-criteria.md`. Every finding
must point at a specific field, file, or column.

## Prerequisites

The `darus-mcp` MCP server must be connected. If its tools aren't available, say
so rather than reviewing from the landing page or memory.

## Workflow

Work in this order — cheap, broad evidence first, then drill into files only
where the metadata gives you something to check against.

1. **Load `references/review-criteria.md`.** It is the authoritative criteria list and
   defines what each later step needs to collect and when a section applies.

2. **Locate the dataset.** If the user gave a DOI/PID (e.g.
   `doi:10.18419/darus-XXXX`), use it directly. Otherwise `Search_Dataverse`
   to find it and confirm the match with the user before reviewing.

3. **Pull the full metadata.** `Get_Dataset_Metadata` for the complete record
   (citation block + any discipline blocks like EngMeta, process, enzymeML). This
   is the backbone — most criteria are checked here. Read the description text
   carefully; you'll cross-reference it against files and schemas later.

4. **List the files.** `List_Files_in_Dataset`. Note file roles/tags,
   per-file descriptions, directory structure, formats, and whether a README or
   documentation file exists.

5. **Inspect tabular data where it matters.** For each tabular file relevant to
   the review, `Get_Tabular_File_Schema` for columns/types, and
   `Read_Tabular_File` for a small **sample** (not the whole file — reads can be
   large).

6. **Read the documentation** — the description, any README/codebook
   (`Read_File_Content`), and per-file descriptions. Read every surface that
   exists.

7. **If the dataset ships code, read it.** `Read_File_Content` on the dependency
   and instruction files so section 7 can be scored.

8. **Cross-check and score.** Run every criterion whose inputs exist. The rows
   whose Evidence column contains `↔` are cross-tool checks; they are what
   automated validators miss, so they usually carry the highest-value findings.

Only pull as much file/table detail as the review needs. A completeness check of
citation metadata doesn't require reading every CSV; a "do the tables match the
description" check does.

## Reporting the review

Default to a **TLDR nobody has to scroll.** Lead with the verdict; below it list
only what's wrong. Never enumerate what passed — a roll-call of ✅ is the bloat
that makes people skip the review and go read the data themselves.

```
# <dataset title> (<DOI>)
**Verdict:** <publishable? — N blocking, M minor>

❌ <criterion> — <field/file/column> — <what's wrong → the fix>
⚠️ <criterion> — <field/file> — <fix>
```

- Blocking (❌) first, then minor (⚠️), one line each. No passes. No per-dimension roll-call.
- Nothing blocks? Say so in the verdict, then list at most the top 3 minor items.
- Don't dump detail — offer it. End with: *"Say 'full breakdown' for per-dimension scoring."* Expand only if asked.

Grounding (unchanged): every line names the field/file/column it rests on
("Description states no method; violates 2.1", not "description is vague"); mark
blocking vs cosmetic per the criteria's section 1 gate; obey the criteria's own
N/A and confidence rules (sections 3, 7, 9).
