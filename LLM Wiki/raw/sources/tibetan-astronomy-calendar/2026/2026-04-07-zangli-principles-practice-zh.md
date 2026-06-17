---
title: Source - 藏历的原理与实践（中文）
type: source
status: active
created: 2026-04-07
updated: 2026-04-07
summary: 一份以藏传时宪历交食推步为核心的中文资料，包含基本常数、符号表、月全食与日食算例及与现代结果的对照。
tags: [source, tibetan-astronomy-calendar, eclipse, shixian-calendar]
sources: [raw/sources/tibetan-astronomy-calendar/藏历的原理与实践-中文.md]
---

# Source - 藏历的原理与实践（中文）

## Source Profile

- File: `raw/sources/tibetan-astronomy-calendar/藏历的原理与实践-中文.md`
- Working title from filename: 《藏历的原理与实践》
- Observed content focus: 藏传时宪历中的交食推步
- Source condition: 当前文件没有完整 frontmatter 或书目信息，后续应补作者、版本、出处、页码范围

## What This Source Contains

- 一组交食推步基本数据，包括历元、周岁、朔策、朔应、太阳平行、太阳自行、太阴自行、罗喉距月等常数
- 一份译解用符号表，说明时间单位、角度单位与换算方式
- 一个月全食算例，案例日期为 1982-01-10
- 一个日食算例，案例日期为 1981-07-31
- 月全食推算结果与现代天文年历的误差对照

## Main Takeaways

- 这份资料很适合当作“交食推步流程”的种子 source，因为它同时给出常数、查表方法和完整算例。
- 文本展示的不是抽象历法原理，而是可执行的手工推算链条：先求根数，再求损益、距时、实望或实朔，最后判定食限与各阶段时刻。
- 交食推算高度依赖表格插值与符号体系统一，因此后续 wiki 需要特别重视术语页和表格说明页。
- 资料已经主动把传统算法结果与现代天文结果做了比较，这使它非常适合成为“传统历算 vs 现代天文学”对照研究的入口。

## Structured Notes

### 1. 基本常数层

- 文件开头列出了历元、岁首、首朔、周岁、朔策、朔应、闰周等基础参数。
- 还给出了太阳平行、太阳自行、太阴自行、罗喉距月、一小时月距日平行等推步用常数。
- 这些参数可以整理成单独的“交食推步参数表”页面。

### 2. 符号与单位层

- 资料明确解释了日、时、刻、分、秒、微、纤等时间单位和度、分、秒等角度单位。
- 符号表是阅读算例的前置条件，说明后续最好拆出一个“术语与单位表”概念页。

### 3. 推算流程层

- 月食算例中，流程大致包括：积年、积月、积日、求五项根数、求太阳/月亮损益数、求平距时与实距时、求实望、求定望、判食限、求食分、求初亏食既食甚生光复圆时刻。
- 日食算例展示了类似结构，但以实朔与日食判限为主。
- 两个算例一起说明：交食推步不是单步公式，而是一套带查表、符号判断与多阶段修正的程序。

### 4. 对照验证层

- 月全食算例末尾给出与 1982 年现代天文年历结果的对照。
- 误差以分钟级为主，这为后续比较研究提供了一个可追踪起点。

## Why It Matters For This Wiki

- 这是当前西藏天文历算主线中的第一份正式 source。
- 它适合衍生出至少两个概念页：
  - 交食推步总览
  - 术语与单位表
  - 参数总表
- 它也可以支撑一条对照研究路线：传统交食推算流程与现代天文学中的食分、食限、时刻计算如何对应。

## Related

- [Tibetan Astronomy Calendar](../concepts/tibetan-astronomy-calendar.md)
- [西藏时宪历交食推步](../concepts/tibetan-eclipse-calculation.md)
- [西藏交食推步术语与单位表](../concepts/tibetan-eclipse-terms-and-units.md)
- [交食推步参数总表](../concepts/tibetan-eclipse-parameters.md)
- [时宪历交食算法逐步拆解](../analyses/shixian-eclipse-step-by-step.md)
- [时轮历交食算法逐步拆解](../analyses/kalachakra-eclipse-step-by-step.md)
- [Modern Astronomy](../concepts/modern-astronomy.md)
- [Mathematics](../concepts/math.md)

## Sources

- `raw/sources/tibetan-astronomy-calendar/藏历的原理与实践-中文.md`
