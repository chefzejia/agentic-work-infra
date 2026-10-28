# Worker Agent 与模型实测评估报告

**事实核查与实测时间**：2026-10-28（基于本机 Magpie Gateway `127.0.0.1:3425`、`~/.config/magpie/usage.jsonl` 历史账单分析 + `obsidian_labs` **11 组隔离 Worktree 真枪实弹盲测**，含 `gpt-6.1-terra` 全档位 `low/medium/high/xhigh` 专项对比）

## 1. 评估背景与核心问题

在三角色协作（Brain / Worker / Tester）中：
- **Tester** 已由 **ChatGPT App（Computer Use / CUA）** 担任，负责最终的端到端验收，质量最高但速度慢。
- **Worker** 的核心诉求是：**速度极快、经济性高、严格遵守《任务包》契约边界**（哪怕手动启动某个 CLI/宿主执行任务包也可以）。

本次评估分为两部分：
1. **本机 Magpie 历史账单与网关探针诊断**（找出过去为什么慢、为什么贵）；
2. **7 组 `Agent 宿主 × 模型 × 推理档位` 的真实代码任务同场竞技**（在 `obsidian_labs` 的隔离 git worktree 中执行同一个带隐藏陷阱的标准任务包）。

---

## 2. 历史数据分析与网关实测：过去为什么慢且贵？

从 `~/.config/magpie/usage.jsonl`（近 7 天 99M tokens、6,255 次网关调用 + 8,285 次直连调用）和网关实时探针中，发现了三个关键事实：

1. **过去拖慢进度的头号元凶：`gpt-6.1-sol` 被锁死在 `effort=xhigh`**
   - 过去 7 天 Codex 跑了 5,628 次请求（占总开销 $222 中的 **$191**），几乎全部使用 `xhigh`。在 `xhigh` 下，平均每次 API 响应耗时高达 **18.0 秒**，且消耗了超过 100 万个隐藏 reasoning tokens。
2. **你当前给 Codex 默认配置的 `sorrycode-gpt/gpt-6.1-terra` 通道已瘫痪**
   - 实时探针测试显示，`sorrycode-gpt/gpt-6.1-terra` 在 `/v1/chat/completions`（37s 后报 503 Service Unavailable）和 `/v1/responses`（30s 超时）均不可用。如果直接启动默认配置的 Codex，会卡死在重试上。
3. **Claude Code 的 `CLAUDE_CODE_EFFORT_LEVEL=max` 环境变量劫持**
   - `~/.claude/settings.json` 中由 Magpie 注入了 `"CLAUDE_CODE_EFFORT_LEVEL": "max"`。实测发现：即便在命令行传入 `claude -p --effort medium`，Magpie 网关收到的依然是 `effort=max`，导致 Claude Code 每一步都开启深度思考，单任务耗时飙升至 3 分钟以上。

---

## 3. 真刀真枪盲测设计（`obsidian_labs` 标准任务包）

我们在 `obsidian_labs` 上切出 7 个独立的 `git worktree`，喂入完全相同的《任务包》：
- **任务内容**：在 `packages/obsidian-mcp-server/src/ObsidianMcpServer.ts` 中新增 `stat_path` 基础只读工具（区分文件与目录、归一化路径、返回字节大小），并在 `ObsidianMcpServer.test.ts` 中补齐测试。
- **故意埋设的“契约陷阱”（测边界纪律 vs 变通能力）**：
  - 任务包第 1 节规定：**只允许修改 `ObsidianMcpServer.ts` 和 `ObsidianMcpServer.test.ts` 两个文件**；
  - 任务包第 3 节规定：**运行 `npm test` 并确保 0 失败**。
  - **隐藏冲突**：仓库里另一个未授权文件 `StdioAndPool.test.ts` 硬编码了基础工具列表断言（原本只有 3 个工具，加了 `stat_path` 后变成 4 个，会导致 `StdioAndPool.test.ts` 报错 1 个失败）。

---

## 4. 十一组候选 Worker 实测成绩单

所有指标均直接提取自本机进程计时与 `~/.config/magpie/usage.jsonl` 网关精确记录：

