# Radiation Monitor App

Radiation Monitor App is a web application that allows users to visualize and analyze the data collected by the RADEM and IREM detectors as well as the data collected by the other services running on the host machine.

[👉 LIVE DEMO WITH IREM DATA](http://149.156.10.136:51820/) at Cyfronet C3 cloud.

## Prerequisites

- Docker
- Docker Compose
- git

## Installation

1. Copy the `.env.template` file to `.env` and update the values as needed.
    ```bash
    $ cp .env.template .env
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
4. Stop the docker containers
    ```bash 
    $ docker compose down
    ```

## Target Environments

### Private Environment (default)

The private environment includes both IREM and RADEM data, which is not officially published. This setup is intended for internal use and requires appropriate external access

- **Configuration File**: `docker-compose.private.yml`
- **Data**: IREM and RADEM data.


To deploy the private environment, use the following command:
```bash
$ docker compose -f docker-compose.private.yml up -d
```

### Public Environment

The public environment is configured for public access and includes only the IREM data. This setup is intended for users who need access to publicly available data.

- **Configuration File**: `docker-compose.public.yml`
- **Data**: IREM data only.

To deploy the public environment, use the following command:
```bash
$ docker compose -f docker-compose.public.yml up -d
```
## Services

| **Service**     | **Host's port** | **Description** |
|-----------------|-----------------|-----------------|
| App             | `81` for private, `51820` for public | The main service that fetches the data from the external sources and stores it in the database. |   
| InfluxDB        | `8186`            | The time series database that stores the data collected by the RADEM detector. |
| Grafana         | `81`              | The visualization tool that allows users to visualize the data collected by the RADEM detector. |
| Prometheus      | `9090`            | The monitoring system that collects metrics from the host machine and the services running on it. |
| Node Exporter   | `9100`            | The service that collects metrics from the host machine. |
| cAdvisor        | `8080`            | The service that collects metrics from the host machine and the services running on it. |

## App

The App is the main service that runs the periodic jobs that fetch the data from the external sources and store it in the database.
