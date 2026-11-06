---
name: multi-agent-collab
version: 1.0.0
description: >
  提供工具与模型无关的多 Agent 双环四重身份（Brain · Router · Worker · Tester）协作协议、契约格式与升级闭环。
  当项目需要启用多 Agent 角色隔离、制定任务包或执行独立验收时使用。
  不适用于单 Agent 即可完成的简单任务，也不硬编码任何特定编排软件的 CLI 或模型名称。
---

# 多 Agent 双环四重身份协作 Skill

## 核心边界原则

1. **角色拆分的唯一依据是“信息差异”与“交互对象差异”，而非“能力差异”**：
   同一个强模型既能写代码也能审代码，但**作者的上下文里包含“我为什么这么写”，会导致验证退化为自我确认**（因此 `Worker ≠ Tester`）；而当采用跨宿主/后台自动执行时，**面对人类聊天的架构会话与面对自动化 Git 钩子的后台总控会话，其交互对象与阻塞语义完全不同**——如果后台总控不知道自己是“无人值守 Router”，收到队列消息时就会误以为对面坐着真人在聊天，遇到授权范围微调就停在后台窗口里向空气提问！因此完整架构包含 **双环四重身份（Brain · Router · Worker · Tester）**。
2. **双环四重身份契约（宿主无关）与默认 Git 参考实现（`TASKS.md + post-commit`）**：
   - **第一环：宏观思考环（人 $\leftrightarrow$ Thinking Brain）**：人类唯一面对的沟通入口（选用旗舰模型），专注需求碰撞、产品审美与架构决策（当面对海量外部 Issues/PR 时，先经仓外 Triage 聚类去重，仅将近期确认立项的活跃任务放入调度板）；定稿后将任务契约以独立编号区块 `## [Task #N] <标题>`（标记 `Status: pending` 与写作用域 `Scope`）写入仓库 `docs/TASKS.md`，并执行隔离提交 `git commit --only docs/TASKS.md`（严禁把后台 Worker 正在修改的半成品代码误打包进提交）：
     - **追加排队（In-File Queue）**：若上一轮 `[Task #N-1]` 仍处于 `Status: pending / in_progress`（后台正在执行），Brain **绝不覆盖或删除 `#N-1`**，直接在文件末尾追加 `## [Task #N]`（`Status: pending`）；
     - **推翻旧单（Supersede）**：若需推翻尚未跑完的 `#N-1`，Brain 将 `## [Task #N-1]` 的状态改为 `Status: superseded (by #N)`，并在下方追加新方案 `## [Task #N]`（`Status: pending`）；
     - **滑动自净（Sliding Window GC）**：文件内仅保留所有未结案区块（`pending / in_progress / blocked`）及最近 `1 ~ 2` 个已结案区块（`verified / superseded`）作为上下文锚点，更早的已结案区块在追加新单时顺手移出（完整历史由 `git log` 保存）。
   - **第二环：无人值守执行环（战术总控 Router $\rightarrow$ Worker & Tester，显性问题 100% 自闭环）**：
     - 在默认的 Git 事件驱动实现中，本地安装 `.git/hooks/post-commit` 监听**已提交树（`HEAD:docs/TASKS.md`）**中存在 `Status: pending` 的任务区块，向**唯一常驻的 Execution Router（单消费者 Single-Consumer）**发送 `[AUTO-WAKEUP]` 机器指令（若宿主不支持常驻会话，也可退化为单次无状态调度器，启动时扫描未结案的 `pending / in_progress` 区块恢复执行）；
     - **Router 是有决断力的现场战术法官（而非无脑传话筒）**：Router 的触发源是自动化钩子而非人类聊天，**绝对禁止在后台会话里停下来向人类提问等待回复**！当 Tester 打回或 Worker 受阻时，Router 必须当场执行**分诊、记账与战术自愈（显性问题不出执行环，战略冲突才报 Brain）**：
       1. **现场分诊与战术决断**：凡属**显性工程/体验问题**（实现漏项、交互/排版瑕疵、测试逃逸，或完成任务目标所需的同切面支撑文件漏列且未触碰【不在范围内 / 严禁触碰】黑名单），**一律由 Router 在执行环内直接拍板解决**——动态授权支撑文件、明确指出根因修复方向（若 Worker 连续 2 轮在同一症状打表层补丁，Router 必须介入止损并重定根因重构方案），绝不拿显性 Bug 打扰上游 Brain；
       2. **执笔 `docs/LESSONS.md` 与 `Seen 3×` 守卫自进化**：只要发生 Tester 打回（说明残次品逃过了 Worker 的自检门禁），**由同时握有“Worker 自检报告”与“Tester 翻车现场”的 Router 亲自在 `docs/LESSONS.md` 中新增或累加该漏检模式（`Seen N×`）**；若某条显性工程规则累计达 `Seen 3×`（或属严重回归），Router 当场指令 Worker 在返工时顺手将其固化为 `tests/` 下的静态架构守卫单测（Guard Test），在执行环内直接完成免疫闭环；
       3. **战略阻塞升级（`Status: blocked`）**：仅当遇到上游冻结的公共契约/核心层自相矛盾、需求存在业务价值二义性需人类取舍、或连续 3 轮战术修复仍未通过时，Router 才将完整阻塞证据写回对应 `[Task #N]` 区块（更新为 `Status: blocked`）并 `git commit` 退回给上游 Brain 裁决。
     - **精准认领、Verified-Commit 锚定与睡前排空循环（Claim & Drain-Loop）**：Router 取单时先将该区块改为 `Status: in_progress`（防重入），串联跑完 `Worker（开工前必读 LESSONS.md，在秒级内环完成代码与破壁自检并在业务 Commit Body 记录意图/根因与验证证据） → Tester 针对该业务 Commit 模拟真实用户终验（若打回则由 Router 记入 LESSONS.md 并调度 Worker 闭环修复） → Router 重读 HEAD/工作区 docs/TASKS.md 核对 [Task #N] 未被 Brain 改为 superseded → 仅用精确 edit 将该 [Task #N] 更新为 Status: verified，并将 Verified-Commit 精确填写为通过验收的那条业务代码 Commit SHA，再提交状态变更`；**提交后结束回合前，Router 必须再次检查 `docs/TASKS.md` 是否仍存在 `Status: pending` 任务区块**——若有则当场继续执行下一单，直至 `pending` 清零后再休眠。
   - *注：在无需跨宿主的简单单软件项目里，Brain 与 Router 可由同一个主会话兼任（退化为三节点）；一旦拆分为跨窗口/跨宿主双环，必须显式立住 Router 身份。*
