from __future__ import annotations

from typing import Dict, Any, Optional, List

import logging
import re

try:
    import spacy
    from spacy.matcher import PhraseMatcher, Matcher

    _HAS_SPACY = True
except Exception:  # pragma: no cover
    spacy = None
    PhraseMatcher = None
    Matcher = None
    _HAS_SPACY = False

logger = logging.getLogger(__name__)

_nlp = None
_phrase_matcher = None
_matcher = None


def init_nlu() -> None:
    """Initialize spaCy matchers if spaCy is available. Otherwise rely on fallback rules."""
    global _nlp, _phrase_matcher, _matcher
    if _nlp is not None:
        return

    if not _HAS_SPACY:
        logger.warning("spaCy not available; using lightweight NLU fallback")
        _nlp = None
        return
    try:
        _nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy loaded: en_core_web_sm")
        try:
            print("spaCy loaded: en_core_web_sm")
        except Exception:
            pass
    except Exception as exc:
        logger.warning("spaCy model load failed: %s. Falling back to lightweight NLU.", exc)
        _nlp = None
        return

    _build_intent_matcher()


def _build_intent_matcher() -> None:
    """Build the PhraseMatcher for intent detection. Called once on startup."""
    global _phrase_matcher
    if _nlp is None:
        return

    _phrase_matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")

    book_phrases = [
        "book", "book an appointment", "make an appointment", "schedule",
        "i would like to book", "i'd like to book", "i want to book",
        "i wanna book", "reserve", "set up an appointment", "schedule a visit",
        "i need an appointment", "can i book", "can i schedule",
    ]
    cancel_phrases = [
        "cancel", "cancel appointment", "cancel my appointment",
        "i need to cancel", "call off", "drop", "no longer need",
    ]
    reschedule_phrases = [
        "reschedule", "resched", "re-schedule", "re-sched", "move",
        "change my appointment", "another time", "postpone", "push back",
        "switch", "move from", "change time",
    ]
    enquire_phrases = [
        "what time", "do you have", "available", "how much", "is there",
        "i have a question", "do you have any availability", "when is",
        "are there any slots", "what services", "what do you offer",
        "do you do", "can you do",
    ]
    end_call_phrases = [
        "no", "nope", "that's all", "nothing else", "goodbye", "bye", 
        "no thank you", "no thanks", "i'm good", "im good", "all set"
    ]

    _phrase_matcher.add("BOOK", [_nlp.make_doc(t) for t in book_phrases])
    _phrase_matcher.add("CANCEL", [_nlp.make_doc(t) for t in cancel_phrases])
    _phrase_matcher.add("RESCHEDULE", [_nlp.make_doc(t) for t in reschedule_phrases])
    _phrase_matcher.add("ENQUIRE", [_nlp.make_doc(t) for t in enquire_phrases])
    _phrase_matcher.add("END_CALL", [_nlp.make_doc(t) for t in end_call_phrases])


def _build_service_matcher(services: List[str]):
    """
    Build a spaCy Matcher for the given list of service strings.
    Each service can be multi-word (e.g. 'beard trim').
    Returns a Matcher instance (or None if spaCy not available).
    """
    if _nlp is None or not services:
        return None

    svc_phrase_matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
    docs = []
    for svc in services:
        # Also add common singular/plural and normalized forms
        normalized_forms = _service_variants(svc)
        for form in normalized_forms:
            try:
                docs.append((svc, _nlp.make_doc(form)))
            except Exception:
                pass

    for svc, doc in docs:
        label = f"SVC_{svc.upper().replace(' ', '_')}"
        svc_phrase_matcher.add(label, [doc])

    return svc_phrase_matcher


def _service_variants(service: str) -> List[str]:
    """Return a list of text variants for a service name (singular, plural, normalized)."""
    s = service.strip().lower()
    variants = {s}
    # Remove trailing 's' for plural/singular coverage
    if s.endswith("s") and len(s) > 3:
        variants.add(s[:-1])
    else:
        variants.add(s + "s")
    # Remove spaces (e.g. "haircut" vs "hair cut")
    no_space = s.replace(" ", "")
    variants.add(no_space)
    # Add with spaces inserted at common split points
    return list(variants)


# ── Entity extraction helpers ──────────────────────────────────────────────────

