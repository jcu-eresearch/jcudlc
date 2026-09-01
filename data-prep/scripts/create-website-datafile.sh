#!/bin/bash
#
# Before running this script, copy the spreadsheet into the spreadsheet input
# folder, rename it to library-index.xlsx, and place source documents in the
# documents input folder.
#
# After running this script, check the *.log files that it has created in
# the logs folder. Search for "warn" as well as "error".
#
# After the python scripts have all run successfully there will be a
# jcudlc-data.json file in ../src/components. Now the website can
# be built.
#
# This script assumes that a virtual environment named .venv has been
# created for the scripts directory.
# Runtime paths are configured in library-config.yml and can be overridden with
# command-line arguments.
#

#
FAILURE=1
SUCCESS=0
#
SCRIPTS_DIR=$(cd "$(dirname "$0")" && pwd)
VENV=$SCRIPTS_DIR/.venv
PYTHON_BIN=$VENV/bin/python
WEBSITE_SRC_PATH=../src/components

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Python virtual environment not found at $VENV."
  exit $FAILURE
fi

RUNTIME_CONFIG=$("$PYTHON_BIN" "$SCRIPTS_DIR/confighelper.py" --print-runtime-defaults) || {
  echo "Unable to load runtime defaults from $SCRIPTS_DIR/library-config.yml."
  exit $FAILURE
}
IFS=$'\t' read -r EXCEL_FILE DOCUMENTS_DIR OUTPUT_DIR LOG_DIR <<< "$RUNTIME_CONFIG"

usage() {
  echo "Usage: $0 [--excel-file FILE] [--documents-dir DIR] [--output-dir DIR] [--log-dir DIR]"
}

require_value() {
  if [ -z "$2" ]; then
    echo "Missing value for $1"
    usage
    exit $FAILURE
  fi
}

while [ $# -gt 0 ]; do
  case "$1" in
    --documents-dir)
      require_value "$1" "$2"
      DOCUMENTS_DIR="$2"
      shift 2
      ;;
    --output-dir)
      require_value "$1" "$2"
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --log-dir)
      require_value "$1" "$2"
      LOG_DIR="$2"
      shift 2
      ;;
    --excel-file)
      require_value "$1" "$2"
      EXCEL_FILE="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit $SUCCESS
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit $FAILURE
      ;;
  esac
done

PYTHON_PATH_ARGS=(
  --documents-dir "$DOCUMENTS_DIR"
  --output-dir "$OUTPUT_DIR"
  --log-dir "$LOG_DIR"
  --excel-file "$EXCEL_FILE"
)

# Print start time and ensure we print finish time on exit (local timezone)
START_TIME=$(date +"%Y-%m-%d %H:%M:%S %Z")
echo "Script started at: ${START_TIME}"

print_finish_time() {
  local pipeline_exit_code=$?
  trap - EXIT
  echo "Script finished at: $(date +"%Y-%m-%d %H:%M:%S %Z") with exit code $pipeline_exit_code"
  exit "$pipeline_exit_code"
}

trap print_finish_time EXIT

if [ ! -f "$EXCEL_FILE" ]; then
  echo "$EXCEL_FILE is missing, no processing can be done."
  exit $FAILURE
fi

mkdir -p "$LOG_DIR" "$OUTPUT_DIR" "$OUTPUT_DIR/documents" || {
  echo "Cannot create output or log directories."
  exit $FAILURE
}

# clear previous outputs and log files
echo "Removing any previous $LOG_DIR/*.log files"
rm -f "$LOG_DIR"/*.log

echo "Removing any previous $OUTPUT_DIR *.csv and *.json files"
rm -f "$OUTPUT_DIR"/*.csv
rm -f "$OUTPUT_DIR"/*.json

#
# Input check and cleanup done. Time to start running the python scripts
#
# Use the virtual environment's interpreter directly. This avoids relying on
# absolute paths embedded in an activation script when the repository is moved.
echo "Using Python virtual environment $VENV"

PYTHON_SCRIPT_NAME=parse-excel-file
echo "Running $PYTHON_SCRIPT_NAME.py ..."
"$PYTHON_BIN" "$SCRIPTS_DIR/$PYTHON_SCRIPT_NAME.py" "${PYTHON_PATH_ARGS[@]}" > "$LOG_DIR/$PYTHON_SCRIPT_NAME.log"  || {
  echo "ERROR | $PYTHON_SCRIPT_NAME.py failed to run successfully."
  exit $FAILURE
}

PYTHON_SCRIPT_NAME=get-library-docs
echo "Running $PYTHON_SCRIPT_NAME.py (this may take quite a while)..."
"$PYTHON_BIN" "$SCRIPTS_DIR/$PYTHON_SCRIPT_NAME.py" "${PYTHON_PATH_ARGS[@]}" > "$LOG_DIR/$PYTHON_SCRIPT_NAME.log" || {
  echo "ERROR | $PYTHON_SCRIPT_NAME.py failed to run successfully."
  grep "error" "$LOG_DIR/$PYTHON_SCRIPT_NAME.log"
  echo "View $LOG_DIR/$PYTHON_SCRIPT_NAME.log for more information."
  exit $FAILURE
}

PYTHON_SCRIPT_NAME=create-library-index
echo "Running $PYTHON_SCRIPT_NAME.py ..."
"$PYTHON_BIN" "$SCRIPTS_DIR/$PYTHON_SCRIPT_NAME.py" "${PYTHON_PATH_ARGS[@]}" > "$LOG_DIR/$PYTHON_SCRIPT_NAME.log" || {
  echo "ERROR | $PYTHON_SCRIPT_NAME.py failed to run successfully."
  grep "error" "$LOG_DIR/$PYTHON_SCRIPT_NAME.log"
  echo "View $LOG_DIR/$PYTHON_SCRIPT_NAME.log for more information."
  exit $FAILURE
}

PYTHON_SCRIPT_NAME=create-library-config
echo "Running $PYTHON_SCRIPT_NAME.py ..."
"$PYTHON_BIN" "$SCRIPTS_DIR/$PYTHON_SCRIPT_NAME.py" "${PYTHON_PATH_ARGS[@]}" > "$LOG_DIR/$PYTHON_SCRIPT_NAME.log" || {
  echo "ERROR | $PYTHON_SCRIPT_NAME.py failed to run successfully."
  grep "error" "$LOG_DIR/$PYTHON_SCRIPT_NAME.log"
  echo "View $LOG_DIR/$PYTHON_SCRIPT_NAME.log for more information."
  exit $FAILURE
}

echo "SUCCESS | No errors but you should still check the log files for warnings."

# # copy json files into website src area
# echo "cp *.json files to $WEBSITE_SRC_PATH"
# cp $OUTPUT_DIR/*.json $WEBSITE_SRC_PATH || {
#   echo "ERROR: Failed to copy files."
#   exit $FAILURE
# }

# Show warnings from the last two script runs to make them easy to spot
echo "--- Warnings in $LOG_DIR/get-library-docs.log ---"
grep -i "warning\|warn" "$LOG_DIR/get-library-docs.log" || echo "(no warnings found)"
echo "--- Warnings in $LOG_DIR/create-library-index.log ---"
grep -i "warning\|warn" "$LOG_DIR/create-library-index.log" || echo "(no warnings found)"
echo "--- Warnings in $LOG_DIR/create-library-config.log ---"
grep -i "warning\|warn" "$LOG_DIR/create-library-config.log" || echo "(no warnings found)"

echo "If all good then you are ready to build the website."
exit $SUCCESS
