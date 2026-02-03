"""OpenAPI specification loader and parser for API documentation."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

logger = logging.getLogger(__name__)


class OpenAPILoader:
    """Load and parse OpenAPI 3.0.2 specification files."""
    
    def __init__(
        self,
        base_path: Path,
    ) -> None:
        """
        Initialize OpenAPI loader.
        
        Args:
            base_path: Base directory containing OpenAPI specification files
        """
        self.base_path = Path(base_path).resolve()
        
        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Cache for loaded specifications
        self._spec_cache: dict[str, dict[str, Any]] = {}
        self._summary_cache: dict[str, dict[str, Any]] = {}
    
    def list_api_specs(self) -> list[dict[str, Any]]:
        """
        List all available OpenAPI specification files.
        
        Supports both JSON (.json) and YAML (.yaml, .yml) formats.
        
        Returns:
            List of specification metadata dictionaries
        """
        specs = []
        
        if not self.base_path.exists():
            logger.warning(f"Base path does not exist: {self.base_path}")
            return specs
        
        # Supported file extensions
        supported_extensions = {".json"}
        if YAML_AVAILABLE:
            supported_extensions.update({".yaml", ".yml"})
        
        for file_path in self.base_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                spec_id = file_path.stem
                try:
                    # Load basic info without full parsing
                    with open(file_path, "r", encoding="utf-8") as f:
                        if file_path.suffix.lower() == ".json":
                            data = json.load(f)
                        elif file_path.suffix.lower() in {".yaml", ".yml"}:
                            if not YAML_AVAILABLE:
                                raise ImportError("PyYAML is required to load YAML files. Install with: pip install PyYAML")
                            data = yaml.safe_load(f)
                        else:
                            continue
                    
                    info = data.get("info", {})
                    specs.append({
                        "id": spec_id,
                        "filename": file_path.name,
                        "path": str(file_path),
                        "title": info.get("title", spec_id),
                        "version": info.get("version", "unknown"),
                        "openapi_version": data.get("openapi", "unknown"),
                        "paths_count": len(data.get("paths", {}))
                    })
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"Error reading spec {spec_id}: {e}")
                    specs.append({
                        "id": spec_id,
                        "filename": file_path.name,
                        "path": str(file_path),
                        "error": str(e)
                    })
        
        return specs
    
    def load_api_spec(self, spec_id: str) -> dict[str, Any]:
        """
        Load a complete OpenAPI specification by ID.
        
        Supports both JSON and YAML formats.
        
        Args:
            spec_id: Specification identifier (filename without extension)
        
        Returns:
            Complete OpenAPI specification dictionary
        """
        # Check cache first
        if spec_id in self._spec_cache:
            return self._spec_cache[spec_id]
        
        # Find the specification file
        spec_file = self._find_spec_file(spec_id)
        if not spec_file:
            raise FileNotFoundError(f"OpenAPI specification not found: {spec_id}")
        
        # Load and parse based on file extension
        try:
            with open(spec_file, "r", encoding="utf-8") as f:
                file_ext = spec_file.suffix.lower()
                if file_ext == ".json":
                    spec = json.load(f)
                elif file_ext in {".yaml", ".yml"}:
                    if not YAML_AVAILABLE:
                        raise ImportError("PyYAML is required to load YAML files. Install with: pip install PyYAML")
                    spec = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Validate it's an OpenAPI spec
            if "openapi" not in spec:
                raise ValueError(f"File {spec_id} is not a valid OpenAPI specification")
            
            # Cache the spec
            self._spec_cache[spec_id] = spec
            
            return spec
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in specification {spec_id}: {e}")
    
    def get_api_summary(self, spec_id: str) -> dict[str, Any]:
        """
        Get a summary of an OpenAPI specification.
        
        Args:
            spec_id: Specification identifier
        
        Returns:
            Summary dictionary with key information
        """
        # Check cache first
        if spec_id in self._summary_cache:
            return self._summary_cache[spec_id]
        
        # Load the full spec
        spec = self.load_api_spec(spec_id)
        
        # Extract summary information
        info = spec.get("info", {})
        paths = spec.get("paths", {})
        components = spec.get("components", {})
        schemas = components.get("schemas", {})
        
        # Build endpoint list
        endpoints = []
        for path, path_item in paths.items():
            for method in ["get", "post", "put", "delete", "patch", "head", "options"]:
                if method in path_item:
                    operation = path_item[method]
                    endpoints.append({
                        "path": path,
                        "method": method.upper(),
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "operation_id": operation.get("operationId", ""),
                        "tags": operation.get("tags", []),
                        "parameters_count": len(operation.get("parameters", [])),
                        "has_request_body": "requestBody" in operation,
                        "responses": list(operation.get("responses", {}).keys())
                    })
        
        summary = {
            "id": spec_id,
            "info": {
                "title": info.get("title", ""),
                "version": info.get("version", ""),
                "description": info.get("description", ""),
                "openapi_version": spec.get("openapi", "")
            },
            "statistics": {
                "paths_count": len(paths),
                "endpoints_count": len(endpoints),
                "schemas_count": len(schemas),
                "tags": self._extract_tags(paths)
            },
            "endpoints": endpoints,
            "schemas": list(schemas.keys())[:50]  # Limit to first 50 schema names
        }
        
        # Cache the summary
        self._summary_cache[spec_id] = summary
        
        return summary
    
    def get_endpoint_details(
        self,
        spec_id: str,
        path: str,
        method: str | None = None
    ) -> dict[str, Any]:
        """
        Get detailed information about a specific endpoint.
        
        Args:
            spec_id: Specification identifier
            path: Endpoint path
            method: HTTP method (optional, if not provided returns all methods for the path)
        
        Returns:
            Detailed endpoint information
        """
        spec = self.load_api_spec(spec_id)
        paths = spec.get("paths", {})
        
        if path not in paths:
            raise ValueError(f"Path '{path}' not found in specification {spec_id}")
        
        path_item = paths[path]
        
        # If method is specified, return only that method
        if method:
            method_lower = method.lower()
            if method_lower not in path_item:
                raise ValueError(
                    f"Method '{method.upper()}' not found for path '{path}' "
                    f"in specification {spec_id}"
                )
            
            return self._extract_operation_details(
                spec, path, method_lower, path_item[method_lower]
            )
        
        # Otherwise, return all methods for this path
        operations = {}
        for method_name in ["get", "post", "put", "delete", "patch", "head", "options"]:
            if method_name in path_item:
                operations[method_name.upper()] = self._extract_operation_details(
                    spec, path, method_name, path_item[method_name]
                )
        
        # Include path-level parameters
        path_parameters = path_item.get("parameters", [])
        
        return {
            "path": path,
            "parameters": path_parameters,
            "operations": operations
        }
    
    def _find_spec_file(self, spec_id: str) -> Path | None:
        """Find specification file by ID.
        
        Searches for files with extensions: .json, .yaml, .yml (in that order).
        
        Args:
            spec_id: Specification identifier (filename without extension)
        
        Returns:
            Path to the specification file, or None if not found
        """
        # Try JSON first
        spec_path = self.base_path / f"{spec_id}.json"
        if spec_path.exists():
            return spec_path
        
        # Try YAML formats if available
        if YAML_AVAILABLE:
            for ext in [".yaml", ".yml"]:
                spec_path = self.base_path / f"{spec_id}{ext}"
                if spec_path.exists():
                    return spec_path
        
        return None
    
    def _extract_tags(self, paths: dict[str, Any]) -> list[str]:
        """Extract unique tags from all operations."""
        tags = set()
        for path_item in paths.values():
            for method in ["get", "post", "put", "delete", "patch", "head", "options"]:
                if method in path_item:
                    operation_tags = path_item[method].get("tags", [])
                    tags.update(operation_tags)
        
        return sorted(list(tags))
    
    def _extract_operation_details(
        self,
        spec: dict[str, Any],
        path: str,
        method: str,
        operation: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract detailed information from an operation."""
        components = spec.get("components", {})
        schemas = components.get("schemas", {})
        
        # Extract request body schema
        request_body = None
        if "requestBody" in operation:
            rb = operation["requestBody"]
            content = rb.get("content", {})
            if content:
                # Get first content type
                content_type = list(content.keys())[0]
                schema_ref = content[content_type].get("schema", {})
                request_body = {
                    "content_type": content_type,
                    "required": rb.get("required", False),
                    "schema": self._resolve_schema_ref(spec, schema_ref),
                    "examples": content[content_type].get("examples", {})
                }
        
        # Extract response schemas
        responses = {}
        for status_code, response in operation.get("responses", {}).items():
            content = response.get("content", {})
            response_schema = None
            if content:
                content_type = list(content.keys())[0]
                schema_ref = content[content_type].get("schema", {})
                response_schema = self._resolve_schema_ref(spec, schema_ref)
            
            responses[status_code] = {
                "description": response.get("description", ""),
                "content_type": list(content.keys())[0] if content else None,
                "schema": response_schema,
                "examples": content.get(list(content.keys())[0], {}).get("examples", {}) if content else {}
            }
        
        return {
            "path": path,
            "method": method.upper(),
            "summary": operation.get("summary", ""),
            "description": operation.get("description", ""),
            "operation_id": operation.get("operationId", ""),
            "tags": operation.get("tags", []),
            "parameters": operation.get("parameters", []),
            "request_body": request_body,
            "responses": responses,
            "security": operation.get("security", []),
            "deprecated": operation.get("deprecated", False)
        }
    
    def _resolve_schema_ref(
        self,
        spec: dict[str, Any],
        schema: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve $ref references in schema."""
        if "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path.startswith("#/components/schemas/"):
                schema_name = ref_path.split("/")[-1]
                components = spec.get("components", {})
                schemas = components.get("schemas", {})
                if schema_name in schemas:
                    return schemas[schema_name]
        
        return schema
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        self._spec_cache.clear()
        self._summary_cache.clear()
    
    def get_integration_info(self, spec_id: str) -> dict[str, Any]:
        """
        Extract integration information from an OpenAPI specification.
        
        Args:
            spec_id: Specification identifier
        
        Returns:
            Dictionary with integration information (base URL, auth, headers, etc.)
        """
        spec = self.load_api_spec(spec_id)
        info = spec.get("info", {})
        servers = spec.get("servers", [])
        security = spec.get("security", [])
        components = spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        
        # Extract base URL from paths if servers not specified
        base_url = None
        if servers:
            base_url = servers[0].get("url", "")
        else:
            # Infer from paths
            paths = spec.get("paths", {})
            if paths:
                first_path = list(paths.keys())[0]
                # Extract base path (e.g., /api/ontology-manager/v1)
                parts = first_path.split("/")
                if len(parts) >= 4:
                    base_url = "/" + "/".join(parts[:4])
        
        # Extract authentication info
        auth_info = {}
        if security_schemes:
            for scheme_name, scheme_def in security_schemes.items():
                auth_type = scheme_def.get("type", "")
                auth_info[scheme_name] = {
                    "type": auth_type,
                    "scheme": scheme_def.get("scheme", ""),
                    "bearerFormat": scheme_def.get("bearerFormat", ""),
                    "description": scheme_def.get("description", "")
                }
        
        return {
            "spec_id": spec_id,
            "title": info.get("title", ""),
            "version": info.get("version", ""),
            "base_url": base_url or "https://api.example.com",
            "servers": servers,
            "security_schemes": auth_info,
            "default_security": security,
            "content_type": "application/json"
        }
    
    def generate_integration_guide(
        self,
        spec_id: str,
        language: str = "typescript"
    ) -> str:
        """
        Generate integration guide for a specific language.
        
        Args:
            spec_id: Specification identifier
            language: Target language (typescript, python, javascript)
        
        Returns:
            Integration guide as formatted string
        """
        spec = self.load_api_spec(spec_id)
        integration_info = self.get_integration_info(spec_id)
        info = spec.get("info", {})
        paths = spec.get("paths", {})
        
        # Extract endpoint examples
        endpoint_examples = []
        for path, path_item in list(paths.items())[:5]:  # Limit to first 5 endpoints
            for method in ["get", "post", "put", "delete"]:
                if method in path_item:
                    operation = path_item[method]
                    endpoint_examples.append({
                        "path": path,
                        "method": method.upper(),
                        "summary": operation.get("summary", ""),
                        "operation_id": operation.get("operationId", "")
                    })
                    break
        
        if language.lower() == "typescript":
            return self._generate_typescript_guide(integration_info, info, endpoint_examples)
        elif language.lower() == "python":
            return self._generate_python_guide(integration_info, info, endpoint_examples)
        elif language.lower() == "javascript":
            return self._generate_javascript_guide(integration_info, info, endpoint_examples)
        else:
            return self._generate_generic_guide(integration_info, info, endpoint_examples)
    
    def generate_endpoint_example(
        self,
        spec_id: str,
        path: str,
        method: str,
        language: str = "typescript"
    ) -> str:
        """
        Generate integration code example for a specific endpoint.
        
        Args:
            spec_id: Specification identifier
            path: Endpoint path
            method: HTTP method
            language: Target language
        
        Returns:
            Code example as formatted string
        """
        spec = self.load_api_spec(spec_id)
        integration_info = self.get_integration_info(spec_id)
        endpoint_details = self.get_endpoint_details(spec_id, path, method)
        
        if language.lower() == "typescript":
            return self._generate_typescript_example(integration_info, endpoint_details)
        elif language.lower() == "python":
            return self._generate_python_example(integration_info, endpoint_details)
        elif language.lower() == "javascript":
            return self._generate_javascript_example(integration_info, endpoint_details)
        else:
            return self._generate_generic_example(integration_info, endpoint_details)
    
    def _generate_typescript_guide(
        self,
        integration_info: dict[str, Any],
        info: dict[str, Any],
        endpoint_examples: list[dict[str, Any]]
    ) -> str:
        """Generate TypeScript integration guide."""
        base_url = integration_info.get("base_url", "https://api.example.com")
        title = integration_info.get("title", "")
        
        guide = f"""# {title} - TypeScript Integration Guide

## Overview
This guide helps you integrate the {title} API into your TypeScript/JavaScript application.

## Base Configuration

### Base URL
```typescript
const BASE_URL = '{base_url}';
```

### HTTP Client Setup
```typescript
// Using fetch (built-in)
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {{}}
): Promise<T> {{
  const url = `${{BASE_URL}}${{endpoint}}`;
  const response = await fetch(url, {{
    ...options,
    headers: {{
      'Content-Type': 'application/json',
      ...options.headers,
    }},
  }});
  
  if (!response.ok) {{
    throw new Error(`API request failed: ${{response.status}} ${{response.statusText}}`);
  }}
  
  return response.json();
}}
```

### Using Axios (Alternative)
```typescript
import axios from 'axios';

const apiClient = axios.create({{
  baseURL: '{base_url}',
  headers: {{
    'Content-Type': 'application/json',
  }},
}});

// Add request interceptor for authentication if needed
apiClient.interceptors.request.use((config) => {{
  // Add auth token here if required
  // config.headers.Authorization = 'Bearer ' + token;
  return config;
}});
```

## Example Endpoints

"""
        for example in endpoint_examples:
            guide += f"""### {example['method']} {example['path']}
```typescript
// {example['summary']}
const result = await apiRequest<ResponseType>(
  '{example['path']}',
  {{
    method: '{example['method']}',
  }}
);
```

"""
        
        guide += """## Error Handling
```typescript
try {{
  const data = await apiRequest('/api/endpoint');
  console.log(data);
}} catch (error) {{
  if (error instanceof Error) {{
    console.error('API Error:', error.message);
  }}
}}
```

## Type Definitions
Consider generating TypeScript types from the OpenAPI schema using tools like:
- `openapi-typescript` (https://github.com/drwpow/openapi-typescript)
- `swagger-typescript-api` (https://github.com/acacode/swagger-typescript-api)
"""
        return guide
    
    def _generate_python_guide(
        self,
        integration_info: dict[str, Any],
        info: dict[str, Any],
        endpoint_examples: list[dict[str, Any]]
    ) -> str:
        """Generate Python integration guide."""
        base_url = integration_info.get("base_url", "https://api.example.com")
        title = integration_info.get("title", "")
        
        guide = f"""# {title} - Python Integration Guide

## Overview
This guide helps you integrate the {title} API into your Python application.

## Installation
```bash
pip install requests
```

## Base Configuration

### Base URL
```python
BASE_URL = '{base_url}'
```

### HTTP Client Setup
```python
import requests
from typing import Any, Dict, Optional

class APIClient:
    def __init__(self, base_url: str = BASE_URL, api_key: Optional[str] = None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({{
            'Content-Type': 'application/json',
        }})
        if api_key:
            self.session.headers.update({{
                'Authorization': f'Bearer {{api_key}}'
            }})
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = f'{{self.base_url}}{{endpoint}}'
        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json_data
        )
        response.raise_for_status()
        return response.json()

# Usage
client = APIClient()
```

## Example Endpoints

"""
        for example in endpoint_examples:
            guide += f"""### {example['method']} {example['path']}
```python
# {example['summary']}
result = client.request(
    method='{example['method']}',
    endpoint='{example['path']}'
)
print(result)
```

"""
        
        guide += """## Error Handling
```python
try:
    data = client.request('GET', '/api/endpoint')
    print(data)
except requests.exceptions.HTTPError as e:
    print(f'HTTP Error: {e}')
except requests.exceptions.RequestException as e:
    print(f'Request Error: {e}')
```

## Type Hints
Consider using `dataclasses` or `pydantic` models for request/response types.
"""
        return guide
    
    def _generate_javascript_guide(
        self,
        integration_info: dict[str, Any],
        info: dict[str, Any],
        endpoint_examples: list[dict[str, Any]]
    ) -> str:
        """Generate JavaScript integration guide."""
        base_url = integration_info.get("base_url", "https://api.example.com")
        title = integration_info.get("title", "")
        
        guide = f"""# {title} - JavaScript Integration Guide

## Overview
This guide helps you integrate the {title} API into your JavaScript application.

## Base Configuration

### Base URL
```javascript
const BASE_URL = '{base_url}';
```

### HTTP Client Setup
```javascript
// Using fetch (built-in)
async function apiRequest(endpoint, options = {{}}) {{
  const url = `${{BASE_URL}}${{endpoint}}`;
  const response = await fetch(url, {{
    ...options,
    headers: {{
      'Content-Type': 'application/json',
      ...options.headers,
    }},
  }});
  
  if (!response.ok) {{
    throw new Error(`API request failed: ${{response.status}} ${{response.statusText}}`);
  }}
  
  return response.json();
}}
```

### Using Axios (Alternative)
```javascript
import axios from 'axios';

const apiClient = axios.create({{
  baseURL: '{base_url}',
  headers: {{
    'Content-Type': 'application/json',
  }},
}});
```

## Example Endpoints

"""
        for example in endpoint_examples:
            guide += f"""### {example['method']} {example['path']}
```javascript
// {example['summary']}
const result = await apiRequest('{example['path']}', {{
  method: '{example['method']}',
}});
console.log(result);
```

"""
        
        guide += """## Error Handling
```javascript
try {{
  const data = await apiRequest('/api/endpoint');
  console.log(data);
}} catch (error) {{
  console.error('API Error:', error.message);
}}
```
"""
        return guide
    
    def _generate_generic_guide(
        self,
        integration_info: dict[str, Any],
        info: dict[str, Any],
        endpoint_examples: list[dict[str, Any]]
    ) -> str:
        """Generate generic integration guide."""
        base_url = integration_info.get("base_url", "https://api.example.com")
        title = integration_info.get("title", "")
        security_schemes_json = json.dumps(integration_info.get("security_schemes", {}), indent=2)
        
        guide = f"""# {title} - Integration Guide

## Base URL
{base_url}

## Authentication
{security_schemes_json}

## Example Endpoints

"""
        for example in endpoint_examples:
            guide += f"""### {example['method']} {example['path']}
{example['summary']}

"""
        return guide
    
    def _generate_typescript_example(
        self,
        integration_info: dict[str, Any],
        endpoint_details: dict[str, Any]
    ) -> str:
        """Generate TypeScript code example for an endpoint."""
        base_url = integration_info.get("base_url", "https://api.example.com")
        path = endpoint_details.get("path", "")
        method = endpoint_details.get("method", "GET")
        summary = endpoint_details.get("summary", "")
        parameters = endpoint_details.get("parameters", [])
        request_body = endpoint_details.get("request_body")
        
        # Build function signature
        path_params = [p for p in parameters if p.get("in") == "path"]
        query_params = [p for p in parameters if p.get("in") == "query"]
        
        example = f"""// {summary}
// {method} {path}

"""
        
        # Build function parameters
        func_params = []
        if path_params:
            for param in path_params:
                param_name = param.get("name", "")
                param_type = self._get_typescript_type(param.get("schema", {}))
                func_params.append(f"{param_name}: {param_type}")
        
        if query_params:
            query_type = "{" + ", ".join([
                f"{p.get('name', '')}?: {self._get_typescript_type(p.get('schema', {}))}"
                for p in query_params
            ]) + "}"
            func_params.append(f"queryParams?: {query_type}")
        
        if request_body:
            func_params.append("body?: any")
        
        # Build URL
        url_path = path
        if path_params:
            for param in path_params:
                param_name = param.get("name", "")
                url_path = url_path.replace(f"{{{param_name}}}", f"${{{param_name}}}")
        
        example += f"""async function callEndpoint({', '.join(func_params) if func_params else ''}) {{
  const url = `${{BASE_URL}}{url_path}`;
  
"""
        
        # Build request options
        if query_params:
            example += "  const searchParams = new URLSearchParams();\n"
            for param in query_params:
                param_name = param.get("name", "")
                example += f"  if (queryParams?.{param_name}) {{\n"
                example += f"    searchParams.append('{param_name}', String(queryParams.{param_name}));\n"
                example += "  }\n"
            example += "  const queryString = searchParams.toString();\n"
            example += "  const fullUrl = queryString ? `${url}?${queryString}` : url;\n\n"
            url_var = "fullUrl"
        else:
            url_var = "url"
        
        request_options = {
            "method": f"'{method}'",
            "headers": "{ 'Content-Type': 'application/json' }"
        }
        
        if request_body:
            request_options["body"] = "JSON.stringify(body)"
        
        example += f"""  const response = await fetch(${{url_var}}, {{
    method: '{method}',
    headers: {{
      'Content-Type': 'application/json',
    }},
"""
        if request_body:
            example += "    body: JSON.stringify(body),\n"
        example += "  });\n\n"
        example += """  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
}

// Usage example:
"""
        
        # Generate usage example
        usage_params = []
        if path_params:
            for param in path_params:
                param_name = param.get("name", "")
                usage_params.append(f"{param_name}: 'example-value'")
        
        if query_params:
            usage_params.append("queryParams: { /* your query params */ }")
        
        if request_body:
            usage_params.append("body: { /* your request body */ }")
        
        if usage_params:
            example += f"const result = await callEndpoint({{\n"
            for param in usage_params:
                example += f"  {param},\n"
            example += "});\n"
        else:
            example += "const result = await callEndpoint();\n"
        
        example += "console.log(result);\n"
        
        return example
    
    def _generate_python_example(
        self,
        integration_info: dict[str, Any],
        endpoint_details: dict[str, Any]
    ) -> str:
        """Generate Python code example for an endpoint."""
        base_url = integration_info.get("base_url", "https://api.example.com")
        path = endpoint_details.get("path", "")
        method = endpoint_details.get("method", "GET")
        summary = endpoint_details.get("summary", "")
        parameters = endpoint_details.get("parameters", [])
        request_body = endpoint_details.get("request_body")
        
        path_params = [p for p in parameters if p.get("in") == "path"]
        query_params = [p for p in parameters if p.get("in") == "query"]
        
        example = f"""# {summary}
# {method} {path}

import requests

BASE_URL = '{base_url}'

def call_endpoint(
"""
        
        # Build function parameters
        func_params = []
        if path_params:
            for param in path_params:
                param_name = param.get("name", "")
                func_params.append(f"    {param_name}: str")
        
        if query_params:
            func_params.append("    query_params: dict = None")
        
        if request_body:
            func_params.append("    body: dict = None")
        
        if func_params:
            example += ",\n".join(func_params) + "\n"
        example += ") -> dict:\n"
        
        # Build URL
        url_path = path
        if path_params:
            for param in path_params:
                param_name = param.get("name", "")
                url_path = url_path.replace(f"{{{param_name}}}", f"{{{param_name}}}")
        
        example += f'    url = f"{{BASE_URL}}{url_path}"\n\n'
        
        if query_params:
            example += "    params = query_params or {}\n\n"
        
        if request_body:
            example += "    json_data = body\n\n"
        
        example += "    response = requests.request(\n"
        example += f"        method='{method}',\n"
        example += "        url=url,\n"
        if query_params:
            example += "        params=params,\n"
        if request_body:
            example += "        json=json_data,\n"
        example += "        headers={'Content-Type': 'application/json'}\n"
        example += "    )\n\n"
        example += "    response.raise_for_status()\n"
        example += "    return response.json()\n\n"
        example += "# Usage example:\n"
        
        # Generate usage example
        usage_params = []
        if path_params:
            for param in path_params:
                param_name = param.get("name", "")
                usage_params.append(f"{param_name}='example-value'")
        
        if query_params:
            usage_params.append("query_params={ /* your query params */ }")
        
        if request_body:
            usage_params.append("body={ /* your request body */ }")
        
        if usage_params:
            example += f"result = call_endpoint(\n"
            for param in usage_params:
                example += f"    {param},\n"
            example += ")\n"
        else:
            example += "result = call_endpoint()\n"
        
        example += "print(result)\n"
        
        return example
    
    def _generate_javascript_example(
        self,
        integration_info: dict[str, Any],
        endpoint_details: dict[str, Any]
    ) -> str:
        """Generate JavaScript code example for an endpoint."""
        base_url = integration_info.get("base_url", "https://api.example.com")
        path = endpoint_details.get("path", "")
        method = endpoint_details.get("method", "GET")
        summary = endpoint_details.get("summary", "")
        parameters = endpoint_details.get("parameters", [])
        request_body = endpoint_details.get("request_body")
        
        path_params = [p for p in parameters if p.get("in") == "path"]
        query_params = [p for p in parameters if p.get("in") == "query"]
        
        example = f"""// {summary}
// {method} {path}

const BASE_URL = '{base_url}';

async function callEndpoint(
"""
        
        # Build function parameters
        func_params = []
        if path_params:
            for param in path_params:
                param_name = param.get("name", "")
                func_params.append(f"  {param_name}")
        
        if query_params:
            func_params.append("  queryParams = {}")
        
        if request_body:
            func_params.append("  body = null")
        
        if func_params:
            example += ",\n".join(func_params) + "\n"
        example += ") {\n"
        
        # Build URL
        url_path = path
        if path_params:
            for param in path_params:
                param_name = param.get("name", "")
                url_path = url_path.replace(f"{{{param_name}}}", f"${{{param_name}}}")
        
        example += f'  const url = `${{BASE_URL}}{url_path}`;\n\n'
        
        if query_params:
            example += "  const searchParams = new URLSearchParams();\n"
            example += "  Object.entries(queryParams).forEach(([key, value]) => {\n"
            example += "    if (value !== undefined && value !== null) {\n"
            example += "      searchParams.append(key, String(value));\n"
            example += "    }\n"
            example += "  });\n"
            example += "  const queryString = searchParams.toString();\n"
            example += "  const fullUrl = queryString ? `${url}?${queryString}` : url;\n\n"
            url_var = "fullUrl"
        else:
            url_var = "url"
        
        example += f"  const response = await fetch(${{url_var}}, {{\n"
        example += f"    method: '{method}',\n"
        example += "    headers: {\n"
        example += "      'Content-Type': 'application/json',\n"
        example += "    },\n"
        if request_body:
            example += "    body: JSON.stringify(body),\n"
        example += "  });\n\n"
        example += "  if (!response.ok) {\n"
        example += "    throw new Error(`Request failed: ${response.status} ${response.statusText}`);\n"
        example += "  }\n\n"
        example += "  return response.json();\n"
        example += "}\n\n"
        example += "// Usage example:\n"
        
        # Generate usage example
        usage_params = []
        if path_params:
            for param in path_params:
                param_name = param.get("name", "")
                usage_params.append(f"{param_name}: 'example-value'")
        
        if query_params:
            usage_params.append("queryParams: { /* your query params */ }")
        
        if request_body:
            usage_params.append("body: { /* your request body */ }")
        
        if usage_params:
            example += "const result = await callEndpoint({\n"
            for param in usage_params:
                example += f"  {param},\n"
            example += "});\n"
        else:
            example += "const result = await callEndpoint();\n"
        
        example += "console.log(result);\n"
        
        return example
    
    def _generate_generic_example(
        self,
        integration_info: dict[str, Any],
        endpoint_details: dict[str, Any]
    ) -> str:
        """Generate generic code example for an endpoint."""
        base_url = integration_info.get("base_url", "https://api.example.com")
        path = endpoint_details.get("path", "")
        method = endpoint_details.get("method", "GET")
        summary = endpoint_details.get("summary", "")
        
        example = f"""# {summary}
# {method} {path}

Base URL: {base_url}
Endpoint: {path}
Method: {method}

Parameters:
{json.dumps(endpoint_details.get("parameters", []), indent=2)}

Request Body:
{json.dumps(endpoint_details.get("request_body"), indent=2) if endpoint_details.get("request_body") else "None"}

Responses:
{json.dumps(endpoint_details.get("responses", {}), indent=2)}
"""
        return example
    
    def _get_typescript_type(self, schema: dict[str, Any]) -> str:
        """Convert OpenAPI schema to TypeScript type."""
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            return ref_name
        elif "type" in schema:
            schema_type = schema["type"]
            if schema_type == "string":
                return "string"
            elif schema_type == "integer" or schema_type == "number":
                return "number"
            elif schema_type == "boolean":
                return "boolean"
            elif schema_type == "array":
                items = schema.get("items", {})
                item_type = self._get_typescript_type(items)
                return f"{item_type}[]"
            elif schema_type == "object":
                return "Record<string, any>"
        return "any"
