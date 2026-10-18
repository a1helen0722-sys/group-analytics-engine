"""
gca_engine.windows —— 时间窗口分析（负责人：雷梦琪）。

目标（开发中）：
    - 固定 5 分钟窗口：课堂 0-300、300-600、... 每段内重算 GCA；
    - 滑动 5 分钟窗口：最近 5 分钟，每 60 秒一个更新点。

v0.1 尚未实现：engine.py 的结果里 timeline 暂时为 None，
并在 warnings 里明确标记，不会静默给出空结果。
"""

from gca_engine.config import (
    FIXED_WINDOW_SECONDS,
    SLIDING_STEP_SECONDS,
    SLIDING_WINDOW_SECONDS,
)


def build_fixed_windows(
    utterances,
    window_seconds: int = FIXED_WINDOW_SECONDS,
    analyzer=None,
):
    """固定时间窗口（未实现）。

    计划：把课堂按 window_seconds 切成 [0,300)、[300,600)...，
    每段内的发言单独跑一次 GCA，输出该段的 group_metrics。
    """
    raise NotImplementedError(
        "固定时间窗口尚未实现（开发中：feature/lei-engine，见 windows.py）"
    )


def build_sliding_windows(
    utterances,
    window_seconds: int = SLIDING_WINDOW_SECONDS,
    step_seconds: int = SLIDING_STEP_SECONDS,
    analyzer=None,
):
    """滑动时间窗口（未实现）。

    计划：每 step_seconds 一个更新点，取"最近 window_seconds 内"
    的发言重算 GCA，输出每个更新点的 group_metrics。
    """
    raise NotImplementedError(
        "滑动时间窗口尚未实现（开发中：feature/lei-engine，见 windows.py）"
    )
