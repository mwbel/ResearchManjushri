# AGENTS.md

## 项目目标

本项目仓库名为 `ResearchManjushri`，当前主产品名为 `LLM Wiki`。

`LLM Wiki/` 是当前核心模块：把微信文章、本地文档、论文、笔记等资料编译为可阅读、可追溯、可审核、可扩展的多学科 Markdown 知识网络。

核心链路：

```text
source intake
→ raw source
→ ingest artifacts
→ source summary
→ candidate concepts / relations
→ human review
→ accepted concept projection
→ concept pages
→ domain graph
→ query / analysis / long-term wiki
```

项目目标不是普通 RAG，也不是临时问答；目标是形成长期可维护的个人知识层。

## 执行前规则

默认可以直接执行用户明确提出的修改任务，不需要每次等待确认。

但如果用户明确说：

- 只读
- 先给计划
- 不要修改文件
- 等我批准
- 先分析

则必须严格停留在只读分析或计划阶段，不得编辑、删除、迁移、生成文件，也不得运行会改变项目状态的命令。

如果任务涉及大范围删除、批量迁移、重写知识库结构、清空数据、改动自动 ingest 规则、改动图谱投影规则，必须先输出简短 Preflight Plan。

Preflight Plan 至少包含：

1. 本次任务目标。
2. 准备修改的文件。
3. 明确不会修改的文件或目录。
4. 是否涉及 `raw/`、`wiki/`、`scripts/`、`webui/`。
5. 准备运行的测试命令。
6. 风险与回滚方式。

## 任务执行清单规则

根目录维护统一任务执行清单：

```text
任务执行清单_技术架构与开发进度.md
```

执行开发任务时必须保持清单同步：

1. 新增模块、页面、接口、数据结构或后台能力时，先在任务执行清单中登记对应模块、子任务、状态、优先级和备注。
2. 每完成一个模块或一个可独立验收的子任务，必须即时更新任务执行清单，把状态从 `未开始` 或 `进行中` 改为 `已完成`，并记录完成内容、影响范围和下一步。
3. 如果任务被阻塞，必须把状态标记为 `阻塞`，并写清楚阻塞原因、需要的输入或依赖。
4. 不要为同一个项目拆出多份重复清单；优先维护根目录这份统一清单。

## 项目结构

根目录主要内容：

- `LLM Wiki/`: 当前主要应用与知识库。
- `services/`: 后续可独立运行或被多应用复用的服务模块。
- `domains/`: 软件架构层面的业务领域边界说明。
- `shared/`: 跨模块共享的数据结构、接口约定和通用说明。
- `docs/api/`: LLM Wiki 对外接口契约。
- `docs/architecture/`: 产品命名、模块边界和集成规范。
- `inputs/`: 原始输入资料集合。
- `outputs/`: 临时或手动产出。
- `AI/`: AI 相关资料。
- `本质之探索/`: 用户研究资料与文档。
- `需读论文/`: 待读论文与 PDF。
- `.agents/skills/`: 项目内 agent skill。

`LLM Wiki/` 内部规则更细，修改该目录前必须优先阅读：

```text
LLM Wiki/AGENTS.md
LLM Wiki/README.md
```

如果根目录规则与 `LLM Wiki/AGENTS.md` 冲突，处理 `LLM Wiki/` 内文件时以 `LLM Wiki/AGENTS.md` 的领域规则为准；但用户在当前对话里的最新明确指令优先级最高。

## LLM Wiki 当前定位

`LLM Wiki/` 是知识编译系统。

后续所有新增能力默认按模块化开发：先明确领域对象、接口输入输出、状态流转和错误处理，再接入前端 app、管理后台、后端服务或数据库。

不同应用集成 LLM Wiki 能力时，优先通过 HTTP API、adapter 或 `services/` 中的可复用服务，不要绕过核心后端直接改写 `raw/`、`wiki/`。

三层数据：

1. `LLM Wiki/raw/`
   - 原始资料层。
   - `raw/sources/<domain>/<year>/` 存放 source stub。
   - `raw/assets/uploads/...` 存放上传附件。
   - 默认不要改写原始资料正文，除非用户明确要求。

2. `LLM Wiki/wiki/`
   - 长期知识层。
   - `wiki/sources/`: 每份资料的 source summary。
   - `wiki/concepts/`: 概念页。
   - `wiki/domains/`: 学科网络入口。
   - `wiki/analyses/`: 查询或专题分析沉淀。

3. `LLM Wiki/scripts/` 与 `LLM Wiki/webui/`
   - `scripts/wiki_web.py`: 本地 HTTP 服务、API 与 Web UI 后端。
   - `webui/`: 前端页面。
   - `scripts/mvp_*`: MVP ingest、候选概念、review、projection 相关逻辑。

## 学科与来源约束

当前不允许应用自动创建错误的新学科。

允许显示和操作的既有学科应包括：

- `ai`
- `ai智能体`
- `math`
- `modern-astronomy`
- `physics`
- `tibetan-astronomy-calendar`
- `世界模型`
- `垂直小模型`

除非用户明确要求恢复“新增学科”功能，否则不要重新打开自动发现学科、自动新增学科或前端 `＋ 新增学科`。

如果本地资料的 `local_path` 指向的文件不存在，必须向用户报错“文件不存在”，不要静默使用 summary fallback。

## Web UI 服务

当前前后端由同一个 Python HTTP 服务提供。

常用启动命令：

```bash
cd "/Users/Min369/Documents/同步空间/Manju/AIProjects/ResearchManjushri/LLM Wiki"
lsof -tiTCP:8765 -sTCP:LISTEN | xargs -r kill
python3 scripts/wiki_web.py --host 127.0.0.1 --port 8765
```

浏览器打开：

```bash
open http://127.0.0.1:8765/
```

