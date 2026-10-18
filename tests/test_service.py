"""
service 层端到端测试（负责人：葛艾蓝）。

用假数据走一遍 analyze_group 的完整流程：
注册 → 分析 → 检查统一结果格式。
"""

import unittest

from gca_engine.schemas import AnalysisStatus, Utterance
from gca_engine.service import (
    analyze_group,
    clear_meeting,
    list_meetings,
    register_meeting,
)


def _make_utterances(meeting_id="demo-1"):
    """3 名学生、6 条发言的假数据（有意义的英文短句，方便 LSA）。"""
    lines = [
        ("u001", "I think this plan works", 10.0),
        ("u002", "I agree but time is short", 40.0),
        ("u003", "We can split the work into steps", 90.0),
        ("u001", "Yes let us build the core first", 150.0),
        ("u003", "I will handle the data part", 210.0),
        ("u002", "I will write the tests", 280.0),
    ]
    return [
        Utterance(meeting_id, spk, text, ts, f"t{i}")
        for i, (spk, text, ts) in enumerate(lines)
    ]


class TestAnalyzeGroup(unittest.TestCase):

    def tearDown(self):
        for mid in list_meetings():
            clear_meeting(mid)

    def test_success_full_flow(self):
        utterances = _make_utterances()
        register_meeting("demo-1", utterances)
        result = analyze_group("demo-1")

        self.assertEqual(result.meeting_id, "demo-1")
        self.assertEqual(result.status, AnalysisStatus.SUCCESS)
        self.assertIsNone(result.error)

        # 学生指标：3 名学生，每人恰好 6 个指标
        self.assertEqual(set(result.student_metrics), {"u001", "u002", "u003"})
        expected_metrics = {
            "participation", "internal_cohesion", "overall_responsivity",
            "social_impact", "newness", "communication_density",
        }
        for spk, metrics in result.student_metrics.items():
            self.assertEqual(set(metrics), expected_metrics)
            for v in metrics.values():
                self.assertIsInstance(v, float)

        # 小组指标：6 个指标，每个都有 mean/min/max/std/count
        self.assertEqual(set(result.group_metrics), expected_metrics)
        for stats in result.group_metrics.values():
            self.assertEqual(
                set(stats), {"mean", "min", "max", "std", "count"}
            )
            self.assertEqual(stats["count"], 3)

        # timeline 第一版未实现：None + 明确标记
        self.assertIsNone(result.timeline)
        self.assertTrue(
            any("timeline 尚未实现" in w for w in result.warnings)
        )

        # 结果可以序列化成 dict
        d = result.to_dict()
        self.assertEqual(d["meeting_id"], "demo-1")

    def test_not_found(self):
        result = analyze_group("no-such-meeting")
        self.assertEqual(result.status, AnalysisStatus.NOT_FOUND)
        self.assertIsNotNone(result.error)
        self.assertEqual(result.student_metrics, {})

    def test_invalid_meeting_id(self):
        for bad in (123, "", "   "):
            result = analyze_group(bad)
            self.assertEqual(result.status, AnalysisStatus.INVALID_INPUT)

    def test_empty_transcript(self):
        register_meeting("empty-1", [])
        result = analyze_group("empty-1")
        self.assertEqual(result.status, AnalysisStatus.EMPTY_TRANSCRIPT)

    def test_single_speaker_still_computes(self):
        register_meeting("solo-1", [
            Utterance("solo-1", "u001", "I like apples", 1.0, "t1"),
            Utterance("solo-1", "u001", "I like oranges", 10.0, "t2"),
        ])
        result = analyze_group("solo-1")
        self.assertEqual(result.status, AnalysisStatus.SINGLE_SPEAKER)
        self.assertEqual(set(result.student_metrics), {"u001"})
        self.assertTrue(any("只有一名学生" in w for w in result.warnings))

    def test_insufficient_data_too_few(self):
        register_meeting("tiny-1", [
            Utterance("tiny-1", "u001", "I like apples", 1.0, "t1"),
        ])
        result = analyze_group("tiny-1")
        self.assertEqual(result.status, AnalysisStatus.INSUFFICIENT_DATA)

    def test_insufficient_data_all_empty_text(self):
        register_meeting("blank-1", [
            Utterance("blank-1", "u001", "...", 1.0, "t1"),
            Utterance("blank-1", "u002", "!!!", 10.0, "t2"),
        ])
        result = analyze_group("blank-1")
        self.assertEqual(result.status, AnalysisStatus.INSUFFICIENT_DATA)

    def test_register_meeting_validation(self):
        with self.assertRaises(ValueError):
            register_meeting("x", ["not an utterance"])
        with self.assertRaises(ValueError):
            register_meeting(123, [])

    def test_list_and_clear(self):
        register_meeting("demo-1", _make_utterances())
        self.assertIn("demo-1", list_meetings())
        clear_meeting("demo-1")
        self.assertNotIn("demo-1", list_meetings())
        clear_meeting("never-existed")  # 不存在也不报错


if __name__ == "__main__":
    unittest.main()
