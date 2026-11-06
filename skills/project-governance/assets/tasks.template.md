# Tasks Queue

<!-- 单文件滑动任务调度板协议（Agent 无关 · Git Hook 驱动 · 支持多 Worktree 并行与流水线重叠）：
     1. 两级分诊漏斗：海量外部 Issues/PR 在仓外去重聚类，仅近期确认立项执行的活跃任务写入本文件。
     2. 宏观 Brain 定稿任务后，以独立编号区块 `## [Task #<N>] <标题>` 写入本文件（标记 `- **Status**: pending` 与 `- **Scope**: <写文件/目录集>`），并执行隔离提交 `git commit --only docs/TASKS.md`（防带入后台 Worker 半成品代码）。
     3. 若上一轮 `[Task #<N-1>]` 仍在后台执行（`Status: pending`），Brain 直接在末尾追加 `## [Task #<N>]`，严禁覆盖或删除正在执行的区块；若需推翻未完旧单，将其改为 `- **Status**: superseded (by #<N>)` 并追加新单。
     4. 文件内仅保留所有未结案区块（`pending / blocked`）+ 最近 1~2 个已结案区块（`verified / superseded`）作为近期锚点，更早的已结案区块在追加新单时顺手移出（历史由 `git log` 保存）。
     5. 仓库 .git/hooks/post-commit 采用 Diff 边沿触发（`git diff-tree -p HEAD -- docs/TASKS.md | grep "^\+.*Status.*: pending"`）：仅当本次 commit 【新增】了 `Status: pending` 行时才唤醒下游 Router；Router 严禁为 `in_progress` 单独提交 Git，结案提交 `verified / blocked` 时因未新增 `pending` 行，绝不会发生自激递归。
     6. 下游 Router 按 Scope 正交性与当前主目录空闲状态调度执行：
        - 单任务且主目录空闲：直接在主工作树执行；
        - 当 Tester 正在主目录耗时验收 `#<N-1>`，或存在 2~3 个 Scope 100% 物理正交的 `pending` 任务时：Router 在本仓库 `.tmp/worktrees/task-<N>/` 下创建隔离 Git Worktree（`git worktree add -B task/<N> .tmp/worktrees/task-<N> HEAD`，软链复用 `node_modules/.venv`）并行派发 Worker 开发，Worker 跑通秒级内环单测后由 Router 变基快进合回主分支（`git rebase main && git merge --ff-only`）并立即销毁该 Worktree（`git worktree remove --force`）。
     7. 每单经独立 Tester 模拟真实用户终验通过后，Router 重读确认未被标为 `superseded`，仅将该 `[Task #<N>]` 区块更新为 `Status: verified`（附 `Verified-Commit`）并执行 `git commit --only docs/TASKS.md`；提交后结束回合前必须再次检查本文件是否仍有新增的 `Status: pending` 区块（Drain-Loop），直至全部排空后再休眠。 -->

## [Task #<N>] <任务名称>

- **Status**: <pending | in_progress | verified | blocked | superseded>
- **Scope**: `<允许修改的文件/模块前缀，供 Router 判定多 Worktree 正交并行>`
- **Verified-Commit**: <sha-or-none>
- **Updated**: <YYYY-MM-DD>

### 1. 目标与边界
- **授权修改范围**：<允许 Worker 修改的文件/模块列表>
- **严禁触碰范围**：<不在本轮范围内的冻结核心契约或用户真实数据目录>

### 2. 任务包明细
1. **<具体改动项 1>**：`<filepath>` — <明确行为契约>
2. **<具体改动项 2>**：`<filepath>` — <明确行为契约>

### 3. 双速验收门禁（Worker 秒级工程内环 + UI 自拍自检 vs. Tester 模拟真实用户外环）
- **Worker 工程内环与 UI 自拍门禁（交卷前置条件）**：`<Worker 必须跑通的全仓测试套件、架构守卫单测、手动破壁验证与构建命令；若涉及 UI 改动，交卷前必须截 1~3 张真实渲染图存入 .tmp/evidence/task-<N>/ 并调用 read_image 亲眼审视自检>`
- **Tester 模拟用户终验要求（按产品形态，首轮穷尽 + 归档证据）**：<Tester 如何像真实人类用户一样在专用沙盒（如 `.tmp/`）中操作产品、需要截屏肉眼审视哪些界面排版/交互位置/文案细节（终验截图归档至 `.tmp/evidence/task-<N>/` 供人一秒审美终审）；严禁仅跑脚本看退出码代替真实体验验收>
