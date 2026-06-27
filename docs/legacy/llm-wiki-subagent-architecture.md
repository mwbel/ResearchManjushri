结论：**你的项目需要 subagent，但核心不是“多 Agent 群聊”，而是“可观测 ingest 流水线 + 函数式 subagent + 确定性数据库写入”。**
下面是把前两个回复整合后的统一版本，可直接作为项目架构设计稿使用。

# LLM Wiki 个人多学科智能体：自动整理与 SubAgent 架构方案

## 1. 总体判断

当前项目的核心目标不是普通 RAG，而是把“我看过 / 收藏过的资料”编译成一个可以继续阅读、检索、跳转、连接和扩展的个人多学科知识网络。

因此，系统不应只做：

```text
资料导入 → 切 chunk → 向量化 → 问答
```

而应做：

```text
资料导入
→ 正文读取
→ 内容清洗
→ 来源摘要
→ 学科分类
→ 候选概念抽取
→ 候选关系抽取
→ Wiki 页面生成
→ 图谱更新
→ 检索索引更新
→ 人工纠错反哺
```

当前“导入资料不能自动整理”的根本问题，大概率不是 LLM 能力不够，而是导入、解析、摘要、概念抽取、关系抽取、图谱更新、索引更新没有被拆成可观测、可重跑、可回滚的流水线。

------

## 2. 核心架构结论

推荐架构是：

```text
Knowledge Compiler Orchestrator 主控编排器
  |
  |-- Parser Worker
  |-- Cleaner SubAgent
  |-- Domain Classifier SubAgent
  |-- Source Summary SubAgent
  |-- Concept Extraction SubAgent
  |-- Concept Merge SubAgent
  |-- Relation Extraction SubAgent
  |-- Wiki Page Compiler SubAgent
  |-- Quality Review SubAgent
  |-- Graph / Index Writer
  |-- Correction Memory Agent
```

核心原则：

```text
SubAgent 负责语义判断、抽取、生成候选结果。
后端代码负责状态机、任务队列、数据库写入、重试、回滚、索引更新。
```

不要让 LLM subagent 直接改数据库。
LLM 只输出结构化 JSON，由后端校验后再写入数据库。

------

## 3. 为什么需要 SubAgent

这个项目的“自动整理”本质是多个不同认知任务的串联。

| 任务                       | 性质            | 是否适合 SubAgent   |
| -------------------------- | --------------- | ------------------- |
| 网页 / docx / 微信正文读取 | 工程解析        | 不一定，需要 worker |
| 正文清洗                   | 规则 + LLM 辅助 | 适合                |
| 学科分类                   | 语义判断        | 适合                |
| 来源摘要                   | 文本理解        | 适合                |
| 候选概念抽取               | 知识抽取        | 很适合              |
| 概念去重 / 合并            | 语义消歧        | 很适合              |
| 概念关系抽取               | 图谱构建        | 很适合              |
| Wiki 页面生成              | 知识编译        | 很适合              |
| 质量检查                   | 审核判断        | 适合                |
| 数据库写入                 | 确定性工程任务  | 不适合 LLM          |
| 向量索引更新               | 工程任务        | 不适合 LLM          |
| 图谱写入                   | 工程任务        | 不适合 LLM          |

所以结论是：

```text
需要 SubAgent，但应做成流水线式、函数式、可观测 SubAgent。
不要做成自治式多 Agent 群聊。
```

------

## 4. 不推荐的架构

不推荐：

```text
资料导入后
→ Agent A 阅读
→ Agent B 评论
→ Agent C 反驳
→ Agent D 总结
→ Agent E 决定是否入库
```

这种“群聊式多 Agent”会带来：

| 问题           | 后果                     |
| -------------- | ------------------------ |
| 成本高         | 每篇资料多轮 LLM 调用    |
| 延迟高         | 导入体验差               |
| 难调试         | 不知道哪个 Agent 出错    |
| 输出不稳定     | 同一篇资料多次结果不一致 |
| 容易污染知识库 | 错误概念和关系被写入图谱 |

推荐：

```text
pipeline step 1
→ pipeline step 2
→ pipeline step 3
→ pipeline step 4
```

也就是确定性的知识编译流水线。

------

## 5. 自动整理状态机

每篇资料导入后，应生成一个 ingest_job，并进入如下状态机：

