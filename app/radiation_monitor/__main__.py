import sys
import logging
from dotenv import load_dotenv

from . import fetchers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logging.getLogger().setLevel(logging.DEBUG)

# Load environment variables
if not load_dotenv():
    logger.debug("No .env file found")
else:
    logger.debug("Loaded .env file")


def main():
    """Main entry point for the radiation monitor application."""
    try:

        fetchers.fetch_irem_data()

    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        # Cleanup code here
        # Close connections
        # Save final state
        logger.info("Monitor shutdown complete")


if __name__ == "__main__":
    main()
