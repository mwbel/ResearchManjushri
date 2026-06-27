# ResearchManjushri 迁移记录

更新时间：2026-06-27

## 迁移背景

原项目目录名为 `ResearchManjusi`，后确认拼写应为 `ResearchManjushri`。

当前项目主体已经从泛研究资料工作区，逐步收敛为以 `LLM Wiki` 为主产品的个人知识编译系统。后续开发方向是模块化：核心能力通过接口输出，可被前端 app、管理后台、阅读工作台、后端服务和数据库层复用。

## 当前命名约定

- 仓库名：`ResearchManjushri`
- 本地目录：`/Users/Min369/Documents/同步空间/Manju/AIProjects/ResearchManjushri`
- GitHub 仓库：`https://github.com/mwbel/ResearchManjushri`
- 主产品名：`LLM Wiki`
- 核心模块目录：`app/llm-wiki/`

`ResearchManjushri` 作为仓库和工程容器保留，`LLM Wiki` 作为产品名、入口名和后续模块化开发的核心能力名。

## 已完成迁移动作

1. 本地目录已从 `ResearchManjusi` 改名为 `ResearchManjushri`。
2. Git remote 已指向 `https://github.com/mwbel/ResearchManjushri.git`。
3. GitHub 远程仓库已重命名为 `ResearchManjushri`。
4. 根目录新增 `README.md`，说明 `LLM Wiki` 是当前主产品。
5. 新增模块化目录：
   - `services/`
   - `domains/`
   - `shared/`
   - `docs/api/`
   - `docs/architecture/`
6. 新增接口与架构文档：
   - `docs/api/llm-wiki-api.md`
   - `docs/architecture/module-boundaries.md`
   - `docs/architecture/product-naming.md`
   - `shared/api-response.md`
7. 根 `AGENTS.md` 已更新为新项目名、新路径和模块化开发规则。
8. GitHub 仓库已清理为代码/框架仓库，不再同步个人资料和知识库内容。
9. 核心应用目录已从根目录 `LLM Wiki/` 迁移到 `app/llm-wiki/`，根目录只保留模块边界、接口契约和技术文档入口。
10. 两份旧 LLM Wiki 方案文档已迁入 `docs/legacy/`：
    - `docs/legacy/llm-wiki-mvp-architecture.md`
    - `docs/legacy/llm-wiki-subagent-architecture.md`
11. 根目录工作文档已扁平迁入 `docs/`：
    - `docs/PRD_研究智能助手.md`
    - `docs/任务执行清单_技术架构与开发进度.md`
    - `docs/提示词历史.md`
    - `docs/sessions/第*次-*.md`

## GitHub 同步策略

GitHub 只保留代码、框架、接口契约和必要开发规范。

不再同步：

- `AI/`
- `outputs/`
- `本质之探索/`
- `需读论文/`
- `inputs/`
- `app/llm-wiki/raw/`
- `app/llm-wiki/wiki/`
- `docs/PRD_*.md`
- `docs/任务执行清单_*.md`
- `docs/提示词历史.md`
- `docs/sessions/第*次-*.md`
- `.DS_Store`

这些文件和目录可以继续保留在本地，但不进入远程仓库。

已推送的清理提交：

```text
5e8e127 chore: keep repository focused on code and framework
```

## LLM Wiki 当前产品定位

LLM Wiki 是长期个人知识编译系统，不是临时问答工具。

核心链路：

```text
资料导入
-> 原始资料归档
-> 摘要生成
-> 候选概念和关系抽取
-> 人工审核
-> 概念页与关系投影
-> 学科知识图谱
-> 多应用通过 API 复用
```

当前核心实现仍在 `app/llm-wiki/`：

- `scripts/wiki_web.py`: 本地 HTTP 服务、API 与 Web UI 后端。
- `webui/`: 当前前端工作台。
- `scripts/mvp_*`: ingest、候选概念、review、projection 相关逻辑。
- `raw/`: 本地原始资料层，已从 GitHub 移除跟踪。
- `wiki/`: 本地长期知识层，已从 GitHub 移除跟踪。

## 已完成的主要功能演进

### 资料导入

已形成以下目标流程：

```text
粘贴微信链接
-> 自动抓取全文及元数据
-> 自动建立 Source
-> 提取候选概念和关系
-> 人工审核
-> 投影到知识图谱
```

支持：

- 微信文章导入。
- 本地文件导入。
- Source 卡片生成。
- 自动 ingest。
- 自动补充草稿。
- 本地文件不存在时报错“文件不存在”。

### 摘要、概念、关系

已实现每篇文章生成摘要、候选概念和候选关系的 MVP。

概念进入人工审核队列后，可执行：

- 同意保留。
- 拒绝。
- 合并建议。
- 创建概念页。
- 编辑概念页。
- 删除概念页或从图谱中移除节点。

### 合并建议

系统已支持对疑似同义词、缩写或中英翻译别名提出合并建议。

推荐交互方向：

```text
系统给出合并建议
-> 用户点击同意或拒绝
-> 同意后保留 alias、来源证据和关系说明
-> 投影到概念图谱
```

### 知识工作台

前端经历多轮简化，目标是降低操作噪音。

页面逻辑被明确为：

