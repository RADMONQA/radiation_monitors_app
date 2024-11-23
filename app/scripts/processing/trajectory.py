#!/usr/bin/env python
from planetary_coverage import TourConfig
import pandas as pd
from datetime import datetime
from pathlib import Path
import os

import influxdb_utils

DATA_DIR = Path(os.getenv('DATA_DIR', '.'))

KERNELS_DIR = os.getenv('KERNELS_DIR', './spice')
KERNELS_MK = os.getenv('KERNELS_MK', '5.1 150lb_23_1')
KERNELS_VERSION = os.getenv('KERNELS_VERSION', 'v451')

START_DATE = datetime(2023, 9, 1)
END_DATE = datetime(2033, 9, 1)
INTERVAL_HOURS = 12

TOKEN = "verylongtokenforinfluxdb"  # os.environ.get("INFLUXDB_TOKEN")
URL = "http://localhost:8186"  # os.environ.get("INFLUXDB_URL")
ORG = "radem"  # os.environ.get("INFLUXDB_ORG")
BUCKET = "dupadupa"


# def build_juice_tour(target):
#     return TourConfig(
#         spacecraft='JUICE',
#         target=target,
#         download_kernels=True,
#         kernels_dir=KERNELS_DIR,
#         mk=KERNELS_MK,
#         version=KERNELS_VERSION,
#     )


# def build_trajectory(tour):
#     return tour[START_DATE: END_DATE: f'{INTERVAL_HOURS} hours']


# def km_to_au(km):
#     return km * 6.68459e-9


# sun_tour = build_juice_tour('SUN')
# earth_tour = build_juice_tour('EARTH')
# mars_tour = build_juice_tour('MARS')
# jupiter_tour = build_juice_tour('JUPITER')

# sun_traj = build_trajectory(sun_tour)
# earth_traj = build_trajectory(earth_tour)
# mars_traj = build_trajectory(mars_tour)
# jupiter_traj = build_trajectory(jupiter_tour)

# sun_dist = km_to_au(sun_traj.dist)
# earth_dist = km_to_au(earth_traj.dist)
# mars_dist = km_to_au(mars_traj.dist)
# jupiter_dist = km_to_au(jupiter_traj.dist)

# sun_ra = sun_traj.ra
# earth_ra = earth_traj.ra
# mars_ra = mars_traj.ra
# jupiter_ra = jupiter_traj.ra

# sun_dec = sun_traj.dec
# earth_dec = earth_traj.dec
# mars_dec = mars_traj.dec
# jupiter_dec = jupiter_traj.dec

# df = pd.DataFrame({
#     'time': sun_traj.utc,
#     'sun_dist_au': sun_dist,
#     'earth_dist_au': earth_dist,
#     'mars_dist_au': mars_dist,
#     'jupiter_dist_au': jupiter_dist,
#     'sun_ra': sun_ra,
#     'earth_ra': earth_ra,
#     'mars_ra': mars_ra,
#     'jupiter_ra': jupiter_ra,
#     'sun_dec': sun_dec,
#     'earth_dec': earth_dec,
#     'mars_dec': mars_dec,
#     'jupiter_dec': jupiter_dec,
# })

# df.to_csv(DATA_DIR / 'juice_trajectory.csv', index=False)

df = pd.read_csv('./juice_trajectory.csv')

print("Done!")

COLUMNS = [
    'sun_dist_au',
    'earth_dist_au',
    'mars_dist_au',
    'jupiter_dist_au',
    'sun_ra',
    'earth_ra',
    'mars_ra',
    'jupiter_ra',
    'sun_dec',
    'earth_dec',
    'mars_dec',
    'jupiter_dec',
]


influxdb = influxdb_utils.InfluxDbUtils(
    token=TOKEN,
    org=ORG,
    bucket=BUCKET,
    url=URL,
)

# line_protocol = pd.DataFrame({
#     "line": [
#         "earth_dist_au value=0.19808306428397512 1693526400000000000",
#         "earth_dist_au value=0.19796976975636563 1693569600000000000",
#         "earth_dist_au value=0.1978467525898514 1693612800000000000",
#     ]
# })


if not influxdb.find_bucket_by_name():
    influxdb.create_bucket()

for col in COLUMNS:
    preprocessed = influxdb_utils.preprocess_trajectories(df)
    line_protocol = influxdb_utils.convert_trajectories_to_line_protocol(
        preprocessed, col)
    influxdb.upload_line_protocol(line_protocol)

print("Done!")
