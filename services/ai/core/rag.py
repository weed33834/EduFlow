"""
RAG 上下文构建助手

将本地知识库检索(knowledge_search)接入智能体：根据用户问题检索相关知识，
构造成可注入系统/用户提示词的上下文块，实现「检索增强生成」——让答案有据可依，
并在无 LLM 时也能给出基于知识库的落点。
"""
from tools.knowledge_search import search_knowledge, get_prerequisites


async def build_knowledge_context(query: str, topic: str = "", max_items: int = 4) -> str:
    """检索知识库并格式化为提示词上下文块。

    Args:
        query: 用户问题/主题。
        topic: 可选主题过滤。
        max_items: 最多注入的条目数。

    Returns:
        一段可拼入提示词的「相关资料」文本；无匹配时返回空串。
    """
    results = await search_knowledge(query, topic)
    if not results:
        return ""
    lines = []
    for r in results[:max_items]:
        title = r.get("title", "")
        content = r.get("content", "")
        lines.append(f"- 【{title}】{content}")
    return "以下是检索到的相关知识，请优先据此回答：\n" + "\n".join(lines)


async def build_prerequisite_context(topic: str) -> str:
    """查找主题的前置知识并格式化为上下文。

    Returns:
        前置知识提示文本；无前置时返回空串。
    """
    prereqs = await get_prerequisites(topic)
    if not prereqs:
        return ""
    return "学习该主题前，建议先掌握：" + "、".join(prereqs) + "。"
