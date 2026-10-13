# DaRUS Dataset Review Criteria

Criteria for reviewing a single DaRUS/Dataverse record. The question behind every
row: **could someone else understand, cite and reuse this dataset from what is
deposited?** Each row says what to check, what a violation looks like, and which
`darus-mcp` tool shows the evidence.

## Contents
1. Required changes (blocking)
2. Recommended changes
3. Out of scope
4. Applicability and unreadable evidence
5. Sources

---

## 1. Required changes (blocking)

Any violation here means the verdict is **Changes needed**.

| # | Criterion | Violation looks like | Evidence |
|---|-----------|----------------------|----------|
| M1 | Every author has an ORCID | An author has no identifier, or only a non-ORCID one (GND, Scopus, …) | `Get_Dataset_Metadata` → author identifier |
| M2 | It is clear what the dataset contains: what was measured, simulated or collected, how, and its scope (samples, cases, variables) | Description gives method or context but not what the data actually is; a reader can't tell what they'd get | `Get_Dataset_Metadata` → dsDescription, plus README if one exists |
| M3 | Every column in tabular data has a definition and a unit, and missing-data codes are explained | Column `v2` or `Qbreak` defined nowhere; numeric columns with no units; `-999`/`<LOQ`/empty columns unexplained | `Get_Tabular_File_Schema` + sampled `Read_Tabular_File` ↔ description, README, per-file descriptions (any one counts) |
| M4 | A README or the description says what each file or folder is, and every data, code or documentation file it points readers to exists | Files nobody explains; README links to data or scripts that aren't deposited. Housekeeping files (`.gitignore`, editor configs, a misnamed dotfile) are never a required change | `List_Files_in_Dataset` ↔ description / `Read_File_Content` on README |
| M5 | Software used to produce or analyse the data is named **with versions**; shipped code states its language/runtime version | "Analysed with Python" or "LC-MS/MS" with no software or version; no Python/R/Node version anywhere | description / README / manifest |
| M6 | The dataset has a license (Dataverse license or custom terms) | License field empty, even if a LICENSE file sits inside the files | `Get_Dataset_Metadata` → license / termsOfUse |
| M7 | Shipped code can be run: dependencies declared in a manifest, and run instructions name the entry point and match the deposited layout | Scripts import packages no manifest declares; no "how to run"; instructions assume folders or files the deposit doesn't have | `List_Files_in_Dataset` + `Read_File_Content` on README, manifest, entry script |

## 2. Recommended changes

Report at most the three that matter most for reuse.

| # | Criterion | Violation looks like | Evidence |
|---|-----------|----------------------|----------|
| S1 | The description stands alone: it covers the README's substance | README explains methods, variables or usage that the landing page omits | README ↔ dsDescription |
| S2 | Documentation agrees with itself and with the data | Docs disagree on versions, parameters or dates; README says 8 variables, table has 5; numeric column holds text | docs ↔ docs ↔ schema / sampled rows |
| S3 | Open, portable formats where an open alternative exists | `.xlsx` only, no `.csv`; vendor-locked binaries; text not in UTF-8 | `List_Files_in_Dataset` → mime_type |
| S4 | Code is reproducible over time: versions pinned (lockfile or pinned manifest), manifest matches real imports, random seeds recorded for stochastic work, code has a license | `numpy>=1.24` only; `import scipy` not declared; no seed for an ML run; data license but none for code | manifest / scripts / LICENSE |
| S5 | Funding documented for publicly funded work | Funder named, no grant number | `Get_Dataset_Metadata` → grantNumber |
| S6 | Related publication is linked by DOI or URL | Citation text only, nothing a machine can follow | `Get_Dataset_Metadata` → publication |

## 3. Out of scope

Out of scope for this review; never report these:

- File-level metadata: role tags, per-file descriptions, directory structure.
- EngMeta and process metadata blocks. What they would hold (system, parameters,
  software) counts only through M2 and M5, wherever it is written.
- Fields Dataverse fills or enforces itself (DOI, DataCite mandatory properties,
  required citation fields), and the contact e-mail, which the tools don't show.

## 4. Applicability and unreadable evidence

- M3 applies only when tabular files exist; M7 and S4 only when code ships
  (`.py`, `.R`, `.jl`, `.m`, `.ipynb`, `.sh`, `.c/.cpp`, `.f90`, …). Otherwise skip
  them silently.
- If a tool can't read something (format, encoding, archive), the criterion is
  **not reviewed**: neither passed nor failed. Say so in the report's "Not reviewed"
  line.
- State facts the deposit itself gives that bear on reuse even if no row covers
  them (e.g. "the authors state the code was never run"), as a required or recommended
  change when they need action.

## 5. Sources

Primary (DaRUS / FoKUS / SimTech / standards):
- DaRUS data publication guide — https://www.izus.uni-stuttgart.de/en/fokus/darus/publication/
- DaRUS / FoKUS overview — https://www.izus.uni-stuttgart.de/en/fokus/darus/
- FoKUS RDM portal — https://www.izus.uni-stuttgart.de/en/fokus/rdmportal/
- SimTech Research Data & Software Management — https://www.simtech.uni-stuttgart.de/exc/research-data-management/
- DataCite Metadata Schema 4.5 — https://datacite-metadata-schema.readthedocs.io/en/4.5/properties/overview/
- FAIR principles (Wilkinson et al. 2016) — https://www.nature.com/articles/sdata201618
- Dataverse data-quality guide — https://dataverse.org/book/data-quality
- Cornell README best practice — https://data.research.cornell.edu/data-management/sharing/readme/
