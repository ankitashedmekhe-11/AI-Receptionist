from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.session import get_db
from models.customer import Customer
from models.call import Call
from models.appointment import Appointment
from routes.schemas import CustomerSummary

router = APIRouter(prefix="/customers", tags=["customers"])


def _build_customer_query(db: Session):
    call_counts = (
        db.query(
            Call.customer_id.label('customer_id'),
            func.count(Call.id).label('total_calls'),
            func.max(Call.timestamp).label('last_interaction'),
            func.max(Call.intent).label('latest_intent'),
        )
        .group_by(Call.customer_id)
        .subquery()
    )

    appointment_counts = (
        db.query(
            Appointment.customer_id.label('customer_id'),
            func.count(Appointment.id).label('total_appointments'),
        )
        .group_by(Appointment.customer_id)
        .subquery()
    )

    return (
        db.query(
            Customer.id,
            Customer.name,
            Customer.phone,
            func.coalesce(call_counts.c.total_calls, 0).label('total_calls'),
            func.coalesce(appointment_counts.c.total_appointments, 0).label('total_appointments'),
            call_counts.c.last_interaction,
            call_counts.c.latest_intent,
        )
        .outerjoin(call_counts, call_counts.c.customer_id == Customer.id)
        .outerjoin(appointment_counts, appointment_counts.c.customer_id == Customer.id)
    )

@router.get("", response_model=list[CustomerSummary])
def list_customers(db: Session = Depends(get_db)) -> list[CustomerSummary]:
    query = _build_customer_query(db).order_by(Customer.name)
    rows = query.all()
    return [
        CustomerSummary(
            id=row.id,
            name=row.name,
            phone=row.phone,
            total_calls=row.total_calls,
            total_appointments=row.total_appointments,
            last_interaction=row.last_interaction,
            latest_intent=row.latest_intent,
        ) for row in rows
    ]


@router.get("/{customer_id}", response_model=CustomerSummary)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> CustomerSummary:
    query = _build_customer_query(db).filter(Customer.id == customer_id)
    row = query.first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return CustomerSummary(
        id=row.id,
        name=row.name,
        phone=row.phone,
        total_calls=row.total_calls,
        total_appointments=row.total_appointments,
        last_interaction=row.last_interaction,
        latest_intent=row.latest_intent,
    )
