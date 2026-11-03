# Handoff

Status: <pending | verified | blocked>
Verified-Commit: <sha-or-none>
Updated: <YYYY-MM-DD>

<!-- 极简事件钩子协议（Agent 无关 · Git Hook 驱动）：
     1. 宏观 Brain 定稿任务后将顶部 Status 设为 pending 并执行 git commit（未 commit 的工作区修改不触发下游）。
     2. 仓库 .git/hooks/post-commit 检测到本次 commit 包含 docs/HANDOFF.md 且为 Status: pending 时，秒级唤醒下游常驻执行主会话。
     3. 下游常驻执行主会话在同一唤醒周期内循环 wait_agent 串联完成 Worker 实现 + Tester 独立真机验收，通过后将 Status 更新为 verified（附 Verified-Commit）并 git commit（因状态已变为 verified，不会二次触发 Hook 死循环）。
     4. 严禁在本文件中堆砌已完成阶段的历史验收大表。 -->

## 本轮目标与范围

- **授权修改范围**：<允许 Worker 修改的文件/模块列表>
- **严禁触碰范围**：<不在本轮范围内的模块、用户真实数据目录>

## 任务包明细

1. **<具体改动项 1>**：`<filepath>:<line>` — <明确行为契约>
2. **<具体改动项 2>**：`<filepath>:<line>` — <明确行为契约>

## 验收门禁（Worker 自检 + Tester 独立真机复验）

- **静态与单测门禁**：`<精确验证命令，如 bash scripts/verify.sh>`
- **动态/真机验收要求**：<Playwright / 原生桌面 CUA 必测路径；所有临时验证产物必须放入 `.gitignore` 已覆盖的固定沙盒目录如 `.tmp/` 或 `.dev-vault/`，严禁污染仓库根目录或宿主全局列表>
