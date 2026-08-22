"""Agent 工具注册表 — v0.7.0 方案 A（工具自主规划）的地基

把项目已有的工具能力包装成 LiteLLM/OpenAI function-calling schema，
并提供统一分发器。agent_loop 节点据此让模型自主决定调用顺序。

新增工具只需：写好 TOOLS 条目 + 在 DISPATCH 里注册执行函数。
"""
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── 工具 Schema（OpenAI function-calling 格式） ──────────────

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "run_code",
            "description": (
                "在隔离沙箱中运行 Python 代码并返回 stdout/stderr。"
                "当学生提交代码、想验证输出、或需要用真实执行结果讲解时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的完整 Python 代码"},
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": (
                "在课程知识库中语义检索相关参考资料。"
                "讲解概念前可先检索，保证内容与教材一致。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索关键词或完整问题"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": (
                "检索该学生的长期记忆（历史对话要点、已学概念、薄弱点）。"
                "个性化讲解或判断起点时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索关键词"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_quiz",
            "description": (
                "围绕指定主题按学生水平出一道选择题（含解析与正确答案索引）。"
                "学生想练习、或讲完概念想检验理解时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "题目主题"},
                    "level": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced"],
                        "description": "学生当前水平",
                    },
                },
                "required": ["topic"],
            },
        },
    },
]

AVAILABLE_TOOLS = [t["function"]["name"] for t in TOOLS]


# ── 分发器 ────────────────────────────────────────────────


async def _dispatch_run_code(args: dict) -> dict:
    from app.tools.sandbox import execute_code
    return await execute_code(args["code"])


async def _dispatch_search_knowledge(args: dict) -> dict:
    from app.tools.knowledge import search_knowledge
    results = await search_knowledge(args["query"])
    return {"results": results}


async def _dispatch_search_memory(args: dict) -> dict:
    # user_id 由调用方注入（见 execute_tool 的 context 参数）
    from app.tools.memory import search_memory
    results = await search_memory(args["user_id"], args["query"])
    return {"results": results}


async def _dispatch_create_quiz(args: dict) -> dict:
    from app.agents.nodes import generate_quiz_payload
    return await generate_quiz_payload(
        topic=args["topic"], level=args.get("level", "beginner"),
    )


DISPATCH: dict[str, Any] = {
    "run_code": _dispatch_run_code,
    "search_knowledge": _dispatch_search_knowledge,
    "search_memory": _dispatch_search_memory,
    "create_quiz": _dispatch_create_quiz,
}


async def execute_tool(
    name: str,
    arguments_json: str,
    *,
    user_id: int | str = "",
) -> dict:
    """执行一次工具调用。

    - 未知工具名 / 非法 JSON / 执行异常都返回 {"error": ...} 而不是抛出，
      让模型能在下一轮看到错误并自我纠正
    - search_memory 自动注入 user_id（模型不可伪造他人记忆）
    """
    if name not in DISPATCH:
        return {"error": f"未知工具: {name}"}

    try:
        args = json.loads(arguments_json or "{}")
    except json.JSONDecodeError as e:
        return {"error": f"参数不是合法 JSON: {e}"}

    if not isinstance(args, dict):
        return {"error": "参数必须是 JSON 对象"}

    if name == "search_memory":
        args["user_id"] = str(user_id)

    try:
        result = await DISPATCH[name](args)
        return result if isinstance(result, dict) else {"result": result}
    except Exception as exc:
        logger.warning("工具 %s 执行失败: %s", name, exc, exc_info=True)
        return {"error": f"工具执行失败: {exc}"}
