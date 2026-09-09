"""
services/business_profile.py
─────────────────────────────
Parses a free-text business description entered by the business owner into a
structured BusinessProfile that the AI uses at call-time.

Example input:
    "We are a hair salon called Style & Co. We offer haircuts, beard trims,
     shaves, fades, hair coloring and hair treatments. We are open Monday to
     Saturday from 9 AM to 7 PM. We are located in Pune, Maharashtra."

Extracted profile:
    name     = "Style & Co."
    services = ["haircuts", "beard trims", "shaves", "fades",
                "hair coloring", "hair treatments"]
    open_time  = time(9, 0)
    close_time = time(19, 0)
    open_days  = ["monday", "tuesday", ..., "saturday"]
    location   = "Pune, Maharashtra"
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from datetime import time
from typing import Optional

# ── Constants ─────────────────────────────────────────────────────────────────

WEEKDAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

OFFER_KEYWORDS = [
    "offer", "offers", "provide", "provides", "specialise in", "specialize in",
    "specialises in", "specializes in", "services include", "service include",
    "services are", "we do", "including", "such as", "like", "business of",
    "salon for", "shop for"
]

NAME_PATTERNS = [
    r"(?:called|named|known as|name is)\s+([A-Za-z0-9\s&'\-\.]{1,50}?)(?:\s*[\.\,\n]|\s+(?:we|our|is|are|and)\b|$)",
    r"(?:we are|i am|this is|welcome to)\s+(?:a\s+\w+\s+)?([A-Za-z0-9\s&'\-\.]{1,50}?)(?:\s*[\.\,\n]|\s+(?:we|our|is|are|and)\b|$)",
    r"^([A-Z][A-Za-z0-9\s&'\-\.]{1,40})[\.\,]",
]

TIME_WORD_MAP = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}

# ── Dataclass ──────────────────────────────────────────────────────────────────

@dataclass
class BusinessProfile:
    name: str = "Our Business"
    services: list[str] = field(default_factory=list)
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    open_days: list[str] = field(default_factory=list)
    location: str = ""
    raw_description: str = ""

    def is_configured(self) -> bool:
        """Returns True if a meaningful profile was parsed."""
        return bool(self.services or self.open_time or self.name != "Our Business")

    def services_display(self) -> str:
        """Human-readable comma list for TTS responses."""
        if not self.services:
            return "our services"
        if len(self.services) == 1:
            return self.services[0]
        return ", ".join(self.services[:-1]) + " and " + self.services[-1]

    def hours_display(self) -> str:
        """Human-readable hours string for TTS."""
        parts = []
        if self.open_days:
            days = self.open_days
            if days == WEEKDAY_ORDER[:5]:
                parts.append("Monday to Friday")
            elif days == WEEKDAY_ORDER[:6]:
                parts.append("Monday to Saturday")
            elif days == WEEKDAY_ORDER:
                parts.append("every day")
            else:
                parts.append(" to ".join([days[0].capitalize(), days[-1].capitalize()]))
        if self.open_time and self.close_time:
            parts.append(
                f"{_fmt_time(self.open_time)} to {_fmt_time(self.close_time)}"
            )
        return ", ".join(parts) if parts else ""

    def is_within_hours(self, t: time) -> bool:
        """Returns True if time t is within open/close hours."""
        if self.open_time is None or self.close_time is None:
            return True  # no restriction configured — allow all times
        return self.open_time <= t <= self.close_time

    def match_service(self, raw: str) -> Optional[str]:
        """
        Case-insensitive fuzzy match of raw against configured services.
        Returns the canonical service name if matched, else None.
        Handles:
          - Exact match:           "haircut"  → "haircuts"
          - No-space match:        "hair cut" → "haircuts"
          - Partial word overlap:  "beard trimming" → "beard trims"
          - Singular/plural:       "shave" → "shaves"
        """
        if not raw or not self.services:
            return None

        # Normalize: lowercase, strip punctuation
        raw_norm = re.sub(r"[^\w\s]", "", raw.lower()).strip()
        raw_nospace = raw_norm.replace(" ", "")
        raw_words = set(raw_norm.split())

        for svc in self.services:
            svc_norm = re.sub(r"[^\w\s]", "", svc.lower()).strip()
            svc_nospace = svc_norm.replace(" ", "")
            svc_words = set(svc_norm.split())

            # 1. Exact normalized match
            if raw_norm == svc_norm:
                return svc
            # 2. No-space match (hair cut ↔ haircut)
            if raw_nospace == svc_nospace:
                return svc
            # 3. One is a substring of the other (no-space)
            if raw_nospace in svc_nospace or svc_nospace in raw_nospace:
                return svc
            # 4. Word-level: all svc words are present in raw words
            #    e.g. "beard trimming" has "beard" which overlaps "beard trims"
            if svc_words and svc_words.issubset(raw_words):
                return svc
            # 5. Majority word overlap: most svc words found in raw
            if len(svc_words) > 1:
                overlap = svc_words & raw_words
                if len(overlap) / len(svc_words) >= 0.6:
                    return svc
            # 6. Singular/plural: try stripping/adding trailing 's'
            for variant in [raw_norm.rstrip("s"), raw_norm + "s"]:
                if variant == svc_norm or variant == svc_nospace:
                    return svc

        return None



# ── Internal cache (invalidated when description changes) ──────────────────────

_cache_lock = threading.Lock()
_cached_profile: Optional[BusinessProfile] = None
_cached_description: Optional[str] = None


# ── Public API ─────────────────────────────────────────────────────────────────

def parse_profile(description: str) -> BusinessProfile:
    """Parse a free-text business description into a BusinessProfile."""
    if not description or not description.strip():
        return BusinessProfile()

    text = description.strip()
    profile = BusinessProfile(raw_description=text)

    profile.name = _extract_name(text) or "Our Business"
    profile.services = _extract_services(text)
    open_t, close_t = _extract_hours(text)
    profile.open_time = open_t
    profile.close_time = close_t
    profile.open_days = _extract_days(text)
    profile.location = _extract_location(text)

    return profile


def get_business_profile(db) -> BusinessProfile:
    """
    Load the business profile from the settings DB, parse it, and cache it.
    The cache is invalidated if the stored description changes.
    """
    global _cached_profile, _cached_description

    from models.setting import Setting  # avoid circular import at module level
    setting = db.get(Setting, "businessProfile")
    description = setting.value if setting else ""

    with _cache_lock:
        if description == _cached_description and _cached_profile is not None:
            return _cached_profile
        profile = parse_profile(description)
        _cached_profile = profile
        _cached_description = description
        return profile


def invalidate_cache() -> None:
    """Call this whenever the businessProfile setting is updated."""
    global _cached_profile, _cached_description
    with _cache_lock:
        _cached_profile = None
        _cached_description = None


# ── Extraction helpers ─────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation."""
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def _fmt_time(t: time) -> str:
    hour = t.hour
    minute = t.minute
    ampm = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    if minute:
        return f"{hour12}:{minute:02d} {ampm}"
    return f"{hour12} {ampm}"