| 阶段 | 状态名              | 产物                             |
| ---- | ------------------- | -------------------------------- |
| 1    | CREATED             | source 记录                      |
| 2    | FETCHED             | raw_text / html / file_text      |
| 3    | CLEANED             | clean_text                       |
| 4    | CHUNKED             | chunks                           |
| 5    | SUMMARIZED          | source_summary                   |
| 6    | CLASSIFIED          | domain_id                        |
| 7    | CONCEPTS_EXTRACTED  | concept_candidates               |
| 8    | RELATIONS_EXTRACTED | relation_candidates              |
| 9    | WIKI_COMPILED       | source page / concept page draft |
| 10   | GRAPH_UPDATED       | domain graph                     |
| 11   | INDEXED             | vector index / full text index   |
| 12   | READY               | 可检索、可阅读、可跳转           |

失败状态：

```text
FAILED_FETCH
FAILED_PARSE
FAILED_LLM_SUMMARY
FAILED_CONCEPT_EXTRACTION
FAILED_RELATION_EXTRACTION
FAILED_GRAPH_UPDATE
FAILED_INDEX
REVIEW_REQUIRED
```

前端必须能显示每一步是否成功、失败原因、是否可重跑。

------

## 6. 最小可行版本

第一阶段不要做太大。

最小闭环是：

```text
资料导入
→ 自动读取正文
→ 自动清洗正文
→ 自动生成 source_summary
→ 自动抽取 concept_candidates
→ 前端显示整理状态
→ 用户可以修改学科和候选概念
```

第一阶段只需要 4 个核心 SubAgent：

```text
Knowledge Orchestrator
  |
  |-- Source Summary SubAgent
  |-- Domain Classifier SubAgent
  |-- Concept Extraction SubAgent
  |-- Quality Review SubAgent
```

配合两个确定性 worker：

```text
Parser Worker
Index Writer
```

------

## 7. 第一阶段 SubAgent 设计

### 7.1 Source Summary SubAgent

职责：把清洗后的正文变成来源卡片。

输入：

```json
{
  "source_id": "xxx",
  "clean_text": "文章正文",
  "metadata": {
    "title": "标题",
    "url": "链接",
    "source_type": "wechat | webpage | docx | pdf | note"
  }
}
```

输出：

```json
{
  "title": "资料标题",
  "one_sentence_summary": "一句话摘要",
  "short_summary": "3 到 5 句话摘要",
  "key_points": [
    "核心要点 1",
    "核心要点 2",
    "核心要点 3"
  ],
  "important_quotes": [
    {
      "quote": "原文摘录",
      "reason": "为什么重要"
    }
  ],
  "why_saved": "这篇资料为什么值得进入知识库",
  "next_actions": [
    "下一步整理建议 1",
    "下一步整理建议 2"
  ]
}
```

------

### 7.2 Domain Classifier SubAgent

职责：判断资料属于哪个学科或主题网络。

输入：

```json
{
  "title": "标题",
  "summary": "摘要",
  "clean_text_sample": "正文片段"
}
```

输出：

```json
{
  "primary_domain": "AI",
  "secondary_domains": ["认知科学", "语言学"],
  "confidence": 0.86,
  "reason": "主要讨论 Transformer、注意力机制和表示学习。"
}
```

规则：

```text
confidence < 0.7 时，不自动归类，进入人工确认。
```

------

### 7.3 Concept Extraction SubAgent

职责：从资料中抽取候选概念。

输入：

```json
{
  "source_id": "xxx",
  "domain": "AI",
  "clean_text": "正文"
}
```

输出：

```json
{
  "concept_candidates": [
    {
      "name": "注意力机制",
      "aliases": ["Attention Mechanism"],
      "type": "method",
      "definition_draft": "一种根据上下文动态分配信息权重的方法。",
      "evidence_quote": "原文证据",
      "confidence": 0.91
    }
  ]
}
```

要求：

```text
每个候选概念必须绑定 evidence_quote。
没有原文证据的概念不得入库。
```

------

### 7.4 Quality Review SubAgent

职责：检查整理结果是否可靠。

输入：

```json
{
  "source_summary": {},
  "domain_classification": {},
  "concept_candidates": [],
  "clean_text": "正文"
}
```

输出：

