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
     - **追加排队（In-File Queue）**：若上一轮 `[Task #N-1]` 仍处于 `Status: pending`（后台正在执行），Brain **绝不覆盖或删除 `#N-1`**，直接在文件末尾追加 `## [Task #N]`（`Status: pending`）；
     - **推翻旧单（Supersede）**：若需推翻尚未跑完的 `#N-1`，Brain 将 `## [Task #N-1]` 的状态改为 `Status: superseded (by #N)`，并在下方追加新方案 `## [Task #N]`（`Status: pending`）；
     - **滑动自净（Sliding Window GC）**：文件内仅保留所有未结案区块（`pending / blocked`）及最近 `1 ~ 2` 个已结案区块（`verified / superseded`）作为上下文锚点，更早的已结案区块在追加新单时顺手移出（完整历史由 `git log` 保存）。
   - **第二环：无人值守执行环（战术总控 Router $\rightarrow$ Worker & Tester，显性问题 100% 自闭环）**：
     - **边沿触发防自激递归（Diff Edge-Trigger Only）**：`.git/hooks/post-commit` **仅检测本次 Commit 的 Diff 新增行是否引入了 `+\s*(- \*\*Status\*\*|Status): pending`**（而非检查全文件是否残留 `pending`）！这样只有当上游 Brain 新派发 `pending` 任务时才会触发唤醒；当 Router 在多任务队列中结案 `#N`（将 `#N` 从 `pending` 改为 `verified / blocked`）并提交时，即使文件内 `#N+1` 仍是 `pending`，因本次 Diff 并未新增 `pending` 行，钩子 100% 静默忽略，**从物理上彻底根绝“Router 提交 `TASKS.md` 自己再次唤醒自己”的无限递归**！
     - **Router 是有决断力的现场战术法官（而非无脑传话筒）**：Router 的触发源是自动化钩子而非人类聊天，**绝对禁止在后台会话里停下来向人类提问等待回复**！当 Tester 打回或 Worker 受阻时，Router 必须当场执行**分诊、记账与战术自愈（显性问题不出执行环，战略冲突才报 Brain）**：
       1. **现场分诊与战术决断**：凡属**显性工程/体验问题**（实现漏项、交互/排版瑕疵、测试逃逸，或完成任务目标所需的同切面支撑文件漏列且未触碰【不在范围内 / 严禁触碰】黑名单），**一律由 Router 在执行环内直接拍板解决**——动态授权支撑文件、明确指出根因修复方向（若 Worker 连续 2 轮在同一症状打表层补丁，Router 必须介入止损并重定根因重构方案），绝不拿显性 Bug 打扰上游 Brain；
       2. **执笔 `docs/LESSONS.md` 与 `Seen 3×` 守卫自进化**：只要发生 Tester 打回（说明残次品逃过了 Worker 的自检门禁），**由同时握有“Worker 自检报告”与“Tester 翻车现场”的 Router 亲自在 `docs/LESSONS.md` 中新增或累加该漏检模式（`Seen N×`）**；若某条显性工程规则累计达 `Seen 3×`（或属严重回归），Router 当场指令 Worker 在返工时顺手将其固化为 `tests/` 下的静态架构守卫单测（Guard Test），在执行环内直接完成免疫闭环；
       3. **战略阻塞升级（`Status: blocked`）**：仅当遇到上游冻结的公共契约/核心层自相矛盾、需求存在业务价值二义性需人类取舍、或连续 3 轮战术修复仍未通过时，Router 才将完整阻塞证据写回对应 `[Task #N]` 区块（更新为 `Status: blocked`）并 `git commit --only docs/TASKS.md` 退回给上游 Brain 裁决。
     - **零中间态提交、Verified-Commit 锚定与睡前排空循环（No Intermediate Claim Commits & Drain-Loop）**：Router 是唯一单消费者，**严禁在取单时为了改 `in_progress` 而执行 `git commit`（避免制造垃圾提交与触发钩子）**！Router 直接按序串联跑完 `Worker（开工前必读 LESSONS.md，在秒级内环完成代码与破壁自检并在业务 Commit Body 记录意图/根因与验证证据） → Tester 针对该业务 Commit 模拟真实用户终验（若打回则由 Router 记入 LESSONS.md 并调度 Worker 闭环修复） → Router 重读 docs/TASKS.md 核对 [Task #N] 未被 Brain 改为 superseded → 仅用精确 edit 将该 [Task #N] 更新为 Status: verified（Verified-Commit 填通过验收的业务代码 SHA）并执行 git commit --only docs/TASKS.md`；**提交后结束回合前，Router 必须再次检查 `docs/TASKS.md` 是否仍存在 `Status: pending` 任务区块**——若有则直接在当前轮次继续执行下一单，直至全文件 `pending` 清零后再休眠。
   - *注：在无需跨宿主的简单单软件项目里，Brain 与 Router 可由同一个主会话兼任（退化为三节点）；一旦拆分为跨窗口/跨宿主双环，必须显式立住 Router 身份。*