def _extract_name(text: str) -> Optional[str]:
    """Extract business name from the description."""
    for pattern in NAME_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            name = m.group(1).strip().rstrip(".,;:")
            # Reject if it looks like a common word rather than a proper name
            if len(name) > 1 and not name.lower() in {
                "a", "an", "the", "open", "located", "we", "our", "salon",
                "shop", "store", "clinic", "office", "studio",
            }:
                return name
    return None


def _extract_services(text: str) -> list[str]:
    """
    Extract services from the description by looking for noun lists after offer keywords.
    """
    services: list[str] = []

    # Build a pattern: "offer|provide|..." followed by a noun list
    kw_pattern = "|".join(re.escape(k) for k in OFFER_KEYWORDS)
    pattern = rf"(?:{kw_pattern})\s+([^.!?\n]{{1,300}})"

    for m in re.finditer(pattern, text, re.IGNORECASE):
        noun_chunk = m.group(1).strip()
        # Split by commas and "and"
        parts = re.split(r",\s*|\s+and\s+|\s+&\s+", noun_chunk)
        for part in parts:
            part = part.strip().rstrip(".,;:")
            
            # Reject if it contains structural descriptions of the business
            if any(w in part.lower().split() for w in ["called", "named", "located", "open", "our", "my"]):
                continue
                
            # Filter out very short or obviously non-service tokens
            if 2 <= len(part) <= 50 and not _is_stop_phrase(part) and len(part.split()) <= 4:
                # Normalize: remove articles at start
                part = re.sub(r"^(a|an|the|of)\s+", "", part, flags=re.I)
                if part:
                    services.append(part.lower())

    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for s in services:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result


