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
2. **双环四重身份契约（宿主无关）与默认 Git 参考实现（`HANDOFF.md + post-commit`）**：
   - **第一环：宏观思考环（人 $\leftrightarrow$ Thinking Brain）**：人类唯一面对的沟通入口（选用旗舰模型），专注需求碰撞、产品审美与架构决策；定稿后将任务契约以独立编号区块 `## [Task #N] <标题>`（区块内标记 `Status: pending`）写入仓库 `docs/HANDOFF.md`，并执行隔离提交 `git commit --only docs/HANDOFF.md`（严禁把后台 Worker 正在修改的半成品代码误打包进提交）：
     - **追加排队（In-File Queue）**：若上一轮 `[Task #N-1]` 仍处于 `Status: pending / in_progress`（后台正在执行），Brain **绝不覆盖或删除 `#N-1`**，直接在文件末尾追加 `## [Task #N]`（`Status: pending`）；
     - **推翻旧单（Supersede）**：若需推翻尚未跑完的 `#N-1`，Brain 将 `## [Task #N-1]` 的状态改为 `Status: superseded (by #N)`，并在下方追加新方案 `## [Task #N]`（`Status: pending`）；
     - **滑动自净（Sliding Window GC）**：文件内仅保留所有未结案区块（`pending / in_progress / blocked`）及最近 `1 ~ 2` 个已结案区块（`verified / superseded`）作为上下文锚点，更早的已结案区块在追加新单时顺手移出（完整历史由 `git log` 保存）。
   - **第二环：无人值守执行环（单消费者 Router $\rightarrow$ Worker & Tester）**：
     - 在默认的 Git 事件驱动实现中，本地安装 `.git/hooks/post-commit` 监听**已提交树（`HEAD:docs/HANDOFF.md`）**中存在 `Status: pending` 的任务区块，向**唯一常驻的 Execution Router（单消费者 Single-Consumer）**发送 `[AUTO-WAKEUP]` 机器指令（若宿主不支持常驻会话，也可退化为单次无状态调度器，启动时扫描未结案的 `pending / in_progress` 区块恢复执行）；
     - **Router 无人值守与显式委托边界（严禁在后台会话向人类提问等待）**：Router 的触发源是自动化钩子而非人类聊天，**绝对禁止在后台会话里停下来向人类提问等待回复**！**仅当任务包显式勾选/声明允许同切面支撑文件微调、且目标文件未触碰【不在范围内 / 严禁触碰】黑名单时**，Router 才可在任务目标范围内授权 Worker 补齐关联支撑文件并重跑 Tester；若任务包锁定了严格文件白名单、或遇到跨核心（`core/`）契约冲突、或连续 3 轮修复未过，Router 必须将阻塞证据写回对应 `[Task #N]` 区块（更新为 `Status: blocked`）并 `git commit` 退回给上游 Brain。
     - **精准认领、Verified-Commit 锚定与睡前排空循环（Claim & Drain-Loop）**：Router 取单时先将该区块改为 `Status: in_progress`（防重入），串联跑完 `Worker 实现代码提交（产出业务代码 Commit，其 Commit Body 完整记录 Why/Cause & Change、Tests、Broken by hand、Run、Not tried） → Tester 针对该业务 Commit 模拟真实用户验收 → Router 重读 HEAD/工作区 docs/HANDOFF.md 核对 [Task #N] 未被 Brain 改为 superseded → 仅用精确 edit 将该 [Task #N] 更新为 Status: verified，并将 Verified-Commit 精确填写为通过验收的那条业务代码 Commit SHA，再提交状态变更`；**提交后结束回合前，Router 必须再次检查 `docs/HANDOFF.md` 是否仍存在 `Status: pending` 任务区块**——若有则当场继续执行下一单，直至 `pending` 清零后再休眠。
   - *注：在无需跨宿主的简单单软件项目里，Brain 与 Router 可由同一个主会话兼任（退化为三节点）；一旦拆分为跨窗口/跨宿主双环，必须显式立住 Router 身份。*