3. **验证维度正交切分与首轮穷尽（Worker = 工程自检 + 手动破壁 + UI 自拍看镜子 vs. Tester = 模拟真实用户终验 & First-Pass Exhaustive）**：
   - **代码单测、手动破壁、构建门禁与 UI 自拍看镜子归 Worker**：编译、类型检查、全仓单元测试、架构边界守卫（Guard Tests）、**手动破壁验证（`Broken by hand, each red`）**以及产物打包是 Worker 交卷前的**分内前置条件**；且凡涉及前端/客户端 UI 修改，Worker 交卷前必须**自己截 1~3 张改动后的真实界面图存入 `.tmp/evidence/task-<N>/` 并调用 `read_image / view_image` 亲眼检查一遍**（当场顺手修掉按钮重复、文字遮挡、位置错位等单测盲区，大幅降低打回率）。
   - **Tester 唯一定位是“模拟真实用户（Simulate the Real User）”且必须“首轮穷尽 + 归档视觉证据”**：具体怎么验证完全由**产品自身的交付形态**决定（CLI 工具就按用户手册敲真实命令看输出；API 服务就发真实请求验状态流转；GUI/网页/客户端应用就像不懂技术的真实人类用户一样在专用沙盒中点按交互、肉眼审视每一帧截图的排版、位置与文案）。Tester 必须在**第一轮验收时一次性穷尽该任务切面的全部交互体验、视觉排版与边界缺陷**（严禁“挤牙膏式”每轮只报 1 个毛病把 3 轮封顶额度耗光），并将最终通过验收的截图证据保留在 `.tmp/evidence/task-<N>/` 供人类一秒审美终审。
4. **上下文当缓存管（Inline & Spill）与热节点复用**：
   - **Inline & Spill**：Brain 与 Router 只内联（Inline）任务 ID、结论摘要与文件路径锚点，完整细节与证据落盘（Spill）到工作区文件中按需索引。
   - **热节点复用（Warm Teammates）**：Router 在项目周期内持续复用已驻留的具名 Worker 与 Tester 子会话（实测 KV Prompt Cache 命中率可达 97%+），消除每次新建空白会话的冷启动重读税。

