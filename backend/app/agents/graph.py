"""LangGraph StateGraph 构建

状态流：understand → recall → plan → [teach | quiz | code | review | judge] → respond → reflect → END

- Checkpointer：DATABASE_URL 为 PostgreSQL 时用 AsyncPostgresSaver（持久化、多 worker 安全），
  否则回退 MemorySaver（进程内，开发/测试用）。
- E2B：代码沙箱（开源，云端 API）
- Qdrant：向量知识库 RAG（开源）
- Mem0：长期记忆（开源）
- fsrs：间隔重复算法（开源）
"""
import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes import (
    understand, recall, plan, teach, quiz, code, review, judge, respond, reflect,
)
from app.config import settings

logger = logging.getLogger(__name__)

# 默认进程内 checkpointer — init_postgres_checkpointer() 成功后会被替换
memory = MemorySaver()

# Postgres saver 的 async context manager（用于关闭连接池）
_pg_saver_cm = None


def build_agent_graph(checkpointer=None):
    """构建 Agent 状态机"""
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

    return graph.compile(checkpointer=checkpointer or memory)


# 全局 Agent 实例
agent_graph = build_agent_graph()


async def use_persistent_checkpointer() -> bool:
    """DATABASE_URL 是 PostgreSQL 时切换到 AsyncPostgresSaver。

    langgraph-checkpoint-postgres 为可选依赖；未安装或初始化失败时保持 MemorySaver。
    返回是否启用持久化。
    """
    global agent_graph, _pg_saver_cm

    dsn = settings.DATABASE_URL
    if not dsn.startswith("postgresql"):
        return False
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    except ImportError:
        logger.warning(
            "DATABASE_URL 是 PostgreSQL 但未安装 langgraph-checkpoint-postgres，"
            "对话历史将不跨进程持久化。pip install langgraph-checkpoint-postgres 后重启。"
        )
        return False

    dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
    cm = AsyncPostgresSaver.from_conn_string(dsn)
    try:
        saver = await cm.__aenter__()
        await saver.setup()
    except Exception as exc:
        logger.warning("AsyncPostgresSaver 初始化失败，回退 MemorySaver：%s", exc)
        return False

    _pg_saver_cm = cm
    agent_graph = build_agent_graph(saver)
    logger.info("LangGraph checkpointer 已切换为 AsyncPostgresSaver（持久化）")
    return True


async def close_checkpointer() -> None:
    """应用关闭时释放 Postgres saver 连接池"""
    global _pg_saver_cm
    if _pg_saver_cm is not None:
        try:
            await _pg_saver_cm.__aexit__(None, None, None)
        finally:
            _pg_saver_cm = None
