#!/usr/bin/env python
# coding: utf-8

# # Level 3: Processing Line Protocol & uploading to InfluxDB

# ## Requirements
#
# 1. [InfluxDB installed](https://www.influxdata.com/downloads/).
# 2. Export InfluxDB API Key in `.env` file.
# 3. Prepare preprocessed CSV data using previous notebook or other tools.

# In[5]:


import pandas as pd
import os
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from pathlib import Path
import time

from dotenv import load_dotenv
load_dotenv("../.env")

os.makedirs("/app_data/radem/line_protocol", exist_ok=True)

DATA_PREROCESSED_DIR = Path("/app_data/radem/csv")
DATA_LINE_PROTOCOL_DIR = Path("/app_data/radem/line_protocol")

TOKEN = os.environ.get("INFLUXDB_TOKEN")
URL = os.environ.get("INFLUXDB_URL")  # "http://localhost:8086"
ORG = os.environ.get("INFLUXDB_ORG")

BUCKET = os.environ.get("INFLUXDB_BUCKET")


print(f"URL: {URL}", flush=True)
print(f"ORG: {ORG}", flush=True)
print(f"BUCKET: {BUCKET}", flush=True)
time.sleep(10)  # wait for InfluxDB to start
print("InfluxDB is ready!", flush=True)


# In[6]:


def get_write_api(url: str = URL, token: str = TOKEN, org: str = ORG):
    client = influxdb_client.InfluxDBClient(
        url=url,
        token=token,
        org=org,
    )

    write_api = client.write_api(write_options=SYNCHRONOUS)

    return write_api


# ### Remove & Clear InfluxDB bucket

# In[7]:


def get_buckets_api(url: str = URL, token: str = TOKEN, org: str = ORG):
    client = influxdb_client.InfluxDBClient(
        url=url,
        token=token,
        org=org
    )

    buckets_api = client.buckets_api()

    return buckets_api


def create_bucket(buckets_api, bucket_name: str, org: str):
    client = influxdb_client.InfluxDBClient(
        url=URL,
        token=TOKEN,
        org=ORG
    )

    buckets_api = client.buckets_api()

    bucket = buckets_api.create_bucket(bucket_name=bucket_name, org=org)

    return bucket


def find_bucket_by_name(buckets_api, bucket_name):
    buckets = buckets_api.find_buckets().buckets
    for bucket in buckets:
        if bucket.name == bucket_name:
            return bucket
    return None


def delete_bucket(buckets_api, bucket_name):
    bucket = find_bucket_by_name(buckets_api, bucket_name)
    if bucket:
        buckets_api.delete_bucket(bucket)
        return True
    return False


# ### Reading preprocessed CSV data

# In[ ]:


def read_temperature(filename: Path) -> pd.DataFrame:
    df = pd.read_csv(str(filename))

    # Convert time
    df['time'] = pd.to_datetime(df['time'])

    # Convert time to ns for InfluxDB
    df['time_ns'] = pd.to_datetime(df['time']).astype('int64')

    # Convert temperatures to int
    df["CEU Temperature (1)"] = df["CEU Temperature (1)"].astype("int64")
    df["P&IDH Temperature (2)"] = df["P&IDH Temperature (2)"].astype("int64")
    df["EDH Temperature (3)"] = df["EDH Temperature (3)"].astype("int64")
    df["DDH Temperature (4)"] = df["DDH Temperature (4)"].astype("int64")
    df["PCU Temperature (5)"] = df["PCU Temperature (5)"].astype("int64")

    return df


def read_particles(filename: Path) -> pd.DataFrame:
    df = pd.read_csv(str(filename))

    # Convert time
    df['time'] = pd.to_datetime(df['time'])

    # Convert time to ns for InfluxDB
    df['time_ns'] = pd.to_datetime(df['time']).astype('int64')

    # Converts
    df["bin"] = df["bin"].astype("int8")
    df["value"] = df["value"].astype("int64")

    return df


def read_flux(filename: Path) -> pd.DataFrame:
    df = pd.read_csv(str(filename))

    # Convert time
    df['time'] = pd.to_datetime(df['time'])

    # Convert time to ns for InfluxDB
    df['time_ns'] = pd.to_datetime(df['time']).astype('int64')

    # Converts
    df["value"] = df["value"].astype("int64")

    return df


# ### Converting DataFrame -> Line Protocol

# In[ ]:


def convert_temp_to_line_protocol(df: pd.DataFrame) -> pd.DataFrame:
    measurements = [
        "temp1_ceu",
        "temp2_pidh",
        "temp3_edh",
        "temp4_ddh",
        "temp5_pcu"
    ]

    labels = [
        "CEU Temperature (1)",
        "P&IDH Temperature (2)",
        "EDH Temperature (3)",
        "DDH Temperature (4)",
        "PCU Temperature (5)"
    ]

    df = pd.concat((
        pd.DataFrame(
            measurement + " " +
            "value=" + df[label].astype(str) + "i " +
            df['time_ns'].astype(str),
            columns=["line"]
        )
        for measurement, label in zip(measurements, labels)
    ), ignore_index=True)
    return df


