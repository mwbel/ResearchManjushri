---
title: Wiki Log
type: meta
status: active
created: 2026-04-07
updated: 2026-06-17
summary: 记录这个 wiki 的 ingest、query、lint 时间线。
tags: [log, meta]
sources: []
---

# Wiki Log

## [2026-04-07] setup | Initialize starter kit

- 建立了 `raw/`、`wiki/`、`scripts/`、`templates/` 基础结构。
- 新增 `CODEX-AGENTS.md` 作为 Codex 维护规范。
- 新建首页、索引、inbox、seed source summary 与概念页。
- 后续可直接开始 ingest 新资料。

## [2026-04-07] setup | Add multi-agent conventions

- agent: codex
- 新增 `CLAUDE-AGENTS.md`，让 Claude Code 与 Codex 共用同一套 wiki 规则。
- 新增 `.codex/` 与 `.claude/` 私有工作区说明，用来存放临时草稿。
- 更新 `README.md`，明确共享层与代理私有层的边界。

## [2026-04-07] setup | Add domain-based source organization

- agent: codex
- 将 `raw/sources/` 的推荐结构调整为按学科再按年份归档。
- 预设 4 个学科目录：数学、物理、西藏天文历算、现代天文学。
- 更新 `new_source.py`，支持用 `--domain` 自动写入对应目录和 frontmatter。

## [2026-04-07] setup | Add discipline concept hubs

- agent: codex
- 新增 4 个学科总览页：数学、物理、西藏天文历算、现代天文学。
- 更新首页与 inbox，使后续 ingest 可以围绕学科主线展开。
- 为跨学科研究预留了数学-物理-现代天文学-传统历算之间的互链结构。

## [2026-04-07] ingest | 藏历的原理与实践（中文）

- agent: codex
- processed source: `raw/sources/tibetan-astronomy-calendar/藏历的原理与实践-中文.md`
- 新建 source summary：`wiki/sources/2026-04-07-zangli-principles-practice-zh.md`
- 新建概念页：`wiki/concepts/tibetan-eclipse-calculation.md`
- 更新 `wiki/concepts/tibetan-astronomy-calendar.md`，把交食推步确立为当前第一条已展开的专题主线。
- 待跟进：补书目信息，拆出术语与单位表、参数总表，以及传统历算与现代天文学的对照页。

## [2026-04-07] analysis | Split shixian and kalachakra algorithm pages

- agent: codex
- 新建 `wiki/analyses/shixian-eclipse-step-by-step.md`，把时宪历月食与日食算法拆成逐步流程。
- 新建 `wiki/analyses/kalachakra-eclipse-step-by-step.md`，把当前资料中能直接确认的时轮历算法骨架单独整理出来。
- 更新西藏天文历算主线页面，补入两条分析页链接。
- 待跟进：补一份时轮历原始算例，把“算法骨架页”升级成严格的逐步拆解页。

## [2026-04-09] handoff | Save chat history for team mode

- agent: codex
- 新建 `wiki/analyses/2026-04-09-team-handoff-chat-history.md`
- 以交接文档形式保存本次搭建与 ingest 过程，供切换到 team 模式后继续使用。

## [2026-04-09] handoff | Save verbatim visible transcript

- agent: codex
- 新建 `wiki/analyses/2026-04-09-verbatim-chat-transcript.md`
- 保存当前线程的用户可见逐字转录，不包含工具输出与隐藏系统提示。

## [2026-04-09] concept | Add terms and parameter reference pages

- agent: codex
- 新建 `wiki/concepts/tibetan-eclipse-terms-and-units.md`
- 新建 `wiki/concepts/tibetan-eclipse-parameters.md`
- 更新西藏天文历算主线页与 source summary，把术语表和参数总表接入现有交食推步主线。
- 待跟进：继续拆时宪历月食算例页、时宪历日食算例页，以及现代对照页。

## [2026-06-17] setup | Add single-discipline knowledge networks

- agent: codex
- 新增 `scripts/rebuild_domain_network.py`，自动生成 `wiki/domains/<domain>.md` 单学科知识网络页。
- 扩展 `scripts/new_source.py`，支持用 `--url` 登记网页文章、用 `--local-path` 登记本地资料，并记录额外标签、作者和发布日期。
- 更新 `scripts/rebuild_index.py`，让 `type: domain` 页面进入总索引。
- 更新 `scripts/lint_wiki.py`，允许 wiki 页面链接到真实存在的 `raw/` 资料文件。
- 新增 `templates/domain-network.md`，补齐 `wiki/sources/` 中缺失的两个 source summary。
- 已生成 `wiki/domains/general.md`、`wiki/domains/llm-wiki.md`、`wiki/domains/math.md`、`wiki/domains/physics.md`、`wiki/domains/tibetan-astronomy-calendar.md`、`wiki/domains/modern-astronomy.md`。
- 待跟进：为选定的第一门学科登记 5 到 10 个真实网页/本地资料 source stub，再逐步升级为 source summary 与 concept 页面。

