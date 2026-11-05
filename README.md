# Agentic Work Infra

当 AI 写单点代码的速度和质量已经超过大多数程序员时，一线研发真正撞上的墙不再是“怎么写出代码”，而是**当代码由 Agent 主力编写时，如何同时拿到「效率、质量、稳定」的可能三角**。

围绕这个终极命题，本仓库持续探索并沉淀三件事：

1. **多 Agent 如何做出不腐败的工程**：为什么有的项目在 Agent 高频迭代下长成难以维护的胶水巨石，有的却能保持高内聚与低认知负担？如何用垂直小包、可离线仿真的纯逻辑内核与反假阳性测试门禁守住工程质量？
2. **人与 Agent 的白盒/黑盒边界在哪里**：既然现在出了 Bug 也是让 Agent 去改，而且真实系统离不开数据库、编译器和游戏引擎等黑盒，什么才是必须共同看懂的？我们的答案是**「控制面与裁判面（意图、契约、任务状态栈、守卫断言、Commit 验证账本）必须 100% 对人透明，计算存储与局部代码实现放心交给底层引擎与多 Agent 闭环」**——确保人永远保有对系统的**可诊断性与可重导向性（Steerability）**。
3. **从立项 0 到 1，人的位置退到了哪里**：当编码与回归交由硅基算力闭环，人类工程师的核心价值收敛为四个支点：**定界（Boundary）、造台（Harness）、证伪（Falsification）、审美（Taste）**。

删掉所有派生索引、缓存和外挂编排框架，系统的方向盘（Markdown 契约）和仪表盘（Git 状态与门禁）依然完整，人随时能看清跑偏在哪一层，随时换一批干净的 Agent 接手重导方向。

## 目录与入口

1. **[项目入口](AGENTS.md)** — 仓库架构、路由与维护约束
2. **底层公理（`docs/core/`）**
   - [人机协同模型](docs/core/agentic-work-model.md) — 控制面白盒 vs 执行面黑盒、三层工作状态与人的四个支点（定界·造台·证伪·审美）
   - [AI-Native 第一性原理](docs/core/ai-native-first-principles.md) — 从代码抽象走向规则抽象、审视旧时代妥协层与跨领域反证门禁
   - [Skill 设计规范](docs/core/skill-design.md) — Skill 即代码的设计准则与演化漏斗
3. **可执行技能包（`skills/`，`v1.0.0`）**
   - [project-governance](skills/project-governance/SKILL.md) — 极简项目治理、核心与易腐边缘隔离及按需文档模板
   - [engineering-discipline](skills/engineering-discipline/SKILL.md) — 实验台先行（Harness-First）、防御式编码、反 Slop 单测与架构加减法
   - [multi-agent-collab](skills/multi-agent-collab/SKILL.md) — 宿主无关的双环四重身份（Brain · Router · Worker · Tester）协作协议
   - [knowledge-base](skills/knowledge-base/SKILL.md) — 人机共同知识对象的构建与维护
   - [web-research-with-assets](skills/web-research-with-assets/SKILL.md) — 网页/推文离线剪藏与关键配图本地化研究包
4. **调研与实验室（`docs/research/`）**
   - [研究索引](docs/research/README.md) — 多 Agent 工具实测（Orca、Herdr）与协同模式调研（Magpie）

[Apache License 2.0](LICENSE)
