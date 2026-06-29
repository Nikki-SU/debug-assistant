# debug-assistant 一键启动（开发模式）
# 用法：在 PowerShell 中执行 .\dev.ps1
#   首次：自动创建 venv、安装 server / SDK / CLI 依赖
#   之后：直接启动 server (8765) 和 GUI 前端 (1420)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

function Section($t) {
    Write-Host ""
    Write-Host "==== $t ====" -ForegroundColor Cyan
}

# ---------- 1. Python venv ----------
Section "1/3 准备 Python 环境"
$venv = Join-Path $root ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "创建虚拟环境 $venv"
    py -3 -m venv $venv
}
$pyExe = Join-Path $venv "Scripts\python.exe"
& $pyExe -m pip install --upgrade pip --quiet

Write-Host "安装 server 依赖"
& $pyExe -m pip install --quiet -r (Join-Path $root "server\requirements.txt")
Write-Host "安装 SDK + CLI（开发模式 -e）"
& $pyExe -m pip install --quiet -e (Join-Path $root "sdk\python")
& $pyExe -m pip install --quiet -e (Join-Path $root "cli")

# ---------- 2. 前端依赖 ----------
Section "2/3 准备 GUI 前端"
Push-Location (Join-Path $root "gui")
if (-not (Test-Path "node_modules")) {
    Write-Host "首次安装 npm 依赖（约 1-2 分钟）"
    npm install
} else {
    Write-Host "node_modules 已存在，跳过 npm install（如需重装请删除该目录）"
}
Pop-Location

# ---------- 3. 启动 ----------
Section "3/3 启动 server + GUI"
$env:DEBUG_ASSISTANT_LOG_LEVEL = "INFO"

Write-Host "启动 server  → http://127.0.0.1:8765"
$serverJob = Start-Job -Name da-server -ScriptBlock {
    param($py, $serverDir)
    Set-Location $serverDir
    & $py -m app.main
} -ArgumentList $pyExe, (Join-Path $root "server")

Start-Sleep -Seconds 2

Write-Host "启动 GUI dev → http://127.0.0.1:1420"
Write-Host ""
Write-Host "按 Ctrl+C 退出（会自动停掉 server 后台任务）" -ForegroundColor Yellow
Write-Host ""

Push-Location (Join-Path $root "gui")
try {
    npm run dev
} finally {
    Pop-Location
    Write-Host "停止 server..."
    Stop-Job -Name da-server -ErrorAction SilentlyContinue
    Remove-Job -Name da-server -ErrorAction SilentlyContinue
}

