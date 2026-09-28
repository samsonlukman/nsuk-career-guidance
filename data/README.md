# O*NET data

This project uses occupational information from the official **O*NET 30.3** database published by the O*NET Resource Center (U.S. Department of Labor / Employment and Training Administration).

The database is licensed under [Creative Commons Attribution 4.0 International](https://www.onetcenter.org/license_db.html). Any use of O*NET data in this project, the dissertation, or a demonstration must credit that source.

## Why O*NET 30.3

- It is the current production release on the official O*NET Resource Center site.
- It is downloadable as tab-delimited text files, which is reproducible and does not require a live API key.
- It includes the worker characteristics needed for a student questionnaire: career interests, knowledge, skills, work styles, education/job zone, and work context.

O*NET Web Services was considered and **not** chosen as the runtime source of truth. A versioned local snapshot is more defensible for a final-year project: the same occupations and ratings can be shown to a supervisor later.

## Directory layout

```
data/
  raw/                  Official files, unmodified
    DOWNLOAD_MANIFEST.txt
    db_30_3_text/       Tab-delimited O*NET 30.3 files
  processed/            Application-ready tables/vectors (generated later)
```

Raw files are gitignored. Re-download them instead of committing the bulk datasets.

## Download

From the repository root:

```bash
python3 scripts/download_onet.py
```

Options:

- `--full-zip` — download the complete official archive `db_30_3_text.zip`
- `--optional` — also fetch task statements and related occupations
- `--timeout 600` — per-file timeout in seconds (increase on a slow connection)

The script writes SHA-256 checksums to `data/raw/DOWNLOAD_MANIFEST.txt`.

Official locations:

- Database: https://www.onetcenter.org/database.html
- Text files: https://www.onetcenter.org/dl_files/database/db_30_3_text/
- Complete zip: https://www.onetcenter.org/dl_files/database/db_30_3_text.zip
- Data dictionary: https://www.onetcenter.org/dictionary/30.3/text/

## Import

From the repository root:

```bash
python3 scripts/ingest_onet.py
```

The ingest pipeline:

1. Reads official text files from `data/raw/db_30_3_text/` (never writes there)
2. Verifies the snapshot is O*NET 30.3 and required files parse
3. Keeps occupations that have complete ratings for the selected KNN domains
4. Applies O*NET flags (`Recommend Suppress`, `Not Relevant`)
5. Normalises using official `Scales Reference.txt` min/max
6. Writes versioned tables to `data/processed/onet_30_3_v1/`

See `data/processed/README.md`. Do not hand-enter occupations.

## Attribution

O*NET® is a trademark of the U.S. Department of Labor, Employment and Training Administration.

This application uses the O*NET 30.3 Database by the U.S. Department of Labor, Employment and Training Administration, used under the CC BY 4.0 license.
