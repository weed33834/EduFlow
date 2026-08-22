"""LangGraph StateGraph 构建

状态流：understand → recall → plan → [teach | quiz | code | review | judge] → respond → reflect → END

v0.6.0 架构简化：对话历史以 Message 表为唯一事实源（路由层每轮从 DB 构建
initial_state.history 传入），不再使用 Checkpointer。收益：
- 重新生成 / 编辑重发 = 纯 DB 截断 + 重跑，LLM 上下文与 UI 天然一致
- 多 worker 部署天然安全（无需 langgraph-checkpoint-postgres）
- 减少一层状态存储
"""
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes import (
    understand, recall, plan, teach, quiz, code, review, judge, respond, reflect,
)


def build_agent_graph():
    """构建 Agent 状态机（无 checkpointer — 历史由路由层注入）"""
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("understand", understand)
    graph.add_node("recall", recall)
    graph.add_node("plan", plan)
    graph.add_node("teach", teach)
    graph.add_node("quiz", quiz)
    graph.add_node("code", code)
    graph.add_node("review", review)
    graph.add_node("judge", judge)
    graph.add_node("respond", respond)
    graph.add_node("reflect", reflect)

    # 固定边
    graph.set_entry_point("understand")
    graph.add_edge("understand", "recall")
    graph.add_edge("recall", "plan")

    # 条件路由：plan → teach / quiz / code / review / judge / respond
    def route_action(state: AgentState) -> str:
        action = state.get("action_plan", "respond")
        if action == "judge" and not (
            state.get("pending_quiz") or state.get("pending_review")
        ):
            return "respond"
        return action

    graph.add_conditional_edges("plan", route_action, {
        "teach": "teach",
        "quiz": "quiz",
        "code": "code",
        "review": "review",
        "judge": "judge",
        "respond": "respond",
    })

    # teach / quiz / code / review / judge → respond → reflect → END
    graph.add_edge("teach", "respond")
    graph.add_edge("quiz", "respond")
    graph.add_edge("code", "respond")
    graph.add_edge("review", "respond")
    graph.add_edge("judge", "respond")
    graph.add_edge("respond", "reflect")
    graph.add_edge("reflect", END)

    return graph.compile()


# 全局 Agent 实例
agent_graph = build_agent_graph()
