from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from models.call import Call
from routes.schemas import CallRead

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("", response_model=list[CallRead])
def list_calls(db: Session = Depends(get_db)) -> list[Call]:
    return db.query(Call).order_by(Call.timestamp.desc()).all()


@router.get("/{call_id}", response_model=CallRead)
def get_call(call_id: int, db: Session = Depends(get_db)) -> Call:
    call = db.get(Call, call_id)
    if call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found",
        )
    return call
