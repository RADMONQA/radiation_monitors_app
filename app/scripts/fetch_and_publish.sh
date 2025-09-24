#!/usr/bin/env sh

echo "Starting the fetch and publish script"

# Get the directory of the script
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

# Fetching
#${SCRIPTS_DIR}/fetching/fetch_all.sh

# Processing
if [ "$IS_USING_RADEM" -ne 0 ]; then
    #${SCRIPTS_DIR}/processing/trajectory.py
    #${SCRIPTS_DIR}/publishing/load_to_influxdb.sh
fi

if [ "$IS_USING_IREM" -ne 0 ]; then
    ${SCRIPTS_DIR}/processing/process_irem.sh
fi
