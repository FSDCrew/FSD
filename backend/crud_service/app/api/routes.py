from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.service import auth
from app.models.models import CrewRun
from db.dbconfig import get_db


router = APIRouter()

@router.get("/health")
def system_check():
    return {"status": "OK"}


@router.get("/runs")
def get_crew_runs(
    current_user: dict = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")

    try:
        runs = db.query(CrewRun).filter(CrewRun.user_id == user_id).all()

        if not runs:
            return {"message": f"No runs found for user id: {user_id}"}

        return runs

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching crews for user id: {user_id}, {e}")