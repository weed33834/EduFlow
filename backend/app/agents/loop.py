"""agent_loop — 工具自主规划主循环（v0.7.0 方案 A 核心）

两阶段设计：
1. 规划期（静默）：模型可连续调用工具（≤4 轮）收集事实——跑代码/查知识库/
   查记忆/出题；每轮结果回填对话，模型自行判断何时信息足够
2. 作答期（流式）：以「导师」身份结合全部工具结果组织最终讲解，
   通过 custom writer 逐 token 推给前端

judge / FSRS / 画像等教学护栏不进入本循环——自主性只开放在信息获取层。

降级：settings.llm_available 为假时路由层不会把流量送进来（plan 保持旧路径）。
"""
import json
import logging
import time

import litellm

from app.agents.state import AgentState
from app.agents.tools_registry import TOOLS, execute_tool
from app.config import settings
from app.tools.llm import chat_completion_streaming
from app.tools.tracing import record_span

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 4

PLANNER_PROMPT = """你是编程学习 Agent 的调查规划器。学生提了一个问题，
你可以调用工具获取真实信息：
- run_code: 在沙箱里真实运行 Python 代码（验证输出/复现报错）
- search_knowledge: 检索课程知识库（保证讲解与教材一致）
- search_memory: 查询该学生的历史记忆（已学过什么、哪里薄弱）
- create_quiz: 生成练习题（一般留给后续环节，不要主动滥用）

规则：
1. 只在必要时调用工具；没有明确需要就一次都不调
2. 每轮思考后给出下一步：要么继续调用工具，要么停止
3. 不要编造工具结果——一切以返回为准
4. 收集到足够信息后，直接停止调用（输出任意简短确认即可）"""

ANSWER_PROMPT = """你是学生的编程导师「EduAgent」。请基于【调查结果】用中文讲解，
要求：
1. 口吻友好、简洁，不超过 300 字（代码示例不计入）
2. 关键结论必须与调查结果一致，禁止编造运行输出
3. 有代码示例时用 markdown 代码块
4. 如果调查发现学生相关薄弱点，讲解时主动照顾"""


async def agent_loop(state: AgentState) -> AgentState:
    """工具自主规划节点：替代原 teach/code 的固定路径"""
    from app.agents.nodes import _emitter, _recent_messages

    message = state["user_message"]
    profile = state.get("student_profile", {})
    level = profile.get("current_level", "beginner")
    history = state.get("history", [])
    user_id = state.get("user_id", "")

    hist_msgs = _recent_messages(history, exclude_last=True, max_entries=6)

    context_parts = []
    knowledge = state.get("knowledge_context") or []
    memories = state.get("memory_context") or []
    if knowledge:
        context_parts.append(
            "参考资料：\n" + "\n".join(k.get("text", "")[:200] for k in knowledge[:2])
        )
    if memories:
        context_parts.append(
            "学生记忆：\n" + "\n".join(m.get("text", "")[:100] for m in memories[:3])
        )

    user_block = f"学生问题：{message}\n学生水平：{level}"
    if context_parts:
        user_block += "\n\n" + "\n\n".join(context_parts)

    # ── 阶段 1：工具规划循环（静默） ─────────────────────
    convo: list[dict] = [
        {"role": "system", "content": PLANNER_PROMPT},
        *hist_msgs,
        {"role": "user", "content": user_block},
    ]
    tool_trace: list[dict] = []

    for rnd in range(1, MAX_TOOL_ROUNDS + 1):
        t0 = time.perf_counter()
        try:
            resp = await litellm.acompletion(
                model=settings.LITELLM_MODEL,
                messages=convo,
                api_key=settings.LITELLM_API_KEY,
                api_base=settings.LITELLM_BASE_URL,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=600,
            )
        except Exception as exc:
            logger.warning("agent_loop 第 %d 轮调用失败：%s", rnd, exc, exc_info=True)
            record_span("loop.error", dur_ms=(time.perf_counter() - t0) * 1000,
                        ok=False, error=str(exc))
            break

        msg = resp.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        record_span(
            f"loop.round{rnd}",
            dur_ms=(time.perf_counter() - t0) * 1000,
            out_chars=len(msg.content or ""),
            stream=False,
        )

        if not tool_calls:
            break  # 模型认为信息足够

        # 回填 assistant 的工具调用请求（OpenAI 协议要求）
        convo.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {
                        "name": c.function.name,
                        "arguments": c.function.arguments,
                    },
                }
                for c in tool_calls
            ],
        })

        for call in tool_calls:
            name = call.function.name
            t1 = time.perf_counter()
            result = await execute_tool(name, call.function.arguments, user_id=user_id)
            dur_ms = (time.perf_counter() - t1) * 1000
            record_span(f"tool.{name}", dur_ms=dur_ms, ok="error" not in result)
            tool_trace.append({
                "tool": name,
                "round": rnd,
                "dur_ms": round(dur_ms, 1),
                "ok": "error" not in result,
            })
            convo.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False)[:4000],
            })
    else:
        logger.warning("agent_loop 达到最大轮数(%d)，强制收尾", MAX_TOOL_ROUNDS)

    # ── 阶段 2：流式作答 ─────────────────────────────────
    if tool_trace:
        findings_lines = []
        for t in tool_trace:
            findings_lines.append(f"- 工具 {t['tool']}（{'成功' if t['ok'] else '失败'}，{t['dur_ms']}ms）")
        findings = "\n".join(findings_lines)
    else:
        findings = "- 本轮未调用任何工具，直接基于已有知识回答"

    answer_messages = [*hist_msgs, {"role": "user", "content":
        f"{user_block}\n\n【调查结果】\n{findings}\n"
        f"（工具原始输出已在上方对话中，请据此回答，不得编造。）"}]

    content = await chat_completion_streaming(
        answer_messages,
        on_delta=_emitter(),
        system_prompt=ANSWER_PROMPT,
        temperature=0.5,
        max_tokens=1200,
    )

    return {**state, "teach_content": content, "tool_trace": tool_trace}
