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


# ── CSV formula injection (WO-001 T4) ────────────────────────────────────────
# Excel and LibreOffice run a cell as a formula when it starts with one of these
# characters. An export writes a single quote before such a text cell. An import
# removes that quote, so export followed by import keeps the original text.
_CSV_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def csv_safe(value):
    """Prefix a text cell that starts with a formula trigger. Numbers, None and bool stay as they are."""
    if isinstance(value, str) and value.startswith(_CSV_TRIGGERS):
        return "'" + value
    return value


def csv_unsafe(value):
    """Undo csv_safe: drop the leading quote only when a trigger character follows it."""
    if isinstance(value, str) and len(value) > 1 and value[0] == "'" and value[1] in _CSV_TRIGGERS:
        return value[1:]
    return value


def safe_row(values):
    """csv_safe for every cell of a data row."""
    return [csv_safe(v) for v in values]
