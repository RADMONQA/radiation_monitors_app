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

To run the stack on your own machine, copy `.env.template` to `.env`. Only one value is different
from the VM: `DATA_IREM_RAW_DIR`, the folder with the raw IREM CDF files. All other data is in
Docker named volumes.

1. Make a local data folder and set `DATA_IREM_RAW_DIR` to it in `.env`:

   ```bash
   mkdir -p ~/radmonqa-local-data/irem_raw
   ```

1. Copy raw IREM data from the VM (first time only):

   ```bash
   rsync -av -e "ssh -J <username>@hopx.psi.ch" \
     ext-gr@ltp-irem-01.psi.ch:/path/to/irem/raw/ \
     ~/radmonqa-local-data/irem_raw/
   ```

1. Build and run:

   ```bash
   docker compose -f docker-compose.irem.yml up -d --build
   docker compose logs -f app
   ```

1. To publish all data again, set `REPROCESS_ALL_DATA=1` in `.env`, restart the `app` container,
   then set it back to `0`.

## IREM Magnetosphere Pipeline

The IREM environment also shows where INTEGRAL was in the magnetosphere and how IREM pointed
relative to the magnetic field. All files of this pipeline are in the `magnetosphere` subfolder of
`DATA_IREM_RAW_DIR`:

```
$DATA_IREM_RAW_DIR/
  <year folders of IREM CDFs>
  magnetosphere/
    orbit/          orbit_historic_NNNN.fits(.gz)              from ISDC
    tsygan_input/   YYYY_OMNI_5m_with_TS05_variables.dat(.zip) from Tsyganenko's site
    kernels/        INTEGRAL SPICE kernels                     copied by hand
    archive/        original input files, kept for reference   not used by the pipeline
    logs/           download.log
    hdf/            orbit_data.h5, magfield_data.h5, pitch_angle_data.h5
```

**The downloads are off.** On 2026-09-25 the ISDC orbit archive did not respond and the
Tsyganenko site blocked access (HTTP 410). `fetch_irem_magnetosphere.sh` only prints this message.
The download code is kept, commented out, for a future source. Until then, production uses HDF5
files that were computed on a local machine and copied into `hdf/`.

`app/scripts/processing/irem_magnetosphere_process.py` builds the files in `hdf/`. InfluxDB gets
its data only from these files:

| HDF5                  | Input                    | Measurement        | Fields                                           |
| --------------------- | ------------------------ | ------------------ | ------------------------------------------------ |
| `orbit_data.h5`       | orbit FITS               | `irem_orbit`       | `r_distance` (Earth radii)                       |
| `magfield_data.h5`    | orbit + TS05 input       | `irem_magfield`    | `bx_gsm`, `by_gsm`, `bz_gsm`, `b_magnitude` (nT) |
| `pitch_angle_data.h5` | magfield + SPICE kernels | `irem_pitch_angle` | `pitch_angle_cos`, `pitch_angle_rad`             |

- `irem_magfield` is the external field of the Tsyganenko T04 model only, without IGRF.
- Grafana converts `pitch_angle_rad` to degrees.
- A stage without input is skipped. A stage that fails does not stop the other stages or the
  publishing. The distance needs only the orbit, so it is shown also when the model stages cannot
  run.
- A stage only computes the rows after the last row with a value in its HDF5 file. Thus, a
  precomputed HDF5 file in `hdf/` is not computed again. `REPROCESS_ALL_DATA=1` publishes the files
  again but does not compute them again (a full computation takes hours).
- Input that is added for a time in the middle of the file (for example, a missing TS05 year) is
  not used. To use it, delete `magfield_data.h5` and `pitch_angle_data.h5` and compute again.
- Some TS05 years are published as plain `.dat` files, not zips. These are listed in
  `TS05_PLAIN_YEARS` and `TS05_LEGACY_YEARS` in `fetch_irem_magnetosphere.sh`.
- The SPICE kernels cannot be downloaded (ESA's archive needs credentials). Copy the kernel folder
  into `magnetosphere/kernels/`. The custom GSE frame is in
  `app/scripts/processing/spice_kernels/gse.tf`.

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
