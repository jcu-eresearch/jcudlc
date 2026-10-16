#!/usr/bin/env python3
""" create-library-index.py

    This reads the library-index spreadsheet and generates a
    jcudlc-data.json file from the information in the spreadsheet.

    The paths and names of files are all defined in constants at
    the top of the file, as are the column names for the csv file.

    The script requires the structlog library to be installed
    (used for logging).
"""
import pandas as pd
import logging
import structlog
import argparse
from dataclasses import asdict
import confighelper as cfg
import libhelper
from confighelper import (
    docs,
    label,
    access_types,
    status_types,
    icons,
    urls,
    files,
)

is_dry_run = False


def split_multi_option_values(lib_data):
    # Split the multi-option columns in to lists of strings
    # hopefully this won't break the lib_docs.to_json function

    #   Columns that can contain multi-options, the value of the item is
    #   a string containing 1 or more tokens separated by semi-colons.
    #   Extract the tokens and replace the value with an array of strings
    #   where each string is a token.
    #
    multi_option_fields = get_multioption_fields(log)
    for column in multi_option_fields:
        log.debug(
            "split_multi_option_values: splitting {}\n  orig\n{} \nsplit values{}".format(
                column, lib_data[column], lib_data[column].str.split(";")
            )
        )
        lib_data[column] = (
            lib_data[column]
            .str.split(";")
            .apply(lambda x: [item.strip() for item in x] if x != [""] else [])
        )
        log.debug("split_multi_option_values: lib_data[{}]\n".format(lib_data[column]))

    return lib_data

def set_url_and_icon(log, lib_data):
    # set label.url value for access via a physical library
    lib_data.loc[
        lib_data[label.access] == access_types.physical_library, label.displayURL
    ] = urls.physical_library
    lib_data.loc[
        lib_data[label.access] == access_types.physical_library, label.displayIcon
    ] = icons.library

    # Prefer copied documents; otherwise preserve the spreadsheet's URL.
    doc_list = {path.name for path in docs.dest_path.iterdir() if path.is_file()}
    open_access = lib_data[label.access] == access_types.open
    local_download = open_access & lib_data[label.filename].isin(doc_list)
    lib_data.loc[open_access, label.displayURL] = lib_data.loc[open_access, label.publishedURL]
    lib_data.loc[local_download, label.displayURL] = (
        urls.download + lib_data.loc[local_download, label.filename]
    )
    lib_data.loc[
        lib_data[label.access] == access_types.open, label.displayIcon
    ] = icons.download

    # set label.url value for documents accessed from an external website
    lib_data.loc[
        lib_data[label.access] == access_types.publisher, label.displayURL
    ] = lib_data[label.publishedURL]
    lib_data.loc[
        lib_data[label.access] == access_types.publisher, label.displayIcon
    ] = icons.webpage

    return lib_data

def create_library_index(log, is_dry_run, lib_data):
    log.info("Creating library_index for website, {}".format(files.libindex_json))

    # convert the list of dictionary items to json string format
    json_lib_data = lib_data.to_json(orient="records")
    log.info("Documents in library, final count: {}".format(lib_data.index.size))

    if not is_dry_run:
        # write library-index json file for the website to use
        json_array_output_file = files.libindex_json.open(mode="w", encoding="utf-8")
        json_array_output_file.write(json_lib_data)

        log.info("Wrote JSON file to {}".format(files.libindex_json))

    return lib_data


def get_multioption_fields(log):
    data = pd.read_csv(files.multi_option_config)
    fields = data.columns[data.iloc[0]].to_list()
    log.info("The multi-option fields for libary are: {}".format(fields))
    return fields

def remove_private_details(log, lib_data):
    # Read in the appropriate config file and drop any columns
    # from lib_data that are set to False in the config file

    public_labels = pd.read_csv(files.doc_display_config)
    col_list = public_labels.columns[~public_labels.iloc[0]].to_list()
    lib_data = lib_data.drop(columns=col_list)
    log.info("Dropped {} columns".format(col_list))

    return lib_data


def replace_invalid_access_values(log, lib_data):
    valid_access_types = asdict(access_types).values()

    # Get a list of docs with an invalid access type
    problem_docs = lib_data[
        ~lib_data[label.access].isin(valid_access_types)
    ]

    log.debug("valid access types are {}".format(valid_access_types))

    for _, row in problem_docs.iterrows():
        log.warning(
            "ID {} | Invalid {} value {!r}; changed to {!r}. Correct the spreadsheet value in the next update.".format(
                row[label.id], label.access, row[label.access], access_types.physical_library
            )
        )

    lib_data.loc[problem_docs.index, label.access] = access_types.physical_library
    log.info(
        "Number of invalid access values changed to {}: {}".format(
            access_types.physical_library, problem_docs.index.size
        )
    )

    return lib_data


