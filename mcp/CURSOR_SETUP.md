# Cursor MCP 服务器配置指南

## 重要说明

**MCP 服务器不要求认证**，客户端可以直接连接，无需配置认证令牌。

## 基本配置

### 最简单的配置（推荐）

在项目根目录创建或编辑 `.cursor/mcp.json` 文件：

```json
{
  "mcpServers": {
    "dip-studio": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

**无需配置 headers 或认证令牌**，服务器会直接接受连接。

## 如果 Cursor 仍然要求认证

如果 Cursor 客户端仍然显示 "缺少认证令牌" 的错误（这是 Cursor 客户端的默认行为），可以使用以下占位符配置：

### 方案 1：使用占位符 token（如果 Cursor 要求）

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

**注意**：服务器不会验证这个 token，任何值都可以工作。

### 方案 2：在 Cursor 设置中配置

1. 打开 Cursor 设置（`Cmd+,` 或 `Ctrl+,`）
2. 导航到 **Tools & MCP** > **Installed MCP Servers**
3. 找到 `dip-studio` 服务器
4. 点击 **Configure** 或 **Authenticate** 按钮
5. 在认证配置中，可以设置任意 token（如 `no-auth-required`），服务器不会验证
6. **URL**: `http://localhost:8001/mcp`

## 验证配置

配置完成后：

1. 检查 Cursor 的 MCP 日志，应该显示连接成功
2. 尝试使用工具，例如：
   - `list_requirements` - 列出需求文档
   - `list_api_specs` - 列出 API 规范
   - `get_api_spec` - 获取 API 规范详情

## 故障排除

### 问题：仍然显示 "缺少认证令牌"

这是 Cursor 客户端的默认行为。解决方法：
- 在 `.cursor/mcp.json` 中添加 `headers` 配置（见方案 1），使用任意 token 值
- 或在 Cursor 设置中配置认证（见方案 2）
- **重要**：服务器不会验证 token，所以任何值都可以工作

### 问题：连接失败

- 确保服务器正在运行（`python -m src.server`）
- 检查 URL 是否正确（默认是 `http://localhost:8001/mcp`）
- 检查端口是否被占用（默认 8001）
- 检查防火墙设置
- 查看服务器日志中的错误信息
- 重启 Cursor IDE

### 问题：工具列表为空

- 确保服务器已成功启动
- 检查服务器日志中是否有错误
- 验证工具是否正确注册
- 检查 Cursor 的 MCP 日志，确认连接状态

## 服务器配置说明

**MCP 服务器完全不要求认证**：
- 服务器代码中没有实现任何认证逻辑
- 所有客户端都可以直接连接
- 如果 Cursor 客户端要求配置 token，可以使用任意值，服务器不会验证
