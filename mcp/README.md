# DIP Studio MCP Server

DIP Studio MCP Server 是基于 Model Context Protocol (MCP) 的远程服务，为 Cursor、Claude Code 等客户端提供 **DIP Studio 项目上下文** 与 **OpenAPI 接口规范** 能力，支持 DIP 应用开发与代码生成。

## 功能特性

- **get_context**: 根据 DIP Studio 节点 ID 从后端获取该节点的完整设计文档与上下文，返回结构化 `context`、`content_to_develop` 及模版化文档 `template_content`，供 Coding Agent 优先使用
- **OpenAPI 工具**: 从 `api-specs` 目录加载 OpenAPI 规范，提供 `list_all_api_endpoints`、`get_api_code_example` 等工具，便于生成接口调用代码
- **远程访问**: 支持 HTTP（含 Streamable HTTP）传输，可与 Cursor、Claude Code 等 MCP 客户端集成

## 安装

### 前置要求

- Python 3.10 或更高版本
- pip 包管理器

### 安装步骤

1. 进入项目目录：

```bash
cd mcp
```

2. 创建虚拟环境（推荐）：

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 安装 MCP SDK（若尚未安装）：

```bash
pip install mcp
```

## 配置

### 1. 配置文件

编辑 `config.yaml`：

```yaml
server:
  host: "0.0.0.0"
  port: 8001
  transport: "streamable-http"   # 或 "http" 兼容旧版 SSE

studio:
  base_url: "http://localhost:8000"   # get_context 调用的 Studio 内部接口地址

api_specs:
  base_path: "./api-specs"   # OpenAPI 规范文档目录
```

### 2. 环境变量

- **STUDIO_BASE_URL**（可选）: 覆盖 `config.yaml` 中的 `studio.base_url`，用于 get_context 请求 Studio 的地址（如 K8s 内：`http://dip-studio:8000`）

### 3. API 规范目录

将 OpenAPI 规范文件（JSON 或 YAML）放入 `api-specs` 目录，服务会自动扫描并加载：

```bash
mkdir -p api-specs
# 将 OpenAPI 3.x 规范放入此目录
```

## 快速开始

### 1. 启动服务

详见 [MCP_SERVER_START.md](./MCP_SERVER_START.md)。

快速启动：

```bash
cd mcp
python -m src.server
```

默认监听 `http://0.0.0.0:8001`，MCP 端点为 `http://localhost:8001/dip-studio/mcp`。

### 2. 配置客户端

详见 [MCP_CLIENT_CONFIG.md](./MCP_CLIENT_CONFIG.md)。

Cursor 快速配置：在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "dip-studio": {
      "url": "http://localhost:8001/dip-studio/mcp"
    }
  }
}
```

## 文档导航

- **[MCP_SERVER_START.md](./MCP_SERVER_START.md)** - 服务启动说明
- **[MCP_CLIENT_CONFIG.md](./MCP_CLIENT_CONFIG.md)** - 客户端配置
- **[DOCKER.md](./DOCKER.md)** - Docker 部署
- **[CURSOR_SETUP.md](./CURSOR_SETUP.md)** - Cursor 配置
- **[QUICKSTART.md](./QUICKSTART.md)** - 快速开始
- **[PROMPT_EXAMPLE.md](./PROMPT_EXAMPLE.md)** - Coding Agent 提示词示例

## MCP Tools

### 1. `get_context`

根据 DIP Studio 节点 ID 获取该节点的完整设计文档与上下文，供 Coding Agent 在回答前**必须先调用一次**。

- **参数**: `node_id` (string, 必需) — 当前 DIP Studio 节点的 UUID，例如 `932dba6a-0640-42fe-b108-00ec94110ff0`
- **返回** (JSON 字符串):
  - `context`: 祖先节点及其文档与可读文本（背景）
  - `content_to_develop`: 当前节点及后代节点及各自文档与可读文本（待开发内容）
  - `template_content`: 完整 AI 应用设计与开发规范模版（应用名称、应用描述、术语表、导航、应用设计、开发规范等）

**依赖**: 需配置 `studio.base_url`（或环境变量 `STUDIO_BASE_URL`），且 Studio 内部接口 `/internal/api/dip-studio/v1/nodes/{node_id}/application-detail` 可访问。

### 2. `list_all_api_endpoints`

列出所有已加载 OpenAPI 规范中的端点详情，适用于代码生成。

- **参数**: 无
- **返回**: 规范元数据、端点列表（路径、方法、参数、请求体、响应 schema、示例等）及集成信息

### 3. `get_api_code_example`

获取指定 API 端点的代码示例。

- **参数**:
  - `spec_id` (string, 必需): 规范 ID
  - `path` (string, 必需): 端点路径，如 `/api/users/{id}`
  - `method` (string, 必需): HTTP 方法（GET、POST、PUT、DELETE、PATCH 等）
  - `language` (string, 可选): 目标语言，默认 `typescript`，可选 `python`、`javascript`
- **返回**: 代码示例、集成信息及使用说明

## MCP Resources

- **api-spec://{spec_id}** — 完整 OpenAPI 规范文档
- **api-spec://{spec_id}/summary** — 规范摘要（端点列表与统计）
- **api-integration://{spec_id}/{language}** — 指定语言的集成指南
- **api-example://{spec_id}** — 该规范下的端点示例列表

## 项目结构

```
mcp/
├── src/
│   ├── __init__.py
│   ├── server.py           # MCP 服务主入口
│   └── openapi_loader.py   # OpenAPI 规范加载与解析
├── api-specs/              # OpenAPI 规范文档目录
├── config.yaml             # 服务配置
├── requirements.txt        # Python 依赖
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── README.md
├── MCP_SERVER_START.md
├── MCP_CLIENT_CONFIG.md
├── DOCKER.md
├── CURSOR_SETUP.md
├── QUICKSTART.md
├── PROMPT_EXAMPLE.md
└── dip-studio-mcp-chart/   # Helm 部署
```

## 故障排除

### MCP SDK 未找到

```bash
pip install mcp
```

### get_context 请求失败

1. 确认 `config.yaml` 中 `studio.base_url` 正确，或设置环境变量 `STUDIO_BASE_URL`
2. 确认 Studio 服务已启动且内部接口可访问（同网络或 K8s 内）
3. 确认传入的 `node_id` 为有效 UUID v4 格式

### API 规范无法加载

1. 确认 `api-specs` 目录存在且包含有效 OpenAPI 3.x 文件（JSON/YAML）
2. 查看服务日志中的加载错误信息

## 日志

日志输出到标准输出，可通过环境变量 `LOG_LEVEL` 控制级别（DEBUG、INFO、WARNING、ERROR）。

## 相关链接

- [Model Context Protocol](https://modelcontextprotocol.io)
- [DIP Studio 项目](../README.md)
