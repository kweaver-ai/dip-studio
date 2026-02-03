# DIP Studio OpenAPI 文档

本目录包含 DIP Studio 项目管理模块的 OpenAPI 3.1 规范文档。

## 目录结构

```
openapi/
├── README.md                           # 本说明文件
└── public/                             # 公开 API 文档
    ├── public.openapi.yaml             # 主 OpenAPI 规范文件
    └── studio/                         # Studio 模块定义
        ├── studio.paths.yaml           # API 路径定义
        └── studio.schemas.yaml         # 数据模型定义
```

## 文件说明

### public.openapi.yaml

主 OpenAPI 规范文件，包含：
- API 信息（标题、描述、版本）
- 标签定义
- 安全配置
- 服务器配置
- 路径引用
- Schema 引用

### studio/studio.paths.yaml

API 路径定义文件，包含所有 API 端点的详细定义：
- 项目管理接口 (Project)
- 节点管理接口 (Node)
- 项目词典接口 (Dictionary)
- 功能设计文档接口 (Document)
- 健康检查接口 (Health)

### studio/studio.schemas.yaml

数据模型定义文件，包含所有请求和响应的 Schema 定义：
- 项目相关 Schema
- 节点相关 Schema
- 词典相关 Schema
- 文档相关 Schema
- 通用 Schema（健康检查、错误响应）

## API 概览

### 项目管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /projects | 创建项目 |
| GET | /projects | 获取项目列表 |
| GET | /projects/{project_id} | 获取项目详情 |
| PUT | /projects/{project_id} | 更新项目 |
| DELETE | /projects/{project_id} | 删除项目 |

### 节点管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /nodes/application | 创建应用节点 |
| POST | /nodes/page | 创建页面节点 |
| POST | /nodes/function | 创建功能节点 |
| GET | /projects/{project_id}/nodes/tree | 获取节点树 |
| PUT | /nodes/{node_id} | 更新节点 |
| PUT | /nodes/move | 移动节点 |
| DELETE | /nodes/{node_id} | 删除节点 |

### 项目词典

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /dictionary | 新增术语 |
| GET | /dictionary | 查询词典 |
| PUT | /dictionary/{id} | 更新术语 |
| DELETE | /dictionary/{id} | 删除术语 |

### 功能设计文档（TipTap + fast-json-patch）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /documents/{document_id} | 根据 document_id 获取完整文档 JSON（创建功能节点时已初始化为空 {}） |
| PUT | /documents/{document_id} | 对文档内容 {} 做 RFC 6902 JSON Patch 增量更新，仅返回是否更新成功 |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |
| GET | /ready | 就绪检查 |

## 使用方式

### 在线查看

启动 DIP Studio 后端服务后，可以通过以下 URL 查看 API 文档：

- Swagger UI: http://localhost:8000/api/dip-studio/v1/docs
- ReDoc: http://localhost:8000/api/dip-studio/v1/redoc
- OpenAPI JSON: http://localhost:8000/api/dip-studio/v1/openapi.json

### 本地预览

可以使用以下工具预览 OpenAPI 文档：

1. **Swagger Editor**
   ```bash
   # 使用 Docker
   docker run -p 8080:8080 -e SWAGGER_FILE=/api/public.openapi.yaml \
     -v $(pwd)/public:/api swaggerapi/swagger-editor
   ```

2. **Redocly CLI**
   ```bash
   npx @redocly/cli preview-docs public/public.openapi.yaml
   ```

3. **VS Code 插件**
   - OpenAPI (Swagger) Editor
   - Swagger Viewer

### 代码生成

可以使用 OpenAPI 规范生成客户端 SDK：

```bash
# 使用 openapi-generator
npx @openapitools/openapi-generator-cli generate \
  -i public/public.openapi.yaml \
  -g typescript-axios \
  -o ../generated/client
```

## 维护说明

当后端 API 发生变化时，需要同步更新 OpenAPI 文档：

1. 更新 `studio.paths.yaml` 中的路径定义
2. 更新 `studio.schemas.yaml` 中的 Schema 定义
3. 如有新增路径，在 `public.openapi.yaml` 中添加引用

## 参考

- [OpenAPI 3.1 规范](https://spec.openapis.org/oas/v3.1.0)
- [Swagger 官方文档](https://swagger.io/docs/)