## [2026-06-17] setup | Add local intake web UI

- agent: codex
- 新增 `scripts/wiki_web.py` 本地 Web 服务。
- 新增 `webui/index.html`、`webui/styles.css`、`webui/app.js`，提供网页、本地资料、笔记三类 source stub 的表单录入。
- 前端支持预览 Markdown、写入 raw source、重建单学科网络、重建总索引和可选 lint。
- 已验证健康接口、静态页面、预览接口、真实写入与清理、Python 编译和 wiki lint。

## [2026-06-17] setup | Allow custom disciplines in intake UI

- agent: codex
- 更新前端学科选择器，新增 `＋ 新增学科` 选项。
- 新增学科时可以填写显示名称和稳定 slug，写入后会创建对应 `raw/sources/<domain>/` 目录。
- 更新 `scripts/wiki_web.py` 与 `scripts/rebuild_domain_network.py`，让新学科的 domain network 使用 source frontmatter 中的 `domain_label`。
- 已验证新增学科预览、真实写入、domain network 中文标题生成，并清理临时测试学科。

## [2026-06-17] setup | Add local automatic ingest

- agent: codex
- 新增 `scripts/auto_ingest.py`，可从 `raw/sources/...` 自动生成 `wiki/sources/...` source summary。
- Web UI 新增 `自动 ingest` 复选框，新增资料时默认同时生成 source summary。
- “最近资料”卡片新增 `Ingest` 操作，可对已有 raw source 补跑自动 ingest。
- 自动 ingest 会读取 frontmatter、收录理由、摘录、备注，并尝试读取网页或文本型本地文件内容。
- 生成 source summary 后会把 raw source 的 `status` 更新为 `active`，再重建对应学科网络和总索引。
- 已用临时资料验证 raw source 写入、source summary 生成、domain network 接入、状态更新与清理流程。

## [2026-06-17] setup | Integrate WeChat crawler for protected articles

- agent: codex
- `scripts/auto_ingest.py` 现在会对 `mp.weixin.qq.com` URL 优先调用本机 `wechat_crawler/enhanced_web_crawler.py`。
- 默认爬虫路径为 `/Users/Min369/Documents/同步空间/Manju/AIProjects/MZ数据库/心之髓/wechat_crawler`，也可用 `LLM_WIKI_WECHAT_CRAWLER` 覆盖。
- 增加微信验证页/风控页识别，避免把“环境异常”“去验证”等页面文本写入 source summary。
- 已重新 ingest `ai智能体` 下 3 篇微信公众号文章，source summary 现在显示 `Extraction: wechat crawler fetched`，并带有作者、HTML 长度与正文摘录。

## [2026-06-17] setup | Add local file upload

- agent: codex
- Web UI 的“本地”模式新增文件选择控件。
- 新增 `/api/uploads`，会将浏览器上传的文件复制到 `raw/assets/uploads/<domain>/<year>/` 并返回稳定绝对路径。
- 新增本地资料时，如果选择了文件，前端会先上传文件，再把上传后的路径写入 source 的 `local_path`。
- 已验证上传 txt、创建 local source、自动 ingest 读取上传正文、重建网络与清理测试文件。

## [2026-06-17] setup | Parse docx and edit source domains

- agent: codex
- `scripts/auto_ingest.py` 新增 `.docx` 读取能力，会提取 Word 段落和表格文本。
- Web UI 的“最近资料”新增学科下拉框和 `修改学科` 操作。
- 新增 `/api/sources/domain`，可修改 raw source 的 `domain`、`domain_label`、`tags`，必要时移动 raw source 和本地上传文件，并重建新旧学科网络。
- 已重新 ingest `对Transformer的批判2：Transformer能输出知识吗`，source summary 现在显示 `Extraction: docx read`。

## [2026-06-17] setup | Build concept network from ingested sources

- agent: codex
- 新增 `scripts/concept_ingest.py`，可从 `wiki/sources/...` source summary 中抽取候选概念和 source-derived relations。
- 自动生成或更新 `wiki/concepts/...`，并在 concept 页中保留 `Source-Derived Evidence` 与 `Source-Derived Relations`。
- `scripts/rebuild_domain_network.py` 新增 `Concept Graph` 和 `Concept Relations` 区块，会汇总同学科 concept 页中的候选关系。
- Web UI 新增 `概念网络` 复选框；新增资料、补跑 `Ingest`、修改学科时默认接入概念网络生成。
- 学科修改流程会把自动概念页从旧学科标签迁移到新学科标签，减少错误归类残留。

