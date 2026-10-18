"""
gca_engine 公共数据格式 —— 统一输入 / 统一输出（负责人：葛艾蓝）。

全员约定（四个人都必须遵守，不要自己另建一套）：

1. 一次 meeting = 一个讨论小组。
2. 学生身份只用 speaker_id（user_id 转成字符串），不用姓名。
3. 时间一律是"课堂开始后的秒数"。
4. 输入只有一种：Utterance；输出只有一种：GroupAnalysisResult。
5. 状态只用 AnalysisStatus 里的 7 种，不要自己发明
   no_data / empty / error / failed / not_enough 之类的重复状态。
6. 学生六指标只叫这 6 个名字：SIX_METRICS。
"""

from dataclasses import asdict, dataclass, field
from enum import Enum

# 学生六指标的正式名字（全项目唯一，Agent 组也按这个名字对接）
SIX_METRICS = (
    "participation",
    "internal_cohesion",
    "overall_responsivity",
    "social_impact",
    "newness",
    "communication_density",
)


class AnalysisStatus(str, Enum):
    """分析状态。全项目只允许这 7 种。"""

    SUCCESS = "success"                      # 正常完成
    EMPTY_TRANSCRIPT = "empty_transcript"    # 没有任何发言
    SINGLE_SPEAKER = "single_speaker"        # 只有一名学生（指标仍会计算）
    INSUFFICIENT_DATA = "insufficient_data"  # 发言太少（<2 条）或全部为空
    INVALID_INPUT = "invalid_input"          # 输入格式不对
    NOT_FOUND = "not_found"                  # 找不到这个 meeting_id
    INTERNAL_ERROR = "internal_error"        # 引擎内部出错


@dataclass
class Utterance:
    """一条课堂发言 —— 全项目唯一的输入格式。

    Attributes:
        meeting_id:   讨论小组 ID（字符串）。
        speaker_id:   user_id 转成的字符串。
        text:         原始发言文本（不做清洗，清洗在预处理阶段）。
        timestamp:    课堂开始后的秒数（float）。
        utterance_id: 原 Transcript.id 或任何唯一记录 ID（字符串）。
        end_time:     发言结束时间；第一版允许 None。
    """

    meeting_id: str
    speaker_id: str
    text: str
    timestamp: float
    utterance_id: str
    end_time: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.meeting_id, str) or not self.meeting_id.strip():
            raise ValueError("meeting_id 必须是非空字符串")
        if not isinstance(self.speaker_id, str) or not self.speaker_id.strip():
            raise ValueError("speaker_id 必须是非空字符串（user_id 转成字符串）")
        if not isinstance(self.text, str):
            raise ValueError("text 必须是字符串")
        if not isinstance(self.timestamp, (int, float)) or self.timestamp < 0:
            raise ValueError("timestamp 必须是 >= 0 的数字（课堂开始后的秒数）")
        if not isinstance(self.utterance_id, str) or not self.utterance_id.strip():
            raise ValueError("utterance_id 必须是非空字符串")
        if self.end_time is not None:
            if not isinstance(self.end_time, (int, float)) or self.end_time < 0:
                raise ValueError("end_time 必须是 >= 0 的数字或 None")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GroupAnalysisResult:
    """analyze_group(meeting_id) 的统一输出格式（第一版）。

    timeline 目标格式（v0.2，见 gca_engine/windows.py）：
        {
            "fixed_5min": [    # 固定 5 分钟窗口：0-300, 300-600, ...
                {"start_second": 0, "end_second": 300, "group_metrics": {...}},
            ],
            "sliding_5min": [  # 最近 5 分钟滑动窗口，每 60 秒一个更新点
                {"center_second": 60,  "group_metrics": {...}},
                {"center_second": 120, "group_metrics": {...}},
            ],
        }
    第一版尚未实现，timeline 为 None，并在 warnings 里明确标记。
    """

    meeting_id: str
    status: str
    student_metrics: dict[str, dict[str, float]]  # speaker_id -> 六指标
    group_metrics: dict[str, dict[str, float]]    # 指标名 -> mean/min/max/std/count
    timeline: dict | None = None
    metadata: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
