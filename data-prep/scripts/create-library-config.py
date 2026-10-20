#!/usr/bin/env python3
"""Create jcudlc-config.json from static settings and generated config CSV files."""

import argparse
import csv
import json
from pathlib import Path

import confighelper as cfg


def append_missing(values, extra_values):
    combined = list(values)
    for value in extra_values:
        if value not in combined:
            combined.append(value)
    return combined


def append_aliases(values, aliases):
    return append_missing(
        values,
        (alias for original, alias in aliases.items() if original in values),
    )


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


def build_library_config(files, aliases=None, quiet_fields=None):
    filter_config = read_config_row(files.filter_config)
    search_config = read_config_row(files.search_config)
    generated_fields = [cfg.label.displayURL, cfg.label.displayIcon]

    config = {
        "noFilter": append_missing(false_fields(filter_config), generated_fields),
        "quietFields": append_missing(generated_fields, quiet_fields or []),
        "hideFromSearch": append_missing(false_fields(search_config), generated_fields),
    }
    for field_list in ("noFilter", "quietFields", "hideFromSearch"):
        config[field_list] = append_aliases(config[field_list], aliases or {})
    return config


def load_static_config(path):
    with path.open(encoding="utf-8") as config_file:
        static_config = json.load(config_file)
    if not isinstance(static_config, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return static_config


def main():
    parser = argparse.ArgumentParser()
    cfg.add_runtime_path_arguments(parser)
    args = parser.parse_args()
    files, _docs = cfg.configure_runtime_paths(args)

    files.output_dir.mkdir(parents=True, exist_ok=True)
    static_config = load_static_config(files.static_config_file)
    generated_config = build_library_config(
        files,
        static_config.get("aliases", {}),
        static_config.get("quietFields", []),
    )
    library_config = {**static_config, **generated_config}
    files.library_config_json.write_text(json.dumps(library_config, indent=4), encoding="utf-8")
    print(f"Wrote library config to {files.library_config_json}")


if __name__ == "__main__":
    main()
