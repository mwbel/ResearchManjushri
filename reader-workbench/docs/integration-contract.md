# LLM Wiki Reader 集成契约

这个模块先作为独立前端应用开发，后续再接入 `LLM Wiki/scripts/wiki_web.py` 或其它后端。

## 前端需要的后端能力

### 1. 文档列表

```http
GET /api/reader/documents?domain=ai智能体
```

返回：

```json
{
  "documents": [
    {
      "document_id": "human-agent-orchestrator",
      "source_id": "source-hash",
      "source_path": "raw/sources/ai智能体/2026/example.md",
      "title": "The Human-Agent Orchestrator",
      "domain": "ai智能体",
      "page_count": 279,
      "current_page": 12,
      "status": "reading"
    }
  ]
}
```

### 2. 页面 blocks

```http
GET /api/reader/documents/:document_id/pages/:page_number
```

返回：

```json
{
  "document_id": "human-agent-orchestrator",
  "page_id": "p12",
  "page_number": 12,
  "blocks": [
    {
      "block_id": "p12-b1",
      "kind": "paragraph",
      "original": "This book follows our previous work...",
      "bbox": [0.12, 0.18, 0.82, 0.27],
      "source_path": "raw/sources/ai智能体/2026/example.md"
    }
  ]
}
```

### 3. 当前页翻译

```http
POST /api/reader/translate
```

请求：

```json
{
  "document_id": "human-agent-orchestrator",
  "page_id": "p12",
  "target_language": "zh-CN",
  "block_ids": ["p12-b1", "p12-b2"]
}
```

返回：

```json
{
  "translation_version": "tr-20260626-001",
  "items": [
    {
      "block_id": "p12-b1",
      "translation": "本书延续了我们之前的著作..."
    }
  ]
}
```

### 4. AI 解释

```http
POST /api/reader/explain
```

请求：

```json
{
  "document_id": "human-agent-orchestrator",
  "page_id": "p12",
  "block_id": "p12-b1",
  "question": "这段和 AI 编排有什么关系？"
}
```

返回：

```json
{
  "answer": "这段把本书从 agent 技术介绍转向组织领导...",
  "citations": [
    {
      "page_id": "p12",
      "block_id": "p12-b1",
      "quote": "This one explains how to lead them."
    }
  ],
  "candidate_concepts": [
    {
      "name": "领导智能体",
      "definition_draft": "对 agent 的任务、边界、风险和反馈回路进行组织化控制。"
    }
  ]
}
```

### 5. 保存笔记与投影候选

```http
POST /api/reader/notes
POST /api/reader/concept-candidates
```

要求：

- 保存笔记时必须带 `document_id/page_id/block_id`。
- 生成候选概念时只写入 artifact 或 review queue，不直接写入 `wiki/concepts/*.md`。
- 投影到长期图谱仍复用现有人工审核链路。

## 与现有 LLM Wiki 的边界

- 读取 source：可复用 `/api/sources`。
- 读取图谱：可复用 `/api/concepts/graph`。
- 新建 source：可复用 `/api/sources`。
- 新增 reader 专用能力时，优先增加 `/api/reader/*`，避免污染已有 intake/workbench API。
- `raw/assets/uploads` 中的原件保持只读；reader 产物单独保存为 artifacts。