3. **验证维度正交切分与首轮穷尽（Worker = 工程契约自检 + 手动破壁 vs. Tester = 模拟真实用户验收 & First-Pass Exhaustive）**：
   - **代码单测、手动破壁与全仓构建门禁归 Worker**：编译、类型检查、全仓单元测试、架构边界守卫（Guard Tests）、**手动破壁验证（`Broken by hand, each red`：手动破坏被测分支确认测试精准报红，杜绝恒真假测试与内部 Mock）**以及产物打包是 Worker 交卷前的**分内前置条件**。严禁把跑代码脚本、写单测或做进程/文件备份检查塞给 Tester。
   - **Tester 唯一定位是“模拟真实用户（Simulate the Real User）”且必须“首轮穷尽”**：具体怎么验证完全由**产品自身的交付形态**决定（CLI 工具就按用户手册敲真实命令看输出；API 服务就发真实请求验状态流转；GUI/网页/客户端应用就像不懂技术的真实人类用户一样在专用沙盒中点按交互、肉眼审视每一帧截图的排版、位置与文案）。Tester 必须在**第一轮验收时一次性穷尽该任务切面的全部交互体验、视觉排版与边界缺陷**（严禁“挤牙膏式”每轮只报 1 个毛病把 3 轮封顶额度耗光），绝不能只重跑一遍 Worker 的测试脚本看 `ok: true` 就放行。
4. **上下文当缓存管（Inline & Spill）与热节点复用**：
   - **Inline & Spill**：Brain 与 Router 只内联（Inline）任务 ID、结论摘要与文件路径锚点，完整细节与证据落盘（Spill）到工作区文件中按需索引。
   - **热节点复用（Warm Teammates）**：Router 在项目周期内持续复用已驻留的具名 Worker 与 Tester 子会话（实测 KV Prompt Cache 命中率可达 97%+），消除每次新建空白会话的冷启动重读税。

| 角色身份 | 所在环与交互对象 | 职责定位 | 模型选型倾向 | 严禁越界行为 |
| --- | --- | --- | --- | --- |
| **1. Brain**（宏观架构师） | **思考环**（唯一面对人类） | 承接人类模糊意图、冻结上游 `core/` 契约、向 `HANDOFF.md` 追加/更新 `[Task #N] (Status: pending)` 并执行 `git commit --only docs/HANDOFF.md`、最终审美把关 | **旗舰模型**（最懂人话、全局视野与审美最强） | 不亲自写具体业务代码、不覆盖正在执行的 `pending` 任务区块、不把冗长工具日志灌入主窗口 |
| **2. Router**（无人值守执行总控） | **执行环**（面对 Git Hook 与子代理） | 接收 `[AUTO-WAKEUP]` 信号、持续等待并串联调度常驻 Worker 与 Tester、精准回写对应 `[Task #N]` 的 `Status: verified / blocked`、**在 Commit Body 中固化完整验证与破壁账本**、**睡前重读 `HANDOFF.md` 排空后续 `pending` 队列** | **次旗舰 / 高稳定性编排模型** | **严禁在后台窗口停下向人类提问等回复**、严禁 10s 短超时早退、严禁覆写其他任务区块、不亲自下场写业务代码 |
| **3. Worker**（隔离实现与工程自检层） | **执行环**（面对 Router） | 按任务包实现完整垂直切面、**独立跑通全仓编译/类型/单测/构建门禁并完成手动破壁验证（`Broken by hand, each red`）**、按 Tester 反馈修复 | **次旗舰 / 高执行力编码模型** | 不直接向人类抢话、不私改 `core/` 冻结契约、不写内部 Mock 或脱离真实环境的假单测、不给自己发最终合格证 |
| **4. Tester**（独立模拟用户验收层） | **执行环**（面对 Router） | **根据产品形态完全模拟真实用户操作产品**（点界面看截图审美 / 跑真实用户旅程）+ 核对授权边界，向 Router 出具体验与行为验收报告 | **次旗舰 / 强工具与视觉模型** | **严禁替 Worker 写代码或写单测脚本**、严禁把跑代码脚本绿灯当成用户体验通过、不搞过度防御的备份/进程扫描、不碰用户真实生产数据 |

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
🧠 [Brain] 制定架构契约，向 docs/HANDOFF.md 追加/更新 ## [Task #N] (Status: pending)
   并执行 git commit --only docs/HANDOFF.md（若推翻未完旧单则将其标为 Status: superseded）
  ↓  (.git/hooks/post-commit 发送 [AUTO-WAKEUP] 机器指令，2 秒内静默唤醒)
