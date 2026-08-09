"""
AI Examiner Agent - 自适应出题与评估

根据学习内容生成高质量练习题，并对学生的作答进行评估。
题目格式统一为 {id, question, options, answer, explanation, difficulty}，
其中 answer 为字符串格式的选项数字索引（如 "0"、"1"）。
未配置 API Key 时返回预设的通用编程题库与基础评估。
"""
import json
from typing import Optional, Union

from core.llm import chat_completion, is_llm_available

EXAMINER_SYSTEM_PROMPT = """你是一位 AI 出题专家，擅长根据学习内容生成高质量的练习题。
出题原则：
1. 难度自适应：根据学生当前水平调整题目难度
2. 覆盖全面：涵盖概念理解、应用分析、综合评估等层次
3. 题型多样：选择题、填空题、简答题、编程题等
4. 即时反馈：每题提供详细解析和参考答案
5. 知识巩固：针对薄弱点重点出题

请用中文出题。所有题目的 answer 字段必须是选项的数字索引字符串（如 "0"、"1"）。"""

# ---------------------------------------------------------------------------
# 预设通用编程题库（降级时使用）
# 涵盖变量、数据类型、控制流、函数、数据结构、面向对象等核心知识点
# answer 为 options 列表的数字索引字符串
# ---------------------------------------------------------------------------

