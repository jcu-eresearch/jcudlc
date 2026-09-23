"""Load and validate configuration for the library data scripts."""

from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "PyYAML is required to read library-config.yml. "
        "Install dependencies with: pip install -r requirements.txt"
    ) from exc


CONFIG_FILE = Path(__file__).with_name("library-config.yml")


@dataclass(frozen=True)
class SheetValues:
    sheetname: str
    filterRowIdx: int
    searchRowIdx: int
    fullDisplayRowIdx: int
    multiOptionRowIdx: int
    colHeaderRowIdx: int


@dataclass(frozen=True)
class Docs:
    file_pattern: str
    src_path: Path
    dest_path: Path


@dataclass(frozen=True)
class Labels:
    id: str
    title: str
    year: str
    access: str
    filename: str
    publishedURL: str
    displayURL: str
    displayIcon: str
    status: str


@dataclass(frozen=True)
class AccessValues:
    open: str
    physical_library: str
    publisher: str


@dataclass(frozen=True)
class StatusValues:
    active: str
    deleted: str


@dataclass(frozen=True)
class Icons:
    webpage: str
    download: str
    support: str
    library: str


@dataclass(frozen=True)
class URLs:
    physical_library: str
    contact_us: str
    download: str


@dataclass(frozen=True)
class RuntimeDefaults:
    excel_file: str
    documents_dir: str
    output_dir: str
    log_dir: str


@dataclass(frozen=True)
class LocalPaths:
    output_dir: Path
    log_dir: Path
    doc_display_config: Path
    search_config: Path
    filter_config: Path
    query_config: Path
    multi_option_config: Path
    excel_file: Path
    libindex_csv: Path
    libindex_json: Path
    library_config_json: Path


def _require(mapping, path):
    current = mapping
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            raise ValueError(f"Missing required configuration value: {path}")
        current = current[key]
    return current


def _optional(mapping, path, default):
    try:
        return _require(mapping, path)
    except ValueError:
        return default


def _resolve_runtime_path(path_value):
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (Path.cwd() / path).resolve()


def add_runtime_path_arguments(parser):
    parser.add_argument(
        "--documents-dir",
        default=runtime_defaults.documents_dir,
        help=(
            "input directory containing source documents "
            f"(default: {runtime_defaults.documents_dir})"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=runtime_defaults.output_dir,
        help=(
            "output directory for generated CSV and JSON files "
            f"(default: {runtime_defaults.output_dir})"
        ),
    )
    parser.add_argument(
        "--log-dir",
        default=runtime_defaults.log_dir,
        help=f"log directory used by wrapper scripts (default: {runtime_defaults.log_dir})",
    )
    parser.add_argument(
        "--excel-file",
        default=runtime_defaults.excel_file,
        help=(
            "path to the Excel workbook "
            f"(default: {runtime_defaults.excel_file})"
        ),
    )


def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_FILE}")

    with CONFIG_FILE.open(encoding="utf-8") as config_file:
        loaded_config = yaml.safe_load(config_file)

    if not isinstance(loaded_config, dict):
        raise ValueError(f"Configuration file is empty or invalid: {CONFIG_FILE}")

    return loaded_config


def get_sheet_config(config):
    rows = _require(config, "excel.rows")

    def spreadsheet_row_to_index(row_path):
        row_number = int(_require(rows, row_path))
        if row_number < 1:
            raise ValueError(f"excel.rows.{row_path} must be a spreadsheet row number >= 1")
        return row_number - 1

    return SheetValues(
        sheetname=_require(config, "excel.sheet"),
        filterRowIdx=spreadsheet_row_to_index("filter"),
        searchRowIdx=spreadsheet_row_to_index("search"),
        fullDisplayRowIdx=spreadsheet_row_to_index("full_display"),
        multiOptionRowIdx=spreadsheet_row_to_index("multi_option"),
        colHeaderRowIdx=spreadsheet_row_to_index("column_headers"),
    )


def get_docs_config(config, documents_dir=None, output_dir=None):
    defaults = get_runtime_defaults(config)
    documents_dir = _resolve_runtime_path(
        defaults.documents_dir if documents_dir is None else documents_dir
    )
    output_dir = _resolve_runtime_path(
        defaults.output_dir if output_dir is None else output_dir
    )
    return Docs(
        file_pattern=_require(config, "documents.file_pattern"),
        src_path=documents_dir,
        dest_path=output_dir / "documents",
    )


