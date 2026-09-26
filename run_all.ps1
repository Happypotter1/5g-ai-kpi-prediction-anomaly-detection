$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "未找到 .venv。请先运行 setup_windows.ps1。"
}

$RawData = Join-Path $ProjectRoot "week3\datasets\raw\DLPRB_train_0w-5w.csv"
if (-not (Test-Path $RawData)) {
    throw "原始 CSV 未找到：$RawData。当前可直接启动 Web 展示；从头重跑前请先补齐原始数据。"
}

& $Python "$ProjectRoot\week3\scripts\preprocess_dlprb.py"
& $Python "$ProjectRoot\week3\scripts\analyze_dlprb.py"
& $Python "$ProjectRoot\week4\scripts\train_models.py"
& $Python "$ProjectRoot\week5\scripts\train_deep_models.py"
& $Python "$ProjectRoot\week5\scripts\transformer_ablation.py"
& $Python "$ProjectRoot\week6\scripts\anomaly_detection.py"

Write-Host "Week 3-6 pipeline finished."
