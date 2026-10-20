# Library data preparation

This directory contains the tools that convert the Digital Library Collection's
Excel catalogue and document files into the JSON files consumed by the website.
The normal entry point is `scripts/build-jcudlc-files.sh`, which runs the
Python scripts in the required order. `scripts/create-website-datafile.sh`
invokes the same pipeline. Run commands from `data-prep` unless noted otherwise.

## What the pipeline does

The pipeline:

1. Reads the configured worksheet from an Excel workbook.
2. Uses four control rows in the workbook to decide which columns are retained,
   searchable, displayed, filterable, or contain multiple values.
3. Writes an intermediate cleaned CSV and four configuration CSV files.
4. Optionally copies active, open-access documents with `--with-documents` into the output directory and normalises
   spaces and `/` characters in their filenames to underscores.
5. Removes inactive records, changes records with invalid access or missing
   access files/URLs to `Contact us`, generates URLs and icons, and writes the
   website's library index. Open records prefer a matching output document
   and otherwise use the spreadsheet URL.
6. Merges static frontend settings with generated workbook settings to create
   the display configuration used by the website.

The generated website files are:

- `outputs/jcudlc-data.json` — the processed catalogue records.
- `outputs/jcudlc-config.json` — static frontend settings plus generated filter,
  search and quiet-field settings.
- `outputs/documents/` — copied open-access documents.

Intermediate CSV files are also written to `outputs/` for inspection.

## Requirements

- Bash (the wrapper script is a Bash script).
- Python 3.11 or newer, with virtual environment support.
- An `.xlsx` workbook with the structure described below.
- Source documents when copying local open-access files.
- The static frontend settings file configured in YAML.

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
bash scripts/build-jcudlc-files.sh --with-documents
```

## Directory layout

The default layout is:

```text
data-prep/
├── inputs/
│   └── jcudlc-config-static.json
├── logs/
├── outputs/
│   └── documents/
├── scripts/
└── tests/
```

The default workbook and source documents are in the sibling `../examples/`
directory. You can configure other input locations in YAML or pass them in as
command line arguments to the `build-jcudlc-files.sh` script.

The workbook, document source, output, and log paths are configured under
`runtime` in `scripts/library-config.yml`:

```yaml
runtime:
  excel_file: ../examples/library-index.xlsx
  documents_dir: ../examples/documents
  output_dir: outputs
  log_dir: logs
  static_config_file: inputs/jcudlc-config-static.json
```

Relative paths are resolved from the directory where the pipeline is run. The
wrapper and individual Python scripts use these same defaults.

The script creates `logs/`, `outputs/`, and `outputs/documents/` if necessary.
Create the source documents directory yourself and place the documents there.
When enabled with `--with-documents`, the document-copying stage stops with an error if it finds no source
files.

## Prepare the workbook

The default workbook is `../examples/library-index.xlsx`. Its layout is controlled by
`scripts/library-config.yml`; by default the worksheet must be named **`MAIN`**,
matching the example workbook, and use these rows:

| Excel row | Purpose                                            | Accepted markers                    |
| --------- | -------------------------------------------------- | ----------------------------------- |
| 2         | Retain the column and optionally make it a filter  | `Filter_yes`, `Filter_no`           |
| 3         | Include the column in text search                  | `Search_yes`, `Search_no`           |
| 4         | Include the column in the published JSON           | `FullDisplay_yes`, `FullDisplay_no` |
| 5         | Treat semicolon-separated cells as multiple values | `MultiOption_yes`, `MultiOption_no` |
| 6         | Column headings                                    | See the required headings below     |
| 7 onward  | Catalogue records                                  | One record per row                  |

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

| Column          | Value                  | Behaviour                                                         |
| --------------- | ---------------------- | ----------------------------------------------------------------- |
| `Portal_Status` | `Active`               | Include the record. Other values are excluded.                    |
| `Access`        | `Open`                 | Prefer a matching output document; otherwise use `Published_URL`. |
| `Access`        | `Access via publisher` | Use `Published_URL` as the record URL.                            |
| `Access`        | `Contact us`           | Use the configured contact/library behaviour.                     |

For an `Open` record with a local document, `PDF_file_name` must match a file
below the document source directory (`../examples/documents/` by default).
Files may be organised in subdirectories. Run with `--with-documents` to copy
eligible files into `outputs/documents/`. During copying, spaces and `/`
characters in output filenames are replaced with `_`. Index generation also
normalises filenames and updates the intermediate CSV, even when copying is
skipped.

A file present only in the source directory does not satisfy the index's
local-file check. Validation uses the selected output directory's `documents/`
subfolder. If no matching output file exists, an `Open` record can instead use
its `Published_URL`, including when the filename is blank.

Source document basenames must be unique across all subdirectories. They must
also remain unique after filename normalisation (for example, `report one.pdf`
and `report_one.pdf` would collide in the flat output directory).

An `Access via publisher` record should contain a valid `Published_URL`.
If an active record has an invalid `Access` value, an `Open` record has no
matching copied file or spreadsheet URL, or an `Access via publisher` record has no URL, the
record remains in the JSON with `Access` changed to `Contact us`. The index
script logs a warning with the record ID and the problem to fix in the next
spreadsheet update. The workbook is unchanged. Access corrections apply to the final JSON; the
intermediate CSV retains source access values but uses normalised filenames.

These access/status values, generated URL prefixes and icons can be changed
in `scripts/library-config.yml`. Browser URLs are separate from local paths.
Include any deployment base path needed by the website in download and contact
URLs; the current frontend opens catalogue URLs directly.

### Placeholder cleanup

Configure exact, case-sensitive missing-value markers in
`scripts/library-config.yml`:

```yaml
excel:
  empty_cell_markers: ["NA", "nan", "NaN", "N/A", "n/a", "NULL"]
