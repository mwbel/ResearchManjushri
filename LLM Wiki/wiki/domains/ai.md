---
title: ai Knowledge Network
type: domain
status: active
created: 2026-06-17
updated: 2026-06-19
summary: ai 单学科知识网络入口，串联网页文章、本地资料、source summary、concept、analysis 与待办问题。
tags: [ai, domain-network]
sources: []
---

# ai Knowledge Network

这页是单学科知识网络的入口。它把原始资料、网页链接、本地资料位置、已沉淀的 wiki 页面和下一步待处理动作放在同一张可维护地图里。

## Current Shape

- Registered raw sources: 3
- Connected wiki pages: 5
- Inbox sources waiting for ingest: 0
- Generated on: 2026-06-19

## How To Add Knowledge

- Web article: `python3 scripts/new_source.py --domain ai --kind article --title "标题" --url "https://..."`
- Local file: `python3 scripts/new_source.py --domain ai --kind paper --title "标题" --local-path "/absolute/path/to/file.pdf"`
- After adding sources, run `python3 scripts/rebuild_domain_network.py` and then `python3 scripts/rebuild_index.py`.
- When a source is important, create or update a `wiki/sources/...` source summary and connect it to concept/entity/analysis pages.

## Knowledge Map

```mermaid
flowchart LR
    D["ai"]
    R1["raw: Agentic AI进入正规军时代：读懂Agentic AI全景图…"] --> D
    R2["raw: 人工智能的数学革命已经到来"] --> D
    R3["raw: 工业软件会被AI绝杀吗？"] --> D
    D --> W1["concept: AI"]
    D --> W2["concept: LLM"]
    D --> W3["source: Source - Agentic AI进入正规军时代：读懂Agen…"]
    D --> W4["source: Source - 人工智能的数学革命已经到来"]
    D --> W5["source: Source - 工业软件会被AI绝杀吗？"]
```

## Concept Graph

```mermaid
flowchart LR
    C1A["Transformer"] -- "构成" --> C1B["AI"]
    C2A["AI"] -- "相关" --> C2B["Skills"]
    C3A["AI"] -- "相关" --> C3B["Agent"]
    C4A["AI"] -- "相关" --> C4B["Mulerun"]
    C5A["AI"] -- "相关" --> C5B["AI Partner Skill"]
    C6A["AI"] -- "相关" --> C6B["Code"]
    C7A["LLM"] -- "属于" --> C7B["AI"]
    C8A["LLM"] -- "是" --> C8B["AI"]
    C9A["Transformer"] -- "构成" --> C9B["LLM"]
```

## Concept Relations

| Source Concept | Relation | Target Concept | Evidence |
| --- | --- | --- | --- |
| Transformer | 构成 | AI | [source](../sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md); evidence: 摘要：“泛BP+Transformer”构成了这一代AI基础架构，泛BP已经被诺贝尔奖封印而昭彰天下，却是个有数十年历史的“资深技术”，有深入理解的人都知道Transformer才是这个魔术的核心道具，LLM的真正“新动能”。 |
| AI | 相关 | Skills | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 巧借通用 Agent 内核，只靠 Skills 设计，就能低成本创造具有通用 AI 智能上限的垂直 Agent 应用。 |
| AI | 相关 | Agent | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 巧借通用 Agent 内核，只靠 Skills 设计，就能低成本创造具有通用 AI 智能上限的垂直 Agent 应用。 |
| AI | 相关 | Mulerun | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 顺便给朋友宇森、付铖的 Mulerun 打个广，他们在做全球性的 Agent 开发与交易市场，即将支持 Creator 用 Skills 开发垂直 Agent，可被用户使用 or 被其他 AI 产品调用。 |
| AI | 相关 | AI Partner Skill | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 又如 AI Partner Skill，让 通用 Agent 深度学习你的记忆，塑造懂你的 AI 伴侣，给到个性回应。 |
| AI | 相关 | Code | [source](../sources/2026-06-17-万字长文-claude-skills完全指南-从概念到实战.md); evidence: OpenAI的Codex CLI也采用了几乎一样的架构。 |
| LLM | 属于 | AI | [source](../sources/2026-06-17-agentic-ai进入正规军时代-读懂agentic-ai全景图与畅想一人公司opc的未来.md); evidence: 如果说去年大家还在为大模型（LLM）的参数量狂欢，那今年整个技术圈的风向已经彻底变了，特别是近期小龙虾OpenClaw的火爆，言必称Agentic AI（代理式人工智能或智能… 自动补充：这份资料属于「ai」资料库，用于补强《Agenti… |
| LLM | 是 | AI | [source](../sources/2026-06-17-agentic-ai进入正规军时代-读懂agentic-ai全景图与畅想一人公司opc的未来.md); evidence: 如果说去年大家还在为大模型（LLM）的参数量狂欢，那今年整个技术圈的风向已经彻底变了，特别是近期小龙虾OpenClaw的火爆，言必称Agentic AI（代理式人工智能或智能体人工智能）。 |
| Transformer | 构成 | LLM | [source](../sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md); evidence: 摘要：“泛BP+Transformer”构成了这一代AI基础架构，泛BP已经被诺贝尔奖封印而昭彰天下，却是个有数十年历史的“资深技术”，有深入理解的人都知道Transformer才是这个魔术的核心道具，LLM的真正“新动能”。 |