```json
{
  "pass": true,
  "risk_level": "low",
  "needs_human_review": false,
  "issues": []
}
```

重点检查：

| 检查项               | 说明                         |
| -------------------- | ---------------------------- |
| 摘要是否空泛         | 不能只是“本文介绍了某某内容” |
| 概念是否有证据       | 每个概念必须有原文摘录       |
| 学科分类是否低置信度 | 低置信度进入人工确认         |
| 微信正文是否误抓     | 风控页、验证页不能入库       |
| 是否出现幻觉         | 没有证据的关系和概念不能写入 |

------

## 8. 第二阶段再加入的 SubAgent

当第一阶段稳定后，再加入：

| SubAgent                     | 加入时机           | 作用                                  |
| ---------------------------- | ------------------ | ------------------------------------- |
| Concept Merge SubAgent       | 候选概念变多后     | 判断新概念是否等于已有概念            |
| Relation Extraction SubAgent | 概念页稳定后       | 抽取概念之间的关系                    |
| Wiki Page Compiler SubAgent  | source card 稳定后 | 生成 source page / concept page draft |
| Cross-Domain Bridge SubAgent | 单学科网络稳定后   | 建立跨学科桥接                        |
| Open Question SubAgent       | 概念网络有规模后   | 自动提出研究问题                      |
| Reading Path SubAgent        | 资料积累后         | 生成学习路径                          |

不要一开始就做跨学科桥接。
优先把单篇资料整理闭环跑通。

------

## 9. 数据库表设计

### 9.1 sources

保存资料本体。

| 字段         | 说明                                 |
| ------------ | ------------------------------------ |
| id           | source_id                            |
| title        | 标题                                 |
| source_type  | webpage / wechat / docx / pdf / note |
| original_url | 原始链接                             |
| file_path    | 本地文件路径                         |
| content_hash | 去重                                 |
| domain_id    | 学科                                 |
| status       | 当前总状态                           |
| created_at   | 导入时间                             |
| updated_at   | 更新时间                             |

------

### 9.2 ingest_jobs

保存自动整理任务。

| 字段             | 说明                                   |
| ---------------- | -------------------------------------- |
| id               | job_id                                 |
| source_id        | 对应资料                               |
| pipeline_version | 流水线版本                             |
| current_step     | 当前步骤                               |
| status           | pending / running / failed / completed |
| retry_count      | 重试次数                               |
| error_message    | 错误信息                               |
| started_at       | 开始时间                               |
| finished_at      | 完成时间                               |

------

### 9.3 source_artifacts

保存中间产物。

| 字段           | 说明                                                   |
| -------------- | ------------------------------------------------------ |
| source_id      | 对应资料                                               |
| artifact_type  | raw_text / clean_text / summary / concepts / relations |
| content_json   | 结构化内容                                             |
| content_text   | 文本内容                                               |
| model_name     | 使用模型                                               |
| prompt_version | 提示词版本                                             |
| created_at     | 生成时间                                               |

这是调试自动整理最关键的表。
没有 source_artifacts，就无法知道系统到底卡在读取、摘要、分类、概念抽取还是索引更新。

------

### 9.4 concept_candidates

保存候选概念，不直接进入正式概念库。

| 字段             | 说明                                   |
| ---------------- | -------------------------------------- |
| id               | candidate_id                           |
| source_id        | 来源                                   |
| domain_id        | 学科                                   |
| name             | 概念名                                 |
| aliases          | 别名                                   |
| definition_draft | 初步定义                               |
| evidence_quote   | 证据摘录                               |
| confidence       | 置信度                                 |
| status           | pending / accepted / rejected / merged |

------

### 9.5 concepts

保存正式概念页。

| 字段               | 说明         |
| ------------------ | ------------ |
| id                 | concept_id   |
| domain_id          | 学科         |
| canonical_name     | 标准概念名   |
| aliases            | 别名         |
| working_definition | 工作定义     |
| evidence_summary   | 证据摘要     |
| open_questions     | 开放问题     |
| source_count       | 来源数量     |
| last_compiled_at   | 最近编译时间 |

------

### 9.6 concept_relations

保存正式概念关系。

