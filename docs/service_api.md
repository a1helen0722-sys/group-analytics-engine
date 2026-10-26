# analyze_group 基础接口说明

## 1. 调用方式

当前已提供 Python 函数入口：

```python
from gca_engine import analyze_group

result = analyze_group(meeting_id)
```

参数 `meeting_id` 必须是非空字符串，表示一个讨论小组。

首轮与 Agent 组采用直接函数调用还是 REST API，待双方确认。
当前代码尚未提供 REST API。

## 2. 数据准备

当前基础版从内存登记表读取发言数据。
开发演示时，需要先在同一 Python 进程中调用
`register_meeting(meeting_id, utterances)` 准备数据。
登记时的校验规则：

- meeting_id 必须是非空字符串，utterances 必须是 Utterance 列表。
- 每条发言的 meeting_id 必须与登记时传入的 meeting_id 完全一致。
- 参数不合法时，register_meeting 抛出 ValueError，不新增或覆盖登记数据。
- 允许登记空列表；随后调用 analyze_group 会返回 empty_transcript。
- 登记时重新校验并保存每条 Utterance 的副本；修改原列表或原对象不会改变已登记数据。
- 每次分析向引擎传入独立副本，引擎异常或修改输入不会污染后续分析。

上述 ValueError 是数据登记阶段的异常，不是新增的分析状态。
analyze_group 的返回状态仍限定为约定的 7 种。

发言统一使用 `Utterance`：
- 学生身份使用 user_id 转成的字符串。
- timestamp 使用课堂开始后的秒数，必须是有限的非负数字，不接受布尔值。
- end_time 使用同一时间起点，必须是有限的非负数字或 None，不接受布尔值。
- end_time 有值时不能早于 timestamp；例如 timestamp=300、end_time=100 会被拒绝。
- 时间字段不合法时，构造 Utterance 会抛出 ValueError，不新增分析状态。
- text 是适配器输出的未分词文本；课堂适配器可以先做 normalize_text 基础清洗。
- 具体字段以 gca_engine/schemas.py 为准。

### 2.1 课堂数据转换口径

课堂数据先转换为 Utterance，再登记到服务：

```python
from gca_engine.adapters.classroom import transcripts_to_utterances
from gca_engine.service import register_meeting, analyze_group

utterances = transcripts_to_utterances(transcript_records, meeting_id)
register_meeting(str(meeting_id), utterances)
result = analyze_group(str(meeting_id))
```

当前适配器的实际行为：

- datetime 时间以本组最早一条记录为零点；例如 09:00:15、09:00:40 转为 0、25 秒。
- 数字时间按已换算的相对秒数保留；服务不再次归零，上游须保证同一零点。
- normalize_text 转换全角空格、压缩连续空白并去除首尾空白；不代表转换所有全角字符。
- None、空字符串和纯空白记录在适配阶段跳过；保留记录按时间及 utterance_id 排序。
- 分词和口语词过滤由预处理模块及引擎负责；服务不再次清洗、分词或执行 ASR 去重。

metadata.n_utterances 是送入引擎的适配后记录数，不是原始 Transcript 行数；
metadata.empty_text_count 是引擎清洗后为空的记录数，不是适配器已跳过的记录数。
需要核对原始/保留/删除数量时，应使用数据转换方提供的对照记录。
真实数据来源已经明确为课堂系统的历史 Transcript；当前服务仍只接收内存登记，
数据库读取由上游完成，不在此服务中重复连接数据库。

## 3. 返回结果

函数返回 `GroupAnalysisResult` 对象。
调用 `result.to_dict()` 可以转换为字典。

| 字段 | 含义 |
|---|---|
| meeting_id | 本次分析的小组 ID |
| status | 分析状态 |
| student_metrics | 按学生 ID 保存的个人六指标 |
| group_metrics | 各指标的 mean、min、max、std、count |
| timeline | 时间趋势字典（fixed_5min + sliding_5min）；关闭窗口计算或分析失败时为 None |
| metadata | 发言数量、人数、版本等附加信息 |
| warnings | 降维、窗口状态等提示，由引擎返回 |
| error | 错误或无法分析的原因；正常完成时为 None |

## 4. 状态约定

