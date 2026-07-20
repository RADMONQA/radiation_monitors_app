#!/usr/bin/env sh
#
# Stages IREM pitch-angle input data.
#
# Default (seed mode): copies a bundled HDF5 - the actual output of a working
# 03_pitch_angle.ipynb run - into app_data so the pipeline can publish to
# InfluxDB without any SPICE/geopack computation.
#
# Set IREM_PITCH_ANGLE_FETCH_MODE=network to instead stage a local INTEGRAL
# SPICE kernel set; irem_pitch_angle_process.py then computes pitch angle
# from scratch using the already-staged magfield data.

set -eu

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPTS_DIR}/../../.." && pwd)"

PITCH_ANGLE_DIR="${DATA_DIR}/irem/pitch_angle"
KERNELS_TARGET="${DATA_DIR}/irem/kernels"
SEED_TARGET="${PITCH_ANGLE_DIR}/pitch_angle_full.h5"

FETCH_MODE="${IREM_PITCH_ANGLE_FETCH_MODE:-seed}"

mkdir -p "${PITCH_ANGLE_DIR}"

log() {
    printf '%s\n' "$*" >&2
}

resolve_seed_path() {
    if [ -n "${IREM_PITCH_ANGLE_SEED_PATH:-}" ] && [ -f "${IREM_PITCH_ANGLE_SEED_PATH}" ]; then
        printf '%s\n' "${IREM_PITCH_ANGLE_SEED_PATH}"
        return 0
    fi

    for candidate in \
        "/app/seeds/irem/pitch_angle_full.h5" \
        "${REPO_ROOT}/irem_magnetic_pitch_angle_full.h5"
    do
        if [ -f "${candidate}" ]; then
            printf '%s\n' "${candidate}"
            return 0
        fi
    done

    return 1
}

stage_pitch_angle_seed() {
    seed_path="$(resolve_seed_path || true)"
    if [ -z "${seed_path}" ]; then
        log "ERROR: No pitch-angle seed file found."
        log "Place irem_magnetic_pitch_angle_full.h5 in the repo root or set IREM_PITCH_ANGLE_SEED_PATH."
        return 1
    fi

    log "Using pitch-angle seed: ${seed_path}"

    if [ ! -f "${SEED_TARGET}" ] || [ "${seed_path}" -nt "${SEED_TARGET}" ]; then
        cp "${seed_path}" "${SEED_TARGET}"
        log "Staged pitch-angle seed -> ${SEED_TARGET}"
    else
        log "Pitch-angle seed already up to date at ${SEED_TARGET}"
    fi
}

resolve_kernels_source() {
    for candidate in \
        "/app/seeds/irem/kernels" \
        "${REPO_ROOT}/irem_kernels"
    do
        if [ -d "${candidate}" ]; then
            printf '%s\n' "${candidate}"
            return 0
        fi
    done

    return 1
}

stage_kernels_seed() {
    src="$(resolve_kernels_source || true)"
    if [ -z "${src}" ]; then
        log "ERROR: No INTEGRAL kernels directory found."
        log "Place a kernels directory at ${REPO_ROOT}/irem_kernels or set IREM_KERNELS_SEED_PATH."
        return 1
    fi

    log "Using kernels source: ${src}"

    stamp="${KERNELS_TARGET}/.staged_from"
    if [ ! -f "${stamp}" ] || [ "${src}" -nt "${stamp}" ]; then
        rm -rf "${KERNELS_TARGET}"
        mkdir -p "${KERNELS_TARGET}"
        cp -r "${src}/." "${KERNELS_TARGET}/"
        printf '%s\n' "${src}" > "${stamp}"
        touch -r "${src}" "${stamp}" 2>/dev/null || true
        log "Staged INTEGRAL kernels -> ${KERNELS_TARGET}"
    else
        log "Kernels already up to date at ${KERNELS_TARGET}"
    fi
}

echo "============= STAGING IREM PITCH-ANGLE INPUT DATA ============="
echo "Fetch mode: ${FETCH_MODE}"

case "${FETCH_MODE}" in
    seed)
        stage_pitch_angle_seed
        ;;
    network)
        stage_kernels_seed
        ;;
    auto)
        if stage_pitch_angle_seed; then
            :
        else
            log "Seed not found; falling back to staging kernels for from-scratch computation."
            stage_kernels_seed
        fi
        ;;
    *)
        log "ERROR: Unknown IREM_PITCH_ANGLE_FETCH_MODE=${FETCH_MODE} (use seed, network, or auto)"
        exit 1
        ;;
esac

echo -e "\e[32mIREM PITCH-ANGLE INPUT DATA READY\e[0m"