| 字段               | 说明                                                         |
| ------------------ | ------------------------------------------------------------ |
| from_concept_id    | 起点概念                                                     |
| to_concept_id      | 终点概念                                                     |
| relation_type      | causes / part_of / analogous_to / contrasts_with / prerequisite_of |
| evidence_source_id | 证据来源                                                     |
| evidence_quote     | 证据摘录                                                     |
| confidence         | 置信度                                                       |
| status             | draft / accepted / rejected                                  |

------

### 9.7 correction_memory

保存人工纠错结果。

| 字段         | 说明                        |
| ------------ | --------------------------- |
| id           | correction_id               |
| object_type  | source / concept / relation |
| object_id    | 被修改对象                  |
| before_value | 修改前                      |
| after_value  | 修改后                      |
| reason       | 用户修改理由                |
| apply_rule   | 是否转成规则                |
| created_at   | 时间                        |

作用：

```text
用户纠错不能只改当前页面，还要反哺未来整理规则。
```

------

## 10. 前端必须增加整理状态面板

source detail 页面不要只显示“已导入”。
应该显示完整整理进度。

| 步骤      | 状态            | 操作            |
| --------- | --------------- | --------------- |
| 读取正文  | 成功 / 失败     | 查看 raw_text   |
| 清洗正文  | 成功 / 失败     | 查看 clean_text |
| 来源摘要  | 成功 / 失败     | 重新生成        |
| 学科分类  | 成功 / 低置信度 | 手动修改        |
| 概念抽取  | 成功 / 失败     | 查看候选概念    |
| 关系抽取  | 成功 / 失败     | 查看候选关系    |
| Wiki 页面 | 成功 / 失败     | 查看页面        |
| 图谱更新  | 成功 / 失败     | 重建图谱        |
| 索引更新  | 成功 / 失败     | 重建索引        |

必须支持：

```text
查看中间产物
查看错误日志
单步重跑
整体重新整理
人工修改学科
人工接受 / 拒绝候选概念
```

------

## 11. 任务队列与 worker 设计

错误方式：

```text
POST /api/sources
  → 上传
  → 解析
  → 调 LLM 摘要
  → 抽概念
  → 入库
```

正确方式：

```text
POST /api/sources
  → 创建 source
  → 创建 ingest_job
  → 立即返回 source_id

worker:
  → 拉取 pending job
  → 执行 pipeline
  → 每一步写状态
  → 每一步保存 artifact
  → 失败时记录 error_message
```

MVP 可以先用：

```text
数据库 ingest_jobs 表 + worker loop
```

后续再升级为：

```text
BullMQ + Redis
Temporal
Celery
```

不要一开始就引入过重的工作流系统。

------

## 12. 幂等与版本控制

每一步必须可以重跑。

推荐唯一键：

```text
source_id + pipeline_version + artifact_type
```

每次 LLM 调用必须记录：

```json
{
  "model_name": "使用的模型",
  "prompt_version": "source_summary_v1",
  "input_hash": "输入内容 hash",
  "output_schema": "source_summary_schema_v1"
}
```

这样可以解决：

| 问题                | 解决方式                     |
| ------------------- | ---------------------------- |
| 同一资料重复整理    | content_hash 去重            |
| prompt 改了无法追踪 | prompt_version               |
| LLM 输出不稳定      | 保存 artifact                |
| 某一步失败无法定位  | current_step + error_message |
| 想重新整理某篇资料  | 单步重跑或整条 pipeline 重跑 |

------

## 13. LLM 输出必须结构化

不要让 LLM 随便输出 Markdown。
所有 SubAgent 都必须输出 JSON，并通过 schema 校验。

标准 source_summary 输出：

```json
{
  "title": "资料标题",
  "source_type": "webpage | wechat | docx | pdf | note",
  "domain": {
    "primary": "AI",
    "secondary": ["认知科学", "语言学"],
    "confidence": 0.82,
    "reason": "文本主要讨论注意力机制、Transformer 和表示学习。"
  },
  "summary": {
    "one_sentence": "本文解释了注意力机制如何在 Transformer 中实现上下文相关的信息选择。",
    "short_summary": "3 到 5 句话摘要",
    "key_points": [
      "要点 1",
      "要点 2",
      "要点 3"
    ]
  },
  "why_saved": "这篇资料适合补充 AI 基础概念网络中的注意力机制节点。",
  "important_quotes": [
    {
      "quote": "原文摘录",
      "reason": "支撑核心定义"
    }
  ],
  "concept_candidates": [
    {
      "name": "注意力机制",
      "aliases": ["Attention Mechanism"],
      "type": "method",
      "definition_draft": "一种根据上下文动态分配信息权重的方法。",
      "evidence_quote": "原文证据",
      "confidence": 0.91
    }
  ],
  "relation_candidates": [
    {
      "from": "注意力机制",
      "relation": "used_in",
      "to": "Transformer",
      "evidence_quote": "原文证据",
      "confidence": 0.88
    }
  ],
  "next_actions": [
    "检查是否已有“注意力机制”概念页",
    "与 Transformer 概念页建立 used_in 关系",
    "补充开放问题：注意力是否等同于解释性"
  ]
}
```

