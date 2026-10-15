# Orca 多 Agent 协作配置指南

本指南基于 Orca v1.4.224 官方文档（skill-guides/orchestration.md 和 orca-cli.md），说明如何使用 Orca 实现 Brain/Worker/Tester 三角色协作（角色定义见 [三角色协作设计.md](三角色协作设计.md)）。

## 目标架构

```
Orca Desktop (可视化管理)
├── Brain (常驻协调者 + 架构师) - Claude Code
│   └── 使用 orchestration 进行任务编排和结果等待
├── Tester (常驻) - Codex
│   └── 接收完成通知并进行审查
└── Workers (临时) - Codex 或 Claude
    └── 在独立 worktree 中执行具体任务
```

## Orca 核心能力

### 1. 两种协作模式

**Full Handoff（完全移交）**：
- 用于 "hand off"、"handover"、"give this to another agent" 等场景
- 原 agent 启动新 agent 后即停止，不监督、不等待
- 使用 `orca worktree create --agent` 或 `orca terminal create --command`
- 命令返回后即视为完成，无需等待接收方完成工作

**Supervised Orchestration（监督式编排）**：
- 用户明确要求 "supervise"、"monitor"、"wait for results"、"coordinate a DAG" 时使用
- Coordinator（协调者）创建 Run、Task、Dispatch，并通过 `orca orchestration check --wait` 等待 `worker_done` 消息
- 支持并行任务、依赖关系、结果验证、失败重试

### 2. Orchestration 消息系统

**核心概念**：
- **Run**：协调者的命名空间和收件箱，记录整体目标
- **Task**：具体工作单元，包含目标、约束、验收标准
- **Dispatch**：一个 Task 的权威执行尝试（可能有重试）
- **Worker**：执行 Dispatch 的 agent，收到注入的 preamble（包含 Task ID、Dispatch ID、heartbeat 间隔）

**消息类型**（通过 `orca orchestration check --wait --types` 指定）：
- `worker_done`：Worker 完成任务（通过 `send --type worker_done` 发送）
- `question`：Worker 需要协调者的阻塞式回答
- `escalation`：Worker 遇到无法自行解决的问题

**生命周期验证**（liveness）：
- `live`：进程运行中
- `unverifiable`：无法确认状态（网络失联、远程主机不可达）
- `exited`：进程已退出

**关键规则**：
- 只有 `exited` 或显式的 `worker_done` 才证明结束，`unverifiable` 或超时不算证据
- 收到消息后必须用 `orca orchestration check --ack <delivery_id>` 确认
- 结算后的 Worker 必须显式 `worker-release` 或 `worker-retain` 或复用

### 3. Worktree 隔离

每个 Worker 可以在独立的 git worktree 中工作：
```bash
orca worktree create --name <task-name> --no-parent --agent codex --prompt "<task>" --json
```

- `--no-parent`：独立顶层工作，默认基于 repo 的 base ref（通常是 origin/main）
- `--parent-worktree active`：基于当前 worktree 创建子任务（stacked work）
- `--agent <id>`：同时启动 agent（支持 codex、claude、cursor、antigravity、muse、opencode、zcode）
- `--prompt "<text>"`：发送初始任务描述

**重要限制（v1.4.224）**：
- `worktree create` **不支持** `--model` 和 `--effort` 参数
- 模型选择由各 agent 自己的配置决定（见下文"配置步骤"）
- 返回的 `result.agentTerminalHandle` 是 agent 句柄（旧版）或 `result.startupTerminal.handle`

## CLI 位置

**本机安装的 Orca CLI**：
```bash
/Applications/Orca.app/Contents/Resources/bin/orca
```

该路径未在 PATH 中，需要显式调用或创建 alias：
```bash
alias orca='/Applications/Orca.app/Contents/Resources/bin/orca'
```

## Brain/Worker/Tester 工作流

### 场景 1：Brain 监督式编排（推荐）

**Brain 作为 Coordinator**：

