# Library data preparation

This directory contains the tools that convert the Digital Library Collection's
Excel catalogue and document files into the JSON files consumed by the website.
The normal entry point is `scripts/create-website-datafile.sh`, which runs the
Python scripts in the required order.

## What the pipeline does

The pipeline:

1. Reads the configured worksheet from an Excel workbook.
2. Uses four control rows in the workbook to decide which columns are retained,
   searchable, displayed, filterable, or contain multiple values.
3. Writes an intermediate cleaned CSV and four configuration CSV files.
4. Copies active, open-access documents into the output directory and normalises
   spaces and `/` characters in their filenames to underscores.
5. Removes inactive records, changes records with invalid access or missing
   access files/URLs to `Contact us`, generates URLs and icons, and writes the
   website's library index and query configuration.
6. Generates the display configuration used by the website.

The generated website files are:

- `outputs/jcudlc-data.json` — the processed catalogue records.
- `outputs/query-config.json` — search fields, filter aggregations, and sorting
  presets.
- `outputs/library-config.json` — display, filtering, and field behaviour.
- `outputs/documents/` — copied open-access documents.

Intermediate CSV files are also written to `outputs/` for inspection.

## Requirements

- Bash (the wrapper script is a Bash script).
- Python 3.11 or newer, with virtual environment support. The pinned NumPy
  release in `scripts/requirements.txt` requires Python 3.11+.
- An `.xlsx` workbook with the structure described below.
- Source documents for open-access records.

The Python requirements file installs the processing libraries, including
`pandas`, `openpyxl`, `PyYAML`, and `structlog`, plus their pinned
dependencies. The wrapper uses POSIX virtual-environment paths, so run it on
macOS or Linux, or in a Linux environment such as WSL rather than native
Windows Command Prompt or PowerShell.

Run the setup commands from `data-prep`:

```bash
python3 -m venv scripts/.venv
scripts/.venv/bin/python -m pip install -r scripts/requirements.txt
```

The wrapper expects the virtual environment at `scripts/.venv` and invokes its
Python interpreter directly.

For a first run using the included sample data:

```bash
cd data-prep
python3 -m venv scripts/.venv
scripts/.venv/bin/python -m pip install -r scripts/requirements.txt
bash scripts/create-website-datafile.sh \
  --excel-file ../examples/library-index.xlsx \
  --documents-dir ../examples/documents
```

## Directory layout

The default layout is:

```text
data-prep/
├── inputs/
│   ├── library-index.xlsx
│   └── documents/
│       └── source documents may be in subdirectories
├── logs/
├── outputs/
│   └── documents/
└── scripts/
```

The workbook, document source, output, and log paths are configured under
`runtime` in `scripts/library-config.yml`:

```yaml
runtime:
  excel_file: inputs/library-index.xlsx
  documents_dir: inputs/documents
  output_dir: outputs
  log_dir: logs
```

Relative paths are resolved from the directory where the pipeline is run. The
wrapper and individual Python scripts use these same defaults.

The script creates `logs/`, `outputs/`, and `outputs/documents/` if necessary.
Create the source documents directory yourself and place the documents there.
The document-copying stage currently stops with an error if it finds no source
files.

## Prepare the workbook

The default workbook is `inputs/library-index.xlsx`. Its layout is controlled by
`scripts/library-config.yml`; by default the worksheet must be named **`MAIN`**,
matching the example workbook, and use these rows:

| Excel row | Purpose | Accepted markers |
| --- | --- | --- |
| 2 | Retain the column and optionally make it a filter | `Filter_yes`, `Filter_no` |
| 3 | Include the column in text search | `Search_yes`, `Search_no` |
| 4 | Include the column in the published JSON | `FullDisplay_yes`, `FullDisplay_no` |
| 5 | Treat semicolon-separated cells as multiple values | `MultiOption_yes`, `MultiOption_no` |
| 6 | Column headings | See the required headings below |
| 7 onward | Catalogue records | One record per row |

