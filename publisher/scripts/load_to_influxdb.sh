#!/usr/bin/env sh

# Get the absolute path of the directory where this script is located
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

# Execute the processing pipeline
python3 ${SCRIPTS_DIR}/1_processing_raw.py
python3 ${SCRIPTS_DIR}/2_processing_csv.py
python3 ${SCRIPTS_DIR}/3_processing_line_protocol.py

echo ok
