"""MCP Server main entry point for DIP Studio."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

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
    global openapi_loader, mcp, studio_base_url
    
    try:
        config = load_config()
        
        # Get server configuration
        server_config = config.get("server", {})
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 8000)
        
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


def _parse_node_id_from_prompt(prompt: str) -> int | None:
    """从 prompt 中解析 node_id：优先匹配 Studio 节点 URL 中的 /nodes/<id>，其次 node_id: 或 node_id=。"""
    if not prompt or not isinstance(prompt, str):
        return None
    # 优先：URL 中的 /nodes/数字（取最后一处，即当前节点）
    matches = re.findall(r"/nodes/(\d+)", prompt)
    if matches:
        return int(matches[-1])
    # 备用：node_id: 123 或 node_id=123
    m = re.search(r"node_id\s*[:=]\s*(\d+)", prompt, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def _register_get_context_tool() -> None:
    """注册 get_context 工具：从 Studio 内部接口获取项目上下文，供 Coding Agent 使用。"""
    if mcp is None:
        return
    
    @mcp.tool()
    def get_context(prompt: str) -> str:
        """Get full project context from DIP Studio for the Coding Agent. You MUST call this tool with the exact prompt string that the user obtained from DIP Studio (e.g. copy prompt for Coding Agent). The prompt may contain (1) a Studio node URL containing \"/nodes/<id>\" (e.g. .../projects/1/nodes/42), or (2) a line \"node_id: <id>\". This tool parses the node_id, fetches from Studio: context (ancestor nodes and documents as background) and content_to_develop (target node and descendants with document_text). Use the returned JSON to write or update code. Input: prompt (string, may be in Chinese). Output: JSON with \"context\" and \"content_to_develop\", each a list of { \"node\", \"document\", \"document_text\" }."""
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
            
            import httpx
            url = f"{studio_base_url}/internal/api/dip-studio/v1/nodes/{node_id}/application-detail"
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()
            # 在 MCP 侧拼接开发任务与技术要求，供 Coding Agent 直接使用
            if isinstance(data, dict):
                data = dict(data)
                data["development_task"] = DEVELOPMENT_TASK
                data["technical_requirements"] = TECHNICAL_REQUIREMENTS
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
    
    # Run the server with streamable-http transport
    logger.info("Starting DIP Studio MCP Server (HTTP transport)...")
    try:
        mcp.run(transport="streamable-http")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise


if __name__ == "__main__":
    main()
