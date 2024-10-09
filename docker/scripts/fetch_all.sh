#!/usr/bin/env sh

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============= FETCHING RADEM DATA =============" 
${SCRIPTS_DIR}/fetch_radem.sh

# echo "============= FETCHING KERNELS =============" 
# cd kernel
# ./0_fetch_data.sh
# cd ..

# echo "============= FETCHING IREM =============" 
# cd irem
# ./0_fetch_data.sh
# cd ..

echo ok