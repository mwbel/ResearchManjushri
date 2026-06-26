# LLM Wiki Reader Workbench

`reader-workbench/` 是一个独立的三栏阅读器模块，用于验证 Moonlight-like 思路：

```text
左栏原文
→ 中栏对齐翻译
→ 右栏 AI 解释 / 笔记 / 候选概念
→ 人工审核
→ LLM Wiki 长期知识层
```

当前实现先使用模拟文档，不改动现有 `LLM Wiki/` 资料、脚本和知识库。

## 本地运行

```bash
cd "/Users/Min369/Documents/同步空间/Manju/AIProjects/ResearchManjusi/reader-workbench"
npm install
npm run dev
```

默认地址：

```text
http://127.0.0.1:5176/
```

## 模块结构

- `src/App.jsx`: 页面状态与模块组合。
- `src/components/`: 顶部工具栏、阅读队列、原文栏、翻译栏、AI 侧栏。
- `src/data/demoDocument.js`: 演示文档和阅读队列。
- `src/adapters/llmWikiAdapter.js`: 预留给 `LLM Wiki` 后端的 API adapter。
- `docs/integration-contract.md`: 后续后端接口契约。
- `assets/concepts/llm-wiki-reader-concept.png`: 本轮界面概念图。

## MVP 已覆盖

- 三栏式阅读界面。
- 原文 block 选中、高亮和搜索。
- 中栏翻译与原文 block 对齐。
- 右栏摘要、解释、笔记、候选概念。
- 顶部页码、缩放、自动翻译、同步滚动、保存到知识库等工作台控件。
- 集成事件日志，用于验证阅读动作如何流向知识库。

## 后续接入顺序

1. 在 `wiki_web.py` 旁新增 `/api/reader/*` 路由，不先改旧 `/api/sources` 语义。
2. 为 PDF/Markdown 生成 `page_id/block_id` 级 artifacts。
3. 翻译和解释按页缓存，避免整本书一次性调用模型。
4. 候选概念只进入 review queue，不直接写入 `wiki/concepts/*.md`。
5. 通过人工审核后复用现有 accepted projection / domain graph 链路。