------

## 14. 开发优先级

### 第 1 阶段：修自动整理底座

目标：

```text
每篇资料导入后，一定能看到 raw_text、clean_text、source_summary、concept_candidates、错误日志。
```

任务：

| 优先级 | 任务                                     |
| ------ | ---------------------------------------- |
| P0     | 增加 ingest_jobs 表                      |
| P0     | 增加 source_artifacts 表                 |
| P0     | 上传后自动创建 ingest_job                |
| P0     | 写 worker 执行 parse → clean → summarize |
| P0     | 前端显示整理状态                         |
| P0     | Source Summary SubAgent 输出 JSON        |
| P0     | Concept Extraction SubAgent 输出 JSON    |
| P1     | 支持失败重试                             |
| P1     | 支持手动重新整理                         |

------

### 第 2 阶段：候选概念层

目标：

```text
资料能自动变成候选概念，但不直接污染正式知识库。
```

任务：

| 优先级 | 任务                        |
| ------ | --------------------------- |
| P0     | 结构化抽 concept_candidates |
| P0     | 前端显示候选概念            |
| P0     | 人工接受 / 拒绝 / 改名      |
| P1     | 与已有 concepts 做名称匹配  |
| P1     | 生成概念页 draft            |
| P1     | 增加 Concept Merge SubAgent |

------

### 第 3 阶段：关系和图谱

目标：

```text
单学科内的概念网络可视化可用。
```

任务：

| 优先级 | 任务                              |
| ------ | --------------------------------- |
| P0     | 抽 relation_candidates            |
| P0     | 前端显示关系候选                  |
| P0     | accepted 后写 concept_relations   |
| P1     | 更新 domain graph                 |
| P1     | 点击图谱节点跳 concept page       |
| P1     | 增加 Relation Extraction SubAgent |

------

### 第 4 阶段：跨学科桥接

目标：

```text
从单学科知识库升级为个人多学科知识网络。
```

任务：

| 优先级 | 任务                                  |
| ------ | ------------------------------------- |
| P0     | 增加 cross_domain_relation_candidates |
| P0     | 建立类比、迁移、冲突、共同结构关系    |
| P1     | 增加跨学科搜索                        |
| P1     | 增加跨学科桥接页面                    |
| P1     | 增加 Cross-Domain Bridge SubAgent     |

------

## 15. 判断系统是否合格的标准

你必须能回答这些问题：

| 问题                       | 要求     |
| -------------------------- | -------- |
| 某篇资料导入后卡在哪一步？ | 必须能查 |
| LLM 有没有被调用？         | 必须能查 |
| 用的是哪个 prompt？        | 必须能查 |
| LLM 返回了什么？           | 必须能查 |
| JSON 解析失败了吗？        | 必须能查 |
| 是正文为空，还是摘要失败？ | 必须能查 |
| 概念候选生成了吗？         | 必须能查 |
| 图谱更新了吗？             | 必须能查 |
| 能不能单独重跑某一步？     | 必须能做 |
| 用户纠错有没有被记录？     | 必须能查 |

如果这些问题答不上来，说明系统还不是可维护的自动整理系统。

------

## 16. 给 Codex 的实施提示词

你可以直接把下面内容交给 Codex：

