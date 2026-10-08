"""MCP protocol adapter consumed by MaxKB."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from smart_service.repository import JsonOrderRepository
from smart_service.service import CustomerService

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = Path(os.getenv("ORDER_DATA_PATH", PROJECT_ROOT / "data" / "orders.json"))

service = CustomerService(JsonOrderRepository(DATA_FILE))
mcp = MCPServer(
    "电商售后工具服务",
    instructions="查询订单前必须同时取得订单号和手机号后四位。工具只读，不会真正执行退款。",
)


@mcp.tool()
def query_order(order_no: str, phone_tail: str) -> dict[str, Any]:
    """查询订单状态、商品和实付金额。仅在用户提供订单号和手机号后四位后调用。"""
    return service.query_order(order_no, phone_tail)


@mcp.tool()
def query_logistics(order_no: str, phone_tail: str) -> dict[str, Any]:
    """查询承运公司、物流单号和最新轨迹。仅用于物流或发货进度问题。"""
    return service.query_logistics(order_no, phone_tail)


@mcp.tool()
def evaluate_refund(order_no: str, phone_tail: str, reason: str) -> dict[str, Any]:
    """根据订单状态、签收时间和退款原因评估退款资格，但不会真正发起退款。"""
    return service.evaluate_refund(order_no, phone_tail, reason)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=os.getenv("MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_PORT", "8000")),
        stateless_http=True,
        json_response=True,
    )
