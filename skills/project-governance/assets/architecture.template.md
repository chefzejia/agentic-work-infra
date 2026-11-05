# Architecture Overview

<!-- 薄契约（Thin Reference）铁律：
     1. 只记录代码签名表达不出的职责边界、状态流转、失败语义与淘汰方案（Alternatives Considered）。
     2. 直接链接源码文件与导出符号（如 `pkg/foo.go` 中的 `Bar`），绝不抄录经常变动的函数列表或实现细节。
     3. 保持对外契约不变的内部重构无需修改本文档。
     4. 一律使用现在时态（Present Tense），严禁写推理心路历程、验收打勾清单或 "（已实现！）" 状态词。 -->

## 系统目标与四层单向依赖（4-Layer DAG）

<一句话：系统解决什么问题，明确不做什么>

- **垂直分包与四层单向 DAG（严禁水平 `service / util` 大泥球与循环依赖）**：
  1. **用户交互外壳（Shell）**：`<如 cli / gui / web>` — 互不依赖，仅调用核心业务子系统。
  2. **核心业务子系统（Core Subsystems）**：`<如 gateway / provider / sessions>` — 高确定性核心状态机与领域逻辑，在 `main` 显式构造函数组装（禁止引入 DI 容器框架）。
  3. **解耦契约与插件/长尾适配层（Contracts & Volatile Edge）**：`<如 routes / plugin / external-adapters>` — 打破循环依赖的纯接口小包，以及高频突变的第三方渠道/插件宿主（严禁核心包反向 import 长尾插件）。
  4. **零业务底座原语（Primitives）**：`<如 proc / filelock / edit / testenv>` — 无业务状态的操作系统与算法原语。

## 子系统薄契约

### <子系统 A>

- **职责与边界**：<负责什么、不负责什么>
- **唯一事实源（源码锚点）**：[`<path/to/file>`](<path/to/file>) 中的 `<SymbolName>`
- **核心运行路径与状态流转**：<关键输入 → 状态变化 → 输出>
- **失败与兼容语义**：<超时/脏数据时 fail-open 还是 fail-closed，如何恢复>
- **守卫单测与验证命令**：`<pytest / go test / pnpm test 具体测试目标>`

## 数据与状态所有权

| 路径/存储 | 语义 | 唯一写入所有者 | 可否删除重建 |
| --- | --- | --- | --- |
| `<如 data/app.db>` | 持久业务状态（唯一事实源） | `<模块名>` | 否 |
| `<如 .cache/index>` | 派生索引/缓存 | `<模块名>` | 是（删除后自动重建） |

## 关键架构决策（已落地现状）

### <决策标题>

- **当前决定（Decision）**：<现在系统采用什么方案（现在时）>
- **淘汰的替代方案（Alternatives Considered）**：
  - **为什么不用 `<方案 X>`**：<具体输在什么物理瓶颈、黑盒税或边界缺陷，防止后人重踩>
- **代价与守卫门禁（Consequences & Guard Tests）**：<付出了什么代价，由哪个守卫单测或编译检查锁死该不变量>