3. **验证维度正交切分与首轮穷尽（Worker = 工程契约自检 + 手动破壁 vs. Tester = 模拟真实用户验收 & First-Pass Exhaustive）**：
   - **代码单测、手动破壁与全仓构建门禁归 Worker**：编译、类型检查、全仓单元测试、架构边界守卫（Guard Tests）、**手动破壁验证（`Broken by hand, each red`：手动破坏被测分支确认测试精准报红，杜绝恒真假测试与内部 Mock）**以及产物打包是 Worker 交卷前的**分内前置条件**。严禁把跑代码脚本、写单测或做进程/文件备份检查塞给 Tester。
   - **Tester 唯一定位是“模拟真实用户（Simulate the Real User）”且必须“首轮穷尽”**：具体怎么验证完全由**产品自身的交付形态**决定（CLI 工具就按用户手册敲真实命令看输出；API 服务就发真实请求验状态流转；GUI/网页/客户端应用就像不懂技术的真实人类用户一样在专用沙盒中点按交互、肉眼审视每一帧截图的排版、位置与文案）。Tester 必须在**第一轮验收时一次性穷尽该任务切面的全部交互体验、视觉排版与边界缺陷**（严禁“挤牙膏式”每轮只报 1 个毛病把 3 轮封顶额度耗光），绝不能只重跑一遍 Worker 的测试脚本看 `ok: true` 就放行。
4. **上下文当缓存管（Inline & Spill）与热节点复用**：
   - **Inline & Spill**：Brain 与 Router 只内联（Inline）任务 ID、结论摘要与文件路径锚点，完整细节与证据落盘（Spill）到工作区文件中按需索引。
   - **热节点复用（Warm Teammates）**：Router 在项目周期内持续复用已驻留的具名 Worker 与 Tester 子会话（实测 KV Prompt Cache 命中率可达 97%+），消除每次新建空白会话的冷启动重读税。