修改 `scripts/wiki_web.py` 后需要重启服务。

修改 `webui/*.js`、`webui/*.html`、`webui/*.css` 后通常刷新浏览器即可。

## 修改边界

除非任务明确要求，否则不要修改：

1. `.git/`
2. `.agents/skills/`
3. `inputs/` 原始资料
4. `本质之探索/` 原始文档
5. `需读论文/` PDF 原件
6. `raw/assets/uploads/` 中的上传原件
7. 已归档的 `wiki/.archive/`
8. `.DS_Store`
9. 未跟踪但看起来是用户备份的文件，例如 `AGENTS_副本.md`、`LLM Wiki/AGENTS.md.bak`

不要恢复、删除或覆盖用户已有未提交改动，除非用户明确要求。

如果需要清理错误生成的资料、概念、学科或附件，必须先列出将删除的路径。

## 内容维护规则

维护 wiki 时遵守：

1. 先读 `LLM Wiki/wiki/00-meta/index.md` 或相关 domain page，理解已有结构。
2. 新结论要能追溯到 source。
3. 概念页要尽量保留 `sources: [...]`。
4. 不要把临时总结直接写入 raw source。
5. 删除概念页优先归档，不要无痕删除。
6. 合并概念时保留 alias、来源证据和关系说明。
7. 新资料如果只是登记，不要急着写入长期概念页。

## 前端与交互规则

`LLM Wiki/webui/` 是工作台，不是营销页。

设计原则：

- “知识工作台”是任务中枢。
- “资料列表”是资料管理区。
- “当前概念”是阅读和编辑区。
- “概念网络”是探索和回溯区。

避免让用户从图谱底部跳到页面顶部后丢失上下文。需要查看来源时，优先在右侧或当前上下文显示证据；只有需要编辑资料时才跳转到资料管理区。

图标按钮优先使用清晰符号，窄栏中不要使用竖排文字按钮。

## 测试与检查

常用检查命令：

```bash
cd "/Users/Min369/Documents/同步空间/Manju/AIProjects/ResearchManjushri/LLM Wiki"
python3 -m py_compile scripts/wiki_web.py scripts/mvp_concept_reviews.py scripts/mvp_ingest_artifacts.py scripts/mvp_ingest_runner.py scripts/rebuild_domain_network.py
node --check webui/app.js
curl -I http://127.0.0.1:8765/
```

如果改动 ingest、concept review、projection 或 domain graph，至少检查：

```bash
python3 -m py_compile scripts/wiki_web.py scripts/mvp_concept_reviews.py scripts/mvp_ingest_artifacts.py scripts/mvp_ingest_runner.py
python3 scripts/rebuild_domain_network.py --domain ai
python3 scripts/rebuild_index.py
```

如果改动前端交互，至少检查：

```bash
node --check webui/app.js
curl -I http://127.0.0.1:8765/
```

如果服务已运行且改动了后端：

```bash
lsof -tiTCP:8765 -sTCP:LISTEN | xargs -r kill
python3 scripts/wiki_web.py --host 127.0.0.1 --port 8765
```

## Git 与工作区规则

当前仓库可能长期存在大量未提交改动。

执行前先看：

```bash
git status --short
```

不要使用：

```bash
git reset --hard
git checkout -- .
```

除非用户明确要求。

不要把无关的大量知识库变更混入小功能修复说明里。最终回答只说明本次实际相关改动和验证结果。

## 回答风格

默认用中文回答。

回答应简洁、具体、可执行。完成修改后说明：

1. 改了什么。
2. 影响哪个功能。
3. 运行了哪些验证。
4. 如果需要刷新或重启服务，明确写出。

不要泛泛解释，不要把用户看不到的命令输出原样堆给用户。

## 提示词记录规范（新增）
- 每次对话要求的提示词需归档到 `提示词历史.md`，格式为：时间、对话序号、提示词内容。
- 每次还需新增一份单一汇总文档，文件名格式：`第N次-YYYYMMDDHHMM-任务重点-前端app-管理后台-后端-数据库.md`。
- 汇总文档必须包含：本次任务重点、下一步行动、前端app/管理后台/后端/数据库各自下一步。
- 同一轮只保留一份汇总文档，不可拆成四份独立 markdown。

## 提示词记录规范（新增）
- 每次对话要求的提示词需归档到 `提示词历史.md`，格式为：时间、对话序号、提示词内容。
- 每次还需新增一份单一汇总文档，文件名格式：`第N次-YYYYMMDDHHMM-任务重点（20字）-前端app-管理后台-后端-数据库.md`。
- 汇总文档必须包含：本次任务重点、下一步行动、前端app/管理后台/后端/数据库各自下一步。
- 同一轮只保留一份汇总文档，不可拆分为多份。

## 提示词记录规范（新增）
- 每次对话要求的提示词需归档到 `提示词历史.md`，格式为：时间、对话序号、提示词内容。
- 每次还需新增一份单一汇总文档，文件名格式：`第N次-YYYYMMDDHHMM-任务重点（20字）-前端app-管理后台-后端-数据库.md`。
- 汇总文档必须包含：本次任务重点、下一步行动、前端app/管理后台/后端/数据库各自下一步。
- 同一轮只保留一份汇总文档，不可拆分为多份。

## 提示词记录规范（新增）
- 每次对话要求的提示词需归档到 提示词历史.md，格式为：时间、对话序号、提示词内容。
- 每次还需新增一份单一汇总文档，文件名格式：第N次-YYYYMMDDHHMM-任务重点（20字）-前端app-管理后台-后端-数据库.md。
- 汇总文档必须包含：本次任务重点、下一步行动、前端app/管理后台/后端/数据库各自下一步。
- 同一轮只保留一份汇总文档，不可拆分为多份。