_FALLBACK_QUESTION_BANK = [
    {
        "id": 1,
        "question": "下列哪个选项是 Python 中合法的变量名？",
        "options": ["2variable", "_username", "class", "my-var"],
        "answer": "1",
        "explanation": (
            "Python 变量名不能以数字开头（排除 2variable），不能是关键字（class 是关键字），"
            "不能包含连字符（my-var 会被解析为减法）。以下划线开头的 _username 是合法的变量名。"
        ),
        "difficulty": "easy",
    },
    {
        "id": 2,
        "question": "在 Python 中，下列哪种数据类型是不可变的？",
        "options": ["list（列表）", "dict（字典）", "tuple（元组）", "set（集合）"],
        "answer": "2",
        "explanation": (
            "tuple（元组）是不可变序列，创建后不能修改其元素；"
            "list、dict、set 都是可变类型，可以原地增删改。"
            "不可变类型更安全，可作为字典的键或集合的元素。"
        ),
        "difficulty": "easy",
    },
    {
        "id": 3,
        "question": "执行 `for i in range(1, 5): print(i)` 会输出几个数字？",
        "options": ["3 个", "4 个", "5 个", "1 个"],
        "answer": "1",
        "explanation": (
            "range(1, 5) 生成从 1 开始到 5（不包含 5）的整数序列，即 1、2、3、4，共 4 个数字。"
            "range 的结束值是「不包含」的，这是初学者常犯的错误。"
        ),
        "difficulty": "easy",
    },
    {
        "id": 4,
        "question": "下列关于 Python 函数参数的说法，哪一项是正确的？",
        "options": [
            "函数必须包含 return 语句，否则会报错",
            "默认参数必须放在非默认参数之后",
            "函数只能接收固定数量的参数",
            "关键字参数不能与位置参数混用",
        ],
        "answer": "1",
        "explanation": (
            "Python 函数可以没有 return 语句，此时默认返回 None；"
            "默认参数必须放在所有非默认参数之后，否则会引发语法错误；"
            "通过 *args 和 **kwargs 可接收可变数量的参数；"
            "关键字参数可以与位置参数混用（位置参数在前）。"
        ),
        "difficulty": "medium",
    },
    {
        "id": 5,
        "question": "以下代码的输出是什么？\n\nx = [1, 2, 3]\ny = x\ny.append(4)\nprint(x)",
        "options": ["[1, 2, 3]", "[1, 2, 3, 4]", "[4]", "报错"],
        "answer": "1",
        "explanation": (
            "在 Python 中，`y = x` 并不会创建新列表，而是让 y 和 x 指向同一个列表对象。"
            "因此 y.append(4) 修改的是它们共同指向的列表，x 也会变成 [1, 2, 3, 4]。"
            "若要创建独立副本，应使用 x.copy() 或 x[:]。"
        ),
        "difficulty": "medium",
    },
    {
        "id": 6,
        "question": "关于 Python 中列表推导式 `[x*2 for x in range(5) if x % 2 == 0]`，结果是什么？",
        "options": ["[0, 4, 8]", "[0, 2, 4, 6, 8]", "[2, 4]", "[0, 4]"],
        "answer": "0",
        "explanation": (
            "range(5) 产生 0,1,2,3,4；条件 `if x % 2 == 0` 筛选出偶数 0,2,4；"
            "再对每个偶数乘以 2，得到 0,4,8。列表推导式从左到右阅读："
            "「表达式 for 变量 in 可迭代对象 if 条件」。"
        ),
        "difficulty": "medium",
    },
    {
        "id": 7,
        "question": "下列关于面向对象编程中「继承」的描述，哪一项是正确的？",
        "options": [
            "子类只能继承一个父类的属性和方法",
            "子类可以重写（override）父类的方法",
            "子类不能调用父类被重写的方法",
            "继承会破坏封装性，应尽量避免使用",
        ],
        "answer": "1",
        "explanation": (
            "子类可以重写父类的方法以实现多态行为；Python 支持多继承；"
            "子类可通过 super() 调用父类被重写的方法；"
            "继承是面向对象的核心特性之一，合理使用能提高代码复用性，不会破坏封装。"
        ),
        "difficulty": "medium",
    },
    {
        "id": 8,
        "question": "在 Python 中，`try/except` 语句的作用是什么？",
        "options": [
            "用于循环控制",
            "用于异常捕获与处理",
            "用于定义函数",
            "用于导入模块",
        ],
        "answer": "1",
        "explanation": (
            "try/except 用于捕获和处理程序运行时可能出现的异常（错误）。"
            "try 块中放置可能出错的代码，except 块中编写异常处理逻辑，"
            "可配合 else（无异常时执行）和 finally（始终执行）使用，保证程序健壮性。"
        ),
        "difficulty": "easy",
    },
    {
        "id": 9,
        "question": "下列哪种方式可以正确地打开一个文件并在使用后自动关闭？",
        "options": [
            "f = open('a.txt'); f.read(); f.close()",
            "with open('a.txt') as f: f.read()",
            "open('a.txt').read()",
            "以上都不对",
        ],
        "answer": "1",
        "explanation": (
            "使用 `with open(...) as f` 语句（上下文管理器）会在代码块结束后自动关闭文件，"
            "即使发生异常也能正确释放资源，是最推荐的文件操作方式。"
            "选项 A 需手动关闭且异常时不安全；选项 C 无法显式关闭文件。"
        ),
        "difficulty": "medium",
    },
    {
        "id": 10,
        "question": "关于递归函数，下列说法正确的是？",
        "options": [
            "递归函数不需要基线条件（终止条件）",
            "递归函数必须有基线条件，否则会无限递归导致栈溢出",
            "递归函数的效率总是高于迭代",
            "递归函数不能有返回值",
        ],
        "answer": "1",
        "explanation": (
            "递归函数必须包含基线条件（base case）以终止递归，否则会无限调用自身导致 "
            "RecursionError（栈溢出）。递归在某些场景（如树遍历）代码更简洁，"
            "但通常因函数调用开销而效率低于迭代，且可能受递归深度限制。"
        ),
        "difficulty": "hard",
    },
    {
        "id": 11,
        "question": "Python 中字典（dict）的键可以是以下哪种类型？",
        "options": [
            "只能是字符串",
            "只能是数字",
            "任何不可变类型（如字符串、数字、元组）",
            "任何类型，包括列表",
        ],
        "answer": "2",
        "explanation": (
            "字典的键必须是可哈希的（即不可变类型），如字符串、数字、元组（元组内元素也需不可变）。"
            "列表、字典、集合等可变类型不可哈希，不能作为键。"
            "这是因为字典基于哈希表实现，键的哈希值在生命周期内必须保持不变。"
        ),
        "difficulty": "medium",
    },
    {
        "id": 12,
        "question": "执行 `sorted([3, 1, 4, 1, 5], reverse=True)` 的结果是？",
        "options": ["[1, 1, 3, 4, 5]", "[5, 4, 3, 1, 1]", "[3, 1, 4, 1, 5]", "报错"],
        "answer": "1",
        "explanation": (
            "sorted() 返回一个排序后的新列表，reverse=True 表示降序排列。"
            "原列表 [3,1,4,1,5] 降序排序后为 [5,4,3,1,1]。"
            "注意 sorted() 不修改原列表，而 list.sort() 是原地排序。"
        ),
        "difficulty": "easy",
    },
]


