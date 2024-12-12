from . import utils


def fetch_irem_data() -> None:
    utils.execute_script("fetch_irem.sh")


def fetch_radem_data() -> None:
    utils.execute_script("fetch_radem.sh")
