# Orca 多 Agent 协作配置指南

本指南基于本机 Orca v1.4.224 的 CLI/skill 文档、Orca 官方发布说明及本机只读核验，说明如何使用 Orca 实现 Brain/Worker/Tester 三角色协作（角色定义见 [三角色协作设计.md](三角色协作设计.md)）。具体行为以实际安装版本的 `orca <command> --help` 为准。

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

## 2. Orchestration 消息系统与编排绑定守则

- Brain 作为 Orca Coordinator，先读取当前安装版本的编排协议：`orca skills get orchestration`。
- 创建受监督 Worker 或 Tester 的标准路径是 `orca orchestration worker-start`，不要把普通 New Terminal 或 `orca worktree create --agent` 当作 supervised worker。
- Worker 和 Tester 必须作为 Orca Dispatch 启动，才能收到包含 Task ID、Dispatch ID、终端句柄和生命周期命令的注入 preamble。Agent 必须使用 preamble 中的精确值，不自行重建 ID 或句柄。
- `worker-start` 返回后，若项目绑定了特定 Provider/模型（例如指定 `--agent`、`--model`、`--effort`），Brain 应检查返回 JSON 中的 `worker.launch.effective.agent`、`worker.launch.effective.model` 等字段；不符时立即停止编排并报告，不静默降级。

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

**重要限制（本机 v1.4.224 CLI 实测）**：
- `worktree create` 不接受 `--model` 和 `--effort`。
- `orchestration worker-start` 接受这两个参数；`--effort` 必须同时传 `--model`，且两者不能与 `--terminal` 一起使用。复用已有 terminal 时，模型由该 terminal 的启动配置决定。
- 具体模型 ID 取决于 agent/provider。不要把示例 ID 当作 Orca 通用模型名。
- 返回结果的 terminal handle 字段可能因启动路径而异；按实际 JSON 中的 `startupTerminal.handle` 或兼容字段读取。

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

# 如需覆盖本次 Codex Worker 的模型，可显式指定模型；effort 必须与 model 一起传。
$ORCA orchestration worker-start \
  --spec "为登录接口补充安全测试。" \
  --worktree current --agent codex --model <provider-model-id> --effort <level> --json

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

### 1. 确认 Orca 安装和运行状态

```bash
ORCA=/Applications/Orca.app/Contents/Resources/bin/orca

# 查看版本和状态
$ORCA status --json

# 列出 repos（需要 Orca runtime 可用）
$ORCA repo list --json
```

**本机核验（2026-10-15）**：安装版本为 `1.4.224`。Orca 当前已退出，`status --json` 返回 `app.running=false`、`runtime.state=not_running`，因此 CLI 的 `repo list` 和 `account list` 无法读取 runtime metadata。另对 Orca profile-state 数据库做了只读核验：`agentic-work-infra` 已登记为本地 Git 项目，设置状态为 `ready`，导入方式为 existing folder。这个持久化记录能确认项目登记，不能替代运行中的 pane/account 状态。旧笔记中的 PID、runtime ID 和 socket 地址属于瞬时信息，不保留。

### 2. Codex 与 SorryCode 配置

本机 Codex CLI 的 SorryCode provider 配置位于 `~/.codex/config.toml`，本次只读检查确认当前 `model_provider` 为 `sorrycode`、模型为 `gpt-6.1-sol`、endpoint 为 `https://api.sorrycode.com/v1`。检查只输出了 provider、模型和 endpoint 元数据，没有读取或展示密钥。

Orca 官方 Codex 说明确认：`System default` 使用真实的 `~/.codex`；Orca 额外管理的 Codex account 使用隔离 home，并将真实 `~/.codex/config.toml` 中的设置同步到当前 runtime home。受管 account 的设置同步失败时会保留上次成功同步的设置；已运行的 Codex session 要重启后才会使用新选择的 account。本机 `codex-pane-accounts.json` 只有 Loomscore 工作区的 `real-home` 记录，没有 `agentic-work-infra` 的显式 pane 选择；该文件未覆盖的默认路由不能仅凭 Orca 已退出时的磁盘状态确认。受管 home 当前没有 `config.toml`，也不能单独证明项目 pane 的实际路由或同步结果。

**结论与操作**：SorryCode 已配置在本机 Codex 全局配置中；本次未改动任何 API key 或 Orca profile。下次打开 Orca 后，检查 `agentic-work-infra` Codex pane 的 account：若要直接使用当前 Codex 默认配置，选择 `System default`；若使用受管 account，先确认 Orca 显示其设置同步正常，再新开/重启 Codex session。不要把 `orca account add --agent codex` 当作添加 SorryCode provider 的办法，它启动的是 Codex device-auth 登录流程。若要在 Claude Code 使用 SorryCode，需按 Claude Code 自身的 provider 配置方式另行设置。

### 3. 自动更新状态与核查

