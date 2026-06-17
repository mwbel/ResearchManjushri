---
title: LLM Wiki Knowledge Network
type: domain
status: active
created: 2026-06-17
updated: 2026-06-17
summary: LLM Wiki 单学科知识网络入口，串联网页文章、本地资料、source summary、concept、analysis 与待办问题。
tags: [llm-wiki, domain-network]
sources: []
---

# LLM Wiki Knowledge Network

这页是单学科知识网络的入口。它把原始资料、网页链接、本地资料位置、已沉淀的 wiki 页面和下一步待处理动作放在同一张可维护地图里。

## Current Shape

- Registered raw sources: 1
- Connected wiki pages: 4
- Inbox sources waiting for ingest: 0
- Generated on: 2026-06-17

## How To Add Knowledge

- Web article: `python3 scripts/new_source.py --domain llm-wiki --kind article --title "标题" --url "https://..."`
- Local file: `python3 scripts/new_source.py --domain llm-wiki --kind paper --title "标题" --local-path "/absolute/path/to/file.pdf"`
- After adding sources, run `python3 scripts/rebuild_domain_network.py` and then `python3 scripts/rebuild_index.py`.
- When a source is important, create or update a `wiki/sources/...` source summary and connect it to concept/entity/analysis pages.

## Knowledge Map

```mermaid
flowchart LR
    D["LLM Wiki"]
    R1["raw: Seed Source - LLM Wiki Pattern"] --> D
    D --> W1["meta: LLM Wiki Home"]
    D --> W2["concept: LLM Wiki"]
    D --> W3["source: Seed Source - LLM Wiki Pattern"]
    D --> W4["source: Source - Seed Source - LLM Wiki P…"]
```

## Source Intake

| Status | Kind | Title | Locator | Raw File |
| --- | --- | --- | --- | --- |
| active | source | [Seed Source - LLM Wiki Pattern](../../raw/sources/llm-wiki/2026/2026-04-04-llm-wiki-pattern.md) | 未登记 | `raw/sources/llm-wiki/2026/2026-04-04-llm-wiki-pattern.md` |

## Wiki Knowledge Layer

| Type | Title | Summary | Wiki Page |
| --- | --- | --- | --- |
| meta | [LLM Wiki Home](../00-meta/home.md) | 这个知识库的入口页，说明当前主题、结构和常用入口。 | `wiki/00-meta/home.md` |
| concept | [LLM Wiki](../concepts/llm-wiki.md) | 用 LLM 持续维护的知识层，位于原始资料与最终回答之间。 | `wiki/concepts/llm-wiki.md` |
| source | [Seed Source - LLM Wiki Pattern](../sources/2026-04-04-llm-wiki-pattern.md) | 对 llm-wiki 设计文档的摘要，说明这个仓库为何采用 raw/wiki/schema 三层结构。 | `wiki/sources/2026-04-04-llm-wiki-pattern.md` |
| source | [Source - Seed Source - LLM Wiki Pattern](../sources/2026-04-07-llm-wiki-pattern.md) | 已登记的llm-wiki资料，等待补充摘录或正文。 | `wiki/sources/2026-04-07-llm-wiki-pattern.md` |

## Next Network Actions

- Turn high-value `inbox` sources into source summaries.
- Promote recurring terms, methods, people, texts, tools, or datasets into concept/entity pages.
- Add explicit `Related` links between source summaries and concept pages, then rerun lint.
- Mark cross-disciplinary bridge candidates in the related pages instead of duplicating content across domains.

## Cross-Disciplinary Bridge Candidates

- 待补：这个学科中哪些概念需要连接到其他学科？
- 待补：哪些资料适合成为下一阶段跨学科 LLM Wiki 的桥接页面？