| 角色身份 | 所在环与交互对象 | 职责定位 | 模型选型倾向 | 严禁越界行为 |
| --- | --- | --- | --- | --- |
| **1. Brain**（宏观架构师） | **思考环**（唯一面对人类） | 承接人类模糊意图、冻结上游公共契约、向 `docs/TASKS.md` 追加/更新 `[Task #N] (Status: pending)` 并执行 `git commit --only docs/TASKS.md`、处理 `blocked` 战略冲突与最终审美终审 | **旗舰模型**（最懂人话、全局视野与审美最强） | 不亲自写具体业务代码、不覆盖正在执行的 `pending` 任务区块、不把冗长工具日志灌入主窗口 |
| **2. Router**（无人值守战术总控与现场法官） | **执行环**（常驻热会话，面对 Git Hook 与子代理） | 接收 `[AUTO-WAKEUP]` 信号、管理本仓 `.tmp/worktrees/task-<ID>` 生命周期并串联调度 Worker 与 Tester；**当 Tester 打回时，现场分诊显性问题、亲自将漏检模式写入 `docs/LESSONS.md`（满 `Seen 3×` 即令 Worker 固化为守卫单测）并直接拍板调度 Worker 闭环自愈**；仅在契约冲突或连败 3 轮时回写 `blocked`；睡前重读排空 `pending` 队列 | **次旗舰 / 强决断力编排模型** | **严禁在后台窗口停下向人类提问等回复**、严禁为 `in_progress` 单独提交 Git、严禁沦为无脑传话筒拿显性 Bug 打扰 Brain、严禁 10s 短超时早退、不亲自下场写业务代码 |
| **3. Worker**（隔离实现与秒级工程内环） | **执行环**（常驻热会话，面对 Router） | 开工前必读 `docs/LESSONS.md`；在主目录或分配的 `.tmp/worktrees/task-<ID>` 内实现完整垂直切面、**在秒级无头内环独立跑通全仓编译/类型/单测/架构守卫单测并完成手动破壁验证（`Broken by hand`）；涉及 UI 改动时交卷前必截屏存入 `.tmp/evidence/task-<ID>/` 并亲自 `read_image` 审视自检** | **次旗舰 / 高执行力编码模型** | 不直接向人类抢话、不私改上游冻结契约、不写内部 Mock 或脱离真实环境的假单测、不给自己发最终合格证 |
| **4. Tester**（独立模拟用户终验外环） | **执行环**（常驻热会话，面对 Router） | **根据产品形态完全模拟真实用户操作产品**（点界面看截图审美 / 跑真实用户旅程，首轮穷尽挑刺，将终验截图归档至 `.tmp/evidence/task-<ID>/`）+ 核对授权边界，向 Router 出具体验与行为验收报告 | **次旗舰 / 强工具与视觉模型** | **严禁替 Worker 写代码或写单测脚本**、严禁把跑代码脚本绿灯当成用户体验通过、不搞过度防御的备份/进程扫描、不碰用户真实生产数据 |
| **5. Auditor**（周期性逆熵铲屎官） | **执行环内按需派生**（**一次性全新冷子代理 Fresh-Context Subagent**，由 Router 在睡前触发，跑完即关） | 当 `TASKS.md` 所有 `pending` 任务排空、准备休眠前，Router 检查距 `LESSONS.md` 首行 `reviewed-through` 是否已累积 $\ge 5$ 个非文档代码提交：若达标，**由 Router 直接派生一个零历史包袱的全新 `Auditor` 子代理**审查区间 `git log -p`；**以三大实证门槛（破壁不红实证 / 反模式行号实证 / 契约冲突实证）抓假单测、套娃补丁与契约漂移**；若抓到铁证屎山，Router 当场调度 Worker 修复 + Tester 复验，全部干净后由 Router 将 `LESSONS.md` 的 `reviewed-through` 更新为最新 `HEAD` 并提交 | **旗舰 / 高审美与强代码洁癖模型** | **严禁在 `post-commit` 里用 `nohup` 另起场外进程抢锁**；**严禁复用旧会话上下文**；**无破壁/行号铁证严禁提主观代码风格建议（零误报噪音）** |

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
  ↓  (.git/hooks/post-commit 仅当本次 Commit Diff 新增了 "+...Status: pending" 行时触发，杜绝 Router 自激递归)
