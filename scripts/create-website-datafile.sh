#!/bin/bash
#
# Before running this script, copy the spreadsheet into the inputs folder,
# and rename it to library-index.xlsx
#
# After running this script, check the *.log files that it has created in
# the logs folder. Search for "warn" as well as "error".
#
# After the python scripts have all run successfully there will be a
# library-index.json file in ../src/components. Now the website can
# be built.
#
# This script assumes that a virtual environment named .venv has been
# created for the scripts directory.
# It also assumes that there are the following folders under the directory
# where you run this command:  inputs, outputs, logs.
#

#
FAILURE=1
SUCCESS=0
#
SCRIPTS_DIR=$(cd "$(dirname "$0")" && pwd)
LOG_DIR=logs
INPUT_DIR=inputs
OUTPUT_DIR=outputs
EXCEL_FILE=library-index.xlsx
WEBSITE_SRC_PATH=../src/components
#
VENV=$SCRIPTS_DIR/.venv

usage() {
  echo "Usage: $0 [--input-dir DIR] [--output-dir DIR] [--log-dir DIR] [--excel-file FILE]"
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
    --input-dir)
      require_value "$1" "$2"
      INPUT_DIR="$2"
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

case "$EXCEL_FILE" in
  /*|*/*)
    LIBRARY_INDEX="$EXCEL_FILE"
    ;;
  *)
    LIBRARY_INDEX="$INPUT_DIR/$EXCEL_FILE"
    ;;
esac

PYTHON_PATH_ARGS=(
  --input-dir "$INPUT_DIR"
  --output-dir "$OUTPUT_DIR"
  --log-dir "$LOG_DIR"
  --excel-file "$EXCEL_FILE"
)

# Print start time and ensure we print finish time on exit (local timezone)
START_TIME=$(date +"%Y-%m-%d %H:%M:%S %Z")
echo "Script started at: ${START_TIME}"
# Always print end time when the script exits
trap 'echo "Script finished at: $(date +"%Y-%m-%d %H:%M:%S %Z") with exit code $?"' EXIT

if [ ! -f "$LIBRARY_INDEX" ]; then
  echo "$LIBRARY_INDEX is missing, no processing can be done."
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
# Activate the virtual environment
echo "Activate virtual environment $VENV"
source "$VENV/bin/activate" || {
  echo "Failed to activate virtual environment."
  exit $FAILURE
}

PYTHON_SCRIPT_NAME=parse-excel-file
echo "Running $PYTHON_SCRIPT_NAME.py ..."
python "$SCRIPTS_DIR/$PYTHON_SCRIPT_NAME.py" "${PYTHON_PATH_ARGS[@]}" > "$LOG_DIR/$PYTHON_SCRIPT_NAME.log"  || {
  echo "ERROR | $PYTHON_SCRIPT_NAME.py failed to run successfully."
  exit $FAILURE
}

PYTHON_SCRIPT_NAME=get-library-docs
echo "Running $PYTHON_SCRIPT_NAME.py (this may take quite a while)..."
python "$SCRIPTS_DIR/$PYTHON_SCRIPT_NAME.py" "${PYTHON_PATH_ARGS[@]}" > "$LOG_DIR/$PYTHON_SCRIPT_NAME.log" || {
  echo "ERROR | $PYTHON_SCRIPT_NAME.py failed to run successfully."
  grep "error" "$LOG_DIR/$PYTHON_SCRIPT_NAME.log"
  echo "View $LOG_DIR/$PYTHON_SCRIPT_NAME.log for more information."
  exit $FAILURE
}

PYTHON_SCRIPT_NAME=create-library-index
echo "Running $PYTHON_SCRIPT_NAME.py ..."
python "$SCRIPTS_DIR/$PYTHON_SCRIPT_NAME.py" "${PYTHON_PATH_ARGS[@]}" > "$LOG_DIR/$PYTHON_SCRIPT_NAME.log" || {
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

echo "If all good then you are ready to build the website."
exit $SUCCESS
