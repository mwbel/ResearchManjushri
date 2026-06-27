# LLM Wiki API 契约（v0.1）

本文档是 `ResearchManjushri` 当前统一接口入口，默认服务地址为 `http://127.0.0.1:8765`。

本合同对应 `app/llm-wiki/scripts/wiki_web.py` 的当前路由实现。若接口版本发生兼容性变更，在 `docs/api/` 下按版本补充新合同。

## 1. 通用约定

1. 路径前缀固定为 `/api`。
2. 成功返回建议采用统一 envelope（详见 `shared/api-response.md`）：

```json
{
  "ok": true,
  "data": {...},
  "error": null,
  "meta": {}
}
```

3. 当前服务中仍存在部分历史返回形态（如直接 `error` 字符串），后续迭代逐步统一为 `error.code` + `error.message`。
4. 任何“长期知识层”写操作必须通过服务动作触发，不可由前端直接改文件。

## 2. 资源对象

### Source（资料）
- `id`: source id
- `title`, `domain`, `kind`, `status`
- `source_url`, `local_path`, `raw_path`, `summary_path`
- `created_at`, `updated_at`

### Concept（概念）
- `slug`, `title`, `domain`, `status`, `aliases`
- `definition`, `sources`, `relations`

### Concept Review（候选/人工审核）
- `id`、`type`、`status`（`pending`、`accepted`、`rejected`）
- `recommendation`、`evidence`、`created_at`、`resolved_at`

## 3. 接口清单（v0.1）

### GET

| 路径 | 说明 | 查询参数 |
| --- | --- | --- |
| `/api/domains` | 查询允许学科列表 | 无 |
| `/api/sources` | 列表 Source，可按学科过滤 | `domain` |
| `/api/sources/recent` | 最近 Source 列表 | `limit`（默认 12） |
| `/api/workbench` | 读取工作台聚合数据 | `domain`（默认 `general`） |
| `/api/concepts/graph` | 概念图谱查询 | `domain`（默认 `general`） |
| `/api/concepts/page` | 读取概念页 | `slug`（必填）、`domain`（可选） |
| `/api/concepts/archive/recent` | 最近概念归档项 | `limit`（默认 12） |
| `/api/sources/{source_id}/ingest-status` | 查询单个 Source 的 ingest 状态 | 无 |
| `/api/sources/{source_id}/concept-candidates` | 查询候选概念 | 无 |
| `/api/sources/{source_id}/accepted-concepts` | 查询已接受概念 | 无 |
| `/api/sources/{source_id}/relation-candidates` | 查询候选关系 | 无 |
| `/api/sources/{source_id}/accepted-graph` | 查询已接受关系投影 | 无 |
| `/api/sources/{source_id}/artifacts/{artifact_type}` | 获取生成产物 | 无 |
| `/api/health` | 服务健康检查 | 无 |

### POST

| 路径 | 说明 | 典型 Body |
| --- | --- | --- |
| `/api/sources` | 创建 Source | `title`, `source_url` / `local_path`, `domain` |
| `/api/sources/preview` | 预览创建（dry-run） | 同 `/api/sources` |
| `/api/uploads` | 本地上传文件 | 上传元信息与内容摘要 |
| `/api/sources/domain` | 更新 Source 学科 | `source_id`, `domain` |
| `/api/sources/update` | 更新 Source 元数据 | `source_id` 与需更新字段 |
| `/api/sources/auto-supplement` | 触发补正文 | `source_id` 或 `path` |
| `/api/sources/delete` | 删除 Source | `source_id` |
| `/api/domains/delete` | 删除自定义学科 | `domain` |
| `/api/sciverse/search` | 外部检索（Sciverse） | 检索关键字与分页参数 |
| `/api/trackers/science` | 提交 science tracker | tracker payload |
| `/api/sciverse/import-source` | 导入检索源到 Source | 标识与字段映射 |
| `/api/concepts/academic-evidence` | 新增学术证据 | `source_id`, `snippet` 等 |
| `/api/concepts/create` | 新建概念 | `slug`, `title`, `definition`, `domain` |
| `/api/concepts/update` | 修改概念 | `slug`, `domain`, 变更字段 |
| `/api/concepts/graph-node/delete` | 删除图谱节点 | `slug`, `domain` |
| `/api/concepts/delete` | 删除概念 | `slug`, `domain` |
| `/api/concepts/organize` | 概念组织与归类 | 组织参数 |
| `/api/concepts/decision` | 审核决策（接受/拒绝） | `source_id`, `candidate_id`, `action` |
| `/api/concepts/merge` | 概念合并 | `source_id`, `source_slug`, `target_slug` |
| `/api/concepts/restore` | 恢复归档概念 | `slug`, `domain` |
| `/api/batch-automation` | 批量自动化任务 | `domain`, `apply`, `limit`, `include_completed`, `overwrite` |
| `/api/sources/{source_id}/reingest` | 重跑 ingest | 无 |
| `/api/sources/{source_id}/concept-candidates/{candidate_id}/{action}` | 更新候选概念状态 | `action=accept|reject|rename|note`，需对应字段 |
| `/api/sources/{source_id}/relation-candidates/{relation_id}/{action}` | 更新候选关系状态 | `action=accept|reject|note` |
| `/api/ingest` | 按路径触发完整 ingest | `path`, `overwrite_ingest` |
| `/api/rebuild` | 重建索引与图谱 | `domain`, `run_lint` |

说明：

- `{action}` 以路径 segment 形式出现，示例：`/api/sources/abc/concept-candidates/1/accept`。
- `slug`、`candidate_id`、`relation_id` 都以字符串路径段传递，不建议包含 `/`，传递前请先 `urlencode`。

## 4. 错误与兼容

1. 缺少参数：`400 Bad Request`，返回 `error` 说明。
2. 资源不存在：`404 Not Found`。
3. 状态冲突：`409 Conflict`。
4. 服务异常：`500 Internal Server Error`。
5. 兼容期内，历史错误返回可能为：

```json
{"ok": false, "error": "错误文字"}
```

后续计划是统一为：

```json
{"ok": false, "error": {"code": "ERR_CODE", "message": "错误说明"}}
```

## 5. 下一步（接口演进）

1. 对 `/api/sources` / `/api/concepts` / `/api/reviews` 的分页与过滤标准化字段补齐。
2. 增加 `version` 头与版本变更日志。
3. 将 `docs/api/llm-wiki-api.md` 与 `shared/api-response.md` 作为所有新前端/app 管控线上的最小验收项。