Use the marker spelling and capitalisation shown above. Leading and trailing
whitespace is removed, but the later marker-to-Boolean conversion is
case-sensitive.

Every column that should enter the pipeline must have either `Filter_yes` or
`Filter_no` in row 2. A blank or unrecognised value causes that entire column to
be dropped when at least one valid filter marker exists elsewhere in the row.
`Filter_no` retains the column; it only prevents the column from becoming a
website filter. Do not leave the entire filter row blank.

For every retained column, also provide the appropriate `_yes` or `_no` marker
in rows 3–5. Blank configuration cells are not a supported substitute for the
`_no` markers and can cause later stages to fail while reading the generated
configuration CSV files.

The configured required headings are:

- `ID`
- `Title`
- `Year`
- `Access`
- `PDF_file_name`
- `Published_URL`
- `Portal_Status`

The exact names can be changed under `columns` in `scripts/library-config.yml`.
The generated `URL` and `Icon` fields must not be added to the workbook.

For fields marked `MultiOption_yes`, separate values with semicolons, for
example:

```text
Coastal; Wetlands; Estuarine
```

### Access and status values

The default accepted values are case-sensitive during final processing:

| Column | Value | Behaviour |
| --- | --- | --- |
| `Portal_Status` | `Active` | Include the record. Other values are excluded. |
| `Access` | `Open` | Copy the named file and generate a download URL. |
| `Access` | `Access via publisher` | Use `Published_URL` as the record URL. |
| `Access` | `Contact us` | Use the configured contact/library behaviour. |

An `Open` record must name an existing source file in `PDF_file_name`. The
filename must match a file below the document source directory
(`inputs/documents/` by default). Files may be organised in subdirectories.
During copying, spaces and `/` characters in output filenames are replaced with
`_`, and the CSV is updated to use the normalised name.

Source document basenames must be unique across all subdirectories. They must
also remain unique after filename normalisation (for example, `report one.pdf`
and `report_one.pdf` would collide in the flat output directory).

An `Access via publisher` record should contain a valid `Published_URL`.
If an active record has an invalid `Access` value, an `Open` record has no
matching copied file, or an `Access via publisher` record has no URL, the
record remains in the JSON with `Access` changed to `Contact us`. The index
script logs a warning with the record ID and the problem to fix in the next
spreadsheet update. The workbook and intermediate CSV retain their original
values.

These values, the generated URL prefixes, icons, and query
sorting presets can all be changed in `scripts/library-config.yml`.

Some website-interface defaults are currently constants near the top of
`scripts/create-library-config.py`, rather than YAML settings. Change that file
if the generated configuration needs a different data URL, hidden-value list,
quiet-field label, maximum result count, icon tooltip, or support text.

## Run the pipeline

From `data-prep`, run:

```bash
bash scripts/create-website-datafile.sh
```

The repository currently stores the wrapper without its executable bit. If you
prefer to invoke it directly, first run:

```bash
chmod +x scripts/create-website-datafile.sh
./scripts/create-website-datafile.sh
```

The wrapper removes existing `logs/*.log` files and `outputs/*.csv` and
`outputs/*.json` files before starting. It does not clear
`outputs/documents/`, so remove obsolete copied documents manually when needed.

When processing finishes, inspect the terminal summary and all files in `logs/`.
A successful exit only means that every stage completed; records and documents
can still have been skipped with warnings.

Useful checks include:

```bash
grep -iE 'warn|error' logs/*.log
ls -lh outputs/*.json
```

After checking the generated JSON and documents, copy or integrate them into the
website's expected data location as required by the website build. The old copy
step in the wrapper is currently commented out, so the script does not publish
the results automatically.

## Use non-default paths

The wrapper accepts command-line overrides for the configured workbook,
document, output, and log paths:

```bash
bash scripts/create-website-datafile.sh \
  --excel-file /path/to/spreadsheets/catalogue.xlsx \
  --documents-dir /path/to/source-documents \
  --output-dir /path/to/output \
  --log-dir /path/to/logs
```

