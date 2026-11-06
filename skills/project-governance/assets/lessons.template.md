<!-- reviewed-through: <commit-sha> (<YYYY-MM-DD HH:mm +0800>) -->
# Lessons from Merged Work

<!-- 顶部注释记录最近一次周期性逆熵审计（Auditor）扫描到的 Commit 水位线，避免重复扫描或漏检。
     双通道触发机制：
     1. 日常现场记账（Router）：当独立 Tester 打回交付（说明残次品逃过了 Worker 自检）时，由 Router 亲自比对 Worker 自检报告与 Tester 翻车现场，将漏检模式写入或累加至本文件（Seen N×）。
     2. 周期性逆熵铲屎（Fresh-Context Auditor）：当 docs/TASKS.md 无 pending 任务（空闲）且距 reviewed-through 已累积 >= 5 个非 docs/ 代码提交时，.git/hooks/post-commit 自动在后台拉起一次性全新冷会话 Auditor，按三大实证门槛审查区间代码 Diff、将 reviewed-through 推进至 HEAD，并将确有铁证的清创任务追加进 docs/TASKS.md。
     每条记录顺序固定为：一句话可执行规则（粗体）→ 为什么 → 真实翻车证据（Commit/Issue）→ Seen N× (<日期列表>)。
     当同一规则累计 Seen 3×（或单次造成严重事故）时，Router 直接安排 Worker 将其固化为 tests/ 下的架构守卫单测（Guard Test）或移入正式规范，并从本文件正文移除（移入底部已晋升列表）。 -->

## Active Lessons

**<一句话可执行规则，直接写主语与必须满足的动作/禁止项>**
- <为什么需要这条规则：省略它会引发什么具体缺陷>
- <真实翻车证据：`<commit-sha>` / `#<issue>` 发生了什么，最后在 `<fix-sha>` 如何修复>
- Seen 1× (<YYYY-MM-DD>).

## Moved to Guard Tests / Standards

- **<已晋升的一句话规则>** → 已固化为守卫测试 `<test_file>:<test_name>`（或 `<目标文档#章节>`）。
