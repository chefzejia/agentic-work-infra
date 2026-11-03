# 研究文档

本目录保存已完成的调研成果，每份文档都带事实核查时间。

## 多 Agent 协作

### 双环四重身份与去 Session 化工作流设计（最新实践）
**文件**：[dsh-native-agent-team-workflow.md](dsh-native-agent-team-workflow.md)
**事实核查**：2026-11-03（基于多波次迭代实测、Orca / Herdr / Codex Daemon / DSH Agent Teams 横向对比）

**核心结论**：
- **区分“状态去 Session 化”与“算力热驻留”**：项目的长期状态与契约必须落盘在工作区文件中（不锁死在聊天窗口），但执行多波次任务的 Router/Worker/Tester 节点应作为**常驻热队友（Warm Teammates）**持续复用，以保有 97%+ 的 KV Prompt Cache 命中率。
- **双环四重身份（Brain · Router · Worker · Tester）与 Git Hook 事件驱动**：人类只面对唯一的主窗口（Brain）定契约并提交 `HANDOFF.md (Status: pending)`，通过 8 行 `.git/hooks/post-commit` 秒级拍醒下游无人值守 Router 串联常驻 Worker 与独立 Tester 闭环。

---

### Worker Agent 与候选模型实测评估及指标体系全记录
**文件**：[worker-benchmark-2026-10-28.md](worker-benchmark-2026-10-28.md)  
**事实核查**：2026-10-28 ~ 2026-10-29（基于本机 Magpie Gateway 账单分析 + `obsidian_labs` 11 组隔离 Worktree 盲测，**仅针对本机指定的候选模型与宿主**）

**核心内容与结论**：
- **实验前置条件与效度威胁披露（学术级严谨性）**：完整盘点并量化了本机叠加条件对评测结果的潜在混杂影响——包括 **RTK（Rust Token Killer v0.99.0）** 在 `Codex CLI`/`Claude Code` 上的非对称注入（`PreToolUse` 输出降噪 + `@RTK.md` 的 *"batch related commands into one call"* 提示词引导）、**Magpie 内置插件栈**（`astrlink-guard` 本地 PII 脱敏延迟、不同 `baseAPI` 协议转译对 Prompt Cache 命中率的影响、`272K` 自动压缩阈值）以及 **Orca Hooks** 开销。
- **评测方法论**：拆解 `TTFT（首字延迟）`、`流速 (tok/s)` 与 `交互轮数 (N)` 的关系（$\text{总耗时} = N \times (\text{TTFT} + \text{输出耗时} + \text{工具耗时})$），解释为什么流速最快的 `deepseek-flash`（180 tok/s，19 轮碎步）在端到端耗时上略逊于少轮数高密度的 `Codex CLI`（7~8 轮大步）。
- **主力首选 Worker（细致度与性价比之王）**：`Codex CLI` + `sorrycode-gpt/gpt-6.1-terra` (**`effort=high`**) —— **79.6 秒完成**（8 轮调用，单任务 **$0.067**，TTFT 仅 **4.2s**），100% 严守范围，且**全场唯一**主动发现相邻模块 `ObsidianVaultHost.ts` 的跨宿主异常类型并做了兼容（`low` 会漏校验，`xhigh` 代码与 `high` 一字不差但慢 38s）。
- **并列极速 Worker（大模型降维快刀）**：`Codex CLI` + `sorrycode-gpt/gpt-6.1-sol` (**`effort=low` 或 `medium`**) —— **68.0 秒完成**（仅 7~8 轮调用，**$0.06–$0.12**），100% 严守任务包文件范围，遇到跨文件契约冲突精准上报行号。
- **极致经济 Worker**：`DSH` + `sorrycode-cn/deepseek-flash` —— **78.3 秒完成**，Prompt Cache 命中率 92%，单任务成本不到 **$0.01**。
- **Magpie 档位锁定排障**：记录了上游 `/v1/models?client_version=0.165.0` 将 `gpt-6.1-terra` 错误标记为 `effort: none` 导致 GUI/Codex 无法切换档位的根因与本地修复方案。

