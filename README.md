# 5G AI 项目（Windows 恢复版）

本目录依据原“项目理解与八周计划”对话中第 1–6 周的真实实验记录重建。

## 周次与交付内容

- `week1`：free5GC + UERANSIM 环境、Network Namespace/veth/NAT、端到端验收材料（历史 Ubuntu 环境归档）。
- `week2`：NAS/NGAP/GTP-U 抓包脚本、协议分析、基线与异常 pcap 清单（历史 Ubuntu 环境归档）。
- `week3`：DLPRB 清洗、99.99% Winsorization、逐列 Min-Max 归一化、统计分析。
- `week4`：Linear Regression、Decision Tree、Random Forest、XGBoost、LightGBM KPI 预测。
- `week5`：LSTM、GRU、Transformer 以及 Transformer 消融实验。
- `week6`：3σ、IQR、Isolation Forest、One-Class SVM 与 KPI 根因分析。
- `week7`：预测与异常检测系统集成、Streamlit Web 展示、测试与性能优化。

## 当前状态

- Windows 项目骨架已建立。
- 原工作区曾使用 Python 3.12 虚拟环境；精简交付包不含 `.venv`，在新电脑上运行 `setup_windows.ps1` 创建。
- Week 3 处理后数据和 Week 4–6 实验结果均已恢复，可直接运行 Week 7 Web 系统。
- 原始 `DLPRB_train_0w-5w.csv` 未在当前恢复材料中找到；因此不能声称已从原始数据完整重跑 Week 3–6。已恢复的清洗、归一化数据及历史结果保留用于复核和展示。

GitHub 仓库默认提交关键代码、测试和文档；恢复的 CSV、图像与模型结果保留在本地完整交付包中，不默认上传到 GitHub。克隆仓库后如需运行 Web 系统，应从本地交付包补入 `week3/datasets/processed`、`week4/results`、`week5/results` 和 `week6/results`。

## 放置数据

如需从头重跑，将 `DLPRB_train_0w-5w.csv` 放到：

`week3/datasets/raw/DLPRB_train_0w-5w.csv`

原记录中的数据基线为 840 行、2881 列；第一列是时间索引，后续 2880 列是 `30 × 3 × 32` 个 Beam/KPI。

## Windows 运行

在项目根目录 PowerShell 中，先创建环境并启动当前可运行的 Web 系统：

```powershell
.\setup_windows.ps1
.\week7\run_web.ps1
```

启动后，在同一电脑的浏览器访问 `http://localhost:8501`。`run_all.ps1` 是原始 CSV 到全部结果的重跑入口，只有补齐原始数据时才能使用；它会重新生成实验结果，不应为查看历史结果而运行。

也可分周运行：

```powershell
python week3\scripts\preprocess_dlprb.py
python week3\scripts\analyze_dlprb.py
python week4\scripts\train_models.py
python week5\scripts\train_deep_models.py
python week5\scripts\transformer_ablation.py
python week6\scripts\anomaly_detection.py
.\week7\run_web.ps1
```

所有脚本均使用相对项目路径，不再依赖 `/home/zizhang` 或固定 Windows 用户名。
