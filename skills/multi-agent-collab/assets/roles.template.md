# 双环四角色协作契约（Brain · Router · Worker · Tester）

<!-- 仅当项目启用多 Agent 角色隔离协作时实例化为 docs/ROLES.md。删除注释与占位符后使用。 -->

角色拆分的唯一依据是**信息差异**（作者上下文包含“我为什么这么写”，自审必然退化为自我确认）与**交互对象差异**（人类交互窗口 vs 后台无人值守自动机）。

| 角色 | 所在环与交互对象 | 核心职责 | 严禁行为 |
| :--- | :--- | :--- | :--- |
| **1. Brain（宏观架构与人类入口）** | **思考环**（唯一面对人类） | 定义 `docs/` 契约、冻结上游公共接口、在 `docs/TASKS.md` 中追加/更新 `## [Task #N]`（置为 `- **Status**: pending` 并声明 `Scope`）且执行 `git commit --only docs/TASKS.md`、处理 `blocked` 战略冲突与最终审美终审 | 不绕过契约堆砌功能代码、不覆盖正在后台执行的 `pending / in_progress` 任务区块、不把 diff 塞进调度板 |
| **2. Router（无人值守战术总控与现场法官）** | **执行环**（由 Git Hook `[AUTO-WAKEUP]` 边沿触发） | 接收 `post-commit` 唤醒信号，管理本仓 `.tmp/worktrees/task-<ID>` 并按序/并行调度常驻 Worker 与独立 Tester（**严禁为 `in_progress` 单独执行 `git commit`**）；**当 Tester 打回时，现场分诊显性问题、亲自将漏检模式写入/累加至 `docs/LESSONS.md`（满 `Seen 3×` 令 Worker 顺手固化为 Guard Test）并直接拍板调度 Worker 自愈闭环**；通过后重读确认未被 `superseded`，将该 `[Task #N]` 更新为 `Status: verified`（附 `Verified-Commit`）并 `git commit --only docs/TASKS.md`，**睡前再次检查 `TASKS.md` 排空所有剩余 `pending` 任务区块** | **严禁在后台会话中停下向人类提问等待回复**；严禁为中间态 `in_progress` 提交 Git 触发钩子；严禁沦为无脑传话筒拿显性 Bug 打扰 Brain；严禁 10s 短超时早退；不亲自写业务代码 |
| **3. Worker（垂直切面实现与秒级工程内环）** | **执行环**（面对 Router） | 开工前必读 `docs/LESSONS.md`；在主目录或分配的 `.tmp/worktrees/task-<ID>` 内完成完整垂直切面、**在秒级无头内环编写并跑通全仓编译/类型检查/单元测试/架构守卫单测、手动破壁验证（`Broken by hand`）与构建同步（交卷前置条件）**，按 Router 战术指令修复缺陷或补齐守卫单测 | **同一工作树严格串行（Write=1）**；不私改上游冻结契约、不写内部 Mock 或脱离真实环境的假 UI 测试、不给自己发最终合格证 |
| **4. Tester（独立模拟真实用户终验外环）** | **执行环**（常驻热会话，面对 Router） | **根据产品形态完全模拟真实用户操作产品**（如 GUI 产品真实点按交互并截屏肉眼审视排版/位置/文案，CLI/API 产品执行真实用户调用链路，首轮穷尽挑刺）+ 核对修改边界，向 Router 出具验收报告 | **严禁替 Worker 写代码或写测试脚本**，不把代码脚本绿灯当成用户体验合格，不搞快照备份/进程扫描等防御内耗 |
| **5. Auditor（周期性逆熵铲屎官）** | **逆熵环**（**一次性全新冷会话 Fresh-Context**，水位线触发跑完即焚） | 当 `TASKS.md` 无 `pending`（空闲）且距 `LESSONS.md` 首行 `reviewed-through` 已累积 $\ge 5$ 个非文档代码提交时自动拉起：零历史包袱审查区间代码与测试 Diff；**按三大实证门槛（破壁不红实证 / 反模式行号实证 / 契约冲突实证）抓假单测、套娃补丁与契约漂移**；更新 `LESSONS.md` 水位线，确有铁证屎山时向 `TASKS.md` 追加 `[Task #Audit]` 清创单自动唤醒 Router 闭环 | **严禁复用旧会话上下文**；**无破壁/行号铁证严禁提主观代码风格建议（代替二次确认，零误报噪音）**；严禁绕过 `TASKS.md` 私自大改业务代码 |

## 无人值守执行环（Router）战术自闭环、多 Worktree 生命周期与升级铁律

