"""
gca_engine 引擎级配置（负责人：雷梦琪）。

注意区分三个 config，不要混用：
- gca_engine/config.py            引擎总配置（本文件）
- gca_engine/core/config.py       GCA 数学参数（GCAConfig，旧基线）
- gca_engine/core/lsa/config.py   LSA 参数（LSAConfig，旧基线）
"""

from dataclasses import asdict, dataclass

# 时间窗口默认值（第一版约定）
FIXED_WINDOW_SECONDS = 300    # 固定 5 分钟窗口
SLIDING_WINDOW_SECONDS = 300  # 滑动 5 分钟窗口
SLIDING_STEP_SECONDS = 60     # 滑动窗口每 60 秒一个更新点


@dataclass
class EngineConfig:
    """引擎总配置（v0.1 只用到 min_utterances 和 lsa_components）。"""

    fixed_window_seconds: int = FIXED_WINDOW_SECONDS
    sliding_window_seconds: int = SLIDING_WINDOW_SECONDS
    sliding_step_seconds: int = SLIDING_STEP_SECONDS
    min_utterances: int = 2   # 少于这个数直接 insufficient_data
    lsa_components: int = 300  # 与旧基线 LSAConfig 默认一致；小语料自动降维

    def to_dict(self) -> dict:
        return asdict(self)
