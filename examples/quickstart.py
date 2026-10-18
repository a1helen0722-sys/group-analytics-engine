"""
最简单的完整示例：假数据 → analyze_group → 统一结果。

运行：
    python examples/quickstart.py

注意：中文分词还没正式接入（preprocessing/chinese.py 开发中），
这里先用英文短句当假数据，重点是看整条流程和结果格式。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from gca_engine.schemas import Utterance
from gca_engine.service import analyze_group, register_meeting


def main() -> None:
    meeting_id = "demo-meeting-001"

    # 第一步：课堂发言 → 统一 Utterance（真实项目里由 adapters 完成）
    lines = [
        ("u001", "I think this plan works", 30.0),
        ("u002", "I agree but time is short", 65.0),
        ("u003", "We can split the work into steps", 120.0),
        ("u001", "Yes let us build the core first", 180.0),
        ("u003", "I will handle the data part", 240.0),
        ("u002", "I will write the tests", 300.0),
    ]
    utterances = [
        Utterance(meeting_id, speaker_id, text, timestamp, f"t{i}")
        for i, (speaker_id, text, timestamp) in enumerate(lines)
    ]

    # 第二步：注册 + 分析（Agent 组以后只需要调 analyze_group）
    register_meeting(meeting_id, utterances)
    result = analyze_group(meeting_id)

    # 第三步：看统一结果
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
