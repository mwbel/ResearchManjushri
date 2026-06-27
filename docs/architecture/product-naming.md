# 产品命名

## 当前约定

- 仓库名：`ResearchManjushri`
- 主产品名：`LLM Wiki`
- 核心模块目录：`app/llm-wiki/`
- 统一模块边界：`services/`、`domains/`、`shared/`（保持代码可复用与可并行扩展）

## 命名原则

`ResearchManjushri` 作为仓库和长期研究工程容器保留。

`LLM Wiki` 作为当前产品、入口、文档和应用名称使用。

后续新增模块不应以仓库名命名，而应按业务能力命名，例如：

- `source-ingest-service`
- `concept-service`
- `graph-service`
- `reader-workbench`
- `model-gateway-service`

## 路径规则

文档和命令中的根路径统一使用：

```text
/Users/Min369/Documents/同步空间/Manju/AIProjects/ResearchManjushri
```

旧路径 `ResearchManjusi` 只作为历史迁移备注出现，不应出现在新命令里。

## 仓库名与主名重命名治理规则

- 一旦 `ResearchManjushri` 迁移为新仓库名，必须同步：
  - `git remote` 与分支默认名
  - CI/CD 配置中的仓库地址
  - 部署脚本中的拉取地址与路径
  - `docs/api` 与 `README` 中的仓库入口链接
- 数据目录与内容目录路径不变原则优先，避免对外链中断。
