#!/bin/bash
# Run the shared catalogue build pipeline.
SCRIPTS_DIR=$(cd "$(dirname "$0")" && pwd)
exec bash "$SCRIPTS_DIR/build-jcudlc-files.sh" "$@"
