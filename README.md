# Agentic Work Infra

接下来我将用最直接、最硬核、最扎心、最不绕弯子、最不墨迹的方式来为你介绍我们的项目：

不管是连了上百个节点的画布工作流、把资料切碎塞进向量库与图数据库的 RAG / 记忆框架，还是让一群 Agent 扮演公司职位互相开会的编排系统——社区里大多数流行方案的共性，都是在人和 AI 之间加一层厚重的“黑盒中间态”：Agent 在向量、图节点和私有状态库里维护一套世界，人在外面看另一套界面。一旦跑偏，人既看不清它脑子里记了什么，也没法直接插手修改。

我们代表另一种思路：**所有真正重要的东西，都必须是碳基生物（人）和硅基生物（Agent）共同可观测、可理解、可直接动手的。**

不靠黑盒数据库托管记忆，不靠繁琐的编排框架托管流程。知识就是本地可读的 Markdown，契约就是源码与测试门禁，协作就是 Git 上的状态流转——删掉所有索引、缓存和外挂框架，工作现场依然完整，人随时能推门进来直接接管。

## 目录与入口

1. **[项目入口](AGENTS.md)** — 仓库架构、路由与维护约束
2. **底层公理（`docs/core/`）**
   - [人机协同模型](docs/core/agentic-work-model.md) — 第一性原理与三层工作状态
   - [AI-Native 第一性原理](docs/core/ai-native-first-principles.md) — 消除“人类带宽妥协层”，始终回归物理、数学与原生最优解
   - [Skill 设计规范](docs/core/skill-design.md) — Skill 即代码的设计准则
3. **可执行技能包（`skills/`）**
   - [project-governance](skills/project-governance/SKILL.md) — 极简项目治理与按需文档模板
   - [engineering-discipline](skills/engineering-discipline/SKILL.md) — 工程变更、分层验证与调试纪律
   - [multi-agent-collab](skills/multi-agent-collab/SKILL.md) — 工具无关的双环四重身份（Brain · Router · Worker · Tester）协作协议
   - [knowledge-base](skills/knowledge-base/SKILL.md) — 人机共同知识对象的构建与维护
   - [web-research-with-assets](skills/web-research-with-assets/SKILL.md) — 网页/推文离线剪藏与关键配图本地化研究包
4. **调研与实验室（`docs/research/`）**
   - [研究索引](docs/research/README.md) — 多 Agent 工具实测（Orca、Herdr）与协同模式调研（Magpie）

[Apache License 2.0](LICENSE)