def _filter_bank_by_difficulty(difficulty: str) -> list[dict]:
    """根据难度从题库中筛选题目。难度不匹配时返回全部。"""
    difficulty = (difficulty or "").lower()
    if difficulty in ("easy", "简单", "初级"):
        matched = [q for q in _FALLBACK_QUESTION_BANK if q["difficulty"] == "easy"]
    elif difficulty in ("hard", "difficult", "困难", "高级"):
        matched = [q for q in _FALLBACK_QUESTION_BANK if q["difficulty"] == "hard"]
    elif difficulty in ("medium", "中等", "中级"):
        matched = [q for q in _FALLBACK_QUESTION_BANK if q["difficulty"] == "medium"]
    else:
        matched = list(_FALLBACK_QUESTION_BANK)
    # 若该难度题目不足，补充其他难度题目
    if not matched:
        matched = list(_FALLBACK_QUESTION_BANK)
    return matched


def _fallback_questions(topic: str, difficulty: str, count: int) -> list[dict]:
    """构建降级题库：返回与主题相关的通用编程题目。

    会将 topic 融入题目标注，使题目与学习主题产生关联。
    """
    bank = _filter_bank_by_difficulty(difficulty)
    # 若该难度题目数量不足 count，则从全库补足
    if len(bank) < count:
        for q in _FALLBACK_QUESTION_BANK:
            if q not in bank:
                bank.append(q)
            if len(bank) >= count:
                break

    selected = bank[: max(count, 1)]
    # 深拷贝并重新编号，同时标注主题关联
    result = []
    for idx, q in enumerate(selected, start=1):
        item = {
            "id": idx,
            "question": q["question"],
            "options": list(q["options"]),
            "answer": str(q["answer"]),
            "explanation": q["explanation"],
            "difficulty": q["difficulty"],
            "topic": topic,
        }
        result.append(item)
    return result


async def generate_questions(
    topic: str,
    difficulty: str = "medium",
    count: int = 5,
    context: Union[str, dict, None] = "",
) -> list[dict]:
    """生成练习题。

    根据主题、难度和数量生成结构化练习题。
    未配置 API Key 时返回与主题相关的通用编程预设题库。

    Args:
        topic: 出题主题。
        difficulty: 难度，easy / medium / hard。
        count: 题目数量。
        context: 附加上下文，可为字符串或字典。

    Returns:
        题目列表，每题格式为 {id, question, options, answer, explanation, difficulty}，
        其中 answer 为选项的数字索引字符串。
    """
    # 降级：直接返回预设题库
    if not is_llm_available():
        return _fallback_questions(topic, difficulty, count)

    context_str = context if isinstance(context, str) else json.dumps(context, ensure_ascii=False) if context else ""
    prompt = f"""请围绕主题「{topic}」生成 {count} 道「{difficulty}」难度的单选练习题。
附加上下文：{context_str or '无'}

要求：
1. 每道题必须包含 4 个选项
2. answer 字段必须是正确选项的数字索引字符串，从 "0" 开始（如 "0"、"1"、"2"、"3"）
3. 提供详细的解析

请以 JSON 数组格式返回，格式为：
[
  {{
    "id": 1,
    "question": "题目内容",
    "options": ["选项1", "选项2", "选项3", "选项4"],
    "answer": "0",
    "explanation": "详细解析",
    "difficulty": "{difficulty}"
  }}
]"""
    messages = [{"role": "user", "content": prompt}]
    result = await chat_completion(messages, EXAMINER_SYSTEM_PROMPT, agent_type="examiner")

    questions = _parse_json(result, expect_list=True)
    if isinstance(questions, list) and questions:
        return _normalize_questions(questions, topic, difficulty)

    # LLM 返回解析失败，回退到预设题库
    return _fallback_questions(topic, difficulty, count)


async def evaluate_answer(
    question: str,
    user_answer: str,
    context: Union[str, dict, None] = "",
) -> dict:
    """评估学生答案。

    对学生的作答进行评分和反馈。
    未配置 API Key 时返回基础评估（基于字符串匹配的简单判断）。

    Args:
        question: 题目内容。
        user_answer: 学生的作答。
        context: 上下文，可包含正确答案（correct_answer）等信息。

    Returns:
        评估结果字典，包含 is_correct、score、feedback、hint 等字段。
    """
    # 降级：基础评估
    if not is_llm_available():
        return _fallback_evaluate(question, user_answer, context)

    # 从 context 中提取正确答案（若有）
    correct_answer = ""
    if isinstance(context, dict):
        correct_answer = str(context.get("correct_answer", "") or context.get("answer", ""))
    elif isinstance(context, str):
        correct_answer = context

    prompt = f"""题目：{question}
正确答案：{correct_answer or '（未提供）'}
学生答案：{user_answer}

请评估学生的回答，返回 JSON 格式：
{{
  "is_correct": true或false,
  "score": 0到100的整数,
  "feedback": "个性化反馈，指出优点和不足",
  "hint": "如果答错，给出引导性提示；答对则可留空或给拓展建议"
}}"""
    messages = [{"role": "user", "content": prompt}]
    result = await chat_completion(messages, EXAMINER_SYSTEM_PROMPT, agent_type="examiner")

    evaluation = _parse_json(result, expect_list=False)
    if isinstance(evaluation, dict) and evaluation:
        return _normalize_evaluation(evaluation)

    # 解析失败，回退到基础评估
    return _fallback_evaluate(question, user_answer, context)


