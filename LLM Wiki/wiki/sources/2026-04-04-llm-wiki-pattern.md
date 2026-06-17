---
title: Seed Source - LLM Wiki Pattern
type: source
status: active
created: 2026-04-07
updated: 2026-06-17
summary: 对 llm-wiki 设计文档的摘要，说明这个仓库为何采用 raw/wiki/schema 三层结构。
tags: [source, llm-wiki, seed]
sources: [llm-wiki.md]
---

# Seed Source - LLM Wiki Pattern

## Source Profile

- Title: `llm-wiki`
- Date in source context: 2026-04-04
- Role in this repo: 作为整个 starter kit 的设计输入

## Main Claims

- 个人知识库不该只停留在“上传文件后临时检索”的模式。
- 更好的做法是让 LLM 持续维护一层结构化 wiki，提前完成总结、交叉链接和冲突标注。
- `index.md` 和 `log.md` 足以支撑一个中小规模 wiki 的导航与时间线管理。
- 随着使用增加，再逐步引入搜索或更强工具即可。

## Implications For This Repo

- 需要一个明确的 agent schema，因此加入 `CODEX-AGENTS.md` 与 `CLAUDE-AGENTS.md`。
- 需要严格区分原始资料和知识层，因此目录拆成 `raw/` 与 `wiki/`。
- 需要把未来高价值问答沉淀成页面，因此预留 `wiki/analyses/`。
- 单学科知识网络可以作为 `raw/` 与跨学科 wiki 之间的中间层，先把每门学科内部的资料和页面串稳。

## Follow-up Questions

- 你的第一批主题会集中在哪些领域？
- 哪些资料类型最常见：文章、播客、会议、书摘，还是自己的日志？
- 未来是否需要实体页模板，例如人物、公司、产品？

## Related

- [LLM Wiki](../concepts/llm-wiki.md)
- [LLM Wiki Home](../00-meta/home.md)
- [LLM Wiki Knowledge Network](../domains/llm-wiki.md)

## Sources

- `llm-wiki.md`
