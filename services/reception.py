from __future__ import annotations

from datetime import date, datetime, time, timedelta
import re
from typing import Optional

from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.appointment import Appointment, AppointmentStatus
from models.customer import Customer

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}


# ── Text normalization ─────────────────────────────────────────────────────────

def _normalize_text(text: str | None) -> str:
    return text.strip().lower() if text else ""


def _parse_number_word(text: str) -> int | None:
    return NUMBER_WORDS.get(text.lower())


def _to_time(hour: int, minute: int, ampm: str | None) -> time:
    if ampm:
        ampm = ampm.lower()
        if ampm == "pm" and hour != 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
    return time(hour=hour, minute=minute)


def _parse_time_strings(text: str) -> list[time]:
    cleaned = _normalize_text(text)
    times: list[time] = []

    for match in re.finditer(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", cleaned, flags=re.I):
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        ampm = match.group(3)
        try:
            times.append(_to_time(hour, minute, ampm))
        except ValueError:
            continue

    for match in re.finditer(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(am|pm)\b",
        cleaned, flags=re.I,
    ):
        hour = _parse_number_word(match.group(1))
        minute = 0
        ampm = match.group(2)
        if hour is not None:
            times.append(_to_time(hour, minute, ampm))

    return times


def _parse_time(text: str | None) -> time | None:
    if not text:
        return None
    times = _parse_time_strings(text)
    return times[0] if times else None


def _parse_time_tuple(text: str | None) -> tuple[time | None, time | None]:
    if not text:
        return (None, None)
    times = _parse_time_strings(text)
    if len(times) >= 2:
        return times[0], times[1]
    return (times[0], None) if times else (None, None)


def _parse_month_day(text: str) -> date | None:
    cleaned = _normalize_text(text)
    match = re.search(
        r"\b(?:on\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?\b",
        cleaned, flags=re.I,
    )
    if match:
        month = MONTHS[match.group(1).lower()]
        day = int(match.group(2))
        year = date.today().year
        return date(year, month, day)

    match = re.search(
        r"\b(?:on\s+)?(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+of\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b",
        cleaned, flags=re.I,
    )
    if match:
        day = int(match.group(1))
        month = MONTHS[match.group(2).lower()]
        year = date.today().year
        return date(year, month, day)

    return None


def _next_weekday(target: str) -> date | None:
    weekday_text = target.lower().strip()
    if weekday_text not in WEEKDAYS:
        return None
    today = date.today()
    target_idx = WEEKDAYS[weekday_text]
    delta = (target_idx - today.weekday() + 7) % 7
    if delta == 0:
        delta = 7
    return today + timedelta(days=delta)


def _parse_date(text: str | None) -> date | None:
    if not text:
        return None
    cleaned = _normalize_text(text)
    if "today" in cleaned:
        return date.today()
    if "tomorrow" in cleaned:
        return date.today() + timedelta(days=1)
    if "next week" in cleaned:
        return _next_weekday("monday")
    match = re.search(r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", cleaned)
    if match:
        return _next_weekday(match.group(1))
    month_day = _parse_month_day(cleaned)
    if month_day:
        return month_day
    return None


def _describe_datetime(appointment_date: date | None, appointment_time: time | None) -> str:
    pieces: list[str] = []
    if appointment_date is not None:
        pieces.append(appointment_date.strftime("%A, %b %d"))
    if appointment_time is not None:
        pieces.append(appointment_time.strftime("%I:%M %p").lstrip("0"))
    return " at ".join(pieces) if pieces else ""


# ── Customer helpers ───────────────────────────────────────────────────────────

def _find_customer(db: Session, name: str | None) -> Customer | None:
    if name:
        name_fragment = re.sub(r"^(dr|doctor|mr|mrs|ms|miss|prof)\.?\s+", "", name, flags=re.I).strip()
        customer = (
            db.query(Customer)
            .filter(Customer.name.ilike(f"%{name_fragment}%"))
            .first()
        )
        if customer:
            return customer
    return None


def _ensure_customer(db: Session, customer_name: str | None) -> Customer | None:
    customer = _find_customer(db, customer_name)
    if customer:
        return customer
    if customer_name:
        customer = Customer(name=customer_name)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
    return None


def _find_scheduled_appointment(
    db: Session,
    customer_id: int | None,
    service: str | None,
    target_date: date | None,
    target_time: time | None,
) -> Appointment | None:
    query = db.query(Appointment).filter(Appointment.status == AppointmentStatus.SCHEDULED)
    if customer_id is not None:
        query = query.filter(Appointment.customer_id == customer_id)
    if service:
        query = query.filter(Appointment.service.ilike(f"%{service}%"))
    if target_date is not None:
        query = query.filter(Appointment.date == target_date)
    if target_time is not None:
        query = query.filter(Appointment.time == target_time)
    appointment = query.order_by(Appointment.date, Appointment.time).first()
    if appointment:
        return appointment

    # Fallback: any scheduled appointment for this customer
    if customer_id is not None:
        return (
            db.query(Appointment)
            .filter(
                Appointment.status == AppointmentStatus.SCHEDULED,
                Appointment.customer_id == customer_id,
            )
            .order_by(Appointment.date, Appointment.time)
            .first()
        )
    return None


# ── Business profile helpers ───────────────────────────────────────────────────

def _business_name(business_profile) -> str:
    if business_profile and business_profile.name and business_profile.name != "Our Business":
        return business_profile.name
    return "our business"


def _validate_service(service: str | None, business_profile) -> tuple[str | None, str | None]:
    """
    Validate service against the business profile.
    Returns (canonical_service, error_message).
    If no profile or no services configured, passes through whatever was extracted.
    """
    if not business_profile or not business_profile.services:
        return service, None

    if not service:
        return None, None  # Missing — handled separately

    matched = business_profile.match_service(service)
    if matched:
        return matched, None

    services_list = business_profile.services_display()
    return None, (
        f"I'm sorry, I didn't catch which service you'd like. "
        f"We offer {services_list}. Which one would you like to book?"
    )


def _validate_time(appointment_time: time | None, business_profile) -> str | None:
    """Returns an error message if the time is outside business hours, else None."""
    if appointment_time is None or business_profile is None:
        return None
    if not business_profile.is_within_hours(appointment_time):
        hours = business_profile.hours_display()
        return (
            f"I'm sorry, we're not open at that time. "
            f"We're available {hours}. "
            f"Would you like to book within those hours?"
        )
    return None


# ── Action handlers ────────────────────────────────────────────────────────────

def book_appointment(
    db: Session,
    intent: str,
    entities: dict[str, str | None],
    business_profile=None,
) -> dict[str, object]:
    name = entities.get("name")
    raw_service = entities.get("service")
    appointment_date = _parse_date(entities.get("date"))
    appointment_time = _parse_time(entities.get("time"))

    biz = _business_name(business_profile)

    # ── Validate service against profile ──────────────────────────────────────
    service, svc_error = _validate_service(raw_service, business_profile)
    if svc_error:
        return {
            "intent": intent, "success": False, "message": svc_error,
            "customer_id": None, "needs_clarification": True,
        }

    # ── Validate time against hours ───────────────────────────────────────────
    time_error = _validate_time(appointment_time, business_profile)
    if time_error:
        return {
            "intent": intent, "success": False, "message": time_error,
            "customer_id": None, "needs_clarification": True,
        }

    # ── Ask for missing info ONE field at a time ──────────────────────────────
    if not service:
        if business_profile and business_profile.services:
            svcs = business_profile.services_display()
            msg = f"I'd be happy to help you book! We offer {svcs}. Which service would you like?"
        else:
            msg = "I'd be happy to help you book! What service would you like?"
        return {
            "intent": intent, "success": False, "message": msg,
            "customer_id": None, "needs_clarification": True,
        }

    if appointment_date is None:
        msg = f"Great, a {service}! What date would you like to come in?"
        return {
            "intent": intent, "success": False, "message": msg,
            "customer_id": None, "needs_clarification": True,
        }

    if appointment_time is None:
        date_str = appointment_date.strftime("%A, %b %d")
        msg = f"Perfect, {date_str} it is. What time would you like?"
        if business_profile and business_profile.hours_display():
            msg += f" We're open {business_profile.hours_display()}."
        return {
            "intent": intent, "success": False, "message": msg,
            "customer_id": None, "needs_clarification": True,
        }

    if not name:
        msg = "May I get your name please?"
        return {
            "intent": intent, "success": False, "message": msg,
            "customer_id": None, "needs_clarification": True,
        }

    # ── All info gathered — create appointment ────────────────────────────────
    customer = _ensure_customer(db, name)
    if customer is None:
        return {
            "intent": intent, "success": False,
            "message": "I'm sorry, I couldn't locate or create your profile. Please call back and provide your name.",
            "customer_id": None,
        }

    appointment = Appointment(
        customer_id=customer.id,
        service=service,
        date=appointment_date,
        time=appointment_time,
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    dt_str = _describe_datetime(appointment_date, appointment_time)
    return {
        "intent": intent,
        "success": True,
        "message": (
            f"You're all set, {customer.name}! I've booked your {service} for {dt_str}. "
            f"Is there anything else I can help you with today?"
        ),
        "appointment_id": appointment.id,
        "customer_id": customer.id,
    }


def cancel_appointment(
    db: Session,
    intent: str,
    entities: dict[str, str | None],
    business_profile=None,
) -> dict[str, object]:
    customer = _find_customer(db, entities.get("name"))
    service = entities.get("service")
    target_date = _parse_date(entities.get("date"))
    target_time = _parse_time(entities.get("time"))

    appointment = _find_scheduled_appointment(
        db, customer.id if customer else None, service, target_date, target_time,
    )
    if appointment is None:
        if not customer:
            return {
                "intent": intent, "success": False,
                "message": "To cancel, may I get your name to look up your appointment?",
                "customer_id": None,
                "needs_clarification": True,
            }
        return {
            "intent": intent, "success": False,
            "message": "I couldn't find a scheduled appointment matching those details. Could you double-check the date or service?",
            "customer_id": customer.id,
        }

    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)

    dt_str = _describe_datetime(appointment.date, appointment.time)
    return {
        "intent": intent,
        "success": True,
        "message": (
            f"Done — I've cancelled your {appointment.service} appointment on {dt_str}. "
            f"Is there anything else I can help you with?"
        ),
        "appointment_id": appointment.id,
        "customer_id": appointment.customer_id,
    }


def reschedule_appointment(
    db: Session,
    intent: str,
    entities: dict[str, str | None],
    business_profile=None,
) -> dict[str, object]:
    customer = _find_customer(db, entities.get("name"))
    service = entities.get("service")
    target_date = _parse_date(entities.get("date"))
    old_time, new_time = _parse_time_tuple(entities.get("time"))

    if old_time is None and new_time is None and target_date is None:
        return {
            "intent": intent, "success": False,
            "message": "When would you like to reschedule to? Please tell me the new date or time.",
            "customer_id": customer.id if customer else None,
            "needs_clarification": True,
        }

    # Validate the new time against business hours
    check_time = new_time or old_time
    time_error = _validate_time(check_time, business_profile)
    if time_error:
        return {
            "intent": intent, "success": False, "message": time_error,
            "customer_id": customer.id if customer else None, "needs_clarification": True,
        }

    appointment = _find_scheduled_appointment(
        db, customer.id if customer else None, service, target_date, old_time,
    )
    if appointment is None:
        if not customer:
            return {
                "intent": intent, "success": False,
                "message": "To reschedule, may I get your name to look up your appointment?",
                "customer_id": None,
                "needs_clarification": True,
            }
        return {
            "intent": intent, "success": False,
            "message": "I couldn't find a scheduled appointment to reschedule. Could you tell me the service or current date?",
            "customer_id": customer.id,
        }

    new_date = target_date or appointment.date
    new_time = new_time or old_time or appointment.time
    appointment.date = new_date
    appointment.time = new_time
    db.commit()
    db.refresh(appointment)

    dt_str = _describe_datetime(new_date, new_time)
    return {
        "intent": intent,
        "success": True,
        "message": f"Done! I've rescheduled your {appointment.service} to {dt_str}. Is there anything else you need?",
        "appointment_id": appointment.id,
        "customer_id": appointment.customer_id,
    }


def handle_enquiry(
    intent: str,
    entities: dict[str, str | None],
    business_profile=None,
) -> dict[str, object]:
    """Handle informational queries using the business profile."""
    if business_profile and business_profile.is_configured():
        parts = []
        if business_profile.services:
            parts.append(f"We offer {business_profile.services_display()}")
        if business_profile.hours_display():
            parts.append(f"we're open {business_profile.hours_display()}")
        if business_profile.location:
            parts.append(f"we're located in {business_profile.location}")
        msg = ". ".join(parts) + ". Would you like to book an appointment?"
    else:
        msg = "We'd be happy to help you. Would you like to book, cancel, or reschedule an appointment?"

    return {
        "intent": intent,
        "success": True,
        "message": msg,
        "customer_id": None,
    }


# ── Dispatcher ─────────────────────────────────────────────────────────────────

def apply_nlu_action(
    transcript: str,
    nlu_result: dict[str, object],
    business_profile=None,
) -> dict[str, object]:
    intent = nlu_result.get("intent", "unknown")
    entities = nlu_result.get("entities", {})

    biz = _business_name(business_profile)

    if intent == "unknown":
        return {
            "intent": intent,
            "success": False,
            "message": (
                f"Thank you for calling {biz}! "
                f"I can help you book, cancel, or reschedule an appointment. "
                f"Which would you like?"
            ),
            "customer_id": None,
            "needs_clarification": True,
        }

    if intent == "enquire":
        return handle_enquiry(intent, entities, business_profile)

    if intent == "end_call":
        return {
            "intent": intent,
            "success": True,
            "message": f"Thank you for calling {biz}. Goodbye!",
            "customer_id": None,
            "end_call": True,
        }

    if intent not in {"book", "cancel", "reschedule"}:
        return {
            "intent": intent,
            "success": False,
            "message": "I can help you book, cancel, or reschedule an appointment. Which would you like?",
            "customer_id": None,
        }

    db = SessionLocal()
    try:
        if intent == "book":
            return book_appointment(db, intent, entities, business_profile)
        if intent == "cancel":
            return cancel_appointment(db, intent, entities, business_profile)
        if intent == "reschedule":
            return reschedule_appointment(db, intent, entities, business_profile)
    finally:
        db.close()

    return {
        "intent": intent, "success": False,
        "message": "No action executed.", "customer_id": None,
    }
