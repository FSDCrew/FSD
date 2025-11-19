from fastapi import APIRouter

status_router = APIRouter(
    prefix="/status",
    tags=["status"],
)

@status_router.get("/health")
def system_check():
    return {"status": "OK"}