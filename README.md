# neuro_ingest

**neuro_ingest** is a system-agnostic ingestion and normalization pipeline for
neurophysiological acquisition data focused promarily on audiological signals like ABR, DPOAE and VEMPs.

Its purpose is to transform raw vendor outputs into a durable, explicit,
and analysis-ready canonical format.

---

## Scope and Philosophy

This project is intentionally limited in scope.

### This project **does**
- ingest raw data from acquisition systems (e.g. TDT, IHS)
- normalize heterogeneous vendor outputs into a canonical table schema
- validate structure and basic integrity
- write durable, language-agnostic storage (Parquet)
- preserve provenance and metadata explicitly

### This project **does not**
- perform signal analysis
- compute thresholds or features
- plot or visualize data
- make scientific assumptions about paradigms
- merge data across acquisition systems

Analysis, visualization, and modeling are expected to happen in **downstream projects**.

---

## Design Principles

1. **Ingest early, integrate late**  
   Data from different systems is normalized independently.
   Integration happens only when scientifically justified.

2. **Schema over filenames**  
   No semantic meaning is inferred from folder structures or file names
   beyond minimal identifiers.

3. **Explicit over implicit**  
   All relevant metadata exists as columns, not encoded in paths.

4. **Long-term stability**  
   Output data is expected to remain readable and meaningful for years.

---

## Canonical Output Format

The pipeline outputs **Parquet files**, one per:

> acquisition system × recording session

Each file contains a single table in long format.

Parquet was chosen because it is:
- columnar and efficient
- language agnostic
- supported by modern data ecosystems

---

## Folder Layout (recommended)

This repository contains **only code**.

Raw and normalized data must live outside the repository, for example:

  raw_data/
    TDT/
    IHS/

  normalized_data/
    TDT/
    IHS/

No raw or normalized data should ever be committed to Git.

---

## Environment

The project uses a dedicated Conda environment defined in `environment.yml`.

To create the environment:

```bash
conda env create -f environment.yml
conda activate neuro-ingest
```

---
## License

To be decided.
---
