# Agentic Work Infra

> **Agent 时代，人和 Agent 协同的核心是：双方面对同一个工作状态，共同观测、操作、修正和演化，而不是各自维护一套。**

## 这个项目做什么

本项目研究人和 Agent 如何协同完成真实工作——怎样分工、怎样保持工作状态可观测、怎样避免协同结构在实践中跑偏。

本仓遵循 **“公理（Core） + 调研实验室（Research） + 自解释技能包（Skills）”** 的三层架构，所有交付的 Skill 均保持工具无关与自解释。

## 目录与入口

1. **[项目入口](AGENTS.md)** — 仓库架构、路由与维护约束
2. **底层公理（`docs/core/`）**
   - [人机协同模型](docs/core/agentic-work-model.md) — 第一性原理与三层工作状态
   - [AI-Native 第一性原理](docs/core/ai-native-first-principles.md) — 消除“人类带宽妥协层”，始终回归物理、数学与原生最优解
   - [Skill 设计规范](docs/core/skill-design.md) — Skill 即代码的设计准则
3. **可执行技能包（`skills/`）**
   - [project-governance](skills/project-governance/SKILL.md) — 极简项目治理与按需文档模板
   - [engineering-discipline](skills/engineering-discipline/SKILL.md) — 工程变更、分层验证与调试纪律
   - [multi-agent-collab](skills/multi-agent-collab/SKILL.md) — 工具无关的 Brain / Worker / Tester 三角色协作协议
   - [knowledge-base](skills/knowledge-base/SKILL.md) — 人机共同知识对象的构建与维护
   - [web-research-with-assets](skills/web-research-with-assets/SKILL.md) — 网页/推文离线剪藏与关键配图本地化研究包
4. **调研与实验室（`docs/research/`）**
   - [研究索引](docs/research/README.md) — 多 Agent 工具实测（Orca、Herdr）与协同模式调研（Magpie）

[Apache License 2.0](LICENSE)
