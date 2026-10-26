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

按岳柔已说明的处理流程，课堂数据先转换为 Utterance，再登记到服务：

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
| timeline | 固定窗口结果字典或 None；本轮不要求 sliding_5min |
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
.\.venv\Scripts\python.exe examples/quickstart.py
```

该示例在同一进程内完成：
准备发言 → 登记数据 → 调用 analyze_group → 输出 JSON。

## 6. 固定窗口的服务返回约定

本轮优先实现固定 5 分钟窗口。服务层原样保留引擎返回的 timeline、metadata、
warnings 和 error；不在服务中重算指标或补造窗口。固定窗口结果的结构示意：

```json
{
  "fixed_5min": [
    {"start_second": 0, "end_second": 300, "group_metrics": {}},
    {"start_second": 300, "end_second": 600, "group_metrics": {}}
  ]
}
```

- 固定窗口使用左闭右开区间 [start_second, end_second)。
- 有数据时 group_metrics 使用已有六指标的 mean/min/max/std/count 结构。
- 空窗口 group_metrics 为 {}；读取 participation.count 前应先判断指标是否存在。
- 若引擎提供 metadata.timeline，保留 fixed_window_seconds、n_fixed_windows 等实际信息。
- 若引擎提供 metadata.window_errors，保留 kind、窗口边界和 error 等失败明细；
  不能把所有 group_metrics={} 的窗口都判断成“没有发言”。
- sliding_5min 是后续可选能力，可以缺省或为空列表，本轮不把它作为成功条件。
- 引擎未接入窗口、关闭窗口计算或整体分析失败时允许 timeline=None。

当前 ge-service/develop 基线中的窗口算法仍是占位实现，真实分析仍会返回
timeline=None；雷梦琪分支中的实现尚未合并到此基线。服务测试用替代引擎返回
固定窗口结果，验证字段透传兼容性，不将其当作真实窗口算法已通过验证。

## 7. 当前范围

- 当前使用内存登记表，上游提供转换后的 Utterance。
- 原始记录提取、文本清洗及分词由对应模块维护；真实样例由数据转换方提供。
- 当前基线的中文处理与雷梦琪后续分支不同，不能把示例结果当作新分词方案的指标基线。
- Agent 组尚未正式对接，调用方式仍待确认；本轮保留现有 Python 入口。
