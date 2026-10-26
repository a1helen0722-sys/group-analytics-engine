# group-analytics-engine

课堂小组讨论 **GCA 六指标分析引擎** —— 后端算法组四个人共同开发的唯一仓库。

> 旧代码（课堂系统、AMI 实验）不在这里开发。这个仓库是全新的、独立的项目。

---

## 1. 这个项目是做什么的

上课时，学生分小组讨论。系统把每个人的发言记录下来，
这个项目负责把这些发言变成**数字化的分析结果**：

- 每个学生 6 个指标：参与度、内部凝聚力、响应度、社会影响力、新信息、沟通密度
- 每个小组的汇总统计
- 按 5 分钟时间窗口（固定 / 滑动）看讨论过程变化

分析结果交给 Agent 组和课堂系统使用。

## 2. 一条数据怎么从"课堂发言"走到"分析结果"

```
课堂发言（Transcript 表里的记录）
   │   adapters/classroom.py（岳柔）转成统一格式
   ▼
统一 Utterance（schemas.py，全项目只有这一种输入格式）
   │   文本清洗 + LSA 建语义空间（core/lsa）
   ▼
GCA 六指标（core/，数学与旧实验基线一致）
   │   aggregation.py（雷梦琪）学生 → 小组
   ▼
小组汇总（mean / min / max / std / count）
   │   service.py（葛艾蓝）
   ▼
analyze_group(meeting_id) → 统一 JSON 结果 → Agent 组 / 课堂系统
```

## 3. 文件夹分别是谁负责

| 文件夹 / 文件 | 负责人 | 内容 |
|---|---|---|
| `gca_engine/core/`（含 `core/lsa/`） | 陈虹宇 | GCA 六指标数学 + LSA（已从旧实验迁移） |
| `gca_engine/semantic.py` | 陈虹宇 | LSA 语义空间入口 |
| `gca_engine/adapters/conversation_json.py` | 陈虹宇 | 旧 AMI 语料 → 统一 Utterance |
| `gca_engine/adapters/classroom.py` | 岳柔 | 课堂数据 → 统一 Utterance |
| `gca_engine/preprocessing/` | 岳柔 | 中文文本处理（基础清洗、分词、口语词过滤） |
| `gca_engine/engine.py` | 雷梦琪 | 把各模块接起来的总流程 |
| `gca_engine/aggregation.py` | 雷梦琪 | 学生结果 → 小组结果 |
| `gca_engine/windows.py` | 雷梦琪 | 固定 5 分钟 / 滑动 5 分钟窗口 |
| `gca_engine/config.py` | 雷梦琪 | 引擎级配置 |
| `gca_engine/schemas.py` | 葛艾蓝 | 统一输入输出格式（全员必须遵守） |
| `gca_engine/service.py` | 葛艾蓝 | `analyze_group(meeting_id)` 对外入口 |
| `tests/` | 公共 | 按文件名前缀分工，见下 |
| `examples/`、`README.md` | 公共 | 改动前在群里说一声 |

**tests/ 分工**（避免两个人同时改同一个测试文件）：

- `test_gca_*.py`、`test_lsa_*.py`、`test_newness_*.py` → 陈虹宇
- `test_classroom_*.py`、`test_chinese_*.py` → 岳柔
- `test_engine_*.py`、`test_aggregation_*.py`、`test_windows_*.py` → 雷梦琪
- `test_schemas_*.py`、`test_service_*.py`、`test_conversation_json.py` → 葛艾蓝

**规则：平时只改自己负责的文件。** 确实需要改到其他模块的文件时，可以在自己的分支里直接修改；涉及 `schemas.py`、公共配置、依赖文件、统一输入输出格式，或合并时发现和别人改了同一个文件，先在群里同步一下。

## 4. 怎么安装依赖

在项目根目录打开终端：

```bash
pip install -r requirements.txt
```

## 5. 怎么运行测试

```bash
python -m pytest tests/ -q
```

全绿（passed）才算没改坏东西。

## 6. 怎么运行一个最简单的示例

```bash
python examples/quickstart.py
```

会看到假数据跑完整个流程的 JSON 结果。

想看 GCA 数学手算验证（每个数字都能用纸笔算出来）：

```bash
python examples/gca_worked_example.py
```

## 7. 四个人如何下载项目

```bash
git clone https://github.com/a1helen0722-sys/group-analytics-engine.git
cd group-analytics-engine
pip install -r requirements.txt
```

## 8. 四个人每天开发前怎么同步

每天开工前，先把 develop 的最新代码合并到自己分支：

```bash
git checkout develop
git pull origin develop
git checkout feature/你的分支
git merge develop
```

## 9. 四个人怎么提交自己的代码

```bash
git checkout feature/你的分支        # 先确保自己在自己的分支上
git add 你改的文件                   # 不要用 git add . 一把梭
git commit -m "做了什么（一句话）"
git push origin feature/你的分支
```

阶段性完成后，在 GitHub 网页上发 **Pull Request**：
`feature/你的分支` → `develop`，组员互相 review 后合并。

