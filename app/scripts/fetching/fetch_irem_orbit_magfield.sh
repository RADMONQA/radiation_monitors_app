#!/usr/bin/env sh
#
# Stages IREM magfield input data for processing.
#
# Default (seed mode): copies a bundled HDF5 file into app_data so the pipeline
# can publish to InfluxDB without downloading orbit / TS05 inputs.
#
# Set IREM_MAGFIELD_FETCH_MODE=network to use the legacy download path instead.

set -eu

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPTS_DIR}/../../.." && pwd)"

ORBIT_ARCHIVE="${DATA_DIR}/irem/orbit/archive"
ORBIT_EXTRACTED="${DATA_DIR}/irem/orbit/extracted"
TSYGAN_DIR="${DATA_DIR}/irem/magfield/tsygan_input"
MAGFIELD_DIR="${DATA_DIR}/irem/magfield"
LOG_DIR="${DATA_DIR}/irem/magfield/logs"
MAGFIELD_TARGET="${MAGFIELD_DIR}/magfield_data.h5"

FETCH_MODE="${IREM_MAGFIELD_FETCH_MODE:-seed}"
ORBIT_FIRST="${IREM_ORBIT_FIRST:-1}"
ORBIT_LAST="${IREM_ORBIT_LAST:-2878}"
TS05_START_YEAR="${IREM_TS05_START_YEAR:-2002}"
ORBIT_PROGRESS_EVERY="${IREM_ORBIT_PROGRESS_EVERY:-25}"

WGET_OPTS="--continue --timestamping --no-check-certificate \
    --timeout=30 --tries=2 --waitretry=2 \
    --read-timeout=120 --dns-timeout=30 --connect-timeout=30"

mkdir -p "${ORBIT_ARCHIVE}" "${ORBIT_EXTRACTED}" "${TSYGAN_DIR}" "${LOG_DIR}" "${MAGFIELD_DIR}"

log() {
    printf '%s\n' "$*" >&2
}

download_file() {
    url="$1"
    dest="$2"
    log_name="$3"

    log "Downloading ${log_name}..."
    if wget ${WGET_OPTS} -O "${dest}.part" "${url}" >>"${LOG_DIR}/download.log" 2>&1; then
        mv "${dest}.part" "${dest}"
        log "Download successful: ${log_name}"
        return 0
    fi

    rm -f "${dest}.part"
    log "Download failed: ${log_name} (see ${LOG_DIR}/download.log)"
    return 1
}

resolve_seed_path() {
    if [ -n "${IREM_MAGFIELD_SEED_PATH:-}" ] && [ -f "${IREM_MAGFIELD_SEED_PATH}" ]; then
        printf '%s\n' "${IREM_MAGFIELD_SEED_PATH}"
        return 0
    fi

    for candidate in \
        "/app/seeds/irem/magfield_data.h5" \
        "${REPO_ROOT}/magfield_data_full.h5" \
        "${REPO_ROOT}/app/seeds/irem/magfield_data.h5" \
        "${REPO_ROOT}/app/seeds/irem/magfield_data_full.h5"
    do
        if [ -f "${candidate}" ]; then
            printf '%s\n' "${candidate}"
            return 0
        fi
    done

    return 1
}

stage_magfield_seed() {
    seed_path="$(resolve_seed_path || true)"
    if [ -z "${seed_path}" ]; then
        log "ERROR: No magfield seed file found."
        log "Place magfield_data_full.h5 in the repo root or set IREM_MAGFIELD_SEED_PATH."
        return 1
    fi

    log "Using magfield seed: ${seed_path}"

    if [ ! -f "${MAGFIELD_TARGET}" ] || [ "${seed_path}" -nt "${MAGFIELD_TARGET}" ]; then
        cp "${seed_path}" "${MAGFIELD_TARGET}"
        log "Staged magfield data -> ${MAGFIELD_TARGET}"
    else
        log "Magfield data already up to date at ${MAGFIELD_TARGET}"
    fi
}