def get_label_config(config):
    return Labels(
        id=_require(config, "columns.id"),
        title=_optional(config, "columns.title", "Title"),
        year=_optional(config, "columns.year", "Year"),
        access=_require(config, "columns.access"),
        filename=_require(config, "columns.filename"),
        publishedURL=_require(config, "columns.published_url"),
        displayURL=_require(config, "columns.generated.display_url"),
        displayIcon=_require(config, "columns.generated.display_icon"),
        status=_require(config, "columns.status"),
    )


def get_access_values(config):
    return AccessValues(
        open=_require(config, "values.access.open"),
        physical_library=_require(config, "values.access.physical_library"),
        publisher=_require(config, "values.access.publisher"),
    )


def get_status_values(config):
    return StatusValues(
        active=_require(config, "values.status.active"),
        deleted=_require(config, "values.status.deleted"),
    )


def get_icons(config):
    return Icons(
        webpage=_require(config, "website.icons.webpage"),
        download=_require(config, "website.icons.download"),
        support=_require(config, "website.icons.support"),
        library=_require(config, "website.icons.library"),
    )


def get_urls(config):
    return URLs(
        physical_library=_require(config, "website.urls.physical_library"),
        contact_us=_require(config, "website.urls.contact_us"),
        download=_require(config, "website.urls.download_prefix"),
    )


def get_runtime_defaults(config):
    values = {
        "excel_file": _require(config, "runtime.excel_file"),
        "documents_dir": _require(config, "runtime.documents_dir"),
        "output_dir": _require(config, "runtime.output_dir"),
        "log_dir": _require(config, "runtime.log_dir"),
    }
    for name, value in values.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"runtime.{name} must be a non-empty string")
        if "\n" in value or "\t" in value:
            raise ValueError(f"runtime.{name} must not contain tabs or newlines")
    return RuntimeDefaults(**values)


def get_query_config(config):
    query_sortings = {}
    sortings = _optional(config, "query.sortings", {})
    if sortings is None:
        return query_sortings
    if not isinstance(sortings, dict):
        raise ValueError("query.sortings must be a mapping of sort preset names")

    for name, spec in sortings.items():
        if not isinstance(spec, dict):
            raise ValueError(f"query.sortings.{name} must be a mapping")

        fields = spec.get("fields", spec.get("field", []))
        order = spec.get("order", [])
        if isinstance(fields, str):
            fields = [fields]
        if isinstance(order, str):
            order = [order]
        if not fields:
            raise ValueError(f"query.sortings.{name}.fields must contain at least one field")
        if order and len(order) != len(fields):
            raise ValueError(
                f"query.sortings.{name}.order must have the same number of values as fields"
            )

        query_sortings[name] = {"field": fields, "order": order}

    return query_sortings


def get_internal_files(
    config,
    output_dir=None,
    log_dir=None,
    excel_file=None,
):
    defaults = get_runtime_defaults(config)
    output_dir = _resolve_runtime_path(
        defaults.output_dir if output_dir is None else output_dir
    )
    log_dir = _resolve_runtime_path(
        defaults.log_dir if log_dir is None else log_dir
    )
    excel_file = _resolve_runtime_path(
        defaults.excel_file if excel_file is None else excel_file
    )
    return LocalPaths(
        output_dir=output_dir,
        log_dir=log_dir,
        doc_display_config=output_dir / "doc-display-config.csv",
        search_config=output_dir / "search-config.csv",
        filter_config=output_dir / "filter-config.csv",
        query_config=output_dir / "query-config.json",
        multi_option_config=output_dir / "multi-option-config.csv",
        excel_file=excel_file,
        libindex_csv=output_dir / "library-index.csv",
        libindex_json=output_dir / "jcudlc-data.json",
        library_config_json=output_dir / "library-config.json",
    )


def configure_runtime_paths(args):
    global docs, files

    docs = get_docs_config(config, args.documents_dir, args.output_dir)
    files = get_internal_files(
        config,
        args.output_dir,
        args.log_dir,
        args.excel_file,
    )
    return files, docs


config = load_config()
runtime_defaults = get_runtime_defaults(config)
sheet_config = get_sheet_config(config)
docs = get_docs_config(config)
label = get_label_config(config)
access_types = get_access_values(config)
status_types = get_status_values(config)
icons = get_icons(config)
urls = get_urls(config)
files = get_internal_files(config)
query = get_query_config(config)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--print-runtime-defaults",
        action="store_true",
        help="print tab-separated runtime defaults for the Bash wrapper",
    )
    args = parser.parse_args()
    if args.print_runtime_defaults:
        print(
            "\t".join(
                (
                    str(files.excel_file),
                    str(docs.src_path),
                    str(files.output_dir),
                    str(files.log_dir),
                )
            )
        )
