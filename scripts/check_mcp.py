"""Connect to the running MCP service and perform a real protocol call."""

import asyncio
import os

from mcp.client import Client


async def main() -> None:
    url = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")
    async with Client(url) as client:
        tools = await client.list_tools()
        print("已发现工具:", ", ".join(tool.name for tool in tools.tools))

        result = await client.call_tool(
            "query_order",
            {"order_no": "DD202610080001", "phone_tail": "5678"},
        )
        if result.is_error:
            raise RuntimeError(f"MCP 工具调用失败: {result.content}")
        print("订单查询结果:", result.structured_content)


if __name__ == "__main__":
    asyncio.run(main())
