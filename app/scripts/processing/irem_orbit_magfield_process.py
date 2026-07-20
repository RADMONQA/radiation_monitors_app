#!/usr/bin/env python3
"""Build orbit and modeled magnetic-field HDF5 files for IREM."""

from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.table import Table
from dotenv import load_dotenv
from spacepy import coordinates as coord
from spacepy import time as spt

import geopack_bootstrap

geopack_bootstrap.ensure_igrf_coeffs()
from geopack import geopack, t04  # noqa: E402

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "/app_data"))
ORBIT_EXTRACTED_DIR = DATA_DIR / "irem" / "orbit" / "extracted"
ORBIT_HDF_PATH = DATA_DIR / "irem" / "orbit" / "orbit_data.h5"
TSYGAN_INPUT_DIR = DATA_DIR / "irem" / "magfield" / "tsygan_input"
MAGFIELD_HDF_PATH = DATA_DIR / "irem" / "magfield" / "magfield_data.h5"
REPROCESS_ALL_DATA = os.getenv("REPROCESS_ALL_DATA", "0") == "1"

EARTH_RADIUS_KM = 6371.2

OMNI_5MIN_TS05_NAMES = [
    "Year",
    "Day",
    "Hour",
    "Minute",
    "BX_GSM",
    "BY_GSM",
    "BZ_GSM",
    "VX_GSE",
    "VY_GSE",
    "VZ_GSE",
    "Proton_Density",
    "Proton_Temperature",
    "SYM_H",
    "IMF_Flag",
    "SW_Flag",
    "Dipole_Tilt_Rad",
    "Ram_Pressure_nPa",
    "W1",
    "W2",
    "W3",
    "W4",
    "W5",
    "W6",
]


def _newest_mtime(paths: list[Path]) -> float | None:
    mtimes = [path.stat().st_mtime for path in paths if path.exists()]
    return max(mtimes) if mtimes else None


def _needs_rebuild(output_path: Path, input_paths: list[Path]) -> bool:
    if REPROCESS_ALL_DATA or not output_path.exists():
        return True
    output_mtime = output_path.stat().st_mtime
    input_mtime = _newest_mtime(input_paths)
    return input_mtime is not None and input_mtime > output_mtime


def build_orbit_hdf() -> None:
    fits_files = sorted(ORBIT_EXTRACTED_DIR.glob("orbit_historic_*.fits"))
    if not fits_files:
        raise FileNotFoundError(f"No orbit FITS files found in {ORBIT_EXTRACTED_DIR}")

    if not _needs_rebuild(ORBIT_HDF_PATH, fits_files):
        print(f"Skipping orbit HDF rebuild; up to date: {ORBIT_HDF_PATH}")
        return

    print(f"Building orbit HDF from {len(fits_files)} FITS files...")
    df_list: list[pd.DataFrame] = []

    for fits_path in fits_files:
        try:
            table = Table.read(fits_path)
            data: dict[str, np.ndarray] = {}
            for name in table.colnames:
                column = table[name]
                if len(column.shape) == 1:
                    data[name] = column
                else:
                    for idx in range(column.shape[1]):
                        data[f"{name}_{idx}"] = column[:, idx]
            df_list.append(pd.DataFrame(data))
        except Exception as exc:
            print(f"Error reading {fits_path}: {exc}")

    if not df_list:
        raise RuntimeError("No orbit FITS files could be parsed.")

    orbit_df = pd.concat(df_list, ignore_index=True)
    final_df = pd.DataFrame(
        {
            "time": pd.to_datetime(orbit_df["EPOCH"], unit="d", origin="2000-01-01"),
            "x_j2000": orbit_df["XYZPOS_0"],
            "y_j2000": orbit_df["XYZPOS_1"],
            "z_j2000": orbit_df["XYZPOS_2"],
            "vx_j2000": orbit_df["XYZVEL_0"],
            "vy_j2000": orbit_df["XYZVEL_1"],
            "vz_j2000": orbit_df["XYZVEL_2"],
            "distance": orbit_df["RDIST"],
        }
    )

    ORBIT_HDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_hdf(
        ORBIT_HDF_PATH,
        key="df",
        mode="w",
        format="table",
        complevel=1,
    )
    print(f"Wrote orbit HDF: {ORBIT_HDF_PATH} ({len(final_df)} rows)")


def _read_ts05_file(path: Path) -> pd.DataFrame:
    df = pd.read_table(path, sep=r"\s+", names=OMNI_5MIN_TS05_NAMES)
    if path.name == "2010_OMNI_5m_with_TS05_variables.dat":
        df.iloc[:, 15] = pd.to_numeric(df.iloc[:, 15], errors="coerce")
        df.iloc[:, 20] = pd.to_numeric(df.iloc[:, 20], errors="coerce")
    return df


def _prepare_orbit_for_magfield(orbit_df: pd.DataFrame) -> pd.DataFrame:
    orbit_df = orbit_df.set_index("time")
    orbit_df = orbit_df[~orbit_df.index.duplicated(keep="first")]

    datetime_index = pd.date_range(
        start=orbit_df.index.min(),
        end=orbit_df.index.max(),
        freq="5min",
    )

    resampled = (
        pd.merge(
            orbit_df,
            orbit_df.asfreq("5min"),
            left_index=True,
            right_index=True,
            how="outer",
        )
        .interpolate(method="time")
        .reindex(datetime_index)
    )
    resampled.index = resampled.index.round("min")

    prepared = resampled[["x_j2000_x", "y_j2000_x", "z_j2000_x", "distance_x"]].rename(
        columns={
            "x_j2000_x": "x_j2000",
            "y_j2000_x": "y_j2000",
            "z_j2000_x": "z_j2000",
            "distance_x": "distance",
        }
    )
    prepared["distance"] = prepared["distance"] / EARTH_RADIUS_KM
    return prepared


