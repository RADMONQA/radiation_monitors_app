#!/usr/bin/env python3
"""Compute IREM pitch angle (boresight vs. modeled B field) HDF5."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "/app_data"))
MAGFIELD_HDF_PATH = DATA_DIR / "irem" / "magfield" / "magfield_data.h5"
KERNELS_DIR = DATA_DIR / "irem" / "kernels"
KERNELS_STAMP_PATH = KERNELS_DIR / ".staged_from"
PITCH_ANGLE_SEED_PATH = DATA_DIR / "irem" / "pitch_angle" / "pitch_angle_full.h5"
PITCH_ANGLE_HDF_PATH = DATA_DIR / "irem" / "pitch_angle" / "pitch_angle_data.h5"
GSE_KERNEL_PATH = Path(__file__).resolve().parent / "spice_kernels" / "gse.tf"

# Recognized NAIF kernel file extensions (spk, ck, sclk, lsk, pck, fk, ik).
KERNEL_EXTENSIONS = {".bsp", ".bc", ".tsc", ".tls", ".tpc", ".bpc", ".tf", ".ti"}

FETCH_MODE = os.getenv("IREM_PITCH_ANGLE_FETCH_MODE", "seed")
INTERVAL_MINUTES = int(os.getenv("IREM_PITCH_ANGLE_INTERVAL_MINUTES", "5"))
REPROCESS_ALL_DATA = os.getenv("REPROCESS_ALL_DATA", "0") == "1"

# IREM is mounted on the spacecraft pointing towards -Z of the spacecraft frame.
IREM_BORESIGHT_SC = [0, 0, -1]
FROM_FRAME = "INTEGRAL_SPACECRAFT"
TO_FRAME = "GSE"


def _newest_mtime(paths: list[Path]) -> float | None:
    mtimes = [path.stat().st_mtime for path in paths if path.exists()]
    return max(mtimes) if mtimes else None


def _needs_rebuild(output_path: Path, input_paths: list[Path]) -> bool:
    if REPROCESS_ALL_DATA or not output_path.exists():
        return True
    output_mtime = output_path.stat().st_mtime
    input_mtime = _newest_mtime(input_paths)
    return input_mtime is not None and input_mtime > output_mtime


def _write_output(df: pd.DataFrame) -> None:
    PITCH_ANGLE_HDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_hdf(
        PITCH_ANGLE_HDF_PATH,
        key="df",
        mode="w",
        format="table",
        complevel=1,
    )
    print(f"Wrote pitch-angle HDF: {PITCH_ANGLE_HDF_PATH} ({len(df)} rows)")


def build_from_seed() -> None:
    """Derive the published schema from a bundled 03_pitch_angle.ipynb output.

    No SPICE/geopack computation needed here - the seed HDF5 already contains
    pitch_angle_cos/pitch_angle_rad, computed offline from real INTEGRAL SPICE
    kernels. This just selects the relevant columns and adds a degrees field.
    """
    if not PITCH_ANGLE_SEED_PATH.exists():
        raise FileNotFoundError(f"Missing pitch-angle seed HDF: {PITCH_ANGLE_SEED_PATH}")

    if not _needs_rebuild(PITCH_ANGLE_HDF_PATH, [PITCH_ANGLE_SEED_PATH]):
        print(f"Skipping pitch-angle HDF rebuild; up to date: {PITCH_ANGLE_HDF_PATH}")
        return

    print(f"Loading pitch-angle seed from {PITCH_ANGLE_SEED_PATH}")
    seed_df = pd.read_hdf(PITCH_ANGLE_SEED_PATH, key="df")
    seed_df["time"] = pd.to_datetime(seed_df["time"])

    output_df = pd.DataFrame(
        {
            "time": seed_df["time"],
            "pitch_angle_cos": seed_df["pitch_angle_cos"],
            "pitch_angle_rad": seed_df["pitch_angle_rad"],
            "pitch_angle_deg": np.degrees(seed_df["pitch_angle_rad"]),
        }
    )
    _write_output(output_df)


def _load_kernels() -> None:
    import spiceypy as spice

    import geopack_bootstrap

    # geopack.geopack tries to download IGRF coefficients over the network at
    # import time; seed the vendored copy first so it works fully offline.
    geopack_bootstrap.ensure_igrf_coeffs()

    kernel_files = sorted(
        path for path in KERNELS_DIR.rglob("*") if path.suffix.lower() in KERNEL_EXTENSIONS
    )
    if not kernel_files:
        raise FileNotFoundError(f"No SPICE kernel files found under {KERNELS_DIR}")

    for kernel_file in kernel_files:
        spice.furnsh(str(kernel_file))

    # Custom GSE frame definition, not part of any ESA-archive kernel set.
    spice.furnsh(str(GSE_KERNEL_PATH))


def _compute_irem_direction(times: pd.DatetimeIndex) -> pd.DataFrame:
    import spiceypy as spice
    from geopack import geopack

    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []

    for utc_time in times:
        try:
            et = spice.str2et(utc_time.isoformat())
            geopack.recalc(et)
            rotation_matrix = spice.pxform(FROM_FRAME, TO_FRAME, et)
            vec_gse = spice.mxv(rotation_matrix, IREM_BORESIGHT_SC)
            vec_gsm = geopack.gsmgse(vec_gse[0], vec_gse[1], vec_gse[2], -1)
            xs.append(vec_gsm[0])
            ys.append(vec_gsm[1])
            zs.append(vec_gsm[2])
        except Exception as exc:
            print(f"Error computing IREM direction at {utc_time}: {exc}")
            xs.append(np.nan)
            ys.append(np.nan)
            zs.append(np.nan)

    return pd.DataFrame({"time": times, "x": xs, "y": ys, "z": zs})


def _angle_between(v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
    v1_u = v1 / np.linalg.norm(v1, axis=1, keepdims=True)
    v2_u = v2 / np.linalg.norm(v2, axis=1, keepdims=True)
    return np.clip(np.sum(v1_u * v2_u, axis=1), -1.0, 1.0)


def build_from_kernels() -> None:
    """Compute pitch angle from scratch using staged SPICE kernels."""
    if not MAGFIELD_HDF_PATH.exists():
        raise FileNotFoundError(f"Missing magfield HDF: {MAGFIELD_HDF_PATH}")
    if not KERNELS_DIR.exists():
        raise FileNotFoundError(f"Missing kernels directory: {KERNELS_DIR}")

    input_paths = [MAGFIELD_HDF_PATH, KERNELS_STAMP_PATH]
    if not _needs_rebuild(PITCH_ANGLE_HDF_PATH, input_paths):
        print(f"Skipping pitch-angle HDF rebuild; up to date: {PITCH_ANGLE_HDF_PATH}")
        return

    print(f"Loading magfield HDF from {MAGFIELD_HDF_PATH}")
    magfield_df = pd.read_hdf(MAGFIELD_HDF_PATH, key="df")
    magfield_df["time"] = pd.to_datetime(magfield_df["time"])

    start_time = magfield_df["time"].min()
    end_time = magfield_df["time"].max()
    print(f"Pitch-angle date range: {start_time} .. {end_time}")

    _load_kernels()
    times = pd.date_range(start=start_time, end=end_time, freq=f"{INTERVAL_MINUTES}min")
    direction_df = _compute_irem_direction(times)

    merged = magfield_df.merge(direction_df, on="time", how="inner")

    b_vec = merged[["bx_gsm", "by_gsm", "bz_gsm"]].to_numpy()
    d_vec = merged[["x", "y", "z"]].to_numpy()
    pitch_angle_cos = _angle_between(b_vec, d_vec)
    pitch_angle_rad = np.arccos(pitch_angle_cos)
    pitch_angle_deg = np.degrees(pitch_angle_rad)

    output_df = pd.DataFrame(
        {
            "time": merged["time"],
            "pitch_angle_cos": pitch_angle_cos,
            "pitch_angle_rad": pitch_angle_rad,
            "pitch_angle_deg": pitch_angle_deg,
        }
    )
    _write_output(output_df)


def main() -> None:
    if FETCH_MODE == "network":
        build_from_kernels()
    else:
        build_from_seed()


if __name__ == "__main__":
    main()
