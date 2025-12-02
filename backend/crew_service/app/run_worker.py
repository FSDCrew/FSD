import asyncio
import logging
import signal
import sys

from app.services.worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_worker():
    worker = Worker()
    logger.info("💼 Worker starting...")

    try:
        await worker.start()
    except asyncio.CancelledError:
        logger.info("Worker cancelled")
    finally:
        logger.info("Shutting down worker...")
        await worker.stop()


def install_signal_handlers(loop, worker_task):
    """Install POSIX signal handlers, skip for Windows."""
    if sys.platform.startswith("win"):
        logger.info("Windows detected — skipping SIGINT/SIGTERM handlers")
        return

    def shutdown(sig):
        logger.info("Received %s — stopping worker...", sig.name)
        worker_task.cancel()

    loop.add_signal_handler(signal.SIGINT, lambda: shutdown(signal.SIGINT))
    loop.add_signal_handler(signal.SIGTERM, lambda: shutdown(signal.SIGTERM))


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    worker_task = loop.create_task(run_worker())

    # Cross-platform signal setup
    install_signal_handlers(loop, worker_task)

    try:
        loop.run_until_complete(worker_task)
    except KeyboardInterrupt:
        # Windows sends KeyboardInterrupt instead of SIGINT
        logger.info("CTRL+C pressed — cancelling worker...")
        worker_task.cancel()
        loop.run_until_complete(worker_task)
    finally:
        pending = asyncio.all_tasks(loop)
        if pending:
            logger.info(f"Waiting for {len(pending)} pending task(s) to finish...")
            for task in pending:
                task.cancel()

            try:
                loop.run_until_complete(
                    asyncio.wait_for(
                        asyncio.gather(*pending, return_exceptions=True),
                        timeout=10.0
                    )
                )
            except asyncio.TimeoutError:
                logger.warning("Some tasks did not finish within timeout, closing loop anyway")

        loop.close()
        logger.info("Worker stopped.")


if __name__ == "__main__":
    main()
