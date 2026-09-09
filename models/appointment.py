import enum
from datetime import date, time

from sqlalchemy import Date, Enum, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    service: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus),
        nullable=False,
        default=AppointmentStatus.SCHEDULED,
    )

    customer: Mapped["Customer"] = relationship(back_populates="appointments")

    @property
    def customer_name(self) -> str:
        return self.customer.name if self.customer else "Unknown"
