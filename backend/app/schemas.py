from __future__ import annotations

from datetime import date as DateType
from typing import Optional

from pydantic import BaseModel


class CycleIn(BaseModel):
    name: str
    start_date: DateType
    end_date: DateType


class ProjectIn(BaseModel):
    pep_wbs: str
    name: Optional[str] = None
    client: Optional[str] = None
    manager: Optional[str] = None
    budget_hours: Optional[float] = None
    status: str = "ativo"
