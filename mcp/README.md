# DIP Studio MCP Server

DIP Studio MCP Server 是一个基于 Model Context Protocol (MCP) 的远程服务器，用于读取本地需求文档并为 Cursor 或 Claude Code 提供自动代码生成能力，支持 DIP 应用开发流程。

## 功能特性

- 📄 **多格式文档支持**: 支持读取 PDF、Markdown、Word、TXT 等格式的需求文档
- 📋 **OpenAPI 接口规范**: 支持读取和解析 OpenAPI 3.0.2 规范的接口文档，提供接口定义和端点信息
- 🤖 **智能代码生成**: 基于需求文档和任务描述，使用 LLM 自动生成代码
- 🔧 **Buildkit 集成**: 与 DIP buildkit 工具集成，支持应用转换和打包流程
- 🌐 **远程访问**: 支持通过 HTTP 协议远程访问
- 🔌 **MCP 协议**: 完全兼容 MCP 标准，可与 Cursor、Claude Code 等客户端集成

## 安装

### 前置要求

- Python 3.10 或更高版本
- pip 包管理器

### 安装步骤

1. 克隆或进入项目目录：
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

4. 安装 MCP SDK（如果尚未安装）：
```bash
pip install mcp
```

## 配置

### 1. 配置文件

编辑 `config.yaml` 文件：

```yaml
server:
  host: "0.0.0.0"
  port: 8001  # 如果端口被占用，可以修改为其他端口
  transport: "http"

documents:
  base_path: "./requirements"  # 需求文档存储路径
  supported_formats: [".pdf", ".md", ".docx", ".txt"]

api_specs:
  base_path: "./api-specs"  # OpenAPI 接口规范文档存储路径

llm:
  provider: "openai"  # 或 "anthropic"
  api_key: "${LLM_API_KEY}"  # 从环境变量读取
  model: "gpt-4"
  temperature: 0.7

buildkit:
  path: "../buildkit"  # buildkit 目录路径
```

### 2. 环境变量

设置 LLM API 密钥：

```bash
# OpenAI
export OPENAI_API_KEY="your-api-key-here"

# 或 Anthropic
export ANTHROPIC_API_KEY="your-api-key-here"

# 或使用通用变量（如果 config.yaml 中配置了）
export LLM_API_KEY="your-api-key-here"
```

### 3. 需求文档目录

在 `mcp` 目录下创建 `requirements` 目录，并将需求文档放入其中：

```bash
mkdir -p requirements
# 将你的需求文档（PDF、Markdown 等）放入此目录
```

### 4. API 规范文档目录

在 `mcp` 目录下创建 `api-specs` 目录，并将 OpenAPI 规范文档（JSON 格式）放入其中：

```bash
mkdir -p api-specs
# 将 OpenAPI 3.0.2 规范的 JSON 文件放入此目录
# 例如：ontology-manager-action-type.json, ontology-query.json 等
```

**注意**: 服务器会自动扫描 `api-specs` 目录下的所有 `.json` 文件作为 OpenAPI 规范文档。

## 快速开始

### 1. 启动服务器

详细启动说明请参考 [MCP_SERVER_START.md](./MCP_SERVER_START.md)

**快速启动**:
```bash
cd mcp
python -m src.server
```

服务器默认在 `http://0.0.0.0:8001` 启动，MCP 端点为 `http://localhost:8001/mcp`。

### 2. 配置客户端

详细配置说明请参考 [MCP_CLIENT_CONFIG.md](./MCP_CLIENT_CONFIG.md)

**Cursor 快速配置**:
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

**重要**: 
- 服务器不要求认证，客户端可以直接连接
- 确保服务器已启动后再配置客户端
- 详细配置和故障排除请参考 [MCP_CLIENT_CONFIG.md](./MCP_CLIENT_CONFIG.md)

## 文档导航

- **[MCP_SERVER_START.md](./MCP_SERVER_START.md)** - 服务器启动详细指南
- **[MCP_CLIENT_CONFIG.md](./MCP_CLIENT_CONFIG.md)** - 客户端配置使用指南
- **[DOCKER.md](./DOCKER.md)** - Docker 部署指南
- **[CURSOR_SETUP.md](./CURSOR_SETUP.md)** - Cursor 详细配置说明
- **[QUICKSTART.md](./QUICKSTART.md)** - 快速开始指南

## MCP Tools

服务器提供以下工具（Tools）：

### 需求文档工具

#### 1. `list_requirements`

列出所有可用的需求文档。

**参数**: 无

**返回**: 文档列表和元数据

#### 2. `read_requirement`

读取指定的需求文档。

**参数**:
- `doc_id` (string, 必需): 文档 ID（文件名不含扩展名）

**返回**: 文档内容和元数据

### API 接口工具

