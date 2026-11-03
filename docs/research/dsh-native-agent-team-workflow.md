# 多 Agent 协同工作流演进实录：从定时轮询到基于 `HANDOFF.md + Git Hook` 的秒级事件闭环

> **事实核查时间**：2026-11-03（基于 `Pith` 与 `AGU` 真实运行日志 `~/.codex/sessions/2026/11/02~03/rollout-*.jsonl`、`state_5.sqlite`、`queue_1.sqlite`、`logs_2.sqlite` 源码级审计，以及 DeepSeek `dsh-superagent-prototype`、yetone `magpie`、Orca、Herdr 横向对比）

---

## 一、 核心命题：当算力无限而人的注意力锁死在 3~5 个会话，普通开发者如何破局？

在 Agent 时代，模型的编码与工具执行算力几乎可以无限横向扩展，但**人类的注意力带宽存在硬物理上限（同时跟进超过 3~5 个活跃 Session 即迅速衰减）**。当前社区出现了三种典型解法：

| 模式 | 代表项目 | 核心机制 | 适用场景与普通开发者的边界 |
| :--- | :--- | :--- | :--- |
| **1. 专用运行时路由派** | DeepSeek `dsh-superagent-prototype` | 独立 Runtime + SQLite 事件流 + 常驻 Router 与隔离 Worker（消融实验证明单 Session + Subagent 在中性提示下 5 次均退化为不调子代理硬干，p95 达 29.5m；双层拆分后降至 15.7m） | 偏理论原型与 IM 群聊/GitHub 多事件并发入口；个人开发 1~2 个本地项目时无需维护重型运行时。 |
| **2. 社区维护三 Loop 派** | yetone `magpie`（[推文实证](https://x.com/yetone/status/2109855710444237018)） | 3 个常驻 `claude --dangerously-skip-permissions` 循环（`dev-app-loop` / `release-magpie` / `agents-status`）+ 严苛 CI + `LESSONS.md`（每晚人工“铲屎”提取规则） | 适合**架构已定型、每日有大量社区 Issue/PR 涌入的成熟开源项目（维护态）**；个人从 0 到 1 做新产品时若无高密度 Issue 喂入，死循环易空转或乱改。 |
| **3. 双环解耦 + Git Hook 事件派（本仓方案 ⭐）** | `agentic-work-infra`（落地于 `Pith` / `AGU`） | **思考环（人 $\leftrightarrow$ 宏观 Brain）** + **`.git/hooks/post-commit` 监听 `HANDOFF.md (Status: pending)` 秒级事件唤醒** + **执行环（常驻总控调度热 Worker 与独立 Tester）** | 专为**独立开发者/小团队从 0 到 1 推进 1~2 个核心产品（创作与演进态）**设计：零外部编排器依赖、平时 0 Token 空转、需要时秒级闭环。 |

---

## 二、 演进脉络：我们走过的四步实测与证伪

1. **阶段一：多窗口人肉剪贴板（`AGU` 早期）**
   - 确立了基于“信息差异”的 **Brain / Worker / Tester** 三角色隔离，但靠人在不同窗口间手动复制粘贴 Prompt 和报错截图，且每次点 `New chat` 导致 KV Prompt Cache 清零（白交 20~40 秒冷启动重读税）。
2. **阶段二：外部重型编排壳实测（Orca 与 Herdr）**
   - **Orca**：桌面 ADE + `orchestration.db` 状态机过重，把自然对话变成了填表。
   - **Herdr（Herdr App + `herdr-core`）**：通过 `hc send` 解决了 CLI 终端间的免粘贴通信，但本质仍是 PTY 终端容器，无法直接调用 GUI 宿主（如 ChatGPT App 或 DSH）独有的原生桌面 CUA 能力。
3. **阶段三：15 分钟 Heartbeat 定时轮询的试水与暴露的三大缺陷（`Pith` Wave 6~7 日志审计）**
   - 起初误以为外部 CLI 无法唤醒 ChatGPT App 已打开的 GUI 会话（因直接跑 `codex exec resume` 会报 `already has an active writer` 排他锁冲突），于是改用 ChatGPT App 内置的 15 分钟 Heartbeat（`automation.toml`）轮询 `docs/HANDOFF.md`。
   - 审计 `~/.codex/sessions/2026/11/02/rollout-2026-11-02T20-04-53-01a19c25-ec2b-78b3-8cae-314ac4432690.jsonl` 发现了三个不查底层日志根本看不见的坑：
     - **缺陷 A（`wait_agent` 10 秒早退导致跨周期空等）**：`21:50:59` 总控在 Heartbeat 轮询中调 `wait_agent(timeout_ms: 10000)` 仅等 10 秒即超时退出（`DONT_NOTIFY`），而 Worker 在 2 分钟后的 `21:53:33` 就跑完了全部 112 项单测，结果白白干等了下一个 15 分钟周期才唤醒 Tester。
     - **缺陷 B（动态改写 `automation.toml` Prompt + 长寿会话规则滞后）**：总控通过 `automation_update` 把已处理 SHA 写进自己的定时任务 Prompt 里，既脆弱又强绑定宿主；且长寿常驻会话一旦启动，外部修改全局 Skill 不会自动热更新它脑子里的旧习惯（直至次日早上 `09:36` Wave 7 触发时，旧总控线程仍在调 `automation_update` 和 10s `wait_agent`）。
     - **缺陷 C（夜间轮询空转缓存税）**：虽然常驻总控线程拿到了 `98.62%`（`8,109,952 / 8,223,082`）的极高缓存命中率（常驻 Worker `01a19c2a` 在 5,984 万总输入中也达到了 `97.75%` 缓存命中率），但总控线程整夜每 15 分钟醒来跑一次 `git log`，从晚间 822 万 Token 空转累积到了次日早上的 2,396 万 Token。
4. **阶段四：拆解源码跑通「Git `post-commit` Hook 秒级事件驱动」（终极形态）**
   - 逆向核查 `/Applications/ChatGPT.app/Contents/Resources/app.asar` 主进程源码（`early-bootstrap-339.js` 与 `early-bootstrap-916.js`）及 `queue_1.sqlite` 发现：
     - 外部虽然不能直接抢 `resume` 写锁，但可以通过 `codex queue --thread <UUID> --message "..."` 将指令无锁写入共享的 `~/.codex/queue_1.sqlite`；
     - 紧接着调用 macOS 原生深链 `open -g "codex://threads/wake/<UUID>"`（对应内部路由 `wakeQueuedThread`，`-g` 保持后台静默不弹窗不抢焦点），ChatGPT App 主进程会立即调用 `thread/queue/list` 并在當前打开的 GUI 会话中启动新 Turn（`turn_trigger: "queue"`）！
   - **真机实测证据（2026-11-03 10:40:04 / UTC `02:40:04`）**：
     - 在隔离仓库配置 `.git/hooks/post-commit`，当提交 `5f1251e` 将 `docs/HANDOFF.md` 设为 `Status: pending` 时，Git Hook 自动执行 `codex queue` + `open -g "codex://threads/wake/01a19c0f-c8e2-7ac3-9212-075f4aec1162"`；
     - 仅隔 **2.1 秒**（UTC `02:40:06.676Z`），常驻线程 `01a19c0f` 即以 `"turn_trigger": "queue"` 自动唤醒，并在 **4.19 秒**内完成响应（`GIT_POST_COMMIT_TRIGGERED_5f1251e`），全程 **0 人工粘贴、0 窗口弹出、平时 0 轮询空转**！

---

## 三、 极简实操规范总结

1. **状态去 Session 化 + 算力热驻留**：
   - 项目契约与交接状态 100% 落盘于 `docs/HANDOFF.md`（顶部维护 `Status: pending | verified | blocked` 与 `Verified-Commit: <sha>`）；
   - 下游执行总控、Worker 与 Tester 作为常驻热会话（Warm Sessions）跨波次复用上下文前缀（实测命中率 `97.7% ~ 98.6%`），但当全局协作协议升级时，必须显式向常驻会话发送一条协议刷新指令。
2. **Git Hook 秒级触发代替定时空转**：
   - 用 `.git/hooks/post-commit` 拦截 `docs/HANDOFF.md` 的 `Status: pending` 提交，秒级唤醒下游执行总控；下游验收通过后提交 `Status: verified` 自动静默收口，不触发死循环。
3. **单轮闭环不早退 + 共享工作区 `Write = 1` + 固定真机沙盒 + `LESSONS.md` 错误复利**：
   - 执行总控被唤醒后必须在同一轮次内循环 `wait_agent` 跑完 `Worker -> Tester -> verified commit`；
   - 同一工作树严格串行写（`Write = 1`），拒绝表演式并发；
   - 真机/CUA 验收固定复用唯一 `.gitignore` 沙盒（如 `.dev-vault/`）；
   - 人类只做事前契约审美与事后模式提取（重复 3 次的错误晋升为 `tests/` 守卫单测）。
