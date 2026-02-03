# MCP Server 启动指南

本文档说明如何启动 DIP Studio MCP Server。

## 前置要求

- Python 3.10 或更高版本
- pip 包管理器
- 已安装项目依赖

## 安装依赖

### 1. 创建虚拟环境（推荐）

```bash
cd /Users/lucyjiang/dipworkspace/dip-studio/mcp
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 MCP SDK

```bash
pip install mcp
```

如果官方包不可用，可以使用：

```bash
pip install git+https://github.com/modelcontextprotocol/python-sdk.git
```

## 配置服务器

### 1. 编辑配置文件

编辑 `config.yaml` 文件：

```yaml
server:
  host: "0.0.0.0"  # 监听所有网络接口
  port: 8001       # 服务器端口（如果被占用可修改）
  transport: "http"

documents:
  base_path: "./requirements"  # 需求文档存储路径
  supported_formats: [".pdf", ".md", ".docx", ".txt"]

api_specs:
  base_path: "./api-specs"  # API规范文档存储路径
```

### 2. 准备数据目录

确保以下目录存在并包含相应文件：

```bash
# 需求文档目录
mkdir -p requirements
# 将需求文档（PDF、Markdown、Word、TXT）放入此目录

# API 规范文档目录
mkdir -p api-specs
# 将 OpenAPI 规范文件（JSON 或 YAML）放入此目录
```

## 启动方式

### 方式 1: 直接运行（开发环境）

```bash
cd /Users/lucyjiang/dipworkspace/dip-studio/mcp
python -m src.server
```

服务器将在 `http://0.0.0.0:8001` 启动，MCP 端点为 `http://localhost:8001/mcp`。

### 方式 2: 使用 Docker（生产环境）

#### 构建镜像

```bash
docker build -t dip-studio-mcp-server .
```

#### 运行容器

```bash
# 前台运行（可以看到日志）
docker run --rm -it \
  -p 8001:8001 \
  -v $(pwd)/requirements:/app/requirements:ro \
  -v $(pwd)/api-specs:/app/api-specs:ro \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  dip-studio-mcp-server

# 或使用 docker-compose
docker-compose up
```

#### 后台运行

```bash
docker-compose up -d
docker-compose logs -f  # 查看日志
```

### 方式 3: 使用 Makefile

```bash
# 构建镜像
make build

# 启动服务
make run

# 查看日志
make logs

# 停止服务
make stop
```

## 验证服务器运行

### 1. 检查服务器状态

```bash
# 测试 MCP 端点
curl http://localhost:8001/mcp

# 或使用 Python
python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8001/mcp').read())"
```

### 2. 查看服务器日志

服务器启动后会输出日志，包括：

```
INFO - MCP Server initialized successfully
INFO - Server will listen on 0.0.0.0:8001
INFO - MCP endpoint will be available at http://0.0.0.0:8001/mcp
INFO - Registered requirement document tools: list_requirements, read_requirement
INFO - Registered API tools: list_all_api_endpoints, get_api_code_example
INFO - Registered resources: requirement, api-spec, api-integration, api-example
INFO - Starting DIP Studio MCP Server (HTTP transport)...
```

### 3. 检查工具注册

服务器启动时会自动注册以下工具：

- **需求文档工具**:
  - `list_requirements` - 列出所有需求文档
  - `read_requirement` - 读取指定需求文档

- **API 接口工具**:
  - `list_all_api_endpoints` - 列出所有 API 端点详情
  - `get_api_code_example` - 获取 API 端点代码示例

## 常见问题

### 问题 1: 端口被占用

**错误信息**: `Address already in use`

**解决方案**:
1. 修改 `config.yaml` 中的端口：
   ```yaml
   server:
     port: 8002  # 改为其他端口
   ```
2. 或停止占用端口的进程：
   ```bash
   lsof -ti:8001 | xargs kill -9
   ```

### 问题 2: 模块导入错误

**错误信息**: `ModuleNotFoundError: No module named 'mcp'`

**解决方案**:
```bash
pip install mcp
# 或
pip install git+https://github.com/modelcontextprotocol/python-sdk.git
```

### 问题 3: 配置文件未找到

**错误信息**: `Config file not found`

**解决方案**:
- 确保在 `mcp` 目录下运行服务器
- 检查 `config.yaml` 文件是否存在

### 问题 4: 数据目录为空

**警告信息**: `No documents found` 或 `No API specs found`

**解决方案**:
- 检查 `requirements/` 和 `api-specs/` 目录是否存在
- 确保目录中有相应格式的文件
- 检查文件权限

### 问题 5: Docker 容器无法启动

**解决方案**:
1. 检查 Docker 是否运行：`docker ps`
2. 查看容器日志：`docker-compose logs`
3. 检查端口映射是否正确
4. 检查卷挂载路径是否正确

## 性能优化

### 1. 启用日志级别控制

```bash
# 设置日志级别
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# 运行服务器
python -m src.server
```

### 2. 生产环境配置

对于生产环境，建议：

1. **使用 Docker**：便于部署和管理
2. **配置反向代理**：使用 Nginx 等反向代理
3. **设置资源限制**：在 Docker 中配置 CPU 和内存限制
4. **启用日志轮转**：配置日志管理

## 服务器端点

启动后，服务器提供以下端点：

- **MCP 端点**: `http://localhost:8001/mcp`
  - 这是 MCP 客户端连接的主要端点
  - 支持 MCP 协议的所有操作（工具调用、资源访问等）

- **健康检查**: 可以通过访问 MCP 端点来检查服务器状态

## 停止服务器

### 直接运行方式

按 `Ctrl+C` 停止服务器

### Docker 方式

```bash
# 停止容器
docker-compose down

# 或使用 docker 命令
docker stop dip-studio-mcp-server
docker rm dip-studio-mcp-server
```

## 下一步

服务器启动后，请参考 [MCP_CLIENT_CONFIG.md](./MCP_CLIENT_CONFIG.md) 配置客户端连接。
