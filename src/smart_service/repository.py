"""Order data access for the reproducible course demo."""

from __future__ import annotations

import json
from pathlib import Path

from smart_service.models import Order


class JsonOrderRepository:
    """Load fictional orders from a JSON file and index them by order number."""

    def __init__(self, data_file: Path) -> None:
        self._data_file = data_file
        self._orders = self._load_orders()

    def _load_orders(self) -> dict[str, Order]:
        with self._data_file.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        orders: dict[str, Order] = {}
        for raw in payload["orders"]:
            order = Order.from_dict(raw)
            if order.order_no in orders:
                raise ValueError(f"重复订单号: {order.order_no}")
            orders[order.order_no] = order
        return orders

    def get(self, order_no: str) -> Order | None:
        return self._orders.get(order_no.strip().upper())