| 角色身份 | 所在环与交互对象 | 职责定位 | 模型选型倾向 | 严禁越界行为 |
| --- | --- | --- | --- | --- |
| **1. Brain**（宏观架构师） | **思考环**（唯一面对人类） | 承接人类模糊意图、冻结上游公共契约、向 `docs/TASKS.md` 追加/更新 `[Task #N] (Status: pending)` 并执行 `git commit --only docs/TASKS.md`、处理 `blocked` 战略冲突与最终审美终审 | **旗舰模型**（最懂人话、全局视野与审美最强） | 不亲自写具体业务代码、不覆盖正在执行的 `pending / in_progress` 任务区块、不把冗长工具日志灌入主窗口 |
| **2. Router**（无人值守战术总控与现场法官） | **执行环**（面对 Git Hook 与子代理） | 接收 `[AUTO-WAKEUP]` 信号、管理本仓 `.tmp/worktrees/task-<ID>` 生命周期并串联调度 Worker 与 Tester；**当 Tester 打回时，现场分诊显性问题、亲自将漏检模式写入 `docs/LESSONS.md`（满 `Seen 3×` 即令 Worker 固化为守卫单测）并直接拍板调度 Worker 闭环自愈**；仅在契约冲突或连败 3 轮时回写 `blocked`；睡前重读排空 `pending` 队列 | **次旗舰 / 强决断力编排模型** | **严禁在后台窗口停下向人类提问等回复**、严禁沦为无脑传话筒拿显性 Bug 打扰 Brain、严禁 10s 短超时早退、严禁覆写其他任务区块、不亲自下场写业务代码 |
| **3. Worker**（隔离实现与秒级工程内环） | **执行环**（面对 Router） | 开工前必读 `docs/LESSONS.md`；在主目录或分配的 `.tmp/worktrees/task-<ID>` 内实现完整垂直切面、**在秒级无头内环独立跑通全仓编译/类型/单测/架构守卫单测并完成手动破壁验证（`Broken by hand`）**；按 Router 战术指令修复缺陷或固化新增守卫单测 | **次旗舰 / 高执行力编码模型** | 不直接向人类抢话、不私改上游冻结契约、不写内部 Mock 或脱离真实环境的假单测、不给自己发最终合格证 |
| **4. Tester**（独立模拟用户终验外环） | **执行环**（面对 Router） | **根据产品形态完全模拟真实用户操作产品**（点界面看截图审美 / 跑真实用户旅程，首轮穷尽挑刺）+ 核对授权边界，向 Router 出具体验与行为验收报告 | **次旗舰 / 强工具与视觉模型** | **严禁替 Worker 写代码或写单测脚本**、严禁把跑代码脚本绿灯当成用户体验通过、不搞过度防御的备份/进程扫描、不碰用户真实生产数据 |

## 子 Agent 派发、并发配额与多 Worktree 生命周期协议

Brain / Router 调度 Worker 与 Tester 时，按**读写性质与 `Scope` 耦合边界**控制系统吞吐：

| 任务类型 | 合理并发数 | 硬性前提与拆分粒度 |
| --- | --- | --- |
| **局部微调 / 上游契约冻结** | **`0`（Fast Path）** | 仅限 ≤5 步工具调用的微调或上游共享契约（如 `schema` / `core` 接口）的冻结，由 Brain 直接完成；**一旦涉及完整业务切面实现或耗时测试，严禁自己硬干，必须下沉给执行环**。 |
| **单共享工作树直写（Worker）** | **`1`（零开销默认态）** | 当活跃队列仅有 1 项任务且主工作树空闲时，直接在主工作树原地执行（无需创建 Worktree），**同一工作树同一时刻只能有 `1` 个活跃写 Worker**。 |
| **流水线重叠或正交多轨道写（Worktree Workers）** | **`2 ~ 3`（封顶）** | 当 **① Tester 正在主工作树耗时验收上一单（Pipelining 流水线重叠）**，或 **② 队列中存在 2~3 项 `Scope`（写文件集）100% 物理正交且上游共享 Schema 已提前冻结的任务**时，Router 在本仓 `.tmp/worktrees/task-<ID>` 下开启隔离工作树并行派发 Worker。 |
| **只读探索 / 分诊聚类（Explore / Triage / Tester）** | **`2 ~ 4`（封顶）** | 海量外部 Issues/PR 分诊聚类、无写入冲突的跨子系统调研或多维度审查可并行扇出。 |

