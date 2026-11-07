# 多 Agent 协同工作流设计：基于 `TASKS.md + Git Hook + 多 Worktree 流水线` 的双环四重身份闭环

> **事实核查时间**：2026-11-06（基于本地常驻会话 JSONL 运行日志、SQLite 账单审计，以及 DeepSeek `dsh-superagent-prototype`、yetone `magpie`、Orca、Herdr 横向对比）

---

## 一、 核心命题：当算力无限而人的注意力锁死在 3~5 个会话，普通开发者如何破局？

在 Agent 时代，模型的编码与工具执行算力几乎可以无限横向扩展，但**人类的注意力带宽存在硬物理上限（同时跟进超过 3~5 个活跃 Session 即迅速衰减）**。当前社区出现了三种典型解法：

| 模式 | 代表项目 | 核心机制 | 适用场景与普通开发者的边界 |
| :--- | :--- | :--- | :--- |
| **1. 专用运行时路由派** | DeepSeek `dsh-superagent-prototype` | 独立 Runtime + SQLite 事件流 + 常驻 Router 与隔离 Worker（消融实验证明单 Session + Subagent 在中性提示下 5 次均退化为不调子代理硬干，p95 达 29.5m；双层拆分后降至 15.7m） | 偏理论原型与 IM 群聊/GitHub 多事件并发入口；个人开发本地项目时无需维护重型运行时。 |
| **2. 社区维护三 Loop 派** | yetone `magpie`（[推文实证](https://x.com/yetone/status/2109855710444237018)） | 3 个常驻 `claude --dangerously-skip-permissions` 循环（`dev-app-loop` / `release-magpie` / `agents-status`）+ 严苛 CI + `LESSONS.md`（每晚人工复盘提取规则） | 适合**架构已定型、每日有大量社区 Issue/PR 涌入的成熟开源项目（维护态）**；个人从 0 到 1 做新产品时若无高密度 Issue 喂入，死循环易空转或过度设计。 |
| **3. 双环四重身份 + Git Hook 事件派（本仓方案 ⭐）** | `aperture` | **思考环（人 $\leftrightarrow$ 宏观 Brain）** + **`.git/hooks/post-commit` 监听 `TASKS.md (Status: pending)` 秒级事件唤醒** + **执行环（无人值守 Router 管理 `.tmp/worktrees/` 调度常驻 Worker 与独立 Tester，收口改回 `Status: verified`）** | 专为**独立开发者/小团队从 0 到 1 推进项目及多任务并发演进**设计：零外部编排器依赖、平时 0 Token 空转、需要时秒级多轨闭环。 |

---

## 二、 核心机制与底层原理解析

1. **为什么不用 15 分钟定时轮询（Heartbeat），而用 Git `post-commit` 事件驱动？**
   - 定时轮询存在三大固有缺陷：
     - **触发延迟与早退空等**：提交任务后需等待下一个轮询周期；若总控调 `wait_agent` 超时设置过短（如 10 秒）提前退出回合，即使 Worker 2 分钟后已完成，也会白白干等下一个 15 分钟周期；
     - **夜间空转缓存税**：无新任务时，定时轮询仍会每 15 分钟唤醒会话重发十余万 Token 上下文检查 `git log`；
     - **动态改写定时任务 Prompt 易腐败**：将已处理 Commit SHA 写进宿主私有的定时任务配置里，既脆弱又强绑定特定客户端。
   - **Git Hook 事件驱动原语**：利用 Git 原生 `.git/hooks/post-commit`，仅在检测到 `docs/TASKS.md` 包含 `Status: pending` 提交时，通过本地队列与静默唤醒深链（如 `codex queue` + `open -g "codex://threads/wake/<UUID>"` 或对应 CLI 命令）在 **2 秒内**直接拍醒后台常驻会话；平时无提交则 **0 唤醒、0 Token 消耗**。

2. **为什么必须从“三角色”升级为“双环四重身份（Brain · Router · Worker · Tester）”？**
   - 如果只定义 `Brain / Worker / Tester` 三角色，后台常驻总控会话在收到队列塞入的自然语言唤醒消息且遇到任务包白名单漏列同切面支撑文件时，会误以为对面坐着人类用户，直接在后台聊天框里停下来提问等待授权，导致无人值守闭环中断。
   - **四重身份职责边界**：
     - **Brain（思考环）**：唯一面对人类的沟通桥梁，负责定义契约并提交 `docs/TASKS.md (Status: pending)`；
     - **Router（执行环战术总控与现场法官）**：由 Git Hook 发送 `[AUTO-WAKEUP]` 机器指令唤醒，明确宣告其无人值守身份（**严禁在后台会话向人类提问等待回复**）。显性缺陷与同切面支撑文件漏列由 Router 亲自记入 `docs/LESSONS.md` 并直接授权 Worker 补齐自愈；核心契约冲突则写入 `Status: blocked` 并 `git commit` 退回给 Brain；
     - **Worker（隔离实现与秒级工程内环）**：同一工作树严格串行（`Write = 1`），多任务正交或流水线重叠时在 `.tmp/worktrees/task-<ID>` 隔离开发，负责在交卷前跑通秒级无头单测与构建门禁；
     - **Tester（独立模拟真实用户终验外环）**：消除作者“自我确认”偏见，不替 Worker 写单测或拿脚本 `ok: true` 充数，而是**根据产品形态完全模拟真实人类用户操作产品**（如点按界面并截屏肉眼审视排版、位置与文案体验）。

3. **状态去 Session 化 + 单文件滑动调度板（`TASKS.md` & Drain-Loop）+ 算力热驻留（实测 97.75% ~ 98.62% 缓存命中）**
   - **单文件滑动调度板与睡前排空（防并发覆盖与运行中漏触发）**：`docs/TASKS.md` 采用独立编号区块 `## [Task #N]` 维护各自的 `- **Status**: pending | in_progress | verified | blocked | superseded` 与 `Scope`（仅保留未结案区块 + 最近 1~2 个已结案锚点）。当 Router 正在后台执行 `#N` 期间，Brain 可随时追加 `## [Task #N+1] (pending)`（或将 `#N` 标为 `superseded`）并通过 `git commit --only docs/TASKS.md` 隔离提交；Router 结案 `#N` 时仅精确修改 `#N` 的状态行，并在结束回合前强制重读 `docs/TASKS.md` 排空所有新增 `pending` 区块（Drain-Loop），彻底根除单槽位覆盖与运行期漏触发；
   - **常驻热节点复用**：下游 Router、Worker 与 Tester 作为常驻热会话（Warm Sessions）跨波次持续复用上下文前缀（实测常驻 Router 缓存命中率达 `98.62%`，常驻 Worker 缓存命中率达 `97.75%`）。