def _extract_datetime_entities(doc) -> Dict[str, str | None]:
    dates = []
    times = []
    for ent in doc.ents:
        if ent.label_ == "DATE":
            dates.append(ent.text)
        if ent.label_ == "TIME":
            times.append(ent.text)

    if not times:
        for m in re.finditer(r"\b(\d{1,2}(:\d{2})?\s?(am|pm)?)\b", doc.text, flags=re.I):
            times.append(m.group(1))
        for m in re.finditer(
            r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(am|pm)\b",
            doc.text, flags=re.I,
        ):
            times.append("".join(m.groups()))

    if not dates:
        ordinal = r"(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|twenty-first|twenty-second|twenty-third|twenty-fourth|twenty-fifth|twenty-sixth|twenty-seventh|twenty-eighth|twenty-ninth|thirtieth|thirty-first)"
        for m in re.finditer(
            r"\b(on\s+(?:the\s+)?(?:\w+\s+(?:\d{1,2}(?:st|nd|rd|th)?|" + ordinal + r")|(?:\d{1,2}(?:st|nd|rd|th)?|" + ordinal + r")\s+of\s+\w+|\w+\s+(?:\d{1,2}(?:st|nd|rd|th)?|" + ordinal + r"))|tomorrow|today|next\s+\w+)\b",
            doc.text, flags=re.I,
        ):
            dates.append(m.group(1))

    time_range = re.search(
        r"\bfrom\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+to\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        doc.text, flags=re.I,
    )
    if time_range:
        times = [time_range.group(1), time_range.group(2)]

    date_match = re.search(
        r"\b(on\s+(?:the\s+)?(?:\w+\s+\d{1,2}(?:st|nd|rd|th)?|\d{1,2}(?:st|nd|rd|th)?\s+of\s+\w+)|tomorrow|today|next\s+\w+)\b",
        doc.text, flags=re.I,
    )
    if date_match and not dates:
        dates.append(date_match.group(1))

    date_val = dates[0] if dates else None
    if not times:
        time_val = None
    elif len(times) == 1:
        time_val = times[0]
    else:
        time_val = times

    return {"date": date_val, "time": time_val}


def _extract_person_name(doc, transcript: str) -> str | None:
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text

    match = re.search(
        r"\b(?:dr|doctor|mr|mrs|ms|miss|prof)\.??\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        transcript, flags=re.I,
    )
    if match:
        return match.group(0).title()

    match = re.search(r"\bmy name is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", transcript, flags=re.I)
    if match:
        return match.group(1).title()

    match = re.search(r"\bI(?:'m| am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", transcript, flags=re.I)
    if match:
        return match.group(1).title()

    match = re.search(r"\bwith\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", transcript)
    if match:
        return match.group(1)

    return None


def _extract_service_fallback(transcript: str, services: List[str]) -> Optional[str]:
    """
    Fallback service extraction: normalize transcript and match against known services.
    Handles minor variations (haircut vs hair cut, etc.)
    """
    text_norm = re.sub(r"[^\w\s]", "", transcript.lower())
    for svc in services:
        svc_norm = re.sub(r"[^\w\s]", "", svc.lower())
        # Direct substring match
        if svc_norm in text_norm:
            return svc
        # Match without spaces
        svc_nospace = svc_norm.replace(" ", "")
        text_nospace = text_norm.replace(" ", "")
        if svc_nospace in text_nospace:
            return svc
        # Word-by-word: if all words of svc appear in transcript words
        svc_words = set(svc_norm.split())
        text_words = set(text_norm.split())
        if svc_words and svc_words.issubset(text_words):
            return svc
    return None


# ── Public API ─────────────────────────────────────────────────────────────────

