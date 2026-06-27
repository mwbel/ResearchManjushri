# 推送边界与内容清单（ResearchManjushri / LLM Wiki）

本仓库的远程推送边界目标：

- 允许：软件、服务、架构、API、模块化、部署、脚本、技术决策文档
- 禁止：书籍、论文、资料目录、原始数据、会话沉淀内容

## 禁止推送的路径与文件类型（默认）

- `inputs/`
- `outputs/`
- `AI/`
- `本质之探索/`
- `需读论文/`
- `app/llm-wiki/raw/`
- `app/llm-wiki/wiki/`
- `*.pdf`, `*.caj`, `*.docx`, `*.pptx`, `*.xlsx`, `*.zip`, `*.tar`, `*.gz`, `*.mp4`, `*.mov`, `*.m4a`, `*.mp3`, `*.wav`
- `docs/sessions/第*次-*.md`
- `docs/PRD_*.md`
- `docs/任务执行清单_*.md`
- `docs/提示词历史.md`

## 执行规范

1. 推送前只提交本次实现与技术决策相关变更。
2. 任何资料型文件即使当前本地有，也不得进入本次要推送的 commit。
3. 若误入 commit，需先 `git reset --mixed` 回退到待分离区，剔除不应推送文件后再重新提交。

## 强制检查（建议）

本仓库提供 pre-push 钩子（`.githooks/pre-push`），可先启用：

```bash
mkdir -p .githooks
chmod +x .githooks/pre-push
git config core.hooksPath .githooks
```

如果不启用，推送前请手工执行：

```bash
git diff --name-only HEAD~1
# 或

git status --short
```

确保输出中不出现“禁止推送”清单里的路径与文件类型。
