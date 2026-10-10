# Library data preparation

Run commands from `data-prep/`. The pipeline converts the Excel catalogue and
source documents into `jcudlc-data.json` and `jcudlc-config.json` for the frontend.
It does not publish or copy the outputs into a website.

## Setup and defaults

Use Python 3.11 or newer and Bash on macOS, Linux or WSL:

```bash
python3 -m venv scripts/.venv
scripts/.venv/bin/python -m pip install -r scripts/requirements.txt
```

Defaults in `scripts/library-config.yml` retain the repository's example inputs:

```yaml
runtime:
  excel_file: ../examples/library-index.xlsx
  documents_dir: ../examples/documents
  output_dir: outputs
  log_dir: logs
  static_config_file: inputs/jcudlc-config-static.json
```

Relative paths are resolved from the current working directory. YAML also
configures worksheet layout, column names, access/status values, file matching,
website URLs and icons. Local paths and browser URLs are separate settings.
Download and contact URLs must include any deployment base path needed by the
website; the frontend opens catalogue URLs directly.

Defaults in `inputs/jcudlc-config-static.yml` relate to the digital library's website page look and behaviour.

## Workbook layout

The default worksheet is `MAIN`. Row numbers refer to the row in the spreadsheet that contains the information:

| Row      | Purpose                        | Markers                             |
| -------- | ------------------------------ | ----------------------------------- |
| 2        | Filtering and retained columns | `Filter_yes`, `Filter_no`           |
| 3        | Search                         | `Search_yes`, `Search_no`           |
| 4        | Public fields                  | `FullDisplay_yes`, `FullDisplay_no` |
| 5        | Multiple values                | `MultiOption_yes`, `MultiOption_no` |
| 6        | Column headings                | Configured column names             |
| 7 onward | Records                        | One record per row                  |

#### Notes

- **Column headings**: Mandatory source columns are listed in `scripts/library-config.yml` and the default mapping to spreadsheet column names is
  `ID`, `Title`, `Year`, `Access`,
  `PDF_file_name`, `Published_URL` and `Portal_Status`. `URL` and `Icon`.
- **Multi-option values are separated by semicolons**.
- Rows with blank IDs are removed from the final dataset;
  only records with status `Active` are published.
- Non-public columns are removed
  after access validation and URL generation.

### Placeholder cleanup

Configure exact, case-sensitive missing-value markers in YAML:

```yaml
excel:
  empty_cell_markers: ["NA", "nan", "NaN", "N/A", "n/a", "NULL"]
```

Strings are trimmed before matching. Matching cells become empty text, as do
actual missing values. The markers apply across the worksheet.

Set `empty_cell_markers: []` to preserve text such as NA, N/A and NULL.
Otherwise, list the exact text values that should be replaced with blanks.

Technical note: Pandas' implicit
NA-string conversion is disabled so values omitted from this list are preserved.

## Generate the catalogue

For a first run or when adding documents:

```bash
bash scripts/build-jcudlc-files.sh --with-documents
```

Or, if the documents are somewhere other than the configured documents_dir:

```bash
bash scripts/build-jcudlc-files.sh --with-documents --documents-dir <path to primary library document storage>
```

For metadata/configuration updates with documents already in `outputs/documents/`:

```bash
bash scripts/build-jcudlc-files.sh
```

`scripts/create-website-datafile.sh` invokes the same pipeline. Both accept
`--excel-file`, `--documents-dir`, `--output-dir`, `--log-dir` and
`--with-documents`. The wrapper invokes the virtual environment's interpreter
without activation, creates output/log directories, and stops on stage failure.

Stages run in order:

1. Parse the workbook into `library-index.csv` and four control-row CSV files.
2. Copy eligible active open-access documents, only with `--with-documents`.
3. Normalise filenames, validate access, split multi-option values, generate
   URLs/icons, remove private columns and write `jcudlc-data.json`.
4. Merge static settings and generated filter/search settings into
   `jcudlc-config.json`.

Filenames replace spaces and `/` with underscores even when copying is skipped.

### Access value handling

| Default access value   | Behaviour                                                                                  |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| `Open`                 | Prefer a matching output document; otherwise use the value from the `Published_URL` column |
| `Contact us`           | Use the configured physical-library URL                                                    |
| `Access via publisher` | Use the value from the `Published_URL` column                                              |

Access values not listed in `library-config.yml`, open records with neither an output document nor a URL,
and publisher records with blank URLs are changed to `Contact us`, with warnings written to the log file.
A document present only in the input folder does not satisfy validation; run
with `--with-documents` to copy it first. The spreadsheet itself is unchanged.

The wrapper clears previous top-level CSV/JSON outputs and logs. Copied documents
are retained, including obsolete files. Review the info/warning summary and logs
before using the generated files. Successful exit does not imply zero warnings.

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

## Frontend settings

Edit the tracked `inputs/jcudlc-config-static.json` for colours, titles, fonts,
aliases, support text and other frontend preferences. It contains configurable settings from the
`frontend` section of this repo and forms part of the final `jcudlc-config.json` file generated
by these scripts for use with the digital libary javascript.

Generated `noFilter` and `hideFromSearch` override those keys in static settings.
`quietFields` combines explicitly configured quiet fields with generated URL/icon
fields. Aliases are included alongside original field names in these lists.
`FullDisplay_yes` or `FullDisplay_no` workbook flags control whether fields are published to the document details view; they do not
control which public fields appear under “Additional details”; that is what the `quietFields` does.

## Review and use outputs

Copy reviewed `outputs/jcudlc-data.json` and `outputs/jcudlc-config.json` into the appropriate folder in your
site's folder structure, this may be the same folder as the your library catalogue HTML but it will depend on
what framework you are using to build your website.
Copy `outputs/documents/` to the location matching `website.urls.download_prefix`.
Check download/contact links and filtering/search
in a website preview before publishing. Review obsolete documents separately.

## Tests

```bash
scripts/.venv/bin/python -B -m unittest discover -s tests -v
```
