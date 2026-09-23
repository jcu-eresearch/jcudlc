#!/usr/bin/env python3
"""Create library-config.json for the website from generated config CSV files."""

import argparse
import csv
import json
from pathlib import Path

import confighelper as cfg


DEFAULT_DATA_URL = "jcudlc-data.json"
DEFAULT_HIDE_VALUES = [""]
DEFAULT_QUIET_LABEL = "Additional details >"
DEFAULT_QUIET_LABEL_FORMAT = "faded italic center smaller"
DEFAULT_MAX_RESULT_COUNT = 200
DEFAULT_ICON_TOOLTIP = cfg.label.access
DEFAULT_SUPPORT_TEXT = "contact eResearch@jcu.edu.au if problems persist"


def append_missing(values, extra_values):
    combined = list(values)
    for value in extra_values:
        if value not in combined:
            combined.append(value)
    return combined


def read_config_row(path):
    with Path(path).open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        try:
            row = next(reader)
        except StopIteration as exc:
            raise ValueError(f"{path} does not contain a configuration row") from exc

    return {field: parse_bool(value) for field, value in row.items()}


def parse_bool(value):
    return str(value).strip().lower() == "true"


def false_fields(config_row):
    return [field for field, enabled in config_row.items() if not enabled]


def true_fields(config_row):
    return [field for field, enabled in config_row.items() if enabled]


def build_field_config(filter_fields, multi_option_fields):
    fields = {
        cfg.label.title: {
            "display": "unlabeled header",
            "format": "bold",
        }
    }

    for field in filter_fields:
        fields.setdefault(field, {})["filter"] = "category"

    for field in multi_option_fields:
        fields.setdefault(field, {})["multiOption"] = True

    return fields


def build_library_config(files):
    filter_config = read_config_row(files.filter_config)
    display_config = read_config_row(files.doc_display_config)
    multi_option_config = read_config_row(files.multi_option_config)
    search_config = read_config_row(files.search_config)
    generated_fields = [cfg.label.displayURL, cfg.label.displayIcon]

    return {
        "dataUrl": DEFAULT_DATA_URL,
        "hideValues": DEFAULT_HIDE_VALUES,
        "noFilter": append_missing(false_fields(filter_config), generated_fields),
        "quietFields": append_missing(false_fields(display_config), generated_fields),
        "quietLabel": DEFAULT_QUIET_LABEL,
        "quietLabelFormat": DEFAULT_QUIET_LABEL_FORMAT,
        "maxResultCount": DEFAULT_MAX_RESULT_COUNT,
        "iconTooltip": DEFAULT_ICON_TOOLTIP,
        "hideFromSearch": append_missing(false_fields(search_config), generated_fields),
        "supportText": DEFAULT_SUPPORT_TEXT,
        "fields": build_field_config(
            true_fields(filter_config),
            true_fields(multi_option_config),
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    cfg.add_runtime_path_arguments(parser)
    args = parser.parse_args()
    files, _docs = cfg.configure_runtime_paths(args)

    files.output_dir.mkdir(parents=True, exist_ok=True)
    library_config = build_library_config(files)
    files.library_config_json.write_text(json.dumps(library_config, indent=4), encoding="utf-8")
    print(f"Wrote library config to {files.library_config_json}")


if __name__ == "__main__":
    main()