def _add_gsm_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    ticks = spt.Ticktock(pd.to_datetime(df.index).to_pydatetime(), "UTC")
    coords = df[["x_j2000", "y_j2000", "z_j2000"]].values
    coords_re = coords / EARTH_RADIUS_KM

    cvals = coord.Coords(coords_re, "ECI2000", "car")
    cvals.ticks = ticks
    cvals.use_irbem = True
    coords_gsm_re = cvals.convert("GSM", "car")

    df = df.copy()
    df["x_gsm_re"] = coords_gsm_re.x
    df["y_gsm_re"] = coords_gsm_re.y
    df["z_gsm_re"] = coords_gsm_re.z
    return df


def _load_ts05_input() -> pd.DataFrame:
    dat_files = sorted(TSYGAN_INPUT_DIR.glob("*_OMNI_5m_with_TS05_variables.dat"))
    if not dat_files:
        raise FileNotFoundError(f"No TS05 input files found in {TSYGAN_INPUT_DIR}")

    input_df = pd.concat(_read_ts05_file(path) for path in dat_files)
    input_df["time"] = (
        pd.to_datetime(input_df["Year"].astype(str), format="%Y")
        + pd.to_timedelta(input_df["Day"] - 1, unit="D")
        + pd.to_timedelta(input_df["Hour"], unit="h")
        + pd.to_timedelta(input_df["Minute"], unit="m")
    )
    input_df = input_df.drop(columns=["Year", "Day", "Hour", "Minute"])
    input_df = input_df.sort_values("time").set_index("time")
    return input_df


def _compute_magfield(merged_df: pd.DataFrame) -> pd.DataFrame:
    total = len(merged_df)
    bx_list: list[float] = []
    by_list: list[float] = []
    bz_list: list[float] = []
    times: list[pd.Timestamp] = []
    error_count = 0

    for i, (idx, row) in enumerate(merged_df.iterrows()):
        if i % 5000 == 0:
            print(f"Computing magnetic field {i}/{total} ({i / total:.2%})")

        dt = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
        ut = int(time.mktime(dt.timetuple()))
        ps = geopack.recalc(ut)

        par = [
            row["Ram_Pressure_nPa"],
            row["SYM_H"],
            row["BY_GSM"],
            row["BZ_GSM"],
            row["W1"],
            row["W2"],
            row["W3"],
            row["W4"],
            row["W5"],
            row["W6"],
        ]
        bxgsm, bygsm, bzgsm = t04.t04(
            par,
            ps,
            row["x_gsm_re"],
            row["y_gsm_re"],
            row["z_gsm_re"],
        )
        if np.isnan(bxgsm) or np.isnan(bygsm) or np.isnan(bzgsm):
            error_count += 1
            bxgsm = bygsm = bzgsm = np.nan

        bx_list.append(bxgsm)
        by_list.append(bygsm)
        bz_list.append(bzgsm)
        times.append(idx)

    print(f"Magnetic field NA values: {error_count}/{total} ({error_count / total:.2%})")

    b_magnitude = np.sqrt(
        np.square(bx_list) + np.square(by_list) + np.square(bz_list)
    )
    return pd.DataFrame(
        {
            "time": times,
            "bx_gsm": bx_list,
            "by_gsm": by_list,
            "bz_gsm": bz_list,
            "b_magnitude": b_magnitude,
            "r_distance": merged_df["distance"].values,
        }
    )


def build_magfield_hdf() -> None:
    if not ORBIT_HDF_PATH.exists():
        raise FileNotFoundError(f"Missing orbit HDF: {ORBIT_HDF_PATH}")

    ts05_files = sorted(TSYGAN_INPUT_DIR.glob("*_OMNI_5m_with_TS05_variables.dat"))
    input_paths = [ORBIT_HDF_PATH, *ts05_files]
    if not _needs_rebuild(MAGFIELD_HDF_PATH, input_paths):
        print(f"Skipping magfield HDF rebuild; up to date: {MAGFIELD_HDF_PATH}")
        return

    print("Building modeled magnetic field HDF...")
    orbit_df = pd.read_hdf(ORBIT_HDF_PATH, key="df")
    prepared_orbit = _prepare_orbit_for_magfield(orbit_df)
    prepared_orbit = _add_gsm_coordinates(prepared_orbit)

    ts05_df = _load_ts05_input()
    start_date = prepared_orbit.index.min()
    end_date = prepared_orbit.index.max()
    print(f"Magfield date range: {start_date} .. {end_date}")

    merged = prepared_orbit.loc[start_date:end_date].merge(
        ts05_df.loc[start_date:end_date],
        left_index=True,
        right_index=True,
        how="left",
    )

    output_df = _compute_magfield(merged)
    MAGFIELD_HDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_hdf(
        MAGFIELD_HDF_PATH,
        key="df",
        mode="w",
        format="table",
        complevel=1,
    )
    print(f"Wrote magfield HDF: {MAGFIELD_HDF_PATH} ({len(output_df)} rows)")


def main() -> None:
    build_orbit_hdf()
    build_magfield_hdf()


if __name__ == "__main__":
    main()