```bash
ORCA=/Applications/Orca.app/Contents/Resources/bin/orca

# 1. 确认运行时
$ORCA status --json

# 2. 创建 Run（协调命名空间）
$ORCA orchestration run-create --objective "实现用户认证功能" --json
# 返回 runId，后续命令会自动绑定到此 Run

# 3. 并行启动多个 Worker（完整波次在等待前全部启动）
$ORCA orchestration worker-start \
  --spec "实现登录接口：POST /api/login，接收 username/password，返回 JWT token。" \
  --worktree current --agent codex --json

$ORCA orchestration worker-start \
  --spec "实现注册接口：POST /api/register，验证邮箱格式，密码强度检查。" \
  --worktree current --agent codex --json

# 4. 等待 worker_done 消息（阻塞式）
$ORCA orchestration check \
  --wait \
  --types "worker_done,escalation,question" \
  --timeout-ms 900000 \
  --json

# 5. 处理返回的消息
# - 如果是 worker_done：验证结果，决定 release/retain/reuse
# - 如果是 question：用 orca orchestration reply --id <message_id> --body "<answer>" 回复
# - 如果是 escalation：记录问题并决定下一步

# 6. 确认消息并继续等待
$ORCA orchestration check \
  --ack <delivery_id> \
  --wait \
  --types "worker_done,escalation,question" \
  --timeout-ms 900000 \
  --json

# 7. 所有 Worker 结算后，清理资源
$ORCA orchestration worker-release --dispatch <dispatch_id> --json
```

**Worker 职责**（自动注入到 Worker 的 preamble 中）：
1. 只做当前 Task，需要协调者回答时用 preamble 中的 `ask` 命令
2. 按 preamble 指定的节奏发送心跳
3. 每个检查点读取协调者的后续消息：`orca orchestration check --terminal <handle> --json`
4. 完成后发送 `worker_done`：
   ```bash
   orca orchestration send \
     --type worker_done \
     --subject "登录接口完成" \
     --body "JWT 生成逻辑已验证，单元测试通过。" \
     --outcome succeeded \
     --files-modified "src/api/auth.ts,tests/auth.test.ts" \
     --json
   ```
5. 发送后进入空闲，等待新 Dispatch 或 release

**Tester 接入方式**：
- Brain 收到 `worker_done` 后，启动 Worker 指定为 Tester（静态审查 + 动态验证）：
  ```bash
  $ORCA orchestration worker-start \
    --spec "审查 Worker A 的登录接口实现：检查安全性、错误处理、测试覆盖。文件：src/api/auth.ts" \
    --worktree current --agent codex --json
  ```
- 或通过 `terminal send` 发送验收请求到常驻 Tester terminal

### 场景 2：Full Handoff（独立工作）

适用于不需要监督的独立任务（如 "让另一个 agent 做这个"）：

```bash
ORCA=/Applications/Orca.app/Contents/Resources/bin/orca

# Brain 创建新 worktree 并启动 Worker
$ORCA worktree create \
  --name implement-auth \
  --no-parent \
  --agent codex \
  --prompt "实现用户认证功能：登录、注册、JWT token 生成和验证。" \
  --json

# 返回后 Brain 的工作完成，Worker 在新 worktree 中独立运行
# 无需 run-create、无需 check --wait
```

### 场景 3：当前 worktree 启动 agent

对于已存在的 worktree，使用 `terminal create` 而非 `worktree create`：

```bash
ORCA=/Applications/Orca.app/Contents/Resources/bin/orca

# 在当前 worktree 启动 Codex
$ORCA terminal create --worktree active --command "codex" --json

# 在当前 worktree 启动 Claude Code
$ORCA terminal create --worktree active --command "claude" --json
```

**重要**：v1.4.224 没有 `agent launch` 命令，使用 `terminal create --command "<agent>"` 代替。

### 场景 4：常驻 Tester 接收通知

**方式 A：通过 terminal send**（适用于非结构化通知）：
```bash
$ORCA terminal send \
  --terminal <reviewer-handle> \
  --text "Worker A 已完成登录接口实现，请审查 src/api/auth.ts" \
  --enter \
  --json
```

**方式 B：通过 orchestration 消息**（结构化，支持类型和优先级）：
```bash
$ORCA orchestration send \
  --to dispatch:<dispatch_id> \
  --subject "审查请求：登录接口实现" \
  --body "请审查 src/api/auth.ts 的登录接口实现" \
  --type question \
  --json
```
- Tester 通过 `orca orchestration check --peek --format --json` 读取收件箱