# ---------------------------------------------------------------------------
# 降级评估
# ---------------------------------------------------------------------------

def _fallback_evaluate(
    question: str,
    user_answer: str,
    context: Union[str, dict, None],
) -> dict:
    """基础评估降级：基于字符串匹配进行简单判断。"""
    correct_answer = ""
    if isinstance(context, dict):
        correct_answer = str(context.get("correct_answer", "") or context.get("answer", ""))
    elif isinstance(context, str):
        correct_answer = context

    user_answer = (user_answer or "").strip()
    correct_answer = (correct_answer or "").strip()

    # 简单匹配：去除空白和大小写后比较
    is_correct = bool(correct_answer) and user_answer.lower() == correct_answer.lower()

    if is_correct:
        score = 100
        feedback = (
            "恭喜你回答正确！在降级模式下我只能做简单的答案匹配，"
            "无法深入评估你的理解程度。建议你进一步思考：为什么这个答案是正确的？"
            "能否用自己的话解释背后的原理？"
        )
        hint = "回答正确！可以尝试用自己的语言复述这个知识点，巩固理解。"
    elif not correct_answer:
        score = 60
        feedback = (
            f"当前处于降级模式（未配置 OPENAI_API_KEY），且未提供标准答案，"
            f"无法判断你的回答是否正确。你的作答是：「{user_answer or '（空）'}」。\n\n"
            "建议你对照教材或笔记，自行核对答案的正确性。"
            "如果能提供正确答案（通过 context 字段），我可以做更准确的匹配评估。"
        )
        hint = "请尝试提供正确答案，我可以帮你做更精确的比对。"
    else:
        score = 30
        feedback = (
            f"很遗憾，这个回答与标准答案不完全一致。\n"
            f"你的回答：「{user_answer or '（空）'}」\n"
            f"参考答案：「{correct_answer}」\n\n"
            "在降级模式下我只能做简单的字符串匹配，"
            "可能存在表述不同但意思相近的情况。建议你仔细对照参考答案，"
            "检查是理解偏差还是表述差异。"
        )
        hint = (
            "提示：先确认自己是否理解了题目的核心要求，再对照参考答案找出差异所在。"
            "如果只是表述不同但意思一致，说明你的理解是对的。"
        )

    return {
        "is_correct": is_correct,
        "score": score,
        "feedback": feedback,
        "hint": hint,
    }


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _parse_json(text: str, expect_list: bool = False):
    """从 LLM 返回的文本中提取 JSON。"""
    try:
        if expect_list:
            start = text.find("[")
            end = text.rfind("]") + 1
        else:
            start = text.find("{")
            end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _normalize_questions(questions: list, topic: str, difficulty: str) -> list[dict]:
    """规范化 LLM 返回的题目结构，确保字段完整、answer 为字符串索引。"""
    normalized = []
    for idx, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            continue
        options = q.get("options") or []
        answer = q.get("answer")
        # 确保 answer 为字符串格式的数字索引
        if answer is not None:
            answer = str(answer)
        else:
            answer = "0"
        normalized.append({
            "id": q.get("id", idx),
            "question": q.get("question", ""),
            "options": options,
            "answer": answer,
            "explanation": q.get("explanation", ""),
            "difficulty": q.get("difficulty", difficulty),
            "topic": topic,
        })
    return normalized


def _normalize_evaluation(evaluation: dict) -> dict:
    """规范化 LLM 返回的评估结构。"""
    return {
        "is_correct": bool(evaluation.get("is_correct", False)),
        "score": int(evaluation.get("score", 0)),
        "feedback": evaluation.get("feedback", ""),
        "hint": evaluation.get("hint", ""),
    }
