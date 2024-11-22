import pandas as pd
import os
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from pathlib import Path


def preprocess_particles(df: pd.DataFrame) -> pd.DataFrame:
    # Convert time
    df['time'] = pd.to_datetime(df['time'])

    # Convert time to ns for InfluxDB
    df['time_ns'] = pd.to_datetime(df['time']).astype('int64')

    # Converts
    df["bin"] = df["bin"].astype("int8")
    df["value"] = df["value"].astype("float64")

    return df


def preprocess_trajectories(df: pd.DataFrame) -> pd.DataFrame:
    df['time'] = pd.to_datetime(df['time'])
    df['time_ns'] = pd.to_datetime(df['time']).astype('int64')
    for column in df.columns:
        if column not in ['time', 'time_ns']:
            df[column] = df[column].astype('float64')
    return df


def convert_trajectories_to_line_protocol(df: pd.DataFrame,
                                          col_name: str) -> pd.DataFrame:
    df = pd.DataFrame(
        col_name +
        ",value=" + df[col_name].astype(str) + " " +
        df['time_ns'].astype(str),
        columns=["line"]
    )
    return df


def convert_particles_to_line_protocol(
        df: pd.DataFrame,
        measurement_name: str) -> pd.DataFrame:
    df = pd.DataFrame(
        measurement_name +
        ",bin=" + df["bin"].astype(str) + " "
        "value=" + df["value"].astype(str) + " " +
        df['time_ns'].astype(str),
        columns=["line"]
    )
    return df


def save_line_protocol(df: pd.DataFrame, filename: Path):
    df.to_csv(filename, index=False, header=False)


def read_line_protocol(filename: Path) -> pd.DataFrame:
    return pd.read_csv(
        str(filename),
        header=None,
        sep='\0',
        names=['line']
    )


class InfluxDbUtils:
    def __init__(self, token: str, org: str, bucket: str, url: str):
        self.token = token
        self.org = org
        self.url = url
        self.bucket = bucket

        self.write_api = self._get_write_api()
        self.buckets_api = self._get_buckets_api()

    def _get_write_api(self) -> influxdb_client.client.write_api:
        client = influxdb_client.InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org
        )

        write_api = client.write_api(write_options=SYNCHRONOUS)
        return write_api

    def _get_buckets_api(self) -> influxdb_client.BucketsApi:
        client = influxdb_client.InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org
        )

        buckets_api = client.buckets_api()
        return buckets_api

    def create_bucket(self) -> influxdb_client.Bucket:
        bucket = self.buckets_api.create_bucket(
            bucket_name=self.bucket, org=self.org)
        return bucket

    def find_bucket_by_name(self) -> influxdb_client.Bucket:
        buckets = self.buckets_api.find_buckets().buckets
        for bucket in buckets:
            if bucket.name == self.bucket:
                return bucket
        return None

    def delete_bucket(self) -> bool:
        bucket = self.find_bucket_by_name()
        if bucket:
            self.buckets_api.delete_bucket(bucket)
            return True
        return False

    def upload_line_protocol(
            self,
            df_lines: pd.DataFrame,
            batch_size: int = 1000000) -> None:
        for batch in range(0, len(df_lines), batch_size):
            batch_end = min(batch + batch_size - 1, len(df_lines) - 1)
            batch_indices = slice(batch, batch_end)

            print(
                f"Uploading batch of {batch_indices.stop - batch_indices.start + 1} records, from {batch_indices.start} to {batch_indices.stop}.", flush=True)
            self.write_api.write(
                self.bucket, self.org, df_lines.loc[batch_indices, 'line'])

        self.write_api.flush()
