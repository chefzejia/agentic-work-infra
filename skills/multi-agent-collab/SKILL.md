---
name: multi-agent-collab
description: >
  提供工具与模型无关的多 Agent 双环四重身份（Brain · Router · Worker · Tester）协作协议、契约格式与升级闭环。
  当项目需要启用多 Agent 角色隔离、制定任务包或执行独立验收时使用。
  不适用于单 Agent 即可完成的简单任务，也不硬编码任何特定编排软件的 CLI 或模型名称。
---

# 多 Agent 双环四重身份协作 Skill

## 核心边界原则

1. **角色拆分的唯一依据是“信息差异”与“交互对象差异”，而非“能力差异”**：
   同一个强模型既能写代码也能审代码，但**作者的上下文里包含“我为什么这么写”，会导致验证退化为自我确认**（因此 `Worker ≠ Tester`）；而当采用跨宿主/后台自动执行时，**面对人类聊天的架构会话与面对自动化 Git 钩子的后台总控会话，其交互对象与阻塞语义完全不同**——如果后台总控不知道自己是“无人值守 Router”，收到队列消息时就会误以为对面坐着真人在聊天，遇到授权范围微调就停在后台窗口里向空气提问！因此完整架构包含 **双环四重身份（Brain · Router · Worker · Tester）**。
2. **双环四重身份与 `HANDOFF.md` + Git Hook 事件驱动（Agent-Agnostic Event-Driven Dual-Loop）**：
   - **第一环：宏观思考环（人 $\leftrightarrow$ Thinking Brain）**：人类唯一面对的沟通入口（选用旗舰模型），专注需求碰撞、产品审美与架构决策；定稿后将任务契约写入仓库 `docs/HANDOFF.md`（顶部标记 `Status: pending`）并执行 `git commit`。
   - **第二环：无人值守执行环（`.git/hooks/post-commit` $\rightarrow$ Execution Router $\rightarrow$ 常驻 Worker & Tester）**：
     - 通过 Git `post-commit` 钩子监听 `docs/HANDOFF.md` 的 `Status: pending` 提交，向后台常驻的 **Execution Router（执行总控会话）** 发送带 `[AUTO-WAKEUP]` 标识的机器唤醒指令；
     - **Router 无人值守铁律（严禁在后台会话向人类提问等待）**：Router 的触发源是自动化 Git 钩子而非人类聊天，**绝对禁止在后台会话里停下来向人类提问等待回复**！当独立 Tester 抓到 Bug 且属于同一任务目标下的漏列关联文件（如改设置 UI 需同步修对应插件的设置消费逻辑）时，Router **有权直接在任务目标范围内授权 Worker 补齐修改并重跑 Tester**；若遇真正的跨核心（`core/`）契约冲突或连续 3 轮修复未过，Router 必须将阻塞证据写入 `docs/HANDOFF.md`（更新为 `Status: blocked`）并 `git commit` 退回给上游 Brain。
     - **单轮闭环不早退铁律**：一旦 Router 被唤醒，必须在当前唤醒周期内**持续等待（循环 `wait_agent`，严禁 10s 短超时早退睡眠）**，串联跑完 `Worker 实现 → Tester 独立真机验收 → 将 HANDOFF.md 更新为 Status: verified（附 Verified-Commit）并 git commit` 全链路。
   - *注：在无需跨宿主的简单单软件项目里，Brain 与 Router 可由同一个主会话兼任（退化为三节点）；一旦拆分为跨窗口/跨宿主双环，必须显式立住 Router 身份。*
3. **上下文当缓存管（Inline & Spill）与热节点复用**：
   - **Inline & Spill**：Brain 与 Router 只内联（Inline）任务 ID、结论摘要与文件路径锚点，完整细节与证据落盘（Spill）到工作区文件中按需索引。
   - **热节点复用（Warm Teammates）**：Router 在项目周期内持续复用已驻留的具名 Worker 与 Tester 子会话（实测 KV Prompt Cache 命中率可达 97%+），消除每次新建空白会话的冷启动重读税。

