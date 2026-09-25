#!/usr/bin/env sh
# shellcheck disable=SC2034
#
# Fetches IREM orbit and TS05 input data for the magnetosphere pipeline.
# Downloads are off (both sources down), uncomment the loops at the end
# when a new source is found.

set -eu

DIR="${DATA_DIR}/irem/magnetosphere"
ORBIT_DIR="${DIR}/orbit"
TSYGAN_DIR="${DIR}/tsygan_input"
LOG="${DIR}/logs/download.log"

ORBIT_URL="http://isdcarc.unige.ch/arc/rev_3/aux/adp"
TS05_URL="https://geo.phys.spbu.ru/~tsyganenko/TS05_data_and_stuff"
TS05_LEGACY_URL="https://geo.phys.spbu.ru/~tsyganenko/models/ts05"

# TS05 years published as .dat instead of .zip
TS05_PLAIN_YEARS="2024"
TS05_LEGACY_YEARS="2003 2015 2016 2017"

# INTEGRAL revolution 1 start and length
REV_EPOCH=1034812800
REV_SECONDS=241920

ORBIT_FIRST=1
ORBIT_LAST=$(( ($(date -u +%s) - REV_EPOCH) / REV_SECONDS + 5 ))
TS05_FIRST=2002
TS05_LAST=$(( $(date -u +%Y) - 1 ))

MAX_FAILURES=5

SOURCES_STATUS="Downloads are off. Checked on 2026-09-25: the ISDC orbit archive \
(isdcarc.unige.ch) does not respond, and the Tsyganenko TS05 site (geo.phys.spbu.ru) \
blocks access (HTTP 410). Using the precomputed HDF5 files in ${DIR}/hdf."

log() {
    printf '%s\n' "$*" >&2
}

# Downloads $1 to $2 through a .part file
download() {
    if wget --no-check-certificate --tries=2 --waitretry=2 --timeout=20 --read-timeout=60 \
        -O "$2.part" "$1" >>"${LOG}" 2>&1; then
        mv "$2.part" "$2"
    else
        rm -f "$2.part"
        return 1
    fi
}

# Writes the output of the command after $1 to $1 through a .part file
unpack() {
    dest="$1"
    shift
    if "$@" > "${dest}.part" 2>>"${LOG}"; then
        mv "${dest}.part" "${dest}"
    else
        rm -f "${dest}.part"
        return 1
    fi
}

# Runs "$@", fails after MAX_FAILURES failures in a row
attempt() {
    label="$1"
    shift
    if "$@"; then
        new=$((new + 1))
        streak=0
        log "Fetched ${label}"
        return 0
    fi

    failed=$((failed + 1))
    streak=$((streak + 1))
    log "Failed to fetch ${label} (see ${LOG})"
    if [ "${streak}" -ge "${MAX_FAILURES}" ]; then
        log "Giving up after ${streak} failures in a row."
        return 1
    fi
}

fetch_orbit_rev() {
    gz="${ORBIT_DIR}/orbit_historic_$1.fits.gz"
    [ -f "${gz}" ] || download "${ORBIT_URL}/$1.001/orbit_historic.fits.gz" "${gz}" || return 1
    unpack "${ORBIT_DIR}/orbit_historic_$1.fits" gunzip -c "${gz}"
}

fetch_ts05_year() {
    name="$1_OMNI_5m_with_TS05_variables"
    dat="${TSYGAN_DIR}/${name}.dat"

    case " ${TS05_PLAIN_YEARS} " in
        *" $1 "*) download "${TS05_URL}/${name}.dat" "${dat}"; return ;;
    esac
    case " ${TS05_LEGACY_YEARS} " in
        *" $1 "*) download "${TS05_LEGACY_URL}/${name}.dat" "${dat}"; return ;;
    esac

    zip="${TSYGAN_DIR}/${name}.zip"
    [ -f "${zip}" ] || download "${TS05_URL}/${name}.zip" "${zip}" || return 1
    unpack "${dat}" unzip -p "${zip}" "${name}.dat"
}

mkdir -p "${ORBIT_DIR}" "${TSYGAN_DIR}" "$(dirname "${LOG}")"

echo "============= FETCHING IREM MAGNETOSPHERE INPUT DATA ============="

log "${SOURCES_STATUS}"

# log "--- Orbit: revolutions ${ORBIT_FIRST}..${ORBIT_LAST} ---"
# new=0 failed=0 streak=0
# for rev in $(seq -f '%04g' "${ORBIT_FIRST}" "${ORBIT_LAST}"); do
#     [ -f "${ORBIT_DIR}/orbit_historic_${rev}.fits" ] && continue
#     attempt "orbit rev ${rev}" fetch_orbit_rev "${rev}" || break
# done
# log "Orbit: ${new} new, ${failed} failed"
#
# log "--- TS05 input: years ${TS05_FIRST}..${TS05_LAST} ---"
# new=0 failed=0 streak=0
# for year in $(seq "${TS05_FIRST}" "${TS05_LAST}"); do
#     [ -f "${TSYGAN_DIR}/${year}_OMNI_5m_with_TS05_variables.dat" ] && continue
#     attempt "TS05 ${year}" fetch_ts05_year "${year}" || break
# done
# log "TS05: ${new} new, ${failed} failed"

printf '\033[32m%s\033[0m\n' "IREM MAGNETOSPHERE INPUT DATA READY"
