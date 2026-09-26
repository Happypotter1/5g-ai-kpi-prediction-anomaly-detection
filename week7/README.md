# Week 7：系统集成与 Web 展示

本周将 Week 4–5 的 KPI 预测结果与 Week 6 的异常检测、根因分析结果集成到 Streamlit Web 应用。

## 启动

在项目根目录双击或运行：

```powershell
.\week7\run_web.ps1
```

浏览器访问 `http://127.0.0.1:8501`。

## 功能

- 系统总览：模型效果与异常检测覆盖。
- KPI 预测：传统机器学习、Boosting、RNN 与 Transformer 结果。
- 异常检测：Isolation Forest、One-Class SVM、共同异常与异常并集。
- 根因分析：异常贡献度、相关性和排名。
- 数据浏览：按需读取任意一个 KPI，支持时间筛选和 CSV 下载。

## 验收

```powershell
.\.venv\Scripts\python.exe -m pytest week7\tests -q
.\.venv\Scripts\python.exe week7\scripts\benchmark.py
```