fetch_orbit_network() {
    log "============= FETCHING IREM ORBIT DATA (network) ============="
    log "Orbit rev range: ${ORBIT_FIRST}..${ORBIT_LAST}"

    ORBIT_DOWNLOADED=0
    ORBIT_EXTRACTED=0
    ORBIT_SKIPPED=0
    ORBIT_FAILED=0
    ORBIT_TOTAL=$((ORBIT_LAST - ORBIT_FIRST + 1))

    i="${ORBIT_FIRST}"
    while [ "${i}" -le "${ORBIT_LAST}" ]; do
        number=$(printf "%04d" "${i}")
        filename="orbit_historic_${number}.fits.gz"
        gz_path="${ORBIT_ARCHIVE}/${filename}"
        fits_path="${ORBIT_EXTRACTED}/orbit_historic_${number}.fits"
        url="http://isdcarc.unige.ch/arc/rev_3/aux/adp/${number}.001/orbit_historic.fits.gz"
        progress=$((i - ORBIT_FIRST + 1))

        if [ $((progress % ORBIT_PROGRESS_EVERY)) -eq 0 ] || [ "${progress}" -eq 1 ]; then
            log "Orbit progress: ${progress}/${ORBIT_TOTAL} (rev ${number}, downloaded ${ORBIT_DOWNLOADED}, skipped ${ORBIT_SKIPPED}, failed ${ORBIT_FAILED})"
        fi

        if [ -f "${fits_path}" ]; then
            ORBIT_SKIPPED=$((ORBIT_SKIPPED + 1))
            i=$((i + 1))
            continue
        fi

        if [ ! -f "${gz_path}" ]; then
            if download_file "${url}" "${gz_path}" "${filename}"; then
                ORBIT_DOWNLOADED=$((ORBIT_DOWNLOADED + 1))
            else
                ORBIT_FAILED=$((ORBIT_FAILED + 1))
            fi
        fi

        if [ -f "${gz_path}" ] && [ ! -f "${fits_path}" ]; then
            log "Extracting ${filename}..."
            if gunzip -c "${gz_path}" > "${fits_path}" 2>>"${LOG_DIR}/download.log"; then
                ORBIT_EXTRACTED=$((ORBIT_EXTRACTED + 1))
            else
                rm -f "${fits_path}"
                ORBIT_FAILED=$((ORBIT_FAILED + 1))
            fi
        fi

        i=$((i + 1))
    done

    log "Orbit fetch complete (downloaded ${ORBIT_DOWNLOADED}, extracted ${ORBIT_EXTRACTED}, skipped ${ORBIT_SKIPPED}, failed ${ORBIT_FAILED})"
}

fetch_ts05_network() {
    CURRENT_YEAR=$(date +%Y)
    TS05_END_YEAR="${IREM_TS05_END_YEAR:-$((CURRENT_YEAR - 1))}"

    log "============= FETCHING TS05 OMNI INPUT DATA (network) ============="
    log "TS05 year range: ${TS05_START_YEAR}..${TS05_END_YEAR}"

    TS05_BASE_URL="https://geo.phys.spbu.ru/~tsyganenko/TS05_data_and_stuff/"
    TS05_DOWNLOADED=0
    TS05_EXTRACTED=0
    TS05_SKIPPED=0
    TS05_FAILED=0

    year="${TS05_START_YEAR}"
    while [ "${year}" -le "${TS05_END_YEAR}" ]; do
        zip_name="${year}_OMNI_5m_with_TS05_variables.zip"
        dat_name="${year}_OMNI_5m_with_TS05_variables.dat"
        zip_path="${TSYGAN_DIR}/${zip_name}"
        dat_path="${TSYGAN_DIR}/${dat_name}"
        url="${TS05_BASE_URL}${zip_name}"

        if [ -f "${dat_path}" ]; then
            TS05_SKIPPED=$((TS05_SKIPPED + 1))
            year=$((year + 1))
            continue
        fi

        if [ ! -f "${zip_path}" ]; then
            if download_file "${url}" "${zip_path}" "${zip_name}"; then
                TS05_DOWNLOADED=$((TS05_DOWNLOADED + 1))
            else
                TS05_FAILED=$((TS05_FAILED + 1))
            fi
        fi

        if [ -f "${zip_path}" ] && [ ! -f "${dat_path}" ]; then
            if unzip -o -q "${zip_path}" -d "${TSYGAN_DIR}" 2>>"${LOG_DIR}/download.log"; then
                TS05_EXTRACTED=$((TS05_EXTRACTED + 1))
            else
                TS05_FAILED=$((TS05_FAILED + 1))
            fi
        fi

        year=$((year + 1))
    done

    log "TS05 fetch complete (downloaded ${TS05_DOWNLOADED}, extracted ${TS05_EXTRACTED}, skipped ${TS05_SKIPPED}, failed ${TS05_FAILED})"
}

echo "============= FETCHING IREM MAGFIELD INPUT DATA ============="
echo "Fetch mode: ${FETCH_MODE}"
echo "Data directory: ${DATA_DIR}"

case "${FETCH_MODE}" in
    seed)
        echo "============= STAGING BUNDLED MAGFIELD SEED ============="
        stage_magfield_seed
        ;;
    network)
        fetch_orbit_network
        fetch_ts05_network
        ;;
    auto)
        if stage_magfield_seed; then
            :
        else
            log "Seed not found; falling back to network fetch."
            fetch_orbit_network
            fetch_ts05_network
        fi
        ;;
    *)
        log "ERROR: Unknown IREM_MAGFIELD_FETCH_MODE=${FETCH_MODE} (use seed, network, or auto)"
        exit 1
        ;;
esac

echo -e "\e[32mIREM MAGFIELD INPUT DATA READY\e[0m"
