#!/usr/bin/env sh

# Get the directory of the script
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

# Data fetching
if [ "$IS_USING_RADEM" -ne 0 ]; then
    echo "============= FETCHING RADEM DATA ============="
    ${SCRIPTS_DIR}/fetch_radem.sh
    echo -e "\e[32mRADEM DATA FETCHED SUCCESSFULLY\e[0m"
fi

if [ "$IS_USING_IREM" -ne 0 ]; then
    echo "============= FETCHING IREM DATA ============="
    ${SCRIPTS_DIR}/fetch_irem.sh
    echo -e "\e[32mIREM DATA FETCHED SUCCESSFULLY\e[0m"
fi