def extract(transcript: str, business_profile=None) -> Dict[str, Any]:
    """
    Extract intent and entities from a transcript.

    Args:
        transcript: The spoken text to process.
        business_profile: Optional BusinessProfile instance. When provided,
            service matching is done against the profile's configured services
            instead of a hardcoded list.

    Returns:
        dict: {"intent": str, "entities": {"date", "time", "service", "name"}}
    """
    global _nlp, _phrase_matcher
    if _nlp is None:
        init_nlu()

    # Determine which services to use
    known_services: List[str] = []
    if business_profile is not None and business_profile.services:
        known_services = business_profile.services
    else:
        # Generic fallback list when no profile configured
        known_services = [
            "haircut", "beard trim", "shave", "fade", "hair color",
            "dentist", "cleaning", "consultation", "checkup", "therapy",
        ]

    if _nlp is None:
        return _extract_fallback(transcript, known_services)

    doc = _nlp(transcript)

    # ── Intent ────────────────────────────────────────────────────────────────
    intent = "unknown"
    if _phrase_matcher:
        matches = _phrase_matcher(doc)
        intents_found = set()
        for match_id, start, end in matches:
            label = _nlp.vocab.strings[match_id]
            intents_found.add(label)

        if "END_CALL" in intents_found:
            intent = "end_call"
        elif "CANCEL" in intents_found:
            intent = "cancel"
        elif "RESCHEDULE" in intents_found:
            intent = "reschedule"
        elif "BOOK" in intents_found:
            intent = "book"
        elif "ENQUIRE" in intents_found:
            intent = "enquire"

    # ── Datetime entities ─────────────────────────────────────────────────────
    dt = _extract_datetime_entities(doc)

    # ── Service detection ─────────────────────────────────────────────────────
    service = None

    # Try spaCy PhraseMatcher first (multi-word aware)
    svc_matcher = _build_service_matcher(known_services)
    if svc_matcher:
        svc_matches = svc_matcher(doc)
        for match_id, start, end in svc_matches:
            label = _nlp.vocab.strings[match_id]
            if label.startswith("SVC_"):
                # Recover canonical name from label
                canonical_label = label[4:].replace("_", " ").lower()
                # Find the best matching service name
                for svc in known_services:
                    if svc.upper().replace(" ", "_") == label[4:]:
                        service = svc
                        break
                if service is None:
                    service = canonical_label
                break

    # Fallback: normalized text matching
    if service is None:
        service = _extract_service_fallback(transcript, known_services)

    # ── Name detection ────────────────────────────────────────────────────────
    name = _extract_person_name(doc, transcript)

    return {
        "intent": intent,
        "entities": {
            "date": dt.get("date"),
            "time": dt.get("time"),
            "service": service,
            "name": name,
        },
    }


def _extract_fallback(transcript: str, known_services: List[str]) -> Dict[str, Any]:
    """Lightweight rule-based NLU when spaCy is not available."""
    text = transcript.lower()
    intent = "unknown"
    if any(k in text for k in ["no", "nope", "that's all", "nothing else", "goodbye", "bye", 
                                 "no thank you", "no thanks", "i'm good", "im good", "all set"]):
        intent = "end_call"
    elif any(k in text for k in ["cancel", "cancel my appointment", "i need to cancel"]):
        intent = "cancel"
    elif any(k in text for k in ["resched", "reschedule", "move", "change my appointment"]):
        intent = "reschedule"
    elif any(k in text for k in ["book", "schedule", "make an appointment", "i'd like to book",
                                "i would like to book", "i wanna book", "i need an appointment"]):
        intent = "book"
    elif any(k in text for k in ["what time", "available", "how much", "i have a question",
                                  "what services", "what do you offer"]):
        intent = "enquire"

    date = None
    time = None
    m = re.search(r"\b(\d{1,2}(:\d{2})?\s?(am|pm)?)\b", text, flags=re.I)
    if m:
        time = m.group(1)
    md = re.search(r"\b(next\s+\w+|on\s+\w+\s+\d{1,2}(st|nd|rd|th)?|tomorrow|today)\b", text, flags=re.I)
    if md:
        date = md.group(1)

    service = _extract_service_fallback(transcript, known_services)

    name = None
    mname = re.search(
        r"\b(?:dr|doctor|mr|mrs|ms|miss|prof)\.??\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b",
        transcript, flags=re.I,
    )
    if mname:
        name = mname.group(0).title()
    else:
        mname = re.search(r"\bmy name is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", transcript, flags=re.I)
        if mname:
            name = mname.group(1).title()
        else:
            mname = re.search(r"\bwith\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", transcript)
            if mname:
                name = mname.group(1)

    return {"intent": intent, "entities": {"date": date, "time": time, "service": service, "name": name}}