## 配置步骤

### 1. 确认 Orca 安装和项目注册

```bash
ORCA=/Applications/Orca.app/Contents/Resources/bin/orca

# 查看版本和状态
$ORCA status --json

# 列出已注册的 repos
$ORCA repo list --json

# 确认当前项目已注册（应该看到 agentic-work-infra）
$ORCA repo list --json | grep -i agentic-work-infra
```

✅ 本项目已在 Orca 中注册（repo ID: 确认于 2026-10-15）

### 2. 配置 Agent 模型（sorrycode API）

**关键发现（2026-10-15 实测修正）**：
- `orca worktree create` **不支持** `--model` 和 `--effort`（其 help 中确实没有这两个参数）
- `orca orchestration worker-start` **支持** `--model` 和 `--effort`，是本项目选模型的主入口

`worker-start` 的模型参数规则（来自 `--help` 原文）：
- `--model <id>`：接受 Claude、Codex、Cursor、Antigravity、Muse 的 opaque provider model id
- `--effort <level>`：**必须配合 `--model`** 使用；OMP 只接受 `--model`，不支持 `--effort`
- 两者都不能与 `--terminal` 同时使用（复用已有 terminal 时模型由该 terminal 决定）
- OpenCode 选模型需要已有 worktree + 可验证的执行宿主 CLI + 可用模型，不支持 effort
- 其他 agent（含 zcode）按自身配置启动

**账户/模型配置位置**：
- Codex 账户配置：`~/Library/Application Support/Orca/profiles/`
- 或 Orca Desktop → Settings → Accounts

**当前状态**（从 `account list --json` 确认）：
- Codex 有 system default，使用 API key 认证
- Claude 无活动账户
- OpenCode 和 Devin 无账户

**待配置**：
1. 如何将 sorrycode API 配置为 Claude 和 Codex 的后端
2. 如何指定具体模型（如 opus-5-5、gpt-6-astra）

**推测路径**（需验证）：
- 检查 `~/Library/Application Support/Orca/profiles/<profile-id>/` 下的配置文件
- 或在 Orca Desktop Settings → Accounts 中添加自定义 API endpoint

### 3. 启动常驻 Brain 和 Tester

**方式 A：在 Orca Desktop 中手动创建**（推荐）：
1. 打开 Orca Desktop
2. 打开当前项目的 worktree
3. 创建 terminal：Menu → New Terminal
4. 在 terminal 中输入 `claude` 启动 Claude Code（作为 Brain）
5. 创建另一个 terminal，输入 `codex` 启动 Codex（作为 Tester）
6. 重命名 terminal 标题为 "Brain" 和 "Tester"

**方式 B：通过 CLI 启动**：
```bash
ORCA=/Applications/Orca.app/Contents/Resources/bin/orca

# 当前 worktree 启动 Brain（Claude Code）
$ORCA terminal create \
  --worktree active \
  --command "claude" \
  --title "Brain" \
  --json

# 当前 worktree 启动 Tester（Codex）
$ORCA terminal create \
  --worktree active \
  --command "codex" \
  --title "Tester" \
  --json
```

**确认句柄**：
```bash
# 列出当前 worktree 的 terminals
$ORCA terminal list --worktree active --json

# 显示特定 terminal 的信息
$ORCA terminal show --terminal <handle> --json
```

### 4. 验证配置

**测试简单的监督式编排**：
```bash
ORCA=/Applications/Orca.app/Contents/Resources/bin/orca

# Brain 执行
$ORCA orchestration run-create --objective "测试 Worker" --json
$ORCA orchestration worker-start \
  --spec "运行 ls -la 并输出结果" \
  --worktree current --agent codex --json
$ORCA orchestration check --wait --types "worker_done" --timeout-ms 60000 --json
```

**测试 Full Handoff**：
```bash
$ORCA worktree create \
  --name test-handoff \
  --no-parent \
  --agent codex \
  --prompt "输出当前目录并退出" \
  --json
```

## 与 Claude Code 的区别

