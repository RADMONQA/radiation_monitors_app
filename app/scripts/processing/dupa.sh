#!/bin/bash

# Configuration (set these environment variables or replace with actual values)
INFLUX_TOKEN=${INFLUX_TOKEN:-"verylongtokenforinfluxdb"}
INFLUX_ORG=${INFLUX_ORG:-"radem"}
INFLUX_BUCKET=${INFLUX_BUCKET:-"dupa"}
INFLUX_URL=${INFLUX_URL:-"http://localhost:8186"}
START_TIME=${START_TIME:-"-100y"}

# Create the Flux query
FLUX_QUERY="from(bucket:\"$INFLUX_BUCKET\") |> range(start: $START_TIME)"

# Execute the query
curl --request POST \
    "$INFLUX_URL/api/v2/query?org=$INFLUX_ORG" \
    --header "Authorization: Token $INFLUX_TOKEN" \
    --header "Accept: application/csv" \
    --header "Content-type: application/vnd.flux" \
    --data "$FLUX_QUERY" \
    --output influx_data.csv

if [ $? -eq 0 ]; then
    echo "Data successfully downloaded to influx_data.csv"
else
    echo "Error downloading data"
    exit 1
fi
