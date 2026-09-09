from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from models.setting import Setting
from routes.schemas import SettingRead, SettingUpdate
from services import business_profile as bp

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ── Existing settings CRUD ─────────────────────────────────────────────────────

@router.get("", response_model=list[SettingRead])
def get_settings(db: Session = Depends(get_db)) -> list[Setting]:
    return db.query(Setting).all()


@router.put("/{key}", response_model=SettingRead)
def update_setting(key: str, payload: SettingUpdate, db: Session = Depends(get_db)) -> Setting:
    setting = db.get(Setting, key)
    if setting is None:
        setting = Setting(key=key, value=payload.value)
        db.add(setting)
    else:
        setting.value = payload.value
    db.commit()
    db.refresh(setting)
    # Invalidate business profile cache whenever any setting changes
    bp.invalidate_cache()
    return setting


# ── Business profile parse-preview endpoint ────────────────────────────────────

class ParseProfileRequest(BaseModel):
    description: str


class ParseProfileResponse(BaseModel):
    name: str
    services: list[str]
    open_time: str | None
    close_time: str | None
    open_days: list[str]
    location: str
    hours_display: str
    services_display: str
    is_configured: bool


@router.post("/parse-profile", response_model=ParseProfileResponse)
def parse_profile_preview(payload: ParseProfileRequest) -> ParseProfileResponse:
    """
    Parse a business description and return the extracted structured profile.
    Used by the Settings page 'Preview' button so the owner can verify the AI
    understood their business correctly before going live.
    """
    profile = bp.parse_profile(payload.description)
    return ParseProfileResponse(
        name=profile.name,
        services=profile.services,
        open_time=bp._fmt_time(profile.open_time) if profile.open_time else None,
        close_time=bp._fmt_time(profile.close_time) if profile.close_time else None,
        open_days=profile.open_days,
        location=profile.location,
        hours_display=profile.hours_display(),
        services_display=profile.services_display(),
        is_configured=profile.is_configured(),
    )
