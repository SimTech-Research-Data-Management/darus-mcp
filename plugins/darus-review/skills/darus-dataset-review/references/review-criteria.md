# DaRUS Dataset Review Criteria

Criteria for reviewing a single DaRUS/Dataverse record. Each row: what to check,
what a violation looks like, and which `darus-mcp` tool shows the evidence.

## Contents
1. Mandatory identity & citation (hard gate)
2. Description sufficiency & internal consistency
3. Discipline metadata — EngMeta (CSE/engineering data)
4. Process / provenance metadata
5. File-level quality
6. Tabular data ↔ documentation consistency
7. Computational reproducibility — code & software
8. Overall reproducibility & curation
9. Confidence caveats
10. Sources

---

## 1. Mandatory identity & citation (hard gate)

Failing any of these is **blocking** — the record is considered not publishable.

| # | Criterion | Violation looks like | Evidence |
|---|-----------|----------------------|----------|
| 1.1 | Five required Dataverse fields present: Title, Author, Contact, Description, Subject | Any empty | `Get_Dataset_Metadata` → citation block |
| 1.2 | Six DataCite-mandatory properties: Identifier, Creator, Title, Publisher, PublicationYear, ResourceType | Missing any | `Get_Dataset_Metadata` |
| 1.3 | Author has an ORCID | ORCID absent | `Get_Dataset_Metadata` → author identifier |
| 1.4 | Long-term / institutional contact e-mail | Personal throwaway or missing | `Get_Dataset_Metadata` → datasetContact |
| 1.5 | Persistent DOI assigned, and metadata references the data it describes (FAIR F1/F3) | No DOI, or metadata doesn't point at its files | `Get_Dataset_Metadata` |

## 2. Description sufficiency & internal consistency

| # | Criterion | Violation looks like | Evidence |
|---|-----------|----------------------|----------|
| 2.1 | Description lets a third party understand & reuse the data | Vague one-liner; no method/context | `Get_Dataset_Metadata` → dsDescription |
| 2.2 | Every file/table/directory named in the description exists | Description cites a file not in the list, or files nobody explains | description ↔ `List_Files_in_Dataset` |
| 2.3 | Variables/quantities named in the description match real columns | Prose names variables the tables lack | description ↔ `Get_Tabular_File_Schema` |
| 2.4 | Description covers the substance of the README, if one exists — the landing page stands alone | README explains methods, variables or usage that the description omits, so the dataset can't be understood without downloading files | `Read_File_Content` on README ↔ `Get_Dataset_Metadata` → dsDescription |
| 2.5 | Funding / public-financing documented | Public-funded, no grant info | `Get_Dataset_Metadata` → grantNumber |

## 3. Discipline metadata — EngMeta (CSE / engineering data)

Applies to computational-science/engineering data (DaRUS **EngMeta** block).
Context conveyed only via file/folder names instead of these fields is a
violation, not a pass.

| # | Criterion | Violation looks like | Evidence |
|---|-----------|----------------------|----------|
| 3.1 | Observed/simulated system described: components, controlled + measured variables | Empty discipline fields on a simulation dataset | `Get_Dataset_Metadata` → EngMeta block |
| 3.2 | System parameters as name/value pairs (e.g. "Reynolds Number" = …) | Key physical parameters absent | `Get_Dataset_Metadata` |
| 3.3 | Spatial & temporal resolution stated where applicable | Simulation with no resolution metadata | `Get_Dataset_Metadata` |
| 3.4 | Discipline-metadata values are consistent with the data | EngMeta names variable X; no table contains X | EngMeta block ↔ `Get_Tabular_File_Schema` / `Read_Tabular_File` |

## 4. Process / provenance metadata (EngMeta process block)

| # | Criterion | Violation looks like | Evidence |
|---|-----------|----------------------|----------|
| 4.1 | Software / instruments used are recorded | No software named for a simulation dataset | `Get_Dataset_Metadata` → process block |
| 4.2 | Methods documented with ≥1 parameter | Method listed, zero parameters | `Get_Dataset_Metadata` |
| 4.3 | Computational environment / processing steps captured (generation → analysis → visualization) | Reproducibility unclear | `Get_Dataset_Metadata` |

## 5. File-level quality

| # | Criterion | Violation looks like | Evidence |
|---|-----------|----------------------|----------|
| 5.1 | Files tagged by role (data vs. documentation) | Untagged pile | `List_Files_in_Dataset` → tags |
| 5.2 | Per-file descriptions present | Files with no description | `List_Files_in_Dataset` |
| 5.3 | Directory hierarchy via path field when many files | Flat dump of many files | `List_Files_in_Dataset` → directoryLabel |
| 5.4 | Open/portable formats where an open alternative exists | Proprietary-only (e.g. `.xlsx` not `.csv`, vendor-locked binaries) with no open export alongside | `List_Files_in_Dataset` → mime_type |

## 6. Tabular data ↔ documentation consistency

Run whenever tabular files exist. **Documentation** = the dataset description, a
README/doc file, or per-file descriptions; a variable is documented if **any** of
them defines it, so check all that exist and name which one. No README is 5.4's
finding, not a 6.x failure; a 2.4 gap is a separate finding, not a second count.

