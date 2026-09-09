from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from models.appointment import Appointment, AppointmentStatus
from models.customer import Customer
from routes.schemas import AppointmentCreate, AppointmentRead, AppointmentUpdate

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _get_appointment_or_404(db: Session, appointment_id: int) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    return appointment


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
) -> Appointment:
    customer = db.get(Customer, payload.customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    appointment = Appointment(
        customer_id=payload.customer_id,
        service=payload.service,
        date=payload.date,
        time=payload.time,
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("", response_model=list[AppointmentRead])
def list_appointments(db: Session = Depends(get_db)) -> list[Appointment]:
    return db.query(Appointment).order_by(Appointment.date, Appointment.time).all()


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
) -> Appointment:
    return _get_appointment_or_404(db, appointment_id)


@router.patch("/{appointment_id}", response_model=AppointmentRead)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
) -> Appointment:
    appointment = _get_appointment_or_404(db, appointment_id)
    if appointment.status == AppointmentStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update a cancelled appointment",
        )
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(appointment, field, value)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/{appointment_id}/cancel", response_model=AppointmentRead)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
) -> Appointment:
    appointment = _get_appointment_or_404(db, appointment_id)
    if appointment.status == AppointmentStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Appointment is already cancelled",
        )
    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)
    return appointment
