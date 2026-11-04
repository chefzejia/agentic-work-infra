# Handoff Queue

<!-- 单文件滑动任务栈协议（Agent 无关 · Git Hook 驱动 · 防并发覆盖与漏触发）：
     1. 宏观 Brain 定稿任务后，以独立编号区块 `## [Task #<N>] <标题>` 写入本文件（标记 `- **Status**: pending`），并执行隔离提交 `git commit --only docs/HANDOFF.md`（防带入后台 Worker 半成品代码）。
     2. 若上一轮 `[Task #<N-1>]` 仍在后台执行（`Status: pending`），Brain 直接在末尾追加 `## [Task #<N>]`，严禁覆盖或删除正在执行的区块；若需推翻未完旧单，将其改为 `- **Status**: superseded (by #<N>)` 并追加新单。
     3. 文件内仅保留所有未结案区块（`pending / blocked`）+ 最近 1~2 个已结案区块（`verified / superseded`）作为近期锚点，更早的已结案区块在追加新单时顺手移出（历史由 `git log` 保存）。
     4. 仓库 .git/hooks/post-commit 检测到本次 commit 包含 docs/HANDOFF.md 且存在 `Status: pending` 区块时，秒级唤醒下游常驻 Router。
     5. 下游 Router 在同一唤醒周期内循环 wait_agent 串联完成 Worker 实现 + Tester 独立真机验收：每单通过后先重读确认未被标为 `superseded`，再仅将该 `[Task #<N>]` 区块更新为 `Status: verified`（附 `Verified-Commit`）并 git commit；提交后结束回合前必须再次检查本文件是否仍有新增的 `Status: pending` 区块（Drain-Loop），直至全部排空后再休眠。 -->

## [Task #<N>] <任务名称>

- **Status**: <pending | verified | blocked | superseded>
- **Verified-Commit**: <sha-or-none>
- **Updated**: <YYYY-MM-DD>

### 1. 目标与范围
- **授权修改范围**：<允许 Worker 修改的文件/模块列表>
- **严禁触碰范围**：<不在本轮范围内的模块、用户真实数据目录>

### 2. 任务包明细
1. **<具体改动项 1>**：`<filepath>:<line>` — <明确行为契约>
2. **<具体改动项 2>**：`<filepath>:<line>` — <明确行为契约>

### 3. 验收门禁（Worker 工程自检 vs. Tester 模拟真实用户验收）
- **Worker 工程自检门禁（交卷前置条件）**：`<Worker 必须跑通的类型检查、单元测试、架构守卫单测与构建命令，如 bash scripts/verify.sh>`
- **Tester 模拟用户验收要求（按产品形态）**：<Tester 如何像真实人类用户一样在专用沙盒中操作产品、需要截屏肉眼审视哪些界面排版/交互位置/文案细节，或执行哪些真实用户旅程；严禁仅跑脚本看退出码代替真实体验验收>
