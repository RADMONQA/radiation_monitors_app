#!/usr/bin/env sh

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
FETCH_MODE="${IREM_MAGFIELD_FETCH_MODE:-seed}"

echo "============= PROCESSING IREM MAGFIELD DATA ============="
echo "Magfield mode: ${FETCH_MODE}"

if [ "${FETCH_MODE}" = "network" ]; then
    python3 "${SCRIPTS_DIR}/irem_orbit_magfield_process.py"
else
    echo "Skipping magfield computation (using staged seed HDF5)."
fi

python3 "${SCRIPTS_DIR}/irem_magfield_publish.py"
echo -e "\e[32mIREM MAGFIELD PROCESSING COMPLETE\e[0m"
