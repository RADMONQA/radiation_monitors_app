#!/usr/bin/env sh

# Get the absolute path of the directory where this script is located
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

# Execute the processing pipeline
python3 ${SCRIPTS_DIR}/irem_process.py

echo ok
