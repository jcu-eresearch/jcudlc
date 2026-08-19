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
SCRIPT_DIR = Path(__file__).resolve().parent


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
class General:
    missing_value_token: str


@dataclass(frozen=True)
class LocalPaths:
    doc_display_config: Path
    search_config: Path
    filter_config: Path
    query_config: Path
    multi_option_config: Path
    excel_file: Path
    libindex_csv: Path
    libindex_json: Path


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


def _resolve_path(path_value):
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (SCRIPT_DIR / path).resolve()


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
    return SheetValues(
        sheetname=_require(config, "excel.sheet"),
        filterRowIdx=int(_require(rows, "filter")),
        searchRowIdx=int(_require(rows, "search")),
        fullDisplayRowIdx=int(_require(rows, "full_display")),
        multiOptionRowIdx=int(_require(rows, "multi_option")),
        colHeaderRowIdx=int(_require(rows, "column_headers")),
    )


def get_docs_config(config):
    return Docs(
        file_pattern=_require(config, "documents.file_pattern"),
        src_path=_resolve_path(_require(config, "documents.source_path")),
        dest_path=_resolve_path(_require(config, "documents.destination_path")),
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


def get_general_config(config):
    return General(missing_value_token=_require(config, "general.missing_value_token"))


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


def get_internal_files(config):
    return LocalPaths(
        doc_display_config=_resolve_path("outputs/doc-display-config.csv"),
        search_config=_resolve_path("outputs/search-config.csv"),
        filter_config=_resolve_path("outputs/filter-config.csv"),
        query_config=_resolve_path("outputs/query-config.json"),
        multi_option_config=_resolve_path("outputs/multi-option-config.csv"),
        excel_file=_resolve_path(_require(config, "excel.file")),
        libindex_csv=_resolve_path("outputs/library-index.csv"),
        libindex_json=_resolve_path("outputs/library-index.json"),
    )


config = load_config()
sheet_config = get_sheet_config(config)
docs = get_docs_config(config)
label = get_label_config(config)
access_types = get_access_values(config)
status_types = get_status_values(config)
icons = get_icons(config)
urls = get_urls(config)
files = get_internal_files(config)
general = get_general_config(config)
query = get_query_config(config)
