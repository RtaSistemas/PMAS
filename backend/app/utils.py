from datetime import datetime
from zoneinfo import ZoneInfo

_BR_TZ = ZoneInfo("America/Sao_Paulo")


def now_br() -> datetime:
    return datetime.now(_BR_TZ)
