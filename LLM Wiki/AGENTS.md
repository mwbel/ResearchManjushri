# LLM Wiki Agent Guide

你是这个仓库的 wiki maintainer。你的职责不是临时回答问题，而是把原始资料持续编译成一个稳定、可增长、可追溯的 Markdown Wiki。

## 目标

- 让 `wiki/` 成为用户的长期知识层。
- 每次 ingest、query、lint 都尽量留下可复用的成果。
- 保持页面之间有清晰的链接、更新痕迹和来源说明。

## 三层结构

### 1. `raw/`

- `raw/sources/` 存放原始资料，默认视为只读。
- `raw/sources/` 按 `学科/domain/year` 组织，例如 `raw/sources/math/2026/`。
- `raw/assets/` 存放图片、截图、附件。
- 不要把总结性内容写回原始资料文件，除非用户明确要求。

### 2. `wiki/`

- 这是由 LLM 维护的知识层。
- 可新建、重写、拆分、合并页面。
- 每个页面尽量只承担一个清晰主题。

### 3. `CODEX-AGENTS.md`

- 这是你的运行规范。
- 如果实际维护中发现更稳定的流程，可以和用户沟通后更新。

## 目录约定

- `wiki/00-meta/`: 入口页、索引、日志、待办。
- `wiki/sources/`: 每个原始资料对应一页 source summary。
- `wiki/domains/`: 每个学科一页自动生成的知识网络入口，串联原始资料、source summary、concept/entity/analysis 和下一步动作。
- `wiki/concepts/`: 概念、方法、主题页。
- `wiki/entities/`: 人物、组织、产品、项目等实体页。
- `wiki/analyses/`: 问答沉淀、比较分析、专题报告。

## 页面 frontmatter 规范

所有 `wiki/` 页面都尽量包含这几个字段：

```yaml
---
title: 页面标题
type: meta | source | concept | entity | analysis
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
summary: 一句话说明这页讲什么
tags: [tag-a, tag-b]
sources: [raw/sources/...]
---
```

约定：

- `title`: 人类可读标题，可用中文。
- `type`: 用固定枚举，便于索引。当前枚举包括 `meta | domain | source | concept | entity | analysis`。
- `summary`: 单行摘要，给 `index.md` 用。
- `sources`: 写仓库根目录相对路径；如果是综合页，可列多个。
- 文件名优先使用 `kebab-case` 英文 slug；若必须中文也可以，但优先稳妥可移植。
- source 文件建议在 frontmatter 中加入 `domain` 与 `domain_label`，便于跨学科管理。

## 写作规范

- 先更新内容，再补交叉链接，再更新 `updated` 字段。
- 多用短段落、小标题、项目符号，避免大段空泛总结。
- 结论和证据尽量分开写清楚。
- 涉及来源的断言，页面底部要有 `## Sources`。
- 如果新资料推翻旧结论，不要静默覆盖；要在相关页写明“已被更新/ challenged”。

## Ingest 工作流

当用户要求处理一个新资料时：

1. 读取目标 source 文件，必要时连同相邻图片一起查看。
2. 识别 source 所属学科，并在 source summary 与相关页面中保留对应标签。
3. 先读 `wiki/00-meta/index.md`，了解现有页面与命名。
4. 新建或更新对应的 `wiki/sources/...` 页面。
5. 更新所有受影响的 concept/entity/analysis 页面。
6. 如发现高频新主题但没有页面，主动补建页面。
7. 如果资料属于某一学科，运行 `python3 scripts/rebuild_domain_network.py --domain <domain>`，让 `wiki/domains/<domain>.md` 同步资料与页面关系。
8. 运行 `python3 scripts/rebuild_index.py`。
9. 在 `wiki/00-meta/log.md` 追加一条 ingest 记录。
10. 如果发现资料空洞、冲突或需补源，把行动项写入 `wiki/00-meta/inbox.md`。

## Single-Discipline Network 工作流

当用户要为某一学科增加网页文章、本地资料或资料库入口时：

1. 用 `python3 scripts/new_source.py` 建立 raw source stub。
2. 网页文章用 `--url` 记录原文链接，本地资料用 `--local-path` 记录稳定路径。
3. 如果资料只是待读，不要急着写入概念页；先让它停在 `status: inbox`。
4. 如果资料已经被整理成长期知识，补建或更新 `wiki/sources/...` source summary。
5. 更新相关 concept/entity/analysis 页的 `Related` 与 `Sources`。
6. 运行 `python3 scripts/rebuild_domain_network.py --domain <domain>`。
7. 运行 `python3 scripts/rebuild_index.py` 与 `python3 scripts/lint_wiki.py`。

目标是先让每个学科内部形成清晰的资料-概念-问题网络，再把跨学科桥接点写入相关页面。

## Query 工作流

当用户问问题时：

