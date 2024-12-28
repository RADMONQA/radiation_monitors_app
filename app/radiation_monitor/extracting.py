from typing import overload, Union
from pathlib import Path
import gzip
import logging
import hashlib
from typing import List

from radiation_monitor.checkpoint import PathRecord
logger = logging.getLogger(__name__)


def get_cdf_gz_files(data_raw_dir: Path) -> List[Path]:
    pattern: str = "*.cdf.gz"
    return sorted(data_raw_dir.rglob(pattern))


def calc_file_checksum(file_path: Path) -> str:
    return hashlib.md5(file_path.read_bytes()).hexdigest()


def diff_paths_and_checksums(
        path_records: List[PathRecord],
        path_local_records: List[PathRecord]) -> List[Path]:
    paths_checkpoint_map = {
        path.path: path.checksum for path in path_records
    }
    paths_stored_map = {
        path.path: path.checksum for path in path_local_records
    }
    paths_to_process = [
        path for path in path_local_records
        if path.path not in paths_checkpoint_map or
        paths_stored_map[path.path] != paths_checkpoint_map[path.path]
    ]
    return paths_to_process


@overload
def extract_cdf_gz_files(
        data_raw_dir: Path,
        data_extracted_dir: Path) -> None:
    ...


@overload
def extract_cdf_gz_files(
        data_raw_paths: List[Path],
        data_extracted_dir: Path) -> None:
    ...


def extract_cdf_gz_files(
        data_raw_input: Union[Path, List[Path]],
        data_extracted_dir: Path) -> None:
    if isinstance(data_raw_input, Path):
        # Get sorted list of .cdf.gz files
        data_raw_paths = get_cdf_gz_files(data_raw_input)
    else:
        data_raw_paths = data_raw_input

    # Process each file
    for filename in data_raw_paths:
        output_filename = data_extracted_dir / filename.stem
        logger.info(f"Extracting {filename} to {output_filename}")
        if output_filename.exists():
            logger.info(f"Overriding {filename} - already exists.")

        # Extract the file
        with open(filename, 'rb') as f_in, \
                gzip.open(f_in) as f_decompressed, \
                open(output_filename, 'wb') as f_out:
            f_out.write(f_decompressed.read())
