---
title: 2026-04-09 Team Handoff Chat History
type: analysis
status: active
created: 2026-04-09
updated: 2026-04-09
summary: 对本次 LLM Wiki 搭建与西藏天文历算主题整理过程的会话级交接记录，供切换到 team 模式后继续使用。
tags: [analysis, handoff, chat-history, team]
sources: [llm-wiki.md, raw/sources/tibetan-astronomy-calendar/藏历的原理与实践-中文.md]
---

# 2026-04-09 Team Handoff Chat History

## Note

这是一份基于当前线程重建的工作记录，不是逐字聊天转录。它的目标是帮助后续 team 模式快速恢复上下文。

## 用户目标

- 搭建一个可长期维护的个人 LLM Wiki
- 后续同时使用 Codex 和 Claude Code
- 按学科管理资料，目前重点学科为：
  - 数学
  - 物理
  - 西藏天文历算
  - 现代天文学
- 已开始向西藏天文历算主线中 ingest 真实资料

## 已完成的仓库搭建

### 1. Starter kit 骨架

- 建立了 `raw/`、`wiki/`、`scripts/`、`templates/` 结构
- 建立了首页、索引、日志、inbox
- 加入了 `rebuild_index.py`、`lint_wiki.py`、`new_source.py`

### 2. 多代理规范

- 将 Codex 规则文件命名为 `CODEX-AGENTS.md`
- 将 Claude Code 规则文件命名为 `CLAUDE-AGENTS.md`
- 建立了私有临时目录：
  - `.codex/README.md`
  - `.claude/README.md`

### 3. 学科化原始资料目录

- `raw/sources/math/`
- `raw/sources/physics/`
- `raw/sources/tibetan-astronomy-calendar/`
- `raw/sources/modern-astronomy/`

- 学科目录说明保存在：
  `raw/sources/DOMAINS.md`

### 4. 学科总览页

- [Mathematics](../concepts/math.md)
- [Physics](../concepts/physics.md)
- [Tibetan Astronomy Calendar](../concepts/tibetan-astronomy-calendar.md)
- [Modern Astronomy](../concepts/modern-astronomy.md)

## 已 ingest 的真实资料

### 西藏天文历算

用户新增了原始资料：
`raw/sources/tibetan-astronomy-calendar/藏历的原理与实践-中文.md`

已完成对应知识层整理：

- source summary：
  [2026-04-07-zangli-principles-practice-zh.md](../sources/2026-04-07-zangli-principles-practice-zh.md)
- 概念页：
  [西藏时宪历交食推步](../concepts/tibetan-eclipse-calculation.md)

## 已完成的分析页

- [时宪历交食算法逐步拆解](./shixian-eclipse-step-by-step.md)
- [时轮历交食算法逐步拆解](./kalachakra-eclipse-step-by-step.md)

## 关键结论

### 1. 当前资料中的双重结构

- 原始资料不只涉及时宪历，也明确涉及时轮历在藏历中的位置
- 但这份文件对两者的“可拆解程度”不同：
  - 时宪历：有完整算例与原理说明，可做严格逐步拆解
  - 时轮历：当前文件主要提供比较性说明和结构线索，因此目前只做成算法骨架页

### 2. 当前最强主线

- 西藏天文历算方向目前最成熟的主线是“交食推步”
- 其中时宪历部分已经形成：
  - source
  - 概念页
  - 分析页

## 仍待完成的工作

- 为 `藏历的原理与实践-中文.md` 补完整书目信息
- 拆出“术语与单位表”
- 拆出“参数总表”
- 拆出“时宪历月食算例逐步页”
- 拆出“时宪历日食算例逐步页”
- 补一份时轮历原始算例，把时轮历算法骨架页升级成严格逐步拆解页
- 继续为数学、物理、现代天文学补第一批正式 source summary

## 建议的 team 模式起手动作

1. 先阅读 [Tibetan Astronomy Calendar](../concepts/tibetan-astronomy-calendar.md)
2. 再阅读 [Source - 藏历的原理与实践（中文）](../sources/2026-04-07-zangli-principles-practice-zh.md)
3. 然后对照两页分析：
   - [时宪历交食算法逐步拆解](./shixian-eclipse-step-by-step.md)
   - [时轮历交食算法逐步拆解](./kalachakra-eclipse-step-by-step.md)
4. 如果继续深挖当前主题，优先拆“术语表”和“参数总表”

## Sources

- `llm-wiki.md`
- `raw/sources/tibetan-astronomy-calendar/藏历的原理与实践-中文.md`
