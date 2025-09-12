#!/usr/bin/env sh
#
# Fetches RADEM data from FTP server.

# Build required folder structure
mkdir -p ${DATA_DIR}/radem/extracted/hk
mkdir -p ${DATA_DIR}/radem/extracted/sc
mkdir -p ${DATA_DIR}/radem/csv

# TODO - replace with current HTTP link - FTP is deprecated

# # Fetch data from ftp
# wget -r \
#     --timestamping \
#     --continue \
#     --user=${FTP_USER} \
#     --password=${FTP_PASSWORD} \
#     ${FTP_URL} \
#     -nd \
#     -np \
#     -P ${DATA_DIR}/radem/raw\


# Download the raw data

wget \
    --recursive \
    --no-parent \
    --continue \
    --no-clobber \
    --no-host-directories \
    --cut-dirs=5 \
    -A cdf \
    https://archives.esac.esa.int/psa/repo/ftp-public/Juice/juice_radem/data_raw/ \
    -P /app_data/data_radem

# Copy the newly downloaded raw data to the processing directory

find /app_data/data_radem/data_raw -type f -name "radem_raw_hk*" -print0 | xargs -0 -Ifilepath mv filepath /app_data/radem/extracted/hk
find /app_data/data_radem/data_raw -type f -name "radem_raw_sc*" -print0 | xargs -0 -Ifilepath mv filepath /app_data/radem/extracted/sc

# Clean up the download directory

rm -rf /app_data/data_radem