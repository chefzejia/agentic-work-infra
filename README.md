# Aperture

> **Focus infinite intelligence into finite purpose.**
> **以有限之孔径，聚无限之智能。**

在光学里，没有光圈（Aperture）约束的漫射光哪怕再强，落在底片上也只是一片白茫茫的过曝噪点；唯有穿过一个精确收缩的孔径，漫天散乱的光子才能在底片上凝结成景深极深、纤毫毕现的清晰图像。

AI 时代的工程与知识工作也是如此。当硅基算力与编码智能趋于无限，真正稀缺且“有限”的只有人的注意力与现实世界的确定性边界。**没有边界约束的无限智能只会加速制造熵增与代码屎山；而 Aperture 研究的终极命题，正是如何用有限的规则、边界与审美孔径，去驾驭无限的智能，在 Agent 主力开发的时代同时拿到「效率、质量、稳定」的可能三角。**

围绕这个命题，本仓库持续探索并沉淀三件事：

1. **多 Agent 如何做出不腐败的工程**：为什么有的项目在 Agent 高频迭代下长成难以维护的胶水巨石，有的却能保持高内聚与低认知负担？如何用垂直小包、可离线仿真的纯逻辑内核、反假阳性破壁门禁与周期性逆熵审计（`Auditor`）守住工程质量？
2. **人与 Agent 的白盒/黑盒边界在哪里**：既然现在出了 Bug 也是让 Agent 去改，而且真实系统离不开数据库、编译器和游戏引擎等黑盒，什么才是必须共同看懂的？我们的答案是**「控制面与裁判面（意图、契约、任务调度板 `TASKS.md`、守卫断言、Commit 验证账本）必须 100% 对人透明，计算存储与局部代码实现放心交给底层引擎与多 Agent 闭环」**——确保人永远保有对系统的**可诊断性与可重导向性（Steerability）**。
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
   - [engineering-discipline](skills/engineering-discipline/SKILL.md) — 双速调试与实验台先行（Harness-First）、UI 自拍自检、反 Slop 单测与架构加减法
   - [multi-agent-collab](skills/multi-agent-collab/SKILL.md) — 宿主无关的五重身份（Brain · Router · Worker · Tester + 周期性冷会话 Auditor）与多 Worktree 协作协议
   - [knowledge-base](skills/knowledge-base/SKILL.md) — 人机共同知识对象的构建与维护
   - [web-research-with-assets](skills/web-research-with-assets/SKILL.md) — 网页/推文离线剪藏与关键配图本地化研究包
4. **调研与实验室（`docs/research/`）**
   - [研究索引](docs/research/README.md) — 多 Agent 工具实测（Orca、Herdr）与协同模式调研（Magpie）

[Apache License 2.0](LICENSE)