```

Strings are trimmed before matching. Matching cells become empty text, as do
actual missing values. The markers apply across the worksheet.

Set `empty_cell_markers: []` to preserve text such as `NA`, `N/A` and `NULL`.
Otherwise, list the exact text values that should be replaced with blanks.
Pandas' implicit NA-string conversion is disabled so values omitted from this
list are preserved.

### Frontend settings

Edit the tracked `inputs/jcudlc-config-static.json` for colours, titles, fonts,
aliases, data URL, hidden values, maximum result count, icon tooltip, support
text and other frontend preferences. The file must contain a JSON object.
Its defaults come from this repository's `front-end` example, with `Access` as
the tooltip label. The path is configured by `runtime.static_config_file`.

Generated `noFilter` and `hideFromSearch` override those keys in static settings.
`quietFields` combines explicitly configured quiet fields with generated URL/icon
fields. Aliases are included alongside original field names in these lists.
`FullDisplay_yes` and `FullDisplay_no` determine whether fields are included in
the published JSON. They do not control which public fields appear under
“Additional details”; use `quietFields` for that.

The pipeline generates `jcudlc-config.json` directly. It no longer generates
`query-config.json` or `library-config.json`.

## Run the pipeline

For a first run or when adding source documents, run from `data-prep`:

```bash
bash scripts/build-jcudlc-files.sh --with-documents
```

For metadata/configuration updates using documents already in the output folder:

```bash
bash scripts/build-jcudlc-files.sh
```

Document copying is skipped by default. To copy from a different source:

```bash
bash scripts/build-jcudlc-files.sh --with-documents \
  --documents-dir "/path/to/primary library document storage"
```

`scripts/create-website-datafile.sh` supports the same options and invokes the
shared build pipeline.

The repository currently stores the wrapper without its executable bit. If you
prefer to invoke it directly, first run:

```bash
chmod +x scripts/build-jcudlc-files.sh
./scripts/build-jcudlc-files.sh
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
website's expected data location as required by the website build. The pipeline does not publish
results automatically. With the supplied frontend, `jcudlc-config.json` is
fetched relative to the catalogue page; the data location is set by `dataUrl`.
Copy documents to the location matching `website.urls.download_prefix`, then
check download/contact links and filtering/search in a website preview.

### Build script usage statement

```
Usage: ./scripts/build-jcudlc-files.sh [--excel-file FILE] [--documents-dir DIR] [--output-dir DIR] [--log-dir DIR] [--with-documents]
  --with-documents  Run get-library-docs.py (skipped by default).
```

### Sample output from build script

```
$ bash ./scripts/build-jcudlc-files.sh
Script started at: 2026-10-09 12:35:58 AEST
Removing any previous /Users/jc350584/github/jcudlc/data-prep/logs/*.log files
Removing any previous /Users/jc350584/github/jcudlc/data-prep/outputs *.csv and *.json files
Using Python virtual environment /Users/jc350584/github/jcudlc/data-prep/scripts/.venv
Running parse-excel-file.py ...
Skipping get-library-docs.py (use --with-documents to run it).
Running create-library-index.py ...
Running create-library-config.py ...
SUCCESS | No errors but you should still check the log files for warnings.
--- Info entries in /Users/jc350584/github/jcudlc/data-prep/logs/create-library-index.log ---
2026-10-09 12:36:03 [info     ] Loading csv file from /Users/jc350584/github/jcudlc/data-prep/outputs/library-index.csv.
2026-10-09 12:36:03 [info     ] Initial # rows loaded: 18
2026-10-09 12:36:03 [info     ] Extracted only the Active records to process
2026-10-09 12:36:03 [info     ] Number of docs dropped due to Status not set to Active is 3
2026-10-09 12:36:03 [info     ] Number of Active records kept: 15
2026-10-09 12:36:03 [info     ] Number of invalid access values changed to Contact us: 0
2026-10-09 12:36:03 [info     ] Number of Open records without a matching file or URL changed to Contact us: 2
2026-10-09 12:36:03 [info     ] Number of Access via publisher records without a publisher URL changed to Contact us: 1
2026-10-09 12:36:03 [info     ] The multi-option fields for libary are: ['Species_Group', 'Habitat', 'Keywords']
2026-10-09 12:36:03 [info     ] Dropped ['Notes_Internal'] columns
2026-10-09 12:36:03 [info     ] Creating library_index for website, /Users/jc350584/github/jcudlc/data-prep/outputs/jcudlc-data.json
2026-10-09 12:36:03 [info     ] Documents in library, final count: 15
2026-10-09 12:36:03 [info     ] Wrote JSON file to /Users/jc350584/github/jcudlc/data-prep/outputs/jcudlc-data.json
2026-10-09 12:36:03 [info     ] Library index file creation is complete
--- Warnings in /Users/jc350584/github/jcudlc/data-prep/logs/create-library-index.log ---
2026-10-09 12:36:03 [warning  ] ID NQ-016 | PDF_file_name 'northern_bettong_woodland_survey_missing.pdf' has no matching file in /Users/jc350584/github/jcudlc/data-prep/outputs/documents and Published_URL is blank for Open access; changed Access to 'Contact us'. Correct the filename, add the PDF, or provide a URL in the next update.
2026-10-09 12:36:03 [warning  ] ID NQ-017 | PDF_file_name is blank and Published_URL is blank for Open access; changed Access to 'Contact us'. Correct the filename, add the PDF, or provide a URL in the next update.
2026-10-09 12:36:03 [warning  ] ID NQ-018 | Published_URL is blank for Access via publisher record; changed Access to 'Contact us'. Add the publisher URL in the next spreadsheet update.
--- Warnings in /Users/jc350584/github/jcudlc/data-prep/logs/create-library-config.log ---
(no warnings found)
If all good then you are ready to build the website.
Script finished at: 2026-10-09 12:36:03 AEST with exit code 0
```