#### 3. `list_all_api_endpoints`

列出所有 API 端点详情，优化用于代码生成。

**参数**: 无

**返回**: 完整的 API 规范信息，包括：
- API 规范元数据（标题、版本、base URL、认证方式）
- 端点详情（路径、方法、参数类型、示例值、请求体、响应 schema）
- 集成信息（认证方式、内容类型）

**特点**: 
- 包含完整的类型信息，便于生成类型安全的代码
- 提供示例值，便于理解和使用
- 结构化数据，便于 AI 理解和处理

#### 4. `get_api_code_example`

获取特定 API 端点的代码示例。

**参数**:
- `spec_id` (string, 必需): API 规范 ID
- `path` (string, 必需): 端点路径（如 `/api/users/{id}`）
- `method` (string, 必需): HTTP 方法（GET, POST, PUT, DELETE, PATCH 等）
- `language` (string, 可选): 目标语言（typescript, python, javascript，默认: typescript）

**返回**: 完整的代码示例，包括：
- 可直接使用的函数代码
- 导入语句
- 错误处理
- 使用示例
- 集成配置信息

**示例**: 
- `get_api_code_example("agent-factory", "/agent-factory/v3/agent", "POST", "typescript")`
- `get_api_code_example("agent-app", "/api/agent-app/v1/app/{app_key}/chat/completion", "POST", "python")`

## MCP Resources

服务器提供以下资源（Resources）：

### 需求文档资源

#### 1. `requirement://{doc_id}`

访问特定的需求文档内容。

**示例**: `requirement://example`

### OpenAPI 接口规范资源

#### 2. `api-spec://{spec_id}`

访问完整的 OpenAPI 规范文档。

**示例**: 
- `api-spec://ontology-manager-action-type`
- `api-spec://ontology-manager-network`
- `api-spec://ontology-manager-object-type`
- `api-spec://ontology-manager-relation-type`
- `api-spec://ontology-query`

#### 3. `api-spec://{spec_id}/summary`

访问 OpenAPI 规范的摘要信息（包含端点列表和统计信息）。

**示例**: `api-spec://ontology-query/summary`

### API 集成资源

#### 4. `api-integration://{spec_id}/{language}`

访问 API 集成指南，包含特定语言的集成说明和示例。

**示例**: 
- `api-integration://agent-factory/typescript`
- `api-integration://agent-app/python`

#### 5. `api-example://{spec_id}`

访问 API 端点示例列表。

## 项目结构

```
mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # MCP 服务器主入口
│   ├── document_loader.py     # 文档加载和解析模块
│   └── openapi_loader.py      # OpenAPI 规范加载和解析模块
├── requirements.txt            # Python 依赖
├── config.yaml                 # 服务器配置
├── Dockerfile                  # Docker 镜像构建文件
├── docker-compose.yml         # Docker Compose 配置
├── Makefile                   # 便捷命令脚本
├── README.md                  # 项目总览
├── MCP_SERVER_START.md        # 服务器启动指南
├── MCP_CLIENT_CONFIG.md       # 客户端配置指南
├── DOCKER.md                  # Docker 部署指南
├── CURSOR_SETUP.md            # Cursor 详细配置
├── QUICKSTART.md              # 快速开始指南
├── requirements/              # 需求文档目录
└── api-specs/                 # OpenAPI 规范文档目录
```

## 开发

### 添加新的文档格式支持

编辑 `src/document_loader.py`，在 `_parse_document` 方法中添加新的格式处理逻辑。

### 扩展 OpenAPI 支持

编辑 `src/openapi_loader.py`，可以：
- 添加新的代码生成语言支持
- 自定义代码示例模板
- 扩展端点信息提取逻辑

## 故障排除

### 问题: MCP SDK 未找到

**解决方案**: 
```bash
pip install mcp
```

### 问题: 文档无法读取

**检查**:
1. 确认 `requirements` 目录存在
2. 确认文档格式在 `supported_formats` 列表中
3. 检查文档文件权限

### 问题: API 规范无法加载

**检查**:
1. 确认 `api-specs` 目录存在
2. 确认文件格式正确（JSON 或 YAML）
3. 检查文件是否为有效的 OpenAPI 3.0.2 规范
4. 查看服务器日志中的错误信息

## 日志

服务器日志会输出到标准输出，包含以下信息：
- 服务器启动和初始化状态
- 工具调用记录
- 错误和警告信息

日志级别可通过环境变量 `LOG_LEVEL` 控制（DEBUG, INFO, WARNING, ERROR）。

## 许可证

本项目遵循与 DIP Studio 项目相同的许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 相关链接

- [Model Context Protocol 文档](https://modelcontextprotocol.io)
- [DIP Studio 项目](../README.md)
- [Buildkit 文档](../buildkit/README.md)
