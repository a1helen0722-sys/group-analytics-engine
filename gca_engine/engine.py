"""
gca_engine.engine —— 把各模块接起来的总流程（负责人：雷梦琪）。

v0.1 流程：

    统一 Utterance 列表
      → 输入检查（invalid_input / empty_transcript / insufficient_data）
      → 按时间排序
      → 文本清洗 + LSA（在本次课堂发言上拟合语义空间）
      → 词数统计（与 LSA 同一种分词，保持旧基线一致）
      → GCA 六指标（core.metrics，数学与旧基线一致）
      → 学生指标 → 小组汇总（aggregation）
      → GroupAnalysisResult

时间窗口（固定 5 分钟 / 滑动 5 分钟）由 windows.py 实现，
v0.1 尚未接入，结果中 timeline=None 并在 warnings 里标记。
"""

import logging
from datetime import datetime, timezone

import numpy as np

from gca_engine.aggregation import group_metric_stats
from gca_engine.config import EngineConfig
from gca_engine.core.config import GCAConfig
from gca_engine.core.lsa import clean_text, tokenize
from gca_engine.core.metrics import compute_gca_metrics
from gca_engine.schemas import (
    SIX_METRICS,
    AnalysisStatus,
    GroupAnalysisResult,
    Utterance,
)
from gca_engine.semantic import fit_lsa_space, project_texts

ENGINE_VERSION = "0.1.0"
logger = logging.getLogger(__name__)


def _error_result(
    meeting_id: str,
    status: AnalysisStatus,
    message: str,
    warnings: list[str] | None = None,
) -> GroupAnalysisResult:
    return GroupAnalysisResult(
        meeting_id=meeting_id,
        status=status,
        student_metrics={},
        group_metrics={},
        timeline=None,
        metadata={},
        warnings=warnings or [],
        error=message,
    )


def _validate(meeting_id: str, utterances: list[Utterance]) -> str | None:
    """返回错误信息；输入没问题时返回 None。"""
    if not isinstance(meeting_id, str) or not meeting_id.strip():
        return "meeting_id 必须是非空字符串"
    if not isinstance(utterances, list):
        return "utterances 必须是列表"
    bad = [i for i, u in enumerate(utterances) if not isinstance(u, Utterance)]
    if bad:
        return f"第 {bad[0]} 条发言不是 Utterance 对象"
    return None


def analyze_utterances(
    meeting_id: str,
    utterances: list[Utterance],
    config: EngineConfig | None = None,
) -> GroupAnalysisResult:
    """对一次课堂讨论的发言做完整 GCA 分析（service 层调用本函数）。

    Args:
        meeting_id: 讨论小组 ID。
        utterances: 统一 Utterance 列表（schemas.py）。
        config:     可选 EngineConfig。

    Returns:
        GroupAnalysisResult（见 schemas.py）。
    """
    config = config or EngineConfig()

    error_msg = _validate(meeting_id, utterances)
    if error_msg is not None:
        return _error_result(meeting_id, AnalysisStatus.INVALID_INPUT, error_msg)

    n = len(utterances)
    if n == 0:
        return _error_result(
            meeting_id, AnalysisStatus.EMPTY_TRANSCRIPT, "没有任何发言记录"
        )

    # 按发言时间排序（引擎不假设输入已排序）
    ordered = sorted(utterances, key=lambda u: (u.timestamp, u.utterance_id))

    if n < config.min_utterances:
        return _error_result(
            meeting_id,
            AnalysisStatus.INSUFFICIENT_DATA,
            f"发言只有 {n} 条，少于最少 {config.min_utterances} 条",
        )

    texts = [u.text or "" for u in ordered]
    speaker_ids = [u.speaker_id for u in ordered]

    cleaned = [clean_text(t) for t in texts]
    n_empty = sum(1 for c in cleaned if not c)
    if n_empty == n:
        return _error_result(
            meeting_id,
            AnalysisStatus.INSUFFICIENT_DATA,
            "所有发言清洗后都为空文本，无法分析",
        )

    warnings: list[str] = []
    if n_empty > 0:
        warnings.append(f"有 {n_empty} 条发言清洗后为空文本，对应向量为零向量")

    # --- LSA 语义空间 ----------------------------------------------------
    try:
        model = fit_lsa_space(texts)
        vectors = project_texts(model, texts)
    except ValueError as e:
        return _error_result(
            meeting_id, AnalysisStatus.INSUFFICIENT_DATA,
            f"LSA 无法在本次发言上拟合：{e}",
        )
    if model.actual_dimensions != model.requested_dimensions:
        warnings.append(
            f"LSA 维度从 {model.requested_dimensions} 自动降到 "
            f"{model.actual_dimensions}（发言太少，属于正常现象）"
        )

    # --- GCA 六指标（数学与旧基线一致） ----------------------------------
    gca_config = GCAConfig()
    word_counts = [len(tokenize(t)) for t in texts]
    gca = compute_gca_metrics(meeting_id, speaker_ids, vectors, word_counts, gca_config)

    student_metrics: dict[str, dict[str, float]] = {
        s: {
            "participation": gca.participation[s],
            "internal_cohesion": gca.internal_cohesion[s],
            "overall_responsivity": gca.overall_responsivity[s],
            "social_impact": gca.social_impact[s],
            "newness": gca.newness_by_speaker[s],
            "communication_density": gca.density_by_speaker[s],
        }
        for s in gca.speakers
    }

    if len(gca.speakers) == 1:
        warnings.append(
            "只有一名学生发言：overall_responsivity 和 social_impact 恒为 0"
        )
        status = AnalysisStatus.SINGLE_SPEAKER
    else:
        status = AnalysisStatus.SUCCESS

    warnings.append(
        "timeline 尚未实现（固定 5 分钟窗口 / 滑动 5 分钟窗口开发中，"
        "见 gca_engine/windows.py）"
    )

    end_seconds = [u.end_time for u in ordered if u.end_time is not None]
    duration = max(end_seconds) if end_seconds else max(u.timestamp for u in ordered)

    metadata = {
        "n_utterances": n,
        "n_speakers": len(gca.speakers),
        "duration_seconds": float(duration),
        "empty_text_count": n_empty,
        "lsa": {
            "requested_dimensions": model.requested_dimensions,
            "actual_dimensions": model.actual_dimensions,
        },
        "gca_config": gca_config.to_dict(),
        "engine_version": ENGINE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    return GroupAnalysisResult(
        meeting_id=meeting_id,
        status=status,
        student_metrics=student_metrics,
        group_metrics=group_metric_stats(student_metrics),
        timeline=None,
        metadata=metadata,
        warnings=warnings,
        error=None,
    )
