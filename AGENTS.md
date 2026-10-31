# Agentic Work Infra

本项目研究 Agent 时代人和 Agent 如何协同完成真实工作，并将经过验证的方法沉淀为**工具无关、自解释的 Skills**。

## 架构与路由

- **底层公理（Why）**：
  - [人机协同模型](docs/core/agentic-work-model.md) — 共同工作状态、三层分离与人机边界
  - [AI-Native 第一性原理](docs/core/ai-native-first-principles.md) — 消除“人类带宽妥协层”，回归物理、数学与系统原生最优解
  - [Skill 设计规范](docs/core/skill-design.md) — Skill 即代码、自解释与迭代漏斗
- **核心交付（Skills，How）**：
  - [项目治理](skills/project-governance/SKILL.md) — 极简起步、按痛点裂变的仓库治理与文档模板
  - [工程与验证纪律](skills/engineering-discipline/SKILL.md) — 工具选择梯度、变更 7 铁律、三面调试与验证分层
  - [多 Agent 三角色协作](skills/multi-agent-collab/SKILL.md) — 基于信息差异隔离的 Brain / Worker / Tester 协作协议
  - [知识库协同](skills/knowledge-base/SKILL.md) — 共同知识对象的构建、核对与维护
  - [网页图文研究包](skills/web-research-with-assets/SKILL.md) — 网页/推文离线剪藏、关键配图本地化与证据包构建
- **调研归档（Lab）**：
  - [研究文档](docs/research/README.md) — 特定工具（Orca、Herdr、Magpie 等）的实测与过程推演记录

## 核心约束

1. **工具与协议解耦**：`docs/core/` 与 `skills/` 保持宿主与工具无关；特定软件的 CLI、模型型号与环境配置归入 `docs/research/` 或宿主本地配置。
2. **Skill 即代码**：每个 Skill 通过 `SKILL.md` 定义可执行步骤与红线，通过 `references/` 自解释设计原理，通过 `assets/` 提供纯净版 `.template.md` 模板（避免使用 `AGENTS.md` 文件名以防被宿主误加载）。
3. **单一事实来源**：修改任何结构或路径时，同步检查全仓 Markdown 链接可解析性。外部参考源码放在 `thirdparty/`（已 Git 忽略）。
