"""
engine.py 直接测试（集成负责人补充；日常维护负责人：雷梦琪）。

覆盖 service 层测试没有直接覆盖的引擎路径：
乱序输入、metadata 字段、部分空文本、单人课堂指标值、
1 特征场景（相同中文发言）的优雅降级、自定义配置、非法输入。
"""

import unittest

import numpy as np

from gca_engine.config import EngineConfig
from gca_engine.engine import analyze_utterances
from gca_engine.schemas import AnalysisStatus, Utterance


def _u(mid, spk, text, ts, uid):
    return Utterance(mid, spk, text, ts, uid)


def _no_nan(result) -> bool:
    """递归检查 GroupAnalysisResult.to_dict() 里没有任何 NaN。"""

    def walk(obj):
        if isinstance(obj, dict):
            return all(walk(v) for v in obj.values())
        if isinstance(obj, (list, tuple)):
            return all(walk(v) for v in obj)
        if isinstance(obj, float):
            return not np.isnan(obj)
        return True

    return walk(result.to_dict())


class TestEngineDirect(unittest.TestCase):

    def test_unsorted_input_is_sorted(self):
        us = [
            _u("m1", "a", "third one here", 90.0, "u3"),
            _u("m1", "b", "first one here", 10.0, "u1"),
            _u("m1", "c", "second one here", 50.0, "u2"),
        ]
        r = analyze_utterances("m1", us)
        self.assertEqual(r.status, AnalysisStatus.SUCCESS)
        self.assertEqual(r.metadata["n_utterances"], 3)
        self.assertEqual(r.metadata["n_speakers"], 3)
        # 三人各 1 条 -> 参与度各 1/3（与输入顺序无关）
        for m in r.student_metrics.values():
            self.assertAlmostEqual(m["participation"], 1 / 3)

    def test_metadata_fields(self):
        us = [
            _u("m1", "a", "I like apples", 10.0, "u1"),
            _u("m1", "b", "I like oranges", 75.0, "u2"),
        ]
        r = analyze_utterances("m1", us)
        self.assertEqual(r.status, AnalysisStatus.SUCCESS)
        md = r.metadata
        self.assertEqual(md["n_utterances"], 2)
        self.assertEqual(md["n_speakers"], 2)
        self.assertEqual(md["duration_seconds"], 75.0)
        self.assertEqual(md["empty_text_count"], 0)
        self.assertEqual(md["lsa"]["requested_dimensions"], 300)
        self.assertLessEqual(md["lsa"]["actual_dimensions"], 2)
        self.assertEqual(md["engine_version"], "0.1.0")

    def test_partial_empty_text_warning(self):
        us = [
            _u("m1", "a", "I have words", 10.0, "u1"),
            _u("m1", "b", "   ", 20.0, "u2"),
            _u("m1", "c", "More words here", 30.0, "u3"),
        ]
        r = analyze_utterances("m1", us)
        self.assertEqual(r.status, AnalysisStatus.SUCCESS)
        self.assertTrue(any("1 条发言清洗后为空文本" in w for w in r.warnings))
        self.assertTrue(_no_nan(r))

    def test_all_blank_text_insufficient(self):
        us = [
            _u("m1", "a", "...", 10.0, "u1"),
            _u("m1", "b", "!!!", 20.0, "u2"),
        ]
        r = analyze_utterances("m1", us)
        self.assertEqual(r.status, AnalysisStatus.INSUFFICIENT_DATA)

    def test_single_speaker_metrics_values(self):
        us = [
            _u("m1", "a", "I like apples", 10.0, "u1"),
            _u("m1", "a", "I like oranges", 20.0, "u2"),
            _u("m1", "a", "I like pears too", 30.0, "u3"),
        ]
        r = analyze_utterances("m1", us)
        self.assertEqual(r.status, AnalysisStatus.SINGLE_SPEAKER)
        m = r.student_metrics["a"]
        self.assertAlmostEqual(m["participation"], 1.0)
        self.assertAlmostEqual(m["overall_responsivity"], 0.0)
        self.assertAlmostEqual(m["social_impact"], 0.0)
        self.assertTrue(any("只有一名学生" in w for w in r.warnings))

    def test_identical_chinese_utterances_insufficient_data(self):
        """回归锁定：相同中文发言 -> 空白分词下只有 1 个特征 ->
        TruncatedSVD 拒绝 -> 引擎优雅降级为 insufficient_data，不得崩溃。
        （10.26 接入中文分词 / ASR 去重后此行为可再调整。）"""
        us = [
            _u("m1", "s1", "好的", 10.0, "u1"),
            _u("m1", "s2", "好的", 20.0, "u2"),
        ]
        r = analyze_utterances("m1", us)
        self.assertEqual(r.status, AnalysisStatus.INSUFFICIENT_DATA)
        self.assertIn("LSA", r.error)
        self.assertTrue(_no_nan(r))

    def test_custom_min_utterances(self):
        us = [
            _u("m1", "a", "hello world", 10.0, "u1"),
            _u("m1", "b", "goodbye world", 20.0, "u2"),
        ]
        r = analyze_utterances("m1", us, config=EngineConfig(min_utterances=3))
        self.assertEqual(r.status, AnalysisStatus.INSUFFICIENT_DATA)
        r2 = analyze_utterances("m1", us, config=EngineConfig(min_utterances=2))
        self.assertEqual(r2.status, AnalysisStatus.SUCCESS)

    def test_custom_lsa_components_used(self):
        # EngineConfig.lsa_components 必须真正传给 LSA（接口断链回归）
        us = [
            _u("m1", "a", "I like apples", 10.0, "u1"),
            _u("m1", "b", "I like oranges", 20.0, "u2"),
            _u("m1", "c", "I like pears too", 30.0, "u3"),
        ]
        r = analyze_utterances("m1", us, config=EngineConfig(lsa_components=2))
        self.assertEqual(r.metadata["lsa"]["requested_dimensions"], 2)
        self.assertLessEqual(r.metadata["lsa"]["actual_dimensions"], 2)

    def test_empty_and_invalid_input(self):
        r = analyze_utterances("m1", [])
        self.assertEqual(r.status, AnalysisStatus.EMPTY_TRANSCRIPT)
        r2 = analyze_utterances("m1", ["not an utterance"])
        self.assertEqual(r2.status, AnalysisStatus.INVALID_INPUT)


if __name__ == "__main__":
    unittest.main()