### 仓库内局部 Worktree（`<repo>/.tmp/worktrees/task-<ID>`）四步生命周期
为彻底隔离多项目（绝不使用全局共享临时目录，亦不污染仓库外层父目录），所有并发工作树统一建在**当前项目仓库内部的 `.tmp/worktrees/` 下**（`.tmp/` 列入 `.gitignore`），并由 **Router 独占管理开启与销毁**：
1. **按需开启（Spawn & Zero-Install Symlink）**：
   - Router 启动时先执行 `git worktree prune` 并清理已完成任务的残留目录；
   - 当触发流水线重叠或正交多任务并行时，Router 执行 `git worktree add -B task/<ID> .tmp/worktrees/task-<ID> HEAD`（若项目含 `node_modules` 或 `.venv`，直接软链复用主工作树依赖如 `ln -s ../../../node_modules .tmp/worktrees/task-<ID>/node_modules`，实现 1 秒零安装就绪）。
2. **隔离秒级内环开发（Isolated Build & Test）**：
   - Worker 进入 `.tmp/worktrees/task-<ID>` 编写代码、跑通秒级无头单测与守卫检查，并在该分支提交业务 Commit。
3. **变基快进合入主干（Rebase & Fast-Forward Merge）**：
   - Worker 交卷后，Router 在该 Worktree 内执行 `git rebase main`（若遇同目标冲突则令 Worker 在 Worktree 内解冲突并重跑单测），随后在主工作树执行 `git merge --ff-only task/<ID>` 将代码合入 `main`。
4. **即刻销毁零残留（Immediate Teardown）**：
   - 一旦合入 `main`（或该任务被 Brain 标为 `superseded` 作废），Router 立即执行 `git worktree remove --force .tmp/worktrees/task-<ID> && git branch -D task/<ID>`，确保 `.tmp/worktrees/` 内永远只存在当前正在活跃编码的 0~3 个目录。

## 标准双环四角色协作闭环

```text
👤 人（唯一交互入口：宏观目标与审美裁定）
  ↕
🧠 [Brain] 制定架构契约，向 docs/TASKS.md 追加/更新 ## [Task #N] (Status: pending, Scope: ...)
   并执行 git commit --only docs/TASKS.md（若推翻未完旧单则将其标为 Status: superseded）
  ↓  (.git/hooks/post-commit 发送 [AUTO-WAKEUP] 机器指令，2 秒内静默唤醒)
🧭 [Router] 无人值守战术总控与现场法官（多 Worktree 流水线调度 + 显性问题执行环自闭环 + 睡前排空 Drain-Loop）
  ├── 按序认领 Status: pending 的 [Task #N]（标为 in_progress；若主目录正忙于验收上一单或多单 Scope 正交，则开启 .tmp/worktrees/task-<N> 并行派发）
  ├── 派发 🔨 [Worker] 必读 LESSONS.md + 实现垂直切面 + 秒级无头内环跑通全仓单测与手动破壁验证（合入主干并销毁临时 Worktree）
  └── 唤醒 🔍 [Tester] 按产品形态模拟真实用户独立终验（操作真实产品界面/入口 + 视觉与体验首轮穷尽审视）
        ├── ✅ 全部通过 → Router 重读 TASKS.md 确认 #N 未被 superseded → 仅将 [Task #N] 更新为 Status: verified
        │     （附 Verified-Commit）并执行 git commit --only docs/TASKS.md
        │     └── 🔄 [Drain Check] 再次检查 TASKS.md 是否存在新追加的 Status: pending 区块？
        │           ├── 有 → 不退出回合，立即循环执行下一项 [Task #N+1]
        │           └── 无 → 队列排空，回合结束休眠
        ├── 🔧 显性实现/体验缺陷或同目标漏列支撑文件（执行环内部自愈闭环，不打扰 Brain）：
        │     ├── ① Router 比对“Worker 自检报告”与“Tester 翻车现场”，亲自将漏检模式写入/累加至 docs/LESSONS.md（Seen N×）
        │     └── ② Router 直接拍板扩权支撑文件、指出根因方向，安排 Worker 修复并补齐回归/守卫单测（满 Seen 3× 强制固化 Guard Test），重跑 Tester（上限 3 次）
        └── ⚠️ 核心契约冲突、需求二义性或连败 3 次 → Router 将证据写回 [Task #N] (Status: blocked) 并 git commit 退回 Brain
```

## 角色间通信契约（工具无关）

无论底层使用何种编排运行时，角色间交互必须通过以下结构化契约传递，拒绝口头模糊指令：

