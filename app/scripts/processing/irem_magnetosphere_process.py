#!/usr/bin/env python3
"""Build the IREM magnetosphere HDF5 files (orbit, magnetic field, pitch angle)."""

import importlib.util
import shutil
import socket
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import spiceypy as spice
from astropy.table import Table
from spacepy import coordinates
from spacepy import time as spacepy_time

from irem_magnetosphere_paths import (
    HDF_DIR,
    HDF_KEY,
    KERNELS_DIR,
    MAGFIELD_HDF_PATH,
    ORBIT_DIR,
    ORBIT_HDF_PATH,
    PITCH_ANGLE_HDF_PATH,
    TSYGAN_INPUT_DIR,
)

PROCESSING_DIR = Path(__file__).resolve().parent
IGRF_COEFFS_DIR = PROCESSING_DIR / "igrf_coeffs"
GSE_KERNEL_PATH = PROCESSING_DIR / "spice_kernels" / "gse.tf"


# geopack downloads IGRF coefficients on import and crashes without them.
def _install_igrf_coeffs() -> None:
    spec = importlib.util.find_spec("geopack")
    target = Path(next(iter(spec.submodule_search_locations))) / "igrf_coeffs"
    if not any(target.glob("igrf*coeffs.txt")):
        target.mkdir(exist_ok=True)
        for path in IGRF_COEFFS_DIR.glob("igrf*coeffs.txt"):
            shutil.copy(path, target)


_install_igrf_coeffs()
socket.setdefaulttimeout(10)
from geopack import geopack, t04  # noqa: E402
socket.setdefaulttimeout(None)

CADENCE = "5min"
EARTH_RADIUS_KM = 6371.2
PROGRESS_EVERY = 5000

# J2000, km
POSITION_COLUMNS = ["x_j2000", "y_j2000", "z_j2000"]
FIELD_COLUMNS = ["bx_gsm", "by_gsm", "bz_gsm"]

KERNEL_EXTENSIONS = {".bsp", ".bc", ".tsc", ".tls", ".tpc", ".bpc", ".tf", ".ti"}
IREM_BORESIGHT = [0, 0, -1]  # IREM points along -Z of the spacecraft frame.

TS05_COLUMNS = [
    "Year", "Day", "Hour", "Minute",
    "BX_GSM", "BY_GSM", "BZ_GSM",
    "VX_GSE", "VY_GSE", "VZ_GSE",
    "Proton_Density", "Proton_Temperature", "SYM_H",
    "IMF_Flag", "SW_Flag", "Dipole_Tilt_Rad", "Ram_Pressure_nPa",
    "W1", "W2", "W3", "W4", "W5", "W6",
]
# geopack.t04 parameter order
T04_PARAMETERS = [
    "Ram_Pressure_nPa", "SYM_H", "BY_GSM", "BZ_GSM",
    "W1", "W2", "W3", "W4", "W5", "W6",
]


class SkipStage(Exception):
    pass


def _read_hdf(path: Path) -> pd.DataFrame:
    df = pd.read_hdf(path, key=HDF_KEY)
    df["time"] = pd.to_datetime(df["time"])
    return df


