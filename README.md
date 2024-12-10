# RADEM App

RADEM App is a web application that allows users to visualize and analyze the data collected by the RADEM detector as well as the data collected by the other services running on the host machine.

[👉 LIVE DEMO](http://149.156.10.136:51820/)

## Prerequisites

- Docker
- Docker Compose

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
4. Stop the docker containers
    ```bash 
    $ docker compose down
    ```

## Services

| **Service**     | **Host's port** | **Description** |
|-----------------|-----------------|-----------------|
| App             | 81              | The main service that fetches the data from the external sources and stores it in the database. |   
| InfluxDB        | 8186            | The time series database that stores the data collected by the RADEM detector. |
| Grafana         | 81              | The visualization tool that allows users to visualize the data collected by the RADEM detector. |
| Prometheus      | 9090            | The monitoring system that collects metrics from the host machine and the services running on it. |
| Node Exporter   | 9100            | The service that collects metrics from the host machine. |
| cAdvisor        | 8080            | The service that collects metrics from the host machine and the services running on it. |

## App

The App is the main service that runs the periodic jobs that fetch the data from the external sources and store it in the database.