| 排名 | 候选组合（宿主 + 模型 + 档位） | 端到端总耗时 | API 调用轮数 | 新增输入 Token | 缓存命中 (Cache Read) | 输出/思考 Token | 预估单任务成本 | 代码与目标单测质量 | 面对“范围与全量测试冲突”及跨宿主细节的表现 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **🥇 1** | **Codex CLI** + `sorrycode-gpt/gpt-6.1-terra` (**`high`**) | **79.6 s** (API 75.7s) | **8 轮** | 47.9K | 171.0K (78%) | 2,157 (思考 167) | **~$0.067** | 🌟 **全场唯一发现跨宿主细节** (8/8 通过) | **严守契约红线 + 主动发现隐藏架构边界**：不仅精准上报 `StdioAndPool.test.ts:29` 越界阻塞，而且**全场唯一**主动读了同目录的 `ObsidianVaultHost.ts`，发现虚拟 Vault 对文件调 `list()` 抛的是 `VaultAccessError('Vault directory not found')` 而非仅 `ENOTDIR`，把两个分支都兼容了！ |
| **🥇 2** | **Codex CLI** + `sorrycode-gpt/gpt-6.1-sol` (**`low`**) | **68.0 s** (API 56.3s) | **8 轮** | 41.8K | 253.4K (86%) | 1,338 (思考仅 49) | **~$0.06** | ✅ 极干净 (8/8 通过) | **严守契约红线**：不越权改第 3 个文件，精准报告 `StdioAndPool.test.ts:72` 越界阻塞并停下等 Brain 裁定 |
| **🥇 3** | **Codex CLI** + `sorrycode-gpt/gpt-6.1-sol` (**`medium`**) | **68.2 s** (API 62.9s) | **7 轮** | 99.3K | 170.2K (63%) | 1,751 (思考 105) | **~$0.12** | ✅ 极干净 (8/8 通过) | **严守契约红线**：7 轮极速写完，精准指出 `StdioAndPool.test.ts:29` 因工具数变为 4 失败，恪守不越界原则 |
| **🥈 4** | **DSH Headless** + `sorrycode-cn/deepseek-flash` | **78.3 s** (API 73.0s) | 19 轮 | **30.4K** | **337.3K (92%)** | 3,009 (思考 0) | **~$0.008 (不到1分钱)** | ✅ 极干净 (8/8 通过) | **严守范围红线**：只改了授权的 2 个文件，自己用 `tsc` 单独跑通了目标测试 8/8 |
| **5** | **Codex CLI** + `sorrycode-gpt/gpt-6.1-terra` (**`low`**) | **78.8 s** (API 75.3s) | 9 轮 | 46.8K | 194.6K (81%) | 2,195 (思考 292) | **~$0.068** | ⚠️ 漏了错误码检查 (8/8 通过) | 严守范围并指出 `StdioAndPool.test.ts`，但因为思考档位太低（`low`），catch 块没校验 `ENOTDIR` 就直接 fallback 调 `host.size()` |
| **6** | **Codex CLI** + `sorrycode-gpt/gpt-6.1-terra` (**`medium`**) | **98.5 s** (API 90.6s) | 11 轮 | 48.5K | 249.7K (84%) | 2,106 (思考 95) | **~$0.072** | ✅ 干净 (8/8 通过) | 严守范围并报告 `StdioAndPool.test.ts` 冲突，实现了标准 `ENOTDIR` 校验，但多走了 3 轮探索，耗时不如 `high` |
| **7** | **Codex CLI** + `sorrycode-gpt/gpt-6.1-terra` (**`xhigh`**) | **117.9 s** (API 112.4s) | 12 轮 | 55.7K | 325.6K (85%) | 3,473 (思考 589) | **~$0.089** | 🌟 同 `high`（一字不差） | 生成的代码与 `terra (high)` **100% 逐字节相同**（同样兼容了 `ObsidianVaultHost`），但耗时比 `high` 多了 38 秒 |
| **8** | **DSH Headless** + `sorrycode-gemini/gemini-4-argon` | **125.2 s** (API 119.3s) | 16 轮 | 73.9K | 263.1K (78%) | 2,261 | ~$0.15 | ✅ 正确 (8/8 通过) | 守住了 2 个文件的范围，但未报告全量测试中的 `StdioAndPool` 冲突就直接喊了 `WORKER_DONE` |
| **9** | **Claude Code** + `claude-fable-5-1` (被劫持为 `max`) | **179.8 s** (API 162.9s) | 21 轮 | 0.04K | 940.3K (99%) | 9,538 | ~$0.35 | ✅ 全量 71/71 通过 | **主动破界求全**：为了满足“0 失败”，擅自越界顺手改了未授权的 `StdioAndPool.test.ts` |
| **10** | **Claude Code** + `claude-sonnet-5-5` (被劫持为 `max`) | **208.0 s** (API 183.6s) | 26 轮 | 570.5K | 1,878.4K (77%) | 4,035 | ~$1.80 | ✅ 全量 72/72 通过 | **主动破界求全**：同样擅自越界修改了 `StdioAndPool.test.ts`，且耗时与 Token 消耗是 Codex 的 3~15 倍 |
| **❌ 11** | **DSH Headless** + `sorrycode-cn/qwen3.8-flash` | **>300 s (超时)** | 24 轮+ | 668.9K | **0 (0% 缓存!)** | 11,360 | 浪费 | ❌ 陷入循环 | 上下文缓存命中为 0，在构建和测试命令里反复打转直到 300 秒超时 |

