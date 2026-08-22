"""意图分类评估集

两层：
- DATASET：带标签的样本，keyword_intent 基线必须全对（回归保护——改关键词时这里会红）
- KNOWN_LIMITS：需要对话上下文才能判对的样本，基线（单条关键词）判不对是已知边界，
  记录在此防止有人误以为基线已覆盖；LLM 分类路径上线后应把它们转正进 DATASET。

跑法：pytest tests/test_eval_intent.py -q
"""
import pytest

from app.agents.nodes import keyword_intent


# 基线必须判对的样本（关键词可区分）
DATASET = [
    # learn_concept
    ("什么是递归？", "learn_concept"),
    ("解释一下列表推导式", "learn_concept"),
    ("讲讲 Python 的装饰器", "learn_concept"),
    ("闭包的原理是什么", "learn_concept"),
    ("怎么理解面向对象", "learn_concept"),
    # practice
    ("给我出几道题", "practice"),
    ("来点练习", "practice"),
    ("考考我循环", "practice"),
    ("出一道 quiz", "practice"),
    ("有没有题目可以做", "practice"),
    # run_code
    ("帮我运行 print(sum(range(10)))", "run_code"),
    ("def add(a, b):\n    return a + b", "run_code"),
    ("import os\nprint(os.getcwd())", "run_code"),
    ("class Foo:\n    pass", "run_code"),
    ("运行这段代码", "run_code"),
    # chitchat
    ("你好", "chitchat"),
    ("hello", "chitchat"),
    ("嘿，在吗", "chitchat"),
    ("Hi there", "chitchat"),
    # ask_question
    ("为什么我的代码会报错", "ask_question"),
    ("这个报错怎么解决", "ask_question"),
    ("帮我看看这段逻辑对不对", "ask_question"),
]


KNOWN_LIMITS = [
    # 需要历史上下文：单独看一条无法与闲聊/答疑区分
    ("继续", "ask_question"),          # 上文在讲概念
    ("那第二点呢？", "ask_question"),   # 指代上文列表
    ("为什么不会栈溢出", "ask_question"),  # 追问上文讲的递归
    ("再来一题", "practice"),           # 省略主语，依赖上文出题场景
]


@pytest.mark.parametrize("text,label", DATASET)
def test_baseline_intent_dataset(text, label):
    assert keyword_intent(text) == label, f"样本 [{text}] 应为 {label}"


@pytest.mark.parametrize("text,label", KNOWN_LIMITS)
def test_known_limits_documented(text, label):
    """记录已知边界：这些样本依赖上下文，v0.4.7 的 LLM 路径负责它们。

    若未来降级基线也能判对，把对应样本移入 DATASET 并删除这里的断言。
    """
    result = keyword_intent(text)
    assert result == label or result == "ask_question", (
        f"样本 [{text}] 基线行为变化：{result}，请更新评估集"
    )


def test_dataset_labels_valid():
    valid = {"learn_concept", "practice", "run_code", "ask_question", "chitchat"}
    for text, label in DATASET + KNOWN_LIMITS:
        assert label in valid, f"样本 [{text}] 标签非法: {label}"


def test_dataset_no_duplicates():
    texts = [t for t, _ in DATASET]
    assert len(texts) == len(set(texts)), "评估集不应有重复样本"
