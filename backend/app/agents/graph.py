"""LangGraph StateGraph 构建

状态流：understand → recall → plan → [teach | quiz | review | respond] → respond → reflect → END

集成开源组件：
- LangGraph MemorySaver：自动管理对话历史（替代手动查数据库）
- fsrs 包：间隔重复算法（v0.3.0 复习功能）
"""
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes import understand, recall, plan, teach, quiz, review, respond, reflect

# LangGraph Checkpointer — 自动持久化和恢复对话状态
memory = MemorySaver()


def build_agent_graph():
    """构建 Agent 状态机"""
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("understand", understand)
    graph.add_node("recall", recall)
    graph.add_node("plan", plan)
    graph.add_node("teach", teach)
    graph.add_node("quiz", quiz)
    graph.add_node("review", review)
    graph.add_node("respond", respond)
    graph.add_node("reflect", reflect)

    # 固定边
    graph.set_entry_point("understand")
    graph.add_edge("understand", "recall")
    graph.add_edge("recall", "plan")

    # 条件路由：plan → teach / quiz / review / respond
    def route_action(state: AgentState) -> str:
        return state.get("action_plan", "respond")

    graph.add_conditional_edges("plan", route_action, {
        "teach": "teach",
        "quiz": "quiz",
        "review": "review",
        "respond": "respond",
    })

    # teach / quiz / review → respond → reflect → END
    graph.add_edge("teach", "respond")
    graph.add_edge("quiz", "respond")
    graph.add_edge("review", "respond")
    graph.add_edge("respond", "reflect")
    graph.add_edge("reflect", END)

    # 编译时传入 checkpointer — 自动管理对话历史
    return graph.compile(checkpointer=memory)


# 全局 Agent 实例
agent_graph = build_agent_graph()
