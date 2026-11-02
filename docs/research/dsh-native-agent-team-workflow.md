# 多 Agent 协同工作流演进实录：基于 `HANDOFF.md` 状态钩子的双环解耦实践

> **事实核查时间**：2026-11-02（基于 `Pith` Wave 6 真实运行日志 `~/.codex/sessions/2026/11/02/rollout-*.jsonl`、`state_5.sqlite` 账单审计，以及 DSH / Orca / Herdr 横向对比）

---

## 一、 演进脉络：从早期多窗口手动搬运，到 Agent 无关的 `HANDOFF` 钩子闭环

1. **阶段一（早期多身份多 Session 手动协同，如 `AGU` 早期）**：
   - 为了防止单一会话上下文被污染，采用“项目薄契约文档 + 代码门禁 + 多身份隔离（Brain / Worker / Tester）”。
   - **痛点**：人类退化为多个窗口之间的剪贴板路由器；每次在下游点 `New chat` 导致 KV Prompt Cache 清零，白交 20~40 秒冷启动重读税。
2. **阶段二（调研外部编排壳：Orca 与 Herdr）**：
   - **Orca**：桌面 ADE + `orchestration.db` + 多 Worktree 面板。提供了 `worker-start` 状态机，但形态过重，填表式派发割裂了人与 Brain 的自然对话。
   - **Herdr（新版 Herdr App + `herdr-core`）**：解决了 CLI 终端之间的 `hc send` 免粘贴通信与后台保活，但本质仍是 PTY 终端容器管理器，无法直接替代原生 GUI 宿主的桌面 CUA 能力。
3. **阶段三（受 DeepSeek《Super-agent 设计探索》启发：双环解耦 + `HANDOFF.md` 事件钩子）**：
   - **宏观架构环（人 $\leftrightarrow$ Thinking Brain）**：人只盯唯一一个主对话窗口（选用旗舰模型如 `Gemini 4 Argon` 或 `Claude Opus 5.5`），聊透需求后将契约写入仓库 `docs/HANDOFF.md`（标为 `Status: pending`）并 `git commit`。
   - **自动执行环（Execution Coordinator $\rightarrow$ 常驻 Worker & Tester）**：下游独立常驻一个执行主会话（Agent 无关：需要重度原生桌面 CUA 时用 ChatGPT App，纯 Web/后端项目可用 DSH Agent Team 或任意 CLI Agent），通过 Heartbeat / Watcher 钩住已提交的 `docs/HANDOFF.md` 自动触发实施与真机验收。

---

## 二、 源码与真机边界核查（防止误判的硬事实）

1. **DSH 原生工具边界（经 `deepseek-harness` 源码核实）**：
   - `@deepseek-ai/dsh-experimental-agent-team-profile`（`spawn_teammate` + `send_message`）：`freshProvider: spawn` 运行的是 **DSH 进程内同构模型**，适合同构常驻队友复用缓存，不能直接把队友切换成外部 ChatGPT App 进程。
   - `@deepseek-ai/dsh-subagent-codex`（`subagent_codex`）：每次调用均创建**全新、一次性隔离的 Codex 线程**（不支持二次 `send_message` 续聊，也无法调起 ChatGPT Desktop 独有的原生桌面 CUA），适合单次独立代码审计或一次性重构任务。
2. **ChatGPT App（Codex Desktop）排他锁与 Heartbeat 实测（经 `state_5.sqlite` 与 `rollout-*.jsonl` 核实）**：
   - ChatGPT App 通过私有 `--stdio` 独占持有打开会话的写锁（`~/.codex/thread-writer-locks/`），外部 CLI 无法直接向已打开的 GUI 线程塞消息。
   - **实测跑通机制**：在 ChatGPT App 内保留**唯一一个永不关闭的项目常驻总控线程**，挂载 `automation.toml`（`kind = "heartbeat"`, `INTERVAL=15`）监测 `docs/HANDOFF.md` 的 Git 提交：
     - **真实缓存命中率铁证**：在 `Pith` 总控线程（`01a19c25`）实测账单中，`input_tokens = 8,223,082`，`cached_input_tokens = 8,109,952`，**KV Prompt Cache 命中率高达 `98.62%`**；Worker（`01a19c2a`）与 Tester（`01a19c26`）子线程均成功跨波次复用。

---

## 三、 真机调试抓出的 3 个工程陷阱与修复门禁

在 `Pith` Wave 6（Commit `ac500c1`）的自动触发实测中，通过审计底层 JSONL 日志发现了 3 个必须由工作流协议锁死的细节：

1. **陷阱 1：`wait_agent` 短超时导致跨周期空等**
   - **现象**：`21:50:59` 总控在 Heartbeat 轮询中调用 `wait_agent` 仅等待 10 秒即超时退出（`DONT_NOTIFY`），而 Worker 在 2 分钟后的 `21:53:33` 即完成全部编码与 `112/112` 单测，导致被迫多等下一个 15 分钟周期（`22:35` 才唤醒 Tester）。
   - **修复门禁**：执行总控在派发或检测到活跃子任务时，必须在当前 Turn 内循环 `wait_agent` 直至串联完成 `Worker 实现 → Tester 验收 → git commit`，严禁短超时早退。
2. **陷阱 2：游标状态不应写在宿主私有的 `automation.toml` Prompt 字符串里**
   - **现象**：总控通过 `automation_update` 动态改写自身 Prompt 字符串来记录基线 SHA，既脆弱又绑定特定宿主。
   - **修复门禁**：改为在仓库 `docs/HANDOFF.md` 顶部维护显式状态机（`Status: pending | verified | blocked` + `Verified-Commit: <sha>`），使外部 Heartbeat Prompt 保持 100% 静态、宿主无关。
3. **陷阱 3：Worker 自创根目录临时文件夹污染工作树**
   - **现象**：Worker 在验证期间于仓库根目录创建了未列入 `.gitignore` 的 `.wave6-verification-20261102/`（含浏览器缓存）。
   - **修复门禁**：所有验证临时产物必须写入 `.gitignore` 已覆盖的固定沙盒目录（`.tmp/` 或 `.dev-vault/`），严禁在仓库根目录自创临时目录或污染宿主全局 Vault 列表。
