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
5. Removes inactive or unusable records, generates document URLs and icons, and
   writes the website's library index and query configuration.
6. Generates the display configuration used by the website.

The generated website files are:

- `outputs/library-index.json` — the processed catalogue records.
- `outputs/query-config.json` — search fields, filter aggregations, and sorting
  presets.
- `outputs/library-config.json` — display, filtering, and field behaviour.
- `outputs/documents/` — copied open-access documents.

Intermediate CSV files are also written to `outputs/` for inspection.

## Requirements

- Bash (the wrapper script is a Bash script).
- Python with virtual environment support.
- An `.xlsx` workbook with the structure described below.
- Source documents for open-access records.

Run the setup commands from `data-prep`:

```bash
python3 -m venv scripts/.venv
scripts/.venv/bin/python -m pip install -r scripts/requirements.txt
```

The wrapper expects the virtual environment at `scripts/.venv` and invokes its
Python interpreter directly.

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

The spreadsheet and document source directories are configured independently.
Their defaults are declared near the top of `scripts/create-website-datafile.sh`:

```bash
INPUT_DIR=inputs
DOCUMENTS_DIR=inputs/documents
```

The script creates `logs/`, `outputs/`, and `outputs/documents/` if necessary.
Create the source documents directory yourself and place the documents there.
The document-copying stage currently stops with an error if it finds no source
files.

## Prepare the workbook

The default workbook is `inputs/library-index.xlsx`. Its layout is controlled by
`scripts/library-config.yml`; by default the worksheet must be named `MAIN` and
use these rows:

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

An `Access via publisher` record should contain a valid `Published_URL`.

These values, the generated URL prefixes, icons, missing-value token, and query
sorting presets can all be changed in `scripts/library-config.yml`.

## Run the pipeline

From `data-prep`, run:

```bash
./scripts/create-website-datafile.sh
```

If the script is not executable, use:

```bash
bash scripts/create-website-datafile.sh
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

The wrapper accepts custom input, output, log, and workbook locations:

```bash
./scripts/create-website-datafile.sh \
  --input-dir /path/to/spreadsheets \
  --documents-dir /path/to/source-documents \
  --output-dir /path/to/output \
  --log-dir /path/to/logs \
  --excel-file catalogue.xlsx
```

`--input-dir` controls only the spreadsheet input directory.
`--documents-dir` directly identifies the source document directory; it is not
resolved below `--input-dir`. If `--excel-file` is only a filename, it is
resolved inside `--input-dir`. A relative spreadsheet path containing `/`, or an
absolute path, is used as supplied. Copied documents are written to a
`documents/` directory below the selected output directory.

For example, run the repository's sample workbook and documents from
`data-prep` with:

```bash
./scripts/create-website-datafile.sh \
  --input-dir ../examples \
  --documents-dir ../examples/documents
```

Run `./scripts/create-website-datafile.sh --help` to see the available options.

## Script reference

| Script | Role |
| --- | --- |
| `create-website-datafile.sh` | Validates paths, clears prior CSV/JSON/log outputs, uses the project virtual environment, and runs the pipeline. |
| `parse-excel-file.py` | Reads Excel, applies control rows, drops records without an ID, validates required columns, and writes the intermediate CSV/configuration CSV files. |
| `get-library-docs.py` | Finds source documents recursively, copies active open-access files, normalises filenames, and updates the intermediate CSV. |
| `create-library-index.py` | Filters records, validates access types and open files, splits multi-value fields, generates URLs/icons, removes non-public columns, and writes `library-index.json` and `query-config.json`. |
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

### An open-access record is missing from the JSON

Check `logs/get-library-docs.log` and `logs/create-library-index.log`. Confirm
that the record is `Active`, its access value is `Open`, and its
`PDF_file_name` exactly matches a source filename below the selected document
source directory (`inputs/documents/` by default).

### A record is unexpectedly omitted

Check that `Portal_Status` is `Active`, `Access` is one of the configured values,
and all access-specific information is present. The index-generation log reports
how many records each validation step removes.

### A column is missing from the final JSON

It must be retained with a valid row 2 filter marker and set to
`FullDisplay_yes` in row 4. `FullDisplay_no` removes the field from the published
index.

### A filter or multi-value field behaves incorrectly

Check the exact control-row marker spelling. For multi-value fields, use `;` as
the separator. Empty spreadsheet cells are emitted as the configured missing
value token (`n/a` by default).
