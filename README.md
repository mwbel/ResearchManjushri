# LLM Wiki

LLM Wiki 是 ResearchManjushri 仓库当前的主产品名。

本项目的目标是把微信文章、本地文档、论文、笔记等研究资料，整理成可追溯、可审核、可扩展的个人知识网络。

当前核心实现位于：

```text
LLM Wiki/
```

根目录用于承载模块化开发边界、共享接口契约和后续应用集成规范。

## 产品定位

LLM Wiki 不是临时问答工具，也不是单次 RAG demo。它是长期知识编译系统：

```text
资料导入
-> 原始资料归档
-> 摘要与候选概念抽取
-> 人工审核
-> 概念页与关系投影
-> 学科知识图谱
-> 被不同应用通过 API 复用
```

## 模块化方向

后续所有新增能力默认按模块化方式开发。

模块之间通过稳定接口集成，不直接互相读取内部实现文件。

推荐边界：

- `LLM Wiki/`: 核心知识编译模块，保留现有 Web UI、API、raw/wiki 数据层。
- `services/`: 可独立运行或被多应用调用的服务模块。
- `domains/`: 领域模块定义，例如资料、概念、图谱、审核、阅读等。
- `shared/`: 跨模块共享的数据结构、接口约定和通用说明。
- `docs/api/`: 对外 API 契约。
- `docs/architecture/`: 架构说明与集成规范。

## 当前入口

启动 LLM Wiki 本地服务：

```bash
cd "/Users/Min369/Documents/同步空间/Manju/AIProjects/ResearchManjushri/LLM Wiki"
python3 scripts/wiki_web.py --host 127.0.0.1 --port 8765
```

打开：

```bash
open http://127.0.0.1:8765/
```

## 集成原则

1. 核心数据由 `LLM Wiki/` 管理。
2. 新应用通过 HTTP API 或明确 adapter 访问核心能力。
3. 不同前端、管理后台、阅读器、自动化任务不得绕过 API 直接改写知识层。
4. 新模块先写清楚输入、输出、状态和错误码，再接 UI。
5. 可复用能力优先放到 `services/` 或 `shared/`，不要写死在单一前端页面里。
