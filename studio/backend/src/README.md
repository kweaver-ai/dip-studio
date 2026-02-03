# DIP Studio Backend

DIP Studio 项目管理模块后端服务。

## 技术栈

- **Web框架**: FastAPI (异步)
- **数据库**: MariaDB（结构化数据与文档内容/文档块均存于 MariaDB）
- **ORM/驱动**: aiomysql
- **配置管理**: pydantic-settings
- **架构模式**: 六边形架构 (Hexagonal Architecture)

## 目录结构

```
src/
├── main.py                    # 应用入口
├── domains/                   # 领域模型
├── ports/                     # 端口接口
├── adapters/                  # 适配器实现
├── application/               # 应用服务
├── routers/                   # API路由
└── infrastructure/            # 基础设施
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
cp .env.example .env
```

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 启动服务

```bash
# 开发模式
python scripts/run_dev.py

# 或使用 uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## API 文档

启动服务后访问:
- Swagger UI: http://localhost:8000/api/dip-studio/v1/docs
- ReDoc: http://localhost:8000/api/dip-studio/v1/redoc

## 主要功能

### 项目管理
- 创建/更新/删除项目
- 项目列表查询

### 节点管理
- 创建应用/页面/功能节点
- 节点树查询
- 节点移动

### 项目词典
- 术语定义管理

### 功能设计文档
- 文档块增量更新
- 支持 text/list/table/plugin 类型

## 开发

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black src/
ruff check src/ --fix
```

## License

MIT
