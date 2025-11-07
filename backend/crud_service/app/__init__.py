import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .db.connection import test_connection

from .api.status_endpoints import status_router
from .api.crew_endpoints import crew_router

logger = logging.getLogger(__name__)


def init_routers(app: FastAPI):
    app.include_router(status_router)
    app.include_router(crew_router)
    
async def on_startup():
    try:
        await test_connection()
    except Exception as e:
        logger.error(f"Error initializing database connection: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

def create_app():
    app = FastAPI()
    
    app.add_event_handler("startup", on_startup)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_routers(app)

    return app

app = create_app()