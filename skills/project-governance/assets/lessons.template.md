<!-- reviewed-through: <commit-sha> (<YYYY-MM-DD HH:mm +0800>) -->
# Lessons from Merged Work

<!-- 顶部注释记录最近一次复盘扫描到的 Commit 水位线，避免重复扫描或漏检。
     触发机制：平时一次通过的任务零开销；当独立 Tester（或人）打回交付（说明残次品逃过了 Worker 自检）时，由 Router 亲自比对 Worker 自检报告与 Tester 翻车现场，将漏检模式写入或累加至本文件。
     每条记录顺序固定为：一句话可执行规则（粗体）→ 为什么 → 真实翻车证据（Commit/Issue）→ Seen N× (<日期列表>)。
     当同一规则在不同日期累计 Seen 3×（或单次造成严重事故）时，Router 直接安排 Worker 将其固化为 tests/ 下的架构守卫单测（Guard Test）或移入正式规范，并从本文件正文移除（移入底部已晋升列表）。 -->

## Active Lessons

**<一句话可执行规则，直接写主语与必须满足的动作/禁止项>**
- <为什么需要这条规则：省略它会引发什么具体缺陷>
- <真实翻车证据：`<commit-sha>` / `#<issue>` 发生了什么，最后在 `<fix-sha>` 如何修复>
- Seen 1× (<YYYY-MM-DD>).

## Moved to Guard Tests / Standards

- **<已晋升的一句话规则>** → 已固化为守卫测试 `<test_file>:<test_name>`（或 `<目标文档#章节>`）。
