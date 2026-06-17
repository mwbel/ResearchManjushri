# LLM Wiki Starter Kit

这是一个按 `llm-wiki` 思路搭起来的个人知识库骨架：`raw/` 保存原始资料，`wiki/` 保存由 LLM 维护的结构化知识页，`CODEX-AGENTS.md` 规定 Codex 侧维护规则，`scripts/` 提供几个轻量工具。

## 目录结构

- `llm-wiki.md`: 这次方案的原始设计文档。
- `raw/sources/`: 原始资料仓库，按学科再按年份归档。
- `raw/assets/`: 文章图片、截图、附件。
- `wiki/`: LLM 持续维护的知识层。
- `wiki/domains/`: 自动生成的单学科知识网络入口，串联资料、页面和后续动作。
- `scripts/`: 新建 source、重建索引、基础 lint。
- `webui/`: 本地资料录入前端。
- `templates/`: 新资料和 wiki 页面模板。
- `CODEX-AGENTS.md`: 给 Codex 用的操作规范。
- `CLAUDE-AGENTS.md`: 给 Claude Code 用的操作规范。
- `.codex/`: Codex 私有草稿和临时工作区。
- `.claude/`: Claude Code 私有草稿和临时工作区。

## 先怎么用

1. 把新的文章、笔记、访谈整理到 `raw/sources/<domain>/<year>/`。
2. 对 Codex 说：
   `请按 CODEX-AGENTS.md 的 ingest 流程处理 /绝对路径/到某个 source 文件。`
3. 处理完成后，查看 [home.md](wiki/00-meta/home.md)、[index.md](wiki/00-meta/index.md) 和对应的 [domain network](wiki/domains/)。
4. 提问题时，优先让 LLM 基于 `wiki/` 回答；如果结果值得沉淀，再让它写回 `wiki/analyses/`。

## 常用命令

```bash
python3 scripts/new_source.py --title "文章标题" --kind article --domain math
python3 scripts/new_source.py --title "网页文章标题" --kind article --domain math --url "https://example.com/article"
python3 scripts/new_source.py --title "本地论文标题" --kind paper --domain math --local-path "/absolute/path/to/file.pdf"
python3 scripts/rebuild_domain_network.py
python3 scripts/rebuild_index.py
python3 scripts/lint_wiki.py
python3 scripts/wiki_web.py
```

目前预设的学科目录：

- `math`: 数学
- `physics`: 物理
- `tibetan-astronomy-calendar`: 西藏天文历算
- `modern-astronomy`: 现代天文学

同时预留：

- `general`: 尚未归入具体学科的通用资料
- `llm-wiki`: 这个知识库自身的设计与维护资料

## 多代理协作规则

- `raw/`、`wiki/`、`scripts/`、`templates/` 是共享层，Codex 和 Claude Code 都可以使用。
- 不要为不同代理复制两套 `wiki/`，知识库必须保持单一版本。
- Codex 读取 `CODEX-AGENTS.md`，Claude Code 读取 `CLAUDE-AGENTS.md`。
- 一次性计划、临时笔记、草稿输出分别放在 `.codex/` 和 `.claude/`。
- 正式沉淀的内容只能进入 `wiki/`，不要长期留在代理私有目录。
- 更新 `wiki/00-meta/log.md` 时，建议写明 `agent: codex` 或 `agent: claude`。

## 推荐工作流

### 1. Ingest

可直接这样说：

```text
请按 CODEX-AGENTS.md 的 ingest 流程处理 raw/sources/math/2026/2026-04-07-example.md。
重点关注：核心观点、和现有页面的关系、是否要新建 concept page。
```

### 2. Single-Discipline Network

先把一个学科内部的资料网络打稳，再做跨学科连接：

```bash
python3 scripts/new_source.py \
  --domain tibetan-astronomy-calendar \
  --kind article \
  --title "新的网页文章" \
  --url "https://example.com/article" \
  --tags "eclipse,calendar"

python3 scripts/new_source.py \
  --domain tibetan-astronomy-calendar \
  --kind paper \
  --title "本地资料标题" \
  --local-path "/absolute/path/to/file.pdf"

python3 scripts/rebuild_domain_network.py --domain tibetan-astronomy-calendar
python3 scripts/rebuild_index.py
python3 scripts/lint_wiki.py
```

对应入口会生成在：

- `wiki/domains/tibetan-astronomy-calendar.md`
- `wiki/domains/math.md`
- `wiki/domains/physics.md`
- `wiki/domains/modern-astronomy.md`

当一个 source 真正值得长期使用时，再让 LLM 把它升级为 `wiki/sources/...` source summary，并把关键概念写入 `wiki/concepts/...`。

### 3. Web UI

