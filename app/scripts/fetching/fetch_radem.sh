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
    https://archives.esac.esa.int/psa/repo/ftp-public/Juice/juice_radem/data_raw/ \
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

# For HK files
grep "radem_raw_hk" "${DATA_DIR}/radem/logs/wget_cleaned.log" | \
  xargs cp -t "${DATA_DIR}/radem/extracted/hk/"

# For SC files
grep "radem_raw_sc" "${DATA_DIR}/radem/logs/wget_cleaned.log" | \
  xargs cp -t "${DATA_DIR}/radem/extracted/sc/"

echo "Files copied to processing directory"

HKCOUNT=$(ls ${DATA_DIR}/radem/extracted/hk/ | wc -l)
SCCOUNT=$(ls ${DATA_DIR}/radem/extracted/sc/ | wc -l)

echo "Number of HK files to process: $HKCOUNT"
echo "Number of SC files to process: $SCCOUNT"

#rm wget_cleaned.log