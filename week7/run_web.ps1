$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "未找到虚拟环境，请先在项目根目录运行 .\setup_windows.ps1"
}

Set-Location -LiteralPath $ProjectRoot
& $Python -m streamlit run "week7\app.py" --server.address 127.0.0.1 --server.port 8501

