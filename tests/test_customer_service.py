"""Tests for the business rules that must not be left to the LLM."""

import unittest
from datetime import date
from pathlib import Path

from smart_service.repository import JsonOrderRepository
from smart_service.service import CustomerService

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CustomerServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        repository = JsonOrderRepository(PROJECT_ROOT / "data" / "orders.json")
        self.service = CustomerService(repository, today_provider=lambda: date(2026, 10, 8))

    def test_query_order_masks_personal_information(self) -> None:
        result = self.service.query_order("DD202610080001", "5678")

        self.assertTrue(result["ok"])
        self.assertEqual("ORDER_FOUND", result["code"])
        self.assertEqual("张**", result["data"]["customer_name"])
        self.assertEqual("138****5678", result["data"]["phone"])

    def test_wrong_phone_tail_does_not_reveal_whether_order_exists(self) -> None:
        result = self.service.query_order("DD202610080001", "0000")

        self.assertFalse(result["ok"])
        self.assertEqual("VERIFY_FAILED", result["code"])
        self.assertIn("不存在或手机号后四位不匹配", result["message"])

    def test_logistics_query_returns_latest_tracking_detail(self) -> None:
        result = self.service.query_logistics("DD202610080001", "5678")

        self.assertTrue(result["ok"])
        self.assertEqual("顺丰速运", result["data"]["carrier"])
        self.assertIn("太原转运中心", result["data"]["latest_detail"])

    def test_unshipped_order_has_no_tracking_number(self) -> None:
        result = self.service.query_logistics("DD202610080004", "8866")

        self.assertTrue(result["ok"])
        self.assertEqual("NOT_SHIPPED", result["code"])
        self.assertEqual("", result["data"]["tracking_no"])

    def test_order_within_seven_days_is_eligible_for_return(self) -> None:
        result = self.service.evaluate_refund(
            "DD202610010002", "2468", "买错了，想七天无理由退货"
        )

        self.assertTrue(result["data"]["eligible"])
        self.assertEqual("可申请七天无理由退货", result["data"]["decision"])
        self.assertEqual(3, result["data"]["days_since_received"])
        self.assertEqual("买家承担", result["data"]["shipping_responsibility"])

    def test_order_over_seven_days_is_not_eligible_without_quality_issue(self) -> None:
        result = self.service.evaluate_refund("DD202609100003", "1357", "不喜欢了")

        self.assertFalse(result["data"]["eligible"])
        self.assertEqual("不符合七天无理由条件", result["data"]["decision"])

    def test_quality_issue_after_seven_days_goes_to_manual_review(self) -> None:
        result = self.service.evaluate_refund("DD202609100003", "1357", "手环屏幕损坏")

        self.assertFalse(result["data"]["eligible"])
        self.assertEqual("需要人工审核", result["data"]["decision"])
        self.assertIn("质量问题", result["data"]["explanation"])

    def test_unshipped_order_can_receive_full_refund(self) -> None:
        result = self.service.evaluate_refund("DD202610080004", "8866", "不需要了")

        self.assertTrue(result["data"]["eligible"])
        self.assertEqual("329.00", result["data"]["estimated_refund"])
        self.assertEqual("无", result["data"]["shipping_responsibility"])


if __name__ == "__main__":
    unittest.main()
