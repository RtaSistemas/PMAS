import os
from datetime import datetime
from zoneinfo import ZoneInfo

_BR_TZ = ZoneInfo("America/Sao_Paulo")


def now_br() -> datetime:
    return datetime.now(_BR_TZ)


def _str_or_none(value) -> str | None:
    """Return stripped string or None for blank / NaN / None values."""
    if value is None:
        return None
    s = str(value).strip()
    return None if s.lower() in {"nan", "none", ""} else s


def is_production() -> bool:
    """True only when PMAS_ENV is exactly 'production' (case and spaces ignored).
    Any other value, or none, is development. run.py uses the same rule."""
    return os.getenv("PMAS_ENV", "development").strip().lower() == "production"
