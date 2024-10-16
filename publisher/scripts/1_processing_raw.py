#!/usr/bin/env python
# coding: utf-8

# # Level 1: Processing raw

# In[ ]:


from spacepy import pycdf
import os
from pathlib import Path
import subprocess
import sys
import re
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any

from dotenv import load_dotenv
load_dotenv("../.env")

if os.environ.get('CDF_LIB', '') == '':
    print('No CDF_LIB environment variable found for CDF file processing.')


# In[ ]:


DATA_RAW = Path("/radem_data/radem/raw/")
DATA_EXTRACTED = Path("/radem_data/radem/extracted/")
DATA_CSV = Path("/radem_data/radem/csv/")


# ## Fetching data

# ### Extracting data

# In[ ]:


def extract_data(source_dir: Path, target_dir: Path) -> bool:
    if 0 != subprocess.call(f"for f in {source_dir}/*.tar.gz; do tar -xvf \"$f\" -C {target_dir}; done;",
                            shell=True):
        print("Error extracting tar files", file=sys.stderr)
        return False
    return True


# ### Validating extracted data

# In[ ]:


def check_batch_dir(batch_dir: Path) -> bool:
    """
    Check if the batch directory contains all the necessary files.
    """

    # eg for juicepsa-pds4-PI-01-juice_rad-20240417T191059
    #                                      ^-------^
    #                                               ^----^
    ts0 = batch_dir.name[-15:-7]
    ts1 = batch_dir.name[-6:]

    paths_valid = [
        Path(
            f"juicepsa-pds4-PI-01-juice_rad-{ts0}T{ts1}-checksum_manifest.tab"),
        Path(
            f"juicepsa-pds4-PI-01-juice_rad-{ts0}T{ts1}-transfer_manifest.tab"),
        Path(f"juicepsa-pds4-PI-01-juice_rad-{ts0}T{ts1}.xml"),
        Path(f"juice_rad/data/raw/rad_raw_sc_{ts0}.cdf"),
        Path(f"juice_rad/data/raw/rad_raw_sc_{ts0}.lblx"),
    ]

    is_ok = True
    for path in paths_valid:
        if not batch_dir.joinpath(path).exists():
            print(f"Missing {path}", file=sys.stderr)
            is_ok = False

    return is_ok


# ### Pipeline

# In[ ]:


# 1.
# !./0_fetching_ftp.sh


# In[ ]:


# 2.
extract_data(DATA_RAW, DATA_EXTRACTED)


# In[ ]:


# 3.
# for batch_dir in DATA_EXTRACTED.iterdir():
#     if not batch_dir.is_dir():
#         continue
#     check_batch_dir(DATA_EXTRACTED)


# ## CDF Processing

# ### Reading CDF data
#
# Output: `pycdf.CDF`

# In[ ]:


def is_path_science_cdf(path: Path) -> bool:
    return path.name.startswith("rad_raw_sc_") and path.name.endswith(".cdf")


def is_path_housekeeping_cdf(path: Path) -> bool:
    return path.name.startswith("rad_raw_hk_") and path.name.endswith(".cdf")


# In[ ]:


def read_cdf(cdf_path: Path) -> pycdf.CDF:
    """
    Note: It keeps the CDF file open, so it should be closed after use.
    """
    return pycdf.CDF(str(cdf_path))

    # cdf = None
    # with pycdf.CDF(str(cdf_path)) as cdf:
    # cdf = cdf.copy()
    # return cdf


def read_science_cdfs(data_dir: Path) -> List[pycdf.CDF]:
    cdfs = []

    for batch_dir in sorted(data_dir.iterdir()):
        cdf_dir = batch_dir.joinpath("juice_rad/data_raw")
        for cdf_path in cdf_dir.glob("*.cdf"):
            if is_path_science_cdf(cdf_path):
                cdfs.append(read_cdf(cdf_path))
    return cdfs


def read_housekeeping_cdfs(data_dir: Path) -> List[pycdf.CDF]:
    cdfs = []

    for batch_dir in sorted(data_dir.iterdir()):
        cdf_dir = batch_dir.joinpath("juice_rad/data_raw")
        for cdf_path in cdf_dir.glob("*.cdf"):
            if is_path_housekeeping_cdf(cdf_path):
                cdfs.append(read_cdf(cdf_path))
    return cdfs