def _is_stop_phrase(text: str) -> bool:
    """Return True if this token is clearly not a service name."""
    stops = {
        "we", "our", "the", "a", "an", "and", "or", "but",
        "open", "monday", "tuesday", "wednesday", "thursday",
        "friday", "saturday", "sunday", "am", "pm",
        "salon", "business", "shop", "store", "clinic",
        "office", "studio", "called", "named"
    }
    return text.lower().strip() in stops or len(text.split()) > 8


def _parse_time_str(raw: str) -> Optional[time]:
    """Parse a time string like '9 AM', '9:30 AM', '09:00', '19:00' into a time object."""
    raw = raw.strip()

    # HH:MM 24-hour
    m = re.match(r"^(\d{1,2}):(\d{2})$", raw)
    if m:
        try:
            return time(int(m.group(1)), int(m.group(2)))
        except ValueError:
            pass

    # 9 AM / 9:30 PM / 9am
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", raw, re.I)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3).lower()
        if ampm == "pm" and hour != 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
        try:
            return time(hour, minute)
        except ValueError:
            pass

    # Word form: "nine AM"
    m = re.match(r"^(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(am|pm)$", raw, re.I)
    if m:
        hour = TIME_WORD_MAP.get(m.group(1).lower(), 0)
        ampm = m.group(2).lower()
        if ampm == "pm" and hour != 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
        try:
            return time(hour, 0)
        except ValueError:
            pass

    return None


def _extract_hours(text: str) -> tuple[Optional[time], Optional[time]]:
    """Extract open and close times from the description."""
    # Pattern: "from 9 AM to 7 PM" or "9:00 to 18:00" or "9am - 5pm"
    patterns = [
        r"from\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+(?:to|till|until|-)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
        r"(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s*(?:to|till|until|-)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm))",
        r"(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(?:am|pm)\s+(?:to|till|until|-)\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(?:am|pm)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            open_t = _parse_time_str(m.group(1).strip())
            close_t = _parse_time_str(m.group(2).strip())
            if open_t and close_t:
                return open_t, close_t
    return None, None


def _extract_days(text: str) -> list[str]:
    """Extract operating days from the description."""
    text_lower = text.lower()

    # "Monday to Saturday" / "Mon–Fri" ranges
    range_m = re.search(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:to|through|till|–|-)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        text_lower,
    )
    if range_m:
        start = range_m.group(1)
        end = range_m.group(2)
        if start in WEEKDAY_ORDER and end in WEEKDAY_ORDER:
            si = WEEKDAY_ORDER.index(start)
            ei = WEEKDAY_ORDER.index(end)
            if si <= ei:
                return WEEKDAY_ORDER[si: ei + 1]

    # "every day" / "daily" / "7 days"
    if re.search(r"\bevery\s+day\b|\bdaily\b|\b7\s+days\b|\bweekdays\s+and\s+weekends\b", text_lower):
        return list(WEEKDAY_ORDER)

    # "weekdays"
    if re.search(r"\bweekdays\b", text_lower):
        return WEEKDAY_ORDER[:5]

    # Individual days listed
    days_found = [d for d in WEEKDAY_ORDER if d in text_lower]
    return days_found


def _extract_location(text: str) -> str:
    """Extract location info from the description."""
    patterns = [
        r"(?:located|based|situated)\s+in\s+([A-Za-z][^.!\n]{1,60}?)(?:\.|!|\n|$)",
        r"(?:in|at)\s+([A-Z][A-Za-z\s,]{2,60}?)(?:\.|!|\n|,\s*(?:we|our|is|are)\b|$)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            loc = m.group(1).strip().rstrip(".,;:")
            if len(loc) > 2:
                return loc
    return ""
