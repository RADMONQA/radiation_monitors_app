#!/usr/bin/env python3
"""Publish the IREM magnetosphere HDF5 files to InfluxDB."""

import os
import traceback
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

import influxdb_utils
from irem_magnetosphere_paths import (
    HDF_DIR,
    HDF_KEY,
    MAGFIELD_HDF_PATH,
    ORBIT_HDF_PATH,
    PITCH_ANGLE_HDF_PATH,
)

TOKEN = os.environ.get("INFLUXDB_TOKEN")
URL = os.environ.get("INFLUXDB_URL")
ORG = os.environ.get("INFLUXDB_ORG")
BUCKET = os.environ.get("INFLUXDB_IREM_BUCKET")
REPROCESS_ALL_DATA = os.environ.get("REPROCESS_ALL_DATA", "0") == "1"
CHUNK_ROWS = int(os.environ.get("IREM_CHUNK_ROWS", "500000"))


@dataclass(frozen=True)
class Measurement:
    name: str
    path: Path
    fields: dict[str, str]  # HDF5 column -> InfluxDB field

    @property
    def watermark_path(self) -> Path:
        return HDF_DIR / f".published_{self.name}"

    def read_watermark(self) -> pd.Timestamp | None:
        if REPROCESS_ALL_DATA or not self.watermark_path.exists():
            return None
        try:
            return pd.Timestamp(self.watermark_path.read_text().strip())
        except ValueError:
            return None


def _same_names(*names: str) -> dict[str, str]:
    return {name: name for name in names}


MEASUREMENTS = [
    Measurement("irem_orbit", ORBIT_HDF_PATH, {"distance": "r_distance"}),
    Measurement("irem_magfield", MAGFIELD_HDF_PATH,
                _same_names("bx_gsm", "by_gsm", "bz_gsm", "b_magnitude")),
    Measurement("irem_pitch_angle", PITCH_ANGLE_HDF_PATH,
                _same_names("pitch_angle_cos", "pitch_angle_rad")),
]


def publish(measurement: Measurement, influxdb: influxdb_utils.InfluxDbUtils) -> None:
    name = measurement.name
    if not measurement.path.exists():
        print(f"{name}: no {measurement.path.name}.")
        return

    df = pd.read_hdf(measurement.path, key=HDF_KEY)
    df = df[["time", *measurement.fields]].rename(columns=measurement.fields)
    df["time"] = pd.to_datetime(df["time"])
    if (watermark := measurement.read_watermark()) is not None:
        df = df[df["time"] > watermark]

    fields = list(measurement.fields.values())
    df = influxdb_utils.preprocess_measurement(df, fields).sort_values("time")
    if df.empty:
        print(f"{name}: nothing new to publish.")
        return

    print(f"{name}: uploading {len(df)} rows.")
    for start in range(0, len(df), CHUNK_ROWS):
        chunk = df.iloc[start:start + CHUNK_ROWS]
        influxdb.upload_line_protocol(influxdb_utils.convert_to_line_protocol(chunk, name, fields))

    # Last published time, only new rows are uploaded next run.
    last = df["time"].max()
    measurement.watermark_path.write_text(last.isoformat())
    print(f"{name}: published up to {last}.")


def main() -> int:
    influxdb = influxdb_utils.InfluxDbUtils(token=TOKEN, org=ORG, bucket=BUCKET, url=URL)
    if not influxdb.find_bucket_by_name():
        influxdb.create_bucket()

    failed = []
    for measurement in MEASUREMENTS:
        try:
            publish(measurement, influxdb)
        except Exception:
            failed.append(measurement.name)
            print(f"ERROR publishing {measurement.name}:\n{traceback.format_exc()}")

    if failed:
        print(f"Failed measurements: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
