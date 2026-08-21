"""LangGraph StateGraph 构建

状态流：understand → recall → plan → [teach | quiz | respond] → respond → reflect → END
"""
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes import understand, recall, plan, teach, quiz, respond, reflect


def build_agent_graph():
    """构建 Agent 状态机"""
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("understand", understand)
    graph.add_node("recall", recall)
    graph.add_node("plan", plan)
    graph.add_node("teach", teach)
    graph.add_node("quiz", quiz)
    graph.add_node("respond", respond)
    graph.add_node("reflect", reflect)

    # 固定边
    graph.set_entry_point("understand")
    graph.add_edge("understand", "recall")
    graph.add_edge("recall", "plan")

    # 条件路由：plan → teach / quiz / respond
    def route_action(state: AgentState) -> str:
        return state.get("action_plan", "respond")

    graph.add_conditional_edges("plan", route_action, {
        "teach": "teach",
        "quiz": "quiz",
        "respond": "respond",
    })

    # teach / quiz → respond → reflect → END
    graph.add_edge("teach", "respond")
    graph.add_edge("quiz", "respond")
    graph.add_edge("respond", "reflect")
    graph.add_edge("reflect", END)

    return graph.compile()


# 全局 Agent 实例
agent_graph = build_agent_graph()