1. **显性问题执行环 100% 自闭环，战略冲突才报 Brain**：`Router` 的触发源是自动化 Git Hook 而非人类聊天，遇到任何分支情况必须按以下两条确定性路径自动收敛，绝不在聊天框停下等人回复，也绝不拿显性 Bug 去打扰 `Brain`：
   - **路径 A（显性实现/体验缺陷与同切面支撑文件直接自愈 + 执笔 `LESSONS.md`）**：当独立 `Tester` 打回显性实现/体验问题，或发现完成本任务目标必须连带修改同切面的非核心支撑文件（且**未触碰任务包声明的【严禁触碰 / 不在范围内】红线**）时：
     1. **Router 亲自记账**：比对 Worker 自检报告与 Tester 翻车现场，将“为何该残次品逃过了 Worker 自检”写入或累加至 `docs/LESSONS.md (Seen N×)`；
     2. **Router 直接拍板**：动态授权 Worker 修改关联支撑文件、明确指出根因修复方向（若某条显性规则已达 `Seen 3×`，直接命令 Worker 在返工时顺手固化为 `tests/` 守卫单测），重跑 `Tester` 直至一鼓作气跑完 `Status: verified`；
   - **路径 B（核心契约冲突或战略二义性退回）**：仅当遇到真正的上游冻结接口自相矛盾、需求存在业务价值二义性需人类取舍、触及严禁修改红线或连续 3 轮战术自愈仍未通过 `Tester` 验收时，`Router` 才将精确阻塞证据写回对应 `## [Task #N]` 区块（状态改为 `- **Status**: blocked`）并执行 `git commit --only docs/TASKS.md` 退回给上游 `Brain`。
2. **单文件滑动调度板与睡前排空（防并发覆盖与漏触发）**：
   - **Brain 追加与撤单**：当后台仍有 `pending / in_progress` 任务在跑时，Brain 新建任务必须在 `docs/TASKS.md` 末尾追加 `## [Task #N+1]`（绝不覆盖在跑任务；若推翻未完旧单则将其标为 `superseded (by #N+1)`），且必须使用 `git commit --only docs/TASKS.md` 提交；文件内仅保留未结案区块及最近 1~2 个已结案区块。
   - **Router 精准核销与 Drain-Loop**：Router 结案时仅修改对应 `## [Task #N]` 的状态行；每次 `git commit` 后、结束回合前，**必须重读 `docs/TASKS.md` 检查是否仍有 `- **Status**: pending` 区块**——若有，立即在当前轮次继续执行下一单，直至全文件 `pending` 清零才休眠。
3. **仓库内 `.tmp/worktrees/task-<ID>` 并行与合入即销毁（Pipelining & Isolation）**：
   - 单任务且主目录空闲时直接在主工作树执行（同一工作树 Write = 1）；
   - 当 Tester 正在主工作树验收上一单（流水线重叠），或存在 2~3 个 `Scope` 100% 物理正交的 `pending` 任务时，Router 在本仓库 `.tmp/worktrees/task-<ID>` 下开启隔离 Git Worktree（`git worktree add -B task/<ID> .tmp/worktrees/task-<ID> HEAD`，软链复用 `node_modules/.venv`）派发 Worker 并行开发；Worker 内环单测全绿后由 Router 变基快进合回 `main`（`git rebase main && git merge --ff-only task/<ID>`），并**立即执行 `git worktree remove --force .tmp/worktrees/task-<ID> && git branch -D task/<ID>` 销毁临时目录**（启动时固定执行 `git worktree prune` 清扫孤儿目录）。
4. **双速回路：秒级工程内环归 Worker，模拟真实用户终验（首轮穷尽）归 Tester**：代码编译、毫秒/秒级无头单测与构建门禁由 `Worker` 在提交前 100% 跑通；`Tester` 只在项目已配置的专用沙盒环境（直接读写使用，无需额外做快照备份或隔离证明）中**按产品形态模拟真实人类用户操作与审视产物**，并在**第一轮验收时一次性穷尽该任务切面的全部功能、交互与视觉体验缺陷**（严禁挤牙膏式分轮报错耗光 3 轮额度）。
5. **周期性逆熵审计（Fresh-Context Auditor，水位线 = 5 个代码提交，实证免二次确认）**：当 `TASKS.md` 无 `pending` 且距 `LESSONS.md` 首行 `reviewed-through: <sha>` 已累积 $\ge 5$ 个非 `docs/` 代码提交时，`.git/hooks/post-commit` 自动在后台拉起一次性全新会话 `Auditor`；`Auditor` 仅在握有**手动破壁仍 PASS 的假单测实证、反模式源码行号实证、或违背 `ARCHITECTURE.md / PRODUCT.md` 的契约冲突实证**时，才向 `docs/TASKS.md` 追加 `[Task #Audit]` 清创任务（同时将 `reviewed-through` 推至 `HEAD`），自动交由 `Router -> Worker -> Tester` 闭环修复。
