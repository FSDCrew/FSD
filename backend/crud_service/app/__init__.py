from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3

from config import settings
# from app.database import engine, Base
from .api.routes import router as crud_router


_app: FastAPI = None

def create_app():
    global _app
    if _app:
        return _app

    _app = FastAPI()

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # Consider restricting this in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- S3 Client Initialization ---
    _app.state.s3_client = boto3.client(
        "s3",
        region_name=settings.s3_region, # Match Pydantic variable name
        aws_access_key_id=settings.s3_access_key, # Match Pydantic variable name
        aws_secret_access_key=settings.s3_secret_key # Match Pydantic variable name
    )

    # --- Database Initialization (REMOVED) ---
    # try:
    #     Base.metadata.create_all(bind=engine)
    #     print("Database tables created successfully")
    # except Exception as e:
    #     print(f"Error creating database tables: {e}")

    # --- Router Registration ---
    _app.include_router(crud_router, prefix="/crud", tags=["CRUD"])

    return _app

# Create the app instance for uvicorn to find
app = create_app()