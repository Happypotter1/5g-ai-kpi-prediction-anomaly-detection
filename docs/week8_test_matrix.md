# 第八周测试矩阵与结果

原有测试验收日期：2026-09-26。最新本地与公网浏览器自动化复验日期：2026-10-02。运行环境：Windows，Python 3.12，Streamlit，Microsoft Edge（Playwright 驱动）。本目录脱离原始恢复包，在保留关键数据和代码的条件下执行测试。

| 测试层 | 用例 | 检查点 |
|---|---|---|
| 数据 | `test_required_project_data_is_ready` | 页面所需数据文件齐备 |
| 数据 | `test_metrics_cover_traditional_and_deep_models` | 传统与深度模型指标可读 |
| 数据 | `test_prediction_groups_have_actual_values_and_models` | 各预测结果有实际值和模型列 |
| 数据 | `test_anomaly_outputs_are_consistent` | 异常摘要、标记与排名一致 |
| 数据 | `test_kpi_catalog_matches_dataset_shape` | KPI 目录与 2880 列数据匹配 |
| 端到端启动 | `test_web_server_starts_and_serves_homepage` | 独立进程、随机本地端口、健康接口和首页均返回 HTTP 200；测试后终止进程 |
| 页面交互 | `test_navigation_and_prediction_controls` | 导航、预测结果组与模型选择、空模型提示 |
| 页面交互 | `test_anomaly_and_root_cause_explanations` | 异常策略、统计零计数解释、17 个共同异常、根因 Top N 与定义 |
| 页面交互 | `test_kpi_browser_filter` | KPI 选择、时间范围与样本数量 |

## 最新复验结果

2026-10-02 在当前工程运行 Python 自动测试：**9 passed**，耗时 3.37 秒。Playwright 驱动 Microsoft Edge 154.0.4258.48，同一组用例在本地与公网分别运行，结果如下。

| 浏览器用例 | 内容断言 | 本地 | 公网 |
|---|---|---|---|
| 总览与预测 | 总览 8 个模型、40/840 异常时刻；切换 Transformer；下载 CSV 含 Transformer 列 | 通过 | 通过 |
| 异常检测 | 3σ/IQR 零异常说明可见；并集切为共同异常，异常数 40→17 | 通过 | 通过 |
| 根因分析 | 指标定义与公式可见；Top N 设为 5，图中实际显示 5 个 KPI 标签 | 通过 | 通过 |
| 数据浏览 | 选择 11_0_19；时间范围缩到 839；导出名称、字段与 839 行数据正确 | 通过 | 通过 |

本地：**4 passed、0 failed**，约 15 秒；公网：**4 passed、0 failed**，约 51 秒。公网目标为 [Streamlit 公开应用](https://5g-ai-kpi-prediction-anomaly-detection-cybqywldc728xbu2uauevq.streamlit.app/)；公网模式不启动本机 Streamlit，使用网站包装层中的真实应用 iframe。

## 启动与页面更新检查

本地模式自行选择随机端口、启动独立服务进程、等待健康接口，然后打开真实浏览器；测试结束关闭浏览器与服务。公网应用本次因长期未访问休眠，通过页面按钮唤醒，待应用就绪后执行验收。

首次公网内容检查有两项失败：新模型或新样本数已出现，但下载控件仍处在旧页面的异步更新阶段。测试补充目标图表已更新、页面没有 stale 元素及运行标记消失的条件后再次执行，并保持 CSV 内容断言，最终四项通过。该修正改善测试同步，没有修改数据、统计阈值或模型结果。

## 验收证据

本地与公网证据分别保存在：

- [本地结果 JSON](acceptance/2026-10-02/local/results.json)
- [公网结果 JSON](acceptance/2026-10-02/cloud/results.json)

各目录包含 `01-prediction.png`、`02-anomaly.png`、`03-root-causes.png`、`04-data-browser.png`，以及实际下载的 `prediction-download.csv` 和 `kpi-download.csv`。JSON 保存目标网址、UTC 时间戳、浏览器版本、逐项状态及耗时；UTC 时间加 8 小时对应本说明的中国标准时间验收日期。

运行方法见 [Week 7 说明](../week7/README.md)。将 `BASE_URL` 设为公网 HTTPS 地址即可运行相同测试；不设置则验收本地进程。设置 `E2E_ARTIFACT_DIR` 可保存截图和结果 JSON。

## 验收边界

本轮结果覆盖 Windows Edge、已有处理后数据与上述操作；不代表已完成所有浏览器、移动端、并发负载或长期可用性验收。2026-09-27 的云端检查曾因休眠唤醒超时，本轮成功唤醒与公网 4/4 通过结果更新了该历史状态。异常数量为无监督候选，根因排名为统计关联，不应解释为真实故障准确率或因果证明。

