import logging
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.crew_endpoints import crew_router
from app.api.status_endpoints import status_router
from app.services.worker import Worker

logger = logging.getLogger(__name__)


def init_routers(app: FastAPI):
    """Register all API routers."""
    app.include_router(status_router)
    app.include_router(crew_router)


def init_worker(app: FastAPI):
    """Attach startup/shutdown handlers to manage the Worker lifecycle."""

    async def start_worker():
        logger.info("Starting worker...")
        worker = Worker()
        app.state.worker = worker
        asyncio.create_task(worker.start())
        logger.info("Worker started")

    async def stop_worker():
        worker: Worker | None = getattr(app.state, "worker", None)
        if worker:
            logger.info("Stopping worker...")
            await worker.stop()
            logger.info("Worker stopped")

    app.add_event_handler("startup", start_worker)
    app.add_event_handler("shutdown", stop_worker)


logger = logging.getLogger(__name__)


def create_app():
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_routers(app)
    init_worker(app)

    return app

app = create_app()
