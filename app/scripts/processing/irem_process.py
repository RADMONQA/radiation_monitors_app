#!/usr/bin/env python
"""irem_process.py: Process IREM data from CDF files to CSV files."""

import os
from pathlib import Path
import gzip
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
from spacepy import pycdf

# Optionally load .env file
load_dotenv("../.env")

# Data directories
# Path(os.getenv("DATA_DIR"))
DATA_DIR = Path("/home/szymon/repos/radem_ops/app/scripts/fetching")
DATA_IREM_DIR = DATA_DIR / "irem"
DATA_IREM_RAW_DIR = DATA_IREM_DIR / "raw"
DATA_IREM_EXTRACTED_DIR = DATA_IREM_DIR / "extracted"
DATA_IREM_CSV_DIR = DATA_IREM_DIR / "csv"


os.environ.setdefault("CDF_LIB", "/home/szymon/repos/cdf39_0-dist/src/lib")
# Verify CDF_LIB environment variable (required for pycdf)
if not os.environ.get('CDF_LIB'):
    raise EnvironmentError(
        "No CDF_LIB environment variable found for CDF file processing.")


class IremDataProcessor:
    def __init__(self):
        self.data_raw = DATA_IREM_RAW_DIR
        self.data_extracted = DATA_IREM_EXTRACTED_DIR
        self.data_csv = DATA_IREM_CSV_DIR

        self.datetime_filter = datetime(2022, 9, 1)

    def get_data_raw_filenames(self) -> List[Path]:
        filenames = [self.data_raw / dirname / filename
                     for dirname in os.listdir(self.data_raw)
                     for filename in os.listdir(self.data_raw / dirname)
                     if filename.endswith(".cdf.gz")]
        return sorted(filenames)

    def extract_data_raw(self) -> None:
        for filename in self.get_data_raw_filenames():
            output_filename = self.data_extracted / filename.stem
            if not output_filename.exists():
                print(f"Extracting {filename} to {output_filename}")
                self._extract_file(filename, output_filename)
            else:
                print(f"File {output_filename} already exists.")

    @staticmethod
    def _extract_file(input_filename: Path, output_filename: Path) -> None:
        with open(input_filename, 'rb') as f_in:
            with gzip.open(f_in) as f_decompressed, open(output_filename, 'wb') as f_out:
                f_out.write(f_decompressed.read())

    def read_irem_cdfs(self) -> List[pycdf.CDF]:
        cdfs = []
        for filename in sorted(self.data_extracted.glob("*.cdf")):
            if self._is_filename_in_datetime_filter(filename.name, self.datetime_filter):
                cdf = self._read_cdf(filename)
                if cdf:
                    cdfs.append(cdf)
        return cdfs

    def _read_cdf(self, cdf_path: Path) -> Optional[pycdf.CDF]:
        if not cdf_path.stat().st_size:
            print(f"File {cdf_path} is empty.")
            return None
        return pycdf.CDF(str(cdf_path))

    @staticmethod
    def _is_filename_in_datetime_filter(filename: str, datetime_filter: datetime) -> bool:
        date_str = filename[10:18]
        file_date = datetime.strptime(date_str, "%Y%m%d")
        return file_date >= datetime_filter

    def fix_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df['time'] = pd.to_datetime(df['time']).dt.floor('s')
        df.drop_duplicates(inplace=True)
        df.sort_values("time", inplace=True)
        return df

    def save_dataframe_to_csv(self, df: pd.DataFrame, name: str) -> None:
        latest_time = df['time'].max().strftime('%Y%m%dT%H%M%S')
        filename = self.data_csv / f"{name}_{latest_time}.csv"
        df.to_csv(filename, index=False)

    def process_pipeline(self, cdfs: List[pycdf.CDF], process_fn, name: str) -> None:
        df = pd.concat(process_fn(cdf) for cdf in cdfs)
        df = self.fix_dataframe(df)
        self.save_dataframe_to_csv(df, name)

    def process_irem_particles(self, cdf: pycdf.CDF, scaler_start: int, scaler_end: int) -> pd.DataFrame:
        # According do the IREM User Manual:
        # CDF label_COUNTERS always are:
        #   - [TC1 S12 S13 S14 S15 TC2 S25 C1 C2 C3 C4 TC3 S32 S33 S34]
        #   - and are 3 characters long e.g. "C1 "
        n = len(cdf["EPOCH"][...])
        times = cdf["EPOCH"][...]

        d_scalers = cdf["label_COUNTERS"][..., scaler_start:scaler_end]
        d = cdf["COUNTRATE"][..., scaler_start:scaler_end]

        time_col = np.repeat(times, len(d_scalers))
        scaler_col = np.tile(d_scalers, n)
        value_col = d.flatten()
        bin_col = np.tile(np.arange(1, 1 + len(d_scalers)), n)

        df = pd.DataFrame({
            "time": time_col,
            "scaler": scaler_col,
            "value": value_col,
            "bin": bin_col
        })

        return df

    def process_irem_d1(self, cdf: pycdf.CDF) -> pd.DataFrame:
        # According do the IREM User Manual:
        # label_COUNTERS[0:5] is [TC1 S12 S13 S14 S15] which is D1
        return self.process_irem_particles(cdf, 0, 5)

    def process_irem_d2(self, cdf: pycdf.CDF) -> pd.DataFrame:
        # According do the IREM User Manual:
        # label_COUNTERS[5:7] is [TC2 S25] which is D2
        return self.process_irem_particles(cdf, 5, 7)

    def process_irem_coincidence(self, cdf: pycdf.CDF) -> pd.DataFrame:
        # According do the IREM User Manual:
        # label_COUNTERS[7:11] is [C1 C2 C3 C4] which is D1+D2 Coincidence
        return self.process_irem_particles(cdf, 7, 11)

    def process_irem_d3(self, cdf: pycdf.CDF) -> pd.DataFrame:
        # According do the IREM User Manual:
        # label_COUNTERS[11:15] is [TC3 S32 S33 S34] which is D3
        return self.process_irem_particles(cdf, 11, 15)

    def process_all_data(self) -> None:
        irem_cdfs = self.read_irem_cdfs()

        print(f"Processing D1...")
        self.process_pipeline(
            irem_cdfs, self.process_irem_d1, "irem_d1")

        print(f"Processing D2...")
        self.process_pipeline(
            irem_cdfs, self.process_irem_d2, "irem_d2")

        print(f"Processing D3...")
        self.process_pipeline(
            irem_cdfs, self.process_irem_d3, "irem_d3")

        print(f"Processing Coincidence...")
        self.process_pipeline(
            irem_cdfs, self.process_irem_coincidence, "irem_coincidence")


if __name__ == "__main__":
    processor = IremDataProcessor()
    processor.extract_data_raw()
    processor.process_all_data()
