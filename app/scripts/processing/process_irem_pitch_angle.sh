#!/usr/bin/env sh

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============= PROCESSING IREM PITCH ANGLE DATA ============="
python3 "${SCRIPTS_DIR}/irem_pitch_angle_process.py"
python3 "${SCRIPTS_DIR}/irem_pitch_angle_publish.py"
echo -e "\e[32mIREM PITCH ANGLE PROCESSING COMPLETE\e[0m"
