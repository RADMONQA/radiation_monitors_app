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

## Local Development Setup

The deployed VM environments (`ltp-irem-01.psi.ch`, `ltp-radem-01.psi.ch`) point a few `.env`
variables at directories on the VM's shared disk. To run the same stack locally, copy
`.env.template` to `.env` and point those variables at directories on your own machine instead —
everything else (InfluxDB, Grafana, Prometheus, Elasticsearch data) lives in Docker-managed named
volumes that `docker compose` creates fresh and local automatically, so it needs no changes.

Only these host-path variables differ between the VM and a local checkout:

- `DATA_IREM_RAW_DIR` — local folder with raw IREM CDF data (or a subset copied from the VM).
- `IREM_MAGFIELD_SEED_PATH` — local path to the bundled `magfield_data_full.h5` (defaults to the
  repo root, so usually no change needed if that file is present there).
- `IREM_PITCH_ANGLE_SEED_PATH` — local path to the bundled `irem_magnetic_pitch_angle_full.h5`
  (defaults to the repo root; this is the actual output of a working `03_pitch_angle.ipynb` run,
  so no SPICE/geopack computation is needed for the default seed mode).
- `IREM_KERNELS_SEED_PATH` — only needed if you switch pitch angle to `network` mode (compute
  from scratch instead of using the bundled seed): local path to an extracted directory of
  INTEGRAL SPICE kernels (defaults to `./irem_kernels`).

Steps:

1. Create local data directories, e.g.:

   ```bash
   mkdir -p ~/radmonqa-local-data/irem_raw
   ```

1. In `.env`, point the host-path variables at them:

   ```
   DATA_IREM_RAW_DIR=/home/<you>/radmonqa-local-data/irem_raw
   IREM_MAGFIELD_SEED_PATH=./magfield_data_full.h5
   IREM_MAGFIELD_FETCH_MODE=seed
   IREM_PITCH_ANGLE_SEED_PATH=./irem_magnetic_pitch_angle_full.h5
   IREM_PITCH_ANGLE_FETCH_MODE=seed
   ```

   Leave both fetch modes as `seed` for local development — `network` mode hits real upstream
   ESA/Tsyganenko URLs (magfield) or requires a full local SPICE kernel set (pitch angle), and is
   slow/unreliable for day-to-day work.

1. First-time only — populate those directories with a local copy of the data (this is a manual,
   one-time step; it is not fetched automatically over the network):

   - `magfield_data_full.h5`: copy from a colleague's checkout or from wherever it was
     originally produced (see `02_tsyganenko_geopack.ipynb`).
   - `irem_magnetic_pitch_angle_full.h5`: copy from a colleague's checkout or from wherever it
     was originally produced (see `03_pitch_angle.ipynb`).
   - `DATA_IREM_RAW_DIR`: copy raw IREM data from the VM over the SSH jump-host path documented
     below, e.g.:
     ```bash
     rsync -av -e "ssh -J <username>@hopx.psi.ch" \
       ext-gr@ltp-irem-01.psi.ch:/path/to/irem/raw/ \
       ~/radmonqa-local-data/irem_raw/
     ```

1. Build and run as usual:

   ```bash
   docker compose -f docker-compose.irem.yml up -d --build
   docker compose logs -f app
   ```

1. To force a clean re-publish after replacing local seed data, set `REPROCESS_ALL_DATA=1` in
   `.env`, restart the `app` container, then set it back to `0`.

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

To deploy the RADEM environment, use the following command:

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