本机 Orca 版本是 `1.4.224`。截至 2026-10-15，Orca 官方 GitHub Releases 页面、GitHub Release API 和官方 macOS update feed 都可核验到 `v1.4.224`；该版本已发布、不是 draft 或 prerelease，并包含 macOS arm64 安装资产。第三方 SourceForge 镜像页面存在元数据冲突：`/v1.4.224/` 文件目录列出 `1.4.224` 资产，但页面的“Latest Version”文案出现 `1.4.226`；该站点同时声明自己不是 Orca 官方关联方。对应 GitHub tag、release 页面和下载地址均无法核验 `1.4.225`/`1.4.226`，因此镜像页面的更高版本字符串不足以证明存在更高的官方正式版。当前只能确认官方渠道可验证的版本是 `1.4.224`，不能据此断言全网不存在更高的未发布或非官方构建。这不证明先前的自动更新流程成功，也不能仅凭界面上的失败提示判断安装损坏。由于没有记录尝试更新前的版本，无法判断是否曾升级完成后又在退出、重启或状态提示阶段报错。

安装包内的 `app-update.yml` 指向 GitHub `stablyai/orca`，并含 `releaseType: draft`。electron-builder v26 文档将 `releaseType` 定义为 GitHub 发布选项，默认会创建 draft release；自动更新文档说明打包后的 `app-update.yml` 提供更新源配置。GitHub 上未发布的 draft 对公开更新不可见，但 `v1.4.224` 本身是已发布的正式版。因此，仅看到包内这个字段，不能证明 Orca 客户端在请求 draft，也不能解释本次失败。

Orca 官方仓库有一条相似的 macOS 报告：v1.4.209 更新至 v1.4.210 时，第一次检查曾用新 release tag 请求旧版本 zip，导致 404；再次检查后成功。该 issue 仍是未解决报告，只能说明“缓存的更新信息/发布时序”是一个可能路径，不能证明本机这次失败也是同一原因。本机 `~/Library/Caches/orca-updater/pending/update-info.json` 不存在，`daemon.log` 只有普通连接记录；Orca 主进程 updater 的具体失败信息未被现存日志捕获。因此，自动更新失败根因仍无法确认。不要手动改写 `/Applications/Orca.app` 内的 `app-update.yml`。

如之后仍需诊断失败原因，应保留具体失败时刻和 updater 日志中的错误码/错误文本，再检查网络请求、发布 feed/manifest、下载与校验、macOS 安装过程。当前 Orca 已退出，本次没有重启它，也没有执行更新或安装操作。

### 4. 启动常驻 Brain 和 Tester

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

### 5. 验证配置

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

只记录本次可复核且对配置决策有用的状态：截至 2026-10-15，CLI 版本为 `1.4.224`，Orca app/runtime 已退出。profile-state 数据库确认 `agentic-work-infra` 项目已登记且设置状态为 `ready`；运行时 CLI 当前不能查询实时 account/pane 状态。旧笔记里的 PID、Runtime ID、WebSocket、Unix socket、数据库大小和 repo 数量都属于瞬时状态，不作为当前事实保留。

## 待解决问题

以下内容保持为待核实项，不据旧笔记推断：

1. `agentic-work-infra` 已在本机 profile-state 中登记且状态为 `ready`；它的 Codex pane 当前是否明确选择 real-home 或 Orca managed account 仍未核实。Orca 运行后在项目 pane 的 account 设置中确认；若选 managed account，再确认配置同步状态。
2. Orca 退出后是否会自动恢复特定 Brain/Tester 会话。本文不将“worktree/terminal 可持久化管理”推导为“进程或 agent 会话一定自动恢复”。
3. 本次自动更新失败的具体原因。需有对应失败日志或错误码才能判断。

## 参考

- **Orca GitHub**：https://github.com/stablyai/orca
- **本机所装正式版发布说明**：https://github.com/stablyai/orca/releases/tag/v1.4.224
- **第三方 SourceForge 镜像（页面元数据与文件目录存在冲突，非官方关联方）**：https://sourceforge.net/projects/orca.mirror/files/v1.4.224/
- **官方文档**：https://onorca.dev/docs
- **Codex 配置与账户切换**：https://www.onorca.dev/docs/agents/codex 和 https://www.onorca.dev/docs/agents/codex-hot-swap
- **macOS 自动更新相似报告（未解决）**：https://github.com/stablyai/orca/issues/22621
- **electron-builder v26 发布与更新源说明**：https://www.electron.build/v26/docs/publish/
- **electron-builder v26 自动更新说明**：https://www.electron.build/v26/docs/features/auto-update/
- **electron-builder 自动更新排障**：https://www.electron.build/v26/docs/troubleshooting/
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

**版本说明**：CLI 参数结论对应本机 Orca v1.4.224（2026-10-15）实测。Orca 更新后应重新检查安装版本对应的 `--help` 与官方发布说明；不要根据旧文档推测命令是否新增或参数是否变更。
