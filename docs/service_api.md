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

上述 ValueError 是数据登记阶段的异常，不是新增的分析状态。
analyze_group 的返回状态仍限定为约定的 7 种。

发言统一使用 `Utterance`：
- 学生身份使用 user_id 转成的字符串。
- 时间使用课堂开始后的秒数。
- 具体字段以 gca_engine/schemas.py 为准。

真实课堂数据的读取和接入方式，后续与数据转换模块衔接。

## 3. 返回结果

函数返回 `GroupAnalysisResult` 对象。
调用 `result.to_dict()` 可以转换为字典。

| 字段 | 含义 |
|---|---|
| meeting_id | 本次分析的小组 ID |
| status | 分析状态 |
| student_metrics | 按学生 ID 保存的个人六指标 |
| group_metrics | 各指标的 mean、min、max、std、count |
| timeline | 时间趋势：固定 5 分钟窗口 + 滑动 5 分钟窗口；关闭窗口计算或分析失败时为 None |
| metadata | 发言数量、人数、版本等附加信息 |
| warnings | 降维、未实现能力等提示 |
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
.\.venv\Scripts\python.exe examples/quickstart.py
```

该示例在同一进程内完成：
准备发言 → 登记数据 → 调用 analyze_group → 输出 JSON。

## 6. 当前限制与待确认事项

- 当前使用内存数据源，真实课堂数据接入尚待联调。
- 时间窗口已接入（固定 5 分钟 + 滑动 5 分钟，滑动每 30 秒一个更新点）；
  课堂时长不足一个滑动更新点时 `sliding_5min` 为空，warnings 会说明。
- 中文处理尚未正式接入，现有 quickstart 使用英文示例数据。
- 待与 Agent 组确认首轮调用方式及返回字段是否满足需求。
- 待与数据转换负责人确认真实数据来源和课堂时间起点。

## 7. timeline 结构（Agent 组对接用）

`timeline` 是字典，两个键：

```json
{
  "fixed_5min": [
    {"start_second": 0, "end_second": 300, "group_metrics": {"participation": {"mean": 0.4, "min": 0.2, "max": 0.6, "std": 0.1, "count": 3}}}
  ],
  "sliding_5min": [
    {"center_second": 30, "group_metrics": {"participation": {"mean": 0.5, "min": 0.5, "max": 0.5, "std": 0.0, "count": 1}}}
  ]
}
```

读法：

- `fixed_5min`：左闭右开 `[start_second, end_second)`，每段单独重算 GCA，
  用来回答"这节课第几个五分钟里小组状态如何"。
- `sliding_5min`：`center_second` 是**更新时刻**（第几秒做的这次统计），
  窗口取 `(center_second - 300, center_second]`，即"最近 5 分钟"；
  首版每 30 秒一个点，课堂结束时间不在 30 秒整数倍上时末尾补一个点。
- 某个窗口没有发言时，`group_metrics` 是空字典 `{}`，不是 None 也不会报错。
  判断"这个窗口里有没有人"看 `group_metrics["participation"]["count"]`。
- 窗口指标和整体指标用的是同一套 LSA 语义空间（整节课只拟合一次），
  所以各窗口之间可以比较。
- 窗口的粒度记录在 `metadata.timeline`：
  `fixed_window_seconds` / `sliding_window_seconds` / `sliding_step_seconds` /
  `n_fixed_windows` / `n_sliding_windows`。
- 只想拿个人和小组指标、不需要时间趋势时，可传
  `EngineConfig(timeline_enabled=False)` 关闭窗口计算。