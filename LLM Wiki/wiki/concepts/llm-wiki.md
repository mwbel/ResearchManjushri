---
title: LLM Wiki
type: concept
status: active
created: 2026-04-07
updated: 2026-06-17
summary: 用 LLM 持续维护的知识层，位于原始资料与最终回答之间。
tags: [llm, wiki, knowledge-management]
sources: [llm-wiki.md]
---

# LLM Wiki

## Core Idea

LLM Wiki 的关键不是“让模型随问随检索”，而是让模型把原始资料持续编译成一个长期存在的 Markdown Wiki。知识不是每次问答临时重建，而是随着 ingest 和 query 不断累积。

## Three Layers

### Raw Sources

- 原始资料是事实来源。
- 默认只读。
- 可以是文章、访谈、截图、笔记、PDF、网页摘录。

### Wiki

- 由 LLM 负责维护。
- 包含概念页、实体页、source summary、专题分析。
- 负责跨页面链接、冲突标注、结论演化。

### Domain Networks

- 每个学科一页自动生成的网络入口，放在 `wiki/domains/`。
- 负责把网页文章、本地资料、source summary、concept、analysis 和待处理问题串在一起。
- 它是从单学科资料库走向跨学科 LLM Wiki 的中间层。

### Schema

- 通过 `CODEX-AGENTS.md` 和 `CLAUDE-AGENTS.md` 约束不同代理的行为。
- 决定 ingest、query、lint 的标准动作。
- 是让代理从“聊天机器人”变成“知识库维护者”的关键。

## Why It Matters

- 避免每次问答都重新检索和拼接相同信息。
- 有利于长期主题研究，因为综合结论会不断变厚。
- 可以把高价值问答沉淀为新页面，而不是丢在聊天记录里。

## Operating Loop

1. Ingest 新 source。
2. 更新 source summary 与相关 concept/entity 页面。
3. Query 时优先读 wiki 而不是回到所有原始资料。
4. 把高价值回答沉淀为 analysis 页面。
5. 定期 lint，修补断链、孤儿页、冲突和缺口。

## Design Choices In This Repo

- 优先使用普通 Markdown 和目录结构，而不是上来就做复杂检索系统。
- `index.md` 充当轻量目录，帮助 LLM 在中小规模知识库中快速定位页面。
- `log.md` 保存时间线，帮助追踪知识库演化。

## Related

- [LLM Wiki Knowledge Network](../domains/llm-wiki.md)
- [LLM Wiki Home](../00-meta/home.md)
- [Mathematics](./math.md)
- [Physics](./physics.md)
- [Tibetan Astronomy Calendar](./tibetan-astronomy-calendar.md)
- [Modern Astronomy](./modern-astronomy.md)
- [Seed Source Summary](../sources/2026-04-04-llm-wiki-pattern.md)

## Sources

- `llm-wiki.md`
