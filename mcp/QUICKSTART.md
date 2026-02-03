# 快速开始指南

## 5 分钟快速启动

### 1. 安装依赖

```bash
cd mcp
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置 API 密钥

```bash
# 当前版本的 dip-studio mcp 服务器只负责读取本地需求文档并返回原始文本内容，
# 不在服务器端调用任何 LLM，也不替你构建提示词或生成代码。
#
# 因此本版本不需要配置 OPENAI_API_KEY / ANTHROPIC_API_KEY 等 LLM API 密钥。
# 提示词构建和 LLM 调用请在你自己的 Cursor / Claude Code 里完成。
```

### 3. 准备需求文档

将需求文档放入 `requirements/` 目录（已包含一个示例文档）。

### 4. 启动服务器

```bash
python -m src.server
```

服务器将在 `http://localhost:8001` 启动，MCP 端点为 `http://localhost:8001/mcp`。

**注意**: 如果端口 8001 被占用，可以在 `config.yaml` 中修改 `server.port` 配置。

### 5. 配置客户端

#### Cursor

在项目根目录创建 `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "dip-studio": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

**重要**: 确保服务器已启动后再配置客户端。

#### Claude Code

在项目根目录创建 `.mcp.json`:

```json
{
  "mcpServers": {
    "dip-studio": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

或者使用命令行添加：

```bash
claude mcp add --transport http dip-studio http://localhost:8001/mcp
```

### 6. 使用

在 Cursor 或 Claude Code 中，你可以：

- 使用 `list_requirements` 工具查看所有需求文档
- 使用 `read_requirement` 工具读取特定文档
- 使用 `generate_code` 工具基于需求生成代码
- 使用 `apply_buildkit_transformation` 工具应用 buildkit 转换

## 示例用法

在 AI 助手中输入：

```
请使用 list_requirements 工具列出所有需求文档
```

或

```
请读取 example 需求文档，然后生成一个用户列表组件
```

## 故障排除

如果遇到问题，请查看 [README.md](README.md) 中的故障排除部分。