🧭 [Router] 无人值守战术总控与现场法官（多 Worktree 流水线调度 + 显性问题执行环自闭环 + 睡前排空 Drain-Loop）
  ├── 按序取出一项 Status: pending 的 [Task #N]（严禁为 in_progress 单独执行 git commit；若主目录正忙于验收上一单或多单 Scope 正交，则开启 .tmp/worktrees/task-<N> 并行派发）
  ├── 派发 🔨 [Worker] 必读 LESSONS.md + 实现垂直切面 + 秒级无头内环跑通全仓单测与手动破壁验证（合入主干并销毁临时 Worktree）
  └── 唤醒 🔍 [Tester] 按产品形态模拟真实用户独立终验（操作真实产品界面/入口 + 视觉与体验首轮穷尽审视）
        ├── ✅ 全部通过 → Router 重读 TASKS.md 确认 #N 未被 superseded → 仅将 [Task #N] 更新为 Status: verified
        │     （附 Verified-Commit）并执行 git commit --only docs/TASKS.md（因 Diff 无新增 pending，不会二次触发 Hook！）
        │     └── 🔄 [Drain & Anti-Entropy Check] 再次检查 TASKS.md 是否存在尚未执行的 Status: pending 区块？
        │           ├── 有 → 不退出回合，立即循环执行下一项 [Task #N+1]
        │           └── 无（队列已排空）→ 检查距 LESSONS.md 首行 reviewed-through 是否已累积 >= 5 个非 docs/ 代码提交？
        │                 ├── 是 → Router 当场派生一次性全新子代理 🧹 [Fresh Auditor] 审查区间代码与单测（三大实证门槛）
        │                 │       → 若有实证屎山则当场令 Worker 清创 + Tester 复验 → 将 reviewed-through 推进至最新 HEAD 提交后休眠
        │                 └── 否 → 直接结束回合安心休眠
        ├── 🔧 显性实现/体验缺陷或同目标漏列支撑文件（执行环内部自愈闭环，不打扰 Brain）：
        │     ├── ① Router 比对“Worker 自检报告”与“Tester 翻车现场”，亲自将漏检模式写入/累加至 docs/LESSONS.md（Seen N×）
        │     └── ② Router 直接拍板扩权支撑文件、指出根因方向，安排 Worker 修复并补齐回归/守卫单测（满 Seen 3× 强制固化 Guard Test），重跑 Tester（上限 3 次）
        └── ⚠️ 核心契约冲突、需求二义性或连败 3 次 → Router 将证据写回 [Task #N] (Status: blocked) 并 git commit --only docs/TASKS.md 退回 Brain
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

### 3. 极简 8 行 `[AUTO-WAKEUP]` 边沿触发协议与 Router 内部睡前逆熵审计（告别场外 `nohup` 与锁竞争）
为实现跨宿主（如 `DSH Brain + ChatGPT App Router`）、每个项目独立常驻会话的全自动闭环，同时**彻底消灭场外 `nohup` 进程的 CLI 兼容故障与 `.git/auditor.lock` 并发踩踏**：
- **一项目一独立常驻 Router（严禁跨项目混用 UUID，严禁 Brain 调 `wait_agent` 阻塞人类窗口）**：每个独立项目必须在执行环宿主（如 ChatGPT App）中拥有**归属于该项目自身根目录的专属常驻 `Router` 顶层会话**，将其 `THREAD_ID` 填入该项目的 `.git/hooks/post-commit`；上游 `Brain` 永远只通过写 `docs/TASKS.md` + `git commit --only docs/TASKS.md` 单向异步派单（0.1 秒立即返回继续陪人类聊天）。
- **极简 8 行边沿触发 Hook**：`.git/hooks/post-commit` **只做唯一一件事**——当本次 Commit 的 Diff 新增行（`+`）中出现了 `Status: pending` 时，拍醒本项目的专属 `Router`。不再在 Hook 中运行任何场外 `nohup` 或目录锁脚本！
- **Router 睡前派生一次性全新 `Auditor` 子代理（三大实证门槛）**：
  - 当 `Router` 排空全部 `pending` 任务准备休眠前，自行检查 `git rev-list --count <reviewed-through>..HEAD -- . ":!docs/"` 是否 $\ge 5$；
  - 若 $\ge 5$，`Router` 直接利用宿主原生的子代理能力**新建一个零历史包袱的一次性空白子代理 `Auditor`**（审完即关，不复用 `Worker/Tester` 上下文），按**三大实证门槛**（① 手动破壁仍 PASS 的假单测实证、② 套娃/sleep/抠源码假测试行号实证、③ 违背架构契约实证；无实证严禁提主观风格建议）审查该区间；
  - 若 `Auditor` 抓出实证屎山，`Router` 当场在当前回合内调度 `Worker` 清创 + `Tester` 复验，最后将 `docs/LESSONS.md` 首行的 `reviewed-through` 更新为最新 `HEAD` 并提交，干净休眠！

```bash
#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# 极简边沿触发：仅当本次 commit 在 docs/TASKS.md 的 diff 中【新增】了 Status: pending 行时，唤醒【本项目专属】的常驻 Router
if git diff-tree --no-commit-id -p HEAD --root -- docs/TASKS.md 2>/dev/null | grep -qE "^\+(- \*\*Status\*\*|Status): pending(\s|$)"; then
  <wake-project-router-command> "[AUTO-WAKEUP] 你是本项目无人值守 Execution Router（详见 docs/ROLES.md）。请按序执行 docs/TASKS.md 中所有 Status: pending 的 [Task #N]（严禁为 in_progress 单独提交 Git；支持 .tmp/worktrees/task-<N> 正交并行），串联常驻 Worker（必读 LESSONS.md，完成秒级内环自检、手动破壁与 UI 自拍看图自检）与独立 Tester（模拟真实用户终验并归档证据至 .tmp/evidence/task-<N>/）；显性缺陷由你记入 LESSONS.md 并当场拍板令 Worker 自愈；每单通过后更新为 Status: verified 并执行 git commit --only docs/TASKS.md。全部 pending 排空后准备休眠前，检查距 LESSONS.md 首行 reviewed-through 若已累积 >= 5 个非 docs/ 代码提交，必须派生一次性全新空白子代理 Auditor 按三大实证门槛审查区间代码，如有实证屎山当场令 Worker 清创 + Tester 复验，最后更新 reviewed-through 至最新 HEAD 提交后休眠。" 2>>.git/router-wakeup.err || echo "[post-commit] wake-router failed, see .git/router-wakeup.err" >&2
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