## 10. 禁止直接往 main 推代码

```bash
git push origin main     # 绝对禁止
```

- `main`：稳定版本，**月底验收后**才由 develop 合并进来。
- `develop`：大家阶段性合并代码的地方。
- 平时只在自己的 feature 分支上开发。

---

## 分支结构

```
main
 ↑
develop
 ├── feature/chen-gca-core   陈虹宇
 ├── feature/yue-adapter     岳柔
 ├── feature/lei-engine      雷梦琪
 └── feature/ge-service      葛艾蓝
```

## 统一输入格式（全员必须遵守）

只有一种输入：`Utterance`（在 `gca_engine/schemas.py`）。

| 字段 | 类型 | 说明 |
|---|---|---|
| `meeting_id` | str | 讨论小组 ID |
| `speaker_id` | str | user_id 转成的字符串（**不用姓名**） |
| `text` | str | 原始发言文本 |
| `timestamp` | float | **课堂开始后的秒数** |
| `utterance_id` | str | 原 Transcript.id 或唯一记录 ID |
| `end_time` | float 或 None | 发言结束时间，第一版允许 None |

```python
from gca_engine.schemas import Utterance

u = Utterance(
    meeting_id="meeting-001",
    speaker_id="1001",          # user_id 转字符串
    text="我觉得这个方案可行",
    timestamp=125.0,            # 课堂开始后 125 秒
    utterance_id="42",          # Transcript.id
    end_time=None,
)
```

## 统一输出格式（Agent 组按这个对接）

Agent 组只调用：

```python
from gca_engine import analyze_group
result = analyze_group("meeting-001")   # meeting_id 是字符串
```

返回结构：

```json
{
  "meeting_id": "meeting-001",
  "status": "success",
  "student_metrics": {
    "1001": {
      "participation": 0.4,
      "internal_cohesion": 0.3,
      "overall_responsivity": 0.2,
      "social_impact": 0.25,
      "newness": 0.5,
      "communication_density": 0.12
    }
  },
  "group_metrics": {
    "participation": {"mean": 0.4, "min": 0.2, "max": 0.6, "std": 0.1, "count": 3}
  },
  "timeline": {
    "fixed_5min": [
      {"start_second": 0, "end_second": 300, "group_metrics": {"participation": {"mean": 0.4, "min": 0.2, "max": 0.6, "std": 0.1, "count": 3}}}
    ],
    "sliding_5min": [
      {"center_second": 30, "group_metrics": {}}
    ]
  },
  "metadata": {"n_utterances": 6, "n_speakers": 3, "engine_version": "0.2.0",
               "timeline": {"fixed_window_seconds": 300, "sliding_window_seconds": 300,
                            "sliding_step_seconds": 30, "n_fixed_windows": 1, "n_sliding_windows": 10}},
  "warnings": ["只有一名学生发言：overall_responsivity 和 social_impact 恒为 0"],
  "error": null
}
```

要点：

- 学生六指标**只叫这 6 个名字**：`participation`、`internal_cohesion`、
  `overall_responsivity`、`social_impact`、`newness`、`communication_density`
- `group_metrics` 只有 `mean / min / max / std / count`，**没有**"团队综合分"
- `timeline` 已实现（雷梦琪，`gca_engine/windows.py`）：
  - `fixed_5min`：左闭右开 `[start_second, end_second)`，固定 5 分钟一段；
  - `sliding_5min`：`center_second` 是更新时刻，窗口取"最近 5 分钟"，
    首版每 30 秒一个更新点，课堂末尾不在 30 秒整数倍上时补一个点；
  - 没有发言的窗口 `group_metrics` 是 `{}`（不是 None，也不会报错）；
  - 窗口与整体共用同一套 LSA 语义空间（整节课只拟合一次），窗口之间可比；
  - 只要个人/小组指标时可传 `EngineConfig(timeline_enabled=False)` 关掉。

## 状态只有这 7 种

`success`、`empty_transcript`、`single_speaker`、`insufficient_data`、
`invalid_input`、`not_found`、`internal_error`

不要自己发明 `no_data`、`empty`、`error`、`failed` 之类的重复状态。

## 已知问题（重要，别静默改动）

1. **Newness 边界问题待复核（陈虹宇）**：当前数学与旧实验基线完全一致
   （legacy 行为已用 `tests/test_newness_edge_cases.py` 锁死）。复核后如果
   确认有 bug：先在群里说明 → 更新测试 → 再改代码，并在提交信息里写清影响。
2. **timeline 已实现（v0.2，雷梦琪）**：固定 5 分钟 + 滑动 5 分钟窗口
   已接入引擎，结构见上文"统一输出格式"与 `docs/service_api.md`。
3. **中文分词已接入（v0.2）**：引擎默认 `tokenizer="chinese"`（jieba，
   依赖已进 requirements.txt）；`EngineConfig(tokenizer="legacy")` 可复现
   旧基线。仍待实现：ASR 重复片段清理、更完整的口语词过滤表。
