#!/usr/bin/env sh

echo "Starting the fetch and publish script"

# Get the directory of the script
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

# Fetching
${SCRIPTS_DIR}/fetching/fetch_all.sh

# Processing
${SCRIPTS_DIR}/processing/trajectory.py
${SCRIPTS_DIR}/processing/process_irem.sh
