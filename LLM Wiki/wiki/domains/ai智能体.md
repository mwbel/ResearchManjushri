---
title: ai智能体 Knowledge Network
type: domain
status: active
created: 2026-06-17
updated: 2026-06-24
summary: ai智能体 单学科知识网络入口，串联网页文章、本地资料、source summary、concept、analysis 与待办问题。
tags: [ai智能体, domain-network]
sources: []
---

# ai智能体 Knowledge Network

这页是单学科知识网络的入口。它把原始资料、网页链接、本地资料位置、已沉淀的 wiki 页面和下一步待处理动作放在同一张可维护地图里。

## Current Shape

- Registered raw sources: 9
- Connected wiki pages: 60
- Inbox sources waiting for ingest: 1
- Generated on: 2026-06-24

## How To Add Knowledge

- Web article: `python3 scripts/new_source.py --domain ai智能体 --kind article --title "标题" --url "https://..."`
- Local file: `python3 scripts/new_source.py --domain ai智能体 --kind paper --title "标题" --local-path "/absolute/path/to/file.pdf"`
- After adding sources, run `python3 scripts/rebuild_domain_network.py` and then `python3 scripts/rebuild_index.py`.
- When a source is important, create or update a `wiki/sources/...` source summary and connect it to concept/entity/analysis pages.

## Knowledge Map

```mermaid
flowchart LR
    D["ai智能体"]
    R1["raw: Agent Skills 终极指南：入门、精通、预测"] --> D
    R2["raw: Agentic AI进入正规军时代：读懂Agentic AI全景图…"] --> D
    R3["raw: AI推理能力仅有人类的0.37%？ARC-AGI-3揭示人工智能最…"] --> D
    R4["raw: attention is all you need"] --> D
    R5["raw: Harness 今天的机会与价值"] --> D
    R6["raw: 【万字长文】Claude Skills完全指南：从概念到实战"] --> D
    R7["raw: 对Transformer的批判2：Transformer能输出知识吗"] --> D
    R8["raw: 最新！万字综述Harness革命！"] --> D
    D --> W1["concept: 大语言模型"]
    D --> W2["concept: Agent Skills"]
    D --> W3["concept: Skills"]
    D --> W4["concept: Anthropic"]
    D --> W5["concept: Claude API"]
    D --> W6["concept: Claude"]
    D --> W7["concept: Crea"]
    D --> W8["concept: Cursor"]
    D --> W9["concept: Github"]
    D --> W10["concept: Mulerun"]
    D --> W11["concept: Noise Leading In"]
    D --> W12["concept: Part"]
```

## Concept Graph

```mermaid
flowchart LR
    C1A["LLM"] -- "相关" --> C1B["语言模型"]
    C2A["Skill"] -- "是" --> C2B["Skill"]
    C3A["Skill"] -- "相关" --> C3B["Skill"]
    C4A["AI"] -- "相关" --> C4B["Skill"]
    C5A["Skill"] -- "是" --> C5B["Agent"]
    C6A["Skill"] -- "是" --> C6B["Crea"]
    C7A["Skill"] -- "是" --> C7B["Claude Skills"]
    C8A["Skill"] -- "属于" --> C8B["Skill"]
    C9A["Agent"] -- "相关" --> C9B["Anthropic"]
    C10A["AI"] -- "相关" --> C10B["Claude API"]
    C11A["AI"] -- "是" --> C11B["Claude"]
    C12A["AI"] -- "相关" --> C12B["Claude"]
    C13A["注意力机制"] -- "产生" --> C13B["NLI"]
    C14A["AI"] -- "是" --> C14B["PCB"]
    C15A["Transformer"] -- "属于" --> C15B["不完全的归纳法"]
    C16A["Transformer"] -- "属于" --> C16B["休谟"]
    C17A["AI"] -- "是" --> C17B["OpenAI"]
    C18A["Transformer"] -- "缺乏" --> C18B["真信念且证成"]
```

