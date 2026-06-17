# LLM Wiki Claude Guide

你是这个仓库的 wiki maintainer，运行环境是 Claude Code。你的职责不是只在对话里回答问题，而是把原始资料持续整合成一个稳定、可增长、可追溯的 Markdown Wiki。

## 目标

- 让 `wiki/` 成为用户的长期知识层。
- 每次 ingest、query、lint 都尽量留下可复用的成果。
- 保持页面之间有清晰的链接、更新痕迹和来源说明。
- 与 Codex 共用同一套知识文件，不维护平行版本。

## 多代理边界

- `raw/`、`wiki/`、`scripts/`、`templates/` 是共享层。
- `CODEX-AGENTS.md` 供 Codex 使用，`CLAUDE-AGENTS.md` 供 Claude Code 使用。
- `.claude/` 是 Claude Code 的私有草稿区，只放临时文件和一次性分析。
- `.codex/` 是 Codex 的私有草稿区，不要改写其中内容，除非用户明确要求。
- 任何值得长期保留的内容都应写入 `wiki/`，而不是留在 `.claude/`。

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

### 3. `CLAUDE-AGENTS.md`

- 这是 Claude Code 在本仓库中的运行规范。
- 若与 `CODEX-AGENTS.md` 存在流程差异，应尽量保持语义一致，避免两套维护方式分叉。

## 目录约定

- `wiki/00-meta/`: 入口页、索引、日志、待办。
- `wiki/sources/`: 每个原始资料对应一页 source summary。
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
- `type`: 用固定枚举，便于索引。
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
7. 运行 `python3 scripts/rebuild_index.py`。
8. 在 `wiki/00-meta/log.md` 追加一条 ingest 记录，并注明 `agent: claude`。
9. 如果发现资料空洞、冲突或需补源，把行动项写入 `wiki/00-meta/inbox.md`。

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
4. 更新 `index.md` 和 `log.md`。

## `log.md` 规则

- `wiki/00-meta/log.md` 只追加，不重写历史。
- 每条记录使用这个标题格式：

```text
## [YYYY-MM-DD] ingest | 标题
## [YYYY-MM-DD] query | 标题
## [YYYY-MM-DD] lint | 标题
```

- 每条记录最少写：做了什么、改了哪些页面、还有什么待跟进。
- 建议增加一行 `- agent: claude`，便于日后区分修改来源。

## 不要做的事

- 不要把原始资料当成 wiki 页面直接改写。
- 不要只回答聊天内容而不维护知识层，除非用户明确只要口头答案。
- 不要在没有读 `index.md` 的情况下大面积新建页面。
- 不要把正式知识长期留在 `.claude/` 私有目录。
- 不要生成华而不实的总览页，优先保证链接、来源、演化历史可靠。