# ### Validating CDF data

# In[ ]:


def check_science_cdfs(science_cdfs: List[pycdf.CDF]) -> bool:
    # ...
    # ...
    # return all([19 == len(cdf.keys()) for cdf in science_cdfs])
    return True


def check_housekeeping_cdfs(housekeeping_cdfs: List[pycdf.CDF]) -> bool:
    # ...
    # ...
    # return all([55 == cdf.keys() for cdf in housekeeping_cdfs])
    return True


# ### Exploring CDF data

# In[ ]:


def print_cdf_report(cdf: pycdf.CDF):
    print(f'Keys:')
    print(cdf)

    print(f'\nCDF meta:')
    print(cdf.meta)
    for key, val in cdf.items():
        print(f'\n{key} -> {val}')
        print(val.meta)


# ## CSV/DataFrame processing

# ### Converting CDF to DataFrame

# In[ ]:


def cdf_to_df(cdf: pycdf.CDF) -> pd.DataFrame:
    df = pd.DataFrame((cdf[key][...] for key in cdf.keys())).T
    df.columns = cdf.keys()
    return df


# ### Loading / Saving CSV

# In[ ]:


def load_csv(filename: str) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame
    """

    df = pd.read_csv(filename)
    df['time'] = pd.to_datetime(df['time'])
    return df


def save_csv(df: pd.DataFrame, name: str) -> None:
    """
    Generate a name and save a pandas DataFrame to a CSV file
    """
    latest_time = max(df['time']).strftime('%Y%m%dT%H%M%S')
    filename = DATA_CSV.joinpath(name + "_" + latest_time + '.csv')

    df.to_csv(filename, index=False)


# ### Fixing DataFrame data

# In[ ]:


def fix_df_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the time column to datetime and floor it to seconds, in place.
    """
    df["time"] = pd.to_datetime(df['time']).dt.floor('S')

    return df


