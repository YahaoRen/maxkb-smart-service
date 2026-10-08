"""Domain models kept independent from MaxKB and MCP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


def parse_optional_date(value: Any) -> date | None:
    """Parse an ISO date from JSON while allowing null values."""
    if value in (None, ""):
        return None
    return date.fromisoformat(str(value))


@dataclass(frozen=True)
class Order:
    """A minimal order model containing only fields used by the demo."""

    order_no: str
    customer_name: str
    phone: str
    product_name: str
    paid_amount: Decimal
    status: str
    created_at: date
    shipped_at: date | None
    received_at: date | None
    carrier: str
    tracking_no: str
    logistics_detail: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Order:
        return cls(
            order_no=str(raw["order_no"]).upper(),
            customer_name=str(raw["customer_name"]),
            phone=str(raw["phone"]),
            product_name=str(raw["product_name"]),
            paid_amount=Decimal(str(raw["paid_amount"])),
            status=str(raw["status"]),
            created_at=date.fromisoformat(str(raw["created_at"])),
            shipped_at=parse_optional_date(raw.get("shipped_at")),
            received_at=parse_optional_date(raw.get("received_at")),
            carrier=str(raw.get("carrier", "")),
            tracking_no=str(raw.get("tracking_no", "")),
            logistics_detail=str(raw.get("logistics_detail", "")),
        )
