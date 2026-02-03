# Docker 构建和运行指南

本文档说明如何使用 Docker 构建和运行 DIP Studio MCP Server。

## 前置要求

- Docker 20.10 或更高版本
- Docker Compose 2.0 或更高版本（可选，用于简化管理）

## 快速开始

### 使用 Docker Compose（推荐）

1. **构建并启动服务**：
   ```bash
   docker-compose up -d
   ```

2. **查看日志**：
   ```bash
   docker-compose logs -f
   ```

3. **停止服务**：
   ```bash
   docker-compose down
   ```

### 使用 Docker 命令

1. **构建镜像**：
   ```bash
   docker build -t dip-studio-mcp-server .
   ```

2. **运行容器**：
   ```bash
   docker run -d \
     --name dip-studio-mcp-server \
     -p 8001:8001 \
     -v $(pwd)/requirements:/app/requirements:ro \
     -v $(pwd)/api-specs:/app/api-specs:ro \
     -v $(pwd)/config.yaml:/app/config.yaml:ro \
     dip-studio-mcp-server
   ```

3. **查看日志**：
   ```bash
   docker logs -f dip-studio-mcp-server
   ```

4. **停止容器**：
   ```bash
   docker stop dip-studio-mcp-server
   docker rm dip-studio-mcp-server
   ```

### 使用 Makefile

项目提供了 Makefile 来简化操作：

```bash
# 构建镜像
make build

# 启动服务
make run

# 查看日志
make logs

# 停止服务
make stop

# 测试服务
make test

# 清理（删除容器和镜像）
make clean
```

## 配置说明

### 端口配置

默认端口是 `8001`，可以在 `config.yaml` 中修改：

```yaml
server:
  port: 8001
```

如果修改了端口，需要同时更新：
- `Dockerfile` 中的 `EXPOSE` 指令
- `docker-compose.yml` 中的端口映射
- 运行 `docker run` 时的 `-p` 参数

### 数据目录挂载

容器中的数据目录通过卷挂载，方便更新：

- `./requirements` → `/app/requirements` (只读)
- `./api-specs` → `/app/api-specs` (只读)
- `./config.yaml` → `/app/config.yaml` (只读)

**注意**：如果需要容器内修改文件，可以移除 `:ro`（只读）标志。

## 健康检查

容器包含健康检查，每 30 秒检查一次服务器是否响应：

```bash
# 查看健康状态
docker ps

# 查看健康检查日志
docker inspect dip-studio-mcp-server | grep -A 10 Health
```

## 故障排查

### 查看容器日志

```bash
# 使用 docker-compose
docker-compose logs -f

# 使用 docker
docker logs -f dip-studio-mcp-server
```

### 进入容器调试

```bash
# 使用 docker-compose
docker-compose exec mcp-server /bin/bash

# 使用 docker
docker exec -it dip-studio-mcp-server /bin/bash
```

### 测试服务器

```bash
# 使用 Makefile
make test

# 或手动测试
curl http://localhost:8001/mcp
```

### 常见问题

1. **端口已被占用**：
   - 修改 `config.yaml` 中的端口
   - 更新 Docker 配置中的端口映射

2. **文件权限问题**：
   - 确保挂载的目录有正确的权限
   - 检查 `config.yaml` 中的路径配置

3. **依赖安装失败**：
   - 检查网络连接
   - 查看构建日志中的错误信息

## 生产环境部署

### 安全建议

1. **不要暴露端口到公网**：
   - 使用反向代理（如 Nginx）
   - 配置防火墙规则

2. **使用环境变量**：
   - 敏感配置通过环境变量传递
   - 不要将敏感信息写入镜像

3. **资源限制**：
   ```yaml
   # docker-compose.yml
   services:
     mcp-server:
       deploy:
         resources:
           limits:
             cpus: '1'
             memory: 512M
   ```

### 多阶段构建优化

Dockerfile 使用多阶段构建，最终镜像只包含运行时依赖，减小镜像大小。

### 镜像标签

建议为生产环境使用版本标签：

```bash
docker build -t dip-studio-mcp-server:v1.0.0 .
docker tag dip-studio-mcp-server:v1.0.0 dip-studio-mcp-server:latest
```

## 更新和维护

### 更新代码

1. 拉取最新代码
2. 重新构建镜像：
   ```bash
   docker-compose build
   docker-compose up -d
   ```

### 更新数据文件

数据文件通过卷挂载，更新本地文件后容器会自动使用新文件（无需重启）。

### 更新配置

修改 `config.yaml` 后需要重启容器：

```bash
docker-compose restart
```

## 示例：完整部署流程

```bash
# 1. 克隆项目
git clone <repository>
cd mcp

# 2. 准备数据文件
# 确保 requirements/ 和 api-specs/ 目录有数据

# 3. 构建并启动
docker-compose up -d

# 4. 验证服务
make test

# 5. 查看日志
docker-compose logs -f
```

## 相关文件

- `Dockerfile` - Docker 镜像构建文件
- `docker-compose.yml` - Docker Compose 配置
- `.dockerignore` - Docker 构建忽略文件
- `Makefile` - 便捷命令脚本
- `config.yaml` - 服务器配置文件
