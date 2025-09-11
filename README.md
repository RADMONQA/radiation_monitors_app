# RADMONQA App 
## (previously named Radiation Monitor)

RADMONQA App is a web application that allows users to visualize and analyze the data collected by the IREM detector as well as the data collected by the other services running on the host machine.

[legacy - probably doesn't work as of now: 👉 LIVE DEMO WITH IREM DATA(http://149.156.10.136:51820/) at Cyfronet C3 cloud.]: # 

## Prerequisites

- Docker
- Docker Compose
- git

## Installation

1. Copy the `.env.template` file to `.env` and update the values as needed.
    ```bash
    cp .env.template .env
    ```

1. Build the docker image
    ```bash
    docker compose build
    ```
2. Run the docker containers in the background
    ```bash
    docker compose up -d
    ```
3. Visit the application in your browser at `http://localhost:51820`
4. Stop the docker containers
    ```bash 
    docker compose down
    ```

## Target Environments

### Default Environment

The default environment is configured for public access and includes only the IREM data. This setup is intended for users who need access to publicly available data.

- **Configuration File**: `docker-compose.yml`
- **Data**: IREM data only.

To deploy the public environment, use the following command:
```bash
docker compose -f docker-compose.yml up -d
```

### Legacy Environment (previously called private)

The private environment used to include both IREM and RADEM data, the second of which is not officially published as of time of writing (24.07.2025). This setup is intended for testing the legacy code which used past RADEM data and is not recommended as of now.

- **Configuration File**: `docker-compose.legacy.yml`
- **Data**: IREM and RADEM data.


To deploy the legacy environment, use the following command:
```bash
docker compose -f docker-compose.legacy.yml up -d
```


## Services

| **Service**     | **Host's port** | **Description** |
|-----------------|-----------------|-----------------|
| App             | `80` for admin, `51820` for public | The main service that fetches the data from the external sources and stores it in the database. |   
| InfluxDB        | `8186`            | The time series database that stores the data collected by the RADEM detector. |
| Grafana         | `81`              | The visualization tool that allows users to visualize the data collected by the RADEM detector. |
| Prometheus      | `9090`            | The monitoring system that collects metrics from the host machine and the services running on it. |
| Node Exporter   | `9100`            | The service that collects metrics from the host machine. |
| cAdvisor        | `8080`            | The service that collects metrics from the host machine and the services running on it. |
| Elasticsearch   | `9200`            | Search and analytics engine, stores data.        |
| Logstash        | `5000/udp`        | Data processing pipeline, ingests logs via UDP on port 5000.                 |
| Kibana          | `5601`            | Web UI for visualizing and exploring Elasticsearch data.                    |

---

**Tip for developers**: To access the virtual machine running this application in IREM mode (ltp-irem-01.psi.ch), use the following SSH command, replacing `<username>` with your actual PSI credentials:
```bash
ssh -J <username>@hopx.psi.ch -L 30080:ltp-irem-01.psi.ch:80 -L 5601:ltp-irem-01.psi.ch:5601 ext-gr
```