```text
你是本项目的后端架构开发 Agent。当前项目基于 LLM Wiki 思路，目标是把用户导入的网页、微信公众号、本地文件、docx、笔记资料自动整理成可阅读、可检索、可跳转、可扩展的个人多学科知识网络。

当前问题：资料可以导入，但导入后不能稳定自动整理。请不要直接重写整个项目。请先围绕 ingest pipeline 做最小可用改造。

核心目标：
1. 上传或新增 source 后，必须自动创建 ingest_job。
2. ingest_job 由 worker 执行，不要在上传接口里直接调用 LLM。
3. pipeline 至少包含：
   CREATED
   FETCHED
   CLEANED
   SUMMARIZED
   CLASSIFIED
   CONCEPTS_EXTRACTED
   INDEXED
   READY
   FAILED
4. 每一步必须写入状态、错误日志和中间产物。
5. 新增 source_artifacts 表，用于保存 raw_text、clean_text、summary、concept_candidates、relation_candidates。
6. LLM 输出必须使用结构化 JSON，不允许只返回 Markdown。
7. 每个 LLM 调用必须记录 model_name、prompt_version、input_hash、output_schema。
8. 前端 source detail 页面需要显示整理状态、失败原因、中间产物，并提供“重新整理”按钮。
9. 所有步骤必须幂等。重复执行同一 source_id + pipeline_version 时，不得污染已有数据。
10. 不要先做跨学科桥接，先保证单资料自动整理闭环稳定。

SubAgent 设计：
1. Source Summary SubAgent：生成 source card。
2. Domain Classifier SubAgent：判断资料所属学科。
3. Concept Extraction SubAgent：抽取候选概念。
4. Quality Review SubAgent：检查摘要、概念、证据和分类是否可靠。
5. 后续再添加 Concept Merge、Relation Extraction、Wiki Page Compiler、Cross-Domain Bridge。

工程边界：
1. SubAgent 只输出 JSON，不直接写数据库。
2. 数据库写入由后端代码完成。
3. 状态流转由 orchestrator 控制。
4. 每个概念和关系必须有 evidence_quote。
5. 低置信度结果进入人工审核。
6. 人工修改必须写入 correction_memory。

请先完成：
A. 阅读当前项目结构。
B. 找到 source 新增、文件上传、docx 读取、微信抓取、summary 生成、concept 生成相关代码。
C. 输出一份改造计划，列出需要修改的文件。
D. 再逐步实现 ingest_jobs、source_artifacts、worker、状态机和前端状态面板。
E. 每完成一个阶段，运行现有测试或最小手工验证。
```

------

## 17. 最终一句话架构定义

这个项目应该被定义为：

```text
一个以 ingest pipeline 为主干、以函数式 SubAgent 为语义处理节点、以 source_artifacts 为中间产物层、以 concepts / relations / graph 为知识网络输出的个人多学科知识编译系统。
```

当前阶段的第一目标不是让 Agent 更复杂，而是让每篇资料都能稳定完成：

```text
导入
→ 读取
→ 清洗
→ 摘要
→ 分类
→ 候选概念
→ 前端可见
→ 可人工纠错
→ 可重跑
```

这个闭环稳定之后，再继续扩展概念合并、关系抽取、图谱更新和跨学科桥接。

最关键的执行顺序：**先做 ingest_jobs、source_artifacts、worker 和前端整理状态面板，再加更多 subagent。**
否则 subagent 越多，系统越难调试。



worker v.s.  subagent

结论：**worker 是“执行任务的工程进程”，subagent 是“完成某类语义判断的 LLM 模块”。**
在你的 LLM Wiki 项目里，**worker 负责跑流程，subagent 负责产出结构化认知结果。**

------

# 1. 一句话区分worker 和  subagent

| 名称     | 本质           | 主要负责                               |
| -------- | -------------- | -------------------------------------- |
| worker   | 后端任务执行器 | 取任务、跑步骤、更新状态、重试、写日志 |
| subagent | 专用语义处理器 | 摘要、分类、抽概念、抽关系、质检       |

简单说：

```text
worker = 干活的执行机器
subagent = 某一步里的智能判断模块
```

------

# 2. 放到你的项目里看

当用户导入一篇资料后，流程应该是：

```text
用户上传资料
→ 后端创建 source
→ 后端创建 ingest_job
→ worker 取出这个 job
→ worker 读取正文
→ worker 调用 Source Summary SubAgent
→ worker 保存 summary
→ worker 调用 Concept Extraction SubAgent
→ worker 保存 concept_candidates
→ worker 更新状态为 READY
```

这里：