1. 先看 `wiki/00-meta/index.md`。
2. 只读取必要页面，优先读 wiki，不要每次回到所有 raw source。
3. 回答时指出结论来自哪些 wiki 页面和哪些 source。
4. 如果用户的提问产出了高价值结论，主动建议或直接写入 `wiki/analyses/`。
5. 如果答案暴露出 wiki 缺口，把缺口写进 `inbox.md`。

## Lint 工作流

当用户要求检查 wiki 健康度时：

1. 运行 `python3 scripts/lint_wiki.py`。
2. 处理断链、缺 frontmatter、孤儿页面。
3. 人工检查是否存在：
   - 旧结论未被新资料修订
   - 高频概念没有独立页面
   - source summary 已有，但没有被整合进 concept/entity 页
   - domain network 中有重要 `inbox` source 长期未 ingest
4. 更新 domain network、`index.md` 和 `log.md`。

## `log.md` 规则

- `wiki/00-meta/log.md` 只追加，不重写历史。
- 每条记录使用这个标题格式：

```text
## [YYYY-MM-DD] ingest | 标题
## [YYYY-MM-DD] query | 标题
## [YYYY-MM-DD] lint | 标题
```

- 每条记录最少写：做了什么、改了哪些页面、还有什么待跟进。

## 不要做的事

- 不要把原始资料当成 wiki 页面直接改写。
- 不要只回答聊天内容而不维护知识层，除非用户明确只要口头答案。
- 不要在没有读 `index.md` 的情况下大面积新建页面。
- 不要生成华而不实的总览页，优先保证链接、来源、演化历史可靠。


---

# Codex 执行规则与 LLM Wiki MVP 架构约束

## 0. 强制执行规则

在进行任何代码修改、文件修改、删除、迁移、重构、生成测试数据，或者执行任何可能改变项目状态的命令之前，Codex 必须先给出实施计划，并等待用户明确批准。

Codex 不能只给出计划后就自动开始执行。

Codex 必须等到用户明确回复以下类似内容后，才能开始修改：

- approve
- approved
- 同意
- 开始执行
- 可以改
- 执行

如果用户没有明确批准，Codex 必须继续等待或询问确认。

这条规则适用于所有任务，包括小修复、UI 修改、测试修改、文件清理、脚本创建和配置修改。

如果任务只是查看、分析、读取文件或输出计划，Codex 可以进行只读操作，但不得在未获批准前修改项目文件。

---

## 1. 项目定位

本项目基于 LLM Wiki 思路开发。

本项目不是普通 RAG 系统。

项目目标是把用户看过、收藏过、上传过、整理过的资料，转化为一个个人多学科知识网络。这个知识网络应该能够被：

- 阅读
- 搜索
- 追踪
- 跳转
- 连接
- 审核
- 纠错
- 扩展
- 跨学科联通

因此，本项目应被视为一个“知识编译系统”，而不是简单的资料存储系统。

长期目标流程是：

```text
source intake
→ ingest artifacts
→ source summary
→ domain classification
→ concept candidates
→ human review
→ accepted concept projection
→ relation candidates
→ relation review
→ source pages
→ concept page drafts
→ graph updates
→ retrieval indexes
→ cross-domain bridges

---

## Codex 执行确认补充规则

### 当前推荐下一任务

当前项目阶段推荐下一任务是：

Accepted Concept Projection MVP

该阶段目标是把：

concept_candidates.json
+ concept_candidate_reviews.json

合成为：

accepted_concepts.json

规则：

1. 不得修改原始 concept_candidates.json。
2. 不得修改 concept_candidate_reviews.json。
3. 不得写入 wiki/concepts/*.md。
4. 不得引入真实 LLM。
5. 不得引入数据库。
6. 不得引入 worker daemon。
7. 不得更新图谱。
8. 不得做跨学科桥接。
9. accepted_concepts.json 只应包含用户已 accepted 的候选概念。
10. rejected 和 pending 概念不得进入 accepted_concepts.json。

### Codex 执行前计划格式

在实现任何修改前，Codex 必须先返回：

1. 任务理解
2. 预计修改文件
3. 实施步骤
4. 数据结构变更，如有
5. API 变更，如有
6. 测试计划
7. 风险与回滚方案
8. 明确询问：“是否批准这个计划？”

用户明确批准前，Codex 不得编辑文件、创建文件、删除文件、运行会改变项目状态的命令。

### 强制停止条件

如果任务涉及以下任何事项，Codex 必须停止并请求用户明确批准：

1. 引入真实 LLM 调用
2. 添加数据库
3. 添加 worker daemon
4. 修改图谱文件
5. 写入正式 wiki/concepts/*.md
6. 删除已有用户数据
7. 大规模重写前端
8. 修改无关文件
9. 执行 rm -rf、git clean、git reset --hard 等破坏性命令
