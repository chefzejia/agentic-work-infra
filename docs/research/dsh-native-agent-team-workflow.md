# 多 Agent 协同工作流演进总结：告别「双 GUI 人肉剪贴板」与「高频新建 Session 缓存失效」

> **生成时间**：2026-11-02
> **核心场景**：在 `Pith`（`/Users/zejiawu/Projects/Project-Atlas/labs/pith`）从零到一的四波高速迭代与动态真机验收中，针对多 Agent 协同研发流（Brain / Worker / Tester）的第一性原理复盘与全局推广方案。

---

## 一、 过去工作流的三大结构性痛点（反模式诊断）

在之前的开发模式中（DSH 负责 Brain 架构规划 $\leftrightarrow$ 人类手动复制粘贴 Prompt 到 ChatGPT/Codex App 点 `New chat` 跑 Worker/CUA $\leftrightarrow$ 截图贴回 DSH），存在三个严重的效率与体验损耗：

1. **人类退化为两个 GUI 之间的「人肉 IPC 剪贴板路由器」**：
   - 人类原本只需做高层产品判断与方向把关，却被迫承担最枯燥的“复制交接单 $\rightarrow$ 切窗口 $\rightarrow$ 新建会话 $\rightarrow$ 粘贴等待 $\rightarrow$ 截图回传”的体力活，心流被频繁打断。
2. **每次任务点 `New chat`，导致 Prompt Cache（前缀缓存）彻底清零**：
   - 每开一个新 Session，Worker 都要从头执行 `ls`、读取 `AGENTS.md`、`docs/002-architecture.md`、`src/core/seams.ts`。
   - 不仅每次白白浪费 20~40 秒冷启动预热时间，更无法复用同一项目上下文的 KV Cache（原本常驻会话可达 90%+ 缓存命中率）。
3. **「去 Session 化」被误解为「频繁销毁重建聊天窗口」**：
   - 真正的**去 Session 化（Sessionless Architecture，源自 `dsh-superagent-prototype`）**，指的是**「项目的长期状态、契约与进度不锁死在某段聊天记录里，而是 100% 落盘在工作区文件（`HANDOFF.md` / Git Commit / Markdown 账本）中」**；
   - 而执行任务的 Agent 进程本身，完全应该作为**常驻热节点（Warm Teammates）**持续复用，直到上下文触及阈值自动 Compaction。

---

## 二、 现有工具链事实核查（Orca vs Herdr vs Codex Daemon vs DSH 原生）

基于 2026-11-02 最新事实核查，对四条技术路线做客观对比：

| 方案 | 2026-11 最新现状与核心机制 | 优势 | 为什么不是当前最优解 / 适用边界 |
| :--- | :--- | :--- | :--- |
| **1. Orca** | 桌面 ADE + `orchestration.db` + 多 Worktree 面板 | 提供标准化的 `worker-start` 与监督状态机 | **过重**。把自然的人机协同变成了填表式的任务派发，UI 割裂感强。 |
| **2. Herdr (新版 Herdr App + herdr-core)** | 已从早期纯 TUI 演进为 `herdr-core` 后台驻留服务 + 原生桌面 **Herdr App**（`herdr.dev`）。支持 `hc run --bg codex "..."` 与 `hc send t3 "..."`，子 Agent 完成后通过 `<hc from="t3">` 自动把报告塞回主 Agent 输入框；支持 OSC 7501 状态协议与 `~/.config/herdr-app` 自修改。 | 解决了 CLI Agent 之间的免复制粘贴通信（`hc send`）与关窗口保活 | 定位仍是**终端（PTY）容器管理器**；当你已经在用 DSH GUI 时，再套一层 Herdr App 属于双宿主重叠。 |
| **3. Codex App 本地 Daemon (`codex queue`)** | ChatGPT/Codex Desktop App 底层运行 `codex app-server`，落盘于 `~/.codex/session_index.jsonl` 与 `state_5.sqlite`。支持通过 `codex exec resume <id>` 或 `codex queue --thread <id> --message "..."` 追加消息。 | 可复用已有 Codex Thread | 默认桌面端 `app-server` 走私有 stdio/IPC 通道，未显式开启 `codex app-server daemon enable-remote-control` 时，外部 CLI `queue --resume` 无法直接唤醒 GUI 渲染进程。 |
| **4. DSH 原生全闭环（最优解 ⭐）** | DSH 自身已内置四大原生套件：<br>① **`@deepseek-ai/dsh-experimental-agent-team`**（`spawn_teammate` + `send_message` + `wait_agent` + 共享 Task Board）<br>② **`subagent_codex` / `subagent-oar`**（直接后台并发调度 Codex / Claude Code）<br>③ **`browser-use-playwright-mcp` + Headless Chromium / `read_image`**（内置浏览器动态交互与截图视觉检查）<br>④ **`@deepseek-ai/dsh-cua-bundle` (`cua-macos`)**（Swift 原生 macOS 桌面级 Computer Use） | **100% 单窗口闭环、零人工粘贴、常驻队友命中 Prompt Cache、原生支持截图/CUA 验收** | **直接满足全部诉求，无需引入第三方重型编排壳。** |

---

## 三、 推荐推广的「DSH 原生单窗口 + 常驻热队友」标准工作流

将 `multi-agent-collab`（Brain / Worker / Tester 三角色协议）直接映射到 **DSH 原生 Agent Teams + Subagents** 上，形成以下零摩擦范式：

```text
+-----------------------------------------------------------------------------------+
| 👤 人类（唯一交互入口：只在一个 DSH 窗口里与 Lead/Brain 对话，彻底告别复制粘贴）  |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| 🧠 Lead / Brain（主会话）                                                         |
|   1. 冻结上游契约（如 `src/core/seams.ts`、`docs/HANDOFF.md`）并提交 Git 基线；   |
|   2. 规划物理正交（Write Scope 零交集）的 1~3 个大步任务包；                      |
|   3. 自动调度常驻 Worker / Tester，汇总验收证据并执行最终 `git commit`。          |
+-----------------------------------------------------------------------------------+
             │                                                   │
             ▼ (send_message 复用常驻队友 / subagent_codex)       ▼ (send_message 唤醒常驻 Tester)
+-----------------------------------------+     +-----------------------------------+
| 🔨 常驻 Worker (`<proj>-worker-a/b`)    |     | 🔍 常驻 Tester (`<proj>-tester`)  |
| • 通过 `spawn_teammate` 创建一次后常驻  |     | • 常驻于同一 Team，不销毁不重建   |
| • 后续波次直接 `send_message` 派发增量  |     | • 后台拉起真机服务 + Playwright   |
|   任务，无需重读全仓，极致命中缓存！    |     |   自动点击、截图 `/tmp/*.png`、   |
| • 或对单次独立重活调用 `subagent_codex` |     |   向 Lead 发送结构化挑刺报告！    |
+-----------------------------------------+     +-----------------------------------+
```
