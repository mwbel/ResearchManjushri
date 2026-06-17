---
title: Wiki Inbox
type: meta
status: active
created: 2026-04-07
updated: 2026-06-17
summary: 记录待处理资料、待回答问题和 wiki 维护缺口。
tags: [inbox, meta]
sources: []
---

# Wiki Inbox

## To Ingest

- 先选一个单学科分支作为第一批资料网络，例如 `tibetan-astronomy-calendar` 或 `math`。
- 为该学科登记 5 到 10 个 source stub：网页文章用 `--url`，本地资料用 `--local-path`。
- 数学目录先放 1 篇基础代表资料，例如证明方法、欧几里得几何或线性代数笔记。
- 物理目录先放 1 篇代表资料，例如经典力学或引力相关笔记。
- 现代天文学目录先放 1 篇代表资料，例如轨道、观测或太阳系综述。
- 西藏天文历算方向的下一步可补一份基础历法结构说明，或另一份非交食主题资料。

## Open Questions

- 这四个学科里，第一条要重点长出来的主线是什么？
- 单学科网络第一批应优先选“西藏天文历算”继续深挖，还是从“数学”补基础工具链？
- 本地资料库是否需要约定一个稳定根目录，例如 `/Users/Min369/Documents/.../资料库/`，方便 `local_path` 长期有效？
- 你是否希望保留每日/每周分析沉淀到 `wiki/analyses/`？
- 是否要优先建立“传统历算 vs 现代天文学”的对照专题？
- `藏历的原理与实践-中文.md` 的作者、版本、出处、页码范围是否可以补齐？
- 是否还有同一书的“时轮历部分”或独立时轮历算例，可用于补全严格的逐步拆解页？

## Gaps

- 目前西藏天文历算方向已有第一份正式 source，但其他三门学科仍缺正式 source summary。
- `wiki/domains/` 已生成单学科网络页，但数学、物理、现代天文学还缺真实 source stub。
- 还没有实体页，后续 ingest 时可以按需要补建。
- 学科总览页已建立，但还缺数学、物理、现代天文学的首批 source summary。
- 西藏天文历算方向还缺“现代对照”“月食算例页”“日食算例页”等子页。
- 时轮历目前只有算法骨架页，还缺一份可直接逐步核对的原始算例。

## Network Follow-ups

- 为每个高价值 source 补齐 `source_url` 或 `local_path`。
- 将长期有效的资料整理为 `wiki/sources/...` source summary。
- 在每个学科网络页的 Cross-Disciplinary Bridge Candidates 中写入可验证桥接点，而不是泛泛列主题。
