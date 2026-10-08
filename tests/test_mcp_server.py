"""Thin integration tests for the MCP adapter."""

import unittest

from smart_service.mcp_server import mcp


class MCPServerTest(unittest.IsolatedAsyncioTestCase):
    async def test_expected_tools_are_registered(self) -> None:
        tools = await mcp.list_tools()

        self.assertEqual(
            {"query_order", "query_logistics", "evaluate_refund"},
            {tool.name for tool in tools},
        )

    async def test_tool_call_returns_structured_content(self) -> None:
        result = await mcp.call_tool(
            "query_order",
            {"order_no": "DD202610080001", "phone_tail": "5678"},
        )

        self.assertIsNotNone(result.structured_content)
        self.assertEqual("ORDER_FOUND", result.structured_content["code"])


if __name__ == "__main__":
    unittest.main()
