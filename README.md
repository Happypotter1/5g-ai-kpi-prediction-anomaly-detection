# 5G 网络 KPI 预测与异常检测平台

本项目围绕 5G 网络下行 PRB 利用率（DLPRB）数据，构建从数据预处理、KPI 预测、异常检测到结果展示的实验与应用流程。项目同时提供传统机器学习、深度学习和 Transformer 模型对比，以及基于 Streamlit 的交互式 Web 页面。

[在线体验](https://5g-ai-kpi-prediction-anomaly-detection-cybqywldc728xbu2uauevq.streamlit.app/) · [技术结项报告（PDF）](docs/final/第8周_5G_AI项目技术结项报告.pdf) · [项目演示 PPT](docs/final/第8周_5G_AI项目结项演示.pptx)

## 主要功能

- **数据处理与分析**：清洗 DLPRB 数据，进行极值截断、逐列归一化和统计分析。
- **KPI 预测**：比较线性回归、决策树、随机森林、XGBoost、LightGBM、LSTM、GRU 和 Transformer，并提供 Transformer 消融结果。
- **异常检测**：展示 3σ、IQR、Isolation Forest 和 One-Class SVM 的检测结果及时间点分析。
- **根因候选分析**：按异常与正常时段的 KPI 差异等指标排列候选项，供进一步排查；候选排序不等于因果证明。
- **Web 展示**：查看数据概况、预测结果、异常检测、根因候选和项目说明。

## 快速开始

运行环境为 Windows、PowerShell 和 64 位 Python 3.11 或 3.12。在项目根目录执行：

```powershell
.\setup_windows.ps1
.\week7\run_web.ps1
```

启动后访问 [http://127.0.0.1:8501](http://127.0.0.1:8501)。第一个命令创建本地 `.venv` 并安装项目依赖；第二个命令启动 Streamlit。网页也可以直接通过上方“在线体验”链接访问，无需本地安装。

## 项目结构

| 路径 | 内容 |
| --- | --- |
| `week1/`、`week2/` | 5G 核心网与协议实验资料；相关环境和抓包记录来自早期 Ubuntu 实验。 |
| `week3/` | 数据预处理、统计分析及处理后数据。 |
| `week4/` | 传统机器学习 KPI 预测代码、结果与图表。 |
| `week5/` | 深度学习预测、Transformer 消融代码、结果与图表。 |
| `week6/` | 异常检测、根因候选分析代码、结果与图表。 |
| `week7/` | Streamlit 应用、运行脚本与自动化测试。 |
| `docs/` | 测试矩阵、交付说明、使用手册、结项报告和演示材料。 |
| `shared/` | 各周共用的项目路径工具。 |

完整的八周工作说明见[技术结项报告](docs/final/第8周_5G_AI项目技术结项报告.pdf)，Web 操作见[系统使用手册](docs/final/第7周_5G_KPI智能运维平台_系统使用手册.docx)。

## 数据与复现说明

仓库包含 Web 展示所需的处理后 CSV，以及第 4–6 周的实验结果和图表。原始文件 `DLPRB_train_0w-5w.csv` 不在当前交付材料中，因此现有展示与历史结果可以核查，但**不能据此声称已经从原始数据完整重跑全部实验**。不同周的模型可能使用不同预测任务或评估范围，指标应先核对任务定义，再作横向比较。

如持有原始 CSV，可将其放在 `week3/datasets/raw/DLPRB_train_0w-5w.csv`，再运行 `.\run_all.ps1` 从预处理开始重跑第 3–6 周。此操作会重新生成相关结果；只想查看现有结果时，无需运行该脚本。原实验记录中的数据基线为 840 行、2881 列（时间列加 2880 个 Beam/KPI 列）。

异常检测页中，3σ 和 IQR 对汇总序列检出的数量为零，表示按当前聚合粒度与阈值未发现越界点，**不表示原始数据没有异常**。根因候选指标衡量的是统计关联或差异，不应直接解释为已证实的故障原因；详细定义见 Web 页面和技术报告。

## 测试与部署

本地运行 Web 测试：

```powershell
.\.venv\Scripts\python.exe -m pytest week7\tests -q
```

测试覆盖数据读取、页面交互与服务启动。云端部署使用 `week7/app.py` 作为入口、`week7/requirements.txt` 作为网页依赖清单。公开站点与本地 `127.0.0.1:8501` 是两个独立访问入口；详见 [Week 7 使用说明](week7/README.md) 和 [Week 8 交付说明](docs/week8_delivery.md)。