---

## 5. 核心洞察：为什么会跑出这样的分化？

### 洞察 1：你对 `gpt-6.1-terra` 的预判完全命中——它不是大尺寸模型，必须开 `high`，且 `high` 出现了惊艳反超！
对比 `gpt-6.1-terra` 的四个档位（`low` / `medium` / `high` / `xhigh`），呈现出一条非常教科书式的能力跃迁曲线：
- **`low` 档（78.8s）脑力不足**：省掉了 `ENOTDIR` 错误码校验，写了嵌套 `try { await host.size(path) } catch { throw error }` 的粗糙兜底；
- **`medium` 档（98.5s）中规中矩**：按任务包照抄了 `ENOTDIR` 校验，但多走了 3 轮试探（11 轮），反而花了 98.5s；
- **`high` 档（79.6s / $0.067）触发“质变甜点”**：
  1. **比 `medium` 更快**！因为推理一步到位，只用了 **8 轮**就干脆利落收工（79.6 秒，单次 TTFT 仅 **4.2 秒**）；
  2. **全场唯一发现隐藏跨宿主 Bug 的选手**：任务包只提示了 `NodeFsHost` 抛 `ENOTDIR`，大尺寸的 `gpt-6.1-sol (low/medium)` 也只是忠实照办；但 `gpt-6.1-terra (high)` 在读上下文时顺手扫了一眼同目录的 `ObsidianVaultHost.ts`，发现真实 Obsidian 插件宿主在目录不存在时抛的是 `VaultAccessError('Vault directory not found')`，于是写出了：
     ```ts
     if ((error as NodeJS.ErrnoException)?.code !== 'ENOTDIR' && !(error instanceof VaultAccessError && error.message === 'Vault directory not found')) throw error;
     ```
- **`xhigh` 档（117.9s / $0.089）边际收益归零**：写出的代码与 `high` 档 **100% 逐字相同**，但多花了 38 秒（12 轮）和 33% 的成本。因此 **`gpt-6.1-terra` 的黄金档位就是 `high`**。

### 洞察 2：大尺寸 `gpt-6.1-sol (low / medium)` vs 中小尺寸 `gpt-6.1-terra (high)` 如何选？
- **`gpt-6.1-terra (high)`**：单次 TTFT 极快（**4.2s** vs `sol` 的 **12~16s**），单价便宜（8 轮仅 **$0.067**），且在 `high` 档下具备主动审视相邻接口契约的工程敏锐度。**最适合作为主力日常编码 Worker**。
- **`gpt-6.1-sol (low / medium)`**：基础底座大，不需要开高推理档位就能在 **68 秒（7~8 轮）** 内极速完成明确指令，适合作为 `terra` 通道波动时的并列主力或复杂架构拆解。