## [2026-06-17] setup | Visualize concept graph in Web UI

- agent: codex
- 新增 `/api/concepts/graph?domain=<domain>`，返回指定学科的概念节点、关系边和证据文本。
- Web UI 新增“概念网络”面板，可选择学科并查看 SVG 节点图与关系表。
- 图谱数据来自 `wiki/concepts/...` 中的 `Source-Derived Relations`，与 domain network 的 `Concept Graph` 保持同源。
- 已用 `ai智能体` 验证接口返回 22 个节点和 16 条关系，前端静态资源、Python 编译、JS 语法和 wiki lint 均通过。

## [2026-06-17] update | Borrow easyML-style force graph

- agent: codex
- 概念网络前端从静态环形图调整为 D3 力导向图，借鉴 easyML 的知识图谱交互形式。
- 支持缩放、平移、节点拖拽、点击节点或关系查看来源证据。
- 按当前需求不显示 `level`/`Lv` 标签。
- 保留关系表作为可审阅的证据视图。

## [2026-06-17] setup | Add Wikipedia-style concept reader

- agent: codex
- 新增 `/api/concepts/page?slug=<concept>&domain=<domain>`，返回概念页 frontmatter、Markdown 正文、同学科 catalog 和相关关系。
- Web UI 的“概念网络”面板新增类 Wikipedia 概念阅读器，包含正文、摘要、状态/路径信息框、相关概念和关系证据侧栏。
- 点击图谱节点、关系表中的概念名、正文中的自动概念链接，都会在阅读器中跳转到对应概念页。
- 正文链接基于同学科 concept catalog 自动生成，不引入 `level` 标签。

## [2026-06-17] fix | Improve source-derived concept pages

- agent: codex
- 修复自动概念页内容过空的问题：`scripts/concept_ingest.py` 现在会为每个概念选择包含该概念的正文证据句。
- `Working Definition` 会使用概念相关摘录生成 source-derived 草稿，而不是统一写“待整理”。
- `Source-Derived Evidence` 不再默认使用文章标题或第一句，而是优先使用概念命中的证据句。
- 已重新生成 `注意力机制`，页面现在包含“结构化的噪声引入（Noise Leading In, NLI）”相关定义、证据和关系。

## [2026-06-17] update | Optimize Web UI reading flow

- agent: codex
- 将资料入口从上下堆叠布局调整为三栏工作台：左侧为学科网络和最近资料，中间为概念图谱与类 Wikipedia 阅读器，右侧为新增资料和运行结果。
- 让最新阅读内容和概念网络进入首屏主区域，新增资料表单作为右侧 composer 保持随手可用。
- 增加桌面、窄屏和手机断点，窄屏时优先显示阅读区，再显示新增资料和导航。

## [2026-06-17] setup | Add knowledge workbench queue

- agent: codex
- 新增 `/api/workbench?domain=<domain>`，按学科汇总 raw sources、source summaries、concepts、relations 与待整理队列。
- Web UI 中央主区域新增“知识工作台”，展示当前学科的统计、待整理概念、待补资料和最近更新。
- 待整理概念可直接跳转到类 Wikipedia 概念阅读器，帮助从“导入资料”进入“整理知识”的下一步。

## [2026-06-17] setup | Add Sciverse academic search entry

- agent: codex
- 新增 `/api/sciverse/search`，通过本地 `sciverse` skill 脚本调用 `semantic_search` 或 `search_papers`。
- Web UI 右侧新增“学术检索”面板，可填写本次会话 Sciverse token、选择语义证据或论文元数据检索。
- Token 不写入项目文件或日志；后端仅在调用 Sciverse 子进程时通过环境变量传递。

## [2026-06-17] setup | Close Sciverse source/evidence loop

- agent: codex
- 新增 `/api/sciverse/import-source`，可把 Sciverse 论文结果转换为 `source_type: sciverse` 的 raw source，并接入现有 auto ingest、概念网络和索引重建流程。
- 新增 `/api/concepts/academic-evidence`，可把选中论文作为 `Academic Evidence` 写入当前 concept 页，和 `Source-Derived Evidence` 分层保存。
- Web UI 的 Sciverse 结果卡片新增 `导入 source`、`补强当前概念`、`导入并补强` 三个动作，形成“检索论文 → 导入 source → 补强 concept”的闭环。

## [2026-06-17] setup | Automate Sciverse token loading

- agent: codex
- 新增 `scripts/store_sciverse_token.command`，用于把 Sciverse API token 存入 macOS Keychain。
- 新增 `start_llm_wiki.command`，启动 Web UI 时自动从 Keychain 读取 token 并导出为 `SCIVERSE_API_TOKEN`。
- README 增加 Keychain 启动说明，避免把 token 写入项目文件、日志或前端代码。

