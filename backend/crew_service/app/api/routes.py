from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def system_check():
    return {"status": "OK"}