`--excel-file` directly identifies the workbook; there is no separate input
directory setting. Relative override paths are resolved from the directory in
which the command is run. Copied documents are written to a `documents/`
directory below the selected output directory.

For example, run the repository's sample workbook and documents from
`data-prep` with:

```bash
bash scripts/create-website-datafile.sh \
  --excel-file ../examples/library-index.xlsx \
  --documents-dir ../examples/documents
```

Run `bash scripts/create-website-datafile.sh --help` to see the available
options.

## What else is needed?

Nothing else is required to generate the files locally once Python, the Python
packages, a correctly structured workbook, and the source documents are in
place. For a complete website publishing workflow, account for these additional
operational steps:

- The pipeline does not copy its results into the Jekyll site or publish them.
  Add a deliberate copy/build/deploy step after reviewing the outputs.
- The pipeline clears old top-level CSV and JSON outputs, but not
  `outputs/documents/`. Remove documents that are no longer in the catalogue so
  stale files are not deployed.
- `inputs/`, `outputs/`, and `logs/` are intentionally ignored by Git apart from
  their `.gitkeep` files. Store the authoritative workbook and documents in an
  appropriate managed location and back them up separately.
- Treat warnings as data-quality failures to investigate: a zero exit code does
  not guarantee that every spreadsheet record or document was included.

## Script reference

| Script | Role |
| --- | --- |
| `create-website-datafile.sh` | Validates paths, clears prior CSV/JSON/log outputs, uses the project virtual environment, and runs the pipeline. |
| `parse-excel-file.py` | Reads Excel, applies control rows, drops records without an ID, validates required columns, and writes the intermediate CSV/configuration CSV files. |
| `get-library-docs.py` | Finds source documents recursively, copies active open-access files, normalises filenames, and updates the intermediate CSV. |
| `create-library-index.py` | Removes inactive records, changes invalid or incomplete access details to `Contact us` with warnings, splits multi-value fields, generates URLs/icons, removes non-public columns, and writes `jcudlc-data.json` and `query-config.json`. |
| `create-library-config.py` | Converts the control-row CSV files into `library-config.json`. |
| `confighelper.py` | Loads and validates `library-config.yml` and resolves runtime paths. |
| `libhelper.py` | Provides shared filename normalisation. |

Although the Python scripts can be run individually, later stages depend on
files produced by earlier stages. Use the wrapper for routine runs.

## Troubleshooting

### The spreadsheet cannot be read

Confirm that the workbook path is correct, the configured worksheet exists, and
the workbook is a valid `.xlsx` file. The default worksheet name is `MAIN`.

### A configured column is reported missing

Confirm that its row 6 heading exactly matches `scripts/library-config.yml` and
that its row 2 cell contains `Filter_yes` or `Filter_no`. An unmarked column is
dropped before required-column validation.

### An open-access record appears as `Contact us`

Check `logs/get-library-docs.log` and `logs/create-library-index.log`. Confirm
that the record is `Active`, its access value is `Open`, and its
`PDF_file_name` exactly matches a source filename below the selected document
source directory (`inputs/documents/` by default).

### A record is unexpectedly omitted

Check that `Portal_Status` is `Active` and the record has an ID. Active records
with invalid access or missing access-specific information remain in the JSON
as `Contact us`; check `logs/create-library-index.log` for the warning.

### A column is missing from the final JSON

It must be retained with a valid row 2 filter marker and set to
`FullDisplay_yes` in row 4. `FullDisplay_no` removes the field from the published
index.

### A filter or multi-value field behaves incorrectly

Check the exact control-row marker spelling. For multi-value fields, use `;` as
the separator. Empty or whitespace-only spreadsheet cells remain empty in the
CSV and JSON. Empty multi-value cells become empty arrays in the JSON.
Literal text such as `n/a` remains text and is not treated as an empty cell.
