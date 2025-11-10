import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3

from config import settings

from .db.connection import test_connection

from .api.status_endpoints import status_router
from .api.crew_endpoints import crew_router
from .api.task_endpoints import task_router
from .api.user_endpoints import user_router

logger = logging.getLogger(__name__)


def init_routers(app: FastAPI):
    app.include_router(status_router)
    app.include_router(crew_router)
    app.include_router(task_router)
    app.include_router(user_router)
    
def init_s3_client(app: FastAPI):
    """Initialize S3 client using settings from config.py"""
    app.state.s3_client = boto3.client(
        "s3",
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key
    )
    
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

    init_s3_client(app)
    init_routers(app)

    return app

app = create_app()