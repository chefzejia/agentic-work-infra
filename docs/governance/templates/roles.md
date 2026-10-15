# 角色定义

<!-- 本模板供多 Agent 协作项目实例化。
来源：agentic-work-infra/docs/governance/templates/roles.md
复制时注明源仓库、commit 和源文件路径，并删除本注释。
详细协作架构见 docs/governance/multi-agent-collab.md。
-->

本项目启用多 Agent 协作。当前活跃角色：

## Architect（主架构师）

- **会话名**：architect-main
- **职责**：
  - 理解业务目标、做架构决策
  - 制定模块边界、接口契约、交接计划
  - 维护 HANDOFF.md（当前状态、下一步、阻塞）
  - 制定任务包，分发给 Worker
  - 处理 Reviewer 升级的架构问题
- **只保留**：目标、边界、当前状态、关键决策
- **不做**：具体实现、代码审查、测试编写

## Worker（执行者）

- **会话名**：worker-<模块名>
  - 示例：worker-auth、worker-payment、worker-api
- **职责**：
  - 读取任务包：范围、契约、验收标准
  - 实现功能、写测试、自验证
  - 提交 PR 给 Reviewer
  - 根据 Reviewer 反馈修复问题
- **只关注**：当前任务的范围和契约
- **不做**：跨模块决策、架构调整、查看其他模块实现

## Reviewer（代码审查）

- **会话名**：reviewer-main
- **职责**：
  - 独立读取代码和契约
  - 检查：正确性、边界、测试、风险
  - 判断问题严重程度，决定是直接要求修复还是升级
  - 通过后标记为"可合并"
- **判断边界**：
  - 轻微问题（测试不足、风格、边界值）：直接告诉 Worker 修复
  - 严重问题（架构冲突、安全风险、连续三次失败）：升级给 Architect
- **不做**：自己修改代码、替 Worker 做决策、绕过 Architect 改架构

## 升级路径

```text
Worker 遇到问题
  ↓
能自己解决？是 → 直接修复
              否 → 提交给 Reviewer

Reviewer 审查
  ↓
轻微问题？是 → 告诉 Worker 修复
          否 → 升级给 Architect

Architect 判断
  ↓
架构调整？是 → 重新设计，更新任务包
          否 → 与人讨论

人裁决 → 做出最终决定
```

## 人的介入时机

**Architect 必须唤醒人**：
- 技术方案有多个选择，各有利弊
- 架构约束冲突
- 需要改变项目范围或优先级
- 预算、时间、风险判断

**Reviewer 必须唤醒人**：
- 安全或数据泄露风险
- Worker 连续 3 次未能通过审查
- 发现 Architect 的架构决策有根本问题

**Worker 基本不唤醒人**（通过 Reviewer 或 Architect 间接反馈）

## 接口约定

### 任务包格式（Architect → Worker）

见 HANDOFF.md 或任务 issue，必须包含：
- 范围（文件、接口、依赖）
- 契约（输入、输出、错误处理、性能）
- 验收标准（测试覆盖、安全检查）
- 不在范围内（明确排除的功能）

### 审查报告格式（Reviewer → Worker/Architect）

必须包含：
- 结论（通过 / 需要修复 / 需要升级）
- 必须修复（问题、位置、原因）
- 建议改进（非阻塞）
- 需要 Architect 裁定（架构问题）

### 状态交接格式（Architect 维护 HANDOFF.md）

必须包含：
- 当前状态（各模块进展）
- 下一步（任务分配）
- 阻塞（等待什么）
- 当前架构约束