🧭 [Router] 无人值守执行总控（单轮持续阻塞等待 + 睡前排空循环 Drain-Loop，绝不停下向人提问）
  ├── 按序取出一项 Status: pending 的 [Task #N]
  ├── 派发 🔨 [Worker] 实现垂直切面 + 跑通全仓工程自检与手动破壁验证（Broken by hand, each red）
  └── 唤醒 🔍 [Tester] 按产品形态模拟真实用户独立验收（操作真实产品界面/入口 + 视觉与体验首轮穷尽审视）
        ├── ✅ 全部通过 → Router 重读 HANDOFF.md 确认 #N 未被 superseded → 仅将 [Task #N] 更新为 Status: verified
        │     并执行 git commit（Commit Body 写入 Cause & Fix / Tests / Broken by hand / Run / Not tried）
        │     └── 🔄 [Drain Check] 再次检查 HANDOFF.md 是否存在新追加的 Status: pending 区块？
        │           ├── 有 → 不退出回合，立即循环执行下一项 [Task #N+1]
        │           └── 无 → 队列排空，回合结束休眠
        ├── 🔧 实现/体验缺陷或同目标漏列支撑文件 → Router 直接授权 Worker 修复/补齐并重跑 Tester（上限 3 次）
        └── ⚠️ 核心契约冲突或连败 3 次 → Router 将证据写回 [Task #N] (Status: blocked) 并 git commit 退回 Brain
```

## 角色间通信契约（工具无关）

无论底层使用何种编排运行时，角色间交互必须通过以下结构化契约传递，拒绝口头模糊指令：

### 1. 任务包区块（Brain 写入 `docs/HANDOFF.md` → Router / Worker / Tester）
```markdown
## [Task #<N>] <任务名称>
- **Status**: pending
- **Verified-Commit**: none
- **Updated**: <YYYY-MM-DD>
- **授权范围**：允许修改的文件/目录，只读依赖的模块（若 Tester 发现完成本任务目标必须连带修改同切面支撑文件，Router 可直接授权补齐）
- **不在范围内**：明确排除的功能与严禁触碰的目录（如 `src/core/` 冻结接口或用户真实数据）
- **接口与行为契约**：输入、输出、边界条件、错误处理、性能要求
- **Worker 工程自检门禁（交卷前置条件）**：必须跑通的全仓测试套件、架构守卫单测、手动破壁验证（`Broken by hand, each red`）与构建命令
- **Tester 模拟用户验收要求（按产品形态）**：真实用户视角下的操作路径、视觉排版/交互体验检查点与期望观测结果
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

### 3. 单文件滑动任务栈与 `[AUTO-WAKEUP]` Git Hook 触发协议（`docs/HANDOFF.md`）
为实现跨宿主、Agent 无关的全自动触发，同时**解决“Router 正在执行 `#N` 期间 Brain 又提交了 `#N+1`，导致结案时误覆盖新任务或漏触发”的并发竞态**，`docs/HANDOFF.md` 采用**单文件滑动任务栈（In-File Task Queue）+ Commit Body 永久账本 + 睡前排空自检（Drain-Loop）**协议：
- **独立区块状态（防 ABA 覆盖）**：每个任务拥有独立标题 `## [Task #N] <标题>` 与各自的状态行（`- **Status**: pending | verified | blocked | superseded`）。Brain 追加新任务时只新增 `## [Task #N+1]`（严禁删改正在执行的 `#N`），Router 结案时仅用 `edit` 更新对应 `## [Task #N]` 下的状态行（严禁全文件盲目覆写）。
- **撤单语义（`Status: superseded`）**：若人类与 Brain 决定推翻正在执行或尚未执行的 `#N`，Brain 将 `[Task #N]` 状态改为 `superseded (by #N+1)` 并追加新区块 `[Task #N+1] (pending)`；Router 在结案前重读文件，若发现当前任务已变为 `superseded`，立即终止该任务验收并转入 `#N+1`。
- **隔离提交（`git commit --only docs/HANDOFF.md`）**：Brain 提交任务单时必须加 `--only docs/HANDOFF.md`，防止将共享工作区内 Worker 改到一半的半成品代码误打包提交。
- **Commit Body 永久验证账本**：由于 `HANDOFF.md` 仅保留最近 1~2 个已结案区块，Worker 或 Router 在提交代码/结案时，必须在 Git Commit Body 中完整记录 `Cause & Fix / Tests / Broken by hand, each red / Run / Not tried`，确保 `HANDOFF.md` 滑动清理后依然可通过 `git log / git blame` 追溯全部验证证据。
- **睡前排空自检（Drain-Loop，防运行中漏触发）**：即使 Router 在运行期间因会话忙而错过了新提交的外部唤醒信号，Router 在将 `#N` 标记为 `verified` 并提交后、结束回合前，**必须重新读取 `docs/HANDOFF.md` 检查是否仍有 `Status: pending` 区块**，若有则当场继续执行直至彻底排空。

```bash
#!/usr/bin/env bash
# .git/hooks/post-commit（需在本地显式安装并赋予可执行权限；冷启动或异常中断后 Router 启动时亦须扫描 HANDOFF.md 恢复未结案任务）
# 读取本次已提交树对象 HEAD:docs/HANDOFF.md（而非可能处于半编辑态的工作区文件），唤醒失败时记录日志至 .git/router-wakeup.err
if git diff-tree --no-commit-id --name-only -r HEAD --root | grep -qx "docs/HANDOFF.md"; then
  if git show HEAD:docs/HANDOFF.md 2>/dev/null | grep -qE "^(- \*\*Status\*\*|Status): pending(\s|$)"; then
    <wake-router-command> "[AUTO-WAKEUP] 你是单消费者无人值守 Execution Router（非人类交互窗口）。请按序认领 docs/HANDOFF.md 中 Status: pending 的 [Task #N]（标为 in_progress），持续等待并串联 Worker（提交业务代码并在 Commit Body 写入 Why/Cause & Change、Tests、Broken by hand、Run、Not tried）与独立 Tester 闭环；通过后重读确认该单未被标为 superseded，将其更新为 Status: verified（Verified-Commit 填通过验收的业务代码 SHA）并 git commit --only docs/HANDOFF.md；睡前再次重读排空新增 pending 区块，严禁向人类提问等待回复。" 2>>.git/router-wakeup.err || echo "[post-commit] wake-router failed, see .git/router-wakeup.err" >&2
  fi
fi
```

## 升级路径与人的介入时机

升级链条固定为：`Worker ↔ Tester ↔ Router → Brain → 人`。

- **Worker 遇到同目标文件漏列或实现报错**：上报 Router；若属任务目标直接关联的非核心支撑文件，由 **Router 直接拍板授权补齐**并重跑 Tester。
- **Router 必须退回 Brain（标 `Status: blocked`）**：需要修改上游已冻结的 `core/` 公共契约、涉及破坏性操作、或同一任务连续 3 轮未通过 Tester 验收。
- **Brain 必须唤醒人**：需要改变项目对外目标/范围、多个技术方案存在业务价值取舍、或收到 `Status: blocked` 需人类做方向裁定。

## 验收清单

- [ ] 四重身份边界清晰：Brain 面向人类定契约，Router 无人值守管闭环，Worker 串行实现并完成全仓代码/单测门禁与手动破壁验证（`Broken by hand, each red`），Tester 独立模拟真实用户验收
- [ ] `docs/HANDOFF.md` 采用 `## [Task #N]` 独立状态区块队列，Brain 使用 `git commit --only docs/HANDOFF.md` 隔离提交，Router 精准核销对应区块、在 Commit Body 中留存完整验证账本，并在睡前重读排空全部 `pending` 任务（无覆盖、无漏触发）
- [ ] Router 收到 `[AUTO-WAKEUP]` 后未在后台窗口停下向人类提问等待，也未发生 10s 短超时早退
- [ ] 未发生共享工作区多子 Agent 并发写（Write=1），未将同一垂直切面拆成零碎小任务并发派发
- [ ] 代码单测与构建门禁已由 Worker 在交卷前跑通；Tester 的最终放行依据来自符合产品形态的真实用户模拟操作与视觉/行为观测证据（而非仅重跑测试脚本看 `ok: true`）
- [ ] 角色定义与宿主工具、特定模型型号及具体调试框架解耦

---

深度参考：
- [references/rationale.md](references/rationale.md) — 为什么从三角色演进为双环四重身份（Brain · Router · Worker · Tester）的推导与实证
- [assets/roles.template.md](assets/roles.template.md) — 供目标项目按需实例化的极简 `docs/ROLES.md` 模板
