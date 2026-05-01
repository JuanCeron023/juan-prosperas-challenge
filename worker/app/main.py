"""Worker entry point.

Starts the asyncio consumer loop that polls SQS and processes report jobs.
"""

import asyncio
import logging
import signal

from worker.app.consumer import consume_loop
from worker.app.processor import process_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Start the worker with graceful shutdown support."""
    shutdown_event = asyncio.Event()

    def handle_signal(sig):
        logger.info(f"Received signal {sig}, shutting down...")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal, sig)

    logger.info("Worker starting...")
    await consume_loop(process_report, shutdown_event)
    logger.info("Worker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
