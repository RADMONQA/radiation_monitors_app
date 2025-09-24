#!/usr/bin/env sh
# This file logs the results of the processing to a .csv log 
# and deletes all of the temporary/intermediate files


echo "Starting log and cleanup"

# Create the log file with header if it doesn't exist
mkdir -p /app_data/radem/logs && touch /app_data/radem/logs/download_log.csv

if [ ! -s /app_data/radem/logs/download_log.csv ]; then
    echo "id,timestamp,path,sha256_checksum" >> /app_data/radem/logs/download_log.csv
fi

DATETIME=$(date -u +"%Y-%m-%d %T")

# Determine the next ID taking into account an empty or non-existent log file
if [ -s /app_data/radem/logs/download_log.csv ]; then
    LAST_ID=$(tail -n 1 /app_data/radem/logs/download_log.csv | cut -d',' -f1)
    if echo "$LAST_ID" | grep -qE '^[0-9]+$'; then
        CURRENT_ID=$((LAST_ID + 1))
    else
        CURRENT_ID=1
    fi
else
    CURRENT_ID=1
fi

# Loop through all lines in the cleaned wget log
while IFS= read -r line; do
    FILEPATH="$line"
    CHECKSUM=$(sha256sum "$FILEPATH" | awk '{print $1}')
    echo "$CURRENT_ID,$DATETIME,$FILEPATH,$CHECKSUM" >> /app_data/radem/logs/download_log.csv
    echo "Logged file with ID $CURRENT_ID: $FILEPATH with checksum $CHECKSUM"
    CURRENT_ID=$((CURRENT_ID + 1))

done < ../wget_cleaned.log

# Cleanup temporary and intermediate files
rm -rf /app_data/radem/extracted/hk/*
rm -rf /app_data/radem/extracted/sc/*
rm -rf /app_data/radem/csv/*
rm -rf /app_data/radem/line_protocol/*

rm ../wget_cleaned.log

echo "Log and cleanup completed"