### 1. 任务包区块（Brain 写入 `docs/TASKS.md` → Router / Worker / Tester）
```markdown
## [Task #<N>] <任务名称>
- **Status**: pending
- **Scope**: `<允许修改的文件/目录前缀，供 Router 判定多 Worktree 正交并行>`
- **Verified-Commit**: none
- **Updated**: <YYYY-MM-DD>
- **授权范围**：允许修改的文件/目录，只读依赖的模块（若 Tester 发现完成本任务目标必须连带修改同切面支撑文件，Router 可直接授权补齐）
- **不在范围内**：明确排除的功能与严禁触碰的目录（如上游冻结契约或用户真实数据）
- **接口与行为契约**：输入、输出、边界条件、错误处理、性能要求
- **Worker 工程内环门禁（交卷前置条件）**：必须跑通的全仓测试套件、架构守卫单测、手动破壁验证与构建命令
- **Tester 模拟用户终验要求（按产品形态）**：真实用户视角下的操作路径、视觉排版/交互体验检查点与期望观测结果
```

### 2. 验收报告（Tester → Router）
```markdown
# 验收报告：[Task #<N>] <任务名称>
- **结论**：✅ 通过 | ❌ 实现或体验问题（退回 Worker） | ⚠️ 核心契约冲突（由 Router 标记 blocked 退回 Brain）
- **边界核对**：是否触碰未授权核心契约、Worker 全仓门禁与手动破壁验证是否已齐备
- **模拟真实用户验收证据**：按产品形态实际操作产品的过程、画面截图审视结论（排版/位置/文案/交互反馈）或真实输出记录
- **必须修复项**（若为实现/体验问题）：具体现象、违背的用户心智或契约条目、复现路径与对应文件位置
- **需升级裁定项**（若为核心契约问题）：契约冲突点或架构缺陷说明
```

### 3. 单文件滑动调度板与 `[AUTO-WAKEUP]` Git Hook 触发协议（`docs/TASKS.md`）
为实现跨宿主、Agent 无关的全自动触发，同时**解决“Router 正在执行 `#N` 期间 Brain 又提交了 `#N+1`，导致结案时误覆盖新任务或漏触发”的并发竞态**，`docs/TASKS.md` 采用**单文件滑动任务栈（In-File Task Queue）+ 多 Worktree 流水线 + 睡前排空自检（Drain-Loop）**协议：
- **独立区块状态（防 ABA 覆盖）**：每个任务拥有独立标题 `## [Task #N] <标题>` 与各自的状态行（`- **Status**: pending | in_progress | verified | blocked | superseded`）。Brain 追加新任务时只新增 `## [Task #N+1]`（严禁删改正在执行的 `#N`），Router 结案时仅用 `edit` 更新对应 `## [Task #N]` 下的状态行（严禁全文件盲目覆写）。
- **撤单语义（`Status: superseded`）**：若人类与 Brain 决定推翻正在执行或尚未执行的 `#N`，Brain 将 `[Task #N]` 状态改为 `superseded (by #N+1)` 并追加新区块 `[Task #N+1] (pending)`；Router 在结案前重读文件，若发现当前任务已变为 `superseded`，立即终止该任务验收（若在临时 Worktree 中则直接销毁该 Worktree）并转入 `#N+1`。
- **隔离提交（`git commit --only docs/TASKS.md`）**：Brain 提交任务单时必须加 `--only docs/TASKS.md`，防止将共享工作区内 Worker 改到一半的半成品代码误打包提交。
- **Commit Body 永久验证账本**：由于 `TASKS.md` 仅保留最近 1~2 个已结案区块，Worker 在提交业务代码时，在 Git Commit Body 中简明记录意图/根因与验证证据，确保 `TASKS.md` 滑动清理后依然可通过 `git log / git blame` 追溯。
- **睡前排空自检（Drain-Loop，防运行中漏触发）**：即使 Router 在运行期间因会话忙而错过了新提交的外部唤醒信号，Router 在将 `#N` 标记为 `verified` 并提交后、结束回合前，**必须重新读取 `docs/TASKS.md` 检查是否仍有 `Status: pending` 区块**，若有则当场继续执行直至彻底排空。