| # | Criterion | Violation looks like | Evidence |
|---|-----------|----------------------|----------|
| 6.1 | Every column has a documented name + definition | Column `v2` defined in no documentation surface | `Get_Tabular_File_Schema` ↔ documentation |
| 6.2 | Units of measurement documented per variable | Numeric columns, no units anywhere | schema ↔ documentation |
| 6.3 | Missing-data codes defined | `-999`/`NA` used but undefined | `Read_Tabular_File` (sample) ↔ documentation |
| 6.4 | Column types match actual values | Numeric column holds text; broken date column | `Get_Tabular_File_Schema` ↔ sampled `Read_Tabular_File` |
| 6.5 | Column set matches what the documentation claims | README or description lists 8 variables; table has 5 | schema ↔ documentation |

## 7. Computational reproducibility — code & software

Applies when the dataset ships code (`.py`, `.R`, `.jl`, `.m`, `.ipynb`, `.sh`,
`.c/.cpp`, `.f90`, …).

| # | Criterion | Violation looks like | Evidence |
|---|-----------|----------------------|----------|
| 7.1 | Dependencies are **declared** in a manifest, not left implicit | Python scripts import `numpy`/`pandas` but no `pyproject.toml`, `uv.lock`, `requirements.txt`, `environment.yml`, `Pipfile.lock` or `poetry.lock`; R without `renv.lock`/`DESCRIPTION`; Julia without `Project.toml`/`Manifest.toml`; JS without `package.json`/lockfile | `List_Files_in_Dataset` + `Read_File_Content` on manifest |
| 7.2 | Dependency **versions are pinned** (a lockfile, or pinned versions in the manifest) | Manifest lists bare package names with no versions → not reproducible over time | `Read_File_Content` on manifest/lockfile |
| 7.3 | **Execution instructions** exist: how to install, and how to run, with the entry point named | README has code but never says how to run it, or names no entry script/command | `Read_File_Content` on README ↔ `List_Files_in_Dataset` |
| 7.4 | **Language/runtime version** stated | No Python/R/Julia version anywhere (`.python-version`, README, or manifest `requires-python`) | manifest / README |
| 7.5 | Manifest **matches the code's real imports** | `import scipy` in a script but `scipy` absent from the declared dependencies (or vice-versa: heavy manifest, trivial script) | script imports ↔ manifest |
| 7.6 | Code ↔ data ↔ outputs are linked | Scripts reference input files not in the dataset, or produce outputs nothing documents | script bodies ↔ `List_Files_in_Dataset` |
| 7.7 | Determinism captured where it matters | Stochastic simulation/ML with no random seed set or recorded → results not reproducible | script/README |
| 7.8 | Code carries a (software) license | Data license present but code has none — reuse of the code is legally unclear (CodeMeta) | `Get_Dataset_Metadata` / a `LICENSE` file |

Plus (not required): `Dockerfile`/`apptainer` recipe, `Makefile`/`snakemake`/
`nextflow` workflow, `.python-version`/`runtime.txt`. Absence is not a failure
when a manifest + instructions exist.

## 8. Overall reproducibility & curation

Judge holistically, once sections 1–7 are checked.

| # | Criterion | Violation looks like | Evidence |
|---|-----------|----------------------|----------|
| 8.1 | Results reproducible from the record alone (binding Uni Stuttgart standard) | A reader could not repeat the work from what is deposited | sections 1–7 |
| 8.2 | Complete, comprehensible, reproducible — the three DaRUS curation questions | Record reads as an unreviewed dump | holistic |
| 8.3 | License present | No license — reuse legally blocked | `Get_Dataset_Metadata` → license |

## 9. Confidence caveats

Don't present encouraged practice as a mandate.

- **Lower confidence:** FoKUS as EngMeta maintainer, and the exact
  EngMeta→citation field mapping. Don't over-index on mapping specifics.
- **Applicability:** sections 3–4 apply to computational-science/engineering
  data, section 7 only when code ships. Mark non-applicable sections N/A rather
  than failing them.

## 10. Sources

Primary (DaRUS / FoKUS / SimTech / standards):
- DaRUS data publication guide — https://www.izus.uni-stuttgart.de/en/fokus/darus/publication/
- DaRUS / FoKUS overview — https://www.izus.uni-stuttgart.de/en/fokus/darus/
- DaRUS hands-on workshop — https://www.izus.uni-stuttgart.de/en/fokus/darus/hands-on-workshop/
- FoKUS RDM portal — https://www.izus.uni-stuttgart.de/en/fokus/rdmportal/
- SimTech Research Data & Software Management — https://www.simtech.uni-stuttgart.de/exc/research-data-management/
- EngMeta metadata block config (darus-508) — https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi:10.18419/darus-508
- EngMeta paper (arXiv 2005.01637) — https://arxiv.org/abs/2005.01637
- EngMeta (Springer chapter) — https://link.springer.com/chapter/10.1007/978-3-030-14401-2_12
- DataCite Metadata Schema 4.5 — https://datacite-metadata-schema.readthedocs.io/en/4.5/properties/overview/
- FAIR principles (Wilkinson et al. 2016) — https://www.nature.com/articles/sdata201618
- Dataverse data-quality guide — https://dataverse.org/book/data-quality
- Dataverse dataset-management guide — https://guides.dataverse.org/en/latest/user/dataset-management.html
- Cornell README best practice — https://data.research.cornell.edu/data-management/sharing/readme/

Secondary:
- Datenbank-Spektrum 2024 (DaRUS/Dataverse overview) — https://link.springer.com/article/10.1007/s13222-024-00475-4
- NFDI4Chem FAIR knowledge base — https://knowledgebase.nfdi4chem.de/knowledge_base/docs/fair/
