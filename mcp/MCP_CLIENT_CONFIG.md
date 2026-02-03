# MCP Client 配置使用指南

本文档说明如何配置 MCP 客户端（如 Cursor、Claude Code）连接到 DIP Studio MCP Server。

## 前置要求

1. **MCP Server 已启动**
   - 服务器运行在 `http://localhost:8001`
   - MCP 端点为 `http://localhost:8001/mcp`
   - 参考 [MCP_SERVER_START.md](./MCP_SERVER_START.md) 启动服务器

2. **客户端支持 MCP 协议**
   - Cursor IDE
   - Claude Code
   - 或其他支持 MCP 的客户端

## Cursor IDE 配置

### 1. 创建配置文件

在项目根目录（或工作区根目录）创建 `.cursor/mcp.json` 文件：

```json
{
  "mcpServers": {
    "dip-studio": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

### 2. 配置说明

**重要**: MCP Server **不要求认证**，客户端可以直接连接。

**基本配置**:
- `url`: MCP 服务器端点地址
- 默认端口: `8001`
- 如果服务器运行在其他机器，将 `localhost` 替换为服务器 IP 或域名

**完整配置示例**:

```json
{
  "mcpServers": {
    "dip-studio": {
      "url": "http://localhost:8001/mcp",
      "description": "DIP Studio MCP Server - 提供需求文档和 API 接口信息"
    }
  }
}
```

### 3. 如果 Cursor 要求认证（可选）

某些 Cursor 版本可能要求配置认证头，可以使用占位符：

```json
{
  "mcpServers": {
    "dip-studio": {
      "url": "http://localhost:8001/mcp",
      "headers": {
        "Authorization": "Bearer no-auth-required"
      }
    }
  }
}
```

**注意**: 服务器不会验证这个 token，任何值都可以工作。

### 4. 验证配置

1. **重启 Cursor IDE**（配置更改后需要重启）

2. **检查 MCP 连接状态**:
   - 打开 Cursor 设置（`Cmd+,` 或 `Ctrl+,`）
   - 导航到 **Tools & MCP** > **Installed MCP Servers**
   - 应该看到 `dip-studio` 服务器，状态为 "Connected"

3. **测试工具**:
   - 在 Cursor 中尝试使用工具
   - 例如：`@dip-studio list_requirements`
   - 或通过命令面板调用 MCP 工具

## Claude Code 配置

### 方式 1: 配置文件

在项目根目录创建 `.mcp.json` 文件：

```json
{
  "mcpServers": {
    "dip-studio": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

### 方式 2: 命令行配置

```bash
claude mcp add --transport http dip-studio http://localhost:8001/mcp
```

### 验证配置

```bash
# 列出已配置的 MCP 服务器
claude mcp list

# 测试连接
claude mcp test dip-studio
```

## 可用工具

配置成功后，客户端可以使用以下工具：

### 需求文档工具

1. **`list_requirements`**
   - 列出所有可用的需求文档
   - 返回文档列表和元数据

2. **`read_requirement`**
   - 读取指定的需求文档
   - 参数: `doc_id` (文档 ID，文件名不含扩展名)
   - 返回: 文档内容和元数据

### API 接口工具

3. **`list_all_api_endpoints`**
   - 列出所有 API 端点详情
   - 返回完整的 API 规范信息，包括：
     - API 规范元数据（标题、版本、base URL）
     - 端点详情（路径、方法、参数、请求体、响应）
     - 集成信息（认证方式、内容类型）
   - **优化用于代码生成**：包含类型信息、示例值、schema 等

4. **`get_api_code_example`**
   - 获取特定 API 端点的代码示例
   - 参数:
     - `spec_id`: API 规范 ID
     - `path`: 端点路径（如 `/api/users/{id}`）
     - `method`: HTTP 方法（GET, POST, PUT, DELETE 等）
     - `language`: 目标语言（typescript, python, javascript，默认: typescript）
   - 返回: 完整的代码示例，包含导入、配置和使用说明

## 使用示例

### 在 Cursor 中使用

1. **列出需求文档**:
   ```
   @dip-studio list_requirements
   ```

2. **读取需求文档**:
   ```
   @dip-studio read_requirement example
   ```

3. **列出所有 API 端点**:
   ```
   @dip-studio list_all_api_endpoints
   ```

4. **获取代码示例**:
   ```
   @dip-studio get_api_code_example agent-factory /agent-factory/v3/agent POST typescript
   ```

### 在代码生成中使用

Cursor 可以自动使用这些工具来：

1. **理解需求**: 通过 `read_requirement` 获取需求文档内容
2. **查看 API**: 通过 `list_all_api_endpoints` 获取所有可用的 API 接口
3. **生成代码**: 基于 API 信息和需求文档生成集成代码
4. **获取示例**: 通过 `get_api_code_example` 获取特定端点的代码示例

## 可用资源

除了工具，还可以通过资源 URI 访问：

### 需求文档资源

- `requirement://{doc_id}` - 访问需求文档内容

### API 规范资源

- `api-spec://{spec_id}` - 访问完整的 OpenAPI 规范
- `api-spec://{spec_id}/summary` - 访问 API 规范摘要
- `api-integration://{spec_id}/{language}` - 访问集成指南
- `api-example://{spec_id}` - 访问 API 示例列表

## 故障排除

### 问题 1: 连接失败

**症状**: Cursor 显示 "无法连接到 MCP 服务器"

**解决方案**:
1. 确认服务器正在运行：
   ```bash
   curl http://localhost:8001/mcp
   ```
2. 检查 URL 配置是否正确
3. 检查端口是否匹配（默认 8001）
4. 如果服务器在其他机器，检查网络连接和防火墙

### 问题 2: 工具列表为空

**症状**: 连接成功但看不到工具

**解决方案**:
1. 检查服务器日志，确认工具已注册
2. 重启 Cursor IDE
3. 检查 Cursor 的 MCP 日志

### 问题 3: 认证错误

**症状**: 显示 "缺少认证令牌"

**解决方案**:
- 服务器不要求认证，这是客户端默认行为
- 在配置中添加 `headers` 字段，使用任意 token 值：
  ```json
  {
    "headers": {
      "Authorization": "Bearer no-auth-required"
    }
  }
  ```

### 问题 4: 工具调用失败

**症状**: 工具调用返回错误

**解决方案**:
1. 查看服务器日志中的错误信息
2. 检查参数是否正确
3. 确认数据目录中有相应的文件
4. 检查文件权限

### 问题 5: 远程连接问题

**症状**: 服务器在其他机器，无法连接

**解决方案**:
1. 确保服务器监听 `0.0.0.0` 而不是 `127.0.0.1`
2. 检查防火墙设置，确保端口 8001 开放
3. 使用服务器 IP 或域名替换 `localhost`
4. 如果使用 HTTPS，确保 URL 使用 `https://`

## 高级配置

### 自定义端口

如果服务器使用非默认端口：

```json
{
  "mcpServers": {
    "dip-studio": {
      "url": "http://localhost:8002/mcp"
    }
  }
}
```

### 远程服务器

连接到远程服务器：

```json
{
  "mcpServers": {
    "dip-studio": {
      "url": "http://192.168.1.100:8001/mcp"
    }
  }
}
```

### 使用域名

```json
{
  "mcpServers": {
    "dip-studio": {
      "url": "http://mcp.example.com:8001/mcp"
    }
  }
}
```

## 最佳实践

1. **本地开发**: 使用 `localhost:8001`
2. **团队共享**: 部署到共享服务器，使用服务器 IP 或域名
3. **生产环境**: 使用 HTTPS 和反向代理（如 Nginx）
4. **配置管理**: 将 `.cursor/mcp.json` 添加到 `.gitignore`（如果包含敏感信息）

## 相关文档

- [MCP_SERVER_START.md](./MCP_SERVER_START.md) - 服务器启动指南
- [README.md](./README.md) - 项目总览
- [DOCKER.md](./DOCKER.md) - Docker 部署指南
