"""Deterministic customer-service rules exposed later as MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Any

from smart_service.models import Order
from smart_service.repository import JsonOrderRepository

ToolResult = dict[str, Any]

QUALITY_KEYWORDS = ("质量", "破损", "损坏", "错发", "漏发", "故障")
UNSHIPPED_STATUSES = ("已付款", "待发货")


class CustomerService:
    """Query orders and evaluate refund rules without involving an LLM."""

    def __init__(
        self,
        repository: JsonOrderRepository,
        today_provider: Callable[[], date] = date.today,
    ) -> None:
        self._repository = repository
        self._today_provider = today_provider

    def query_order(self, order_no: str, phone_tail: str) -> ToolResult:
        order, error = self._verified_order(order_no, phone_tail)
        if error:
            return error
        assert order is not None

        return self._success(
            code="ORDER_FOUND",
            message=f"订单 {order.order_no} 当前状态为“{order.status}”。",
            data={
                "order_no": order.order_no,
                "customer_name": self._mask_name(order.customer_name),
                "phone": self._mask_phone(order.phone),
                "product_name": order.product_name,
                "paid_amount": self._money(order.paid_amount),
                "status": order.status,
                "created_at": order.created_at.isoformat(),
            },
        )

    def query_logistics(self, order_no: str, phone_tail: str) -> ToolResult:
        order, error = self._verified_order(order_no, phone_tail)
        if error:
            return error
        assert order is not None

        if not order.tracking_no:
            return self._success(
                code="NOT_SHIPPED",
                message=f"订单 {order.order_no} 尚未发货，暂时没有物流单号。",
                data={
                    "order_no": order.order_no,
                    "status": order.status,
                    "carrier": "",
                    "tracking_no": "",
                    "latest_detail": "等待商家发货",
                },
            )

        return self._success(
            code="LOGISTICS_FOUND",
            message=f"已查询到订单 {order.order_no} 的最新物流信息。",
            data={
                "order_no": order.order_no,
                "status": order.status,
                "carrier": order.carrier,
                "tracking_no": order.tracking_no,
                "latest_detail": order.logistics_detail,
            },
        )

    def evaluate_refund(self, order_no: str, phone_tail: str, reason: str) -> ToolResult:
        order, error = self._verified_order(order_no, phone_tail)
        if error:
            return error
        assert order is not None

        reason = reason.strip()
        if not reason:
            return self._failure("INVALID_ARGUMENT", "请说明退款原因。")

        is_quality_issue = any(keyword in reason for keyword in QUALITY_KEYWORDS)
        common_data: dict[str, Any] = {
            "order_no": order.order_no,
            "status": order.status,
            "reason": reason,
            "estimated_refund": self._money(order.paid_amount),
        }

        if order.status == "待付款":
            return self._refund_result(
                common_data,
                decision="无需退款",
                eligible=False,
                explanation="订单尚未付款，可直接取消订单。",
                shipping_responsibility="无",
            )

        if order.status in UNSHIPPED_STATUSES:
            return self._refund_result(
                common_data,
                decision="可申请退款",
                eligible=True,
                explanation="订单尚未发货，预计按实付金额原路退回。",
                shipping_responsibility="无",
            )

        if order.status == "已发货" and order.received_at is None:
            shipping_responsibility = "商家承担" if is_quality_issue else "以平台退货规则为准"
            return self._refund_result(
                common_data,
                decision="可申请退货退款",
                eligible=True,
                explanation="商品已发货，需拒收或收到商品后按平台指引退回。",
                shipping_responsibility=shipping_responsibility,
            )

        if order.status == "已签收" and order.received_at is not None:
            days = (self._today_provider() - order.received_at).days
            common_data["days_since_received"] = max(days, 0)
            if days <= 7:
                shipping_responsibility = "商家承担" if is_quality_issue else "买家承担"
                return self._refund_result(
                    common_data,
                    decision="可申请七天无理由退货",
                    eligible=True,
                    explanation="当前仍在签收后七天期限内，商品需保持完好。",
                    shipping_responsibility=shipping_responsibility,
                )
            if is_quality_issue:
                return self._refund_result(
                    common_data,
                    decision="需要人工审核",
                    eligible=False,
                    explanation="已超过七天，但质量问题可上传凭证申请售后审核。",
                    shipping_responsibility="审核通过后由商家承担",
                )
            return self._refund_result(
                common_data,
                decision="不符合七天无理由条件",
                eligible=False,
                explanation="订单已超过签收后七天，且未描述质量问题。",
                shipping_responsibility="无",
            )

        return self._refund_result(
            common_data,
            decision="需要人工审核",
            eligible=False,
            explanation="当前订单状态无法自动判断，请转人工客服。",
            shipping_responsibility="待审核",
        )

    def _verified_order(
        self, order_no: str, phone_tail: str
    ) -> tuple[Order | None, ToolResult | None]:
        if len(phone_tail) != 4 or not phone_tail.isdigit():
            return None, self._failure("INVALID_ARGUMENT", "手机号后四位必须是 4 位数字。")

        order = self._repository.get(order_no)
        if order is None or not order.phone.endswith(phone_tail):
            return None, self._failure(
                "VERIFY_FAILED",
                "订单不存在或手机号后四位不匹配，请核对后重试。",
            )
        return order, None

    @staticmethod
    def _refund_result(
        common_data: dict[str, Any],
        *,
        decision: str,
        eligible: bool,
        explanation: str,
        shipping_responsibility: str,
    ) -> ToolResult:
        data = {
            **common_data,
            "decision": decision,
            "eligible": eligible,
            "explanation": explanation,
            "shipping_responsibility": shipping_responsibility,
        }
        return CustomerService._success(
            code="REFUND_EVALUATED",
            message=f"退款资格评估结果：{decision}。{explanation}",
            data=data,
        )

    @staticmethod
    def _success(code: str, message: str, data: dict[str, Any]) -> ToolResult:
        return {"ok": True, "code": code, "message": message, "data": data}

    @staticmethod
    def _failure(code: str, message: str) -> ToolResult:
        return {"ok": False, "code": code, "message": message, "data": {}}

    @staticmethod
    def _money(value: Decimal) -> str:
        return f"{value.quantize(Decimal('0.01'))}"

    @staticmethod
    def _mask_name(name: str) -> str:
        if len(name) <= 1:
            return "*"
        return f"{name[0]}{'*' * (len(name) - 1)}"

    @staticmethod
    def _mask_phone(phone: str) -> str:
        return f"{phone[:3]}****{phone[-4:]}"