---

### 三角色协作设计
**文件**：[三角色协作设计.md](三角色协作设计.md)  
**事实核查**：2026-10-15（基于 Orca 官方推荐 + 第一性原理推导）

**设计原则**：
- 角色边界成立的唯一依据：合并它会产生一个**可以说出名字的具体失败**
- 能力差异不是拆分理由（同一强模型既能规划又能写码又能审查），信息差异才是
- 项目唯一 → 项目级上下文 = 架构上下文

**三角色分工**：
1. **Brain**（协调者 + 架构师，`brain`）：制定方案、契约、任务包、验收标准；协调 Worker/Tester；维护 HANDOFF.md 和 ARCHITECTURE.md；处理升级
2. **Worker**（实现者，`worker-<模块名>`）：实现代码 + 写单元测试 + 自验证
3. **Tester**（验收者，`tester`）：静态审查 + 动态验证（集成测试 / 直接部署生产验证）

**为什么是三个**：
- **Brain = Architect**：同一份上下文（项目目标、边界、当前状态、架构决策），同一类产物（决策和任务分配），拆开只增加一次"互相转述"的成本
- **Tester = Reviewer**：同一份上下文（契约 + 代码），同一个产物（通过/不通过）；代码审查和测试执行是同一验收流程的两个**阶段**，不是两个角色
- **Worker ≠ Tester**（唯一必须保留的边界）：作者给自己发合格证。Worker 的上下文里有"我为什么这么写"，这个信息本身让他看不见"这么写对不对"——信息差异，模型再强也溶解不掉

**工作流**：
```
用户需求 → [Brain] 制定方案和任务包
         → [Worker] 实现 + 单元测试 → worker_done
         → [Tester] 静态审查 + 动态验证
         → ✅ 通过：完成
         → ❌ 实现问题：Brain 重新启动 Worker（循环，上限 3 次）
         → ⚠️ 契约问题：Brain 自己重写契约（不新增角色，这是 Brain 的控制流）
```

**升级路径**：`Worker → Tester → Brain → 人`

**适配"直接上线部署调试"**：
- Tester 的动态验证 = 直接部署生产 → 验证关键路径 → 观察日志 5-10 分钟 → 异常即回滚
- 前提：静态审查必须先通过（不能盲目部署）

**实现方式**：
- 提供完整的 Brain 协调脚本（基于 Orca CLI v1.4.224 实测）
- 支持 `--model` 和 `--effort` 参数选择模型

---

### Orca 配置指南
**文件**：[orca-配置指南.md](orca-配置指南.md)  
**事实核查**：2026-10-15（官方文档 + 本机 CLI v1.4.224 实测）

**核心认知**：
- Orca **不是我们需要设计工作流的对象**，而是提供好底层能力的基础设施
- Agent 只需要遵从 Orca 的协作协议（调用对应的 CLI 命令），不需要编写自己的多 Agent 编排逻辑
- 两种协作模式都是 Orca 提供的底层设计，选择哪种取决于场景

**底层能力**：
1. **监督式编排**（Supervised Orchestration）
   - Coordinator 创建 Run/Task/Dispatch
   - Worker 通过 `orca orchestration send` 主动报告状态
   - Coordinator 通过 `orca orchestration check --wait` 阻塞等待消息
   - 适用于：需要 Brain 持续协调 Worker 和 Tester 的场景

2. **完全移交**（Full Handoff）
   - 启动 agent 后交出控制权，不再监督
   - Worker 独立完成任务，通过 git commit 或文件系统呈现结果
   - 适用于：Worker 可以独立完成任务，Brain 通过其他方式判断完成

**我们需要做什么**：
- 让 Agent 理解并执行 Orca 的协作协议（在 system prompt 或文档中说明）
- 选择合适的协作模式（监督式 vs 完全移交）
- 配置 Agent 账户和模型；本机 Codex CLI 的 SorryCode provider 已在 `~/.codex/config.toml` 中配置