```bash
#!/usr/bin/env bash
# .git/hooks/post-commit（需在本地显式安装并赋予可执行权限；冷启动或异常中断后 Router 启动时亦须扫描 TASKS.md 恢复未结案任务）
# 读取本次已提交树对象 HEAD:docs/TASKS.md（而非可能处于半编辑态的工作区文件），唤醒失败时记录日志至 .git/router-wakeup.err
if git diff-tree --no-commit-id --name-only -r HEAD --root | grep -qx "docs/TASKS.md"; then
  if git show HEAD:docs/TASKS.md 2>/dev/null | grep -qE "^(- \*\*Status\*\*|Status): pending(\s|$)"; then
    <wake-router-command> "[AUTO-WAKEUP] 你是单消费者无人值守 Execution Router（执行环战术总控与现场法官，非人类交互窗口）。请按序认领 docs/TASKS.md 中 Status: pending 的 [Task #N]（标为 in_progress；若多任务 Scope 正交或主目录正忙于 Tester 验收，可开启 .tmp/worktrees/task-<N> 并行派发 Worker 并在单测通过后变基合回主干销毁 Worktree），持续等待并串联 Worker（必读 LESSONS.md，完成秒级内环自检与手动破壁验证）与独立 Tester 闭环；若 Tester 打回显性实现/体验问题或漏列同切面支撑文件，由你直接将漏检模式写入/累加至 docs/LESSONS.md（满 Seen 3× 令 Worker 顺手固化为 Guard Test）并拍板安排 Worker 修复自愈，绝不拿显性 Bug 打扰 Brain；通过后重读确认该单未被标为 superseded，将其更新为 Status: verified（Verified-Commit 填通过验收的业务代码 SHA）并 git commit --only docs/TASKS.md；睡前再次重读排空新增 pending 区块，严禁向人类提问等待回复。" 2>>.git/router-wakeup.err || echo "[post-commit] wake-router failed, see .git/router-wakeup.err" >&2
  fi
fi
```

## 升级路径与人的介入时机

升级链条固定为：`Worker ↔ Tester ↔ Router（显性问题执行环自闭环） → Brain → 人`。

- **Tester 打回显性实现/体验缺陷或 Worker 遇到同目标支撑文件漏列（不出执行环）**：由 **Router 当场裁决自愈**——Router 比对 Worker 自检与 Tester 翻车现场，亲自在 `docs/LESSONS.md` 记录/递增漏检模式（若累计达 `Seen 3×` 则安排 Worker 顺手写成 `tests/` 守卫单测），直接拍板授权补齐同切面支撑文件、指出根因方向并调度 Worker 重修 + Tester 复验。
- **Router 必须退回 Brain（标 `Status: blocked`）**：仅当需要修改上游已冻结的公共契约、需求存在业务价值二义性需人类取舍、涉及破坏性操作、或同一任务连续 3 轮战术自愈仍未通过 Tester 验收。
- **Brain 必须唤醒人**：需要改变项目对外目标/范围、多个技术方案存在业务价值取舍、或收到 `Status: blocked` 需人类做方向裁定。

## 验收清单

- [ ] 四重身份边界清晰：Brain 面向人类定契约，Router 担任执行环战术法官（管理 `.tmp/worktrees/` 并行轨道、现场分诊显性问题、执笔 `docs/LESSONS.md` 并调度执行环自愈闭环），Worker 串行或隔离 Worktree 实现并完成全仓代码/单测门禁与手动破壁验证，Tester 独立模拟真实用户验收
- [ ] `docs/TASKS.md` 采用 `## [Task #N]` 独立状态区块与 `Scope` 声明，Brain 使用 `git commit --only docs/TASKS.md` 隔离提交，Router 精准核销对应区块并在睡前重读排空全部 `pending` 任务（无覆盖、无漏触发、临时 Worktree 合入即销毁零残留）
- [ ] Router 收到 `[AUTO-WAKEUP]` 后未在后台窗口停下向人类提问等待，也未发生 10s 短超时早退
- [ ] 未发生同一共享工作树多子 Agent 并发写（同目录 Write=1；跨任务并行均通过本仓 `.tmp/worktrees/task-<ID>` 物理隔离）
- [ ] 代码单测与构建门禁已由 Worker 在秒级内环交卷前跑通；Tester 的最终放行依据来自符合产品形态的真实用户模拟操作与视觉/行为观测证据（而非仅重跑测试脚本看 `ok: true`）
- [ ] 角色定义与宿主工具、特定模型型号及具体调试框架解耦

---

深度参考：
- [references/rationale.md](references/rationale.md) — 为什么从三角色演进为双环四重身份（Brain · Router · Worker · Tester）的推导与实证
- [assets/roles.template.md](assets/roles.template.md) — 供目标项目按需实例化的极简 `docs/ROLES.md` 模板
