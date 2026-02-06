"""MCP Server main entry point for DIP Studio."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    # Fallback: create a simple server structure
    MCP_AVAILABLE = False
    FastMCP = None

from .openapi_loader import OpenAPILoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances (will be initialized in setup)
openapi_loader: OpenAPILoader | None = None
mcp: FastMCP | None = None
studio_base_url: str = ""
# Server transport mode: "http" (SSE) or "streamable-http"
server_transport: str | None = None

# 标准开发任务说明（get_context 返回中附带，供 Coding Agent 使用）
DEVELOPMENT_TASK = """请你作为本项目的专业开发助手，基于当前功能节点以及其上下文：

1. 先全面阅读与当前节点相关的设计文档和上游/下游节点信息，理解业务背景和已有实现。
2. 在充分理解的基础上，编写或修改所需的代码（包括后端接口、领域逻辑、数据访问层或必要的前端代码），保证与现有架构和约定风格一致。
3. 如涉及数据库或接口契约变更，请同步考虑并描述数据结构、接口入参/出参的设计。
4. 对你编写或修改的代码，给出简要的设计说明（核心思路、关键数据流、边界条件处理）。
5. 如有必要，请给出对应的测试思路或示例测试用例（单元测试或集成测试），以便后续补充自动化测试。

回答中请优先给出可直接使用的代码片段，并避免与现有逻辑产生冲突。"""

# 技术要求列表（get_context 返回中附带）
TECHNICAL_REQUIREMENTS = [
    "使用 Python 3 作为后端语言",
    "在 .venv 下创建 Python 虚拟环境",
    "使用 FastAPI 作为后端服务框架",
    "后端接口超时时间为 1 分钟",
    "使用 TypeScript 作为前端开发语言",
    "使用 ReactJS 作为前端框架",
    "使用 Tailwind CSS 作为 CSS 框架",
    "使用 Ant Design 作为 UI 框架，参考 @docs/vendor/antdesign/llms.txt",
    "使用 @kweaver-ai/chatkit 作为 AI 助手交互组件，安装 NPM 包后仔细阅读 README.md 了解使用方式",
]


# 开发规范固定内容（不包含应用名称 / 导航 / 页面结构，由 _build_template_content 动态拼接）
CODE_GUIDE_TEMPLATE = """
## 注意
- 在编写代码前，一定要仔细阅读文档
- 完全按照应用设计来开发，不要实现任何应用设计中没有提到的功能
- 不要 Mock 任何数据，如果获取不到数据显示 “--”

## 技术规格
- 使用 TypeScript 作为前端开发语言
- 使用 ReactJS 作为前端框架
- 使用 React Router 6 作为前端路由框架
- 使用 axios 作为 HTTP 库
- 使用 Tailwind CSS 作为 CSS 框架
- 使用 Vite 作为打包工具
- 使用 Ant Design 作为 UI 框架，先阅读一遍组件列表 https://ant.design/llms.txt，在需要的时候仔细查阅组件 API
- 使用 @kweaver-ai/chatkit 作为 AI 助手交互组件，安装 NPM 包后仔细阅读 README.md 了解使用方式

## 调试
- 使用 Vite 进行本地代理解决 CORS 问题，代理地址为：/api
- 使用环境变量注入以下参数：
  - API 服务根路径
  - token

## 代码要求
你要开发的是一个 qiankun 微应用，项目代码必须遵循以下要求。

## 主应用注入的 props
以下是由主应用注入的，在微应用中需要使用到的 props，推荐在前端项目中定义为 TypeScript 的 `MicroAppProps` 接口。其语义如下（JSON Schema 形式，仅供说明）：