| 角色身份 | 所在环与交互对象 | 职责定位 | 模型选型倾向 | 严禁越界行为 |
| --- | --- | --- | --- | --- |
| **1. Brain**（宏观架构师） | **思考环**（唯一面对人类） | 承接人类模糊意图、冻结上游 `core/` 契约、提交 `HANDOFF.md (Status: pending)`、最终审美把关 | **旗舰模型**（最懂人话、全局视野与审美最强） | 不亲自写具体业务代码、不把冗长工具日志灌入主窗口 |
| **2. Router**（无人值守执行总控） | **执行环**（面对 Git Hook 与子代理） | 接收 `[AUTO-WAKEUP]` 信号、循环 `wait_agent` 串联调度常驻 Worker 与 Tester、裁决同切面局部范围补齐、回写 `Status: verified / blocked` | **次旗舰 / 高稳定性编排模型** | **严禁在后台窗口停下向人类提问等回复**、严禁 10s 短超时早退、不亲自下场写业务代码 |
| **3. Worker**（隔离实现层，默认串行） | **执行环**（面对 Router） | 按任务包实现完整垂直切面、编写并跑通单元测试（自反馈）、按 Tester 反馈修复 | **次旗舰 / 高执行力编码模型** | 不直接向人类抢话、不私改 `core/` 冻结契约、不给自己发合格证 |
| **4. Tester**（独立验收与 Watchdog 层） | **执行环**（面对 Router） | 独立静态审查 + 动态真机验证（Playwright / 原生桌面 CUA 交互取证，不抢占用户正在使用的真实宿主焦点） | **次旗舰 / 强工具与视觉模型** | 不直接替 Worker 改代码、不自创未忽略临时目录污染仓库、不碰用户真实数据 |

## 子 Agent 派发与并发配额纪律

Brain / Router 调度 Worker 与 Tester 时，必须按**读写性质与耦合边界**严格限制并发数量，禁止把一个模块拆成多个零碎小功能同时派给多个子 Agent：

| 任务类型 | 合理并发数 | 硬性前提与拆分粒度 |
| --- | --- | --- |
| **局部微调 / 上游契约冻结** | **`0`（Fast Path）** | 仅限 ≤5 步工具调用的微调或上游共享契约（如 `schema.py` / `seams.ts`）的冻结，由 Brain 直接完成；**一旦涉及完整业务切面实现或耗时测试，严禁自己硬干，必须下沉给执行环**。 |
| **共享工作区写任务（Worker）** | **`1`（严格串行）** | 同一本地目录（共享 Working Tree）下，**同一时刻只能有 `1` 个活跃 Worker**，严禁多子 Agent 并发改代码、争抢构建锁或互相污染测试状态。 |
| **隔离工作树写任务（Worker）** | **`2 ~ 3`（封顶）** | 仅当 **① 具备独立 Git Worktree**、**② 写文件集 100% 物理正交**、且 **③ 上游共享 Schema 已提前冻结**时才允许并行；必须按**完整垂直业务切面**拆分，禁止按小函数/小按钮拆分。 |
| **只读探索 / 独立审查（Explore / Tester）** | **`2 ~ 4`（封顶）** | 无写入冲突的跨子系统调研或多维度静态审查可并行扇出，按正交子系统或审查视角划分。 |

## 标准双环四角色协作闭环

```text
👤 人（唯一交互入口：宏观目标与审美裁定）
  ↕
🧠 [Brain] 制定架构契约，写入 docs/HANDOFF.md (Status: pending) 并 git commit
  ↓  (.git/hooks/post-commit 发送 [AUTO-WAKEUP] 机器指令，2 秒内静默唤醒)
🧭 [Router] 无人值守执行总控（单轮循环 wait_agent，绝不停下向人提问）
  ├── 派发 🔨 [Worker] 实现垂直切面 + 单测自检
  └── 唤醒 🔍 [Tester] 独立审查（阶段1：静态审查 → 阶段2：无干扰动态/真机验证）
        ├── ✅ 全部通过 → Router 将 HANDOFF.md 更新为 Status: verified 并 git commit 收口
        ├── 🔧 实现缺陷或同目标漏列支撑文件 → Router 直接授权 Worker 修复/补齐并重跑 Tester（上限 3 次）
        └── ⚠️ 核心契约冲突或连败 3 次 → Router 将证据写入 HANDOFF.md (Status: blocked) 并 git commit 退回 Brain
```

## 角色间通信契约（工具无关）

无论底层使用何种编排运行时，角色间交互必须通过以下结构化契约传递，拒绝口头模糊指令：

### 1. 任务包（Brain 写入 `docs/HANDOFF.md` → Router / Worker / Tester）
```markdown
# Task: <任务名称>
- **授权范围**：允许修改的文件/目录，只读依赖的模块（若 Tester 发现完成本任务目标必须连带修改同切面支撑文件，Router 可直接授权补齐）
- **不在范围内**：明确排除的功能与严禁触碰的目录（如 `src/core/` 冻结接口或用户真实数据）
- **接口与行为契约**：输入、输出、边界条件、错误处理、性能要求
- **Worker 自检要求**：需覆盖的单元测试场景
- **Tester 验收标准**：静态安全检查项、集成测试与无干扰真机验证项
```

