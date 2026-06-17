---
title: LLM Wiki Home
type: meta
status: active
created: 2026-04-07
updated: 2026-06-17
summary: 这个知识库的入口页，说明当前主题、结构和常用入口。
tags: [home, meta, llm-wiki]
sources: [llm-wiki.md]
---

# LLM Wiki Home

这个仓库是一个个人版 LLM Wiki：`raw/` 负责保存原始资料，`wiki/` 负责保存经过整合、可持续维护的知识页面。

## 入口

- [Index](./index.md)
- [Log](./log.md)
- [Inbox](./inbox.md)
- [General Knowledge Network](../domains/general.md)
- [LLM Wiki Knowledge Network](../domains/llm-wiki.md)
- [数学 Knowledge Network](../domains/math.md)
- [物理 Knowledge Network](../domains/physics.md)
- [西藏天文历算 Knowledge Network](../domains/tibetan-astronomy-calendar.md)
- [现代天文学 Knowledge Network](../domains/modern-astronomy.md)
- [LLM Wiki Concept](../concepts/llm-wiki.md)
- [Mathematics](../concepts/math.md)
- [Physics](../concepts/physics.md)
- [Tibetan Astronomy Calendar](../concepts/tibetan-astronomy-calendar.md)
- [Modern Astronomy](../concepts/modern-astronomy.md)
- [Seed Source Summary](../sources/2026-04-04-llm-wiki-pattern.md)

## 当前默认工作流

1. 把新资料放进按学科分类的 `raw/sources/<domain>/<year>/`。
2. 让 LLM 按 `CODEX-AGENTS.md` 或 `CLAUDE-AGENTS.md` 执行 ingest。
3. 运行 `python3 scripts/rebuild_domain_network.py --domain <domain>`，更新单学科知识网络。
4. 问题优先基于 `wiki/` 回答。
5. 高价值问答写回 `wiki/analyses/`。
6. 定期运行 lint，清理断链、孤儿页和知识缺口。

## 目前主题

- 如何把 LLM 从“临时问答工具”变成“持续维护个人知识库的代理”。
- 如何用简单 Markdown、索引和日志支撑长期增长，而不是一开始就上复杂 RAG 基建。
- 当前原始资料的主要学科包括数学、物理、西藏天文历算、现代天文学。

## 学科入口

- [数学 Knowledge Network](../domains/math.md): 数学资料、概念页和待处理 source 的网络入口。
- [Mathematics](../concepts/math.md): 数学资料、定理、证明方法和计算工具的入口。
- [物理 Knowledge Network](../domains/physics.md): 物理资料、概念页和待处理 source 的网络入口。
- [Physics](../concepts/physics.md): 物理理论与天体物理基础的入口。
- [西藏天文历算 Knowledge Network](../domains/tibetan-astronomy-calendar.md): 西藏天文历算资料、概念页、分析页和待处理 source 的网络入口。
- [Tibetan Astronomy Calendar](../concepts/tibetan-astronomy-calendar.md): 传统历算规则、术语与计算体系的入口。
- [现代天文学 Knowledge Network](../domains/modern-astronomy.md): 现代天文学资料、概念页和待处理 source 的网络入口。
- [Modern Astronomy](../concepts/modern-astronomy.md): 现代观测、天体分类、轨道和数据分析的入口。

## 下一步建议

- 导入 3 到 5 篇你最近最常回看的资料。
- 先选一个学科，用 `new_source.py --url` 或 `--local-path` 建立 5 到 10 个 raw source stub。
- 每次新增资料后重建对应 `wiki/domains/<domain>.md`，观察这门学科内部的资料网络是否变清晰。
- 优先在四个学科目录中各放入 1 篇代表性资料，帮助 wiki 建立跨学科结构。
- 先围绕一个明确主题建立第一批 concept/entity 页面。
- 连续用一周，观察哪些操作值得继续自动化。

## Sources

- `llm-wiki.md`
