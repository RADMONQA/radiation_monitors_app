import os
import logging
from pathlib import Path

from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load (optional) environment variables
if not load_dotenv():
    logger.debug("No .env file found")
else:
    logger.debug("Loaded .env file")

# Dir paths
DATA_DIR = Path(os.getenv("DATA_DIR", "../data"))

DATA_IREM_DIR = DATA_DIR / "irem"
DATA_RADEM_DIR = DATA_DIR / "radem"

DATA_IREM_RAW_DIR = DATA_IREM_DIR / "raw"
DATA_IREM_EXTRACTED_DIR = DATA_IREM_DIR / "extracted"
DATA_IREM_HDF5_DIR = DATA_IREM_DIR / "hdf5"
DATA_IREM_CSV_DIR = DATA_IREM_DIR / "csv"

DATA_RADEM_RAW_DIR = DATA_RADEM_DIR / "raw"
DATA_RADEM_EXTRACTED_DIR = DATA_RADEM_DIR / "extracted"
DATA_RADEM_HDF5_DIR = DATA_RADEM_DIR / "hdf5"
DATA_RADEM_CSV_DIR = DATA_RADEM_DIR / "csv"

# File paths
DATA_IREM_HDF5_FILENAME = DATA_IREM_HDF5_DIR / "data_irem.h5"

# Checkpoint
CHECKPOINT_DIR = DATA_DIR

# InfluxDB
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_IREM_BUCKET = os.getenv("INFLUXDB_IREM_BUCKET")
INFLUXDB_RADEM_BUCKET = os.getenv("INFLUXDB_RADEM_BUCKET")
