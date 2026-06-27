# LLM Wiki API 契约

本文档记录 LLM Wiki 核心能力对外暴露的接口边界。当前以现有本地 HTTP 服务为基础，后续可迁移到独立后端或服务网关。

默认本地地址：

```text
http://127.0.0.1:8765
```

## 设计原则

1. API 返回结构应稳定，前端 app、管理后台和阅读器都通过 API 集成。
2. 文件路径、raw source、wiki page 的写入由后端控制。
3. 前端只提交用户动作，不直接改写长期知识层。
4. 所有自动抽取结果都应进入人工审核或可回滚状态。

## 核心资源

### Source

资料来源，包括网页、微信文章、本地文件、笔记。

核心字段：

- `id`
- `title`
- `domain`
- `kind`
- `status`
- `source_url`
- `local_path`
- `raw_path`
- `summary_path`
- `created_at`
- `updated_at`

### Concept

长期概念页或候选概念。

核心字段：

- `slug`
- `title`
- `domain`
- `status`
- `aliases`
- `definition`
- `sources`
- `relations`

### Relation

概念之间的关系。

核心字段：

- `source`
- `target`
- `type`
- `confidence`
- `evidence`
- `source_id`

### Review Task

人工审核任务。

核心字段：

- `id`
- `type`
- `status`
- `target`
- `recommendation`
- `evidence`
- `created_at`
- `resolved_at`

## 当前接口分组

### 资料接口

建议统一到：

```text
GET /api/sources
POST /api/sources
POST /api/sources/ingest
POST /api/sources/auto-supplement
DELETE /api/sources/{id}
```

### 概念接口

建议统一到：

```text
GET /api/concepts
GET /api/concepts/page
POST /api/concepts/create
POST /api/concepts/update
POST /api/concepts/delete
```

### 审核接口

建议统一到：

```text
GET /api/reviews
POST /api/reviews/{id}/accept
POST /api/reviews/{id}/reject
POST /api/reviews/{id}/edit
```

### 图谱接口

建议统一到：

```text
GET /api/concepts/graph
POST /api/concepts/graph/rebuild
POST /api/concepts/graph/remove-node
```

## 下一步

1. 对照 `scripts/wiki_web.py` 中已有 route，补齐真实接口清单。
2. 为 Reader Workbench 和后续管理后台定义最小 adapter。
3. 把错误码和 response envelope 固化到 `shared/`。
