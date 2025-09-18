# RADMONQA App

## (previously named Radiation Monitor)

RADMONQA App is a web application that allows users to visualize and analyze the data collected by the IREM and RADEM detectors as well as the data collected by the other services running on the host machine. It includes Prometheus and the ELK stack for the convenience of administrators and users.

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
1. Run the docker containers in the background in either IREM or RADEM mode:

   ```bash
   docker compose -f docker-compose.irem.yml up -d
   ```

   or

   ```bash
   docker compose -f docker-compose.radem.yml up -d
   ```

1. Visit the application in your browser at `http://localhost:80`
1. Stop the docker containers
   ```bash
   docker compose down
   ```

## Target Environments

### IREM Environment

This environment is made for deployment on the `http://ltp-irem-01.psi.ch/` virtual machine - it displays countrate data from IREM aboard INTEGRAL space telescope.

- **Configuration File**: `docker-compose.irem.yml`
- **Data**: IREM data only

To deploy this environment, use the following command:

```bash
docker compose -f docker-compose.irem.yml up -d
```

### RADEM Environment

This environment is made for deployment on the `http://ltp-radem-01.psi.ch/` virtual machine - it displays countrate data from all channels on RADEM aboard JUICE ESA's mission. It also includes some of the housekeeping data.

- **Configuration File**: `docker-compose.radem.yml`
- **Data**: RADEM science and housekeeping data

To deploy the legacy environment, use the following command:

```bash
docker compose -f docker-compose.radem.yml up -d
```

## Services

| **Service**   | **Host's port** | **Description**                                                                                   |
| ------------- | --------------- | ------------------------------------------------------------------------------------------------- |
| App           | -               | The main service that fetches the data from the external sources and stores it in the database.   |
| InfluxDB      | `8186`          | The time series database that stores the data collected by the RADEM detector.                    |
| Grafana       | `80`            | The visualization tool that allows users to visualize the data collected by the RADEM detector.   |
| Prometheus    | `9090`          | The monitoring system that collects metrics from the host machine and the services running on it. |
| Node Exporter | `9100`          | The service that collects metrics from the host machine.                                          |
| cAdvisor      | `8080`          | The service that collects metrics from the host machine and the services running on it.           |
| Elasticsearch | `9200`          | Search and analytics engine, stores data.                                                         |
| Logstash      | `5000/udp`      | Data processing pipeline, ingests logs via UDP on port 5000.                                      |
| Kibana        | `5601`          | Web UI for visualizing and exploring Elasticsearch data.                                          |

---

**Tip for developers**: To access the virtual machine running this application in IREM mode (ltp-irem-01.psi.ch), use the following SSH command, replacing `<username>` with your actual PSI credentials:

```bash
ssh -J <username>@hopx.psi.ch -L 30080:ltp-irem-01.psi.ch:80 -L 5601:ltp-irem-01.psi.ch:5601 ext-gr
```
