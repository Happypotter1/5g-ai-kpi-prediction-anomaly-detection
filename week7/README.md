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

真实浏览器端到端测试位于 `week7/e2e/`。它会自行启动本地 Streamlit 进程、打开 Chromium 浏览器，操作五个页面，并在结束时关闭浏览器和服务。首次运行需安装 Node.js 与浏览器依赖：

```powershell
cd week7\e2e
npm install
npx playwright install chromium
npm test
```

默认使用项目根目录 `.venv\Scripts\python.exe` 启动服务。如 Python 环境位于别处，先设置 `PYTHON` 环境变量；已安装 Edge 时也可设置 `BROWSER_CHANNEL=msedge`，无需另下载 Chromium。

验收已部署的公网应用时，在同一目录设置 `BASE_URL` 后运行相同用例；此模式不会启动本地服务。测试可通过网站的唤醒按钮恢复休眠应用，随后执行页面交互与 CSV 下载检查：

```powershell
$env:BASE_URL = "https://5g-ai-kpi-prediction-anomaly-detection-cybqywldc728xbu2uauevq.streamlit.app/"
$env:E2E_ARTIFACT_DIR = "./acceptance-output"
npm test
```

`E2E_ARTIFACT_DIR` 可选，设置后保存四页截图与 `results.json`（目标网址、浏览器版本、各用例状态和耗时）。切回本地测试前运行 `Remove-Item Env:BASE_URL`。