| 步骤                        | 谁负责                  |
| --------------------------- | ----------------------- |
| 从数据库取 pending job      | worker                  |
| 读取 docx / 网页 / 微信正文 | worker 或 parser worker |
| 判断这篇文章属于哪个学科    | subagent                |
| 生成摘要                    | subagent                |
| 抽取候选概念                | subagent                |
| 校验 JSON                   | worker                  |
| 写入 source_artifacts       | worker                  |
| 更新 ingest_jobs 状态       | worker                  |
| 失败重试                    | worker                  |
| 记录 error_message          | worker                  |

------

# 3. 更准确的定义

## worker 是什么

worker 是一个长期运行的后端程序。

它通常做这些事：

```text
1. 从任务表里找 pending 的任务
2. 把任务状态改成 running
3. 执行 pipeline 的每一步
4. 调用必要的 parser、subagent、indexer
5. 保存中间产物
6. 失败时记录错误
7. 成功时更新状态
```

伪代码：

```ts
while (true) {
  const job = await getNextPendingJob()

  try {
    await markJobRunning(job.id)

    const rawText = await parseSource(job.sourceId)
    await saveArtifact(job.sourceId, "raw_text", rawText)

    const cleanText = await cleanText(rawText)
    await saveArtifact(job.sourceId, "clean_text", cleanText)

    const summary = await callSourceSummarySubAgent(cleanText)
    await saveArtifact(job.sourceId, "source_summary", summary)

    const concepts = await callConceptExtractionSubAgent(cleanText)
    await saveArtifact(job.sourceId, "concept_candidates", concepts)

    await markJobReady(job.id)
  } catch (error) {
    await markJobFailed(job.id, error.message)
  }
}
```

worker 不一定是 AI。
大多数时候它只是普通后端代码。

------

## subagent 是什么

subagent 是一个专门负责某类认知任务的 LLM 调用模块。

例如：

```text
Source Summary SubAgent
```

只负责：

```text
输入 clean_text
输出 source_summary.json
```

它不关心数据库、不关心任务队列、不关心前端状态。

例如：

```json
{
  "one_sentence_summary": "本文解释了注意力机制如何在 Transformer 中实现信息选择。",
  "key_points": [
    "注意力机制通过权重分配突出相关信息。",
    "Transformer 使用自注意力建模上下文关系。",
    "该机制改变了序列建模方式。"
  ],
  "important_quotes": [
    {
      "quote": "原文摘录",
      "reason": "支撑核心定义"
    }
  ]
}
```

------

# 4. 二者最核心的差别

| 对比项             | worker                  | subagent                |
| ------------------ | ----------------------- | ----------------------- |
| 类型               | 工程执行单元            | LLM 语义处理单元        |
| 是否必须用 LLM     | 否                      | 是，或至少通常是        |
| 是否长期运行       | 是                      | 否，通常是一次调用      |
| 是否直接操作数据库 | 可以，而且应该由它操作  | 不应该                  |
| 是否更新状态       | 是                      | 不应该                  |
| 是否处理重试       | 是                      | 不应该                  |
| 是否负责判断语义   | 通常不负责              | 负责                    |
| 输出               | 状态、artifact、日志    | JSON 语义结果           |
| 失败处理           | 记录错误、重试、回滚    | 返回失败或不合格输出    |
| 类比               | 工厂流水线工人 / 调度器 | 专科顾问 / 专用模型函数 |

------

# 5. 在你的系统里，worker 是主干，subagent 是插件

推荐关系是：

```text
Ingest Worker
  |
  |-- Parser function
  |-- Cleaner function
  |-- Source Summary SubAgent
  |-- Domain Classifier SubAgent
  |-- Concept Extraction SubAgent
  |-- Quality Review SubAgent
  |-- Index Writer
```

也就是：

```text
worker 调用 subagent
subagent 不调用 worker
subagent 不调用其他 subagent
subagent 不直接写库
```

这个边界很重要。

------

# 6. 错误架构

不要这样：

```text
Source Summary SubAgent
  → 自己去数据库查 source
  → 自己调用 Concept Agent
  → 自己写入 concepts 表
  → 自己更新 ingest_job 状态
```

这会导致：