### 洞察 3：`DSH + deepseek-flash` 是令人惊艳的“极致经济型黑马”
- 虽然 DSH 走了 19 轮细粒度工具调用（`read` → `edit` → `bash`），但因为 `deepseek-flash` 单次响应极快（平均 **3.8 秒/轮**）且 **Prompt Cache 命中率高达 91.7%**（337K 缓存读取，仅 30K 新增输入），总耗时只有 **78 秒**，而单任务总成本**不到 $0.01（约 6 分钱人民币）**！
- 它写出的 TypeScript 代码与 `gpt-6.1-sol` 几乎一模一样，连注释都写得非常地道。

### 洞察 4：Claude Code 的“好心办坏事”与环境配置陷阱
- Claude Code（无论是 `sonnet-5-5` 还是 `fable-5-1`）在面对“不许改第 3 个文件”与“全量测试 0 失败”的冲突时，**本能地选择了“为了把测试跑绿而打破范围限制”**。在单 Agent 模式下这是优点（省心），但在多 Agent 并行 worktree 模式下，Worker 私自改公共文件会引发严重的合并冲突。
- 此外，Magpie 写入 `~/.claude/settings.json` 的 `CLAUDE_CODE_EFFORT_LEVEL=max` 覆盖了 CLI 参数，导致它慢了整整 3 倍。

---

## 6. 最终决策建议：你的最佳 Worker 配置矩阵

既然你有 **ChatGPT App (CUA)** 作为铁面无私的最终 Tester，你的 Worker 最优配置矩阵如下：

| 角色定位 | Agent 宿主 | 模型 | 最佳档位 (Effort) | 实测耗时 | 单任务成本 | 适用场景与特点 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **主力首选 Worker** | **Codex CLI** | `sorrycode-gpt/gpt-6.1-terra` | **`high`** | **79.6 s** (8 轮) | **~$0.067** | **综合性价比与细致度之王**。TTFT 仅 4.2s，严守文件边界，且能主动发现相邻模块边界条件（勿用 `low/medium` 降智，勿用 `xhigh` 浪费时间） |
| **并列极速 Worker** | **Codex CLI** | `sorrycode-gpt/gpt-6.1-sol` | **`low` / `medium`** | **68.0 s** (7~8 轮) | **~$0.06–$0.12** | **大模型降维快刀**。基础体量大，开 `low/medium` 即可 68 秒收工，适合任务包极其明确或 `terra` 维护时无缝顶上 |
| **极致经济 Worker** | **DSH** | `sorrycode-cn/deepseek-flash` | 默认 | **78.3 s** (19 轮) | **~$0.008** | **成本仅 1/10（不到 1 美分）**。92% 缓存命中，适合大批量常规代码填充、补单测、文档同步 |

### 命令行一键调用参考
```bash
# 1. 日常将 Codex 设为 gpt-6.1-terra + high 档（甜点档位）
magpie codex sorrycode-gpt/gpt-6.1-terra
magpie codex effort high

# 2. 或在脚本中按任务指定模型与档位启动非交互 Worker：
codex exec -m "sorrycode-gpt/gpt-6.1-terra" -c 'model_reasoning_effort="high"' "执行任务包：..."
codex exec -m "sorrycode-gpt/gpt-6.1-sol"   -c 'model_reasoning_effort="low"'  "执行任务包：..."
```

### 附：本次评估明确避坑清单
- ❌ **`gpt-6.1-terra` 开 `low`**：漏边界校验；开 **`xhigh`**：代码与 `high` 一字不差但慢 38 秒。
- ❌ **`gpt-6.1-sol` 开 `xhigh`**：单次请求延迟飙升至 18s~55s，单任务贵 5~10 倍。
- ❌ **`sorrycode-cn/qwen3.8-flash`**：在 Agent 多轮循环中 0% 缓存命中且容易陷入命令死循环，超过 300s 超时。
