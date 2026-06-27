# LLM Wiki 个人多学科智能体 MVP 技术架构方案

## 1. MVP 总目标

当前项目不是要先做大型知识工程平台，而是先实现一个可用的个人知识整理 MVP。

MVP 目标是：

```text
用户导入资料
→ 系统自动读取内容
→ 自动生成 source summary
→ 自动抽取候选概念
→ 自动生成可阅读的 wiki source 页面
→ 前端能看到整理结果
→ 失败时能看到失败原因
→ 用户可以重新整理
```

第一阶段不追求完整数据库、复杂任务队列、多 Agent 协同、跨学科图谱和正式概念审核系统。

核心目标只有一个：

```text
导入一篇资料后，系统稳定生成一张可阅读的知识卡片。
```

------

## 2. MVP 架构原则

| 原则                         | 说明                                             |
| ---------------------------- | ------------------------------------------------ |
| 保留现有 Markdown 文件结构   | 不把项目改造成数据库应用                         |
| 不上复杂 job 系统            | 不做 SQLite migration、ingest_jobs、后台 daemon  |
| 不做复杂 subagent            | 先用几个普通 Python 函数完成摘要、分类、概念抽取 |
| 不直接大改 concept_ingest.py | 先生成候选概念 JSON，不直接污染正式概念页        |
| 所有中间产物落地为文件       | 方便你直接打开查看、调试、删除和重跑             |
| 前端只做最小状态显示         | 显示整理状态、错误、结果、重新整理按钮           |
| 先同步执行                   | 本地个人 MVP 可以接受导入后等待几秒到几十秒      |
| 后续再升级 worker / SQLite   | MVP 跑通后再工程化                               |

------

## 3. MVP 总体架构

```text
Web UI
  |
  v
POST /api/sources
  |
  v
create_source 写入 raw/sources/.../*.md
  |
  v
mvp_ingest_runner.py
  |
  |→ 读取 raw source
  |→ 抽取正文
  |→ 清洗正文
  |→ 生成 source summary
  |→ 抽取候选概念
  |→ 生成 wiki source markdown
  |→ 保存 artifacts
  |→ 写入 status.json
  |
  v
前端显示整理状态和结果
```

MVP 只需要一个核心新增模块：

```text
scripts/mvp_ingest_runner.py
```

它不是长期 worker，只是一个“整理执行器”。

------

## 4. 文件结构设计

新增一个轻量 artifact 目录：

```text
data/ingest_artifacts/
  source_id/
    status.json
    raw_text.txt
    clean_text.txt
    source_summary.json
    concept_candidates.json
    error.json
```

示例：

```text
data/ingest_artifacts/attention_mechanism_20260619/
  status.json
  raw_text.txt
  clean_text.txt
  source_summary.json
  concept_candidates.json
```

这样做的好处：

| 好处                     | 说明                        |
| ------------------------ | --------------------------- |
| 不需要数据库             | 文件直接可读                |
| 调试简单                 | 打开 JSON 和 txt 就能看问题 |
| 容易删除重跑             | 删除 artifact 文件夹即可    |
| 和现有 Markdown 架构一致 | 不破坏当前项目              |
| 适合个人本地 MVP         | 成本低，开发快              |

------

## 5. MVP pipeline

MVP pipeline 只保留 6 步。

