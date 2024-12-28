from pathlib import Path
from typing import List, Optional
import pandas as pd
from spacepy.pycdf import CDF

import radem
from ..checkpoint import DataCheckpoint, PathRecord
from ..extracting import calc_file_checksum, diff_paths_and_checksums, extract_cdf_gz_files
from ..script_executor import execute_script
from ..influxdb_utils import InfluxDbUtils
from .. import env
import logging

logger = logging.getLogger(__name__)


def fetch_irem_data() -> None:
    logger.info("Fetching IREM data from remote server.")
    execute_script("fetch_irem.sh")


def extract_irem_data(data_raw_paths: Optional[List[Path]] = None) -> None:
    logger.info("Extracting IREM data from GZ files.")
    if data_raw_paths is None:
        extract_cdf_gz_files(
            env.DATA_IREM_RAW_DIR,
            env.DATA_IREM_EXTRACTED_DIR)
    else:
        extract_cdf_gz_files(
            data_raw_paths,
            env.DATA_IREM_EXTRACTED_DIR)


def get_path_records_to_process(
        data_checkpoint: DataCheckpoint) -> List[PathRecord]:
    logger.info("Getting paths to process.")
    path_checkpoint_records = data_checkpoint.irem_paths_processed

    paths = radem.handlers.get_irem_cdf_paths(
        env.DATA_IREM_EXTRACTED_DIR)
    path_local_records = [PathRecord(
        path=str(path.absolute()),
        checksum=calc_file_checksum(path),
        is_processed=False) for path in paths]

    paths_to_process = diff_paths_and_checksums(
        path_checkpoint_records,
        path_local_records)

    logger.info(f"Found {len(paths_to_process)} paths to process:")
    for path in paths_to_process:
        logger.info(f"  {path.path}")

    return paths_to_process


def read_irem_cdf_files(paths: List[Path]) -> List[CDF]:
    logger.info("Reading CDF files.")
    cdfs = radem.handlers.read_irem_cdfs(paths)
    return cdfs


def process_irem_cdf_files(cdfs: List[CDF]) -> pd.DataFrame:
    logger.info("Processing CDF files to DF.")
    df_patch = radem.handlers.convert_irem_cdfs_to_df(cdfs)
    return df_patch


def append_irem_hdf(df_patch: pd.DataFrame, filename: Path) -> None:
    logger.info("Appending data to HDF5 file.")
    radem.handlers.append_hdf(df_patch, filename)


def upload_irem_data(df_patch: pd.DataFrame) -> None:
    logger.info("Uploading data to remote server.")


def update_checkpoint(data_checkpoint: DataCheckpoint,
                      path_records_to_process: List[PathRecord]) -> None:
    data_checkpoint.irem_paths_processed.extend(path_records_to_process)
    data_checkpoint.write()


def run_irem_job(influxdb_utils: InfluxDbUtils,
                 data_checkpoint: Optional[DataCheckpoint] = None) -> None:
    logger.info("Running IREM job.")

    # 1. Read checkpoint
    if data_checkpoint is None:
        data_checkpoint = DataCheckpoint.read()

    # 2. Fetch data
    # fetch_irem_data()

    # 3. Extract data
    # extract_irem_data()

    # 4. Compare CDF paths with checkpoint
    # path_records_to_process = get_path_records_to_process(data_checkpoint)
    # paths_to_process = [
    #     path_record.path for path_record in path_records_to_process]

    df = radem.handlers.read_hdf(env.DATA_IREM_HDF5_FILENAME)
    print(df)
    influxdb_utils.upload_df(df)

    return
    if len(paths_to_process) == 0:
        logger.info("No paths to process. Skipping job.")
        return

    # 5. Read CDF files
    cdfs = read_irem_cdf_files(paths_to_process)

    # 6. Process CDF files
    df_patch = process_irem_cdf_files(cdfs)

    # 7. Append data
    append_irem_hdf(df_patch, env.DATA_IREM_HDF5_FILENAME)

    # 8. Upload data
    influxdb_utils.upload_df(df_patch)

    # 9. Save checkpoint
    update_checkpoint(data_checkpoint, path_records_to_process)
