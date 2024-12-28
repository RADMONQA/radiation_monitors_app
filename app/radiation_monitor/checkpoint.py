from pathlib import Path
from typing import List
from dataclasses import asdict, dataclass
import json
import logging
from . import env

logger = logging.getLogger(__name__)


@dataclass
class PathRecord:
    path: str
    checksum: str
    is_processed: bool


@dataclass
class DataCheckpoint:
    """
    Checkpoint for the radiation monitor application.
    """

    irem_paths_processed: List[PathRecord]

    @staticmethod
    def get_checkpoint_path() -> Path:
        return env.CHECKPOINT_DIR / "checkpoint.json"

    @staticmethod
    def read() -> "DataCheckpoint":
        if not DataCheckpoint.get_checkpoint_path().exists():
            return DataCheckpoint(irem_paths_processed=[])

        try:
            with open(DataCheckpoint.get_checkpoint_path(), "r") as f:
                data = json.load(f)

                path_records = [
                    PathRecord(
                        path=str(record["path"]),
                        checksum=str(record["checksum"]),
                        is_processed=bool(record["is_processed"]),
                    )
                    for record in data.get("irem_paths_processed", [])
                ]
                return DataCheckpoint(irem_paths_processed=path_records)
        except Exception as e:
            logger.error(
                "Error reading checkpoint (empty checkpoint will be created): "
                f"{e}")
            return DataCheckpoint(irem_paths_processed=[])

    def write(self) -> None:
        checkpoint_path = DataCheckpoint.get_checkpoint_path()
        checkpoint_data = asdict(self)

        with open(checkpoint_path, "w") as file:
            json.dump(checkpoint_data, file, indent=4)