def fix_df_time_start(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataframe to only include events after September 1, 2023, in place.
    """
    df.query("time >= '2023-09-01'", inplace=True)

    return df


def fix_df_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Find and remove duplicates from the dataframe, in place.
    """
    df.drop_duplicates(inplace=True, keep="first")
    return df


def fix_sorting_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort the dataframe by time, in place.
    """
    df.sort_values("time", inplace=True)
    return df


def fix_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix the dataframe in place.
    """
    fix_df_time(df)
    fix_df_time_start(df)
    fix_df_duplicates(df)
    fix_sorting_df(df)
    return df


# ### Validating DataFrame data

# In[ ]:


def verify_df_sorted(df: pd.DataFrame) -> None:
    """
    Verify that the dataframe is sorted by "time"
    """
    # Find rows where the 'time' is decreasing from the previous row
    not_sorted_mask = df['time'].diff().dt.total_seconds() < 0

    # The first row can't be "not sorted" by definition, so we can exclude it from the mask
    not_sorted_mask.iloc[0] = False

    # Filter the DataFrame to find the not sorted rows
    not_sorted_rows = df[not_sorted_mask]

    if not df['time'].is_monotonic_increasing:
        raise ValueError(
            f"Dataframe is not sorted by time:\n{not_sorted_rows}")


def verify_df_time_diffs(df: pd.DataFrame,
                         max_diff_tolerance: np.timedelta64 = np.timedelta64(
                             90, 's'),
                         min_diff_tolerance: np.timedelta64 = np.timedelta64(500, 'ms')) -> None:
    """
    Verify that the time differences between events are within tolerance.
    If time diff >= max_diff_tolerance, just prints the warning (data holes are permitted).
    If time diff <= min_diff_tolerance, raises an exception (possible floating point errors).

    Assumes that the dataframe is non-decreasingly sorted by "time".  

    There may me multiple groups of events with the same time.

    Args:
        df (pd.DataFrame): input dataframe with "time" column
        max_diff_tolerance (np.timedelta64, optional): max time difference tolerance in ms (warning only)
        min_diff_tolerance (np.timedelta64, optional): min time difference tolerance in ms (exception)

    Raises:
        ValueError: when time differences < min_diff_tolerance (possible floating point errors)
    """

    # get all unique "time" values in df
    times = df['time'].unique()

    # calc time diffs
    time_diffs = np.diff(times)

    # check if all time diffs are not larger than the tolerance
    checks = max_diff_tolerance > time_diffs
    if not all(checks):
        # find all indexes of unmet conditions
        indexes = np.where(checks == False)[0]

        # create a dataframe of times
        df_times = pd.DataFrame(times, columns=["time"])

        # find all holes
        holes = [
            f"{df_times.iloc[i]['time']} and {df_times.iloc[i + 1]['time']}" for i in indexes]

        print("Found time holes out of tolerance at times:", *holes, sep='\n\t')

    # check if all time diffs are not smaller than the tolerance
    # (possible floating point errors)
    checks = min_diff_tolerance < time_diffs
    if not all(checks):
        # find all indexes of unmet conditions
        indexes = np.where(checks == False)[0]

        # create a dataframe of times
        df_times = pd.DataFrame(times, columns=["time"])

        # find all too close values
        too_close = [
            f"{df_times.iloc[i]['time']} and {df_times.iloc[i + 1]['time']}" for i in indexes]

        raise ValueError(
            "Found time values too close to each other at times " +
            "(possible floating point errors):\n\t" +
            "\n\t".join(too_close))


# # Procesing data categories

# ## Temperature

# ### Temperature data conversions
# According to *RADEM User Manual*.

# In[ ]:


def convert_hk_temp(adc_out: int | np.ndarray) -> int:
    """
    Convert housekeeping temperature (ADC output) to Celsius.

    Notes:
    - Uses Equation 6 for RADEM EQM/PFM HK from RADEM User Manual.
    - Applicable for temperature sensors 1-5.
    - 1 Celsius degree precision.
    - RADEM operating range: -40 to +85 Celsius degrees.
    """
    return np.round(adc_out * (3.3 / 4096) * (1000000 / 2210) - 273.16)


# ### Pipeline

# In[ ]:


# 1. Reading CDFs
hk_cdfs = read_housekeeping_cdfs(DATA_EXTRACTED)
print("Found hk CDFs:", len(hk_cdfs))
print(f"Checking hk CDFs: {check_housekeeping_cdfs(hk_cdfs)}")

# 2. Converting CDFs to DataFrames
temp_cdf_keys = [
    "HK_Temp1_CEU",
    "HK_PandI_Stack_Temp2",
    "HK_E_Stack_Temp3",
    "HK_DD_Temp4",
    "HK_Temp5_CPU",
]

temp_csv_keys = [
    "time",
    "CEU Temperature (1)",
    "P&IDH Temperature (2)",
    "EDH Temperature (3)",
    "DDH Temperature (4)",
    "PCU Temperature (5)",
]

hk_dfs = []
for cdf in hk_cdfs:
    df = pd.DataFrame(
        np.vstack([
            cdf["TIME_UTC"][...],
            *[convert_hk_temp(cdf[k][...]) for k in temp_cdf_keys]]).T,
        columns=temp_csv_keys
    )
    hk_dfs.append(df)

# close opened files
del hk_cdfs

# 3. Combining and fixing DataFrames
df = pd.concat(hk_dfs)
print("DF length before fixing:", len(df))
fix_df(df)
print("DF length after fixing:", len(df))

# 4. Validating DataFrames (to be 100% sure)
print("Verifying sorting")
verify_df_sorted(df)
print("Verifying time diffs")
verify_df_time_diffs(df)

# 5. Saving DataFrames to CSV
save_csv(df, "temperature")


# ## Particles

# ### Particles data processing

# In[ ]:


def process_particles(cdf: pycdf.CDF,
                      cdf_particle_key: str,
                      cdf_particle_bin: str) -> pd.DataFrame:
    times = cdf["TIME_UTC"][...]
    particles = cdf[cdf_particle_key][...]
    particle_bins = cdf[cdf_particle_bin][...]

    time_col = np.repeat(times, len(particle_bins))
    # event_type_col = np.full(len(particles) * len(particle_bins), event_type, dtype="U1")
    bin_col = np.tile(particle_bins, len(particles))
    value_col = particles.flatten()

    df = pd.DataFrame({
        "time": time_col,
        # "event_type": event_type_col,
        "bin": bin_col,
        "value": value_col
    })

    return df


# ### Additional particles data validation

# In[ ]:


def verify_df_time_p_counts(df: pd.DataFrame) -> None:
    check = all(df["time"].value_counts() == 9)

    if not check:
        raise ValueError("Incorrect number of proton events for some times")


def verify_df_time_e_counts(df: pd.DataFrame) -> None:
    check = all(df["time"].value_counts() == 9)

    if not check:
        raise ValueError("Incorrect number of electron events for some times")


def verify_df_time_dd_counts(df: pd.DataFrame) -> None:
    check = all(df["time"].value_counts() == 31)

    if not check:
        raise ValueError("Incorrect number of DD events for some times")


def verify_df_time_hi_counts(df: pd.DataFrame) -> None:
    check = all(df["time"].value_counts() == 8)

    if not check:
        raise ValueError("Incorrect number of heavy ion events for some times")


# ### Pipeline

# In[ ]:


# 1. Reading CDFs
sc_cdfs = read_science_cdfs(DATA_EXTRACTED)

print("Found sc CDFs:", len(sc_cdfs))
print(f"Checking sc CDFs: {check_science_cdfs(sc_cdfs)}")

# 2. Converting CDFs to DataFrames
df_p = pd.concat((
    process_particles(cdf, "PROTONS", "PROTON_BINS")
    for cdf in sc_cdfs
))

df_e = pd.concat((
    process_particles(cdf, "ELECTRONS", "ELECTRON_BINS")
    for cdf in sc_cdfs
))

df_d = pd.concat((
    process_particles(cdf, "DD", "DD_BINS")
    for cdf in sc_cdfs
))

df_h = pd.concat((
    process_particles(cdf, "HI_IONS", "HI_ION_BINS")
    for cdf in sc_cdfs
))

print("Proton measurements:", len(df_p))
print("Electron measurements:", len(df_e))
print("DD measurements:", len(df_d))
print("Heavy ion measurements:", len(df_h))

# close opened files
del sc_cdfs

# 3. Fixing DataFrames
fix_df(df_p)
fix_df(df_e)
fix_df(df_d)
fix_df(df_h)

print("Proton measurements:", len(df_p), "(after fixing)")
print("Electron measurements:", len(df_e), "(after fixing)")
print("DD measurements:", len(df_d), "(after fixing)")
print("Heavy ion measurements:", len(df_h), "(after fixing)")

# 4. Validating DataFrames
print("Verifying sorting")
verify_df_sorted(df_p)
verify_df_sorted(df_e)
verify_df_sorted(df_d)
verify_df_sorted(df_h)
print("Verifying time diffs")
verify_df_time_diffs(df_p)
verify_df_time_diffs(df_e)
verify_df_time_diffs(df_d)
verify_df_time_diffs(df_h)
print("Verifying time counts")
verify_df_time_p_counts(df_p)
verify_df_time_e_counts(df_e)
verify_df_time_dd_counts(df_d)
verify_df_time_hi_counts(df_h)

# 5. Saving DataFrames to CSV
print("Saving CSVs")
save_csv(df_p, "protons")
save_csv(df_e, "electrons")
save_csv(df_d, "dd")
save_csv(df_h, "heavy_ions")


# ## Patricle Flux

# In[ ]:


# 1. Reading CDFs
sc_cdfs = read_science_cdfs(DATA_EXTRACTED)

print("Found sc CDFs:", len(sc_cdfs))
print(f"Checking sc CDFs: {check_science_cdfs(sc_cdfs)}")

# 2. Converting CDFs to DataFrames
cdf = sc_cdfs[0]
flux_labels = cdf["LABEL_FLUX"][...]
print(flux_labels)

dfs = {}
for idx, flux_label in enumerate(flux_labels):
    dfs[flux_label] = pd.concat((
        pd.DataFrame({
            "time": cdf["TIME_UTC"][...],
            "value": cdf["FLUX"][...][:, idx]
        })
        for cdf in sc_cdfs
    ))

# close opened files
del sc_cdfs

# 3. Fixing DataFrames
for df in dfs.values():
    fix_df(df)

# 4. Validating DataFrames (to be 100% sure)
for df in dfs.values():
    verify_df_sorted(df)
    verify_df_time_diffs(df)

# 5. Saving DataFrames to CSV
save_csv(dfs["PIDH"], "protons_flux")
save_csv(dfs["EDH "], "electrons_flux")  # NOTE: "EDH " is correct, not "EDH"
save_csv(dfs["DDH "], "dd_flux")  # NOTE: "DDH " is correct, not "DDH"