def convert_particles_to_line_protocol(df: pd.DataFrame, measurement_name: str) -> pd.DataFrame:
    df = pd.DataFrame(
        measurement_name +
        ",bin=" + df["bin"].astype(str) + " "
        "value=" + df["value"].astype(str) + "i " +
        df['time_ns'].astype(str),
        columns=["line"]
    )
    return df


def convert_flux_to_line_protocol(df: pd.DataFrame, measurement_name: str) -> pd.DataFrame:
    df = pd.DataFrame(
        measurement_name +
        " " +
        "value=" + df["value"].astype(str) + "i " +
        df['time_ns'].astype(str),
        columns=["line"]
    )
    return df


# ### Saving Line Protocol file
#
# Example line: `my_measurement,event_type=e,channel=0 value=123 1556813561098000000`
#

# In[ ]:


def save_line_protocol(df: pd.DataFrame, filename: Path):
    df.to_csv(filename, index=False, header=False)


# ### Reading Line Protocol file

# In[ ]:


def read_line_protocol(filename: Path) -> pd.DataFrame:
    return pd.read_csv(
        str(filename),
        header=None,
        sep='\0',
        names=['line']
    )


# ### Upload data to InfluxDB

# In[ ]:


def upload_line_protocol(
        write_api: influxdb_client.WriteApi,
        df_lines: pd.DataFrame,
        bucket: str,
        org: str,
        batch_size: int = 1000000) -> None:
    for batch in range(0, len(df_lines), batch_size):
        batch_end = min(batch + batch_size - 1, len(df_lines) - 1)
        batch_indices = slice(batch, batch_end)

        print(
            f"Uploading batch of {batch_indices.stop - batch_indices.start + 1} records, from {batch_indices.start} to {batch_indices.stop}.", flush=True)

        write_api.write(bucket, org, df_lines.loc[batch_indices, 'line'])

    write_api.flush()


# ## Pipelines

# ### Buckets setup

# In[10]:


buckets_api = get_buckets_api()

# Optionally delete existing bucket
#delete_bucket(buckets_api, BUCKET)

bucket = find_bucket_by_name(buckets_api, BUCKET)
if not bucket:
    create_bucket(buckets_api, BUCKET, ORG)



# ### Temperature

# In[ ]:


# 1. get the newest CSV filename
csv_filename = sorted(DATA_PREROCESSED_DIR.glob("temperature_*.csv"))[-1]

# 2. read the CSV file
df = read_temperature(csv_filename)

# 3. convert the CSV file to line protocol
df_lines = convert_temp_to_line_protocol(df)

# 4. (optional) save the line protocol to a file
line_protocol_filename = DATA_LINE_PROTOCOL_DIR / f"{csv_filename.stem}.line"
save_line_protocol(df_lines, line_protocol_filename)

# 5. upload the line protocol to InfluxDB
write_api = get_write_api(
    url=URL,
    token=TOKEN,
    org=ORG)

upload_line_protocol(
    write_api=write_api,
    df_lines=df_lines,
    bucket=BUCKET,
    org=ORG)


# ### Particles

# In[ ]:


for particle in ["protons", "electrons", "dd", "heavy_ions"]:
    print(f"Uploading {particle} data...", flush=True)

    # 1. get the newest CSV filename
    csv_filename = sorted(DATA_PREROCESSED_DIR.glob(f"{particle}_2*.csv"))[-1]

    # 2. read the CSV file
    df = read_particles(csv_filename)
    print(f"Read {len(df)} records from {csv_filename}", flush=True)

    # 3. convert the CSV file to line protocol
    df_lines = convert_particles_to_line_protocol(df, particle)

    # 4. (optional) save the line protocol to a file
    line_protocol_filename = DATA_LINE_PROTOCOL_DIR / \
        f"{csv_filename.stem}.line"
    save_line_protocol(df_lines, line_protocol_filename)

    # 5. upload the line protocol to InfluxDB
    write_api = get_write_api(
        url=URL,
        token=TOKEN,
        org=ORG)

    upload_line_protocol(
        write_api=write_api,
        df_lines=df_lines,
        bucket=BUCKET,
        org=ORG)

    write_api.close()


# # ### Flux - as of 12.09.2025 data is not available

# # In[ ]:


# for particle in ["protons_flux", "electrons_flux", "dd_flux"]:
#     print(f"Uploading {particle} data...", flush=True)

#     # 1. get the newest CSV filename
#     csv_filename = sorted(DATA_PREROCESSED_DIR.glob(f"{particle}_*.csv"))[-1]

#     # 2. read the CSV file
#     df = read_flux(csv_filename)
#     print(f"Read {len(df)} records from {csv_filename}", flush=True)

#     # 3. convert the CSV file to line protocol
#     df_lines = convert_flux_to_line_protocol(df, particle)

#     # 4. (optional) save the line protocol to a file
#     line_protocol_filename = DATA_LINE_PROTOCOL_DIR / \
#         f"{csv_filename.stem}.line"
#     save_line_protocol(df_lines, line_protocol_filename)

#     # 5. upload the line protocol to InfluxDB
#     write_api = get_write_api(
#         url=URL,
#         token=TOKEN,
#         org=ORG)

#     upload_line_protocol(
#         write_api=write_api,
#         df_lines=df_lines,
#         bucket=BUCKET,
#         org=ORG)

#     write_api.close()
