@echo off
chcp 65001 >nul
title QQ Chat AI Analyzer - Launcher

echo ========================================================
echo        QQ Chat AI Analyzer - 启动脚本
echo ========================================================

:: 1. Check Python
echo [1/3] 正在检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到 Python，请先安装 Python 3.8+ 并添加到 PATH 环境变量。
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b
)

:: 2. Setup/Check Virtual Environment
echo [2/3] 正在检查依赖环境...
if not exist "venv" (
    echo     检测到首次运行，正在创建虚拟环境 (可能需要几分钟)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo     创建虚拟环境失败，尝试直接使用系统 Python...
    ) else (
        echo     虚拟环境创建成功。
    )
)

if exist "venv" (
    call venv\Scripts\activate
)

:: 3. Install Requirements
if exist "requirements.txt" (
    echo     正在检查/更新依赖库...
    pip install -r requirements.txt -q
)

:: 4. Start App
echo [3/3] 正在启动应用...
echo.
echo     服务启动后，请在浏览器访问: http://127.0.0.1:5000
echo     (如果不自动跳转，请手动复制链接)
echo.

:: Start browser in background after 3 seconds
start "" /b cmd /c "timeout /t 3 >nul && start http://127.0.0.1:5000"

python app.py

pause
