@echo off
chcp 65001 >nul
echo ============================================
echo Web 版性能分析器
echo ============================================
echo.

cd /d "%~dp0"

echo 正在启动服务...
echo.

set PYTHONIOENCODING=utf-8
set PYTHONPATH=%CD%\backend
cd backend
python app.py

pause