def replace_openaccess_without_file(log, lib_data):
    # Request library access only when neither a copied file nor a URL exists.

    # Get the list of files for the library.
    doc_list = {path.name for path in docs.dest_path.iterdir() if path.is_file()}

    # DEBUG - log the list of files in the library, displaying each file on a separate line
    log.debug("Documents in the library: \n{}".format("\n".join(sorted(doc_list))))

    # Get a list of the open access docs that don't have a file in the library
    problem_docs = lib_data[
        (lib_data[label.access] == access_types.open)
        & (~lib_data[label.filename].isin(doc_list))
        & (lib_data[label.publishedURL].fillna("").str.strip() == "")
    ]
    for _, doc in problem_docs.iterrows():
        filename = doc[label.filename]
        problem = (
            "{} is blank".format(label.filename)
            if filename == ""
            else "{} {!r} has no matching file in {}".format(
                label.filename, filename, docs.dest_path
            )
        )
        log.warning(
            "ID {} | {} and {} is blank for {} access; changed {} to {!r}. Correct the filename, add the PDF, or provide a URL in the next update.".format(
                doc[label.id], problem, label.publishedURL, access_types.open, label.access,
                access_types.physical_library
            )
        )

    lib_data.loc[problem_docs.index, label.access] = access_types.physical_library
    log.info(
        "Number of {} records without a matching file or URL changed to {}: {}".format(
            access_types.open, access_types.physical_library, problem_docs.index.size
        )
    )

    return lib_data


def replace_publisheraccess_without_url(log, lib_data):
    # Get a list of the external access docs that don't have a URL in the lib data
    problem_docs = lib_data[
        (lib_data[label.access] == access_types.publisher)
        & (lib_data[label.publishedURL] == "")
    ]
    for _, doc in problem_docs.iterrows():
        log.warning(
            "ID {} | {} is blank for {} record; changed {} to {!r}. Add the publisher URL in the next spreadsheet update.".format(
                doc[label.id], label.publishedURL, access_types.publisher,
                label.access, access_types.physical_library
            )
        )

    lib_data.loc[problem_docs.index, label.access] = access_types.physical_library
    log.info(
        "Number of {} records without a publisher URL changed to {}: {}".format(
            access_types.publisher, access_types.physical_library, problem_docs.index.size
        )
    )
    return lib_data


def remove_nonactive_rows(log, lib_data):
    # Drop all rows that don't have status set to Active
    # unless there is no Status column
    initial_num_docs = lib_data.index.size
    if label.status in lib_data.columns:
        # Use the configured status column name rather than a hard-coded 'Status'
        lib_data = lib_data[lib_data[label.status] == status_types.active]
        log.info("Extracted only the {} records to process".format(status_types.active))

    log.info(
        "Number of docs dropped due to Status not set to {} is {}".format(
            status_types.active, initial_num_docs - lib_data.index.size
        )
    )
    log.info(
        "Number of {} records kept: {}".format(
            status_types.active, lib_data.index.size
        )
    )

    return lib_data


if __name__ == "__main__":
    # Specify level of entries to log
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )
    log = structlog.get_logger()

    # create parser
    parser = argparse.ArgumentParser()
    cfg.add_runtime_path_arguments(parser)

    # add arguments to the parser
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="don't make any changes but give me some stats on what would happen",
    )

    # parse the command line arguments
    args = parser.parse_args()
    files, docs = cfg.configure_runtime_paths(args)
    files.output_dir.mkdir(parents=True, exist_ok=True)
    docs.dest_path.mkdir(parents=True, exist_ok=True)

    is_dry_run = args.dry_run
    if is_dry_run:
        log.info("This is a dry-run, no changes will be made")

    log.info("Loading csv file from {}.".format(files.libindex_csv))

    # Read in data from the library-index.csv file and ensure that
    # there are no leading or trailing spaces on the contents
    lib_data = pd.read_csv(
        files.libindex_csv, dtype="str", skipinitialspace=True, keep_default_na=False
    ).map(str.strip)
    log.info("Initial # rows loaded: {}".format(lib_data.index.size))

    # Match the filenames used for copied documents, including when the copy
    # stage was skipped and documents were already present in the output folder.
    lib_data[label.filename] = lib_data[label.filename].map(libhelper.get_normalised_filename)
    if not is_dry_run:
        lib_data.to_csv(files.libindex_csv, index=False, encoding="utf-8")

    lib_data = remove_nonactive_rows(log, lib_data)
    lib_data = replace_invalid_access_values(log, lib_data)
    lib_data = replace_openaccess_without_file(log, lib_data)
    lib_data = replace_publisheraccess_without_url(log, lib_data)
    lib_data = split_multi_option_values(lib_data)
    lib_data = set_url_and_icon(log, lib_data)
    # Remove non-public columns after validation and URL/icon generation.
    lib_data = remove_private_details(log, lib_data)

    create_library_index(log, is_dry_run, lib_data)

    log.info("Library index file creation is complete")
