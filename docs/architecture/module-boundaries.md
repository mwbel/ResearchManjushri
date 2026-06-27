# 模块化开发边界

## 总原则

LLM Wiki 作为核心知识编译能力模块，沿用「先接口，再实现」顺序构建新能力：先定义可复用边界，再定义服务边界，再接入应用。

模块化目标不是“切服务”，而是让 `LLM Wiki` 的能力可被多个前端、后台、数据库流程调用，不绕过 API 写入 `raw/` 与 `wiki/`。

## 当前执行边界

### 应用层

- `LLM Wiki Web UI`：核心工作台。
- `Reader Workbench`：阅读与研究者交互。
- 后续管理后台：审核/发布/运营类应用。

### 接口层

- `docs/api/llm-wiki-api.md`：LLM Wiki 对外 REST 契约（当前接口源于 `app/llm-wiki/scripts/wiki_web.py` 的实际路由）。
- `docs/api/` 下统一记录 API 版本、错误码、字段含义。
- 未来跨语言服务接入优先通过 adapter 或 API 网关，不直接读取模块实现细节文件。

### 领域层

- `domains/sources/`：资料与导入域。
- `domains/concepts/`：概念与关系域。
- `domains/relations/`：关系抽取与投影域。
- `domains/reviews/`：审核与状态流转域。
- `domains/graphs/`：图谱查询与维护域。
- `domains/readers/`：阅读、分页、批注域。

### 实现层

- `app/llm-wiki/scripts/`：现有后端入口与脚本能力（现阶段保持核心入口，不作大规模迁移）。
- `app/llm-wiki/webui/`：现有工作台页面与交互。
- `app/llm-wiki/raw/`、`app/llm-wiki/wiki/`：知识编译知识层运行时数据。

### 共享层

- `services/`：可独立运行的可复用服务（如 source-ingest-service、concept-service、graph-service、review-service、model-gateway-service）。
- `shared/`：跨模块共享 schema、错误码、响应格式与常量约定。

## 模块化开发规范

1. 每个新能力先判定归属域（sources/concepts/relations/reviews/graphs/readers）。
2. 领域能力必须先形成：
   - 数据对象（ID、状态、时间字段）。
   - 输入输出与副作用。
   - 状态流转与错误码。
3. 对外能力默认通过 REST HTTP 暴露在 `docs/api/llm-wiki-api.md`，并注明版本与迁移计划。
4. 同一逻辑不重复：`services/` 负责服务化能力，`webui` 只承载展示与触发动作。
5. 不经明确 API 契约，不新增“可复用”功能。
6. `raw/`、`wiki/` 写入仅允许来源于核心脚本/服务输出或经过审核动作，避免页面直接改库。

## 近期执行约束

当前阶段不拆分/不重构：

- `app/llm-wiki/scripts/wiki_web.py`
- `app/llm-wiki/webui/`
- `app/llm-wiki/raw/`
- `app/llm-wiki/wiki/`

这部分继续作为 MVP 核心运行，并通过 API 契约逐步解耦。

## 路线图

1. 先把 `LLM Wiki` 接口收敛到 `docs/api/llm-wiki-api.md`（本项）。
2. 新应用/工具先接入 API 契约，再对 `LLM Wiki` 内部实现提出改造建议。
3. 形成 `services/` 与 `shared/` 的最小可复用模块骨架后，逐步迁移可独立运行能力。