**我们不需要做什么**：
- 不需要设计自己的任务生命周期管理
- 不需要实现消息队列和通信机制
- 不需要编写 worktree 管理逻辑

**架构层次**：
```
前端层 (CLI/GUI) → Runtime (daemon + orchestration.db) → Agent 进程
```
- CLI 和 GUI 操作同一套状态（orchestration.db）
- Runtime 通过 PTY 管理 agent 进程
- Agent 通过调用 `orca` 命令参与协作协议

**模型选择**：
- ✅ `worker-start` 现已支持 `--model` 和 `--effort` 参数（v1.4.224 实测确认）
- Orca 的 Codex `System default` 使用本机 `~/.codex`；受管 Codex account 会把其中的设置同步到独立 home
- `agentic-work-infra` 项目的 pane 当前选用哪个 account 尚未核实
- 示例模型 ID 应使用所选 agent/provider 实际支持的值；`--effort` 与 `--model` 一起传

**待核实**：
- Orca 运行后确认本项目 Codex pane 选用 `System default` 还是受管 account，并确认受管 account 的设置同步状态
- Claude Code 使用 SorryCode 时需按 Claude Code 自身的 provider 配置方式单独设置

---

### Herdr 深度调研
**文件**：[herdr-调研.md](herdr-调研.md)  
**事实核查**：2026-10-13（GitHub API + 官网实测）

**核心发现**：
- Herdr 是编码 Agent 的**运行时**（不是编排框架）
- 定位：让 Agent 能后台持久运行、断连重连、跨机器访问
- 与 LangGraph/CrewAI 不冲突，可作为底层运行时
- 唯一专门为"Claude Code 调用 Codex"场景设计的工具

**适用场景**：
- 需要 Agent 7×24 后台运行
- 多机器管理多个编码 Agent
- Agent 间需要持久化会话

---

## magpie 人机协同研究

### 九个深度问题的回答
**文件**：[magpie-九个深度问题.md](magpie-九个深度问题.md)  
**事实核查**：2026-10-13（GitHub API 实测）

**核心机制**：
1. **LESSONS.md** - 失败反馈机制，记录 Agent 重复失败的模式
2. **规则演化** - 出现 3 次晋升到 code-standards.md
3. **人机边界** - 每晚 review、提取模式、价值判断
4. **CI 门禁** - 机器裁判，红色不许发布

**我们的可用结论**：
- 立即建立 docs/LESSONS.md
- 验收标准必须可执行
- 区分"稳定原则"和"待验证规则"

### loop 模式研究
**文件**：[magpie-loop模式研究.md](magpie-loop模式研究.md)  
**来源**：作者推文 2026-10-10

**核心认知**：
- 放权成立的前提：CI 门禁 + 沉淀规则 + 事后介入
- 人的占比极小，但规则产出是系统收敛的来源
- 任务式 vs 常驻式：事前批准 vs 事后低频高杠杆介入

---

## 多 Agent 工具对比

| 工具 | 定位 | 适用场景 |
|------|------|----------|
| **Orca** | 桌面 ADE，并行 worktrees | GUI 工作流，可视化管理多 agents |
| **Herdr** | 终端运行时 | 后台持久化，CLI 工作流 |
| **LangGraph** | 编排框架（低层） | 复杂状态流转，需要精细控制 |
| **CrewAI** | 编排框架（高层） | 角色明确的多 Agent 团队 |
| **Claude Code Workflow** | 内置编排 | 官方原生，agent()/parallel()/pipeline() |

---

## 文档清理历史

**2026-10-15 清理**：
- 删除个人配置记录（agents 清单、magpie 配置）
- 删除已吸收的总结（多 Agent 协同与 ComputerUse）
- 删除 magpie 早期研究（人机协同研究、深度分析）
- 保留最终研究成果和独立价值文档

**清理原则**：
- 个人配置不是研究成果
- 已沉淀进 governance 的删除
- 中间产物被最终报告吸收后删除
- 保留有独立价值的调研报告
