---
name: darus-dataset-review
description: >-
  Review a DaRUS (or any Dataverse) research dataset for quality, FAIR
  compliance, and internal consistency between its metadata, human-readable
  description, and data files/tables. Use this whenever the user wants to
  review, audit, quality-check, curate, or assess a DaRUS/Dataverse dataset;
  check whether a dataset's metadata is complete; verify that a description
  matches its files or tabular columns; check whether it is clear what a dataset
  contains and which software produced it; check whether a dataset that
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

3. **Pull the full metadata.** `Get_Dataset_Metadata` for the complete record.
   Read the description text carefully; you'll cross-reference it against files
   and schemas later.

4. **List the files.** `List_Files_in_Dataset`. Note formats and whether a
   README or documentation file exists.

5. **Inspect tabular data where it matters.** For each tabular file relevant to
   the review, `Get_Tabular_File_Schema` for columns/types, and
   `Read_Tabular_File` for a small **sample** (not the whole file — reads can be
   large).

6. **Read the documentation** — the description, any README/codebook
   (`Read_File_Content`), and per-file descriptions. Read every surface that
   exists.

7. **If the dataset ships code, read it.** `Read_File_Content` on the dependency
   and instruction files so M5, M7 and S4 can be checked.

8. **Cross-check and score.** Run every criterion whose inputs exist. The rows
   whose Evidence column contains `↔` are cross-tool checks; they are what
   automated validators miss, so they usually carry the highest-value findings.

Only pull as much file/table detail as the review needs. A completeness check of
citation metadata doesn't require reading every CSV; a "do the tables match the
description" check does.

## Reporting the review

One report, complete on its own: researchers may read it once on a web page
with no chance to ask back. **Must fix and Should fix together: at most ~150
words**, one example per line, not a list ("Not checked" and "Solid" don't count
toward it). Plain and factual: no praise,
no softening ("great work, just a few things"), no list of what passed.

```
# <dataset title> (<DOI>)
**Verdict:** <Ready | Not ready>: <the main reason, one sentence>

**Must fix**
- <problem>: <field/file/column>. <the fix>

**Should fix**
- <problem>: <field/file>. <the fix>

**Not checked:** <what, and why>
**Solid:** <one factual line>
```

- **Must fix:** every section-1 violation, most severe first. Omit the heading if there are none.
- **Should fix:** at most 3 section-2 items, the ones that matter most for reuse. Omit if none.
- **Not checked:** only when a tool couldn't read something a criterion needs (section 4).
- **Solid:** only when something stands out that a reader can rely on (e.g. "README
  defines every column with units"). A fact, not a compliment. Usually omitted.
- No criterion numbers, no section names, no follow-up offer. Never report what
  section 3 excludes.

Grounding: every line names the field, file or column it rests on
("Description says how samples were taken but not which compounds were measured",
not "description is vague").
