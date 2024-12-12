import os

from . import utils


def fetch_irem_data() -> None:
    utils.execute_script("fetch_irem.sh")


def fetch_radem_data() -> None:
    utils.execute_script("fetch_radem.sh")


def fetch_all() -> None:
    if os.environ.get("IS_USING_RADEM", "0") != "0":
        fetch_radem_data()

    if os.environ.get("IS_USING_IREM", "0") != "0":
        fetch_irem_data()
