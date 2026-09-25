#!/usr/bin/env sh
#
# Builds the IREM magnetosphere HDF5 files and publishes them to InfluxDB.

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============= BUILDING IREM MAGNETOSPHERE DATA ============="
python3 "${SCRIPTS_DIR}/irem_magnetosphere_process.py"

echo "============= PUBLISHING IREM MAGNETOSPHERE DATA ============="
python3 "${SCRIPTS_DIR}/irem_magnetosphere_publish.py"

printf '\033[32m%s\033[0m\n' "IREM MAGNETOSPHERE PROCESSING COMPLETE"
