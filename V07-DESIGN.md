# v0.7.0 设计提案：从固定状态机到工具自主规划

## 背景

当前 Agent 是**固定路由**：understand 意图分类 → plan 按意图表硬编码跳转
（learn_concept→teach，practice→quiz……）。这套结构稳定可测，但本质是
"带 LLM 的流程图"，不是自主 Agent——模型没有决定"下一步做什么"的权力。

路线图承诺的 v0.7.0「多 Agent 协作 / 工具自主规划」有两个候选实现方向，
成本与收益差异大，需要产品决策。

## 方案 A：工具自主规划（推荐）

把 teach/review/code 三类"生成型"节点合并为一个 **function-calling 主循环**：

```
plan 之后 → agent_loop:
    LiteLLM function calling 绑定工具：
      - run_code(code)        → E2B 沙箱
      - search_knowledge(q)   → Qdrant RAG
      - search_memory(q)      → Mem0
      - create_quiz(topic, level)  → JSON mode 出题
    模型自行决定调用哪个工具、调用几次、何时收尾作答
    循环上限 N=4 次，超限强制总结
judge / FSRS 调度 / 画像回写保持现状（教学规则不该交给模型自由发挥）
```

- ✅ 真正的 agent 行为：学生贴一段报错代码时，模型可以自己先跑代码、
  再查知识库、再讲解——现在这种组合问题只能走单一路径
- ✅ 复用现有全部工具函数，主要是编排层改造
- ⚠️ 成本：token 用量上升（每轮多次模型调用）；需要 trace 里记录完整工具链
- ⚠️ 需要为降级模式保留现有关键词路由（无 key 时行为不变）
- 预估改动：graph.py 重构 + nodes 新增 loop 节点 + tools 包装成 schema + 测试，
  约 2~3 天工作量

## 方案 B：专业子 Agent 协作

保持现有图结构不变，把 teach/quiz/judge 升级为三个带独立 system prompt
与上下文的「角色 Agent」（出题官/判卷官/导师），互相通过状态传递协作。

- ✅ 改动小，风险低
- ❌ 本质还是现在的固定流程，只是提示词更精致——不满足"自主性"目标
- 更像 v0.4.x 的打磨而非新迭代

## 建议

**方案 A**。理由：项目定位就是 Agent（用户明确强调过）；
且现有 judge/FSRS/画像等教学护栏不动，自主性只开放在"信息获取与验证"层面，
风险可控。

## 无论选哪个都先做的地基（已具备 ✅）

- 追踪：traces.jsonl 会自动记录每次 LLM 调用的耗时与规模，
  方案 A 需要的工具链路追踪在此扩展 event 字段即可
- 测试：118 个离线用例保证重构安全网
- 评估集：意图分类已有基线；方案 A 需要新增"工具选择合理性"评估样本
