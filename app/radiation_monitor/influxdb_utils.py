import pandas as pd
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


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
    df['time_ns'] = (df['time'] - pd.Timestamp("1970-01-01")
                     ) // pd.Timedelta('1ns')

    for column in df.columns:
        if column not in ['time', 'time_ns']:
            df[column] = df[column].astype('float64')
    return df


def convert_trajectories_to_line_protocol(df: pd.DataFrame,
                                          col_name: str) -> pd.DataFrame:
    measurement = col_name
    value = df[col_name].astype(str)
    ts = df['time_ns'].astype(str)

    df = pd.DataFrame(
        measurement +
        ",bin=" + "1" + " "
        "value=" + value + " " +
        ts,
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
        logger.info(f"Creating bucket {self.bucket}.")
        if self.find_bucket_by_name():
            logger.info(
                f"Bucket {self.bucket} already exists. Skipping creation.")
            return

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
        logger.info(f"Deleting bucket {self.bucket}.")
        bucket = self.find_bucket_by_name()
        if bucket:
            self.buckets_api.delete_bucket(bucket)
            return True
        return False

    @staticmethod
    def _preprocess_df_for_influxdb(df: pd.DataFrame) -> pd.DataFrame:
        # Convert time to ns for influxdb
        df['time_ns'] = (df.index - pd.Timestamp("1970-01-01")
                         ) // pd.Timedelta('1ns')

        # Convert all columns to coresponding influxdb types
        for column in df.columns:
            if df[column].dtype == 'float' or \
                    df[column].dtype == 'float16' or \
                    df[column].dtype == 'float32':
                df[column] = df[column].astype('float64')
            elif df[column].dtype == 'int8' or \
                    df[column].dtype == 'int16' or \
                    df[column].dtype == 'int32' or \
                    df[column].dtype == 'int64':
                df[column] = df[column].astype('int64')
            elif df[column].dtype == 'bool':
                df[column] = df[column].astype('boolean')
        return df

    def upload_df(self, df: pd.DataFrame) -> None:
        self.create_bucket()

        df = InfluxDbUtils._preprocess_df_for_influxdb(df)
        self._upload_line_protocol(df)

    def _convert_row_to_line_protocol(self, measurement: str,
                                      **kwargs) -> str:
        line = f"{measurement}"
        line += " "
        line += ",".join(f"{key}={value}" for key, value in kwargs.items())
        line += " "
        line += f"{kwargs['time_ns']:.0f}"
        return line

    def _convert_to_line_protocol(self,
                                  measurement: str,
                                  df: pd.DataFrame) -> pd.DataFrame:
        time_ns_col = df['time_ns'].astype(str)
        lines = [
            f"{measurement} " +
            ",".join(f"{key}={value}" for key, value in row.items() if key != 'time_ns') +
            f" {time_ns}"
            for row, time_ns in zip(df.to_dict(orient='records'), time_ns_col)
        ]

        df_lines = pd.DataFrame(lines, columns=["line"])
        return df_lines

    def _upload_line_protocol(
            self,
            df: pd.DataFrame,
            batch_size: int = 100000) -> None:
        for batch_start in range(0, len(df), batch_size):
            batch_end = min(batch_start + batch_size - 1, len(df) - 1)

            df_lines = self._convert_to_line_protocol(
                "irem", df.iloc[batch_start:batch_end])

            logger.info(
                f"Uploading batch of {batch_end - batch_start + 1} records, from {batch_start} to {batch_end}.")
            self.write_api.write(
                self.bucket, self.org, df_lines['line'])

        self.write_api.flush()