```yaml
$schema: https://json-schema.org/draft/2020-12/schema
$title: MicroAppProps

MicroAppProps:
  type: object
  properties:
    token:
      type: object
      properties:
        $ref: '#/schema/GetAccessToken'
        $ref: '#/schema/RefreshToken'
        $ref: '#/schema/TokenExpiredHandler'
    route:
      $ref: '#/schema/Route'
    User:
      $ref: '#/schema/User'
    renderAppMenu:
      $ref: '#/schema/RenderAppMenu'
    logout:
      $ref: '#/schema/Logout'
    SetMicroAppState:
      $ref: '#/schema/SetMicroAppState'
    onMicroAppStateChange:
      $ref: '#/schema/MicroAppStateChangeHandler'
    container:
      $ref: '#/schema/RootContainer'

schema:
  GetAccessToken:
    type: function
    name: accessToken
    summary: 获取 Access Token
    returns:
      type: string
      description: 返回 Token

  RefreshToken:
    type: function
    name: refreshToken
    summary: 刷新 Access Token
    returns:
      type: object
      properties:
        accessToken:
          type: string
          description: 返回新的 Access Token

  TokenExpiredHandler:
    type: function
    name: onTokenExpired
    summary: Token 过期处理函数
    parameters:
      - name: code
        type: number
        description: 可选的错误码

  Route:
    type: object
    properties:
      basename:
        type: string
        description: 应用路由基础路径，例如 "dip-hub/application/123"

  User:
    type: object
    properties:
      id:
        type: string
      vision_name:
        type: getter
        description: 获取用户显示名称
        returns:
          type: string
      account:
        type: getter
        description: 获取用户账号

  RenderAppMenu:
    type: function
    description: 渲染应用菜单
    parameters:
      - name: container
        type: (HTMLElement | string)

  Logout:
    type: function
    description: 用户登出函数

  SetMicroAppState:
    type: function
    description: 设置微应用状态
    parameters:
      - name: state
        type: Record<string, any>
    returns:
      type: boolean

  MicroAppStateChangeHandler:
    type: function
    description: 监听微应用状态变化
    parameters:
      - type: function
        name: callback
        description: 状态变化回调函数
        parameters:
          - name: state
            type: any
          - name: prev
            type: any
      - name: fireImmediately
        type: boolean
        description: 是否立即触发回调
    returns:
      type: function
      description: 取消监听函数

  RootContainer:
    type: HTMLElement
    description: 容器元素
```

### 导出 qiankun 生命周期函数
入口文件 `main.tsx` 中需要导出 `bootstrap`、`mount`、`unmount` 三个 qiankun 生命周期函数，例如：

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider } from "antd";
import { renderWithQiankun, qiankunWindow } from "vite-plugin-qiankun/dist/helper";
import App from "./App";
import type { MicroAppProps } from "./micro-app";

let root: ReturnType<typeof ReactDOM.createRoot> | null = null;

const render = ({ container, route, token, user, setMicroAppState, onMicroAppStateChange }: MicroAppProps = {}) => {
  const rootElement = container ? container.querySelector("#root") || container : document.querySelector("#root");

  if (!rootElement) {
    return;
  }

  if (root) {
    root.unmount();
  }

  root = ReactDOM.createRoot(rootElement as HTMLElement);
  root.render(
    <React.StrictMode>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: "#b45309",
            colorTextBase: "#1f2937",
            fontFamily:
              "'IBM Plex Sans', 'Noto Sans SC', 'PingFang SC', sans-serif"
          }
        }}
      >
        <App
          basename={route?.basename}
          token={token}
          user={user}
          setMicroAppState={setMicroAppState}
          onMicroAppStateChange={onMicroAppStateChange}
        />
      </ConfigProvider>
    </React.StrictMode>
  );
};

renderWithQiankun({
  mount(props) {
    console.log("[微应用] mount", props);
    render(props);
  },
  bootstrap() {
    console.log("[微应用] bootstrap");
  },
  unmount(props: any) {
    console.log("[微应用] unmount");
    if (root) {
      root.unmount();
      root = null;
    }
  },
  update(props: any) {
    console.log("[微应用] update", props);
  }
});

if (!qiankunWindow.__POWERED_BY_QIANKUN__) {
  render();
}
```

### 路由
从 props 中获取 `basename` 并传递给路由应用，示例：

```tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import type { MicroAppProps } from "./micro-app";

const App = ({ basename = "/" }: MicroAppProps) => {
  return (
    <BrowserRouter basename={basename}>
      <Routes>
        <Route path="/" element={<Home />} />
        {/* 其他路由 */}
      </Routes>
    </BrowserRouter>
  );
};

export default App;
```

### 认证集成
在微应用中接收主应用注入的 token 和用户信息，典型使用方式：

```tsx
import { BrowserRouter } from "react-router-dom";
import type { MicroAppProps } from "./micro-app";

