from fastapi import APIRouter

crew_router = APIRouter(
    prefix="/crew",
    tags=["crew"],
)


@crew_router.post("/kickoff")
def crew_kickoff():
    return {"status": "OK"}
