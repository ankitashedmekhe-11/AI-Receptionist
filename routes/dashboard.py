from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.session import get_db
from models.appointment import Appointment, AppointmentStatus
from models.call import Call
from models.customer import Customer
from routes.schemas import (
    AppointmentRead,
    CallRead,
    CustomerSummary,
    DashboardData,
    ServiceCount,
)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent


@router.get("/dashboard", response_class=FileResponse)
@router.get("/overview", response_class=FileResponse)
@router.get("/calls", response_class=FileResponse)
@router.get("/appointments", response_class=FileResponse)
@router.get("/customers", response_class=FileResponse)
@router.get("/analytics", response_class=FileResponse)
def dashboard_page() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "dashboard.html")


@router.get("/settings", response_class=FileResponse)
def settings_page() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "settings.html")


@router.get("/dashboard/data", response_model=DashboardData)
def dashboard_data(db: Session = Depends(get_db)) -> DashboardData:
    today = datetime.utcnow().date()

    today_schedule = (
        db.query(Appointment)
        .filter(
            Appointment.status == AppointmentStatus.SCHEDULED,
            Appointment.date == today,
        )
        .order_by(Appointment.time)
        .limit(10)
        .all()
    )

    upcoming_appointments = (
        db.query(Appointment)
        .filter(Appointment.status == AppointmentStatus.SCHEDULED)
        .order_by(Appointment.date, Appointment.time)
        .limit(15)
        .all()
    )

    recent_calls = db.query(Call).order_by(Call.timestamp.desc()).limit(12).all()

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

    customers = []
    customer_rows = (
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
        .order_by(call_counts.c.last_interaction.desc().nulls_last())
        .limit(10)
        .all()
    )
    for row in customer_rows:
        customers.append(
            CustomerSummary(
                id=row.id,
                name=row.name,
                phone=row.phone,
                total_calls=row.total_calls,
                total_appointments=row.total_appointments,
                last_interaction=row.last_interaction,
                latest_intent=row.latest_intent,
            )
        )

    appointments_today = db.query(Appointment).filter(
        Appointment.date == today,
        Appointment.status == AppointmentStatus.SCHEDULED,
    ).count()
    active_appointments = db.query(Appointment).filter(
        Appointment.status == AppointmentStatus.SCHEDULED
    ).count()
    recent_call_count = db.query(Call).filter(
        Call.timestamp >= today,
        Call.intent.in_(["book", "cancel", "reschedule", "enquire"]),
    ).count()

    ai_bookings = db.query(Appointment).filter(
        Appointment.status == AppointmentStatus.SCHEDULED,
        Appointment.customer_id.is_not(None),
    ).count()

    missed_calls = db.query(Call).filter(Call.intent == 'missed').count()

    MEANINGFUL_INTENTS = {"book", "cancel", "reschedule", "enquire"}

    calls_by_intent = {
        row.intent: row.count
        for row in db.query(Call.intent, func.count(Call.id).label("count"))
        .group_by(Call.intent)
        .order_by(func.count(Call.id).desc())
        .all()
        if row.intent and row.intent in MEANINGFUL_INTENTS
    }

    appointments_by_status = {
        row.status.value: row.count
        for row in db.query(Appointment.status, func.count(Appointment.id).label("count"))
        .group_by(Appointment.status)
        .all()
    }

    top_services = [
        ServiceCount(service=row.service, count=row.count)
        for row in db.query(Appointment.service, func.count(Appointment.id).label("count"))
        .group_by(Appointment.service)
        .order_by(func.count(Appointment.id).desc())
        .limit(5)
        .all()
    ]

    return {
        "reception_status": "listening",
        "appointments_today": appointments_today,
        "active_appointments": active_appointments,
        "recent_call_count": recent_call_count,
        "missed_calls": missed_calls,
        "ai_bookings": ai_bookings,
        "today_schedule": today_schedule,
        "upcoming_appointments": upcoming_appointments,
        "recent_calls": recent_calls,
        "customers": customers,
        "appointments_by_status": appointments_by_status,
        "calls_by_intent": calls_by_intent,
        "top_services": top_services,
    }
