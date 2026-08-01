from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ReportOrder:
    id: str
    date: date
    city: str
    contractor: str
    master: str
    status: str
    amount: Decimal
    complaint: bool
    photo: bool
    service_type: str
    source: str
    comment: str | None
    row_number: int


@dataclass(frozen=True)
class ValidationError:
    row_number: int
    order_id: str | None
    field: str
    message: str
    value: Any
