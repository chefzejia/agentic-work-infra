# 通用工作标准

本仓库是标准的真源仓库，执行标准来自 [templates/standards.md](governance/templates/standards.md)。标准正文只在该文件维护，本文件保持路由职责。

本仓的项目约束：

- `AGENTS.md` 只记录本仓边界和路由，不复制通用标准正文。
- `docs/LESSONS.md` 保存失败证据和候选规则；经人审议后，通用规则更新标准真源，本仓特有约束更新其所属文档。
- 目标项目采用固定版本的标准副本，规则反馈和升级方式见 [文档工程指南](governance/agent-governance.md#标准真源与项目承接)。

文档级验证：

```bash
git status --short --branch -uall
git diff --check
```

同时检查 Markdown 链接、规则引用、文档职责与模板实例化路径。模板填空示例与实际失效链接分别报告，不将历史研究稿当作当前执行规则。