## Use non-default paths

The wrapper accepts command-line overrides for the configured workbook,
document, output, and log paths:

```bash
bash scripts/build-jcudlc-files.sh --with-documents \
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
bash scripts/build-jcudlc-files.sh --with-documents \
  --excel-file ../examples/library-index.xlsx \
  --documents-dir ../examples/documents
```

Run `bash scripts/build-jcudlc-files.sh --help` to see the available
options.

## What else is needed?

Nothing else is required to generate the files locally once Python, the Python
packages, a correctly structured workbook, static frontend settings and any
needed source documents are in
place. For a complete website publishing workflow, account for these additional
operational steps:

- The pipeline does not copy its results into the Jekyll site or publish them.
  Add a deliberate copy/build/deploy step after reviewing the outputs.
- The pipeline clears old top-level CSV and JSON outputs, but not
  `outputs/documents/`. Remove documents that are no longer in the catalogue so
  stale files are not deployed.
- `inputs/`, `outputs/`, and `logs/` are intentionally ignored by Git apart from
  their `.gitkeep` files and the tracked `inputs/jcudlc-config-static.json`.
  Store the authoritative workbook and documents in an appropriate managed location and back them up separately.
- Treat warnings as data-quality failures to investigate: a zero exit code does
  not guarantee that every spreadsheet record or document was included.

## Script reference

| Script                       | Role                                                                                                                                                                                                                                          |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `build-jcudlc-files.sh`      | Validates paths, clears prior CSV/JSON/log outputs, uses the project virtual environment, optionally copies documents, and prints info/warning summaries.                                                                                     |
| `create-website-datafile.sh` | Invokes the shared build pipeline with the same arguments.                                                                                                                                                                                    |
| `parse-excel-file.py`        | Reads Excel, normalises configured placeholders, applies control rows, drops records without an ID, validates required columns, and writes the intermediate CSV/configuration CSV files.                                                      |
| `get-library-docs.py`        | Finds source documents recursively, copies active open-access files, and normalises copied filenames. Runs only with `--with-documents` in the wrapper.                                                                                       |
| `create-library-index.py`    | Normalises index filenames, removes inactive records, changes invalid or incomplete access details to `Contact us` with warnings, splits multi-value fields, generates URLs/icons, removes non-public columns, and writes `jcudlc-data.json`. |
| `create-library-config.py`   | Merges static JSON and generated control-row settings into `jcudlc-config.json`.                                                                                                                                                              |
| `confighelper.py`            | Loads and validates `library-config.yml` and resolves runtime paths.                                                                                                                                                                          |
| `libhelper.py`               | Provides shared filename normalisation.                                                                                                                                                                                                       |

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

Check `logs/create-library-index.log` and, when copying was enabled,
`logs/get-library-docs.log`. Confirm that the record is `Active`, its access
value is `Open`, and either a matching normalised file exists in the selected
output directory's `documents/` folder or `Published_URL` is non-blank.
Run with `--with-documents` if the file exists only in the source directory
(`../examples/documents/` by default).

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
Text such as `n/a` becomes empty when listed in `excel.empty_cell_markers`.
Remove it from that list if it should remain literal text.

### The static frontend settings cannot be read

Confirm that `runtime.static_config_file` points to an existing JSON file and
that the file contains a JSON object. The default file extension is `.json`,
not `.yml`. Rerun the pipeline after changing either YAML or static JSON settings.

## Tests

Run the regression tests from `data-prep`:

```bash
scripts/.venv/bin/python -B -m unittest discover -s tests -v
```

The tests cover download selection and fallback, configurable placeholder
cleanup, configuration validation and preservation of literal Excel values.
