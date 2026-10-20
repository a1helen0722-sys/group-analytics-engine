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
| timeline | 时间趋势；当前基础版为 None |
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
- 时间窗口尚未接入，timeline 为 None；完成指标计算时，warnings 会包含未实现提示。
- 中文处理尚未正式接入，现有 quickstart 使用英文示例数据。
- 待与 Agent 组确认首轮调用方式及返回字段是否满足需求。
- 待与数据转换负责人确认真实数据来源和课堂时间起点。