| 问题       | 后果                     |
| ---------- | ------------------------ |
| 权限混乱   | 不知道谁改了数据库       |
| 错误难追踪 | 失败点不清楚             |
| 重试困难   | 不知道从哪一步重跑       |
| 数据污染   | LLM 可能直接写错正式表   |
| 状态失真   | 前端显示和真实任务不一致 |

------

# 7. 正确架构

应该这样：

```text
worker:
  1. 读取 source
  2. 得到 clean_text
  3. 调用 Summary SubAgent
  4. 校验 JSON
  5. 写入 source_artifacts
  6. 调用 Concept SubAgent
  7. 校验 JSON
  8. 写入 concept_candidates
  9. 更新状态
```

subagent 只做：

```text
输入文本
→ 语义处理
→ 输出 JSON
```

------

# 8. 用工厂比喻

你的系统像一个知识加工厂。

| 工厂角色               | 项目角色                       |
| ---------------------- | ------------------------------ |
| 传送带                 | ingest pipeline                |
| 车间调度员             | orchestrator                   |
| 负责搬运和记录的工人   | worker                         |
| 专门判断材料类别的专家 | Domain Classifier SubAgent     |
| 专门写说明书的专家     | Source Summary SubAgent        |
| 专门提取零件名的专家   | Concept Extraction SubAgent    |
| 质检员                 | Quality Review SubAgent        |
| 仓库管理员             | database writer / index writer |

worker 是让流水线动起来的人。
subagent 是某个工位上的专家。

------

# 9. 你的项目中应该有哪些 worker

第一阶段建议有 1 到 2 个 worker 就够。

## 9.1 Ingest Worker

负责完整自动整理流程：

```text
parse
→ clean
→ summarize
→ classify
→ extract concepts
→ quality review
→ index
→ ready
```

这是最重要的 worker。

------

## 9.2 Rebuild Worker

后期再加。

负责重建：

```text
重新生成 summary
重新抽 concept_candidates
重新建 graph
重新建 index
```

适合用户点击“重新整理”或你改了 prompt_version 后批量重跑。

------

# 10. 你的项目中应该有哪些 subagent

第一阶段建议只有 4 个：

| SubAgent                    | 输入                                | 输出                       |
| --------------------------- | ----------------------------------- | -------------------------- |
| Source Summary SubAgent     | clean_text                          | source_summary.json        |
| Domain Classifier SubAgent  | title + summary + clean_text_sample | domain_classification.json |
| Concept Extraction SubAgent | clean_text + domain                 | concept_candidates.json    |
| Quality Review SubAgent     | summary + concepts + clean_text     | review_result.json         |

第二阶段再加：

| SubAgent                     | 用途                         |
| ---------------------------- | ---------------------------- |
| Concept Merge SubAgent       | 判断候选概念是否等于已有概念 |
| Relation Extraction SubAgent | 抽概念关系                   |
| Wiki Page Compiler SubAgent  | 生成概念页草稿               |
| Cross-Domain Bridge SubAgent | 跨学科类比和桥接             |

------

# 11. 最重要的工程边界

你可以用这条规则判断某个模块是 worker 还是 subagent：

| 问题                                               | 答案     |
| -------------------------------------------------- | -------- |
| 它主要在“跑流程、改状态、写库、重试”吗？           | worker   |
| 它主要在“理解文本、判断学科、抽概念、生成摘要”吗？ | subagent |
| 它需要长期监听任务队列吗？                         | worker   |
| 它只是被调用一次，返回 JSON 吗？                   | subagent |
| 它的输出需要人类语义判断吗？                       | subagent |
| 它的行为必须完全确定、可追踪、可重试吗？           | worker   |

------

# 12. 最终建议

你的项目应该这样分工：

```text
orchestrator / worker = 工程控制层
subagent = 语义处理层
database = 真值存储层
source_artifacts = 中间产物层
frontend = 可观测与人工纠错层
```

最小实现：

```text
用户导入资料
→ 创建 source
→ 创建 ingest_job
→ ingest worker 开始执行
→ parser 读取正文
→ worker 调用 summary subagent
→ worker 调用 domain subagent
→ worker 调用 concept subagent
→ worker 调用 quality subagent
→ worker 保存 artifacts
→ worker 更新 source 为 READY
→ 前端显示整理结果
```

一句话定性：

> **worker 是流水线执行者，subagent 是流水线里的专业脑。**