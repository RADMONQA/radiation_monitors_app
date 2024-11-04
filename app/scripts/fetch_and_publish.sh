#!/usr/bin/env sh

# Get the directory of the script
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

# Fetching
${SCRIPTS_DIR}/fetching/fetch_all.sh

# Publishing
${SCRIPTS_DIR}/publishing/load_to_influxdb.sh
