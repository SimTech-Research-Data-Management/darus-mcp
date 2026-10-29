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
with no chance to ask back. **Required and recommended changes together: at most
~150 words**, one example per line, not a list ("Not reviewed" doesn't count toward
it). Plain and factual: no praise, no softening ("great work, just a
few things"). What the deposit already does well goes first, under "Already in place":
facts, not compliments, so the researcher sees what to keep.

**Write for the researcher, not for a curator.** Name places the way the DaRUS edit
form shows them ("License, Terms tab", "Description", "Author identifier"), never
internal field names like `dsDescription` or `termsOfUse`. No words a researcher
wouldn't use: fixture, MIME type, ingest, schema, metadata block, PID. File names,
column names and values go in backticks; they are the researcher's own words.

```
# <dataset title>
<DOI>

**Ready to submit:** nothing blocks reuse.
  or
**<n> mandatory change(s) needed**

## Already in place
- <what is there>: <form field, file or column>

## Mandatory changes
- <problem>: <form field, file or column>. <the fix>

## Recommended changes
- <problem>: <form field, file or column>. <the fix>

## Not reviewed
- <file>: <why, in a few words>
```

- **The verdict line is fixed wording**, exactly one of the two lines above. Never a
  justification: the lists say why.
- **Ready to submit** when no section-1 criterion is violated; otherwise the
  number of mandatory changes, nothing else on the line.
- **Already in place:** 2 to 4 things the deposit gets right that matter for reuse, each
  grounded like a change ("License, Terms tab: CC BY 4.0", "`csv_files/`: one file per
  figure panel, named after it"). Only what you checked; never a criterion you could not
  review. Does not count toward the ~150 words. Omit if nothing qualifies.
- **Mandatory changes:** every section-1 violation, most severe first. Omit the heading if there are none.
- **Recommended changes:** at most 3 section-2 items, the ones that matter most for reuse. Omit if none.
- **Not reviewed:** one line per file a tool couldn't read when a criterion needs it
  (section 4), e.g. "`a.txt`: restricted by you". Omit if none.
- The four `##` headings above are the only headings, spelled exactly so. No criterion
  numbers, no criteria section names, no follow-up offer. Never report what section 3
  excludes.

Grounding: every line names the field, file or column it rests on
("Description says how samples were taken but not which compounds were measured",
not "description is vague").