如果不想用命令行新增资料，可以启动本地前端：

```bash
python3 scripts/wiki_web.py
```

默认地址：

- `http://127.0.0.1:8765`

前端支持：

- 新增网页文章 source stub
- 新增本地资料 source stub，并可直接上传文件到 `raw/assets/uploads/<domain>/<year>/`
- 新增笔记 source stub
- 在学科下拉框中选择 `＋ 新增学科`，为新学科创建第一个 source stub 和对应 domain network
- 预览即将写入的 Markdown
- 勾选 `自动 ingest` 后，写入 raw source 的同时生成 `wiki/sources/...` source summary
- 勾选 `概念网络` 后，会从 source summary 自动生成/更新 `wiki/concepts/...` 候选概念页和概念关系
- 在“最近资料”中对已有 source 点 `Ingest`，可补跑自动 ingest
- 在“最近资料”中可选择新学科并点 `修改学科`，修正已有 source 的学科归属
- 在“概念网络”面板中选择学科，可直接查看概念节点图和关系证据表
- 点击概念节点、关系表中的概念名或百科正文中的概念链接，可打开类 Wikipedia 的概念页面
- 写入后自动重建单学科网络和总索引
- 可选运行 lint

自动 ingest 当前是本地规则版：

- 读取 raw source 的 frontmatter、收录理由、摘录和备注
- 微信公众号文章会优先调用本机 `wechat_crawler` 模块解析正文
- 其他网页资料会尝试抓取 `source_url` 的可读文本
- 本地 `.md`、`.txt`、`.csv`、`.tsv` 会尝试读取正文
- 本地 `.docx` 会尝试读取段落和表格文本
- PDF、旧版 `.doc` 等资料先只登记路径，不直接解析
- 生成 source summary 后会把 raw source 的 `status` 标为 `active`

概念网络当前是本地规则版：

- 从 source summary 的摘要、Main Takeaways、Extracted Notes 中抽取候选概念
- 自动生成或更新 `wiki/concepts/...` 页面，并保留 source-derived evidence
- 抽取概念之间的候选关系，写入 `Source-Derived Relations`
- `scripts/rebuild_domain_network.py` 会把这些关系渲染到学科页的 `Concept Graph` 和 `Concept Relations`
- Web UI 会通过 `/api/concepts/graph?domain=<domain>` 把同一份关系数据渲染成 SVG 概念图和关系表
- 前端概念图借鉴 easyML 的知识图谱形式，使用 D3 力导向布局、缩放平移、节点拖拽和点击查看证据；当前不显示 `level`/`Lv` 标签
- Web UI 会通过 `/api/concepts/page?slug=<concept>&domain=<domain>` 渲染类 Wikipedia 概念页，并基于同学科 concept catalog 自动把正文中的概念变成跳转链接
- 候选概念页默认带 `auto-concept` 标签，等待后续人工整理定义、边界和跨学科桥接

本地上传说明：

- 在“本地”模式下选择文件，应用会先复制文件到 `raw/assets/uploads/...`
- source 的 `local_path` 会写入复制后的稳定绝对路径
- `.md`、`.txt`、`.csv`、`.tsv`、`.docx` 上传后可被自动 ingest 读取正文
- PDF、旧版 `.doc` 等文件会先进入资料库，后续可再接专门解析器

默认微信爬虫路径：

- `/Users/Min369/Documents/同步空间/Manju/AIProjects/MZ数据库/心之髓/wechat_crawler`

如果以后移动了爬虫目录，可用环境变量覆盖：

```bash
LLM_WIKI_WECHAT_CRAWLER="/path/to/wechat_crawler" python3 scripts/wiki_web.py
```

后续可在这个脚本上接 LLM 摘要、概念抽取和跨学科关系建议。

### 4. Query

```text
请先读 wiki/00-meta/index.md，再回答：
目前 wiki 里关于 LLM Wiki 的核心设计原则是什么？
回答后把一页可复用的结论写入 wiki/analyses/。
```

### 5. Lint

```text
请对整个 wiki 做一次 lint：
检查断链、孤儿页面、过时结论、缺失但高频出现的概念页，并更新 inbox 与 log。
```

## 设计取向

- 文件尽量是普通 Markdown，方便 Obsidian、git、任意编辑器一起用。
- frontmatter 只用简单字段，脚本不依赖第三方库。
- `index.md` 由脚本重建，`log.md` 由 LLM 追加维护。
- 先用目录 + 索引检索，不急着上向量库。
- 先把单学科网络打成稳定的资料-概念-问题图，再扩展到跨学科 LLM Wiki。
- 多代理共享一套知识库，差异只体现在代理规则和临时工作区。
- 原始资料按学科归档，知识页保持统一网络，允许跨学科链接。
