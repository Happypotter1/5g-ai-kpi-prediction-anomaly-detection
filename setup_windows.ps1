$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Venv = Join-Path $ProjectRoot ".venv"

$Launcher = Get-Command py -ErrorAction SilentlyContinue
if ($Launcher) {
    & py -3.12 --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        & py -3.12 -m venv $Venv
    } else {
        & py -3.11 --version 2>$null
        if ($LASTEXITCODE -ne 0) { throw "需要 Python 3.11 或 3.12（64 位）。" }
        & py -3.11 -m venv $Venv
    }
} else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand) {
        throw "未检测到 Python。请安装 Python 3.11 或 3.12（64 位），安装时勾选 Add Python to PATH。"
    }
    & python -m venv $Venv
}

$Python = Join-Path $Venv "Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
& $Python -c "import numpy,pandas,matplotlib,sklearn,xgboost,lightgbm,torch; print('Environment OK'); print('Torch:',torch.__version__); print('CUDA:',torch.cuda.is_available())"
