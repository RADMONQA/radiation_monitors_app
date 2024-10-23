# RADEM App

RADEM App is a web application that allows users to visualize and analyze the data collected by the RADEM detector.

## Prerequisites

- Docker

## Installation
1. Copy the `.env.example` file to `.env` and update the values as needed.
    ```bash
    $ cp .env.example .env
    ```

1. Build the docker image
    ```bash
    $ docker compose build
    ```
2. Run the docker containers in the background
    ```bash
    $ docker compose up -d
    ```
3. Visit the application in your browser at `http://localhost:81`

## Containers

| **Service**     | **Host's port** |
|-----------------|-----------------|
| RADEM Fetcher   | -               |
| RADEM Publisher | -               |
| InfluxDB        | 8186            |
| Grafana         | 81              |
| Prometheus      | 9090            |
| Node Exporter   | 9100            |
| cAdvisor        | 8080            |


### RADEM Fetcher

Service fetching the data.
 * periodically fetch data available on external locations (cron job)
  * RADEM data (FTP connection)
  * IREM data (publicly available)
* store the data in DATA_DIR, which is shared with other containers

### RADEM Publisher

### InfluxDB

### Grafana

### Prometheus

### Node Exporter

### cAdvisor
