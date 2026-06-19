---
title: Skill
type: concept
status: active
created: 2026-06-17
updated: 2026-06-18
summary: Skill 是 AI Agent 可按需加载的单个能力包，用来封装某类任务的说明、流程、脚本和资源。
tags: [ai智能体, auto-concept]
sources: [wiki/sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md]
---

# Skill

## Working Definition

- Skill 是一个可被 AI Agent 按需加载的能力包。它把某类任务的操作说明、流程、脚本、模板、示例和资源组织在一起。
- 一个 Skill 通常回答的是：“遇到这类任务时，Agent 应该调用哪些知识、遵循哪些步骤、使用哪些工具？”
- Skill 与 MCP 的区别在于：MCP 定义工具和数据如何被连接，Skill 定义任务如何被执行。一个 Skill 可以调用 MCP 工具，但 Skill 本身不是协议。
- 在本知识库中，Skill 是理解 Agent 能力扩展、工作流封装和非模型层智能的重要概念。

## Why It Matters

- 它让 Agent 的能力可以被打包、复用和版本化，而不是每次都靠临时提示词。
- 它把隐性的工作流知识显性化，让人可以检查、改进和迁移。
- 它也是“模型能力”和“系统能力”之间的重要连接点：模型负责推理，Skill 提供任务上下文和执行结构。

## Source-Derived Evidence

- [Agent Skills 终极指南：入门、精通、预测](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md): 🎐 卷首语 应该是全网最好的 Skills 中文指南与教程 ，全文 1.
- [Agent Skills 终极指南：入门、精通、预测](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md): 2w 字，包含了我对 Skills 的完整应用思考。
- [Agent Skills 终极指南：入门、精通、预测](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md): 巧借通用 Agent 内核，只靠 Skills 设计，就能低成本创造具有通用 AI 智能上限的垂直 Agent 应用。

## Source-Derived Relations

- `Skills` --是--> `Skill` ([source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 🎐 卷首语 应该是全网最好的 Skills 中文指南与教程 ，全文 1.)
- `Skills` --相关--> `Skill` ([source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 2w 字，包含了我对 Skills 的完整应用思考。)
- `AI` --相关--> `Skill` ([source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 一个好 Skill 能发挥的智能效果，甚至能轻松等同、超越完整的 AI 产品。)
- `Skills` --属于--> `Skill` ([source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 任何不懂技术的人，都能开发属于自己的 Skills。)
- `Agent` --相关--> `Skill` ([source](../sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md); evidence: 在研读 Anthropic 官方技术博客，与持续 Agent Skill 实验之后，形成了 这份全网最完整的 Skill 指南 ，包含： 1.)

## Open Questions

- 这个概念是否应该保留为独立页面，还是并入更大的主题页？
- 它和同学科其他概念的层级关系是什么？
- 是否存在跨学科桥接价值？

## Related

- [ai智能体 Knowledge Network](../domains/ai智能体.md)

## Sources

- `wiki/sources/2026-06-17-agent-skills-终极指南-入门-精通-预测.md`
