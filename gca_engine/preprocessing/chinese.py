"""
中文文本处理（负责人：岳柔）。

v0.1 只提供最基础的两个函数，保证流程能跑通：
    normalize_text  基础清洗（全角空格、多余空白）
    tokenize        分词（装了 jieba 用 jieba，没装先按空白切）

注意：引擎目前计算 LSA 和词数用的是 core/lsa/preprocessing.py
的旧分词（与旧实验基线一致）。等这里的中文分词方案定下来并
验证通过后，再把引擎切过来 —— 切换时要重新核对基线结果。

待办（岳柔）：
    - 确定中文分词方案（jieba / 其他）
    - 口语词过滤表
    - ASR 重复片段清理
    - 测试样例（tests/test_chinese_*.py）
"""

import re

_FULLWIDTH_SPACE_RE = re.compile(r"[　]")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str | None) -> str:
    """基础清洗：全角空格转半角、压缩连续空白、去首尾空白。

    None 或空字符串返回 ""。
    """
    if text is None:
        return ""
    t = _FULLWIDTH_SPACE_RE.sub(" ", str(text))
    t = _WHITESPACE_RE.sub(" ", t)
    return t.strip()


def tokenize(text: str | None) -> list[str]:
    """中文分词。

    装了 jieba 时用 jieba；没装时先按空白切分（中文句子会变成
    一整个词，效果差 —— 这是临时方案，正式分词方案待定）。
    """
    cleaned = normalize_text(text)
    if not cleaned:
        return []
    try:
        import jieba  # 可选依赖，未安装时回退
    except ImportError:
        return cleaned.split(" ")
    return [w for w in jieba.cut(cleaned) if w.strip()]