## Source Intake

| Status | Kind | Title | Locator | Raw File |
| --- | --- | --- | --- | --- |
| active | article | [Agentic AI进入正规军时代：读懂Agentic AI全景图与畅想一人公司OPC的未来](../../raw/sources/ai/2026/2026-06-17-agentic-ai进入正规军时代-读懂agentic-ai全景图与畅想一人公司opc的未来.md) | [web](https://mp.weixin.qq.com/s/jVcYKvy585KYzlbLOAb4HQ) | `raw/sources/ai/2026/2026-06-17-agentic-ai进入正规军时代-读懂agentic-ai全景图与畅想一人公司opc的未来.md` |
| active | article | [人工智能的数学革命已经到来](../../raw/sources/ai/2026/2026-06-17-人工智能的数学革命已经到来.md) | [web](https://mp.weixin.qq.com/s/cp246PJTaFZGQoPbbRFZew) | `raw/sources/ai/2026/2026-06-17-人工智能的数学革命已经到来.md` |
| active | article | [工业软件会被AI绝杀吗？](../../raw/sources/ai/2026/2026-06-17-工业软件会被ai绝杀吗.md) | [web](https://mp.weixin.qq.com/s/dTXLDOfRsvCq0LO8ar_VaQ) | `raw/sources/ai/2026/2026-06-17-工业软件会被ai绝杀吗.md` |

## Wiki Knowledge Layer

| Type | Title | Summary | Wiki Page |
| --- | --- | --- | --- |
| concept | [AI](../concepts/ai.md) | AI 是 ai 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/ai.md` |
| concept | [LLM](../concepts/llm.md) | LLM 是 ai 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/llm.md` |
| source | [Source - Agentic AI进入正规军时代：读懂Agentic AI全景图与畅想一人公司OPC的未来](../sources/2026-06-17-agentic-ai进入正规军时代-读懂agentic-ai全景图与畅想一人公司opc的未来.md) | 自动补充：这份资料属于「ai」资料库，用于补强《Agentic AI进入正规军时代：读懂Agentic AI全景图与畅想一人公司OPC的未来》相关的核心观点、概念证据和学科网络关系。 如果说去年大家还在为大模型（LLM）的参数量狂欢，那今年整个技术圈的风向已经彻底变了，特别是近期小龙虾OpenClaw的火爆，言必称Agentic AI（代理式人工智能或智能… | `wiki/sources/2026-06-17-agentic-ai进入正规军时代-读懂agentic-ai全景图与畅想一人公司opc的未来.md` |
| source | [Source - 人工智能的数学革命已经到来](../sources/2026-06-17-人工智能的数学革命已经到来.md) | 已登记的AI资料，等待补充摘录或正文。 | `wiki/sources/2026-06-17-人工智能的数学革命已经到来.md` |
| source | [Source - 工业软件会被AI绝杀吗？](../sources/2026-06-17-工业软件会被ai绝杀吗.md) | 已登记的ai资料，等待补充摘录或正文。 | `wiki/sources/2026-06-17-工业软件会被ai绝杀吗.md` |

## Next Network Actions

- Turn high-value `inbox` sources into source summaries.
- Promote recurring terms, methods, people, texts, tools, or datasets into concept/entity pages.
- Add explicit `Related` links between source summaries and concept pages, then rerun lint.
- Mark cross-disciplinary bridge candidates in the related pages instead of duplicating content across domains.

## Cross-Disciplinary Bridge Candidates

- 待补：这个学科中哪些概念需要连接到其他学科？
- 待补：哪些资料适合成为下一阶段跨学科 LLM Wiki 的桥接页面？
