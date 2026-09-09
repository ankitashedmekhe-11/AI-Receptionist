from datetime import datetime
from datetime import date as Date
from datetime import time as Time

from pydantic import BaseModel, ConfigDict, Field

from models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    customer_id: int
    service: str = Field(..., min_length=1, max_length=255)
    date: Date
    time: Time


class SettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    value: str


class SettingUpdate(BaseModel):
    value: str


class AppointmentUpdate(BaseModel):
    service: str | None = Field(None, min_length=1, max_length=255)
    date: Date | None = None
    time: Time | None = None
    status: AppointmentStatus | None = None


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    customer_name: str | None = None
    service: str
    date: Date
    time: Time
    status: AppointmentStatus


class CallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int | None
    customer_name: str | None = None
    timestamp: datetime
    transcript: str | None
    intent: str | None
    resolution: str | None


class CustomerSummary(BaseModel):
    id: int
    name: str
    phone: str | None = None
    total_calls: int
    total_appointments: int
    last_interaction: datetime | None = None
    latest_intent: str | None = None


class ServiceCount(BaseModel):
    service: str
    count: int


class DashboardData(BaseModel):
    reception_status: str
    appointments_today: int
    active_appointments: int
    recent_call_count: int
    missed_calls: int
    ai_bookings: int
    today_schedule: list[AppointmentRead]
    upcoming_appointments: list[AppointmentRead]
    recent_calls: list[CallRead]
    customers: list[CustomerSummary]
    appointments_by_status: dict[str, int]
    calls_by_intent: dict[str, int]
    top_services: list[ServiceCount]
