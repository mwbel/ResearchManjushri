---
title: 西藏时宪历交食推步
type: concept
status: active
created: 2026-04-07
updated: 2026-04-07
summary: 对西藏时宪历中日月食推步流程的概念化整理，涵盖常数、查表、损益修正、判食限与食时求法。
tags: [tibetan-astronomy-calendar, eclipse, shixian-calendar, calculation]
sources: [raw/sources/tibetan-astronomy-calendar/藏历的原理与实践-中文.md]
---

# 西藏时宪历交食推步

## What This Page Covers

这页整理西藏时宪历中用于推算月食与日食的一条核心工作流。目标不是复制原文每一步公式，而是把整套方法拆成便于持续维护的知识结构。

## Core Structure

### 1. 基础数据

- 推步以一组固定常数起步，例如历元、周岁、朔策、朔应、太阳平行、太阳自行、太阴自行、罗喉距月等。
- 这些常数决定了后续积月、根数和交周相关计算的基准。

### 2. 根数计算

- 算例首先根据积年、积月、积日等中间量，求出平望根或平朔根。
- 接着分别求太阳平行根、太阳自行根、太阴自行根、罗月距根等基础量。
- 这一步可以理解为把“历元以来的累计位置”转成当前案例月的工作起点。

### 3. 查表与损益修正

- 文本中的多个表用于根据宫、度和余量做插值。
- 太阳损益数、太阴损益数、实自行、时差等都不是直接公式一次得出，而是“查表 + 秒差插值 + 正负判断”的组合。
- 因此，阅读这类资料的关键不只是公式，还包括表格结构和正负号规则。

### 4. 距时与实望/实朔

- 通过日月损益数得到平距时、实距时，再推进到实望或实朔。
- 这是把平行位置修正成实际用时的重要阶段。

### 5. 判食与分阶段时刻

- 算出实交周或相关距弧后，需要先判定是否进入食限。
- 若进入，则继续求食甚距纬、食分、初亏、食既、食甚、生光、复圆等时刻。
- 这说明“有无食”与“食到什么程度、发生在何时”是两个连续阶段。

## Why This Matters

- 交食推步是西藏天文历算中最适合做结构化 wiki 的主题之一，因为它天然包含参数表、术语表、流程图和案例。
- 它也非常适合做跨学科连接：
  - 与 [Mathematics](./math.md) 连接在于数值累积、比例、插值与单位换算
  - 与 [Modern Astronomy](./modern-astronomy.md) 连接在于食限、食分和时刻可以与现代天文结果比较

## Current Source Evidence

- 月全食案例：1982-01-10
- 日食案例：1981-07-31
- 月全食案例中已出现与现代天文年历结果的误差对照

## Pages This Suggests Next

- [西藏交食推步术语与单位表](./tibetan-eclipse-terms-and-units.md)
- [交食推步参数总表](./tibetan-eclipse-parameters.md)
- 月食算例拆解
- 日食算例拆解
- 传统交食推步与现代天文学对照

## Current Analysis Pages

- [时宪历交食算法逐步拆解](../analyses/shixian-eclipse-step-by-step.md)
- [时轮历交食算法逐步拆解](../analyses/kalachakra-eclipse-step-by-step.md)

## Current Reference Pages

- [西藏交食推步术语与单位表](./tibetan-eclipse-terms-and-units.md)
- [交食推步参数总表](./tibetan-eclipse-parameters.md)

## Open Questions

- 同一推步流程在不同传承、版本或寺院资料中是否存在常数差异？
- 这些表格能否整理成更适合机器检索和比较的结构化格式？
- 对照现代天文结果时，误差主要来自参数、表格近似，还是历法体系假设？

## Related

- [Tibetan Astronomy Calendar](./tibetan-astronomy-calendar.md)
- [Source - 藏历的原理与实践（中文）](../sources/2026-04-07-zangli-principles-practice-zh.md)
- [西藏交食推步术语与单位表](./tibetan-eclipse-terms-and-units.md)
- [交食推步参数总表](./tibetan-eclipse-parameters.md)
- [时宪历交食算法逐步拆解](../analyses/shixian-eclipse-step-by-step.md)
- [时轮历交食算法逐步拆解](../analyses/kalachakra-eclipse-step-by-step.md)
- [Mathematics](./math.md)
- [Modern Astronomy](./modern-astronomy.md)

## Sources

- `raw/sources/tibetan-astronomy-calendar/藏历的原理与实践-中文.md`
