#!/usr/bin/env sh
#
# Fetches RADEM data from FTP server.

# Build required folder structure
mkdir -p ${DATA_DIR}/radem
mkdir -p ${DATA_DIR}/radem/raw
mkdir -p ${DATA_DIR}/radem/extracted
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
