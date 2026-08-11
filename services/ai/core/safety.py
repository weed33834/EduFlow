"""
内容安全与输入过滤模块

对用户输入做轻量级安全检查：
- 检测明显的提示注入 / 系统指令覆盖企图
- 检测超长或疑似滥用输入
被判定为不安全的输入返回拒绝文案，安全输入返回 None。

注意：这是基础防线，不替代深度内容审核；在无 LLM 的场景也提供保护。
"""
import re

# 明显的系统指令覆盖 / 提示注入模式(大小写不敏感)
_INJECTION_PATTERNS = [
    r"ignore (all )?(the )?(above|previous|prior) instructions",
    r"ignore (your|all) previous (prompt|instructions|rules)",
    r"disregard (the )?(above|previous).*instructions",
    r"(you are now|act as if you are|pretend to be)\s*(the system|system|developer|admin)",
    r"reveal (your|the) (system prompt|system-prompt|instructions|prompt)",
    r"(print|output|show) (your )?(system prompt|system-prompt)",
    r"override (your )?(instructions|system|rules)",
    r"jailbreak",
    r"(bypass|remove) (your )?(safety|filter|guardrail|restrictions)",
]

# 明文个人敏感信息(国内常用)简单检测。用数字边界而非 \b，兼容中文语境。
_SENSITIVE_PATTERNS = [
    r"(?<!\d)\d{17}[\dXx](?!\d)",   # 18 位身份证
    r"(?<!\d)1[3-9]\d{9}(?!\d)",    # 大陆手机号
    r"(?<!\d)\d{16,19}(?!\d)",      # 银行卡号
]

_MAX_LENGTH = 4000


def _flag_refusal(reason: str) -> str:
    return (
        "这条消息无法处理：检测到" + reason + "。\n\n"
        "为保证学习环境的安全与纯净，此类内容不会被响应。"
        "如果你有学习相关问题，欢迎继续向我提问。"
    )


def check_input_safety(text: str) -> str | None:
    """检查用户输入。安全返回 None，不安全返回拒绝文案。"""
    if not text or not text.strip():
        return None

    lower = text.lower()

    for pat in _INJECTION_PATTERNS:
        if re.search(pat, lower):
            return _flag_refusal("疑似提示注入或试图覆盖系统指令")

    for pat in _SENSITIVE_PATTERNS:
        if re.search(pat, text):
            return _flag_refusal("包含疑似个人敏感信息(如证件号/手机号/卡号)")

    if len(text) > _MAX_LENGTH:
        return _flag_refusal("输入内容过长")

    return None
