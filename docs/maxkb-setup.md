# MaxKB 配置步骤

本页只保留完成课程演示所需的配置。目标是让 MaxKB 负责对话和 RAG，让本仓库的 MCP 服务负责确定性业务规则。

## 1. 启动服务

安装 Docker Desktop 后，在项目根目录执行：

```powershell
docker compose up -d --build
```

启动完成后：

- MaxKB：`http://localhost:8080`
- MCP 工具地址：`http://localhost:8000/mcp`

MaxKB 官方镜像的初始管理员账号通常为 `admin / MaxKB@123..`。首次登录后立即修改密码，不要把新密码提交到仓库。

## 2. 配置大模型

在 MaxKB 的模型设置中添加一个支持工具调用的聊天模型。课程演示可选择 DeepSeek、通义千问或 OpenAI 兼容模型。

只配置一个聊天模型和一个嵌入模型即可，不要同时堆很多模型。API Key 只保存在 MaxKB 或本地 `.env` 中。

## 3. 创建知识库

1. 新建知识库，名称填写“星云商城售后知识库”。
2. 上传 `knowledge_base/` 中的三个 Markdown 文件。
3. 使用通用分段方式，建议单段约 300 至 500 个中文字符。
4. 完成向量化后，分别搜索“七天无理由”“退款多久到账”“为什么要手机号后四位”，确认能命中对应段落。

## 4. 创建应用

1. 新建“高级编排”应用，名称填写“星云商城售后助手”。
2. 保留开始、AI 对话和回复这条主链路。
3. 在 AI 对话节点中选择刚创建的聊天模型。
4. 关联“星云商城售后知识库”。
5. 将 `config/system-prompt.md` 的内容复制到系统提示词。

## 5. 接入 MCP 工具

在 AI 对话节点的工具设置中启用 MCP，并粘贴 `config/mcp-server.json`：

```json
{
  "smart-after-sales": {
    "url": "http://smart-tools:8000/mcp",
    "transport": "streamable_http"
  }
}
```

这里必须使用 Docker Compose 服务名 `smart-tools`，不能在 MaxKB 容器内部填写 `localhost:8000`，因为容器中的 `localhost` 只代表 MaxKB 自己。

保存后应能看到三个工具：

- `query_order`
- `query_logistics`
- `evaluate_refund`

## 6. 最小验收

依次测试以下问题：

1. `七天无理由退货由谁承担运费？`
   - 预期：只检索知识库，不索要订单号。
2. `帮我查一下 DD202610080001 的物流。`
   - 预期：先追问手机号后四位。
3. 回复 `5678`。
   - 预期：调用 `query_logistics` 并返回顺丰及最新轨迹。
4. `DD202609100003，后四位 1357，手环屏幕损坏了，能退吗？`
   - 预期：调用 `evaluate_refund`，结果为需要人工审核。
5. `DD202610080001，后四位 0000，查订单。`
   - 预期：不泄露订单详情，提示校验失败。

## 7. 常见错误

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| MaxKB 找不到 MCP 工具 | 工具容器未启动或地址写成 localhost | 检查 `docker compose ps`，使用 `http://smart-tools:8000/mcp` |
| 政策问题也要求订单号 | 系统提示词的路由规则未生效 | 重新粘贴提示词，确认知识库已关联 |
| 订单结果乱码 | 终端编码问题 | Web 页面一般不受影响；Windows 终端切换 UTF-8 |
| 大模型不调用工具 | 模型不支持工具调用或工具描述未加载 | 更换支持工具调用的模型并重新保存 AI 节点 |