### 2. 验收报告（Tester → Router）
```markdown
# 验收报告：<任务名称>
- **结论**：✅ 通过 | ❌ 实现问题（退回 Worker） | ⚠️ 核心契约冲突（由 Router 标记 blocked 退回 Brain）
- **静态审查结果**：契约符合度、边界越权检查、安全风险排查
- **动态验证结果**：集成测试、真实环境/部署核验的实际观测证据
- **必须修复项**（若为实现问题）：文件路径、行号、复现条件与原因
- **需升级裁定项**（若为核心契约问题）：契约冲突点或架构缺陷说明
```

### 3. 全局交接状态机与 `[AUTO-WAKEUP]` Git Hook 触发协议（`docs/HANDOFF.md`）
为实现跨宿主、Agent 无关的全自动触发，同时**消除下游 Router 的身份迷失（防止它把唤醒消息当成人类聊天而停下提问）**，`docs/HANDOFF.md` 顶部维护确定性状态头，配合 8 行 `.git/hooks/post-commit` 脚本：
- **`Status: pending`**：由上游 Brain 定稿任务后写入并 `git commit`，作为触发 `post-commit` 秒级唤醒下游 Router 的唯一信号；
- **`Status: verified`（附 `Verified-Commit: <sha>`）**：由下游 Router 在 Worker 实现并通过 Tester 独立验收后更新并 `git commit`（因状态不再是 `pending`，`post-commit` 自动忽略，防止死循环）；
- **`Status: blocked`**：遇到 `core/` 级契约冲突或连续 3 轮未通过验收时，由 Router 写入阻塞证据并 `git commit` 退回上游 Brain。

```bash
#!/usr/bin/env bash
# .git/hooks/post-commit（仅当本次 commit 修改了 docs/HANDOFF.md 且顶部为 Status: pending 时秒级唤醒下游 Router）
if git diff-tree --no-commit-id --name-only -r HEAD --root | grep -qx "docs/HANDOFF.md"; then
  if grep -qx "Status: pending" docs/HANDOFF.md 2>/dev/null; then
    export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
    codex queue --thread "$CODEX_COORD_THREAD_ID" \
      --message "[AUTO-WAKEUP] 你是无人值守 Execution Router（非人类交互窗口）。请读取 docs/HANDOFF.md (Status: pending)，在同一轮次内循环 wait_agent 调度常驻 Worker 与独立 Tester 完成闭环并提交 Status: verified（若遇同目标漏列支撑文件可直接授权 Worker 补齐；若遇核心契约冲突则提交 Status: blocked），严禁在会话中停下向人类提问等待回复。" >/dev/null 2>&1 || true
    open -g "codex://threads/wake/${CODEX_COORD_THREAD_ID}" >/dev/null 2>&1 || true
  fi
fi
```

## 升级路径与人的介入时机

升级链条固定为：`Worker ↔ Tester ↔ Router → Brain → 人`。

- **Worker 遇到同目标文件漏列或实现报错**：上报 Router；若属任务目标直接关联的非核心支撑文件，由 **Router 直接拍板授权补齐**并重跑 Tester。
- **Router 必须退回 Brain（标 `Status: blocked`）**：需要修改上游已冻结的 `core/` 公共契约、涉及破坏性操作、或同一任务连续 3 轮未通过 Tester 验收。
- **Brain 必须唤醒人**：需要改变项目对外目标/范围、多个技术方案存在业务价值取舍、或收到 `Status: blocked` 需人类做方向裁定。

## 验收清单

- [ ] 四重身份边界清晰：Brain 面向人类定契约，Router 无人值守管闭环，Worker 串行实现，Tester 独立验收
- [ ] Router 收到 `[AUTO-WAKEUP]` 后未在后台窗口停下向人类提问等待，也未发生 10s 短超时早退
- [ ] 未发生共享工作区多子 Agent 并发写（Write=1），未将同一垂直切面拆成零碎小任务并发派发
- [ ] 单元测试仅作为 Worker 自检手段，最终放行依据来自 Tester 的独立验收报告（且真机验收未干扰用户正在使用的真实宿主窗口）
- [ ] 角色定义与宿主工具、特定模型型号解耦

---

深度参考：
- [references/rationale.md](references/rationale.md) — 为什么从三角色演进为双环四重身份（Brain · Router · Worker · Tester）的推导与实证
- [assets/roles.template.md](assets/roles.template.md) — 供目标项目按需实例化的极简 `docs/ROLES.md` 模板
