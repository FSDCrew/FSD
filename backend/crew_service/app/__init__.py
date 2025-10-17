from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# from config import settings
# from app.database import engine, Base
from .api.routes import router as crew_router


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

    _app.include_router(crew_router, prefix="/crew", tags=["Crew"])

    return _app

# Create the app instance for uvicorn to find
app = create_app()