#!/usr/bin/env sh
#
# Fetches RADEM data from FTP server.

# Build required folder structure

# Contains all downloaded cdfs permanently
mkdir -p ${DATA_DIR}/radem/archive

# Temporary directiories for downloading and processing
mkdir -p ${DATA_DIR}/radem/extracted/hk
mkdir -p ${DATA_DIR}/radem/extracted/sc
mkdir -p ${DATA_DIR}/radem/csv
mkdir -p ${DATA_DIR}/radem/logs

# Download the raw data

echo "Starting RADEM data fetch"

wget \
    --recursive \
    --no-parent \
    --continue \
    --timestamping \
    --no-host-directories \
    --cut-dirs=5 \
    -A cdf \
    https://archives.esac.esa.int/psa/ftp/Juice/juice_radem/data_raw/ \
    -P ${DATA_DIR}/radem/archive \
    -o logfile \
    --output-file=wget.log \
    -nv

echo "RADEM data fetch completed"

# Cleanup the log file

grep -o '"[^"]*\.cdf"' wget.log | sed 's/"//g' > ${DATA_DIR}/radem/logs/wget_cleaned.log

rm wget.log

#Get line count of cleaned log
LINECOUNT=$(wc -l < ${DATA_DIR}/radem/logs/wget_cleaned.log)
echo "Number of files downloaded: $LINECOUNT"
echo "Copying files to processing directory"

# Get all downloaded files and copy them to the processing directory
if [ "${REPROCESS_ALL_DATA}" = "1" ]; then
    echo "REPROCESS_ALL_DATA=1 -> copying all archived CDFs to extracted folders"

    HK_ARCHIVE_COUNT=$(find "${DATA_DIR}/radem/archive" -type f -name "radem_raw_hk_*.cdf" | wc -l)
    SC_ARCHIVE_COUNT=$(find "${DATA_DIR}/radem/archive" -type f -name "radem_raw_sc_*.cdf" | wc -l)

    echo "Archive HK files: ${HK_ARCHIVE_COUNT}"
    echo "Archive SC files: ${SC_ARCHIVE_COUNT}"

    if [ "${HK_ARCHIVE_COUNT}" -gt 0 ]; then
        find "${DATA_DIR}/radem/archive" -type f -name "radem_raw_hk_*.cdf" -print0 | \
          xargs -0 -I {} cp {} "${DATA_DIR}/radem/extracted/hk/"
    fi

    if [ "${SC_ARCHIVE_COUNT}" -gt 0 ]; then
        find "${DATA_DIR}/radem/archive" -type f -name "radem_raw_sc_*.cdf" -print0 | \
          xargs -0 -I {} cp {} "${DATA_DIR}/radem/extracted/sc/"
    fi
else
    echo "Using latest downloaded files from wget log"
    # For HK files
    grep "radem_raw_hk" "${DATA_DIR}/radem/logs/wget_cleaned.log" | \
      awk '{print $NF}' | \
      xargs -I {} cp {} "${DATA_DIR}/radem/extracted/hk/"

    # For SC files
    grep "radem_raw_sc" "${DATA_DIR}/radem/logs/wget_cleaned.log" | \
      awk '{print $NF}' | \
      xargs -I {} cp {} "${DATA_DIR}/radem/extracted/sc/"
fi

echo "Files copied to processing directory"

HKCOUNT=$(ls ${DATA_DIR}/radem/extracted/hk/ | wc -l)
SCCOUNT=$(ls ${DATA_DIR}/radem/extracted/sc/ | wc -l)

echo "Number of HK files to process: $HKCOUNT"
echo "Number of SC files to process: $SCCOUNT"

#rm wget_cleaned.log
