---
name: multi-agent-collab
description: >
  提供工具与模型无关的多 Agent 三角色（Brain / Worker / Tester）协作协议、契约格式与升级闭环。
  当项目需要启用多 Agent 角色隔离、制定任务包或执行独立验收时使用。
  不适用于单 Agent 即可完成的简单任务，也不硬编码任何特定编排软件的 CLI 或模型名称。
---

# 多 Agent 三角色协作 Skill

## 核心边界原则

1. **角色拆分的唯一依据是“信息差异”，而非“能力差异”**：
   同一个强模型既能写代码也能审代码，但**作者的上下文里包含“我为什么这么写”，这会导致验证退化为自我确认**。因此协作架构收敛为三个角色。
2. **双环解耦与 `HANDOFF.md` + Git Hook 事件驱动（Agent-Agnostic Event-Driven Dual-Loop）**：
   - **宏观架构环（人 $\leftrightarrow$ Thinking Brain）**：人类只面对唯一的主窗口（使用旗舰推理与沟通模型），专注需求对齐与架构决策；定稿后将任务契约写入仓库 `docs/HANDOFF.md`（顶部标记 `Status: pending`）并执行 `git commit`。
   - **事件触发与自动执行环（`.git/hooks/post-commit` $\rightarrow$ Execution Coordinator $\rightarrow$ Worker & Tester）**：下游独立常驻一个执行主会话（工具无关，可按项目是否需要原生桌面 CUA 等能力自由选用宿主）。通过 Git `post-commit` 钩子监听 `docs/HANDOFF.md` 的 `Status: pending` 提交并**秒级事件唤醒**下游执行总控（无提交时 0 轮询、0 Token 消耗；**严禁将未 `git commit` 的脏修改当作触发信号**）。
   - **单轮闭环不早退与状态头防死循环铁律**：一旦执行主会话被唤醒，必须在当前唤醒周期内**持续等待（循环 `wait_agent`，严禁短超时早退睡眠）**，串联跑完 `Worker 实现 → Tester 独立真机验收 → 将 HANDOFF.md 更新为 Status: verified（附 Verified-Commit）并 git commit` 全链路；因收口提交的状态为 `Status: verified`，`post-commit` 钩子自动静默放行，天然杜绝死循环与文档整理误触发。
3. **上下文当缓存管（Inline & Spill）与热节点复用**：
   - **Inline & Spill**：主会话只内联（Inline）任务 ID、结论摘要与文件路径锚点，完整细节与证据落盘（Spill）到工作区文件中按需索引。
   - **热节点复用（Warm Teammates）**：执行总控在项目周期内持续复用已驻留的具名 Worker 与 Tester 子会话（实测 KV Prompt Cache 命中率可达 95%+），消除每次新建空白会话的冷启动重读税。

| 角色 | 职责定位 | 模型选型倾向 | 严禁越界行为 |
| --- | --- | --- | --- |
| **Brain**（宏观架构与路由层） | 承接人类唯一交互入口、冻结上游契约、提交 `HANDOFF.md` 触发下游、最终审美把关 | **旗舰模型**（最懂人话、全局视野与审美最强） | 不亲自写具体业务代码、不把冗长工具日志灌入主窗口 |
| **Worker**（隔离实现层，默认串行） | 按任务包实现完整垂直切面、编写并跑通单元测试（自反馈）、按验收反馈修复 | **次旗舰 / 高执行力编码模型** | 不直接向人类抢话、不跨模块越权修改、不给自己发合格证 |
| **Tester**（独立验收与 Watchdog 层） | 独立静态审查 + 动态真机验证（Playwright / 原生桌面 CUA 交互取证） | **次旗舰 / 强工具与视觉模型** | 不直接替 Worker 改代码、不自创未忽略临时目录污染仓库 |

## 子 Agent 派发与并发配额纪律

Brain 调度 Worker 与 Tester 时，必须按**读写性质与耦合边界**严格限制并发数量，禁止把一个模块拆成多个零碎小功能同时派给多个子 Agent：

| 任务类型 | 合理并发数 | 硬性前提与拆分粒度 |
| --- | --- | --- |
| **局部微调 / 上游契约冻结** | **`0`（Fast Path）** | 仅限 ≤5 步工具调用的微调或上游共享契约（如 `schema.py`）的冻结，由主会话直接完成；**一旦涉及完整业务切面实现或耗时测试，主会话严禁自己硬干，必须下沉给 Worker**。 |
| **共享工作区写任务（Worker）** | **`1`（严格串行）** | 同一本地目录（共享 Working Tree）下，**同一时刻只能有 `1` 个活跃 Worker**，严禁多子 Agent 并发改代码、争抢构建锁或互相污染测试状态。 |
| **隔离工作树写任务（Worker）** | **`2 ~ 3`（封顶）** | 仅当 **① 具备独立 Git Worktree**、**② 写文件集 100% 物理正交**、且 **③ 上游共享 Schema 已提前冻结**时才允许并行；必须按**完整垂直业务切面**拆分，禁止按小函数/小按钮拆分。 |
| **只读探索 / 独立审查（Explore / Tester）** | **`2 ~ 4`（封顶）** | 无写入冲突的跨子系统调研或多维度静态审查可并行扇出，按正交子系统或审查视角划分。 |

