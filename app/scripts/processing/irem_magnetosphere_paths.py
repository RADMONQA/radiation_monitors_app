"""Paths of the IREM magnetosphere pipeline (see README)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MAGNETOSPHERE_DIR = Path(os.getenv("DATA_DIR", "/app_data")) / "irem" / "magnetosphere"
ORBIT_DIR = MAGNETOSPHERE_DIR / "orbit"
TSYGAN_INPUT_DIR = MAGNETOSPHERE_DIR / "tsygan_input"
KERNELS_DIR = MAGNETOSPHERE_DIR / "kernels"
HDF_DIR = MAGNETOSPHERE_DIR / "hdf"

ORBIT_HDF_PATH = HDF_DIR / "orbit_data.h5"
MAGFIELD_HDF_PATH = HDF_DIR / "magfield_data.h5"
PITCH_ANGLE_HDF_PATH = HDF_DIR / "pitch_angle_data.h5"

HDF_KEY = "df"
