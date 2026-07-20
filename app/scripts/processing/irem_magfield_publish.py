#!/usr/bin/env python3
"""Load modeled IREM magnetic field HDF5 data into InfluxDB."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

import influxdb_utils

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "/app_data"))
MAGFIELD_HDF_PATH = DATA_DIR / "irem" / "magfield" / "magfield_data.h5"
PUBLISH_STATE_PATH = DATA_DIR / "irem" / "magfield" / "last_published_mtime"

TOKEN = os.environ.get("INFLUXDB_TOKEN")
URL = os.environ.get("INFLUXDB_URL")
ORG = os.environ.get("INFLUXDB_ORG")
BUCKET = os.environ.get("INFLUXDB_IREM_BUCKET")
REPROCESS_ALL_DATA = os.getenv("REPROCESS_ALL_DATA", "0") == "1"
MAGFIELD_CHUNK_ROWS = int(os.getenv("IREM_MAGFIELD_CHUNK_ROWS", "500000"))


def _needs_publish() -> bool:
    if not MAGFIELD_HDF_PATH.exists():
        print(f"No magfield HDF found at {MAGFIELD_HDF_PATH}; skipping publish.")
        return False

    if REPROCESS_ALL_DATA:
        return True

    hdf_mtime = MAGFIELD_HDF_PATH.stat().st_mtime
    if not PUBLISH_STATE_PATH.exists():
        return True

    last_published = float(PUBLISH_STATE_PATH.read_text().strip())
    return hdf_mtime > last_published


def main() -> None:
    if not _needs_publish():
        print("Magfield Influx publish skipped; data already published.")
        return

    print(f"Loading magfield HDF from {MAGFIELD_HDF_PATH}")
    df = pd.read_hdf(MAGFIELD_HDF_PATH, key="df")
    df = df.sort_values("time")

    influxdb = influxdb_utils.InfluxDbUtils(
        token=TOKEN,
        org=ORG,
        bucket=BUCKET,
        url=URL,
    )
    if not influxdb.find_bucket_by_name():
        influxdb.create_bucket()

    preprocessed = influxdb_utils.preprocess_magfield(df)
    print(f"Uploading {len(preprocessed)} magfield rows to InfluxDB...")

    for start in range(0, len(preprocessed), MAGFIELD_CHUNK_ROWS):
        chunk = preprocessed.iloc[start : start + MAGFIELD_CHUNK_ROWS]
        line_protocol = influxdb_utils.convert_magfield_to_line_protocol(chunk)
        influxdb.upload_line_protocol(line_protocol)

    PUBLISH_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PUBLISH_STATE_PATH.write_text(str(MAGFIELD_HDF_PATH.stat().st_mtime))
    print("Magfield data published successfully.")


if __name__ == "__main__":
    main()