const App = ({ basename, token, user }: MicroAppProps) => {
  useEffect(() => {
    if (token) {
      // 设置 HTTP 请求的 token
      // axios.defaults.headers.common["Authorization"] = `Bearer ${token.accessToken}`;

      // 监听 token 过期
      if (token.onTokenExpired) {
        // 在 HTTP 拦截器中调用
      }
    }
  }, [token]);

  return (
    <BrowserRouter basename={basename}>
      {/* 应用内容 */}
    </BrowserRouter>
  );
};
```

### 适配 Vite 与构建
- 微应用基于 Vite 构建，需要引入 `vite-plugin-qiankun`。
- 在 `vite.config.ts` 中配置 qiankun 插件，并设置 `base` 属性与 `packageName` 对应，例如：

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import qiankun from "vite-plugin-qiankun";

const packageName = "dip-for-talent";

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    qiankun(packageName, {
      useDevMode: mode === "development"
    })
  ],
  base: "/dip-for-talent/"
}));
```
"""


def _build_template_content(data: Dict[str, Any]) -> str:
    """
    基于 Studio 返回的 context/content_to_develop 构建完整的 AI 应用设计 + 开发规范模版内容。

    结构包括：
    - 应用名称 / 应用描述
    - 术语表
    - 导航（多页面时）
    - 应用设计（页面 + 功能 + 文档内容）
    - 开发规范（固定说明 + DEVELOPMENT_TASK + TECHNICAL_REQUIREMENTS）
    """
    context_items: List[Dict[str, Any]] = list(data.get("context") or [])
    content_items: List[Dict[str, Any]] = list(data.get("content_to_develop") or [])
    all_items: List[Dict[str, Any]] = context_items + content_items

    def _get_node(item: Dict[str, Any]) -> Dict[str, Any]:
        return item.get("node") or {}

    # 应用节点：优先从 context 中查找 node_type == application
    app_item: Optional[Dict[str, Any]] = None
    for item in all_items:
        node = _get_node(item)
        if node.get("node_type") == "application":
            app_item = item
            break

    app_node: Dict[str, Any] = _get_node(app_item) if app_item else {}
    app_name: str = app_node.get("name") or ""
    app_description: str = app_node.get("description") or ""

    # 1. 基本信息：应用名称 / 应用描述
    basic_section_lines: List[str] = [
        "开发 AI 应用。",
        "",
        f"- 应用名称：{app_name or '--'}",
        f"- 应用描述：{app_description or '--'}",
    ]
    basic_section = "\n".join(basic_section_lines)

    # 2. 术语表：当前版本仅输出表头和占位行，后续可从文档中解析
    glossary_lines: List[str] = [
        "# 术语表",
        "",
        "| 术语 | 解释 |",
        "| -- | -- |",
        "| -- | -- |",
    ]
    glossary_section = "\n".join(glossary_lines)

    # 3. 页面与功能分组
    pages_by_id: Dict[str, Dict[str, Any]] = {}
    for item in all_items:
        node = _get_node(item)
        if node.get("node_type") == "page" and node.get("id"):
            pages_by_id[node["id"]] = {"node": node, "item": item}

    # functions 仅从 content_to_develop 中聚合（目标节点及其后代）
    functions_by_page_id: Dict[str, List[Dict[str, Any]]] = {}
    for item in content_items:
        node = _get_node(item)
        if node.get("node_type") == "function":
            parent_id = node.get("parent_id")
            if parent_id:
                functions_by_page_id.setdefault(parent_id, []).append(item)

    # 页面按 sort 排序（若存在）
    pages: List[Dict[str, Any]] = list(pages_by_id.values())
    pages.sort(key=lambda p: (p["node"].get("sort") is None, p["node"].get("sort", 0)))

    # 4. 导航（多页面时才生成）
    nav_section = ""
    if len(pages) > 1 and app_name:
        nav_lines: List[str] = [app_name]
        for page in pages:
            node = page["node"]
            page_name = node.get("name") or "--"
            page_desc = node.get("description") or "--"
            nav_lines.append(f"  |-- {page_name}: {page_desc}")
        nav_body = "\n".join(nav_lines)
        nav_section = "# 导航\n\n```\n" + nav_body + "\n```"

    # 5. 应用设计：按页面分组功能节点
    app_design_lines: List[str] = ["# 应用设计"]
    if not pages:
        app_design_lines.append("")
        app_design_lines.append("（当前节点下暂无页面节点）")
    else:
        for page_idx, page in enumerate(pages, start=1):
            node = page["node"]
            page_id = node.get("id")
            page_name = node.get("name") or "--"

            app_design_lines.append("")
            app_design_lines.append(f"## {page_name}")

            functions: List[Dict[str, Any]] = functions_by_page_id.get(page_id, [])
            if not functions:
                app_design_lines.append("")
                app_design_lines.append("（该页面当前没有功能节点）")
                continue

            for func_idx, func_item in enumerate(functions, start=1):
                func_node = _get_node(func_item)
                func_name = func_node.get("name") or "--"
                title_no = f"{page_idx}.{func_idx}"

                app_design_lines.append("")
                app_design_lines.append(f"### 功能 {title_no} {func_name}")

                doc_text = (func_item.get("document_text") or "").strip()
                if not doc_text:
                    doc_text = "--"
                app_design_lines.append("")
                app_design_lines.append(doc_text)

    app_design_section = "\n".join(app_design_lines)

    # 6. 开发规范：固定说明 + DEVELOPMENT_TASK + TECHNICAL_REQUIREMENTS
    dev_spec_header = "# 开发规范"
    dev_spec_body = CODE_GUIDE_TEMPLATE.strip()

    dev_task_section_lines: List[str] = [
        "## 开发任务说明",
        "",
        DEVELOPMENT_TASK.strip(),
    ]
    dev_task_section = "\n".join(dev_task_section_lines)

    tech_req_lines: List[str] = ["## 附加技术要求", ""]
    tech_req_lines.extend(f"- {req}" for req in TECHNICAL_REQUIREMENTS)
    tech_req_section = "\n".join(tech_req_lines)

    dev_spec_section = "\n\n".join(
        part for part in [dev_spec_header, dev_spec_body, dev_task_section, tech_req_section] if part
    )

    # 汇总各部分
    sections: List[str] = [
        basic_section,
        glossary_section,
        nav_section,
        app_design_section,
        dev_spec_section,
    ]

    return "\n\n".join(part for part in sections if part)


def _format_error_response(error: Exception, **kwargs: Any) -> str:
    """Format error response as JSON."""
    error_result = {"error": str(error), **kwargs}
    return json.dumps(error_result, indent=2, ensure_ascii=False)


def _format_success_response(data: dict[str, Any]) -> str:
    """Format success response as JSON."""
    return json.dumps(data, indent=2, ensure_ascii=False)


def load_config() -> dict[str, Any]:
    """Load configuration from config.yaml."""
    import yaml
    
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return {}
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        if not config:
            logger.warning("Config file is empty, using defaults")
            return {}
        
        if "api_specs" not in config:
            logger.warning("No 'api_specs' section in config, using defaults")
            config["api_specs"] = {}
        
        return config
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        raise


def setup_server() -> None:
    """Initialize server components with configuration."""
    global openapi_loader, mcp, studio_base_url, server_transport
    
    try:
        config = load_config()
        
        # Get server configuration
        server_config = config.get("server", {})
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 8000)
        # Transport: "http" (legacy SSE) or "streamable-http" (recommended)
        server_transport = server_config.get("transport", "streamable-http")
        
        # Studio internal API base URL (for get_context); env STUDIO_BASE_URL overrides config
        studio_config = config.get("studio", {})
        studio_base_url = (os.environ.get("STUDIO_BASE_URL") or studio_config.get("base_url") or "").rstrip("/")
        
        # Initialize OpenAPI loader
        api_specs_config = config.get("api_specs", {})
        api_specs_base_path = api_specs_config.get("base_path", "./api-specs")
        # Resolve relative to mcp directory
        if not Path(api_specs_base_path).is_absolute():
            api_specs_base_path = str(Path(__file__).parent.parent / api_specs_base_path)
        
        openapi_loader = OpenAPILoader(
            base_path=Path(api_specs_base_path)
        )
        
        # Initialize FastMCP server if available
        if not MCP_AVAILABLE or FastMCP is None:
            logger.error("MCP SDK not available. Please install: pip install mcp")
            logger.error("Server will not be able to start without MCP SDK")
            return
        
        try:
            # Create FastMCP server with HTTP transport support
            # Use stateless_http=True and json_response=True for optimal scalability
            global mcp
            mcp = FastMCP(
                "dip-studio-mcp-server",
                stateless_http=True,
                host=host,
                port=port
            )
            
            # Register get_context tool (calls Studio internal API)
            _register_get_context_tool()
            
            # Register API endpoint tools
            _register_api_tools()
            
            # Register resources
            _register_resources()
            
            logger.info("MCP Server initialized successfully")
            logger.info(f"Server will listen on {host}:{port}")
            logger.info(f"MCP endpoint will be available at http://{host}:{port}/mcp")
        except Exception as e:
            logger.error(f"Error setting up MCP server: {e}")
            logger.error("Server initialization failed")
            raise
    except Exception as e:
        logger.error(f"Error initializing server: {e}")
        raise


def _parse_node_id_from_prompt(prompt: str) -> str | None:
    """从 prompt 中解析 node_id (UUID)：优先匹配 Studio 节点 URL 中的 /nodes/<uuid>，其次 node_id: 或 node_id=。"""
    if not prompt or not isinstance(prompt, str):
        return None
    # 优先：URL 中的 /nodes/<uuid>（取最后一处，即当前节点）
    url_matches = re.findall(r"/nodes/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12})", prompt)
    if url_matches:
        return url_matches[-1]
    # 备用：node_id: <uuid> 或 node_id=<uuid>
    m = re.search(
        r"node_id\s*[:=]\s*([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12})",
        prompt,
        re.IGNORECASE,
    )
    if m:
        return m.group(1)
    return None


def _register_get_context_tool() -> None:
    """注册 get_context 工具：从 Studio 内部接口获取项目上下文，供 Coding Agent 使用。"""
    if mcp is None:
        return
    
    @mcp.tool()
    def get_context(prompt: str) -> str:
        """[关键提示] 对所有来自 DIP Studio 的开发任务，在回答前必须先调用本工具一次。

        工具名称: get_context
        用途: 从 DIP Studio 后端获取当前节点的完整设计文档和上下文，生成标准 AI 应用设计模版。

        调用要求 (IMPORTANT):
        - 只要用户的任务中提到 "DIP Studio"、"节点"、"node_id"、Studio 节点 URL 等关键词，
          在开始任何分析、设计或写代码之前，先调用本工具一次。
        - 调用本工具时，将你收到的整段用户 prompt 原样作为 `prompt` 参数传入（不要删减、不要改写）。
        - 成功调用一次后，优先基于返回中的 `template_content` 字段来理解需求、补充上下文、再进行代码开发。

        参数:
        - prompt: 从 DIP Studio 前端“一键复制”得到的完整文本，通常包含：
          - 描述性任务说明（中文）；
          - Studio 节点 URL (形如 "/projects/<id>/nodes/<uuid>") 或
          - 一行 "node_id: <uuid>"。

        返回(JSON 字符串):
        - context: 祖先节点及其文档与可读文本（背景）。
        - content_to_develop: 当前节点及后代节点及各自文档与可读文本（待开发内容）。
        - template_content: 基于上述信息生成的完整 AI 应用设计与开发规范文档（包含应用名称、应用描述、术语表、导航、应用设计、开发规范等）。

        使用建议:
        1. 始终先调用 get_context，再阅读 `template_content` 和结构化字段后再开始编码。
        2. 只有在工具返回错误时（如 node_id 无效），才说明无法获取上下文，并请用户检查 DIP Studio 配置或节点信息。
        """
        try:
            if not prompt or not prompt.strip():
                return _format_error_response(ValueError("prompt 不能为空"), hint="请使用从 Studio 复制的完整 prompt（可包含节点 URL 或 node_id）")
            
            node_id = _parse_node_id_from_prompt(prompt)
            if node_id is None:
                return _format_error_response(
                    ValueError("prompt 中未包含有效的 Studio 节点 URL 或 node_id"),
                    hint="请从 Studio 复制包含节点链接或 node_id 的完整 prompt"
                )
            
            if not studio_base_url:
                return _format_error_response(
                    RuntimeError("MCP 未配置 studio.base_url，无法请求 Studio"),
                    hint="请在 config.yaml 中配置 studio.base_url"
                )
            
            url = f"{studio_base_url}/internal/api/dip-studio/v1/nodes/{node_id}/application-detail"
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()
            # 在 MCP 侧拼接模版化内容，供 Coding Agent 直接使用（开发任务与技术要求已内嵌于 template_content）
            if isinstance(data, dict):
                data = dict(data)
                try:
                    data["template_content"] = _build_template_content(data)
                except Exception as build_err:
                    # 构建模版内容失败时，仅记录日志，不影响基础上下文返回
                    logger.exception(f"构建 template_content 失败: {build_err}")
            return _format_success_response(data)
        except httpx.HTTPStatusError as e:
            logger.error(f"Studio 请求失败: {e.response.status_code} {e.response.text}")
            return _format_error_response(
                e,
                status_code=e.response.status_code,
                hint="请检查 Studio 服务是否可用及 node_id 是否有效"
            )
        except Exception as e:
            logger.exception(f"get_context 失败: {e}")
            return _format_error_response(e, hint="请检查 prompt 格式及 Studio 配置")
    
    logger.info("Registered tool: get_context")


def _register_api_tools() -> None:
    """Register API endpoint tools."""
    if mcp is None:
        return
    
    @mcp.tool()
    def list_all_api_endpoints() -> str:
        """List all API endpoints from all available OpenAPI specifications with complete details optimized for code generation.
        
        Returns a comprehensive, structured list of all API endpoints designed for AI code generation:
        - Complete API specification metadata (title, version, base URL, authentication)
        - Detailed endpoint information with types, examples, and schemas
        - Request/response schemas with example values
        - Parameter details with types, required flags, and examples
        - Operation IDs for easy function naming
        - Tags for endpoint grouping
        
        This tool provides all information needed for Cursor to generate accurate API integration code.
        """
        try:
            if openapi_loader is None:
                raise RuntimeError("OpenAPI loader not initialized")
            
            # Get all API specifications
            specs = openapi_loader.list_api_specs()
            all_endpoints = []
            
            for spec_info in specs:
                spec_id = spec_info.get("id")
                if "error" in spec_info:
                    logger.warning(f"Skipping spec {spec_id} due to error: {spec_info['error']}")
                    continue
                
                try:
                    # Get API summary and integration info
                    summary = openapi_loader.get_api_summary(spec_id)
                    integration_info = openapi_loader.get_integration_info(spec_id)
                    spec = openapi_loader.load_api_spec(spec_id)
                    paths = spec.get("paths", {})
                    
                    spec_endpoints = []
                    for path, path_item in paths.items():
                        for method_name in ["get", "post", "put", "delete", "patch", "head", "options"]:
                            if method_name in path_item:
                                operation = path_item[method_name]
                                
                                try:
                                    endpoint_details = openapi_loader.get_endpoint_details(
                                        spec_id, path, method_name
                                    )
                                    
                                    # Extract enhanced information for code generation
                                    parameters = endpoint_details.get("parameters", [])
                                    request_body = endpoint_details.get("request_body")
                                    responses = endpoint_details.get("responses", {})
                                    
                                    # Enhance parameters with type information
                                    enhanced_parameters = []
                                    for param in parameters:
                                        param_info = {
                                            "name": param.get("name", ""),
                                            "in": param.get("in", ""),  # query, path, header, cookie
                                            "required": param.get("required", False),
                                            "description": param.get("description", ""),
                                            "schema": param.get("schema", {}),
                                            "type": param.get("schema", {}).get("type", "string"),
                                            "example": param.get("example") or param.get("schema", {}).get("example")
                                        }
                                        enhanced_parameters.append(param_info)
                                    
                                    # Enhance request body with schema
                                    enhanced_request_body = None
                                    if request_body:
                                        content = request_body.get("content", {})
                                        for content_type, content_schema in content.items():
                                            schema = content_schema.get("schema", {})
                                            enhanced_request_body = {
                                                "content_type": content_type,
                                                "schema": schema,
                                                "required": request_body.get("required", False),
                                                "description": request_body.get("description", ""),
                                                "example": content_schema.get("example") or schema.get("example")
                                            }
                                            break
                                    
                                    # Enhance responses with schemas and examples
                                    enhanced_responses = {}
                                    for status_code, response_info in responses.items():
                                        content = response_info.get("content", {})
                                        response_schema = None
                                        response_example = None
                                        for content_type, content_schema in content.items():
                                            schema = content_schema.get("schema", {})
                                            response_schema = schema
                                            response_example = content_schema.get("example") or schema.get("example")
                                            break
                                        
                                        enhanced_responses[status_code] = {
                                            "description": response_info.get("description", ""),
                                            "schema": response_schema,
                                            "example": response_example,
                                            "content_type": list(content.keys())[0] if content else "application/json"
                                        }
                                    
                                    spec_endpoints.append({
                                        "path": endpoint_details.get("path", path),
                                        "method": endpoint_details.get("method", method_name.upper()),
                                        "operation_id": endpoint_details.get("operation_id", operation.get("operationId", "")),
                                        "summary": endpoint_details.get("summary", operation.get("summary", "")),
                                        "description": endpoint_details.get("description", operation.get("description", "")),
                                        "tags": endpoint_details.get("tags", operation.get("tags", [])),
                                        "parameters": enhanced_parameters,
                                        "request_body": enhanced_request_body,
                                        "responses": enhanced_responses,
                                        "security": operation.get("security", []),
                                        "deprecated": operation.get("deprecated", False)
                                    })
                                except Exception as e:
                                    logger.warning(f"Error getting details for {method_name.upper()} {path} in {spec_id}: {e}")
                                    # Fallback to basic info
                                    spec_endpoints.append({
                                        "path": path,
                                        "method": method_name.upper(),
                                        "summary": operation.get("summary", ""),
                                        "description": operation.get("description", ""),
                                        "operation_id": operation.get("operationId", ""),
                                        "tags": operation.get("tags", []),
                                        "error": f"Could not load full details: {str(e)}"
                                    })
                    
                    # Add specification with all its endpoints
                    all_endpoints.append({
                        "spec_id": spec_id,
                        "spec_info": {
                            "title": summary.get("info", {}).get("title", spec_id),
                            "version": summary.get("info", {}).get("version", "unknown"),
                            "openapi_version": spec.get("openapi", "unknown"),
                            "description": summary.get("info", {}).get("description", ""),
                            "base_url": integration_info.get("base_url", ""),
                            "servers": spec.get("servers", []),
                            "security_schemes": integration_info.get("security_schemes", {}),
                            "content_type": integration_info.get("content_type", "application/json"),
                            "authentication": {
                                "type": list(integration_info.get("security_schemes", {}).keys())[0] if integration_info.get("security_schemes") else None,
                                "schemes": integration_info.get("security_schemes", {})
                            }
                        },
                        "statistics": summary.get("statistics", {}),
                        "endpoints": spec_endpoints,
                        "endpoints_count": len(spec_endpoints)
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing spec {spec_id}: {e}")
                    all_endpoints.append({
                        "spec_id": spec_id,
                        "error": str(e),
                        "endpoints": []
                    })
            
            return _format_success_response({
                "total_specs": len(specs),
                "total_endpoints": sum(spec.get("endpoints_count", 0) for spec in all_endpoints),
                "api_specifications": all_endpoints
            })
        except Exception as e:
            logger.error(f"Error listing all API endpoints: {e}")
            return _format_error_response(
                e,
                total_specs=0,
                total_endpoints=0,
                api_specifications=[]
            )
    
    @mcp.tool()
    def get_api_code_example(
        spec_id: str,
        path: str,
        method: str,
        language: str = "typescript"
    ) -> str:
        """Get code example for a specific API endpoint.
        
        Generates ready-to-use code examples for integrating a specific API endpoint.
        This is optimized for AI code generation tools like Cursor.
        
        Args:
            spec_id: The API specification ID
            path: The endpoint path (e.g., "/users/{id}")
            method: HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)
            language: Target programming language (typescript, python, javascript, default: typescript)
        
        Returns:
            Complete code example with imports, configuration, and usage instructions.
        """
        try:
            if openapi_loader is None:
                raise RuntimeError("OpenAPI loader not initialized")
            
            if not spec_id or not path or not method:
                raise ValueError("spec_id, path, and method are required")
            
            # Generate code example
            code_example = openapi_loader.generate_endpoint_example(
                spec_id=spec_id,
                path=path,
                method=method,
                language=language
            )
            
            # Get additional context for better code generation
            endpoint_details = openapi_loader.get_endpoint_details(spec_id, path, method)
            integration_info = openapi_loader.get_integration_info(spec_id)
            
            return _format_success_response({
                "spec_id": spec_id,
                "endpoint": {
                    "path": path,
                    "method": method.upper(),
                    "operation_id": endpoint_details.get("operation_id", ""),
                    "summary": endpoint_details.get("summary", "")
                },
                "language": language,
                "code_example": code_example,
                "integration_info": {
                    "base_url": integration_info.get("base_url", ""),
                    "authentication": integration_info.get("security_schemes", {}),
                    "content_type": integration_info.get("content_type", "application/json")
                },
                "usage_notes": {
                    "description": "This code example is ready to use. Replace placeholder values with actual data.",
                    "authentication": "Make sure to configure authentication as shown in the integration_info section."
                }
            })
        except Exception as e:
            logger.error(f"Error generating code example: {e}")
            return _format_error_response(
                e,
                spec_id=spec_id,
                path=path,
                method=method,
                language=language
            )
    
    logger.info("Registered API tools: list_all_api_endpoints, get_api_code_example")


def _register_resources() -> None:
    """Register MCP resources."""
    if mcp is None:
        return
    @mcp.resource("api-spec://{spec_id}")
    def get_api_spec_resource(spec_id: str) -> str:
        """Get OpenAPI specification document resource."""
        try:
            if openapi_loader is None:
                raise RuntimeError("OpenAPI loader not initialized")
            spec = openapi_loader.load_api_spec(spec_id)
            return _format_success_response(spec)
        except Exception as e:
            logger.error(f"Error reading resource api-spec://{spec_id}: {e}")
            return _format_error_response(e, spec_id=spec_id)
    
    @mcp.resource("api-spec://{spec_id}/summary")
    def get_api_spec_summary_resource(spec_id: str) -> str:
        """Get OpenAPI specification summary resource."""
        try:
            if openapi_loader is None:
                raise RuntimeError("OpenAPI loader not initialized")
            summary = openapi_loader.get_api_summary(spec_id)
            return _format_success_response(summary)
        except Exception as e:
            logger.error(f"Error reading resource api-spec://{spec_id}/summary: {e}")
            return _format_error_response(e, spec_id=spec_id)
    
    @mcp.resource("api-integration://{spec_id}/{language}")
    def get_api_integration_resource(spec_id: str, language: str) -> str:
        """Get API integration guide resource for a specific language."""
        try:
            if openapi_loader is None:
                raise RuntimeError("OpenAPI loader not initialized")
            guide = openapi_loader.generate_integration_guide(spec_id, language)
            return _format_success_response({
                "spec_id": spec_id,
                "language": language,
                "guide": guide
            })
        except Exception as e:
            logger.error(f"Error reading resource api-integration://{spec_id}/{language}: {e}")
            return _format_error_response(e, spec_id=spec_id, language=language)
    
    @mcp.resource("api-example://{spec_id}")
    def get_api_example_resource(spec_id: str) -> str:
        """Get API endpoint code example resource.
        
        Returns a list of available endpoints for the specification.
        """
        try:
            if openapi_loader is None:
                raise RuntimeError("OpenAPI loader not initialized")
            
            summary = openapi_loader.get_api_summary(spec_id)
            endpoints = summary.get("endpoints", [])[:20]
            return _format_success_response({
                "spec_id": spec_id,
                "available_endpoints": [
                    {
                        "path": ep["path"],
                        "method": ep["method"],
                        "summary": ep["summary"]
                    }
                    for ep in endpoints
                ],
                "total_endpoints": summary.get("statistics", {}).get("endpoints_count", 0)
            })
        except Exception as e:
            logger.error(f"Error reading resource api-example://{spec_id}: {e}")
            return _format_error_response(e, spec_id=spec_id)
    
    logger.info("Registered resources: api-spec, api-integration, api-example")


def main() -> None:
    """Main entry point for the MCP server."""
    setup_server()
    
    if not MCP_AVAILABLE or mcp is None:
        logger.error("MCP SDK not available. Please install: pip install mcp")
        logger.error("Alternatively, install from: pip install git+https://github.com/modelcontextprotocol/python-sdk.git")
        return
    
    # Run the server with configured transport
    transport = server_transport or "streamable-http"
    logger.info(f"Starting DIP Studio MCP Server (transport={transport})...")
    try:
        mcp.run(transport=transport)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise


if __name__ == "__main__":
    main()
