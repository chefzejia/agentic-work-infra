# Agentic Work Infra

适用范围：整个 `agentic-work-infra` 仓库。

## 项目定位

本项目研究 Agent 时代人和 Agent 如何协同完成真实工作。知识库、投标和其他业务是研究课题，不是项目的边界。

## 优先读取

1. [通用工作标准](docs/STANDARDS.md)：本仓任务的执行约束。
2. [当前状态](docs/HANDOFF.md)：当前工作、阻塞和下一步。
3. [README](README.md)：项目入口。

改造项目文档时再读 [文档工程指南](docs/governance/agent-governance.md)，修改 Skill 时再读 [Skill 设计](docs/core/skill-design.md)。

## 架构约束

1. **共同可观测**：人和 Agent 面对同一个工作状态，不分别维护两套。
2. **授权边界**：Agent 只修改明确授权的范围，不能静默覆盖原始材料。
3. **显式不确定**：未知、冲突和待确认必须保持显式，不能伪装成确定。
4. **当前与长期分离**：当前任务可以引用长期知识和规则，但不能把任务变量自动写回长期层。
5. **单一主线**：辅助索引、缓存和生成结果可重建，不能成为第二套工作状态。

## 修改和验证

```bash
git status --short --branch -uall
git diff --check
```

检查 Markdown 链接、文档职责、规则来源和模板实例化路径。模板中的填空字段必须在目标项目落地时替换或删除。

验收标准：Agent 能从入口找到当前工作与适用规则，确定修改范围并执行验证。未验证的场景明确列出。

## 工具和本地环境

按 [通用工作标准](docs/STANDARDS.md) 选择最轻够用的工具。使用宿主已有接口和运行时，先实测再判断能力缺口；不把本机路径、浏览器版本或认证状态写入通用模板。

外部参考源码放在 `thirdparty/`，已被 Git 忽略。快照可重新获取，不进主仓库。

## 文档路由

- [人机协同模型](docs/core/agentic-work-model.md)：原则与推导。
- [文档工程指南](docs/governance/agent-governance.md)：职责、更新条件、标准分发和 mono-repo 适配。
- [通用标准真源](docs/governance/templates/standards.md)：标准正文唯一修改位置；本仓 `docs/STANDARDS.md` 只做路由。
- [模板](docs/governance/templates/)：按实际需要实例化，不批量创建空文档。
- [LESSONS](docs/LESSONS.md)：失败证据与候选规则，审议后更新对应规则所有者。
- [知识库 Skill](tracks/knowledge-base/SKILL.md)：协同模型在知识工作中的应用。