## 标准协作闭环

```text
人（目标与审批）
  ↓
[Brain] 制定架构契约与《任务包》
  ↓
[Worker] 实现功能 + 单元测试自检 → 提交待验
  ↓
[Tester] 独立审查（阶段1：静态审查 → 阶段2：动态验证）
  ├── ✅ 通过         → 通知 Brain 可合入/发布
  ├── ❌ 实现问题     → 退回 Worker 修复（附精确位置与原因，上限 3 次）
  └── ⚠️ 契约/架构问题 → 升级回 Brain 重写契约与任务包（不让 Worker 硬凑）
```

## 角色间通信契约（工具无关）

无论底层使用何种编排运行时（原生子 Agent、工作流脚本、多终端或人工调度），角色间交互必须通过以下三种结构化契约传递，拒绝口头模糊指令：

### 1. 任务包（Brain → Worker & Tester）
```markdown
# Task: <任务名称>
- **授权范围**：允许修改的文件/目录，只读依赖的模块
- **不在范围内**：明确排除的功能（防止 Worker 顺手扩权）
- **接口与行为契约**：输入、输出、边界条件、错误处理、性能要求
- **Worker 自检要求**：需覆盖的单元测试场景
- **Tester 验收标准**：静态安全检查项、集成测试与真实入口验证项
```

### 2. 验收报告（Tester → Brain & Worker）
```markdown
# 验收报告：<任务名称>
- **结论**：✅ 通过 | ❌ 实现问题（退回 Worker） | ⚠️ 契约问题（升级 Brain）
- **静态审查结果**：契约符合度、边界越权检查、安全风险排查
- **动态验证结果**：集成测试、真实环境/部署核验的实际观测证据
- **必须修复项**（若为实现问题）：文件路径、行号、复现条件与原因
- **需 Brain 裁定项**（若为契约问题）：契约冲突点或架构缺陷说明
```

### 3. 全局交接状态机与 Git `post-commit` 极简触发协议（`docs/HANDOFF.md`）
为实现跨宿主、Agent 无关的全自动触发（消灭定时轮询的等待延迟与空转 Token 税，同时防止下游收口提交或日常文档整理误触发死循环），`docs/HANDOFF.md` 顶部维护确定性状态头，配合 8 行 `.git/hooks/post-commit` 脚本实现秒级闭环：
- **`Status: pending`**：由上游 Brain 定稿任务后写入并 `git commit`（**永远不把具体代码 diff 塞进交接文档**），作为触发 `post-commit` 秒级唤醒下游的唯一信号；
- **`Status: verified`（附 `Verified-Commit: <sha>`）**：由下游执行总控在 Worker 实现并通过 Tester 独立验收后更新并 `git commit`（因状态不再是 `pending`，`post-commit` 自动忽略，防止自己唤醒自己的死循环）；
- **`Status: blocked`**：连续 3 轮未通过验收或遇架构/权限冲突时标记，主动通知人类裁定。

```bash
#!/usr/bin/env bash
# .git/hooks/post-commit（仅当本次 commit 修改了 docs/HANDOFF.md 且顶部为 Status: pending 时秒级唤醒下游）
if git diff-tree --no-commit-id --name-only -r HEAD --root | grep -qx "docs/HANDOFF.md"; then
  if grep -qx "Status: pending" docs/HANDOFF.md 2>/dev/null; then
    export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
    codex queue --thread "$CODEX_COORD_THREAD_ID" --message "docs/HANDOFF.md 有新提交（Status: pending），请读取并执行。" >/dev/null 2>&1 || true
    open -g "codex://threads/wake/${CODEX_COORD_THREAD_ID}" >/dev/null 2>&1 || true
  fi
fi
```

## 升级路径与人的介入时机

升级链条固定为：`Worker → Tester → Brain → 人`。

- **Worker 遇到边界不清**：停止猜测，上报 Brain 澄清契约。
- **Tester 必须唤醒人**：发现安全/数据泄露风险、涉及不可逆生产操作、或发现 Brain 的架构决策有根本性缺陷。
- **Brain 必须唤醒人**：需要改变项目对外目标/范围、多个技术方案存在业务价值取舍、或同一任务连续 3 轮未通过 Tester 验收。

## 验收清单

- [ ] 实现者（Worker）与验收者（Tester）保持上下文隔离，未发生“作者自审自合”
- [ ] 未发生共享工作区多子 Agent 并发写（Write=1），未将同一垂直切面拆成零碎小任务并发派发
- [ ] 每个派发的任务均具备明确《任务包》（含“不在范围内”声明）
- [ ] 单元测试仅作为 Worker 自检手段，最终放行依据来自 Tester 的独立验收报告
- [ ] 连续 3 次修复失败时已触发契约重审或升级给人，未陷入无限重试循环
- [ ] 角色定义与宿主工具、特定模型型号解耦

---

深度参考：
- [references/rationale.md](references/rationale.md) — 三角色合并与拆分的推导证明（Brain=Architect, Tester=Reviewer, Worker≠Tester）
- [assets/roles.template.md](assets/roles.template.md) — 供目标项目按需实例化的极简 `docs/ROLES.md` 模板