| 能力 | Claude Code | Orca |
|------|-------------|------|
| 后台 agent | `--bg`、`claude agents` | `orca terminal create`、`orca terminal list` |
| 常驻会话 | `--name`、`claude attach` | Orca Desktop 的 worktree 和 terminal 管理 |
| 多 Agent 消息 | `SendMessage` 工具（会话间消息） | `orca orchestration` 命令（结构化任务编排） |
| 并行 worktree | `EnterWorktree`（临时隔离） | `orca worktree create`（持久化管理） |
| 可视化管理 | 无（纯 CLI） | Orca Desktop + Mobile Companion |
| 监督式编排 | 无（需手动轮询） | `orca orchestration check --wait`（阻塞式等待） |

**选择 Orca 的原因**（用户已确认）：
1. 可视化管理：Desktop 应用可以实时看到所有 agent 状态
2. 结构化编排：Run/Task/Dispatch 提供清晰的任务生命周期
3. 并行 worktree：每个 Worker 在独立环境中工作，结果对比和合并更清晰
4. 消息持久化：orchestration.db 记录所有消息，不会因 agent 重启丢失

## 本机运行时状态

**Orca 运行时**（确认于 2026-10-15）：
- Version: 1.4.224
- PID: 30722
- Runtime ID: 22dad164-f3da-41b3-abc6-bfc4762afd66
- WebSocket: ws://127.0.0.1:6768
- Unix Socket: /Users/zejiawu/Library/Application Support/orca/o-30722-22da.sock

**Orchestration DB**：
- 位置：`~/Library/Application Support/Orca/orchestration.db`
- 大小：452 KB
- 主要表：runs、tasks、worker_dispatches、messages、deliveries

**已注册 repos**：45 个（包括 agentic-work-infra）

## 待解决问题

以下问题需要进一步验证或查看 Orca 源码：

1. **自定义 API endpoint**：如何配置 sorrycode 作为 Claude 和 Codex 的后端？
   - 查看 `~/Library/Application Support/Orca/profiles/` 的 agent 配置
   - 或在 Orca Desktop Settings → Accounts 中配置

2. **模型选择**（已修正）：`worktree create` 不支持 `--model`/`--effort`，但 `worker-start` **支持**
   - 选模型走 `worker-start --model <id> [--effort <level>]`
   - 复用已有 terminal 时不能传这两个参数，模型由该 terminal 决定
   - 各 agent 无显式 `--model` 时按自身配置启动

3. **消息路由**：`orchestration send` 的 `--to` 参数支持的地址格式
   - `run:<id>`：发送给 Run 的协调者
   - `dispatch:<id>`：发送给特定 Dispatch 的 Worker
   - `@all`、`@idle`、`@codex`、`@claude`：组地址（发送给 Run 内的所有/空闲/特定类型 Worker）
   - `@worktree:<id>`：发送给特定 worktree 的所有 terminal

4. **常驻会话保持**：Orca Desktop 如何保证 Brain/Tester 不被自动关闭？
   - Orca 的 worktree 和 terminal 默认持久化，除非显式 `terminal close`
   - 需要确认 Orca Desktop 的 session 恢复机制（重启后是否自动恢复）

## 参考

- **Orca GitHub**：https://github.com/stablyai/orca（92,723 stars，MIT 许可）
- **官方文档**：https://onorca.dev/docs
- **Skill Guides**（本指南的主要来源）：
  - `skill-guides/orchestration.md`：监督式编排核心概念和循环
  - `skill-guides/orca-cli.md`：worktree 和 terminal 管理
  - `skill-guides/orchestration/references/`：详细参考（按需加载）
    - `coordinator-loop.md`：扩展的 DAG 编排和模型/effort 配置
    - `worker-contract.md`：Worker 的完整职责和协议
    - `messaging-and-gates.md`：消息路由和决策门
    - `placement-and-remote.md`：远程 Worker 和 SSH/WSL 部署
    - `recovery-and-cleanup.md`：失败处理、重试、清理
    - `low-level-topology.md`：自定义 argv 和 terminal 拓扑
    - `legacy-contract-migration.md`：旧版协议兼容

**版本说明**：本指南基于 Orca v1.4.224（2026-10-15）的实际 CLI 输出编写。更新版本的 Orca 可能支持新功能（如 `agent launch`、`--model`/`--effort` 参数），届时需要更新本指南。