| status | 含义 |
|---|---|
| success | 正常完成 |
| empty_transcript | 已找到小组，但没有发言记录 |
| single_speaker | 只有一名学生发言，且数据足以完成计算 |
| insufficient_data | 发言不足、清洗后全部为空，或无法拟合语义空间 |
| invalid_input | 调用参数不符合要求 |
| not_found | 当前数据源中找不到该 meeting_id |
| internal_error | 分析过程中出现未预期异常 |

当前使用内存数据源时，未登记的 meeting_id 返回 not_found。
已登记但发言列表为空时，返回 empty_transcript。

## 5. 可运行示例

在项目根目录执行：

```powershell
python examples/quickstart.py
```

该示例在同一进程内完成：
准备发言 → 登记数据 → 调用 analyze_group → 输出 JSON。
示例用英文假数据；中文发言走同一入口（引擎默认中文分词，见第 7 节）。

## 6. timeline 结构与读法（Agent 组对接用）

v0.2 已实现固定 5 分钟窗口和滑动 5 分钟窗口（gca_engine/windows.py 计算，
engine 接出）。服务层原样透传引擎返回的 timeline、metadata、warnings 和
error，不在服务中重算指标或补造窗口。

`timeline` 是字典，两个键：

```json
{
  "fixed_5min": [
    {"start_second": 0, "end_second": 300,
     "group_metrics": {"participation": {"mean": 0.4, "min": 0.2, "max": 0.6, "std": 0.1, "count": 3}}},
    {"start_second": 300, "end_second": 600, "group_metrics": {}}
  ],
  "sliding_5min": [
    {"center_second": 30,
     "group_metrics": {"participation": {"mean": 0.5, "min": 0.5, "max": 0.5, "std": 0.0, "count": 1}}}
  ]
}
```

读法：

- `fixed_5min`：左闭右开 `[start_second, end_second)`，每段单独重算 GCA，
  用来回答"这节课第几个五分钟里小组状态如何"。窗口长度始终完整
  （课堂时长不足 5 分钟时也只有一个 [0,300) 窗口）。
- `sliding_5min`：`center_second` 是**更新时刻**（第几秒做的这次统计），
  窗口取 `(center_second - 300, center_second]`，即"最近 5 分钟"；
  首版每 30 秒一个点，课堂结束时间不在 30 秒整数倍上时末尾补一个点；
  课堂时长不足一个更新点（30 秒）时 `sliding_5min` 为 `[]`，warnings 会说明。
- 某个窗口没有发言时，`group_metrics` 是空字典 `{}`，不是 None 也不会报错。
  判断"这个窗口里有没有人"看 `group_metrics["participation"]["count"]`。
  若 metadata 里有 `window_errors`，失败的窗口也按空窗口返回，
  不能把所有 `group_metrics={}` 的窗口都判断成"没有发言"。
- 有数据时 `group_metrics` 使用六指标的 mean/min/max/std/count 结构。
- 窗口指标和整体指标用的是同一套 LSA 语义空间（整节课只拟合一次），
  所以各窗口之间可以比较。
- 窗口的粒度记录在 `metadata.timeline`：
  `fixed_window_seconds` / `sliding_window_seconds` / `sliding_step_seconds` /
  `n_fixed_windows` / `n_sliding_windows`。
- 只想拿个人和小组指标、不需要时间趋势时，可传
  `EngineConfig(timeline_enabled=False)` 关闭窗口计算，此时 timeline 为 None，
  warnings 会说明已关闭。
- 以下情况 timeline 也为 None：分析状态不是 success / single_speaker
  （empty_transcript、insufficient_data、invalid_input、not_found、
  internal_error），例如 LSA 无法拟合。

## 7. 分词方案

引擎默认 `tokenizer="chinese"`：文本先经旧清洗（小写 + 去标点），再交给
中文分词（jieba，依赖已在 requirements.txt；未安装时自动退回按空白切，
中文效果会明显变差）。需要复现旧基线时传
`EngineConfig(tokenizer="legacy")` 使用旧空白分词。实际方案记录在
`metadata.tokenization`（scheme / total_tokens / tokens_per_utterance）。

## 8. 当前限制与待确认事项

- 当前使用内存数据源；数据库读取由上游完成（见 2.1），尚未联调。
- 尚未提供 REST API；与 Agent 组的调用方式和返回字段待确认。
- ASR 重复片段清理尚未实现；口语词过滤目前只有极简词表
  （gca_engine/preprocessing/chinese.py）。
- LSA 语义空间当前在每次课堂发言上单独拟合；跨课堂统一语义空间是后续计划。
