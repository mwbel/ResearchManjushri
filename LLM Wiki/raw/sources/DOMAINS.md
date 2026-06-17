# Source Domains

当前这个仓库推荐使用以下学科目录：

- `general`: 通用、暂未归类资料
- `llm-wiki`: 知识库自身的设计与维护资料
- `math`: 数学
- `physics`: 物理
- `tibetan-astronomy-calendar`: 西藏天文历算
- `modern-astronomy`: 现代天文学

推荐目录结构：

```text
raw/sources/<domain>/<year>/<date>-<slug>.md
```

例如：

- `raw/sources/math/2026/2026-04-07-euclid-notes.md`
- `raw/sources/physics/2026/2026-04-07-quantum-overview.md`
- `raw/sources/tibetan-astronomy-calendar/2026/2026-04-07-calendar-method.md`
- `raw/sources/modern-astronomy/2026/2026-04-07-exoplanet-survey.md`

新增网页文章：

```bash
python3 scripts/new_source.py \
  --domain math \
  --kind article \
  --title "文章标题" \
  --url "https://example.com/article" \
  --tags "logic,proof"
```

新增本地资料：

```bash
python3 scripts/new_source.py \
  --domain math \
  --kind paper \
  --title "资料标题" \
  --local-path "/absolute/path/to/file.pdf"
```

生成学科网络：

```bash
python3 scripts/rebuild_domain_network.py --domain math
```

原则：

- 路径用稳定英文 slug。
- frontmatter 中可写中文 `domain_label`。
- 网页资料用 `source_url` 记录原文链接。
- 本地资料用 `local_path` 记录稳定路径，不把大文件直接塞进 Markdown。
- `status: inbox` 表示已登记但尚未 ingest；`status: active` 表示已经沉淀进 wiki。
- `wiki/` 页面保持统一网络，不按学科硬隔离。
- 当一个主题跨多个学科时，优先在 `wiki/` 中用链接和 tags 建立关系，而不是复制页面。