| 步骤 | 名称              | 产物                                          |
| ---- | ----------------- | --------------------------------------------- |
| 1    | READ_SOURCE       | 读取 raw source markdown                      |
| 2    | EXTRACT_TEXT      | 读取网页、本地文件、docx 或已有 markdown 内容 |
| 3    | CLEAN_TEXT        | 去掉空白、风控页、无效内容                    |
| 4    | SUMMARIZE         | 生成 source summary                           |
| 5    | EXTRACT_CONCEPTS  | 生成候选概念                                  |
| 6    | WRITE_WIKI_SOURCE | 生成 wiki/sources/.../*.md                    |

最终状态只需要：

| 状态            | 含义         |
| --------------- | ------------ |
| pending         | 等待整理     |
| running         | 正在整理     |
| completed       | 整理完成     |
| failed          | 整理失败     |
| review_required | 需要人工检查 |

不要一开始做十几个状态。
MVP 状态越少越稳定。

------

## 6. status.json 设计

每个 source 一个 status.json。

```json
{
  "source_id": "attention_mechanism_20260619",
  "source_path": "raw/sources/ai/attention_mechanism.md",
  "status": "completed",
  "current_step": "WRITE_WIKI_SOURCE",
  "created_at": "2026-06-19T21:00:00",
  "updated_at": "2026-06-19T21:00:30",
  "error": null,
  "artifacts": {
    "raw_text": true,
    "clean_text": true,
    "source_summary": true,
    "concept_candidates": true
  }
}
```

失败时：

```json
{
  "source_id": "wechat_xxx",
  "status": "review_required",
  "current_step": "CLEAN_TEXT",
  "error": {
    "message": "疑似微信风控页或验证页，未生成有效正文。",
    "type": "WECHAT_BLOCKED"
  }
}
```

------

## 7. source_summary.json 设计

```json
{
  "title": "资料标题",
  "source_type": "webpage",
  "one_sentence_summary": "一句话说明这篇资料讲什么。",
  "short_summary": "三到五句话摘要。",
  "key_points": [
    "核心要点一",
    "核心要点二",
    "核心要点三"
  ],
  "important_quotes": [
    {
      "quote": "原文摘录",
      "reason": "为什么重要"
    }
  ],
  "why_saved": "这篇资料为什么值得进入知识库。",
  "next_actions": [
    "建议后续补充某个概念页",
    "建议和某个已有主题关联"
  ]
}
```

MVP 阶段可以先用规则摘要。
如果已经有可用 LLM API，再把这一步替换为 LLM 调用。

------

## 8. concept_candidates.json 设计

```json
{
  "concept_candidates": [
    {
      "name": "注意力机制",
      "aliases": ["Attention Mechanism"],
      "type": "method",
      "definition_draft": "一种根据上下文动态分配信息权重的方法。",
      "evidence_quote": "原文中支持该概念的摘录。",
      "confidence": 0.8
    }
  ]
}
```

MVP 阶段原则：

```text
只生成候选概念，不直接写入正式 wiki/concepts。
```

这样可以避免错误概念污染知识库。

------

## 9. mvp_ingest_runner.py 职责

新增：

```text
scripts/mvp_ingest_runner.py
```

核心函数：

```text
run_mvp_ingest(source_path, overwrite=False)
```

它负责：

| 功能                 | 说明                                                         |
| -------------------- | ------------------------------------------------------------ |
| 读取 source markdown | 读取 raw/sources 中的源文件                                  |
| 抽正文               | 复用 auto_ingest.py 中已有网页、微信、docx、本地文件读取逻辑 |
| 清洗正文             | 去空内容、异常页、无意义内容                                 |
| 生成摘要             | 先用规则型 fallback，后续可换 LLM                            |
| 抽候选概念           | 先用规则型 fallback，后续可换 LLM                            |
| 写 artifacts         | 保存 raw_text、clean_text、summary、concepts                 |
| 写 wiki source 页面  | 生成 wiki/sources 下的 markdown                              |
| 写 status.json       | 前端可读取状态                                               |
| 失败处理             | 写 error.json 和 status failed                               |

------

## 10. 最小 subagent 设计

MVP 阶段不要真的做复杂 subagent。
先做成普通函数。

```text
scripts/mvp_subagents.py
```

包含 3 个函数：

```text
generate_source_summary(clean_text, metadata) -> dict
extract_concept_candidates(clean_text, metadata) -> dict
quality_check(clean_text, summary, concepts) -> dict
```

这就是 MVP 版本的“函数式 subagent”。

| 函数                       | 作用                                           |
| -------------------------- | ---------------------------------------------- |
| generate_source_summary    | 生成资料摘要                                   |
| extract_concept_candidates | 抽候选概念                                     |
| quality_check              | 判断正文是否为空、是否风控页、是否需要人工检查 |

暂时不需要：

| 暂不需要                     | 原因                                         |
| ---------------------------- | -------------------------------------------- |
| Domain Classifier SubAgent   | source 已经在学科目录下，先用目录作为 domain |
| Concept Merge SubAgent       | 先不自动合并概念                             |
| Relation Extraction SubAgent | 先不抽关系                                   |
| Cross Domain Bridge SubAgent | 单学科稳定后再做                             |
| 独立 LLM provider 层         | 有真实 LLM 调用需求后再加                    |

------

## 11. 修改 wiki_web.py 的最小方式

当前 `POST /api/sources` 已经可以创建 source。

MVP 改法：

```text
create_source 成功
→ 如果 auto_ingest=true
→ 调用 run_mvp_ingest(source_path, overwrite=True)
→ 返回 source 创建结果 + ingest_result
```

不要先做后台任务。
本地个人工具可以先同步执行。

如果担心请求阻塞，可以做一个极简后台线程：

```text
threading.Thread(target=run_mvp_ingest, args=(source_path,)).start()
```

但第一版建议先同步，容易调试。

------

## 12. 新增 API

MVP 只需要 3 个 API。

| API                                                    | 作用                    |
| ------------------------------------------------------ | ----------------------- |
| GET /api/sources/<source_id>/ingest-status             | 读取 status.json        |
| GET /api/sources/<source_id>/artifacts/<artifact_type> | 查看 artifact 内容      |
| POST /api/sources/<source_id>/reingest                 | 重新执行 run_mvp_ingest |

暂时不需要：

| 暂不需要                              | 原因                  |
| ------------------------------------- | --------------------- |
| ingest_jobs API                       | MVP 不做 job 系统     |
| concept candidate accept / reject API | 第二阶段再做          |
| artifact 列表 API                     | 可以从 status.json 读 |
| worker loop API                       | MVP 不需要后台 worker |

------

## 13. 前端 MVP 改造

前端只改 source 展开面板。

在每条 source 的 `<details>` 中显示：

| 内容               | 说明                                    |
| ------------------ | --------------------------------------- |
| 整理状态           | completed / failed / review_required    |
| 当前步骤           | READ_SOURCE / CLEAN_TEXT / SUMMARIZE 等 |
| 错误原因           | 如果失败则显示                          |
| source_summary     | 显示一句话摘要和 key points             |
| concept_candidates | 显示候选概念列表                        |
| 重新整理按钮       | 调用 reingest API                       |

不要先做复杂 UI。
不要先做候选概念编辑器。
不要先做图谱联动。

------

## 14. MVP 不做的内容

第一版明确不做：

| 不做                               | 原因                 |
| ---------------------------------- | -------------------- |
| SQLite 数据库                      | 对 MVP 过重          |
| migration 系统                     | 当前项目不是数据库型 |
| ingest_jobs 表                     | 可以后续再加         |
| 独立 worker daemon                 | 本地 MVP 不需要      |
| Redis / BullMQ / Celery / Temporal | 完全没必要           |
| 多 subagent 协作                   | 先用普通函数         |
| JSON Schema 框架                   | 先用简单字段检查     |
| 正式 concept 写入                  | 防止污染概念页       |
| concept accept / reject UI         | 第二阶段再加         |
| relation extraction                | 先不抽关系           |
| cross domain bridge                | 单学科稳定后再做     |
| 大规模前端重构                     | 只加状态和结果展示   |

------

## 15. 推荐实现顺序

### 第 1 步：新增 artifact 文件层

新增目录：

```text
data/ingest_artifacts/
```

新增工具函数：

```text
write_status
read_status
write_artifact
read_artifact
write_error
```

------

### 第 2 步：新增 mvp_ingest_runner.py

实现：

```text
run_mvp_ingest(source_path, overwrite=False)
```

先让它能处理已有 raw source markdown。

------

### 第 3 步：复用 auto_ingest.py 的正文读取能力

不要重写抓取逻辑。
优先复用：

| 内容         | 位置           |
| ------------ | -------------- |
| 微信抓取     | auto_ingest.py |
| 普通网页抓取 | auto_ingest.py |
| docx 读取    | auto_ingest.py |
| 本地文件读取 | auto_ingest.py |

如果不好复用，第一版可以先用 raw source markdown 中已有内容生成 summary。

------

### 第 4 步：生成 source_summary.json

先用规则型 fallback：

```text
标题
前 500 到 1000 字摘要
提取 3 到 5 个关键句
记录 why_saved
```

后续再替换为 LLM。

------

### 第 5 步：生成 concept_candidates.json

先用简单规则：

```text
从标题、正文高频词、已有候选概念字段中提取 5 到 10 个候选概念。
```

不要直接写正式 concept markdown。

------

### 第 6 步：生成 wiki source markdown

写入：

```text
wiki/sources/<domain>/<source_id>.md
```

包含：

```text
标题
来源
摘要
关键要点
重要摘录
候选概念
下一步整理建议
```

------

### 第 7 步：修改 wiki_web.py

在 source 创建后调用：

```text
run_mvp_ingest(source_path)
```

并新增：

```text
ingest-status
artifact
reingest
```

三个 API。

------

### 第 8 步：前端显示最小状态

在 source 展开面板中显示：

```text
整理状态
摘要
候选概念
错误原因
重新整理按钮
```

------

## 16. MVP 验收标准

MVP 完成后，只看这些标准：

| 验收项           | 标准                                                         |
| ---------------- | ------------------------------------------------------------ |
| 新增网页资料     | 能生成 wiki source 页面                                      |
| 新增 docx 资料   | 能读取正文并生成摘要                                         |
| 微信风控页       | 不生成假摘要，显示 review_required                           |
| 摘要结果         | 前端可见                                                     |
| 候选概念         | 前端可见                                                     |
| 失败原因         | 前端可见                                                     |
| 重新整理         | 点击后能重跑                                                 |
| 文件可调试       | artifact 文件夹里能看到 raw_text、clean_text、summary、concepts |
| 不污染正式概念页 | 不自动写 wiki/concepts                                       |
| 不破坏旧功能     | 原有 source 创建和文件结构仍可用                             |

------

## 17. MVP 版本一句话定义

这个 MVP 不是完整知识工程系统，而是：

```text
一个基于现有 Markdown 文件库的轻量自动整理器。
```

它只需要做到：

```text
导入资料
→ 生成可阅读 source card
→ 保存中间产物
→ 前端显示状态
→ 失败可定位
→ 可重新整理
```

等这个闭环稳定后，再进入第二阶段：

```text
SQLite job 层
候选概念审核
正式概念页写入
关系抽取
图谱更新
跨学科桥接
真实 LLM subagent
```