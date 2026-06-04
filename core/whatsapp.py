"""
Core messaging helpers — SMS and WhatsApp via Twilio.

Environment variables required:
  TWILIO_ACCOUNT_SID   — Twilio account SID
  TWILIO_AUTH_TOKEN    — Twilio auth token
  TWILIO_SMS_FROM      — Twilio phone number for SMS  e.g. +14155238886
  SMS_ENABLED          — set to "1" to enable SMS sending
  TWILIO_WHATSAPP_FROM — Twilio WhatsApp sender      e.g. whatsapp:+14155238886
  WHATSAPP_ENABLED     — set to "1" to enable Twilio WhatsApp sending
  WHATSAPP_COUNTRY_CODE— default country code        e.g. +91
"""
from django.conf import settings


# ---------------------------------------------------------------------------
# Phone normalisation helpers
# ---------------------------------------------------------------------------

def _normalize_e164(raw_phone: str) -> str:
    """Return E.164 format (+91XXXXXXXXXX) or empty string."""
    digits = "".join(ch for ch in (raw_phone or "") if ch.isdigit())
    if not digits:
        return ""
    country = (getattr(settings, "WHATSAPP_COUNTRY_CODE", "+91") or "+91").strip()
    country_digits = "".join(ch for ch in country if ch.isdigit())
    if country_digits == "91" and len(digits) >= 10:
        digits = digits[-10:]
    if digits.startswith(country_digits):
        return f"+{digits}"
    return f"+{country_digits}{digits}"


def _normalize_phone_for_whatsapp(raw_phone: str) -> str:
    """Return whatsapp:+91XXXXXXXXXX or empty string."""
    e164 = _normalize_e164(raw_phone)
    return f"whatsapp:{e164}" if e164 else ""


def wa_me_link(raw_phone: str, message: str) -> str:
    """Build a wa.me link with a pre-filled message (opens WhatsApp)."""
    import urllib.parse
    e164 = _normalize_e164(raw_phone)
    if not e164:
        return ""
    digits_only = e164.lstrip("+")
    return f"https://wa.me/{digits_only}?text={urllib.parse.quote(message)}"


# ---------------------------------------------------------------------------
# SMS via Twilio
# ---------------------------------------------------------------------------

def send_sms(phone: str, body: str) -> tuple[bool, str]:
    """Send a plain SMS via Twilio. Returns (ok, reason)."""
    if not getattr(settings, "SMS_ENABLED", False):
        return False, "SMS disabled — set SMS_ENABLED=1"
    sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    from_ = getattr(settings, "TWILIO_SMS_FROM", "")
    if not (sid and token and from_):
        return False, "Twilio SMS settings missing (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_SMS_FROM)"
    to = _normalize_e164(phone)
    if not to:
        return False, "Customer phone number missing or invalid"
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        client.messages.create(from_=from_, to=to, body=body)
        return True, "sent"
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# WhatsApp via Twilio API (server-side)
# ---------------------------------------------------------------------------

def send_whatsapp_message(phone: str, body: str) -> tuple[bool, str]:
    """Send a WhatsApp message via Twilio API (server-side). Returns (ok, reason)."""
    if not getattr(settings, "WHATSAPP_ENABLED", False):
        return False, "WhatsApp disabled — set WHATSAPP_ENABLED=1"
    sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    from_ = getattr(settings, "TWILIO_WHATSAPP_FROM", "")
    if not (sid and token and from_):
        return False, "Twilio WhatsApp settings missing"
    to = _normalize_phone_for_whatsapp(phone)
    if not to:
        return False, "Customer phone number missing or invalid"
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        client.messages.create(from_=from_, to=to, body=body)
        return True, "sent"
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Legacy helpers (kept for backward compatibility)
# ---------------------------------------------------------------------------

def send_jobcard_created_whatsapp(jobcard) -> tuple[bool, str]:
    body = (
        f"Dear {jobcard.customer.name}, your job card {jobcard.job_number} has been created "
        f"at {settings.SHOP_NAME}. Vehicle: {jobcard.vehicle.registration_number}. Thank you."
    )
    return send_whatsapp_message(jobcard.customer.phone, body)