def _read_hdf_or_none(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return _read_hdf(path)
    except Exception as exc:
        print(f"Cannot read {path.name} ({exc}), building it again.")
        return None


def _write_hdf(path: Path, df: pd.DataFrame) -> None:
    df = df.sort_values("time").reset_index(drop=True)
    df.to_hdf(path, key=HDF_KEY, mode="w", format="table", complevel=1)
    print(f"Wrote {path.name}: {len(df)} rows, {df['time'].min()} .. {df['time'].max()}")


def _append_hdf(path: Path, new_rows: pd.DataFrame) -> None:
    old = _read_hdf_or_none(path)
    if old is not None:
        new_rows = pd.concat([old, new_rows]).drop_duplicates("time", keep="last")
    _write_hdf(path, new_rows)


def _rows_without_values(df: pd.DataFrame, output: Path, column: str) -> pd.DataFrame:
    old = _read_hdf_or_none(output)
    if old is None:
        return df
    return df[~df.index.isin(old.loc[old[column].notna(), "time"])]


def _is_stale(output: Path, inputs: list[Path]) -> bool:
    if not output.exists():
        return True
    mtime = output.stat().st_mtime
    return any(path.stat().st_mtime > mtime for path in inputs)


def _unix_seconds(times: pd.DatetimeIndex) -> np.ndarray:
    # Timestamps are naive UTC.
    return ((times - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)).to_numpy()


def build_orbit() -> None:
    fits_files = sorted(ORBIT_DIR.glob("orbit_historic_*.fits"))
    if not fits_files:
        if not ORBIT_HDF_PATH.exists():
            raise SkipStage(f"no orbit FITS files and no {ORBIT_HDF_PATH.name}")
        print(f"No orbit FITS files, using the existing {ORBIT_HDF_PATH.name}.")
        return

    if not _is_stale(ORBIT_HDF_PATH, fits_files):
        print(f"{ORBIT_HDF_PATH.name} is up to date.")
        return

    print(f"Reading {len(fits_files)} orbit FITS files.")
    frames = []
    for path in fits_files:
        try:
            frames.append(_read_orbit_fits(path))
        except Exception as exc:
            print(f"Cannot read {path.name}: {exc}")
    if not frames:
        raise RuntimeError("Cannot read any orbit FITS file.")

    orbit = pd.concat(frames, ignore_index=True).drop_duplicates("time")
    _write_hdf(ORBIT_HDF_PATH, orbit)


def _read_orbit_fits(path: Path) -> pd.DataFrame:
    table = Table.read(path)
    position = np.asarray(table["XYZPOS"])
    return pd.DataFrame({
        "time": pd.to_datetime(np.asarray(table["EPOCH"]), unit="D", origin="2000-01-01"),
        "x_j2000": position[:, 0],
        "y_j2000": position[:, 1],
        "z_j2000": position[:, 2],
        "distance": np.asarray(table["RDIST"]) / EARTH_RADIUS_KM,
    })


def build_magfield() -> None:
    if not ORBIT_HDF_PATH.exists():
        raise SkipStage(f"no {ORBIT_HDF_PATH.name}")
    orbit = _read_hdf(ORBIT_HDF_PATH)
    positions = _rows_without_values(_resample_orbit(orbit), MAGFIELD_HDF_PATH, "b_magnitude")
    if positions.empty:
        print("No new orbit rows.")
        return

    ts05 = _read_ts05_input(set(positions.index.year))
    rows = positions.join(ts05, how="inner").dropna(subset=T04_PARAMETERS)
    if rows.empty:
        print("No TS05 input for the new orbit rows.")
        return

    print(f"Modeling {len(rows)} rows, {rows.index.min()} .. {rows.index.max()}")
    _append_hdf(MAGFIELD_HDF_PATH, _model_field(_add_gsm_position(rows)))


def _resample_orbit(orbit: pd.DataFrame) -> pd.DataFrame:
    # Grid on full 5 minutes, the same timestamps as the TS05 input.
    df = orbit.set_index("time").sort_index()
    df = df[~df.index.duplicated()][POSITION_COLUMNS]
    grid = pd.date_range(df.index.min().ceil(CADENCE), df.index.max().floor(CADENCE), freq=CADENCE)
    return df.reindex(df.index.union(grid)).interpolate(method="time").reindex(grid).dropna()


def _read_ts05_input(years: set[int]) -> pd.DataFrame:
    paths = [
        path for path in sorted(TSYGAN_INPUT_DIR.glob("*_OMNI_5m_with_TS05_variables.dat"))
        if int(path.name[:4]) in years
    ]
    if not paths:
        raise SkipStage(f"no TS05 input for {sorted(years)} in {TSYGAN_INPUT_DIR}")

    df = pd.concat(
        (pd.read_table(path, sep=r"\s+", names=TS05_COLUMNS) for path in paths),
        ignore_index=True,
    ).apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["Year", "Day", "Hour", "Minute"])

    df["time"] = (
        pd.to_datetime(df["Year"].astype(int).astype(str), format="%Y")
        + pd.to_timedelta(df["Day"] - 1, unit="D")
        + pd.to_timedelta(df["Hour"], unit="h")
        + pd.to_timedelta(df["Minute"], unit="min")
    )
    return df.drop(columns=["Year", "Day", "Hour", "Minute"]).set_index("time").sort_index()


def _add_gsm_position(df: pd.DataFrame) -> pd.DataFrame:
    coords = coordinates.Coords(df[POSITION_COLUMNS].to_numpy() / EARTH_RADIUS_KM, "ECI2000", "car")
    coords.ticks = spacepy_time.Ticktock(df.index.to_pydatetime(), "UTC")
    coords.use_irbem = True
    gsm = coords.convert("GSM", "car")
    return df.assign(x_gsm=gsm.x, y_gsm=gsm.y, z_gsm=gsm.z)