## [2026-06-17] fix | Shorten Sciverse network errors

- agent: codex
- 将 Sciverse `fetch failed`、`UND_ERR_SOCKET`、认证失败和限额错误映射为简短中文提示，避免 Node stack trace 撑满前端右栏。
- 限制 Sciverse 结果区域高度并允许滚动，长错误或长结果不再破坏资料入口布局。
- 本地诊断显示 `api.sciverse.space` 当前解析到 `198.18.0.173`，属于本机代理/TUN/fake-ip 网络路径，需要优先检查代理节点或模式。

## [2026-06-17] fix | Add curl fallback for Sciverse

- agent: codex
- Sciverse 检索默认继续优先调用本地 skill 的 Node 脚本。
- 当 Node `fetch/undici` 出现 `UND_ERR_SOCKET`、`fetch failed` 或 `other side closed` 时，后端会自动退回系统 `curl` 调用 Sciverse API。
- 可用 `SCIVERSE_TRANSPORT=curl ./start_llm_wiki.command` 强制 Sciverse 全程走 curl，适配代理/TUN/fake-ip 下 Node fetch 不稳定的场景。

## [2026-06-17] fix | Guard concept graph from metadata/tool noise

- agent: codex
- 收紧 `scripts/concept_ingest.py` 的候选概念规则，过滤 `Title`、`Author`、`Doc ID`、`DOI`、`Score`、`Offset`、`Sciverse`、`academic`、`RAG`、`LightRAG` 等工具和元数据词。
- Sciverse source 现在默认只作为 source/evidence 导入，不再自动触发概念网络生成；论文元数据保存在 Notes，正文摘录才进入 source summary。
- Web UI 新增 `删除当前概念`，会删除概念页并清理其他概念页中指向它的自动关系。
- 已清理 `ai智能体` 图谱中的 metadata/tool 污染节点并重建全部 domain network。

## [2026-06-17] update | Auto-read Sciverse token from Keychain

- agent: codex
- Sciverse 调用现在按 `SCIVERSE_API_TOKEN`、前端本次 token、macOS Keychain `llm-wiki-sciverse` 的顺序读取 token。
- 开发期可直接运行 `python3 scripts/wiki_web.py`，前端 Sciverse Token 留空也能使用 Keychain 中的 token。
- README 和前端占位文案已更新，token 仍不写入项目文件或前端代码。

## [2026-06-17] setup | Add per-domain source management

- agent: codex
- 新增 `/api/sources?domain=...`、`/api/sources/update`、`/api/sources/delete`，支持按学科查看、编辑和删除 raw source。
- Web UI 新增“学科资料”面板；点击左侧学科会同步切换工作台、概念图谱和该学科资料列表。
- `新增到此学科` 会把新增资料表单预选到当前学科；资料卡片可展开编辑、修改学科、保存、Ingest 或删除。
- 删除资料时会删除 raw source 和对应 source summary，但保留本地上传的原始文件，避免误删资料库资产。

## [2026-06-18] setup | Add Science main-journal candidate tracker

- agent: codex
- 新增 `/api/trackers/science`，通过 Sciverse 元数据检索使用 `Science + topic + years` 查询，默认跟踪 `hierarchical memory` 近两年候选论文。
- Web UI 右侧新增“Science 主刊候选追踪”面板，可设置主题、年份和数量，并复用论文结果卡片。
- 追踪结果会根据返回的期刊字段显示 `Science match` 或“候选，需核对期刊”，避免把宽松检索误判成主刊命中。
- Science 追踪结果可直接导入 source 或补强当前概念；导入时自动增加 `science-main`、`journal-tracker`、`memory` 标签。

## [2026-06-18] update | Improve intake and concept reading flow

- agent: codex
- 将“新增资料”移动到最左侧学科栏上方，并增加隐藏/恢复按钮，减少非录入状态下的视觉占用。
- 概念页现在优先显示类 Wikipedia 阅读器，再把关系表折叠为辅助信息，避免关系明细压住概念解释。
- 将右侧“结果”改名为“运行日志”，说明它显示操作返回而不是知识正文。
- 为 `Skill` / `Skills` 补充人工可读定义、价值说明，并在前端首屏显示“简明解释”。

## [2026-06-18] update | Add direct source deletion and concept cleanup

- agent: codex
- 在“最近资料”“待补资料”“最近更新”和“学科资料”中提供直接删除入库资料的入口。
- 删除资料时会删除 raw source 与对应 source summary，并默认移除只由该资料生成的孤立 `auto-concept` 页面。
- 删除时保留本地上传的原始文件，避免误删本地资料库资产。
