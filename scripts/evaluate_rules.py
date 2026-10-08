"""Run deterministic evaluation cases against the after-sales service."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from smart_service.repository import JsonOrderRepository
from smart_service.service import CustomerService

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")


def read_path(payload: dict[str, Any], dotted_path: str) -> Any:
    value: Any = payload
    for part in dotted_path.split("."):
        value = value[part]
    return value


def evaluate_case(service: CustomerService, case: dict[str, Any]) -> list[str]:
    tool = getattr(service, case["tool"])
    result = tool(**case["arguments"])
    errors: list[str] = []

    for path, expected in case["expected"].items():
        try:
            actual = read_path(result, path)
        except (KeyError, TypeError):
            errors.append(f"{path}: 字段不存在")
            continue
        if actual != expected:
            errors.append(f"{path}: 期望 {expected!r}，实际 {actual!r}")
    return errors


def main() -> int:
    cases_file = PROJECT_ROOT / "evaluation" / "tool-cases.json"
    with cases_file.open("r", encoding="utf-8") as file:
        suite = json.load(file)

    as_of = date.fromisoformat(suite["as_of"])
    repository = JsonOrderRepository(PROJECT_ROOT / "data" / "orders.json")
    service = CustomerService(repository, today_provider=lambda: as_of)

    passed = 0
    for case in suite["cases"]:
        errors = evaluate_case(service, case)
        if errors:
            print(f"[FAIL] {case['name']}")
            for error in errors:
                print(f"       - {error}")
        else:
            passed += 1
            print(f"[PASS] {case['name']}")

    total = len(suite["cases"])
    print(f"\n规则评测结果: {passed}/{total} 通过，准确率 {passed / total:.1%}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