def _model_field(rows: pd.DataFrame) -> pd.DataFrame:
    # External field only, IGRF is not added.
    parameters = rows[T04_PARAMETERS].to_numpy()
    positions = rows[["x_gsm", "y_gsm", "z_gsm"]].to_numpy()
    field = np.full((len(rows), 3), np.nan)
    errors = 0

    for i, unix_time in enumerate(_unix_seconds(rows.index)):
        if i % PROGRESS_EVERY == 0:
            print(f"Modeling field {i}/{len(rows)}", flush=True)
        try:
            tilt = geopack.recalc(unix_time)
            field[i] = t04.t04(parameters[i], tilt, *positions[i])
        except Exception as exc:
            errors += 1
            if errors == 1:
                print(f"Model failed at {rows.index[i]}: {exc}")

    print(f"Modeled {len(rows) - errors}/{len(rows)} rows ({errors} errors)")
    return pd.DataFrame({
        "time": rows.index,
        **dict(zip(FIELD_COLUMNS, field.T, strict=True)),
        "b_magnitude": np.linalg.norm(field, axis=1),
    })


def build_pitch_angle() -> None:
    if not MAGFIELD_HDF_PATH.exists():
        raise SkipStage(f"no {MAGFIELD_HDF_PATH.name}")

    field = _read_hdf(MAGFIELD_HDF_PATH).dropna(subset=["b_magnitude"]).set_index("time").sort_index()
    field = _rows_without_values(field, PITCH_ANGLE_HDF_PATH, "pitch_angle_cos")
    if field.empty:
        print("No new magnetic field rows.")
        return

    _furnish_kernels()
    print(f"Pointing IREM for {len(field)} rows, {field.index.min()} .. {field.index.max()}")
    boresight = _boresight_gsm(field.index)
    valid = np.isfinite(boresight).all(axis=1)

    cos = _cos_angle(field.loc[valid, FIELD_COLUMNS].to_numpy(), boresight[valid])
    _append_hdf(PITCH_ANGLE_HDF_PATH, pd.DataFrame({
        "time": field.index[valid],
        "pitch_angle_cos": cos,
        "pitch_angle_rad": np.arccos(cos),
    }))


def _furnish_kernels() -> None:
    kernels = sorted(p for p in KERNELS_DIR.rglob("*") if p.suffix.lower() in KERNEL_EXTENSIONS)
    if not kernels:
        raise SkipStage(f"no SPICE kernels in {KERNELS_DIR}")
    for path in [*kernels, GSE_KERNEL_PATH]:
        spice.furnsh(str(path))
    print(f"Loaded {len(kernels)} SPICE kernels.")


def _boresight_gsm(times: pd.DatetimeIndex) -> np.ndarray:
    boresight = np.full((len(times), 3), np.nan)
    failures = 0

    for i, (timestamp, unix_time) in enumerate(zip(times, _unix_seconds(times), strict=True)):
        if i % PROGRESS_EVERY == 0:
            print(f"Pointing IREM {i}/{len(times)}", flush=True)
        try:
            et = spice.str2et(timestamp.isoformat())
            gse = spice.mxv(spice.pxform("INTEGRAL_SPACECRAFT", "GSE", et), IREM_BORESIGHT)
            geopack.recalc(unix_time)
            boresight[i] = geopack.gsmgse(*gse, -1)
        except Exception as exc:
            failures += 1
            if failures == 1:
                print(f"No pointing at {timestamp}: {exc}")

    if failures:
        print(f"No pointing for {failures}/{len(times)} rows (no kernel data).")
    return boresight


def _cos_angle(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a / np.linalg.norm(a, axis=1, keepdims=True)
    b = b / np.linalg.norm(b, axis=1, keepdims=True)
    return np.clip((a * b).sum(axis=1), -1.0, 1.0)


STAGES = {
    "orbit": build_orbit,
    "magnetic field": build_magfield,
    "pitch angle": build_pitch_angle,
}


def main() -> int:
    HDF_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for name, stage in STAGES.items():
        print(f"----- {name} -----", flush=True)
        try:
            stage()
        except SkipStage as exc:
            print(f"Skipped: {exc}")
        except Exception:
            failed.append(name)
            print(f"ERROR in {name} stage:\n{traceback.format_exc()}")

    if failed:
        print(f"Failed stages: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