1. 资料库：查看和管理原始资料。
2. 处理资料：补正文、生成摘要、重新 ingest。
3. 审核概念：合并、保留、拒绝。
4. 看图谱：浏览概念网络和来源证据。

已加入页面逻辑说明和从概念网络返回“资料整理”的入口。

### 概念网络

概念网络用于探索概念之间的关系和回溯来源证据。

已支持：

- 点击节点查看概念信息。
- 从节点创建概念页。
- 删除概念页。
- 移除图谱节点。
- 在原始资料中显示相关来源。

已明确的问题：

- 从图谱底部跳到中部或顶部的阅读动线仍需继续优化。
- 关系类型如“相关”“映射到”需要后续收敛语义，否则图谱解释性不足。

### 学科管理

曾出现应用自动添加错误学科的问题。当前原则是禁用自动新增学科。

允许显示和操作的既有学科包括：

- `ai`
- `ai智能体`
- `math`
- `modern-astronomy`
- `physics`
- `tibetan-astronomy-calendar`
- `世界模型`
- `垂直小模型`

除非明确恢复，不要重新打开自动发现学科或自动新增学科。

### 本地上传与资料队列

已修复：

- 本地文件导入成功后，导入面板不消失的问题。
- 已保存修改并完成整理后，资料仍错误留在“待补资料”的问题。
- 已完成补充草稿但仍被判断为待补的问题。

### Mathpix / MinerU 资料显示

已明确交互原则：

如果资料已经通过 Mathpix 校正，则不再同时显示 MinerU 源码，避免同一个 block 出现两份 Markdown 源码造成阅读混乱。

## 当前代码和文档边界

### 保留在 GitHub 的内容

- 代码。
- 框架。
- 开发规范。
- 接口契约。
- 模块边界说明。
- 启动脚本和必要配置。

### 只保留本地的内容

- 原始资料。
- 知识库内容。
- 个人论文与文档。
- 对话提示词历史。
- 任务执行清单。
- 自动 ingest 生成的数据产物。

## 当前遗留状态

### Reader Workbench

本地 Git 状态显示 `reader-workbench/` 有删除项。

这部分没有混入最近一次 GitHub 清理提交。后续需要单独确认：

1. 是否保留在当前仓库。
2. 是否迁移为同级独立项目。
3. 是否只作为外部前端 app，通过 LLM Wiki API 集成。

建议：不要在未确认前提交 `reader-workbench/` 的删除。

### Codex 旧会话

Codex 侧边栏中的旧 `ResearchManjusi` 会话可保留作历史。

建议：

1. 不在旧会话中继续执行开发。
2. 新开发统一在 `ResearchManjushri` 目录打开的新会话中进行。
3. 旧会话只用于查历史决策和上下文。

## 后续开发原则

### 模块化优先

新增能力先判断属于哪一层：

- 前端 app。
- 管理后台。
- 后端服务。
- 数据库。
- 核心知识编译能力。
- 通用接口契约。

不要把所有能力继续堆入 `app/llm-wiki/webui/app.js` 或 `scripts/wiki_web.py`。当能力会被多个应用复用时，应先定义 API 和领域对象。

### API 优先

不同应用应通过 API 或 adapter 调用 LLM Wiki 能力。

不要让前端、管理后台、阅读器直接改写：

- `app/llm-wiki/raw/`
- `app/llm-wiki/wiki/`

写入长期知识层必须经过核心后端、明确脚本或人工审核动作。

### 数据对象优先

下一阶段建议优先固化四类对象：

1. `Source`
2. `Concept`
3. `Relation`
4. `ReviewTask`

这些对象应进入 `shared/`，再被前端 app、管理后台、后端和数据库共同使用。

## 建议下一步

1. 对照 `app/llm-wiki/scripts/wiki_web.py` 整理真实 API 路由清单。
2. 把 `docs/api/llm-wiki-api.md` 从建议接口改成当前真实接口表。
3. 在 `shared/` 增加 `source.schema.md`、`concept.schema.md`、`relation.schema.md`、`review-task.schema.md`。
4. 判断 `reader-workbench/` 是否作为独立应用迁出当前仓库。
5. 将管理后台规划为围绕 Source、Concept、Relation、ReviewTask 四类对象的审核与维护界面。
6. 后续再考虑数据库化，先不要急着把文件知识库全部迁移到数据库。

## 启动命令

本地启动 LLM Wiki：

```bash
cd "/Users/Min369/Documents/同步空间/Manju/AIProjects/ResearchManjushri/app/llm-wiki"
python3 scripts/wiki_web.py --host 127.0.0.1 --port 8765
```

打开前端：

```bash
open http://127.0.0.1:8765/
```

如端口被占用：

```bash
lsof -tiTCP:8765 -sTCP:LISTEN | xargs kill
```

## 关键提醒

1. `ResearchManjushri` 是仓库和工程容器。
2. `LLM Wiki` 是当前主产品。
3. GitHub 只同步代码和框架。
4. 本地资料和知识库不要再推到 GitHub。
5. 旧 `ResearchManjusi` Codex 会话保留作历史，不再作为开发入口。
6. 后续开发先定义模块边界和 API，再做页面或具体功能。