## Concept Relations

| Source Concept | Relation | Target Concept | Evidence |
| --- | --- | --- | --- |
| LLM | 相关 | 语言模型 | [source](../sources/2026-06-17-人工智能的数学革命已经到来.md); evidence: 而在另一些情形中，与ChatGPT、Claude或Gemini等大语言模型的深入对话则催生了全新的证明思路。 |
| Skill | 是 | Skill | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 🎐 卷首语 应该是全网最好的 Skills 中文指南与教程 ，全文 1. |
| Skill | 相关 | Skill | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 2w 字，包含了我对 Skills 的完整应用思考。 |
| AI | 相关 | Skill | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 巧借通用 Agent 内核，只靠 Skills 设计，就能低成本创造具有通用 AI 智能上限的垂直 Agent 应用。 |
| Skill | 是 | Agent | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 顺便给朋友宇森、付铖的 Mulerun 打个广，他们在做全球性的 Agent 开发与交易市场，即将支持 Crea… 🎐 卷首语 应该是全网最好的 Skills 中文指南与教程 ，全文 1. |
| Skill | 是 | Crea | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 顺便给朋友宇森、付铖的 Mulerun 打个广，他们在做全球性的 Agent 开发与交易市场，即将支持 Crea… 🎐 卷首语 应该是全网最好的 Skills 中文指南与教程 ，全文 1. |
| Skill | 是 | Claude Skills | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: @ 一泽Eze Claude Skills 的价值，还是被大大低估了。 |
| Skill | 属于 | Skill | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 任何不懂技术的人，都能开发属于自己的 Skills。 |
| Agent | 相关 | Anthropic | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 在研读 Anthropic 官方技术博客，与持续 Agent Skill 实验之后，形成了 这份全网最完整的 Skill 指南 ，包含： 1. |
| AI | 相关 | Claude API | [source](../sources/2026-06-17-万字长文-claude-skills完全指南-从概念到实战.md); evidence: 如果你用Claude Code、Claude API，或者对AI Agent感兴趣，这篇文章应该对你有用。 |
| AI | 是 | Claude | [source](../sources/2026-06-17-万字长文-claude-skills完全指南-从概念到实战.md); evidence: 用Claude Code自己构建Skills的人是一小撮，但想用AI解决实际问题、又没能力从零创建工作流的人，才是更大的群体。 |
| AI | 相关 | Claude | [source](../sources/2026-06-17-万字长文-claude-skills完全指南-从概念到实战.md); evidence: 如果你用Claude Code、Claude API，或者对AI Agent感兴趣，这篇文章应该对你有用。 |
| 注意力机制 | 产生 | NLI | [source](../sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md); evidence: 文章首先揭示注意力机制在本质上是一种结构化的噪声引入（Noise Leading In, NLI）​ 过程，其产生的权重分配具有内在的不稳定性和偏性。 |
| AI | 是 | PCB | [source](../sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md); evidence: 这种所谓的定义，作为 工程师把握手上做的这块板子（PCB）或者这段代码，未必没有实际意义，但是作为AI的定义就太儿戏了。 |
| Transformer | 属于 | 不完全的归纳法 | [source](../sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md); evidence: 其次，本文指出Transformer的工作机制属于不完全的归纳法，其结论建立在数据统计规律而非逻辑必然性之上，该问题在哲学上已被 休谟和波普尔进行了充分的批判论证。 |
| Transformer | 属于 | 休谟 | [source](../sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md); evidence: 其次，本文指出Transformer的工作机制属于不完全的归纳法，其结论建立在数据统计规律而非逻辑必然性之上，该问题在哲学上已被 休谟和波普尔进行了充分的批判论证。 |
| AI | 是 | OpenAI | [source](../sources/2026-06-17-全面解析-世界模型-定义-路线-实践与agi的更近一步.md); evidence: 而为了解决这个问题，OpenAI、谷歌、微软等大公司，Yann LeCun、李飞飞等顶尖学者都开始抢着研究同一件事，那就是——世界模型。 |
| Transformer | 缺乏 | 真信念且证成 | [source](../sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md); evidence: 最终，Transformer的输出是一种高度复杂的、数据驱动的信息结构，它缺乏知识所必需的“真信念且证成”等条件。 |
| Agent | 相关 | Article-Copilot | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 比如我自己做的 Article-Copilot，一个 skill 就实现了从素材处理到正文写作的 Agent 应用 |
| AI | 相关 | AI Partner Skill | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 又如 AI Partner Skill，让 通用 Agent 深度学习你的记忆，塑造懂你的 AI 伴侣，给到个性回应。 |
| Agent | 相关 | Agent Skill | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 在研读 Anthropic 官方技术博客，与持续 Agent Skill 实验之后，形成了 这份全网最完整的 Skill 指南 ，包含： 1. |
| AI | 相关 | Agent | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 巧借通用 Agent 内核，只靠 Skills 设计，就能低成本创造具有通用 AI 智能上限的垂直 Agent 应用。 |
| Agent | 相关 | Skill | [source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 在研读 Anthropic 官方技术博客，与持续 Agent Skill 实验之后，形成了 这份全网最完整的 Skill 指南 ，包含： 1. |
| Transformer | 构成 | AI | [source](../sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md); evidence: 摘要：“泛BP+Transformer”构成了这一代AI基础架构，泛BP已经被诺贝尔奖封印而昭彰天下，却是个有数十年历史的“资深技术”，有深入理解的人都知道Transformer才是这个魔术的核心道具，LLM的真正“新动能”。 |
| AI | 属于 | AI | [source](../sources/2026-06-17-人工智能的数学革命已经到来.md); evidence: 自动补充：这份资料属于「AI」资料库，用于补强《人工智能的数学革命已经到来》相关的核心观点、概念证据和学科网络关系。 |
| AI | 相关 | AI | [source](../sources/2026-06-17-人工智能的数学革命已经到来.md); evidence: 普林斯顿高等研究院的 Akshay Venkatesh 认为，随着AI模型成 人工智能正以极快的速度被用来证明新的数学成果。 |
| Transformer | 构成 | BP | [source](../sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md); evidence: 摘要：“泛BP+Transformer”构成了这一代AI基础架构，泛BP已经被诺贝尔奖封印而昭彰天下，却是个有数十年历史的“资深技术”，有深入理解的人都知道Transformer才是这个魔术的核心道具，LLM的真正“新动能”。 |
| Transformer | 构成 | LLM | [source](../sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md); evidence: 摘要：“泛BP+Transformer”构成了这一代AI基础架构，泛BP已经被诺贝尔奖封印而昭彰天下，却是个有数十年历史的“资深技术”，有深入理解的人都知道Transformer才是这个魔术的核心道具，LLM的真正“新动能”。 |
| LLM | 属于 | AI | [source](../sources/2026-06-17-agentic-ai进入正规军时代-读懂agentic-ai全景图与畅想一人公司opc的未来.md); evidence: 如果说去年大家还在为大模型（LLM）的参数量狂欢，那今年整个技术圈的风向已经彻底变了，特别是近期小龙虾OpenClaw的火爆，言必称Agentic AI（代理式人工智能或智能… 自动补充：这份资料属于「ai」资料库，用于补强《Agenti… |
| LLM | 是 | AI | [source](../sources/2026-06-17-agentic-ai进入正规军时代-读懂agentic-ai全景图与畅想一人公司opc的未来.md); evidence: 如果说去年大家还在为大模型（LLM）的参数量狂欢，那今年整个技术圈的风向已经彻底变了，特别是近期小龙虾OpenClaw的火爆，言必称Agentic AI（代理式人工智能或智能体人工智能）。 |

## Source Intake

| Status | Kind | Title | Locator | Raw File |
| --- | --- | --- | --- | --- |
| active | article | [Agent Skills 终极指南：入门、精通、预测](../../raw/sources/ai智能体/2026/2026-06-17-agent-skills-终极指南-入门-精通-预测.md) | [web](https://mp.weixin.qq.com/s/jUylk813LYbKw0sLiIttTQ) | `raw/sources/ai智能体/2026/2026-06-17-agent-skills-终极指南-入门-精通-预测.md` |
| inbox | article | [Agentic AI进入正规军时代：读懂Agentic AI全景图与畅想一人公司OPC的未来](../../raw/sources/ai智能体/2026/2026-06-17-agentic-ai进入正规军时代-读懂agentic-ai全景图与畅想一人公司opc的未来.md) | [web](https://mp.weixin.qq.com/s/jVcYKvy585KYzlbLOAb4HQ) | `raw/sources/ai智能体/2026/2026-06-17-agentic-ai进入正规军时代-读懂agentic-ai全景图与畅想一人公司opc的未来.md` |
| active | article | [AI推理能力仅有人类的0.37%？ARC-AGI-3揭示人工智能最致命的盲区](../../raw/sources/ai智能体/2026/2026-06-17-ai推理能力仅有人类的0-37-arc-agi-3揭示人工智能最致命的盲区.md) | [web](https://mp.weixin.qq.com/s/-WjIzxr8xhms4CeXlbObVw) | `raw/sources/ai智能体/2026/2026-06-17-ai推理能力仅有人类的0-37-arc-agi-3揭示人工智能最致命的盲区.md` |
| active | paper | [attention is all you need](../../raw/sources/ai智能体/2026/2026-06-17-attention-is-all-you-need.md) | 未登记 | `raw/sources/ai智能体/2026/2026-06-17-attention-is-all-you-need.md` |
| active | article | [Harness 今天的机会与价值](../../raw/sources/ai智能体/2026/2026-06-17-harness-今天的机会与价值.md) | [web](https://mp.weixin.qq.com/s/FSnvyRDmkgXQzJtC-cwJGw) | `raw/sources/ai智能体/2026/2026-06-17-harness-今天的机会与价值.md` |
| active | article | [【万字长文】Claude Skills完全指南：从概念到实战](../../raw/sources/ai智能体/2026/2026-06-17-万字长文-claude-skills完全指南-从概念到实战.md) | [web](https://mp.weixin.qq.com/s/x9UpqjuYzLb7I2ZZ932bNg) | `raw/sources/ai智能体/2026/2026-06-17-万字长文-claude-skills完全指南-从概念到实战.md` |
| active | paper | [对Transformer的批判2：Transformer能输出知识吗](../../raw/sources/ai智能体/2026/2026-06-17-对transformer的批判2-transformer能输出知识吗.md) | `/Users/Min369/Documents/同步空间/Manju/AIProjects/ResearchManjusi/LLM Wiki/raw/assets/uploads/ai智能体/2026/对transformer的批判2-transformer能输出知识吗.docx` | `raw/sources/ai智能体/2026/2026-06-17-对transformer的批判2-transformer能输出知识吗.md` |
| active | article | [最新！万字综述Harness革命！](../../raw/sources/ai智能体/2026/2026-06-17-最新-万字综述harness革命.md) | [web](https://mp.weixin.qq.com/s/0CTwb4aEr5mWwsdRdwzwkw) | `raw/sources/ai智能体/2026/2026-06-17-最新-万字综述harness革命.md` |
| active | article | [第196期：什么是蒸馏？什么是知识蒸馏？](../../raw/sources/ai智能体/2026/2026-06-17-第196期-什么是蒸馏-什么是知识蒸馏.md) | [web](https://mp.weixin.qq.com/s/mQL4ZQl82xng09vW2ipncQ) | `raw/sources/ai智能体/2026/2026-06-17-第196期-什么是蒸馏-什么是知识蒸馏.md` |

## Wiki Knowledge Layer

| Type | Title | Summary | Wiki Page |
| --- | --- | --- | --- |
| concept | [大语言模型](../.archive/concepts/20260624-125416-120a3982-大语言模型.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-125416-120a3982-大语言模型.md` |
| concept | [Agent Skills](../.archive/concepts/20260624-200519-38a18c57-agent-skills.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200519-38a18c57-agent-skills.md` |
| concept | [Skills](../.archive/concepts/20260624-200610-610a944f-skills.md) | Skills 是 AI Agent 可按需加载的能力包，用来把某类任务的说明、流程、脚本和资源封装成稳定的执行能力。 | `wiki/.archive/concepts/20260624-200610-610a944f-skills.md` |
| concept | [Anthropic](../.archive/concepts/20260624-200619-299233cc-anthropic.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200619-299233cc-anthropic.md` |
| concept | [Claude API](../.archive/concepts/20260624-200625-96ace9c8-claude-api.md) | 从资料《【万字长文】Claude Skills完全指南：从概念到实战》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200625-96ace9c8-claude-api.md` |
| concept | [Claude](../.archive/concepts/20260624-200629-3b8f8261-claude.md) | 从资料《【万字长文】Claude Skills完全指南：从概念到实战》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200629-3b8f8261-claude.md` |
| concept | [Crea](../.archive/concepts/20260624-200632-b39ac988-crea.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200632-b39ac988-crea.md` |
| concept | [Cursor](../.archive/concepts/20260624-200635-c0ff1df4-cursor.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200635-c0ff1df4-cursor.md` |
| concept | [Github](../.archive/concepts/20260624-200639-7a590d37-github.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200639-7a590d37-github.md` |
| concept | [Mulerun](../.archive/concepts/20260624-200656-6e3dc9c3-mulerun.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200656-6e3dc9c3-mulerun.md` |
| concept | [Noise Leading In](../.archive/concepts/20260624-200703-ac2e901e-noise-leading-in.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200703-ac2e901e-noise-leading-in.md` |
| concept | [Part](../.archive/concepts/20260624-200713-8e094f1c-part.md) | 从资料《【万字长文】Claude Skills完全指南：从概念到实战》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200713-8e094f1c-part.md` |
| concept | [PCB](../.archive/concepts/20260624-200719-7a26cf2a-pcb.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200719-7a26cf2a-pcb.md` |
| concept | [Simon](../.archive/concepts/20260624-200724-b3faef7a-simon.md) | 从资料《【万字长文】Claude Skills完全指南：从概念到实战》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200724-b3faef7a-simon.md` |
| concept | [VS Code](../.archive/concepts/20260624-200727-fb7a9b0b-vs-code.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200727-fb7a9b0b-vs-code.md` |
| concept | [不完全的归纳法](../.archive/concepts/20260624-200740-25cca01f-不完全的归纳法.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200740-25cca01f-不完全的归纳法.md` |
| concept | [休谟](../.archive/concepts/20260624-200742-42250a4a-休谟.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200742-42250a4a-休谟.md` |
| concept | [图灵](../.archive/concepts/20260624-200744-4b31fb22-图灵.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200744-4b31fb22-图灵.md` |
| concept | [OpenAI](../.archive/concepts/20260624-200748-79ff636a-openai.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200748-79ff636a-openai.md` |
| concept | [波普尔](../.archive/concepts/20260624-200751-452f0c3d-波普尔.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200751-452f0c3d-波普尔.md` |
| concept | [真信念且证成](../.archive/concepts/20260624-200803-e4fa95fc-真信念且证成.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200803-e4fa95fc-真信念且证成.md` |
| concept | [知识](../.archive/concepts/20260624-200805-f232f3ae-知识.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200805-f232f3ae-知识.md` |
| concept | [Code](../.archive/concepts/20260624-200812-1c0e997a-code.md) | 从资料《【万字长文】Claude Skills完全指南：从概念到实战》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200812-1c0e997a-code.md` |
| concept | [Creator](../.archive/concepts/20260624-200814-9926ab68-creator.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200814-9926ab68-creator.md` |
| concept | [泛BP](../.archive/concepts/20260624-200815-55e2737a-泛bp.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200815-55e2737a-泛bp.md` |
| concept | [结构化的噪声引入](../.archive/concepts/20260624-200821-ab2d9f97-结构化的噪声引入.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200821-ab2d9f97-结构化的噪声引入.md` |
| concept | [运作机制](../.archive/concepts/20260624-200836-53a76b18-运作机制.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200836-53a76b18-运作机制.md` |
| concept | [知识论](../.archive/concepts/20260624-200840-451d888d-知识论.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200840-451d888d-知识论.md` |
| concept | [Article-Copilot](../.archive/concepts/20260624-200845-f96c6d10-article-copilot.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200845-f96c6d10-article-copilot.md` |
| concept | [AI Partner Skill](../.archive/concepts/20260624-200850-68cdb913-ai-partner-skill.md) | 从资料《Agent Skills 终极指南：入门、精通、预测》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/.archive/concepts/20260624-200850-68cdb913-ai-partner-skill.md` |
| concept | [Agent Skill](../concepts/agent-skill.md) | Agent Skill 是 ai智能体 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/agent-skill.md` |
| concept | [Agent](../concepts/agent.md) | Agent 是 ai智能体 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/agent.md` |
| concept | [AI Agent](../concepts/ai-agent.md) | AI Agent 是 ai智能体 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/ai-agent.md` |
| concept | [AI](../concepts/ai.md) | AI 是 ai 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/ai.md` |
| concept | [ai智能体](../concepts/ai智能体.md) | ai智能体 是 ai智能体 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/ai智能体.md` |
| concept | [BP](../concepts/bp.md) | BP 是 ai智能体 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/bp.md` |
| concept | [Claude Skills](../concepts/claude-skills.md) | Claude Skills 是 ai智能体 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/claude-skills.md` |
| concept | [LLM](../concepts/llm.md) | LLM 是 ai 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/llm.md` |
| concept | [MCP](../concepts/mcp.md) | MCP 是 ai智能体 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/mcp.md` |
| concept | [NLI](../concepts/nli.md) | 从资料《对Transformer的批判2：Transformer能输出知识吗》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。 | `wiki/concepts/nli.md` |
| concept | [Skill](../concepts/skill.md) | Skill 是 AI Agent 可按需加载的单个能力包，用来封装某类任务的说明、流程、脚本和资源。 | `wiki/concepts/skill.md` |
| concept | [Transformer](../concepts/transformer.md) | Transformer 是 ai智能体 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/transformer.md` |
| concept | [归纳法](../concepts/归纳法.md) | 归纳法 是 ai智能体 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/归纳法.md` |
| concept | [注意力机制](../concepts/注意力机制.md) | 注意力机制 是 ai智能体 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/注意力机制.md` |
| concept | [语言模型](../concepts/语言模型.md) | 语言模型 是 ai 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。 | `wiki/concepts/语言模型.md` |
| source | [Source - Agent Skills 终极指南：入门、精通、预测](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md) | 🎐 卷首语 应该是全网最好的 Skills 中文指南与教程 ，全文 1.2w 字，包含了我对 Skills 的完整应用思考。 巧借通用 Agent 内核，只靠 Skills 设计，就能低成本创造具有通用 AI 智能上限的垂直 Agent 应用。 顺便给朋友宇森、付铖的 Mulerun 打个广，他们在做全球性的 Agent 开发与交易市场，即将支持 Crea… | `wiki/sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md` |
| source | [Source - AI推理能力仅有人类的0.37%？ARC-AGI-3揭示人工智能最致命的盲区](../sources/2026-06-17-ai推理能力仅有人类的0-37-arc-agi-3揭示人工智能最致命的盲区.md) | 一个悄然上线、没有任何头条新闻的测试，却让硅谷核心圈的很多人在深夜辗转难眠。 这个测试叫 ARC-AGI-3，2026年3月25日发布。它的结论只有一句话，却重如千钧： 当今世界上最强大的AI，面对全新环境的推理能力，只有人类的0.37%。 不是37%，是0.37%。 --- 一片凯歌中突然出现的"镜子" 过去两年，AI刷榜的速度近乎疯狂。今天某个模型登上… | `wiki/sources/2026-06-17-ai推理能力仅有人类的0-37-arc-agi-3揭示人工智能最致命的盲区.md` |
| source | [Source - attention is all you need](../sources/2026-06-17-attention-is-all-you-need.md) | Sciverse 学术检索导入，用于补强当前知识网络的论文证据。 The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. The… | `wiki/sources/2026-06-17-attention-is-all-you-need.md` |
| source | [Source - Harness 今天的机会与价值](../sources/2026-06-17-harness-今天的机会与价值.md) | 摘要 Harness 已成为产业共识,前沿模型持续逼近静态智能天花板。在此条件下,Harness 的经济价值由「扩展能力上限」转向「保障执行下限」:同一任务上,其对模型成绩的边际贡献随模型变强而系统性收窄,常见任务由弱模型时代的约 30% 压缩至强模型时代的约 7% 更长、更动态、更安全的前沿任务与跨重复执行的一致性是 Harness 的长存价值。如 Op… | `wiki/sources/2026-06-17-harness-今天的机会与价值.md` |
| source | [Source - 【万字长文】Claude Skills完全指南：从概念到实战](../sources/2026-06-17-万字长文-claude-skills完全指南-从概念到实战.md) | 1万字，国内最完整的Skills指南。想了解Skills是什么、怎么用、怎么建，看这一篇就够了。 内容很长，建议先点赞、收藏再慢慢读～ 说起来，Skills这个功能我关注挺久了。 去年10月Anthropic发布Skills的时候，我的判断是：这东西会火，但还早。 三个月过去，情况完全不一样了。 2025年12月，Anthropic把Skills做成了开放… | `wiki/sources/2026-06-17-万字长文-claude-skills完全指南-从概念到实战.md` |
| source | [Source - 对Transformer的批判2：Transformer能输出知识吗](../sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md) | Transformer的输出是知识吗？ 摘要：“泛BP+Transformer”构成了这一代AI基础架构，泛BP已经被诺贝尔奖封印而昭彰天下，却是个有数十年历史的“资深技术”，有深入理解的人都知道Transformer才是这个魔术的核心道具，LLM的真正“新动能”。批判不是批评，批评是负面的，而批判则是深刻洞察之后的判断。Transformer太重要了！我… | `wiki/sources/2026-06-17-对transformer的批判2-transformer能输出知识吗.md` |
| source | [Source - 最新！万字综述Harness革命！](../sources/2026-06-17-最新-万字综述harness革命.md) | 已登记的ai智能体资料，等待补充摘录或正文。 | `wiki/sources/2026-06-17-最新-万字综述harness革命.md` |
| source | [Source - 第196期：什么是蒸馏？什么是知识蒸馏？](../sources/2026-06-17-第196期-什么是蒸馏-什么是知识蒸馏.md) | “ “ 鲸吞阅、精输出，内修外求，日拱一卒，慢慢变富。”——半亩云田 ” “ 普通的人改变结果，优秀的人改变原因，顶级高手改变模型 ”。 各位同学，大家好，我是你们的 老朋友Fisher。 你应该感觉到了，手机里的AI助手好像“ 开窍 ”了，比以前“聪明”点了。 以前，你问Siri、小爱同学“今天天气怎么样”，它要转圈、联网，有时候还答非所问。 现在，你断… | `wiki/sources/2026-06-17-第196期-什么是蒸馏-什么是知识蒸馏.md` |
| source | [Source - Agent Skills 终极指南：入门、精通、预测](../sources/ai智能体/2026-06-17-agent-skills-终极指南-入门-精通-预测-ebe9cbe567.md) | 🎐 卷首语 应该是全网最好的 Skills 中文指南与教程 ，全文 1.2w 字，包含了我对 Skills 的完整应用思考。 | `wiki/sources/ai智能体/2026-06-17-agent-skills-终极指南-入门-精通-预测-ebe9cbe567.md` |
| source | [Source - AI推理能力仅有人类的0.37%？ARC-AGI-3揭示人工智能最致命的盲区](../sources/ai智能体/2026-06-17-ai推理能力仅有人类的0-37-arc-agi-3揭示人工智能最致命的盲区-f1d13e80f7.md) | 自动补充：这份资料属于「ai智能体」资料库，用于补强《AI推理能力仅有人类的0.37%？ARC-AGI-3揭示人工智能最致命的盲区》相关的核心观点、概念证据和学科网络关系。 | `wiki/sources/ai智能体/2026-06-17-ai推理能力仅有人类的0-37-arc-agi-3揭示人工智能最致命的盲区-f1d13e80f7.md` |
| source | [Source - attention is all you need](../sources/ai智能体/2026-06-17-attention-is-all-you-need-b3cf7f40c4.md) | Sciverse 学术检索导入，用于补强当前知识网络的论文证据。 | `wiki/sources/ai智能体/2026-06-17-attention-is-all-you-need-b3cf7f40c4.md` |
| source | [Source - Harness 今天的机会与价值](../sources/ai智能体/2026-06-17-harness-今天的机会与价值-1f518612c6.md) | 自动补充：这份资料属于「AI智能体」资料库，用于补强《Harness 今天的机会与价值》相关的核心观点、概念证据和学科网络关系。 | `wiki/sources/ai智能体/2026-06-17-harness-今天的机会与价值-1f518612c6.md` |
| source | [Source - 【万字长文】Claude Skills完全指南：从概念到实战](../sources/ai智能体/2026-06-17-万字长文-claude-skills完全指南-从概念到实战-2dffbb86af.md) | 自动补充：这份资料属于「ai智能体」资料库，用于补强《【万字长文】Claude Skills完全指南：从概念到实战》相关的核心观点、概念证据和学科网络关系。 | `wiki/sources/ai智能体/2026-06-17-万字长文-claude-skills完全指南-从概念到实战-2dffbb86af.md` |
| source | [Source - 对Transformer的批判2：Transformer能输出知识吗](../sources/ai智能体/2026-06-17-对transformer的批判2-transformer能输出知识吗-9bfc895f9a.md) | 自动补充：这份资料属于「ai智能体」资料库，用于补强《对Transformer的批判2：Transformer能输出知识吗》相关的核心观点、概念证据和学科网络关系。 | `wiki/sources/ai智能体/2026-06-17-对transformer的批判2-transformer能输出知识吗-9bfc895f9a.md` |
| source | [Source - 最新！万字综述Harness革命！](../sources/ai智能体/2026-06-17-最新-万字综述harness革命-6afeea086e.md) | 自动补充：这份资料属于「ai智能体」资料库，用于补强《最新！万字综述Harness革命！》相关的核心观点、概念证据和学科网络关系。 | `wiki/sources/ai智能体/2026-06-17-最新-万字综述harness革命-6afeea086e.md` |

## Next Network Actions

- Turn high-value `inbox` sources into source summaries.
- Promote recurring terms, methods, people, texts, tools, or datasets into concept/entity pages.
- Add explicit `Related` links between source summaries and concept pages, then rerun lint.
- Mark cross-disciplinary bridge candidates in the related pages instead of duplicating content across domains.

## Cross-Disciplinary Bridge Candidates

- 待补：这个学科中哪些概念需要连接到其他学科？
- 待补：哪些资料适合成为下一阶段跨学科 LLM Wiki 的桥接页面？
