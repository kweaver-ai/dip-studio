# Coding Agent Prompt 示例（中文）

从 DIP Studio 获取 prompt 后，将整段提供给 Coding Agent；Coding Agent 需根据 prompt **必调** `get_context` 工具，再根据返回的上下文编写或修改代码。

## 示例一（含 Studio 节点 URL，推荐）

```
请根据以下 DIP Studio 节点获取项目上下文并完成开发任务。

Studio 节点 URL：https://studio.example.com/dip-studio/projects/1/nodes/42

请先调用 get_context 工具，将本段 prompt 原样传入；再根据返回的 context（背景）和 content_to_develop（待开发内容，含 document_text）编写或修改代码。
```

## 示例二（仅含 node_id）

```
请根据 DIP Studio 节点获取项目上下文并完成开发任务。

node_id: 42

请先调用 get_context 工具，将本段 prompt 原样传入；再根据返回的 context 和 content_to_develop（尤其是 document_text）编写或修改代码。
```

## 说明

- **context**：当前节点的祖先链（根到父节点）及各自文档，作为背景。
- **content_to_develop**：当前节点及其所有子节点及各自文档（含 `document_text` 可读文本），作为待开发内容。
- Studio 前端可在节点详情页提供「复制 Coding Agent Prompt」按钮，生成内容需包含**当前页节点 URL**（含 `/nodes/<节点id>`）或至少一行 `node_id: <节点id>`。
