# 第八周测试矩阵与结果

验收日期：2026-09-26。运行环境：Windows，Python 3.12，Streamlit。本目录脱离原始恢复包，在保留关键数据和代码的条件下执行测试。

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

在精简工程目录运行 `python -m pytest week7/tests -q`：**9 passed**。另以真实浏览器打开运行中的 `http://127.0.0.1:8501`，核查总览载入、异常检测页切换及统计零计数解释、根因分析页切换及指标定义显示。该地址为本机服务。

云端验收：公开网站 <https://5g-ai-kpi-prediction-anomaly-detection-cybqywldc728xbu2uauevq.streamlit.app/> 已从 GitHub `main` 分支启动。实际浏览器依次打开系统总览、KPI 预测、异常检测、根因分析、数据浏览五页；异常检测显示 3σ/IQR 的零计数解释，根因分析显示字段和加权公式；数据浏览把 KPI 从 `1_1_22` 切换到 `11_0_19` 后，图表标题与统计值同步更新。另用无登录态的新 HTTP Cookie 会话访问公网首页，最终返回 HTTP 200。此检查不能替代不同地域、浏览器和长期运行稳定性测试。
