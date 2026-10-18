"""
统一 schemas 测试（负责人：葛艾蓝）。

覆盖：Utterance 创建与校验、AnalysisStatus 的 7 种状态、
GroupAnalysisResult 序列化。
"""

import unittest

from gca_engine.schemas import (
    SIX_METRICS,
    AnalysisStatus,
    GroupAnalysisResult,
    Utterance,
)


class TestUtterance(unittest.TestCase):

    def test_create_basic(self):
        u = Utterance(
            meeting_id="m1", speaker_id="u001", text="大家好",
            timestamp=12.5, utterance_id="t1",
        )
        self.assertEqual(u.end_time, None)
        self.assertEqual(u.to_dict()["text"], "大家好")

    def test_create_with_end_time(self):
        u = Utterance("m1", "u001", "大家好", 12.5, "t1", end_time=15.0)
        self.assertEqual(u.end_time, 15.0)

    def test_speaker_id_must_be_string(self):
        # user_id 必须转成字符串，不能直接放 int
        with self.assertRaises(ValueError):
            Utterance("m1", 1, "大家好", 1.0, "t1")

    def test_empty_meeting_id_raises(self):
        with self.assertRaises(ValueError):
            Utterance("", "u001", "大家好", 1.0, "t1")

    def test_empty_speaker_id_raises(self):
        with self.assertRaises(ValueError):
            Utterance("m1", "  ", "大家好", 1.0, "t1")

    def test_negative_timestamp_raises(self):
        with self.assertRaises(ValueError):
            Utterance("m1", "u001", "大家好", -0.5, "t1")

    def test_non_str_text_raises(self):
        with self.assertRaises(ValueError):
            Utterance("m1", "u001", None, 1.0, "t1")

    def test_empty_utterance_id_raises(self):
        with self.assertRaises(ValueError):
            Utterance("m1", "u001", "大家好", 1.0, "")

    def test_negative_end_time_raises(self):
        with self.assertRaises(ValueError):
            Utterance("m1", "u001", "大家好", 1.0, "t1", end_time=-1.0)


class TestStatuses(unittest.TestCase):
    """状态只允许这 7 种，全项目统一。"""

    def test_exact_seven_statuses(self):
        values = [s.value for s in AnalysisStatus]
        self.assertEqual(
            sorted(values),
            sorted([
                "success",
                "empty_transcript",
                "single_speaker",
                "insufficient_data",
                "invalid_input",
                "not_found",
                "internal_error",
            ]),
        )


class TestSixMetrics(unittest.TestCase):

    def test_exact_six_metric_names(self):
        self.assertEqual(
            SIX_METRICS,
            (
                "participation",
                "internal_cohesion",
                "overall_responsivity",
                "social_impact",
                "newness",
                "communication_density",
            ),
        )


class TestGroupAnalysisResult(unittest.TestCase):

    def test_to_dict_round_trip(self):
        result = GroupAnalysisResult(
            meeting_id="m1",
            status="success",
            student_metrics={"u001": {"participation": 0.5}},
            group_metrics={"participation": {"mean": 0.5, "min": 0.5,
                                             "max": 0.5, "std": 0.0, "count": 1}},
            timeline=None,
            metadata={"n_utterances": 2},
            warnings=["timeline 尚未实现"],
            error=None,
        )
        d = result.to_dict()
        self.assertEqual(d["meeting_id"], "m1")
        self.assertEqual(d["status"], "success")
        self.assertEqual(d["timeline"], None)
        self.assertEqual(d["warnings"], ["timeline 尚未实现"])
        self.assertEqual(d["error"], None)


if __name__ == "__main__":
    unittest.main()
