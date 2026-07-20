#!/usr/bin/env python3
"""Load IREM pitch-angle HDF5 data into InfluxDB."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

import influxdb_utils

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "/app_data"))
PITCH_ANGLE_HDF_PATH = DATA_DIR / "irem" / "pitch_angle" / "pitch_angle_data.h5"
PUBLISH_STATE_PATH = DATA_DIR / "irem" / "pitch_angle" / "last_published_mtime"

TOKEN = os.environ.get("INFLUXDB_TOKEN")
URL = os.environ.get("INFLUXDB_URL")
ORG = os.environ.get("INFLUXDB_ORG")
BUCKET = os.environ.get("INFLUXDB_IREM_BUCKET")
REPROCESS_ALL_DATA = os.getenv("REPROCESS_ALL_DATA", "0") == "1"
PITCH_ANGLE_CHUNK_ROWS = int(os.getenv("IREM_PITCH_ANGLE_CHUNK_ROWS", "500000"))


def _needs_publish() -> bool:
    if not PITCH_ANGLE_HDF_PATH.exists():
        print(f"No pitch-angle HDF found at {PITCH_ANGLE_HDF_PATH}; skipping publish.")
        return False

    if REPROCESS_ALL_DATA:
        return True

    hdf_mtime = PITCH_ANGLE_HDF_PATH.stat().st_mtime
    if not PUBLISH_STATE_PATH.exists():
        return True

    last_published = float(PUBLISH_STATE_PATH.read_text().strip())
    return hdf_mtime > last_published


def main() -> None:
    if not _needs_publish():
        print("Pitch angle Influx publish skipped; data already published.")
        return

    print(f"Loading pitch-angle HDF from {PITCH_ANGLE_HDF_PATH}")
    df = pd.read_hdf(PITCH_ANGLE_HDF_PATH, key="df")
    df = df.sort_values("time")

    influxdb = influxdb_utils.InfluxDbUtils(
        token=TOKEN,
        org=ORG,
        bucket=BUCKET,
        url=URL,
    )
    if not influxdb.find_bucket_by_name():
        influxdb.create_bucket()

    preprocessed = influxdb_utils.preprocess_pitch_angle(df)
    print(f"Uploading {len(preprocessed)} pitch-angle rows to InfluxDB...")

    for start in range(0, len(preprocessed), PITCH_ANGLE_CHUNK_ROWS):
        chunk = preprocessed.iloc[start : start + PITCH_ANGLE_CHUNK_ROWS]
        line_protocol = influxdb_utils.convert_pitch_angle_to_line_protocol(chunk)
        influxdb.upload_line_protocol(line_protocol)

    PUBLISH_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PUBLISH_STATE_PATH.write_text(str(PITCH_ANGLE_HDF_PATH.stat().st_mtime))
    print("Pitch angle data published successfully.")


if __name__ == "__main__":
    main()
