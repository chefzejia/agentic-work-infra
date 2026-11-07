# Aperture

> **Focus infinite intelligence into finite purpose.**
> **以有限之孔径，聚无限之智能。**

本项目研究 Agent 时代如何用有限的规则、边界与审美孔径（Aperture）驾驭近乎无限的硅基算力，并将经过验证的方法沉淀为**工具无关、自解释的 Skills**。

## 架构与路由

- **底层公理（Why）**：
  - [人机协同模型](docs/core/agentic-work-model.md) — 控制面透明 vs 执行面黑盒、三层工作状态与人的四个支点（定界·造台·证伪·审美）
  - [AI-Native 第一性原理](docs/core/ai-native-first-principles.md) — 从代码抽象走向规则抽象、审视旧时代妥协层与跨领域反证门禁
  - [Skill 设计规范](docs/core/skill-design.md) — Skill 即代码、独立自封闭与迭代漏斗
- **核心交付（Skills，How）**：
  - [项目治理](skills/project-governance/SKILL.md) — 极简起步、核心与易腐边缘隔离及按需文档模板
  - [工程与验证纪律](skills/engineering-discipline/SKILL.md) — 双速调试与实验台先行（Harness-First）、防御式编码、反 Slop 单测与垂直单向 DAG
  - [多 Agent 四角色协作](skills/multi-agent-collab/SKILL.md) — 基于信息差异与交互对象隔离的 Brain / Router / Worker / Tester 双环协作与多 Worktree 并行协议
  - [知识库协同](skills/knowledge-base/SKILL.md) — 共同知识对象的构建、核对与维护
  - [网页图文研究包](skills/web-research-with-assets/SKILL.md) — 网页/推文离线剪藏、关键配图本地化与证据包构建
- **调研归档（Lab）**：
  - [研究文档](docs/research/README.md) — 特定工具（Orca、Herdr、Magpie 等）的实测与过程推演记录

## 核心约束

1. **工具与协议解耦**：`docs/core/` 与 `skills/` 保持宿主与工具无关；特定软件的 CLI、模型型号与环境配置归入 `docs/research/` 或宿主本地配置。
2. **Skill 即代码（独立自封闭与统一版本）**：每个 Skill 通过 `SKILL.md` 定义可执行步骤与红线（YAML Frontmatter 中的 `version` 必须与根目录 [`VERSION`](VERSION) 严格同步），通过 `references/` 自解释设计原理，通过 `assets/` 提供纯净版 `.template.md` 模板（避免使用 `AGENTS.md` 文件名以防被宿主误加载）；单个 `skills/<name>/` 目录内的相对链接必须 100% 自封闭，不向外逃逸。
3. **单一事实来源**：修改任何结构或路径时，同步运行下方守卫检查验证全仓 Markdown 链接可解析性与 Frontmatter 契约。外部参考源码放在 `thirdparty/`（已 Git 忽略）。

## 修改与验证

```bash
python3 scripts/verify.py
```
