from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    calls: Mapped[list["Call"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )
