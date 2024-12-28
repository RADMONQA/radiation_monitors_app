import logging

from radiation_monitor.checkpoint import DataCheckpoint
from radiation_monitor.influxdb_utils import InfluxDbUtils
import radiation_monitor.env as env

from .jobs import irem


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.DEBUG)

# Configure influxdb
irem_influxdb_utils = InfluxDbUtils(
    token=env.INFLUXDB_TOKEN,
    org=env.INFLUXDB_ORG,
    bucket=env.INFLUXDB_IREM_BUCKET,
    url=env.INFLUXDB_URL,
)
radem_influxdb_utils = InfluxDbUtils(
    token=env.INFLUXDB_TOKEN,
    org=env.INFLUXDB_ORG,
    bucket=env.INFLUXDB_RADEM_BUCKET,
    url=env.INFLUXDB_URL,
)


def load_checkpoint() -> DataCheckpoint:
    return DataCheckpoint.read()


def job() -> None:
    irem.run_irem_job(irem_influxdb_utils)


def main():
    """Main entry point for the radiation monitor application."""
    # try:
    job()
    # except Exception as e:
    #     logger.critical(f"Fatal error: {e}")
    #     sys.exit(1)
    # finally:
    #     # Cleanup code here
    #     # Close connections
    #     # Save final state
    #     logger.info("Monitor shutdown complete")


if __name__ == "__main__":
    main()
